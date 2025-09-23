"""
State Node - Atlas Rewrite

Node representing a module-level state variable with pure self-extracting architecture.
Type inference eliminated for clean responsibility separation.
Self-extracts name from individual ast.Name target nodes.
"""

import ast
from typing import Optional, TYPE_CHECKING
from ..core import TreeNode, BaseNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from . import StateContainerNode


class StateNode(TreeNode):
    """Node representing a module-level state variable."""
    
    def __init__(self, target_ast: ast.Name, parent: BaseNode):
        if not target_ast:
            raise ValueError("StateNode requires valid ast.Name target")
        if not isinstance(target_ast, ast.Name):
            raise ValueError("StateNode requires ast.Name node")
        
        # Pure self-extraction from target AST
        super().__init__(target_ast.id, parent, target_ast)
    
    @property
    def assignment_ast(self) -> ast.AST:
        """Get complete assignment AST from parent container."""
        if hasattr(self.parent, 'ast_node'):
            return self.parent.ast_node
        raise AttributeError("StateNode parent must have ast_node for assignment context")
    
    def list_all(self) -> dict:
        """Get comprehensive state variable information."""
        return {
            'name': self.name,
            'line_number': self.line_number
        }