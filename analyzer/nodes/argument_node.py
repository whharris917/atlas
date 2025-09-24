"""
Argument Node - Atlas Rewrite

Node representing a function argument with type analysis as final Reconnaissance Phase step.
Extremely focused implementation adhering to strict separation of concerns.
"""

import ast
from typing import Optional, List, Union, TYPE_CHECKING
from ..core import TreeNode, BaseNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from .type_node import TypeNode
    from ..violations import MissingTypeHint


class ArgumentNode(TreeNode):
    """Node representing a function argument with type analysis."""
    
    def __init__(self, arg_ast: ast.arg, parent: BaseNode):
        if not arg_ast:
            raise ValueError("ArgumentNode requires valid ast.arg node")
        if not isinstance(arg_ast, ast.arg):
            raise ValueError("ArgumentNode requires ast.arg node")
        
        # Initialize collections before parent init (which calls _create_children)
        self._type: Optional['TypeNode'] = None
        self._violations: List['MissingTypeHint'] = []
        
        # Pure self-extraction from AST
        super().__init__(arg_ast.arg, parent, arg_ast)
    
    def _create_children(self):
        """
        Final step of Reconnaissance Phase: analyze type information.
        Creates either TypeNode child or MissingTypeHint violation.
        """
        if self.ast_node.annotation:
            # Type annotation exists - create TypeNode
            self._create_type_node(self.ast_node.annotation)
        else:
            # No type annotation - create MissingTypeHint violation
            self._create_missing_type_violation()
    
    def _create_type_node(self, type_ast: ast.AST) -> 'TypeNode':
        """Create TypeNode child from type annotation AST."""
        from .type_node import TypeNode
        self._type = TypeNode(type_ast, parent=self)
        return self._type
    
    def _create_missing_type_violation(self) -> 'MissingTypeHint':
        """Create MissingTypeHint violation ornament."""
        from ..violations import MissingTypeHint
        violation = MissingTypeHint(parent=self, argument_name=self.name)
        self._violations.append(violation)
        return violation