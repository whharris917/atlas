"""
Analysis Pass - Code Atlas

Contains the AnalysisVisitor and logic for the second pass of the analysis,
which resolves relationships, tracks calls, and detects special patterns
like SocketIO emits.
"""

import ast
import pathlib
from typing import Dict, List, Any, Optional

from .resolver import NameResolver
from .type_inference import TypeInferenceEngine
from .symbol_table import SymbolTableManager
from .code_checker import CodeStandardChecker
from .utils import LOG_LEVEL, EXTERNAL_LIBRARY_ALLOWLIST, log_violation, ViolationType


class AnalysisVisitor(ast.NodeVisitor):
    """Clean analysis visitor focused on traversal and reporting with SocketIO emit detection, intermediate chain tracking, and external library support."""
    
    def __init__(self, recon_data: Dict[str, Any], module_name: str):
        self.recon_data = recon_data
        self.module_name = module_name
        self.import_map = {}
        
        # Core components
        self.name_resolver = NameResolver(recon_data)
        self.type_inference = TypeInferenceEngine(recon_data)
        self.symbol_manager = SymbolTableManager()
        self.code_checker = CodeStandardChecker()
        
        # Context tracking
        self.current_class = None
        self.current_function_report = None
        self.current_function_fqn = None
        self.resolution_cache = {}
        
        # Output
        self.module_report = {
            "file_path": f"{module_name}.py",
            "module_docstring": None,
            "imports": {},
            "classes": [],
            "functions": [],
            "module_state": []
        }
    
    def log(self, message: str, indent: int = 0, level: int = 1):
        """Output formatted log messages with level control."""
        if level <= LOG_LEVEL:
            print("  " * indent + message)
    
    def _get_context(self) -> Dict[str, Any]:
        """Get current resolution context."""
        return {
            'current_module': self.module_name,
            'current_class': self.current_class,
            'current_function_fqn': self.current_function_fqn,
            'import_map': self.import_map,
            'symbol_manager': self.symbol_manager,
            'type_inference': self.type_inference
        }
    
    def _cached_resolve_name(self, name_parts: List[str], context: Dict[str, Any]) -> Optional[str]:
        """Resolve name with caching to avoid redundant work."""
        cache_key = tuple(name_parts)
        
        if cache_key in self.resolution_cache:
            cached_result = self.resolution_cache[cache_key]
            if LOG_LEVEL >= 2:
                print(f"    [CACHE] {'.'.join(name_parts)} -> {cached_result} (cached)")
            return cached_result
        
        result = self.name_resolver.resolve_name(name_parts, context)
        self.resolution_cache[cache_key] = result
        return result
    
    def _add_unique_call(self, call_fqn: str):
        """Add call to function report, ensuring no duplicates."""
        if call_fqn not in self.current_function_report["calls"]:
            self.current_function_report["calls"].append(call_fqn)
    
    def visit_Module(self, node: ast.Module):
        """Process module."""
        self.log("=== Starting Module Analysis ===")
        
        if (node.body and isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            self.module_report["module_docstring"] = node.body[0].value.value
        
        self.generic_visit(node)
        self.module_report["imports"] = self.import_map.copy()
        self.log("=== Module Analysis Complete ===")
    
    def visit_Import(self, node: ast.Import):
        """Process imports."""
        for alias in node.names:
            key = alias.asname if alias.asname else alias.name
            self.import_map[key] = alias.name
            self.log(f"[IMPORT] {key} -> {alias.name}", 2)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Process from imports."""
        if node.module:
            for alias in node.names:
                key = alias.asname if alias.asname else alias.name
                self.import_map[key] = f"{node.module}.{alias.name}"
                self.log(f"[FROM_IMPORT] {key} -> {node.module}.{alias.name}", 2)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Process class definitions."""
        class_fqn = f"{self.module_name}.{node.name}"
        self.log(f"[CLASS] Analyzing class: {node.name}", 1)
        
        class_report = {
            "name": node.name,
            "docstring": ast.get_docstring(node),
            "methods": []
        }
        
        old_class = self.current_class
        self.current_class = class_fqn
        self.symbol_manager.enter_class_scope()
        
        try:
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    method_report = self._analyze_function(child)
                    class_report["methods"].append(method_report)
        finally:
            self.current_class = old_class
            self.symbol_manager.exit_class_scope()
        
        self.module_report["classes"].append(class_report)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Process function definitions and handle nested functions properly."""
        if not self.current_class:
            # Top-level function
            self.log(f"[FUNCTION] Analyzing function: {node.name}", 1)
            function_report = self._analyze_function(node)
            self.module_report["functions"].append(function_report)
        elif not self.current_function_report:
            # Class method (not nested)
            method_report = self._analyze_function(node)
            # This will be handled by visit_ClassDef
        else:
            # Nested function - process within current function context
            self.log(f"[NESTED_FUNCTION] Analyzing nested function: {node.name}", 3)
            self.symbol_manager.enter_nested_scope()
            try:
                # Populate symbol table from nested function arguments
                self._populate_symbols_from_args(node.args)
                # Traverse nested function body - all calls will be attributed to parent
                for child in node.body:
                    self.visit(child)
            finally:
                self.symbol_manager.exit_nested_scope()
    
    def _analyze_function(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Analyze function with clean separation of concerns."""
        if self.current_class:
            function_fqn = f"{self.current_class}.{node.name}"
        else:
            function_fqn = f"{self.module_name}.{node.name}"
        
        self.log(f"[FUNCTION_ANALYSIS] Starting analysis of: {function_fqn}", 2)
        
        function_report = {
            "name": node.name,
            "args": [arg.arg for arg in node.args.args],
            "docstring": ast.get_docstring(node),
            "calls": [],
            "instantiations": [],
            "accessed_state": [],
            "decorators": [],
            "emit_contexts": {}  # Store SocketIO emit context information
        }
        
        # Check for code standard violations
        violations = self.code_checker.check_function_type_hints(node, function_fqn)
        if violations:
            self.log(f"[CODE_QUALITY] Found {len(violations)} violations in {function_fqn}", 3)
        
        # Process decorators
        for decorator in node.decorator_list:
            try:
                decorator_str = f"@{ast.unparse(decorator)}"
                function_report["decorators"].append(decorator_str)
                self.log(f"[DECORATOR] {decorator_str}", 2)
            except Exception:
                pass
        
        # Set up function context
        old_report = self.current_function_report
        old_fqn = self.current_function_fqn
        self.current_function_report = function_report
        self.current_function_fqn = function_fqn
        self.symbol_manager.enter_function_scope()
        self.resolution_cache = {}

        try:
            # Populate symbol table from arguments
            self._populate_symbols_from_args(node.args)
            
            # Analyze function body
            for child in node.body:
                self._visit_with_nested_handling(child)
        
        finally:
            self.current_function_report = old_report
            self.current_function_fqn = old_fqn
        
        # Clean up empty emit_contexts to keep JSON clean
        if not function_report.get("emit_contexts"):
            function_report.pop("emit_contexts", None)
        
        self.log(f"[FUNCTION_ANALYSIS] Completed analysis of: {function_fqn}", 2)
        self.log(f"  Calls: {len(function_report['calls'])}", 3)
        self.log(f"  Instantiations: {len(function_report['instantiations'])}", 3)
        self.log(f"  State Access: {len(function_report['accessed_state'])}", 3)
        emit_count = len(function_report.get("emit_contexts", {}))
        if emit_count > 0:
            self.log(f"  SocketIO Emits: {emit_count}", 3)
        
        return function_report
    
    def _populate_symbols_from_args(self, args: ast.arguments):
        """Populate symbol table from function arguments with violation checking and parameter type lookup."""
        context = self._get_context()
        self.log(f"[ARG_PROCESSING] Processing {len(args.args)} arguments", 3)
        
        # Try to get parameter types from recon_data if available
        param_types_from_recon = {}
        if self.current_function_fqn and self.current_function_fqn in self.recon_data["functions"]:
            func_info = self.recon_data["functions"][self.current_function_fqn]
            param_types_from_recon = func_info.get("param_types", {})
            if param_types_from_recon:
                self.log(f"[ARG_PROCESSING] Found parameter types in recon data: {param_types_from_recon}", 4)
        
        for arg in args.args:
            if arg.arg == 'self':
                continue
                
            if arg.annotation:
                # Type hint present - process normally
                try:
                    type_parts = self.name_resolver.extract_name_parts(arg.annotation)
                    if type_parts:
                        self.log(f"[ARG_TYPE] Processing type annotation for {arg.arg}: {'.'.join(type_parts)}", 4)
                        resolved_type = self._cached_resolve_name(type_parts, context)
                        if resolved_type:
                            self.symbol_manager.update_variable_type(arg.arg, resolved_type)
                            self.log(f"[ARG_TYPE] RESOLVED {arg.arg} : {resolved_type}", 4)
                        else:
                            self.log(f"[ARG_TYPE] FAILED Could not resolve type annotation for {arg.arg}", 4)
                            log_violation(
                                ViolationType.UNRESOLVABLE_TYPE,
                                f"Type annotation for parameter '{arg.arg}' could not be resolved",
                                "Method calls on this parameter may fail"
                            )
                except Exception as e:
                    self.log(f"[ARG_TYPE] ERROR processing type for {arg.arg}: {e}", 4)
            elif arg.arg in param_types_from_recon:
                # No direct annotation but we have type info from recon
                param_type_str = param_types_from_recon[arg.arg]
                self.log(f"[ARG_TYPE] Using recon data type for {arg.arg}: {param_type_str}", 4)
                
                try:
                    # Parse the type string and resolve it
                    import ast as ast_module
                    type_node = ast_module.parse(param_type_str, mode='eval').body
                    type_parts = self.name_resolver.extract_name_parts(type_node)
                    if type_parts:
                        resolved_type = self._cached_resolve_name(type_parts, context)
                        if resolved_type:
                            self.symbol_manager.update_variable_type(arg.arg, resolved_type)
                            self.log(f"[ARG_TYPE] RESOLVED {arg.arg} : {resolved_type} (from recon)", 4)
                        else:
                            # Fallback to the original string
                            self.symbol_manager.update_variable_type(arg.arg, param_type_str)
                            self.log(f"[ARG_TYPE] FALLBACK {arg.arg} : {param_type_str} (from recon)", 4)
                    else:
                        # Simple type, use as-is
                        self.symbol_manager.update_variable_type(arg.arg, param_type_str)
                        self.log(f"[ARG_TYPE] SIMPLE {arg.arg} : {param_type_str} (from recon)", 4)
                except Exception as e:
                    self.log(f"[ARG_TYPE] ERROR processing recon type for {arg.arg}: {e}", 4)
                    # Still use the string as fallback
                    self.symbol_manager.update_variable_type(arg.arg, param_type_str)
            else:
                # Missing type hint and no recon data - already logged by code checker
                self.log(f"[ARG_TYPE] No type hint or recon data for {arg.arg}", 4)
    
    def _visit_with_nested_handling(self, node: ast.AST):
        """Handle nested functions properly."""
        if isinstance(node, ast.FunctionDef) and self.current_function_report:
            self.log(f"[NESTED_FUNCTION] Analyzing nested function: {node.name}", 3)
            self.symbol_manager.enter_nested_scope()
            try:
                self._populate_symbols_from_args(node.args)
                for child in node.body:
                    self.visit(child)
            finally:
                self.symbol_manager.exit_nested_scope()
        else:
            self.visit(node)
    
    def visit_Call(self, node: ast.Call):
        """Process function calls with comprehensive logging - FIXED VERSION."""
        if not self.current_function_report:
            return
        
        try:
            name_parts = self.name_resolver.extract_name_parts(node.func)
            if not name_parts:
                self.log(f"[CALL] Could not extract name parts from call", 3)
                return
            
            raw_name = ".".join(name_parts)
            self.log(f"[CALL] Found call: {raw_name}", 3)
            
            # Check if this is a built-in that should be ignored
            if len(name_parts) == 1 and name_parts[0] in ['print', 'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'set', 'tuple', 'range', 'enumerate', 'zip', 'all', 'any', 'max', 'min', 'sum', 'abs', 'round', 'sorted']:
                self.log(f"-> IGNORED (built-in function)", 3)
                self.generic_visit(node)
                return
            
            context = self._get_context()
            
            # **FIXED: Always resolve the complete call first**
            resolved_fqn = self._cached_resolve_name(name_parts, context)
            
            # **ENHANCED: Track intermediate calls in method chains**
            if len(name_parts) > 1 and resolved_fqn:
                self._track_intermediate_chain_calls(name_parts, context, resolved_fqn)
            
            if resolved_fqn:
                self.log(f"-> Resolved to: {resolved_fqn}", 3)
                
                # **ENHANCED EMIT DETECTION**: Check for emit calls with comprehensive patterns
                self.log(f"[EMIT_DEBUG] Checking if '{resolved_fqn}' is an emit call", 4)
                self.log(f"[EMIT_DEBUG] Raw name: {raw_name}", 4)
                self.log(f"[EMIT_DEBUG] Name parts: {name_parts}", 4)
                
                is_emit_call = self._is_emit_call(resolved_fqn, name_parts, raw_name)
                
                if is_emit_call:
                    self._handle_emit_call(node, resolved_fqn)
                    self.log(f"-> DETECTED and ADDED emit call: {resolved_fqn}", 3)
                # Handle instantiations
                elif resolved_fqn in self.recon_data["classes"]:
                    if resolved_fqn not in self.current_function_report["instantiations"]:
                        self.current_function_report["instantiations"].append(resolved_fqn)
                    self.log(f"-> ADDED to instantiations", 3)
                # Handle external class instantiations
                elif resolved_fqn in self.recon_data.get("external_classes", {}):
                    if resolved_fqn not in self.current_function_report["instantiations"]:
                        self.current_function_report["instantiations"].append(resolved_fqn)
                    self.log(f"-> ADDED to instantiations (external)", 3)
                # Handle function calls
                elif resolved_fqn in self.recon_data["functions"]:
                    self._add_unique_call(resolved_fqn)
                    self.log(f"-> ADDED to calls", 3)
                # Handle external function calls
                elif resolved_fqn in self.recon_data.get("external_functions", {}):
                    self._add_unique_call(resolved_fqn)
                    self.log(f"-> ADDED to calls (external)", 3)
                # Handle external library calls from old allowlist (for backward compatibility)
                elif any(resolved_fqn.startswith(lib) for lib in EXTERNAL_LIBRARY_ALLOWLIST):
                    self._add_unique_call(resolved_fqn)
                    self.log(f"-> ADDED to calls (external library)", 3)
                else:
                    self.log(f"-> REJECTED (not in catalog or allowlist)", 3)
                    self.log(f"   Available classes: {len(self.recon_data['classes'])}", 4)
                    self.log(f"   Available functions: {len(self.recon_data['functions'])}", 4)
            else:
                self.log(f"-> REJECTED (could not resolve)", 3)
                
                # **FALLBACK EMIT DETECTION**: Check for emit patterns even when resolution fails
                self.log(f"[EMIT_FALLBACK] Checking unresolved call for emit patterns", 4)
                if self._is_emit_call_fallback(name_parts, raw_name):
                    self.log(f"[EMIT_FALLBACK] DETECTED unresolved emit call: {raw_name}", 3)
                    self._handle_emit_call(node, raw_name)  # Use raw name if we can't resolve
                    self.log(f"-> ADDED unresolved emit call: {raw_name}", 3)
            
            # Check for function arguments
            self._process_function_arguments(node)
        
        except Exception as e:
            self.log(f"-> ERROR: {e}", 3)
        
        self.generic_visit(node)
    
    def _is_emit_call(self, resolved_fqn: str, name_parts: List[str], raw_name: str) -> bool:
        """Comprehensive emit call detection with multiple patterns including external libraries."""
        
        # Pattern 1: Direct flask_socketio.emit import
        if resolved_fqn == 'flask_socketio.emit':
            self.log(f"[EMIT_DETECTION] Match: flask_socketio.emit", 4)
            return True
        
        # Pattern 2: Any method ending with .emit
        if resolved_fqn.endswith('.emit'):
            self.log(f"[EMIT_DETECTION] Match: ends with .emit", 4)
            return True
        
        # Pattern 3: External SocketIO class emit method
        if 'flask_socketio.SocketIO.emit' in resolved_fqn:
            self.log(f"[EMIT_DETECTION] Match: SocketIO class emit method", 4)
            return True
        
        # Pattern 4: Contains SocketIO
        if 'SocketIO' in resolved_fqn:
            self.log(f"[EMIT_DETECTION] Match: contains SocketIO", 4)
            return True
        
        # Pattern 5: Contains socketio (case insensitive)
        if 'socketio' in resolved_fqn.lower():
            self.log(f"[EMIT_DETECTION] Match: contains socketio", 4)
            return True
        
        # Pattern 6: Check if resolved to external emit function
        if resolved_fqn in self.recon_data.get("external_functions", {}):
            ext_func_info = self.recon_data["external_functions"][resolved_fqn]
            if ext_func_info["name"] == "emit" and "socketio" in ext_func_info["module"]:
                self.log(f"[EMIT_DETECTION] Match: external socketio emit function", 4)
                return True
        
        # Pattern 7: Check if any part of the name is 'emit'
        if 'emit' in name_parts:
            self.log(f"[EMIT_DETECTION] Match: 'emit' in name parts", 4)
            return True
        
        # Pattern 8: Check raw name patterns
        if '.emit(' in raw_name or raw_name.endswith('.emit'):
            self.log(f"[EMIT_DETECTION] Match: raw name contains emit pattern", 4)
            return True
        
        # Log what we're NOT matching
        self.log(f"[EMIT_DETECTION] No match for: resolved='{resolved_fqn}', parts={name_parts}, raw='{raw_name}'", 4)
        return False
    
    def _is_emit_call_fallback(self, name_parts: List[str], raw_name: str) -> bool:
        """Fallback emit detection for unresolved calls."""
        
        # Check if 'emit' is the last part of the call
        if name_parts and name_parts[-1] == 'emit':
            self.log(f"[EMIT_FALLBACK] Match: last part is 'emit'", 4)
            return True
        
        # Check for common SocketIO patterns in the raw name
        if any(pattern in raw_name.lower() for pattern in ['socketio.emit', '.emit']):
            self.log(f"[EMIT_FALLBACK] Match: contains socketio emit pattern", 4)
            return True
        
        self.log(f"[EMIT_FALLBACK] No match for unresolved call: {raw_name}", 4)
        return False
    
    def _track_intermediate_chain_calls(self, name_parts: List[str], context: Dict[str, Any], final_resolved_fqn: str):
        """Track intermediate method calls in complex chains - FIXED VERSION."""
        self.log(f"    [INTERMEDIATE] Tracking chain steps for: {'.'.join(name_parts)}", 4)
        
        # Only track intermediate calls if we have a multi-part chain
        if len(name_parts) <= 1:
            return
        
        # Track each progressive step in the chain (excluding the final call which is handled separately)
        for i in range(1, len(name_parts)):  # Skip the final step since it's handled by main resolution
            partial_chain = name_parts[:i+1]
            partial_name = ".".join(partial_chain)
            
            self.log(f"    [INTERMEDIATE] Step {i}: {partial_name}", 4)
            
            # Skip if this is the same as the final resolved call
            if partial_name == ".".join(name_parts):
                continue
            
            # Try to resolve this partial chain
            partial_resolved = self._cached_resolve_name(partial_chain, context)
            
            if partial_resolved and partial_resolved != final_resolved_fqn:
                self.log(f"    [INTERMEDIATE] Step {i} resolved to: {partial_resolved}", 4)
                
                # Check if this is a function/method call (not just an attribute access)
                if (partial_resolved in self.recon_data["functions"] or
                    partial_resolved in self.recon_data.get("external_functions", {})):
                    # Only add if not already captured
                    if partial_resolved not in self.current_function_report["calls"]:
                        self._add_unique_call(partial_resolved)
                        self.log(f"    [INTERMEDIATE] ADDED intermediate call: {partial_resolved}", 4)
                
                # Update context for next step using return type if available
                if i < len(name_parts) - 1:  # Don't update for the last step
                    self._update_chain_context(partial_resolved, name_parts[0], context)
            else:
                self.log(f"    [INTERMEDIATE] Step {i} could not be resolved or same as final", 4)
    
    def _update_chain_context(self, resolved_fqn: str, base_name: str, context: Dict[str, Any]):
        """Update resolution context based on intermediate call return type."""
        if resolved_fqn in self.recon_data["functions"]:
            func_info = self.recon_data["functions"][resolved_fqn]
            return_type = func_info.get("return_type")
            if return_type:
                # Extract core type and try to resolve it to FQN
                core_type = self.type_inference.extract_core_type(return_type)
                if core_type:
                    resolved_type_fqn = self.type_inference._resolve_return_type_to_fqn(core_type, context)
                    if resolved_type_fqn:
                        # Update symbol table for next resolution step
                        self.symbol_manager.update_variable_type(base_name, resolved_type_fqn)
                        self.log(f"    [INTERMEDIATE] Updated context: {base_name} -> {resolved_type_fqn}", 4)
    
    def _handle_emit_call(self, node: ast.Call, resolved_fqn: str):
        """Handle special emit methods for event name extraction."""
        self.log(f"[EMIT] Processing SocketIO emit call: {resolved_fqn}", 3)
        
        # Extract event name from first argument
        event_name = None
        if node.args and len(node.args) > 0:
            first_arg = node.args[0]
            if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                event_name = first_arg.value
                self.log(f"[EMIT] Extracted event name: '{event_name}'", 4)
            elif isinstance(first_arg, ast.Name):
                # Variable reference - try to resolve if it's a string constant
                event_name = f"${first_arg.id}"  # Mark as variable reference
                self.log(f"[EMIT] Event name from variable: {first_arg.id}", 4)
        
        # Create special emit entry
        emit_target = f"{resolved_fqn}::{event_name or 'unknown_event'}"
        self._add_unique_call(emit_target)
        self.log(f"-> ADDED emit call: {emit_target}", 3)
        
        # Extract additional emit parameters for context
        emit_context = {}
        
        # Check for room parameter
        for keyword in node.keywords:
            if keyword.arg == 'room':
                if isinstance(keyword.value, ast.Constant):
                    emit_context['room'] = keyword.value.value
                elif isinstance(keyword.value, ast.Name):
                    emit_context['room'] = f"${keyword.value.id}"
                self.log(f"[EMIT] Room parameter: {emit_context.get('room')}", 4)
            elif keyword.arg == 'broadcast':
                if isinstance(keyword.value, ast.Constant):
                    emit_context['broadcast'] = keyword.value.value
                self.log(f"[EMIT] Broadcast parameter: {emit_context.get('broadcast')}", 4)
        
        # Store emit context if we have any
        if emit_context:
            context_key = f"{emit_target}_context"
            if "emit_contexts" not in self.current_function_report:
                self.current_function_report["emit_contexts"] = {}
            self.current_function_report["emit_contexts"][context_key] = emit_context
    
    def _process_function_arguments(self, node: ast.Call):
        """Process function arguments for function references."""
        context = self._get_context()
        
        for arg in node.args:
            if isinstance(arg, ast.Name):
                self.log(f"[FUNCTION_ARG] Checking argument: {arg.id}", 4)
                arg_fqn = self.name_resolver.resolve_name([arg.id], context)
                if (arg_fqn and (arg_fqn in self.recon_data["functions"] or
                               arg_fqn in self.recon_data.get("external_functions", {}))):
                    self._add_unique_call(arg_fqn)
                    self.log(f"-> ADDED to calls (function as argument): {arg_fqn}", 4)
    
    def visit_Name(self, node: ast.Name):
        """Process name references for state access."""
        if not self.current_function_report:
            return
        
        try:
            self.log(f"[NAME] Found name reference: {node.id}", 3)
            
            context = self._get_context()
            resolved_fqn = self._cached_resolve_name([node.id], context)
            
            if resolved_fqn and resolved_fqn in self.recon_data["state"]:
                self.log(f"-> Resolved to state: {resolved_fqn}", 3)
                
                # Shadow check
                if not self.symbol_manager.get_variable_type(node.id):
                    if resolved_fqn not in self.current_function_report["accessed_state"]:
                        self.current_function_report["accessed_state"].append(resolved_fqn)
                    self.log(f"-> ADDED to accessed_state", 3)
                else:
                    self.log(f"-> REJECTED (shadowed by local variable)", 3)
            else:
                self.log(f"-> Not module state", 3)
        
        except Exception as e:
            self.log(f"-> ERROR: {e}", 3)
        
        self.generic_visit(node)
    
    def visit_Attribute(self, node: ast.Attribute):
        """Process attribute access for state variables."""
        if not self.current_function_report:
            self.generic_visit(node)
            return
        
        try:
            name_parts = self.name_resolver.extract_name_parts(node)
            if not name_parts:
                self.generic_visit(node)
                return
            
            full_name = ".".join(name_parts)
            self.log(f"[ATTRIBUTE] Found attribute access: {full_name}", 3)
            
            context = self._get_context()
            resolved_fqn = self._cached_resolve_name(name_parts, context)
            
            if resolved_fqn and resolved_fqn in self.recon_data["state"]:
                self.log(f"-> Resolved to state: {resolved_fqn}", 3)
                
                # Shadow check on base
                base_name = name_parts[0]
                if not self.symbol_manager.get_variable_type(base_name):
                    if resolved_fqn not in self.current_function_report["accessed_state"]:
                        self.current_function_report["accessed_state"].append(resolved_fqn)
                    self.log(f"-> ADDED to accessed_state", 3)
                else:
                    self.log(f"-> REJECTED (base shadowed)", 3)
            else:
                self.log(f"-> Not module state", 3)
        
        except Exception as e:
            self.log(f"-> ERROR: {e}", 3)
        
        self.generic_visit(node)
    
    def visit_Assign(self, node: ast.Assign):
        """Process assignments for both module state and local variables."""
        if not self.current_class and not self.current_function_report:
            # Module-level state
            for target in node.targets:
                if isinstance(target, ast.Name):
                    try:
                        state_entry = {
                            "name": target.id,
                            "value": ast.unparse(node.value) if node.value else "None"
                        }
                        self.module_report["module_state"].append(state_entry)
                        self.log(f"[MODULE_STATE] {target.id} = {state_entry['value']}", 2)
                    except Exception:
                        pass
        elif self.current_function_report:
            # Function-level assignments - update symbol table
            for target in node.targets:
                if isinstance(target, ast.Name):
                    try:
                        self.log(f"[ASSIGNMENT] Processing: {target.id} = ...", 3)
                        
                        if isinstance(node.value, ast.Call):
                            # This is a function call assignment
                            self.log(f"[ASSIGNMENT] Call assignment detected", 4)
                            context = self._get_context()
                            var_type = self.type_inference.infer_from_call(node.value, self.name_resolver, context)
                            if var_type:
                                self.symbol_manager.update_variable_type(target.id, var_type)
                                self.log(f"[ASSIGNMENT] RESOLVED Updated symbol table: {target.id} = {var_type}", 4)
                            else:
                                self.log(f"[ASSIGNMENT] FAILED Could not infer type for {target.id}", 4)
                        else:
                            self.log(f"[ASSIGNMENT] Non-call assignment", 4)
                    except Exception as e:
                        self.log(f"[ASSIGNMENT] ERROR: {e}", 4)
        
        self.generic_visit(node)
    
    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Process annotated assignments."""
        if (not self.current_class and not self.current_function_report and
            isinstance(node.target, ast.Name)):
            try:
                state_entry = {
                    "name": node.target.id,
                    "value": ast.unparse(node.value) if node.value else "None"
                }
                self.module_report["module_state"].append(state_entry)
                self.log(f"[MODULE_STATE] {node.target.id} : {ast.unparse(node.annotation) if node.annotation else 'Unknown'} = {state_entry['value']}", 2)
            except Exception:
                pass
        elif self.current_function_report and isinstance(node.target, ast.Name):
            try:
                if node.annotation:
                    self.log(f"[ANNOTATED_ASSIGNMENT] {node.target.id} : {ast.unparse(node.annotation)}", 3)
                    context = self._get_context()
                    type_parts = self.name_resolver.extract_name_parts(node.annotation)
                    if type_parts:
                        resolved_type = self._cached_resolve_name(type_parts, context)
                        if resolved_type:
                            self.symbol_manager.update_variable_type(node.target.id, resolved_type)
                            self.log(f"-> Updated symbol table: {node.target.id} : {resolved_type}", 4)
                        else:
                            self.log(f"-> Could not resolve type annotation", 4)
            except Exception as e:
                self.log(f"[ANNOTATED_ASSIGNMENT] ERROR: {e}", 3)
        
        self.generic_visit(node)


def run_analysis_pass(python_files: List[pathlib.Path], recon_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute analysis pass with clean architecture and external library support."""
    print("=== ANALYSIS PASS START ===")
    
    atlas = {}
    
    for py_file in python_files:
        print(f"=== Analyzing {py_file.name} ===")
        
        try:
            source_code = py_file.read_text(encoding='utf-8')
            tree = ast.parse(source_code)
            module_name = py_file.stem
            
            visitor = AnalysisVisitor(recon_data, module_name)
            visitor.visit(tree)
            
            atlas[py_file.name] = visitor.module_report
            print(f"  Module analysis complete")
        
        except Exception as e:
            print(f"  ERROR: Failed to analyze {py_file.name}: {e}")
            atlas[py_file.name] = {
                "file_path": py_file.name,
                "module_docstring": None,
                "imports": {},
                "classes": [],
                "functions": [],
                "module_state": []
            }
            continue
    
    print("=== ANALYSIS PASS COMPLETE ===")
    print()
    
    return atlas
