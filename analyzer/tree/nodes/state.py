"""
State Node - Atlas Rewrite

Node representing a module-level state variable.
"""

import ast
from ..base import TreeNode


class StateNode(TreeNode):
    """Node representing a module-level state variable."""
    
    def __init__(self, name: str, ast_node: ast.AST):
        super().__init__(name, ast_node)