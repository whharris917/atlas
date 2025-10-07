"""
State Node - Atlas Rewrite

Node representing a module-level state variable with pure self-extracting architecture.
Extremely focused implementation adhering to strict separation of concerns.
"""

import ast
from typing import Optional, Dict
from ..core import TreeNode, BaseNode


class StateNode(TreeNode):
    """Node representing a module-level state variable."""
    
    def __init__(self, parent: BaseNode, source_data: ast.AST):
        if not isinstance(source_data, ast.AST):
            raise TypeError("StateNode requires ast.AST as source_data")
        
        # Parent class handles name extraction and validation
        super().__init__(parent, source_data)
    
    def _extract_name(self) -> str:
        """Extract variable name from AST node."""
        # Handle ast.Name (typical case for simple assignments)
        if isinstance(self.source_data, ast.Name):
            return self.source_data.id
        # Could extend to handle other cases in the future
        raise ValueError(f"StateNode cannot extract name from {type(self.source_data).__name__}")
    
    def _create_children(self):
        """StateNode is a leaf node - no children to create."""
        pass

    def analyze(self, parent_scope: Optional[Dict[str, str]] = None):
        """
        Analyze this state node (module-level assignment).
        
        State nodes are leaf nodes representing assignments.
        Future analysis may track variable type evolution.
        """
        # No analysis needed yet (leaf node)
        # Cascade to children (TypeNode if present)
        for child in self._get_direct_children():
            child.analyze(parent_scope=parent_scope or {})