"""
Assignment Analyzer - Code Atlas

Handles the logic for processing `ast.Assign` and `ast.AnnAssign` nodes.
This module is responsible for identifying module-level state, class attributes,
and local variable assignments, and for triggering type inference where appropriate.
"""

import ast
from typing import Dict, Any, Optional

from .logger import get_logger, LogLevel
from .utils import get_source


class AssignmentAnalyzer:
    """Analyzes assignment nodes to update state and symbol tables."""

    def __init__(self, recon_data: Dict[str, Any], visitor):
        self.recon_data = recon_data
        self.visitor = visitor  # The main AnalysisVisitor instance
        self.logger = get_logger()

    def _log(self, level: LogLevel, message: str, extra: Optional[Dict[str, Any]] = None):
        """Enhanced log with automatic source detection and correct module tracking."""
        getattr(get_logger(), level.name.lower())(message, get_source(), extra)

    def analyze_assignment(self, node: ast.Assign):
        """Process assignments for both module state and local variables."""
        if not self.visitor.current_class and not self.visitor.current_function_report:
            # Module-level state
            for target in node.targets:
                if isinstance(target, ast.Name):
                    try:
                        state_entry = {
                            "name": target.id,
                            "value": ast.unparse(node.value) if node.value else "None"
                        }
                        self.visitor.module_report["module_state"].append(state_entry)
                        self._log(LogLevel.DEBUG, f"Module state assignment: {target.id} = {state_entry['value']}")
                    except Exception:
                        pass
        elif self.visitor.current_function_report:
            # Function-level assignments - update symbol table
            for target in node.targets:
                if isinstance(target, ast.Name):
                    try:
                        if isinstance(node.value, ast.Call):
                            # This is a function call assignment
                            context = self.visitor._get_context()
                            var_type = self.visitor.type_inference.infer_from_call(node.value, self.visitor.name_resolver, context)
                            if var_type:
                                self.visitor.symbol_manager.update_variable_type(target.id, var_type)
                                self._log(LogLevel.TRACE, f"Variable assignment with type inference: {target.id} = {var_type}")
                                self._log(LogLevel.TRACE, f"Symbol table updated: {target.id} : {var_type}")
                            else:
                                self._log(LogLevel.TRACE, f"Could not infer type for assignment: {target.id}")
                        else:
                            self._log(LogLevel.TRACE, f"Non-call assignment: {target.id}")
                    except Exception as e:
                        self._log(LogLevel.ERROR, f"Error processing assignment for {target.id}: {e}")
    
    def analyze_annotated_assignment(self, node: ast.AnnAssign):
        """Process annotated assignments."""
        if (not self.visitor.current_class and not self.visitor.current_function_report and
            isinstance(node.target, ast.Name)):
            try:
                state_entry = {
                    "name": node.target.id,
                    "value": ast.unparse(node.value) if node.value else "None"
                }
                self.visitor.module_report["module_state"].append(state_entry)
                annotation_str = ast.unparse(node.annotation) if node.annotation else 'Unknown'
                self._log(LogLevel.DEBUG, f"Module annotated assignment: {node.target.id} : {annotation_str} = {state_entry['value']}")
            except Exception:
                pass
        elif self.visitor.current_function_report and isinstance(node.target, ast.Name):
            try:
                if node.annotation:
                    annotation_str = ast.unparse(node.annotation)
                    self._log(LogLevel.TRACE, f"Annotated assignment: {node.target.id} : {annotation_str}")
                    context = self.visitor._get_context()
                    type_parts = self.visitor.name_resolver.extract_name_parts(node.annotation)
                    if type_parts:
                        resolved_type = self.visitor._cached_resolve_name(type_parts, context)
                        if resolved_type:
                            self.visitor.symbol_manager.update_variable_type(node.target.id, resolved_type)
                            self._log(LogLevel.TRACE, f"Symbol table updated: {node.target.id} : {resolved_type}")
                        else:
                            self._log(LogLevel.WARNING, f"Could not resolve type annotation: {annotation_str}")
            except Exception as e:
                self._log(LogLevel.ERROR, f"Error processing annotated assignment: {e}")
