"""
Argument Node - Atlas Rewrite

Node representing a function argument.
"""

import ast
from ..base import TreeNode


class ArgumentNode(TreeNode):
    """Node representing a function argument."""
    
    def __init__(self, name: str, arg_type: str, ast_node: ast.arg):
        super().__init__(name, ast_node)
        self.arg_type = arg_type