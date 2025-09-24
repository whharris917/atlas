"""
Return Node - Atlas Rewrite

Node representing a function return type with type analysis as final Reconnaissance Phase step.
Extremely focused implementation adhering to strict separation of concerns.
"""

import ast
from typing import Optional, List, TYPE_CHECKING
from ..core import TreeNode, BaseNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from .type_node import TypeNode
    from ..violations import MissingReturnTypeHint


class ReturnNode(TreeNode):
    """Node representing a function return type with type analysis."""
    
    def __init__(self, function_ast: ast.FunctionDef, parent: BaseNode):
        if not function_ast:
            raise ValueError("ReturnNode requires valid ast.FunctionDef node")
        if not isinstance(function_ast, ast.FunctionDef):
            raise ValueError("ReturnNode requires ast.FunctionDef node")
        
        # Initialize collections before parent init (which calls _create_children)
        self._type: Optional['TypeNode'] = None
        self._violations: List['MissingReturnTypeHint'] = []
        
        # ReturnNode always has name "return" for consistency
        super().__init__("return", parent, function_ast)
    
    def _create_children(self):
        """
        Final step of Reconnaissance Phase: analyze return type information.
        Creates either TypeNode child or MissingReturnTypeHint violation.
        """
        if self.ast_node.returns:
            # Return type annotation exists - create TypeNode
            self._create_type_node(self.ast_node.returns)
        else:
            # No return type annotation - create MissingReturnTypeHint violation
            self._create_missing_return_type_violation()
    
    def _create_type_node(self, type_ast: ast.AST) -> 'TypeNode':
        """Create TypeNode child from return type annotation AST."""
        from .type_node import TypeNode
        self._type = TypeNode(type_ast, parent=self)
        return self._type
    
    def _create_missing_return_type_violation(self) -> 'MissingReturnTypeHint':
        """Create MissingReturnTypeHint violation ornament."""
        from ..violations import MissingReturnTypeHint
        violation = MissingReturnTypeHint(parent=self, function_name=self.parent.name)
        self._violations.append(violation)
        return violation