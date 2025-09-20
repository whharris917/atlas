"""
Attribute Node - Atlas Rewrite

Node representing a class attribute.
"""

import ast
from typing import Optional
from ..base import TreeNode


class AttributeNode(TreeNode):
    """Node representing a class attribute."""
    
    def __init__(self, name: str, attribute_type: str = "", ast_node: Optional[ast.AST] = None):
        super().__init__(name, ast_node)
        self.attribute_type = attribute_type