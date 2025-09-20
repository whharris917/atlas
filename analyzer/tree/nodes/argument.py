"""
Argument Node - Atlas Rewrite

Node representing a function argument.
"""

import ast
from typing import Optional
from ..base import TreeNode


class ArgumentNode(TreeNode):
    """Node representing a function argument."""
    
    def __init__(self, name: str, arg_type: str = "", ast_node: Optional[ast.arg] = None):
        super().__init__(name, ast_node)
        self.arg_type = arg_type