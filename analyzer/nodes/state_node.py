"""
State Node - Atlas Rewrite

Node representing a module-level state variable.
"""

import ast
from ..core import TreeNode


class StateNode(TreeNode):
    """Node representing a module-level state variable."""
    
    def __init__(self, name: str, parent: TreeNode, ast_node: ast.AST):
        if not ast_node:
            raise ValueError("StateNode requires valid AST node")
        
        super().__init__(name, parent, ast_node)
        
        # Extract type from AST annotation or value
        self.state_type = self._extract_type_from_ast()
    
    def _extract_type_from_ast(self) -> str:
        """Extract state variable type from AST annotation or assignment."""
        if isinstance(self.ast_node, ast.AnnAssign) and self.ast_node.annotation:
            try:
                return ast.unparse(self.ast_node.annotation)
            except:
                return "Unknown"
        elif isinstance(self.ast_node, ast.Assign):
            # Try to infer from assignment value
            if self.ast_node.value:
                try:
                    # Simple value-based type inference
                    if isinstance(self.ast_node.value, ast.Constant):
                        return type(self.ast_node.value.value).__name__
                    elif isinstance(self.ast_node.value, ast.List):
                        return "list"
                    elif isinstance(self.ast_node.value, ast.Dict):
                        return "dict"
                    else:
                        return "Unknown"
                except:
                    return "Unknown"
        return ""  # No type information