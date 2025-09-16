"""
Function Analyzer - Code Atlas

Handles the analysis of a single function or method definition (`ast.FunctionDef`).
It is responsible for creating and populating the 'function report' dictionary
that appears in the final analysis output.

UPDATED: Integrated with enhanced ScopeManager for unified scope management.
"""

import ast
from typing import Dict, Any, Optional

from .scope_manager import ScopeType
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
        """Analyze function with enhanced scope management."""
        
        # Get parent scope from scope manager instead of manually tracking
        parent_scope_fqn = self.visitor.scope_manager.get_current_scope_fqn()
        function_fqn = f"{parent_scope_fqn}.{node.name}"
        
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
        self.visitor.current_function_report = function_report
        
        # Use enhanced scope management - this automatically updates logger context
        self.visitor.scope_manager.enter_scope(function_fqn, ScopeType.FUNCTION)
        self.visitor.resolution_cache = {}

        try:
            # Populate symbol table from arguments
            self._populate_symbols_from_args(node.args)
            
            # Analyze function body
            for child in node.body:
                self.visitor.visit(child)
        
        finally:
            self.visitor.current_function_report = old_report
            # Exit scope - this automatically updates logger context
            self.visitor.scope_manager.exit_scope()
        
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
        
        # Get function FQN for recon data lookup
        function_fqn = self.visitor.scope_manager.get_current_scope_fqn()
        
        # Extract parameter types from recon data
        param_types_from_recon = {}
        if function_fqn in self.recon_data.get("functions", {}):
            param_types_from_recon = self.recon_data["functions"][function_fqn].get("param_types", {})
        
        context = self.visitor._get_context()
        
        for arg in args.args:
            if arg.annotation:
                # Direct type annotation available
                try:
                    # Extract type parts and resolve
                    type_parts = self.visitor.name_resolver.extract_name_parts(arg.annotation)
                    if type_parts:
                        self._log(LogLevel.TRACE, f"Processing type annotation for {arg.arg}: {'.'.join(type_parts)}")
                        resolved_type = self.visitor._cached_resolve_name(type_parts, context)
                        if resolved_type:
                            # Use scope manager instead of symbol manager
                            self.visitor.scope_manager.update_variable_type(arg.arg, resolved_type)
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
                            # Use scope manager instead of symbol manager
                            self.visitor.scope_manager.update_variable_type(arg.arg, resolved_type)
                            self._log(LogLevel.TRACE, f"Resolved parameter {arg.arg} : {resolved_type} (from recon)")
                        else:
                            # Fallback to the original string
                            self.visitor.scope_manager.update_variable_type(arg.arg, param_type_str)
                            self._log(LogLevel.TRACE, f"Fallback parameter {arg.arg} : {param_type_str} (from recon)")
                    else:
                        # Simple type, use as-is
                        self.visitor.scope_manager.update_variable_type(arg.arg, param_type_str)
                        self._log(LogLevel.TRACE, f"Simple parameter {arg.arg} : {param_type_str} (from recon)")
                except Exception as e:
                    self._log(LogLevel.ERROR, f"Error processing recon type for {arg.arg}: {e}")
                    # Still use the string as fallback
                    self.visitor.scope_manager.update_variable_type(arg.arg, param_type_str)
            else:
                # Missing type hint and no recon data
                self._log(LogLevel.TRACE, f"No type hint or recon data for parameter '{arg.arg}'")
