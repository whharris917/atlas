"""
Alias Node - Atlas Rewrite

Node representing an imported alias.
Pure self-extracting architecture - determines full_name from parent context.
"""

import ast
from ..core import TreeNode


class AliasNode(TreeNode):
    """Node representing an imported alias."""
    
    def __init__(self, ast_node: ast.alias, parent: TreeNode):
        if not ast_node:
            raise ValueError("AliasNode requires valid AST node")
        
        # Self-extract local name from AST
        local_name = ast_node.asname if ast_node.asname else ast_node.name
        super().__init__(local_name, parent, ast_node)
    
    @property
    def full_name(self) -> str:
        """Calculate full import name from parent context and AST."""
        # Get the import statement from parent container
        if hasattr(self.parent, 'ast_node'):
            if isinstance(self.parent.ast_node, ast.Import):
                # Direct import: import os, sys
                return self.ast_node.name
            elif isinstance(self.parent.ast_node, ast.ImportFrom):
                # From import: from os.path import join
                module_name = self.parent.ast_node.module or ""
                if self.ast_node.name == "*":
                    return f"{module_name}.*"
                else:
                    return f"{module_name}.{self.ast_node.name}" if module_name else self.ast_node.name
        
        # Fallback if parent context unclear
        return self.ast_node.name