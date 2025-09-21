"""
Argument Node - Atlas Rewrite

Node representing a function argument.
"""

import ast
from ..base import TreeNode


class ArgumentNode(TreeNode):
    """Node representing a function argument."""
    
    def __init__(self, ast_node: ast.arg, arg_type: str):
        super().__init__(ast_node.arg, ast_node)
        self.arg_type = arg_type