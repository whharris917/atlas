"""
Function Analyzer - Code Atlas

Handles the analysis of a single function or method definition (`ast.FunctionDef`).
It is responsible for creating and populating the 'function report' dictionary
that appears in the final analysis output.
"""

import ast
from typing import Dict, Any, Optional

from .logger import get_logger, LogLevel
from .utils import get_source


class FunctionAnalyzer:
    """Analyzes a function definition to create a structured report."""

    def __init__(self, recon_data: Dict[str, Any], visitor):
        self.recon_data = recon_data
        self.visitor = visitor  # The main AnalysisVisitor instance
        self.logger = get_logger()

    def _log(self, level: LogLevel, message: str, extra: Optional[Dict[str, Any]] = None):
        """Enhanced log with automatic source detection and correct module tracking."""
        getattr(get_logger(), level.name.lower())(message, get_source(), extra)

    def analyze_function(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Analyze function with clean separation of concerns."""
        if self.visitor.current_class:
            function_fqn = f"{self.visitor.current_class}.{node.name}"
        else:
            function_fqn = f"{self.visitor.module_name}.{node.name}"
        
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
        violations = self.visitor.code_checker.check_function_type_hints(node, function_fqn)
        for violation in violations:
            self.visitor._log_code_violation("MISSING_TYPE_HINT", violation, "Type inference may fail")
        
        # Process decorators
        for decorator in node.decorator_list:
            try:
                decorator_str = f"@{ast.unparse(decorator)}"
                function_report["decorators"].append(decorator_str)
                self._log(LogLevel.TRACE, f"Decorator found: {decorator_str}")
            except Exception:
                pass
        
        # Set up function context
        old_report = self.visitor.current_function_report
        old_fqn = self.visitor.current_function_fqn
        self.visitor.current_function_report = function_report
        self.visitor.current_function_fqn = function_fqn  # This triggers logger context update
        self.visitor.symbol_manager.enter_function_scope()
        self.visitor.resolution_cache = {}

        try:
            # Populate symbol table from arguments
            self._populate_symbols_from_args(node.args)
            
            # Analyze function body
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    # This is the restored logic for handling nested functions directly.
                    self._log(LogLevel.TRACE, f"Analyzing nested function: {child.name}")
                    self.visitor.symbol_manager.enter_nested_scope()
                    try:
                        self._populate_symbols_from_args(child.args)
                        for nested_child in child.body:
                            self.visitor.visit(nested_child)
                    finally:
                        self.visitor.symbol_manager.exit_nested_scope()
                else:
                    self.visitor.visit(child)
        
        finally:
            self.visitor.current_function_report = old_report
            self.visitor.current_function_fqn = old_fqn  # This triggers logger context update
        
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
        context = self.visitor._get_context()
        self._log(LogLevel.TRACE, f"Processing {len(args.args)} function arguments")
        
        # Try to get parameter types from recon_data if available
        param_types_from_recon = {}
        if self.visitor.current_function_fqn and self.visitor.current_function_fqn in self.recon_data["functions"]:
            func_info = self.recon_data["functions"][self.visitor.current_function_fqn]
            param_types_from_recon = func_info.get("param_types", {})
            if param_types_from_recon:
                self._log(LogLevel.TRACE, f"Found parameter types in recon data: {param_types_from_recon}")
        
        for arg in args.args:
            if arg.arg == 'self':
                continue
                
            if arg.annotation:
                # Type hint present - process normally
                try:
                    type_parts = self.visitor.name_resolver.extract_name_parts(arg.annotation)
                    if type_parts:
                        self._log(LogLevel.TRACE, f"Processing type annotation for {arg.arg}: {'.'.join(type_parts)}")
                        resolved_type = self.visitor._cached_resolve_name(type_parts, context)
                        if resolved_type:
                            self.visitor.symbol_manager.update_variable_type(arg.arg, resolved_type)
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
                    type_parts = self.visitor.name_resolver.extract_name_parts(type_node)
                    if type_parts:
                        resolved_type = self.visitor._cached_resolve_name(type_parts, context)
                        if resolved_type:
                            self.visitor.symbol_manager.update_variable_type(arg.arg, resolved_type)
                            self._log(LogLevel.TRACE, f"Resolved parameter {arg.arg} : {resolved_type} (from recon)")
                        else:
                            # Fallback to the original string
                            self.visitor.symbol_manager.update_variable_type(arg.arg, param_type_str)
                            self._log(LogLevel.TRACE, f"Fallback parameter {arg.arg} : {param_type_str} (from recon)")
                    else:
                        # Simple type, use as-is
                        self.visitor.symbol_manager.update_variable_type(arg.arg, param_type_str)
                        self._log(LogLevel.TRACE, f"Simple parameter {arg.arg} : {param_type_str} (from recon)")
                except Exception as e:
                    self._log(LogLevel.ERROR, f"Error processing recon type for {arg.arg}: {e}")
                    # Still use the string as fallback
                    self.visitor.symbol_manager.update_variable_type(arg.arg, param_type_str)
            else:
                # Missing type hint and no recon data
                self._log(LogLevel.TRACE, f"No type hint or recon data for parameter '{arg.arg}'")
