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
from .utils import EXTERNAL_LIBRARY_ALLOWLIST
from .logger import get_logger, LogContext, AnalysisPhase


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
            get_logger(__name__).trace(f"Cache hit: {'.'.join(name_parts)} -> {cached_result}", 
                        context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS))
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
        get_logger(__name__).warning(f"Code violation - {violation_type}: {details}",
                      context=LogContext(
                          module=self.module_name,
                          phase=AnalysisPhase.ANALYSIS,
                          function=self.current_function_fqn,
                          extra={'impact': impact, 'violation_type': violation_type}
                      ))
    
    def visit_Module(self, node: ast.Module):
        """Process module."""
        get_logger(__name__).info(f"Starting module analysis: {self.module_name}",
                   context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS))
        
        if (node.body and isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            self.module_report["module_docstring"] = node.body[0].value.value
        
        self.generic_visit(node)
        self.module_report["imports"] = self.import_map.copy()
        
        get_logger(__name__).info(f"Module analysis complete: {self.module_name}",
                   context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS))
    
    def visit_Import(self, node: ast.Import):
        """Process imports."""
        for alias in node.names:
            key = alias.asname if alias.asname else alias.name
            self.import_map[key] = alias.name
            get_logger(__name__).debug(f"Import: {key} -> {alias.name}",
                        context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS))
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Process from imports."""
        if node.module:
            for alias in node.names:
                key = alias.asname if alias.asname else alias.name
                self.import_map[key] = f"{node.module}.{alias.name}"
                get_logger(__name__).debug(f"From import: {key} -> {node.module}.{alias.name}",
                           context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS))
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Process class definitions."""
        class_fqn = f"{self.module_name}.{node.name}"
        get_logger(__name__).debug(f"Analyzing class: {node.name}",
                    context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS))
        
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
            get_logger(__name__).debug(f"Analyzing function: {node.name}",
                        context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS))
            function_report = self._analyze_function(node)
            self.module_report["functions"].append(function_report)
        elif not self.current_function_report:
            # Class method (not nested)
            method_report = self._analyze_function(node)
            # This will be handled by visit_ClassDef
        else:
            # Nested function - process within current function context
            get_logger(__name__).trace(f"Analyzing nested function: {node.name}",
                        context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                         function=self.current_function_fqn))
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
        
        get_logger(__name__).debug(f"Starting function analysis: {function_fqn}",
                    context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS))
        
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
                get_logger(__name__).trace(f"Decorator found: {decorator_str}",
                           context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                            function=function_fqn))
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
        
        get_logger(__name__).debug(f"Function analysis complete: {function_fqn} - "
                    f"Calls: {len(function_report['calls'])}, "
                    f"Instantiations: {len(function_report['instantiations'])}, "
                    f"State Access: {len(function_report['accessed_state'])}",
                    context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS))
        
        emit_count = len(function_report.get("emit_contexts", {}))
        if emit_count > 0:
            get_logger(__name__).info(f"SocketIO emits detected: {emit_count}",
                       context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                        function=function_fqn))
        
        return function_report
    
    def _populate_symbols_from_args(self, args: ast.arguments):
        """Populate symbol table from function arguments with violation checking and parameter type lookup."""
        context = self._get_context()
        get_logger(__name__).trace(f"Processing {len(args.args)} function arguments",
                    context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                     function=self.current_function_fqn))
        
        # Try to get parameter types from recon_data if available
        param_types_from_recon = {}
        if self.current_function_fqn and self.current_function_fqn in self.recon_data["functions"]:
            func_info = self.recon_data["functions"][self.current_function_fqn]
            param_types_from_recon = func_info.get("param_types", {})
            if param_types_from_recon:
                get_logger(__name__).trace(f"Found parameter types in recon data: {param_types_from_recon}",
                           context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                            function=self.current_function_fqn))
        
        for arg in args.args:
            if arg.arg == 'self':
                continue
                
            if arg.annotation:
                # Type hint present - process normally
                try:
                    type_parts = self.name_resolver.extract_name_parts(arg.annotation)
                    if type_parts:
                        get_logger(__name__).trace(f"Processing type annotation for {arg.arg}: {'.'.join(type_parts)}",
                                   context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                                    function=self.current_function_fqn))
                        resolved_type = self._cached_resolve_name(type_parts, context)
                        if resolved_type:
                            self.symbol_manager.update_variable_type(arg.arg, resolved_type)
                            get_logger(__name__).trace(f"Resolved parameter {arg.arg} : {resolved_type}",
                                       context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                                        function=self.current_function_fqn))
                        else:
                            get_logger(__name__).warning(f"Could not resolve type annotation for parameter '{arg.arg}'",
                                         context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                                          function=self.current_function_fqn,
                                                          extra={'impact': 'Method calls on this parameter may fail'}))
                except Exception as e:
                    get_logger(__name__).error(f"Error processing type for {arg.arg}: {e}",
                               context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                                function=self.current_function_fqn))
            elif arg.arg in param_types_from_recon:
                # No direct annotation but we have type info from recon
                param_type_str = param_types_from_recon[arg.arg]
                get_logger(__name__).trace(f"Using recon data type for {arg.arg}: {param_type_str}",
                           context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                            function=self.current_function_fqn))
                
                try:
                    # Parse the type string and resolve it
                    import ast as ast_module
                    type_node = ast_module.parse(param_type_str, mode='eval').body
                    type_parts = self.name_resolver.extract_name_parts(type_node)
                    if type_parts:
                        resolved_type = self._cached_resolve_name(type_parts, context)
                        if resolved_type:
                            self.symbol_manager.update_variable_type(arg.arg, resolved_type)
                            get_logger(__name__).trace(f"Resolved parameter {arg.arg} : {resolved_type} (from recon)",
                                       context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                                        function=self.current_function_fqn))
                        else:
                            # Fallback to the original string
                            self.symbol_manager.update_variable_type(arg.arg, param_type_str)
                            get_logger(__name__).trace(f"Fallback parameter {arg.arg} : {param_type_str} (from recon)",
                                       context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                                        function=self.current_function_fqn))
                    else:
                        # Simple type, use as-is
                        self.symbol_manager.update_variable_type(arg.arg, param_type_str)
                        get_logger(__name__).trace(f"Simple parameter {arg.arg} : {param_type_str} (from recon)",
                                   context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                                    function=self.current_function_fqn))
                except Exception as e:
                    get_logger(__name__).error(f"Error processing recon type for {arg.arg}: {e}",
                               context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                                function=self.current_function_fqn))
                    # Still use the string as fallback
                    self.symbol_manager.update_variable_type(arg.arg, param_type_str)
            else:
                # Missing type hint and no recon data
                get_logger(__name__).trace(f"No type hint or recon data for parameter '{arg.arg}'",
                           context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                            function=self.current_function_fqn))
    
    def _visit_with_nested_handling(self, node: ast.AST):
        """Handle nested functions properly."""
        if isinstance(node, ast.FunctionDef) and self.current_function_report:
            get_logger(__name__).trace(f"Analyzing nested function: {node.name}",
                        context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                         function=self.current_function_fqn))
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
                get_logger(__name__).trace("Could not extract name parts from call",
                           context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                            function=self.current_function_fqn))
                return
            
            raw_name = ".".join(name_parts)
            get_logger(__name__).trace(f"Found call: {raw_name}",
                        context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                         function=self.current_function_fqn))
            
            # Check if this is a built-in that should be ignored
            if len(name_parts) == 1 and name_parts[0] in ['print', 'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'set', 'tuple', 'range', 'enumerate', 'zip', 'all', 'any', 'max', 'min', 'sum', 'abs', 'round', 'sorted']:
                get_logger(__name__).trace(f"Ignored built-in function: {raw_name}",
                           context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                            function=self.current_function_fqn))
                self.generic_visit(node)
                return
            
            context = self._get_context()
            
            # **FIXED: Always resolve the complete call first**
            resolved_fqn = self._cached_resolve_name(name_parts, context)
            
            # **ENHANCED: Track intermediate calls in method chains**
            if len(name_parts) > 1 and resolved_fqn:
                self._track_intermediate_chain_calls(name_parts, context, resolved_fqn)
            
            if resolved_fqn:
                get_logger(__name__).trace(f"Resolved call: {raw_name} -> {resolved_fqn}",
                           context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                            function=self.current_function_fqn))
                
                # **ENHANCED EMIT DETECTION**: Check for emit calls with comprehensive patterns
                is_emit_call = self._is_emit_call(resolved_fqn, name_parts, raw_name)
                
                if is_emit_call:
                    self._handle_emit_call(node, resolved_fqn)
                    get_logger(__name__).info(f"SocketIO emit detected: {resolved_fqn}",
                              context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                               function=self.current_function_fqn))
                # Handle instantiations
                elif resolved_fqn in self.recon_data["classes"]:
                    if resolved_fqn not in self.current_function_report["instantiations"]:
                        self.current_function_report["instantiations"].append(resolved_fqn)
                    get_logger(__name__).debug(f"Class instantiation: {resolved_fqn}",
                               context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                                function=self.current_function_fqn))
                # Handle external class instantiations
                elif resolved_fqn in self.recon_data.get("external_classes", {}):
                    if resolved_fqn not in self.current_function_report["instantiations"]:
                        self.current_function_report["instantiations"].append(resolved_fqn)
                    get_logger(__name__).debug(f"External class instantiation: {resolved_fqn}",
                               context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                                function=self.current_function_fqn))
                # Handle function calls
                elif resolved_fqn in self.recon_data["functions"]:
                    self._add_unique_call(resolved_fqn)
                    get_logger(__name__).debug(f"Function call: {resolved_fqn}",
                               context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                                function=self.current_function_fqn))
                # Handle external function calls
                elif resolved_fqn in self.recon_data.get("external_functions", {}):
                    self._add_unique_call(resolved_fqn)
                    get_logger(__name__).debug(f"External function call: {resolved_fqn}",
                               context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                                function=self.current_function_fqn))
                # Handle external library calls from old allowlist (for backward compatibility)
                elif any(resolved_fqn.startswith(lib) for lib in EXTERNAL_LIBRARY_ALLOWLIST):
                    self._add_unique_call(resolved_fqn)
                    get_logger(__name__).debug(f"External library call: {resolved_fqn}",
                               context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                                function=self.current_function_fqn))
                else:
                    get_logger(__name__).trace(f"Call not in catalog: {resolved_fqn}",
                               context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                                function=self.current_function_fqn))
            else:
                get_logger(__name__).trace(f"Could not resolve call: {raw_name}",
                           context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                            function=self.current_function_fqn))
                
                # **FALLBACK EMIT DETECTION**: Check for emit patterns even when resolution fails
                if self._is_emit_call_fallback(name_parts, raw_name):
                    get_logger(__name__).info(f"Unresolved SocketIO emit detected: {raw_name}",
                              context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                               function=self.current_function_fqn))
                    self._handle_emit_call(node, raw_name)  # Use raw name if we can't resolve
            
            # Check for function arguments
            self._process_function_arguments(node)
        
        except Exception as e:
            get_logger(__name__).error(f"Error processing call: {e}",
                        context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                         function=self.current_function_fqn))
        
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
        get_logger(__name__).trace(f"Tracking intermediate chain calls for: {'.'.join(name_parts)}",
                    context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                     function=self.current_function_fqn))
        
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
                get_logger(__name__).trace(f"Intermediate chain step {i}: {partial_name} -> {partial_resolved}",
                           context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                            function=self.current_function_fqn))
                
                # Check if this is a function/method call (not just an attribute access)
                if (partial_resolved in self.recon_data["functions"] or
                    partial_resolved in self.recon_data.get("external_functions", {})):
                    # Only add if not already captured
                    if partial_resolved not in self.current_function_report["calls"]:
                        self._add_unique_call(partial_resolved)
                        get_logger(__name__).debug(f"Intermediate call added: {partial_resolved}",
                                   context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                                    function=self.current_function_fqn))
                
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
                        get_logger(__name__).trace(f"Updated chain context: {base_name} -> {resolved_type_fqn}",
                                   context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                                    function=self.current_function_fqn))
    
    def _handle_emit_call(self, node: ast.Call, resolved_fqn: str):
        """Handle special emit methods for event name extraction."""
        get_logger(__name__).debug(f"Processing SocketIO emit call: {resolved_fqn}",
                    context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                     function=self.current_function_fqn))
        
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
        
        get_logger(__name__).trace(f"Emit details - Event: {event_name}, Context: {emit_context}",
                    context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                     function=self.current_function_fqn))
    
    def _process_function_arguments(self, node: ast.Call):
        """Process function arguments for function references."""
        context = self._get_context()
        
        for arg in node.args:
            if isinstance(arg, ast.Name):
                arg_fqn = self.name_resolver.resolve_name([arg.id], context)
                if (arg_fqn and (arg_fqn in self.recon_data["functions"] or
                               arg_fqn in self.recon_data.get("external_functions", {}))):
                    self._add_unique_call(arg_fqn)
                    get_logger(__name__).trace(f"Function argument reference: {arg_fqn}",
                               context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                                function=self.current_function_fqn))
    
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
                    get_logger(__name__).debug(f"State access: {resolved_fqn}",
                               context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                                function=self.current_function_fqn))
                else:
                    get_logger(__name__).trace(f"Name {node.id} shadowed by local variable",
                               context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                                function=self.current_function_fqn))
        
        except Exception as e:
            get_logger(__name__).error(f"Error processing name reference {node.id}: {e}",
                        context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                         function=self.current_function_fqn))
        
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
                    get_logger(__name__).debug(f"Attribute state access: {resolved_fqn}",
                               context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                                function=self.current_function_fqn))
                else:
                    get_logger(__name__).trace(f"Attribute base {base_name} shadowed by local variable",
                               context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                                function=self.current_function_fqn))
        
        except Exception as e:
            get_logger(__name__).error(f"Error processing attribute access: {e}",
                        context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                         function=self.current_function_fqn))
        
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
                        get_logger(__name__).debug(f"Module state assignment: {target.id} = {state_entry['value']}",
                                   context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS))
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
                                get_logger(__name__).trace(f"Variable assignment with type inference: {target.id} = {var_type}",
                                           context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                                            function=self.current_function_fqn))
                            else:
                                get_logger(__name__).trace(f"Could not infer type for assignment: {target.id}",
                                           context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                                            function=self.current_function_fqn))
                        else:
                            get_logger(__name__).trace(f"Non-call assignment: {target.id}",
                                       context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                                        function=self.current_function_fqn))
                    except Exception as e:
                        get_logger(__name__).error(f"Error processing assignment for {target.id}: {e}",
                                   context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                                    function=self.current_function_fqn))
        
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
                get_logger(__name__).debug(f"Module annotated assignment: {node.target.id} : {annotation_str} = {state_entry['value']}",
                           context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS))
            except Exception:
                pass
        elif self.current_function_report and isinstance(node.target, ast.Name):
            try:
                if node.annotation:
                    annotation_str = ast.unparse(node.annotation)
                    get_logger(__name__).trace(f"Annotated assignment: {node.target.id} : {annotation_str}",
                               context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                                function=self.current_function_fqn))
                    context = self._get_context()
                    type_parts = self.name_resolver.extract_name_parts(node.annotation)
                    if type_parts:
                        resolved_type = self._cached_resolve_name(type_parts, context)
                        if resolved_type:
                            self.symbol_manager.update_variable_type(node.target.id, resolved_type)
                            get_logger(__name__).trace(f"Symbol table updated: {node.target.id} : {resolved_type}",
                                       context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                                        function=self.current_function_fqn))
                        else:
                            get_logger(__name__).warning(f"Could not resolve type annotation: {annotation_str}",
                                         context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                                          function=self.current_function_fqn))
            except Exception as e:
                get_logger(__name__).error(f"Error processing annotated assignment: {e}",
                           context=LogContext(module=self.module_name, phase=AnalysisPhase.ANALYSIS,
                                            function=self.current_function_fqn))
        
        self.generic_visit(node)


def run_analysis_pass(python_files: List[pathlib.Path], recon_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute analysis pass with clean architecture and external library support."""
    get_logger(__name__).info("Starting analysis pass",
               context=LogContext(phase=AnalysisPhase.ANALYSIS))
    
    atlas = {}
    
    for py_file in python_files:
        get_logger(__name__).info(f"Analyzing file: {py_file.name}",
                   context=LogContext(phase=AnalysisPhase.ANALYSIS, file_name=py_file.name))
        
        try:
            source_code = py_file.read_text(encoding='utf-8')
            tree = ast.parse(source_code)
            module_name = py_file.stem
            
            visitor = AnalysisVisitor(recon_data, module_name)
            visitor.visit(tree)
            
            atlas[py_file.name] = visitor.module_report
            get_logger(__name__).info(f"File analysis complete: {py_file.name}",
                       context=LogContext(phase=AnalysisPhase.ANALYSIS, file_name=py_file.name))
        
        except Exception as e:
            get_logger(__name__).error(f"Failed to analyze {py_file.name}: {e}",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS, file_name=py_file.name))
            atlas[py_file.name] = {
                "file_path": py_file.name,
                "module_docstring": None,
                "imports": {},
                "classes": [],
                "functions": [],
                "module_state": []
            }
            continue
    
    get_logger(__name__).info("Analysis pass complete",
               context=LogContext(phase=AnalysisPhase.ANALYSIS))
    
    return atlas
