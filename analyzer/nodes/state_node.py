"""
State Node - Atlas Rewrite

Node representing a module-level state variable.
Pure self-extracting from individual ast.Name target nodes.
Works exclusively with StateContainerNode - no legacy support.

File: analyzer/nodes/state_node.py
"""

import ast
from ..core import TreeNode


class StateNode(TreeNode):
    """Node representing a module-level state variable."""
    
    def __init__(self, target_ast: ast.Name, parent):
        if not isinstance(target_ast, ast.Name):
            raise ValueError("StateNode requires ast.Name target node")
        
        # Pure self-extraction from target AST
        super().__init__(target_ast.id, parent, target_ast)
    
    @property 
    def assignment_ast(self) -> ast.AST:
        """Get the original assignment AST from parent StateContainerNode."""
        return self.parent.ast_node
    
    @property
    def target_ast(self) -> ast.Name:
        """Get the target AST node for this specific variable."""
        return self.ast_node  # ast_node IS the target in this architecture
    
    @property
    def assignment_value_ast(self) -> ast.AST:
        """Get the assignment value AST for Analysis Phase."""
        assignment = self.assignment_ast
        if isinstance(assignment, ast.Assign):
            return assignment.value
        elif isinstance(assignment, ast.AnnAssign):
            return assignment.value
        return None
    
    @property 
    def type_annotation_ast(self) -> ast.AST:
        """Get type annotation AST for Analysis Phase (AnnAssign only)."""
        assignment = self.assignment_ast
        if isinstance(assignment, ast.AnnAssign):
            return assignment.annotation
        return None