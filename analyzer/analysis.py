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
from .utils import EXTERNAL_LIBRARY_ALLOWLIST, get_source
from .logger import get_logger, LogContext, AnalysisPhase, LogLevel


class AnalysisVisitor(ast.NodeVisitor):
    """Enhanced analysis visitor with automatic source tracking and verbose context."""
    
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
    

    def _log(
            self, 
            level: LogLevel, 
            message: str, 
            extra: Optional[Dict[str, Any]] = None
        ):
        """Enhanced log with automatic source detection and correct module tracking."""
        
        context = LogContext(
            phase=AnalysisPhase.ANALYSIS,
            source=get_source(),
            module=self.module_name,
            class_name=self.current_class,
            function=self.current_function_fqn
        )

        getattr(get_logger(__name__), level.name.lower())(message, context, extra)

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
            self._log(LogLevel.TRACE, f"Cache hit: {'.'.join(name_parts)} -> {cached_result}")
            return cached_result
        
        result = self.name_resolver.resolve_name(name_parts, context)
        self.resolution_cache[cache_key] = result
        return result
    
    def _add_unique_call(self, call_fqn: str):
        """Add call to function report, ensuring no duplicates."""
        if call_fqn not in self.current_function_report["calls"]:
            self.current_function_report["calls"].append(call_fqn)
    
    def _log_code_violation(self, violation_type: str, details: str, impact: str):
        """Log code standard violations using centralized logging."""
        self._log(LogLevel.WARNING, f"Code violation - {violation_type}: {details}", extra={'impact': impact, 'violation_type': violation_type})
    
    def visit_Module(self, node: ast.Module):
        """Process module."""
        self._log(LogLevel.INFO, f"Starting module analysis: {self.module_name}")
        
        if (node.body and isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            self.module_report["module_docstring"] = node.body[0].value.value
        
        self.generic_visit(node)
        self.module_report["imports"] = self.import_map.copy()
        
        self._log(LogLevel.INFO, f"Module analysis complete: {self.module_name}")
    
    def visit_Import(self, node: ast.Import):
        """Process imports."""
        for alias in node.names:
            key = alias.asname if alias.asname else alias.name
            self.import_map[key] = alias.name
            self._log(LogLevel.DEBUG, f"Import: {key} -> {alias.name}")
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Process from imports."""
        if node.module:
            for alias in node.names:
                key = alias.asname if alias.asname else alias.name
                self.import_map[key] = f"{node.module}.{alias.name}"
                self._log(LogLevel.DEBUG, f"From import: {key} -> {node.module}.{alias.name}")
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Process class definitions."""
        class_fqn = f"{self.module_name}.{node.name}"
        self._log(LogLevel.DEBUG, f"Analyzing class: {node.name}")
        
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
            self._log(LogLevel.DEBUG, f"Analyzing function: {node.name}")
            function_report = self._analyze_function(node)
            self.module_report["functions"].append(function_report)
        elif not self.current_function_report:
            # Class method (not nested)
            method_report = self._analyze_function(node)
            # This will be handled by visit_ClassDef
        else:
            # Nested function - process within current function context
            self._log(LogLevel.TRACE, f"Analyzing nested function: {node.name}")
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
        
        self._log(LogLevel.DEBUG, f"Starting function analysis: {function_fqn}")
        
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
        for violation in violations:
            self._log_code_violation("MISSING_TYPE_HINT", violation, "Type inference may fail")
        
        # Process decorators
        for decorator in node.decorator_list:
            try:
                decorator_str = f"@{ast.unparse(decorator)}"
                function_report["decorators"].append(decorator_str)
                self._log(LogLevel.TRACE, f"Decorator found: {decorator_str}")
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
        
        self._log(LogLevel.DEBUG, f"Function analysis complete: {function_fqn} - "
            f"Calls: {len(function_report['calls'])}, "
            f"Instantiations: {len(function_report['instantiations'])}, "
            f"State Access: {len(function_report['accessed_state'])}"    
        )
        
        emit_count = len(function_report.get("emit_contexts", {}))
        if emit_count > 0:
            self._log(LogLevel.INFO, f"SocketIO emits detected: {emit_count}")
        
        return function_report
    
    def _populate_symbols_from_args(self, args: ast.arguments):
        """Populate symbol table from function arguments with violation checking and parameter type lookup."""
        context = self._get_context()
        self._log(LogLevel.TRACE, f"Processing {len(args.args)} function arguments")
        
        # Try to get parameter types from recon_data if available
        param_types_from_recon = {}
        if self.current_function_fqn and self.current_function_fqn in self.recon_data["functions"]:
            func_info = self.recon_data["functions"][self.current_function_fqn]
            param_types_from_recon = func_info.get("param_types", {})
            if param_types_from_recon:
                self._log(LogLevel.TRACE, f"Found parameter types in recon data: {param_types_from_recon}")
        
        for arg in args.args:
            if arg.arg == 'self':
                continue
                
            if arg.annotation:
                # Type hint present - process normally
                try:
                    type_parts = self.name_resolver.extract_name_parts(arg.annotation)
                    if type_parts:
                        self._log(LogLevel.TRACE, f"Processing type annotation for {arg.arg}: {'.'.join(type_parts)}")
                        resolved_type = self._cached_resolve_name(type_parts, context)
                        if resolved_type:
                            self.symbol_manager.update_variable_type(arg.arg, resolved_type)
                            self._log(LogLevel.TRACE, f"Resolved parameter {arg.arg} : {resolved_type}")
                        else:
                            self._log(LogLevel.WARNING, f"Could not resolve type annotation for parameter '{arg.arg}'",
                                extra={'impact': 'Method calls on this parameter may fail'})
                except Exception as e:
                    self._log(LogLevel.ERROR, f"Error processing type for {arg.arg}: {e}")
            elif arg.arg in param_types_from_recon:
                # No direct annotation but we have type info from recon
                param_type_str = param_types_from_recon[arg.arg]
                self._log(LogLevel.TRACE, f"Using recon data type for {arg.arg}: {param_type_str}")
                
                try:
                    # Parse the type string and resolve it
                    import ast as ast_module
                    type_node = ast_module.parse(param_type_str, mode='eval').body
                    type_parts = self.name_resolver.extract_name_parts(type_node)
                    if type_parts:
                        resolved_type = self._cached_resolve_name(type_parts, context)
                        if resolved_type:
                            self.symbol_manager.update_variable_type(arg.arg, resolved_type)
                            self._log(LogLevel.TRACE, f"Resolved parameter {arg.arg} : {resolved_type} (from recon)")
                        else:
                            # Fallback to the original string
                            self.symbol_manager.update_variable_type(arg.arg, param_type_str)
                            self._log(LogLevel.TRACE, f"Fallback parameter {arg.arg} : {param_type_str} (from recon)")
                    else:
                        # Simple type, use as-is
                        self.symbol_manager.update_variable_type(arg.arg, param_type_str)
                        self._log(LogLevel.TRACE, f"Simple parameter {arg.arg} : {param_type_str} (from recon)")
                except Exception as e:
                    self._log(LogLevel.ERROR, f"Error processing recon type for {arg.arg}: {e}")
                    # Still use the string as fallback
                    self.symbol_manager.update_variable_type(arg.arg, param_type_str)
            else:
                # Missing type hint and no recon data
                self._log(LogLevel.TRACE, f"No type hint or recon data for parameter '{arg.arg}'")
    
    def _visit_with_nested_handling(self, node: ast.AST):
        """Handle nested functions properly."""
        if isinstance(node, ast.FunctionDef) and self.current_function_report:
            self._log(LogLevel.TRACE, f"Analyzing nested function: {node.name}")
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
                self._log(LogLevel.TRACE, "Could not extract name parts from call")
                return
            
            raw_name = ".".join(name_parts)
            self._log(LogLevel.TRACE, f"Found call: {raw_name}")
            
            # Check if this is a built-in that should be ignored
            if len(name_parts) == 1 and name_parts[0] in ['print', 'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'set', 'tuple', 'range', 'enumerate', 'zip', 'all', 'any', 'max', 'min', 'sum', 'abs', 'round', 'sorted']:
                self._log(LogLevel.TRACE, f"Ignored built-in function: {raw_name}")
                self.generic_visit(node)
                return
            
            context = self._get_context()
            
            # **FIXED: Always resolve the complete call first**
            resolved_fqn = self._cached_resolve_name(name_parts, context)
            
            # **ENHANCED: Track intermediate calls in method chains**
            if len(name_parts) > 1 and resolved_fqn:
                self._track_intermediate_chain_calls(name_parts, context, resolved_fqn)
            
            if resolved_fqn:
                self._log(LogLevel.TRACE, f"Resolved call: {raw_name} -> {resolved_fqn}")
                
                # **ENHANCED EMIT DETECTION**: Check for emit calls with comprehensive patterns
                is_emit_call = self._is_emit_call(resolved_fqn, name_parts, raw_name)
                
                if is_emit_call:
                    self._handle_emit_call(node, resolved_fqn)
                    self._log(LogLevel.INFO, f"SocketIO emit detected: {resolved_fqn}")
                # Handle instantiations
                elif resolved_fqn in self.recon_data["classes"]:
                    if resolved_fqn not in self.current_function_report["instantiations"]:
                        self.current_function_report["instantiations"].append(resolved_fqn)
                    self._log(LogLevel.DEBUG, f"Class instantiation: {resolved_fqn}")
                # Handle external class instantiations
                elif resolved_fqn in self.recon_data.get("external_classes", {}):
                    if resolved_fqn not in self.current_function_report["instantiations"]:
                        self.current_function_report["instantiations"].append(resolved_fqn)
                    self._log(LogLevel.DEBUG, f"External class instantiation: {resolved_fqn}")
                # Handle function calls
                elif resolved_fqn in self.recon_data["functions"]:
                    self._add_unique_call(resolved_fqn)
                    self._log(LogLevel.DEBUG, f"Function call: {resolved_fqn}")
                # Handle external function calls
                elif resolved_fqn in self.recon_data.get("external_functions", {}):
                    self._add_unique_call(resolved_fqn)
                    self._log(LogLevel.DEBUG, f"External function call: {resolved_fqn}")
                # Handle external library calls from old allowlist (for backward compatibility)
                elif any(resolved_fqn.startswith(lib) for lib in EXTERNAL_LIBRARY_ALLOWLIST):
                    self._add_unique_call(resolved_fqn)
                    self._log(LogLevel.DEBUG, f"External library call: {resolved_fqn}")
                else:
                    self._log(LogLevel.TRACE, f"Call not in catalog: {resolved_fqn}")
            else:
                self._log(LogLevel.TRACE, f"Could not resolve call: {raw_name}")
                
                # **FALLBACK EMIT DETECTION**: Check for emit patterns even when resolution fails
                if self._is_emit_call_fallback(name_parts, raw_name):
                    self._log(LogLevel.INFO, f"Unresolved SocketIO emit detected: {raw_name}")
                    self._handle_emit_call(node, raw_name)  # Use raw name if we can't resolve
            
            # Check for function arguments
            self._process_function_arguments(node)
        
        except Exception as e:
            self._log(LogLevel.ERROR, f"Error processing call: {e}")
        
        self.generic_visit(node)
    
    def _is_emit_call(self, resolved_fqn: str, name_parts: List[str], raw_name: str) -> bool:
        """Comprehensive emit call detection with multiple patterns including external libraries."""
        
        # Pattern 1: Direct flask_socketio.emit import
        if resolved_fqn == 'flask_socketio.emit':
            return True
        
        # Pattern 2: Any method ending with .emit
        if resolved_fqn.endswith('.emit'):
            return True
        
        # Pattern 3: External SocketIO class emit method
        if 'flask_socketio.SocketIO.emit' in resolved_fqn:
            return True
        
        # Pattern 4: Contains SocketIO
        if 'SocketIO' in resolved_fqn:
            return True
        
        # Pattern 5: Contains socketio (case insensitive)
        if 'socketio' in resolved_fqn.lower():
            return True
        
        # Pattern 6: Check if resolved to external emit function
        if resolved_fqn in self.recon_data.get("external_functions", {}):
            ext_func_info = self.recon_data["external_functions"][resolved_fqn]
            if ext_func_info["name"] == "emit" and "socketio" in ext_func_info["module"]:
                return True
        
        # Pattern 7: Check if any part of the name is 'emit'
        if 'emit' in name_parts:
            return True
        
        # Pattern 8: Check raw name patterns
        if '.emit(' in raw_name or raw_name.endswith('.emit'):
            return True
        
        return False
    
    def _is_emit_call_fallback(self, name_parts: List[str], raw_name: str) -> bool:
        """Fallback emit detection for unresolved calls."""
        
        # Check if 'emit' is the last part of the call
        if name_parts and name_parts[-1] == 'emit':
            return True
        
        # Check for common SocketIO patterns in the raw name
        if any(pattern in raw_name.lower() for pattern in ['socketio.emit', '.emit']):
            return True
        
        return False
    
    def _track_intermediate_chain_calls(self, name_parts: List[str], context: Dict[str, Any], final_resolved_fqn: str):
        """Track intermediate method calls in complex chains - FIXED VERSION."""
        self._log(LogLevel.TRACE, f"Tracking intermediate chain calls for: {'.'.join(name_parts)}")
        
        # Only track intermediate calls if we have a multi-part chain
        if len(name_parts) <= 1:
            return
        
        # Track each progressive step in the chain (excluding the final call which is handled separately)
        for i in range(1, len(name_parts)):  # Skip the final step since it's handled by main resolution
            partial_chain = name_parts[:i+1]
            partial_name = ".".join(partial_chain)
            
            # Skip if this is the same as the final resolved call
            if partial_name == ".".join(name_parts):
                continue
            
            # Try to resolve this partial chain
            partial_resolved = self._cached_resolve_name(partial_chain, context)
            
            if partial_resolved and partial_resolved != final_resolved_fqn:
                self._log(LogLevel.TRACE, f"Intermediate chain step {i}: {partial_name} -> {partial_resolved}")
                
                # Check if this is a function/method call (not just an attribute access)
                if (partial_resolved in self.recon_data["functions"] or
                    partial_resolved in self.recon_data.get("external_functions", {})):
                    # Only add if not already captured
                    if partial_resolved not in self.current_function_report["calls"]:
                        self._add_unique_call(partial_resolved)
                        self._log(LogLevel.DEBUG, f"Intermediate call added: {partial_resolved}")
                
                # Update context for next step using return type if available
                if i < len(name_parts) - 1:  # Don't update for the last step
                    self._update_chain_context(partial_resolved, name_parts[0], context)
    
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
                        self._log(LogLevel.TRACE, f"Updated chain context: {base_name} -> {resolved_type_fqn}")
    
    def _handle_emit_call(self, node: ast.Call, resolved_fqn: str):
        """Handle special emit methods for event name extraction."""
        self._log(LogLevel.DEBUG, f"Processing SocketIO emit call: {resolved_fqn}")
        
        # Extract event name from first argument
        event_name = None
        if node.args and len(node.args) > 0:
            first_arg = node.args[0]
            if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                event_name = first_arg.value
            elif isinstance(first_arg, ast.Name):
                # Variable reference - try to resolve if it's a string constant
                event_name = f"${first_arg.id}"  # Mark as variable reference
        
        # Create special emit entry
        emit_target = f"{resolved_fqn}::{event_name or 'unknown_event'}"
        self._add_unique_call(emit_target)
        
        # Extract additional emit parameters for context
        emit_context = {}
        
        # Check for room parameter
        for keyword in node.keywords:
            if keyword.arg == 'room':
                if isinstance(keyword.value, ast.Constant):
                    emit_context['room'] = keyword.value.value
                elif isinstance(keyword.value, ast.Name):
                    emit_context['room'] = f"${keyword.value.id}"
            elif keyword.arg == 'broadcast':
                if isinstance(keyword.value, ast.Constant):
                    emit_context['broadcast'] = keyword.value.value
        
        # Store emit context if we have any
        if emit_context:
            context_key = f"{emit_target}_context"
            if "emit_contexts" not in self.current_function_report:
                self.current_function_report["emit_contexts"] = {}
            self.current_function_report["emit_contexts"][context_key] = emit_context
        
        self._log(LogLevel.TRACE, f"Emit details - Event: {event_name}, Context: {emit_context}")
    
    def _process_function_arguments(self, node: ast.Call):
        """Process function arguments for function references."""
        context = self._get_context()
        
        for arg in node.args:
            if isinstance(arg, ast.Name):
                arg_fqn = self.name_resolver.resolve_name([arg.id], context)
                if (arg_fqn and (arg_fqn in self.recon_data["functions"] or
                               arg_fqn in self.recon_data.get("external_functions", {}))):
                    self._add_unique_call(arg_fqn)
                    self._log(LogLevel.TRACE, f"Function argument reference: {arg_fqn}")
    
    def visit_Name(self, node: ast.Name):
        """Process name references for state access."""
        if not self.current_function_report:
            return
        
        try:
            context = self._get_context()
            resolved_fqn = self._cached_resolve_name([node.id], context)
            
            if resolved_fqn and resolved_fqn in self.recon_data["state"]:
                # Shadow check
                if not self.symbol_manager.get_variable_type(node.id):
                    if resolved_fqn not in self.current_function_report["accessed_state"]:
                        self.current_function_report["accessed_state"].append(resolved_fqn)
                    self._log(LogLevel.DEBUG, f"State access: {resolved_fqn}")
                else:
                    self._log(LogLevel.TRACE, f"Name {node.id} shadowed by local variable")
        
        except Exception as e:
            self._log(LogLevel.ERROR, f"Error processing name reference {node.id}: {e}")
        
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
            context = self._get_context()
            resolved_fqn = self._cached_resolve_name(name_parts, context)
            
            if resolved_fqn and resolved_fqn in self.recon_data["state"]:
                # Shadow check on base
                base_name = name_parts[0]
                if not self.symbol_manager.get_variable_type(base_name):
                    if resolved_fqn not in self.current_function_report["accessed_state"]:
                        self.current_function_report["accessed_state"].append(resolved_fqn)
                    self._log(LogLevel.DEBUG, f"Attribute state access: {resolved_fqn}")
                else:
                    self._log(LogLevel.TRACE, f"Attribute base {base_name} shadowed by local variable")
        
        except Exception as e:
            self._log(LogLevel.ERROR, f"Error processing attribute access: {e}")
        
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
                        self._log(LogLevel.DEBUG, f"Module state assignment: {target.id} = {state_entry['value']}")
                    except Exception:
                        pass
        elif self.current_function_report:
            # Function-level assignments - update symbol table
            for target in node.targets:
                if isinstance(target, ast.Name):
                    try:
                        if isinstance(node.value, ast.Call):
                            # This is a function call assignment
                            context = self._get_context()
                            var_type = self.type_inference.infer_from_call(node.value, self.name_resolver, context)
                            if var_type:
                                self.symbol_manager.update_variable_type(target.id, var_type)
                                self._log(LogLevel.TRACE, f"Variable assignment with type inference: {target.id} = {var_type}")
                            else:
                                self._log(LogLevel.TRACE, f"Could not infer type for assignment: {target.id}")
                        else:
                            self._log(LogLevel.TRACE, f"Non-call assignment: {target.id}")
                    except Exception as e:
                        self._log(LogLevel.ERROR, f"Error processing assignment for {target.id}: {e}")
        
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
                annotation_str = ast.unparse(node.annotation) if node.annotation else 'Unknown'
                self._log(LogLevel.DEBUG, f"Module annotated assignment: {node.target.id} : {annotation_str} = {state_entry['value']}")
            except Exception:
                pass
        elif self.current_function_report and isinstance(node.target, ast.Name):
            try:
                if node.annotation:
                    annotation_str = ast.unparse(node.annotation)
                    self._log(LogLevel.TRACE, f"Annotated assignment: {node.target.id} : {annotation_str}")
                    context = self._get_context()
                    type_parts = self.name_resolver.extract_name_parts(node.annotation)
                    if type_parts:
                        resolved_type = self._cached_resolve_name(type_parts, context)
                        if resolved_type:
                            self.symbol_manager.update_variable_type(node.target.id, resolved_type)
                            self._log(LogLevel.TRACE, f"Symbol table updated: {node.target.id} : {resolved_type}")
                        else:
                            self._log(LogLevel.WARNING, f"Could not resolve type annotation: {annotation_str}")
            except Exception as e:
                self._log(LogLevel.ERROR, f"Error processing annotated assignment: {e}")
        
        self.generic_visit(node)


def _run_analysis_pass_log_context(source: str) -> LogContext:
    """Create standardized analysis context to eliminate repetitive LogContext creation."""
    return LogContext(
        phase=AnalysisPhase.ANALYSIS,
        source=source,
        module=None,
        class_name=None,
        function=None,
    )


def run_analysis_pass(python_files: List[pathlib.Path], recon_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute analysis pass with clean architecture and external library support."""
    get_logger(__name__).info("Starting analysis pass", context=_run_analysis_pass_log_context(source=get_source()))
    
    atlas = {}
    
    for py_file in python_files:
        get_logger(__name__).info(f"Analyzing file: {py_file.name}", context=_run_analysis_pass_log_context(source=get_source()))
        
        try:
            source_code = py_file.read_text(encoding='utf-8')
            tree = ast.parse(source_code)
            module_name = py_file.stem
            
            visitor = AnalysisVisitor(recon_data, module_name)
            visitor.visit(tree)
            
            atlas[py_file.name] = visitor.module_report
            get_logger(__name__).info(f"File analysis complete: {py_file.name}", context=_run_analysis_pass_log_context(source=get_source()))
        
        except Exception as e:
            get_logger(__name__).error(f"Failed to analyze {py_file.name}: {e}", context=_run_analysis_pass_log_context(source=get_source()))
            atlas[py_file.name] = {
                "file_path": py_file.name,
                "module_docstring": None,
                "imports": {},
                "classes": [],
                "functions": [],
                "module_state": []
            }
            continue
    
    get_logger(__name__).info("Analysis pass complete", context=_run_analysis_pass_log_context(source=get_source()))
    
    return atlas
