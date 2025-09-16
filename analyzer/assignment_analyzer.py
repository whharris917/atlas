"""
Assignment Analyzer - Code Atlas

Handles the logic for processing `ast.Assign` and `ast.AnnAssign` nodes.
This module is responsible for identifying module-level state, class attributes,
and local variable assignments, and for triggering type inference where appropriate.

UPDATED: Minimal ExpressionTraversal integration with robust fallbacks.
"""

import ast
from typing import Dict, Any, Optional

from .expression_traversal import ExpressionTraversal
from .logger import get_logger, LogLevel
from .utils import get_source


class AssignmentAnalyzer:
    """Analyzes assignment nodes to update state and symbol tables."""

    def __init__(self, recon_data: Dict[str, Any], visitor):
        self.recon_data = recon_data
        self.visitor = visitor
        self.logger = get_logger()
        
        # MINIMAL INTEGRATION: Add ExpressionTraversal for enhanced type inference
        try:
            self.expression_traversal = ExpressionTraversal(
                recon_data=self.recon_data,
                scope_manager=self.visitor.scope_manager,
                module_fqn=self.visitor.module_name
            )
            self.use_expression_traversal = True
        except Exception as e:
            self._log(LogLevel.WARNING, f"Failed to initialize ExpressionTraversal: {e}")
            self.expression_traversal = None
            self.use_expression_traversal = False

    def _log(self, level: LogLevel, message: str, extra: Optional[Dict[str, Any]] = None):
        """Enhanced log with automatic source detection and correct module tracking."""
        getattr(get_logger(), level.name.lower())(message, get_source(), extra)

    def analyze_assignment(self, node: ast.Assign):
        """Process assignments for both module state and local variables."""
        
        # Check if we're in module scope (no class or function context)
        current_class = self.visitor.scope_manager.get_current_class_fqn()
        is_in_function = self.visitor.current_function_report is not None
        
        if not current_class and not is_in_function:
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
        elif is_in_function:
            # Function-level assignments - update scope manager
            for target in node.targets:
                if isinstance(target, ast.Name):
                    try:
                        if isinstance(node.value, ast.Call):
                            # MINIMAL INTEGRATION: Enhanced function call type inference
                            var_type = self._infer_call_type_enhanced(node.value)

                            if var_type:
                                # Use scope manager instead of symbol manager
                                self.visitor.scope_manager.update_variable_type(target.id, var_type)
                                self._log(LogLevel.TRACE, f"Variable assignment with type inference: {target.id} = {var_type}")
                            else:
                                self._log(LogLevel.TRACE, f"Could not infer type for assignment: {target.id}")
                        else:
                            self._log(LogLevel.TRACE, f"Non-call assignment: {target.id}")
                    except Exception as e:
                        self._log(LogLevel.ERROR, f"Error processing assignment for {target.id}: {e}")
    
    def analyze_annotated_assignment(self, node: ast.AnnAssign):
        """Process annotated assignments."""
        
        # Check if we're in module scope (no class or function context)
        current_class = self.visitor.scope_manager.get_current_class_fqn()
        is_in_function = self.visitor.current_function_report is not None
        
        if (not current_class and not is_in_function and
            isinstance(node.target, ast.Name)):
            # Module-level annotated assignment
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
        elif is_in_function and isinstance(node.target, ast.Name):
            # Function-level annotated assignment
            try:
                if node.annotation:
                    annotation_str = ast.unparse(node.annotation)
                    self._log(LogLevel.TRACE, f"Annotated assignment: {node.target.id} : {annotation_str}")
                    
                    # KEEP ORIGINAL: Use proven annotation resolution
                    context = self.visitor._get_context()
                    type_parts = self.visitor.name_resolver.extract_name_parts(node.annotation)
                    if type_parts:
                        resolved_type = self.visitor._cached_resolve_name(type_parts, context)
                        if resolved_type:
                            # Use scope manager instead of symbol manager
                            self.visitor.scope_manager.update_variable_type(node.target.id, resolved_type)
                            self._log(LogLevel.TRACE, f"Scope updated: {node.target.id} : {resolved_type}")
                        else:
                            self._log(LogLevel.WARNING, f"Could not resolve type annotation: {annotation_str}")
            except Exception as e:
                self._log(LogLevel.ERROR, f"Error processing annotated assignment: {e}")

    def _infer_call_type_enhanced(self, call_node: ast.Call) -> Optional[str]:
        """
        STRESS TEST: ExpressionTraversal-only function call type inference.
        
        No fallback - forces ExpressionTraversal to handle all cases.
        """
        if not self.use_expression_traversal:
            self._log(LogLevel.WARNING, "ExpressionTraversal not available, cannot infer call type")
            return None
            
        try:
            _, inferred_type = self.expression_traversal.resolve_and_evaluate(call_node)
            if inferred_type:
                self._log(LogLevel.TRACE, f"ExpressionTraversal inferred type: {inferred_type}")
                return inferred_type
            else:
                self._log(LogLevel.TRACE, "ExpressionTraversal returned None for type inference")
                return None
        except Exception as e:
            self._log(LogLevel.ERROR, f"ExpressionTraversal failed completely: {e}")
            return None
