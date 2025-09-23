"""
Attribute Node - Atlas Rewrite

Node representing a class attribute with pure self-extracting architecture.
Type inference eliminated for clean responsibility separation.
Self-extracts name from ast.AnnAssign target nodes.
"""

import ast
from typing import Optional, TYPE_CHECKING
from ..core import TreeNode, BaseNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    pass


class AttributeNode(TreeNode):
    """Node representing a class attribute."""
    
    def __init__(self, attr_ast: ast.AnnAssign, parent: BaseNode):
        if not attr_ast:
            raise ValueError("AttributeNode requires valid ast.AnnAssign node")
        if not isinstance(attr_ast, ast.AnnAssign):
            raise ValueError("AttributeNode requires ast.AnnAssign node")
        if not isinstance(attr_ast.target, ast.Name):
            raise ValueError("AttributeNode requires ast.AnnAssign with ast.Name target")
        
        # Pure self-extraction from AST target
        super().__init__(attr_ast.target.id, parent, attr_ast)
    
    def list_all(self) -> dict:
        """Get comprehensive attribute information."""
        return {
            'name': self.name,
            'line_number': self.line_number
        }