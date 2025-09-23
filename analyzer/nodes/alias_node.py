"""
Alias Node - Atlas Rewrite

Node representing an imported alias.
"""

import ast
from ..core import TreeNode


class AliasNode(TreeNode):
    """Node representing an imported alias."""
    
    def __init__(self, name: str, parent: TreeNode, full_name: str, ast_node: ast.alias):
        if not ast_node:
            raise ValueError("AliasNode requires valid AST node")
        
        super().__init__(name, parent, ast_node)
        self.full_name = full_name  # The actual import target