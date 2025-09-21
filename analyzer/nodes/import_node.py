"""
Import Node - Atlas Rewrite

Node representing an import statement.
"""

import ast
from ..core import TreeNode


class ImportNode(TreeNode):
    """Node representing an import statement."""
    
    def __init__(self, name: str, ast_node: ast.AST):
        if not ast_node:
            raise ValueError(f"ImportNode '{name}' requires valid AST node")
        
        super().__init__(name, ast_node)
        
        # Derive module_name from AST node
        self.module_name = self._extract_module_name_from_ast()
    
    def _extract_module_name_from_ast(self) -> str:
        """Extract the actual module name from the AST node."""
        if isinstance(self.ast_node, ast.Import):
            # For "import requests", find the alias that matches our name
            for alias in self.ast_node.names:
                local_name = alias.asname if alias.asname else alias.name
                if local_name == self.name:
                    return alias.name
        
        elif isinstance(self.ast_node, ast.ImportFrom) and self.ast_node.module:
            # For "from auth import AuthManager", find the alias that matches our name
            for alias in self.ast_node.names:
                local_name = alias.asname if alias.asname else alias.name
                if local_name == self.name:
                    return f"{self.ast_node.module}.{alias.name}"
        
        # Fallback - shouldn't happen with proper construction
        return "unknown"