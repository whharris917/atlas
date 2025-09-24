"""
Type Node - Atlas Rewrite

Node representing a type annotation with pure self-extracting architecture.
Part of final Reconnaissance Phase step that discovers type information.
Creates TypeNode children for arguments with type annotations.
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
    
    @property
    def type_representation(self) -> str:
        """Get the full type representation as it appears in code."""
        return self.name
    
    def list_all(self) -> dict:
        """Get comprehensive type information."""
        return {
            'name': self.name,
            'type_representation': self.type_representation,
            'line_number': self.line_number,
            'ast_type': self.ast_node.__class__.__name__
        }