"""
Attribute Node - Atlas Rewrite

Node representing a class attribute.
Pure structural discovery - no type inference.
"""

import ast
from ..core import TreeNode


class AttributeNode(TreeNode):
    """Node representing a class attribute."""
    
    def __init__(self, name: str, parent: TreeNode, ast_node: ast.AST):
        if not ast_node:
            raise ValueError("AttributeNode requires valid AST node")
        
        super().__init__(name, parent, ast_node)
        # No type extraction - AST node contains all context for Analysis Phase