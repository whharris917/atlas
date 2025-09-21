"""
Attribute Node - Atlas Rewrite

Node representing a class attribute.
"""

import ast
from ..core import TreeNode


class AttributeNode(TreeNode):
    """Node representing a class attribute."""
    
    def __init__(self, name: str, ast_node: ast.AST):
        if not ast_node:
            raise ValueError(f"AttributeNode '{name}' requires valid AST node")
        
        super().__init__(name, ast_node)
        
        # Extract type from AST node
        self.attribute_type = self._extract_type_from_ast()
    
    def _extract_type_from_ast(self) -> str:
        """Extract attribute type from AST node."""
        # For annotated assignments: self.attr: Type = value
        if isinstance(self.ast_node, ast.AnnAssign) and self.ast_node.annotation:
            try:
                return ast.unparse(self.ast_node.annotation)
            except:
                return "Unknown"
        
        # For regular assignments, we could try to infer from value
        # but that's complex, so return empty for now
        return ""