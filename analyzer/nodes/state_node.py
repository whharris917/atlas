"""
State Node - Atlas Rewrite

Node representing a module-level state variable.
Pure structural discovery with self-extracting name.
"""

import ast
from ..core import TreeNode


class StateNode(TreeNode):
    """Node representing a module-level state variable."""
    
    def __init__(self, ast_node: ast.AST, parent: TreeNode):
        if not ast_node:
            raise ValueError("StateNode requires valid AST node")
        
        # Self-extract name from assignment target
        name = self._extract_name_from_ast(ast_node)
        super().__init__(name, parent, ast_node)
    
    def _extract_name_from_ast(self, ast_node: ast.AST) -> str:
        """Extract variable name from assignment AST node."""
        if isinstance(ast_node, ast.Assign):
            # Handle: var = value
            for target in ast_node.targets:
                if isinstance(target, ast.Name):
                    return target.id
        elif isinstance(ast_node, ast.AnnAssign) and isinstance(ast_node.target, ast.Name):
            # Handle: var: Type = value
            return ast_node.target.id
        
        raise ValueError("StateNode requires assignment with simple name target")