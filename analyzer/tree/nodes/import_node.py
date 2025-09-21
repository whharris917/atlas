"""
Import Node - Atlas Rewrite

Node representing an import statement.
"""

import ast
from ..base import TreeNode


class ImportNode(TreeNode):
    """Node representing an import statement."""
    
    def __init__(self, name: str, module_name: str, ast_node: ast.AST):
        super().__init__(name, ast_node)
        self.module_name = module_name