"""
State Node - Atlas Rewrite

Node representing a module-level state variable.
"""

import ast
from ..core import TreeNode


class StateNode(TreeNode):
    """Node representing a module-level state variable."""
    
    def __init__(self, name: str, ast_node: ast.AST):
        if not ast_node:
            raise ValueError(f"StateNode '{name}' requires valid AST node")
        
        super().__init__(name, ast_node)