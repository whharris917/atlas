"""
Argument Node - Atlas Rewrite

Node representing a function argument.
"""

import ast
from ..core import TreeNode


class ArgumentNode(TreeNode):
    """Node representing a function argument."""
    
    def __init__(self, ast_node: ast.arg):
        if not ast_node:
            raise ValueError("ArgumentNode requires valid AST node")
        
        super().__init__(ast_node.arg, ast_node)
        
        # Extract type from AST annotation
        self.arg_type = self._extract_type_from_ast()
    
    def _extract_type_from_ast(self) -> str:
        """Extract argument type from AST annotation."""
        if self.ast_node.annotation:
            try:
                return ast.unparse(self.ast_node.annotation)
            except:
                return "Unknown"
        return ""  # No annotation