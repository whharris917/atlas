"""
Argument Node - Atlas Rewrite

Node representing a function argument.
Pure structural discovery - no type inference.
"""

import ast
from ..core import TreeNode


class ArgumentNode(TreeNode):
    """Node representing a function argument."""
    
    def __init__(self, ast_node: ast.arg, parent: TreeNode):
        if not ast_node:
            raise ValueError("ArgumentNode requires valid AST node")
        
        super().__init__(ast_node.arg, parent, ast_node)
        # No type extraction - AST node contains all context for Analysis Phase