"""
Attribute Node - Atlas Rewrite

Node representing a class attribute.
"""

import ast
from ..base import TreeNode


class AttributeNode(TreeNode):
    """Node representing a class attribute."""
    
    def __init__(self, name: str, attribute_type: str, ast_node: ast.AST):
        super().__init__(name, ast_node)
        self.attribute_type = attribute_type