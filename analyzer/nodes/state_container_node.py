"""
State Container Node - Atlas Rewrite

Container for assignment statements that creates individual StateNode children.
Implements universal Entity/Container pattern for state variable handling.
Eliminates arbitrary target[0] selection in favor of complete multi-target support.
"""

import ast
from typing import List, TYPE_CHECKING
from ..core import ContainerNode, BaseNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from . import StateNode


class StateContainerNode(ContainerNode):
    """Container for assignment statements that creates StateNode children."""
    
    def __init__(self, parent: BaseNode, ast_node: ast.AST):
        # Initialize children list before parent init (which calls _create_children)
        self.children: List['StateNode'] = []
        
        super().__init__(parent, ast_node)
    
    def _create_children(self):
        """Create StateNode for each assignment target."""
        from . import StateNode
        
        # Handle different assignment types
        if isinstance(self.ast_node, ast.Assign):
            # Regular assignment: x = y = z = 42
            for target in self.ast_node.targets:
                if isinstance(target, ast.Name):
                    state_node = StateNode(target, parent=self)
                    self.children.append(state_node)
        
        elif isinstance(self.ast_node, ast.AnnAssign):
            # Annotated assignment: x: int = 42
            if isinstance(self.ast_node.target, ast.Name):
                state_node = StateNode(self.ast_node.target, parent=self)
                self.children.append(state_node)
    
    def list_state_variables(self) -> List['StateNode']:
        """Get all StateNodes created by this assignment."""
        return self.children
    
    def get_state_variable(self, name: str) -> 'StateNode':
        """Get a specific StateNode by name."""
        for state_node in self.children:
            if state_node.name == name:
                return state_node
        raise KeyError(f"State variable '{name}' not found in assignment")
    
    def __repr__(self) -> str:
        """String representation showing assignment type and targets."""
        target_names = [state.name for state in self.children]
        if len(target_names) == 1:
            return f"StateContainer({target_names[0]})"
        else:
            return f"StateContainer({', '.join(target_names)})"