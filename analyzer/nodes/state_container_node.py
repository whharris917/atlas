"""
State Container Node - Atlas Rewrite

ContainerNode for module-level assignment statements.
Creates individual StateNodes for each assignment target.
Pure StateContainerNode architecture - no backward compatibility.

File: analyzer/nodes/state_container_node.py
"""

import ast
from typing import List, TYPE_CHECKING
from ..core import ContainerNode

if TYPE_CHECKING:
    from .state_node import StateNode


class StateContainerNode(ContainerNode):
    """
    Container for module-level assignment statements.
    Creates StateNode children for each assignment target.
    Eliminates arbitrary target[0] selection completely.
    """
    
    def __init__(self, parent, ast_node: ast.AST):
        if not isinstance(ast_node, (ast.Assign, ast.AnnAssign)):
            raise ValueError("StateContainerNode requires ast.Assign or ast.AnnAssign node")
        
        self.children: List['StateNode'] = []
        super().__init__(parent, ast_node)  # This calls _create_children()
    
    def _create_children(self):
        """Create StateNode for each assignment target."""
        if isinstance(self.ast_node, ast.Assign):
            # Handle: x = y = z = value (multiple targets)
            for target in self.ast_node.targets:
                if isinstance(target, ast.Name):
                    state_node = self._create_state_node(target)
                    self.children.append(state_node)
        
        elif isinstance(self.ast_node, ast.AnnAssign):
            # Handle: x: Type = value (single target)
            if isinstance(self.ast_node.target, ast.Name):
                state_node = self._create_state_node(self.ast_node.target)
                self.children.append(state_node)
    
    def _create_state_node(self, target_ast: ast.Name) -> 'StateNode':
        """Create individual StateNode from target AST."""
        from .state_node import StateNode
        return StateNode(target_ast, parent=self)
    
    def list_state_variables(self) -> List['StateNode']:
        """List all state variables created by this assignment."""
        return self.children
    
    def get_state_variable(self, name: str) -> 'StateNode':
        """Get state variable by name."""
        for state in self.children:
            if state.name == name:
                return state
        raise KeyError(f"State variable '{name}' not found in assignment container")
    
    def __repr__(self) -> str:
        """Representation for debugging."""
        assignment_type = type(self.ast_node).__name__
        var_count = len(self.children)
        if var_count == 1:
            return f"StateContainer({assignment_type}, {self.children[0].name})"
        else:
            names = [child.name for child in self.children]
            return f"StateContainer({assignment_type}, [{', '.join(names)}])"