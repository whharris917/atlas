"""
Type Node - Atlas Rewrite

Node representing a type annotation with pure self-extracting architecture.
Extremely focused implementation adhering to strict separation of concerns.
"""

import ast
from typing import Optional, TYPE_CHECKING
from ..core import TreeNode, BaseNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    pass


class TypeNode(TreeNode):
    """Node representing a type annotation extracted from AST."""
    
    def __init__(self, type_ast: ast.AST, parent: BaseNode):
        if not type_ast:
            raise ValueError("TypeNode requires valid type AST node")
        if not parent:
            raise ValueError("TypeNode requires parent")
        
        # Self-extract type representation from AST
        type_name = self._extract_type_name(type_ast)
        super().__init__(type_name, parent, type_ast)
    
    def _extract_type_name(self, type_ast: ast.AST) -> str:
        """Extract human-readable type name from AST annotation."""
        try:
            return ast.unparse(type_ast)
        except:
            # Fallback for complex or unsupported type annotations
            return type_ast.__class__.__name__