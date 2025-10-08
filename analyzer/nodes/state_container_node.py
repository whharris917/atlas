"""
State Container Node - Atlas Rewrite

Container node for module-level assignment statements.
Creates StateNode for each assignment target following Entity/Container pattern.
"""

import ast
from typing import List, Optional, Dict, Union
from ..core import ContainerNode, BaseNode
from .state_node import StateNode


class StateContainerNode(ContainerNode):
    """Container node for module-level assignment statements."""
    
    def __init__(self, parent: BaseNode, source_data: Union[ast.Assign, ast.AnnAssign]):
        if not isinstance(source_data, (ast.Assign, ast.AnnAssign)):
            raise TypeError("StateContainerNode requires ast.Assign or ast.AnnAssign as source_data")
        
        # Initialize collections before parent init (which calls _create_children)
        self._state_variables: List[StateNode] = []
        
        # Parent class handles initialization
        super().__init__(parent, source_data)
    
    def _create_children(self):
        """Create StateNode for each assignment target."""
        if isinstance(self.source_data, ast.Assign):
            # Regular assignment: x = y = z = 5
            for target in self.source_data.targets:
                if isinstance(target, ast.Name):
                    self._create_state_variable(target)
        elif isinstance(self.source_data, ast.AnnAssign):
            # Annotated assignment: x: int = 5
            if isinstance(self.source_data.target, ast.Name):
                self._create_state_variable(self.source_data.target)
    
    def analyze(self, parent_scope: Optional[Dict[str, str]] = None):
        """
        Analyze this state container and cascade to state nodes.
        
        State containers organize module-level assignments.
        """
        # Cascade to all state children
        for child in self._get_direct_children():
            child.analyze(parent_scope=parent_scope or {})

    def _create_state_variable(self, name_ast: ast.Name) -> StateNode:
        """Create and hook a new state variable from ast.Name target (internal use only)."""
        state_node = StateNode(parent=self, source_data=name_ast)
        self._state_variables.append(state_node)
        return state_node