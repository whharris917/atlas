"""
Alias Node - Atlas Rewrite

Node representing an imported name (alias) from import statements.
Extremely focused implementation adhering to strict separation of concerns.
"""

import ast
from typing import Optional, Dict
from ..core import TreeNode, BaseNode


class AliasNode(TreeNode):
    """Node representing an imported name (alias)."""
    
    def __init__(self, parent: BaseNode, source_data: ast.alias):
        if not isinstance(source_data, ast.alias):
            raise TypeError("AliasNode requires ast.alias as source_data")
        
        # Parent class handles name extraction and validation
        super().__init__(parent, source_data)
    
    def _extract_name(self) -> str:
        """Extract alias name from ast.alias node."""
        # Use asname if provided, otherwise use the actual import name
        return self.source_data.asname if self.source_data.asname else self.source_data.name
    
    def _create_children(self):
        """AliasNode is a leaf node - no children to create."""
        pass

    def analyze(self, parent_scope: Optional[Dict[str, str]] = None):
        """
        Analyze this alias node (import alias).
        
        Alias nodes are leaf nodes representing import names.
        No analysis needed.
        """
        # No analysis needed (leaf node, no children)
        pass