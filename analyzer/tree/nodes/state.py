"""
State Node - Atlas Rewrite

Node representing a module-level state variable.
"""

import ast
from typing import Optional
from ..base import TreeNode


class StateNode(TreeNode):
    """Node representing a module-level state variable."""
    
    def __init__(self, name: str, line_number: int = 0, ast_node: Optional[ast.AST] = None):
        super().__init__(name, ast_node)
        self.line_number = line_number