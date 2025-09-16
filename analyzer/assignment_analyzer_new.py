"""
Analyzes `ast.Assign` and `ast.AnnAssign` nodes to update lexical scope.

This module provides the AssignmentAnalyzer class, which is responsible for
handling variable assignments. It acts as a "command" orchestrator, using the
"query" capabilities of the ExpressionTraversal engine to determine the type
of the right-hand side of an assignment, and then writing that information
into the current ScopeFrame via the ScopeManager.
"""

import ast
from typing import Dict, Any

from .expression_traversal import ExpressionTraversal
from .scope_manager import ScopeManager
from .logger import get_logger, LogLevel
from .utils import get_source

logger = get_logger()

class AssignmentAnalyzer:
    """
    Analyzes `ast.Assign` and `ast.AnnAssign` nodes to update scope.
    """
    def __init__(self, expression_traversal: ExpressionTraversal, scope_manager: ScopeManager):
        """
        Initializes the AssignmentAnalyzer.

        Args:
            expression_traversal: An instance of the ExpressionTraversal engine,
                                  used to evaluate the right-hand side of
                                  assignments.
            scope_manager: The manager for the current lexical scope stack.
                           This is what the analyzer will modify.
        """
        self.expression_traversal = expression_traversal
        self.scope_manager = scope_manager
        self.logger = get_logger()

    def _log(self, level: LogLevel, message: str, node: ast.AST):
        """
        Helper for logging with consistent, rich context, including source location.
        """
        meta = {'source': f"demo.py:L{node.lineno}"}
        getattr(self.logger, level.name.lower())(message, extra={'meta': meta})

    def analyze_assignment(self, node: ast.Assign):
        """
        Analyzes a standard assignment (e.g., `x = value`).

        It evaluates the type of the right-hand side (`node.value`) and then
        registers that type with the target variable name in the scope.
        """
        self._log(LogLevel.INFO, f"Analyzing assignment: {ast.dump(node)}", node)

        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target_name = node.targets[0].id
            
            # Use the expression traversal engine to determine the type of the RHS.
            _, rhs_type = self.expression_traversal.resolve_and_evaluate(node.value)

            if rhs_type:
                self.scope_manager.add_variable_type(target_name, rhs_type)
                self._log(LogLevel.DEBUG, f"Scope updated for '{target_name}' with type '{rhs_type}'", node)
            else:
                self._log(LogLevel.WARNING, f"Could not determine type for RHS of assignment to '{target_name}'", node)

    def analyze_annotated_assignment(self, node: ast.AnnAssign):
        """
        Analyzes an annotated assignment (e.g., `x: int = value` or `x: int`).

        It evaluates the type annotation itself to determine the variable's
        type and registers it in the scope.
        """
        self._log(LogLevel.INFO, f"Analyzing annotated assignment: {ast.dump(node)}", node)
        
        if isinstance(node.target, ast.Name):
            target_name = node.target.id
            
            # The primary source of truth is the annotation itself. We use the
            # traversal engine to evaluate the annotation expression.
            _, annotation_type = self.expression_traversal.resolve_and_evaluate(node.annotation)

            if annotation_type:
                self.scope_manager.add_variable_type(target_name, annotation_type)
                self._log(LogLevel.DEBUG, f"Scope updated for '{target_name}' via annotation to type '{annotation_type}'", node)
            else:
                self._log(LogLevel.WARNING, f"Could not resolve type annotation for '{target_name}'", node)
