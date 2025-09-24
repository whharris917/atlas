"""
State Container Node - Atlas Rewrite

Container node for assignment statements with automatic state variable creation.
Extremely focused implementation adhering to strict separation of concerns.
"""

import ast
from typing import List, TYPE_CHECKING
from ..core import ContainerNode, BaseNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from . import StateNode


class StateContainerNode(ContainerNode):
    """Container node representing assignment statement with multiple targets."""
    
    def __init__(self, parent: BaseNode, ast_node: ast.Assign):
        if not isinstance(ast_node, ast.Assign):
            raise ValueError("StateContainerNode requires ast.Assign node")
        
        # Initialize collections before parent init (which calls _create_children)
        self._state_variables: List['StateNode'] = []
        
        super().__init__(parent, ast_node)
    
    def _create_children(self):
        """Create StateNode for each target in assignment."""
        from . import StateNode
        
        for target in self.ast_node.targets:
            if isinstance(target, ast.Name):
                state_node = StateNode(target.id, parent=self, ast_node=target)
                self._state_variables.append(state_node)
    
    def create_state_variable(self, name: str, ast_node: ast.AST) -> 'StateNode':
        """Create and hook a new state variable."""
        from . import StateNode
        state_node = StateNode(name, parent=self, ast_node=ast_node)
        self._state_variables.append(state_node)
        return state_node