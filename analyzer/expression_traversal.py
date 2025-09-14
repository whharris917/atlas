"""
Core Expression Traversal Engine for Code Atlas.

This module provides the ExpressionTraversal class, the cornerstone of the
new analysis engine. It is a unified, stateful "query" engine responsible
for processing any given Python expression (ast.expr). It replaces all
previous, fragmented resolution logic with a single, robust mechanism.
"""

import ast
from typing import List, Tuple, Optional, Dict, Any

from .operations import Operation, GetName, GetAttribute, CallFunction
from .scope_manager import ScopeManager
from .logger import get_logger

logger = get_logger()

class ExpressionTraversal:
    """
    Orchestrates the analysis of a single Python expression (ast.expr).

    This class is the core of the new, unified analysis engine. It replaces
    all previous "resolver" and "chain walking" logic. Its primary job is to
    take a complex, nested AST expression and process it step-by-step to
    determine its final identity (Resolve) and its resulting type (Evaluate).

    The process works in two phases:
    1.  Linearization: The `_linearize_expression` method walks the nested
        ast.expr node (e.g., a.b.c()) and converts it into a flat, sequential
        list of `Operation` objects, called the Linear Operation Queue.
    2.  Traversal: The `resolve_and_evaluate` method iterates through this
        queue, calling the `execute` method on each operation. It statefully
        passes the result of one operation as the input context to the next,
        a process known as Type Propagation.
    """

    def __init__(self, recon_data: Dict[str, Any], scope_manager: ScopeManager, module_fqn: str):
        """
        Initializes the ExpressionTraversal engine.

        Args:
            recon_data: The read-only dictionary of all discovered code
                        entities from the reconnaissance phase.
            scope_manager: The manager for the current lexical scope stack.
                         This is read from to look up local variables.
            module_fqn: The Fully Qualified Name of the module currently
                        being analyzed.
        """
        self.recon_data = recon_data
        self.scope_manager = scope_manager
        self.module_fqn = module_fqn
        self.logger = get_logger()

    def _linearize_expression(self, expression: ast.expr) -> List[Operation]:
        """
        Converts a nested AST expression node into a linear queue of operations.

        This method recursively walks down an expression tree and builds a
        flat list of operations that represents the order of execution.

        Example:
            `a.b()` becomes `[GetName('a'), GetAttribute('b'), CallFunction()]`

        Args:
            expression: The ast.expr node to linearize.

        Returns:
            A list of Operation objects.
        """
        if isinstance(expression, ast.Name):
            return [GetName(expression.id)]
        elif isinstance(expression, ast.Attribute):
            prefix_ops = self._linearize_expression(expression.value)
            prefix_ops.append(GetAttribute(expression.attr))
            return prefix_ops
        elif isinstance(expression, ast.Call):
            prefix_ops = self._linearize_expression(expression.func)
            prefix_ops.append(CallFunction())
            return prefix_ops
        else:
            self.logger.warning(f"Unsupported expression type for linearization: {type(expression).__name__}")
            return []

    def resolve_and_evaluate(self, expression: ast.expr) -> Tuple[Optional[str], Optional[str]]:
        """
        Performs the full traversal of an expression to resolve and evaluate it.

        This is the main public method of the class. It orchestrates the
        entire process: linearizing the expression and then executing the
        resulting operation queue.

        Args:
            expression: The ast.expr node to analyze.

        Returns:
            A tuple containing:
            - The resolved FQN of the final entity in the expression (Identity).
            - The evaluated FQN of the resulting type of the expression.
        """
        operations = self._linearize_expression(expression)
        op_str = "".join(map(str, operations))
        log_meta = {'expression': ast.dump(expression)}
        self.logger.debug(
            f"Linearized Operation Queue: {op_str}",
            extra={'meta': log_meta}
        )

        current_type_fqn: Optional[str] = None
        final_identity_fqn: Optional[str] = None

        for i, operation in enumerate(operations):
            current_type_fqn = operation.execute(
                current_type_fqn,
                self.recon_data,
                self.scope_manager
            )

            if current_type_fqn is None:
                self.logger.warning(f"Expression traversal failed at step {i+1}: {operation}")
                return None, None

            # The "Identity" of an expression is the FQN of the entity itself,
            # while the "Resulting Type" can change after an operation like a
            # function call. We update the identity for operations that resolve
            # to a new entity (GetName, GetAttribute). For a CallFunction, the
            # identity remains the function that was called, which was determined
            # in the previous step.
            if not isinstance(operation, CallFunction):
                final_identity_fqn = current_type_fqn

        self.logger.debug(f"Traversal complete. Final Identity: '{final_identity_fqn}', Final Type: '{current_type_fqn}'")

        return final_identity_fqn, current_type_fqn
