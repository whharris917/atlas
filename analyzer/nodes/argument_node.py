"""
Argument Node - Atlas Rewrite

Node representing a function argument with pure self-extracting architecture.
Type inference eliminated for clean responsibility separation.
Self-extracts name from ast.arg nodes.
"""

import ast
from typing import Optional, TYPE_CHECKING
from ..core import TreeNode, BaseNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    pass


class ArgumentNode(TreeNode):
    """Node representing a function argument."""
    
    def __init__(self, arg_ast: ast.arg, parent: BaseNode):
        if not arg_ast:
            raise ValueError("ArgumentNode requires valid ast.arg node")
        if not isinstance(arg_ast, ast.arg):
            raise ValueError("ArgumentNode requires ast.arg node")
        
        # Pure self-extraction from AST
        super().__init__(arg_ast.arg, parent, arg_ast)
    
    def list_all(self) -> dict:
        """Get comprehensive argument information."""
        return {
            'name': self.name,
            'line_number': self.line_number
        }