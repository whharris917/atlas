"""
State Container Node - Atlas Rewrite

Container node for module-level assignment statements.
Creates StateNode for each assignment target following Entity/Container pattern.
"""

import ast
from typing import List, TYPE_CHECKING
from ..core import ContainerNode, BaseNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from .state_node import StateNode


class StateContainerNode(ContainerNode):
    """Container node for module-level assignment statements."""
    
    def __init__(self, parent: BaseNode, source_data: ast.Assign):
        if not isinstance(source_data, ast.Assign):
            raise TypeError("StateContainerNode requires ast.Assign as source_data")
        
        # Initialize collections before parent init (which calls _create_children)
        self._state_variables: List['StateNode'] = []
        
        # Parent class handles initialization
        super().__init__(parent, source_data)
    
    def _create_children(self):
        """Create StateNode for each assignment target."""
        for target in self.source_data.targets:
            if isinstance(target, ast.Name):
                self.create_state_variable(target)
            # Note: Could extend to handle other target types like ast.Tuple for unpacking
    
    def create_state_variable(self, name_ast: ast.Name) -> 'StateNode':
        """Create and hook a new state variable from ast.Name target."""
        from .state_node import StateNode
        state_node = StateNode(parent=self, source_data=name_ast)
        self._state_variables.append(state_node)
        return state_node