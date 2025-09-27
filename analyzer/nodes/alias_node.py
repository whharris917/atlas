"""
Alias Node - Atlas Rewrite

Node representing an import alias with module resolution.
Extremely focused implementation adhering to strict separation of concerns.
"""

import ast
from typing import TYPE_CHECKING
from ..core import TreeNode, BaseNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    pass


class AliasNode(TreeNode):
    """Node representing an import alias."""
    
    def __init__(self, parent: BaseNode, source_data: ast.alias):
        if not isinstance(source_data, ast.alias):
            raise TypeError("AliasNode requires ast.alias as source_data")
        
        # Parent class handles name extraction and validation
        super().__init__(parent, source_data)
    
    def _extract_name(self) -> str:
        """Extract alias name (asname if present, otherwise original name)."""
        # Use alias name if present, otherwise use the original import name
        return self.source_data.asname or self.source_data.name
    
    def _create_children(self):
        """AliasNode is a leaf node - no children to create."""
        pass
    
    @property
    def full_name(self) -> str:
        """Get the full module name being imported."""
        # Check if this alias is part of a from-import
        if hasattr(self.parent, 'source_data') and isinstance(self.parent.source_data, ast.ImportFrom):
            module = self.parent.source_data.module
            if module:
                return f"{module}.{self.source_data.name}"
            else:
                # Relative import
                return self.source_data.name
        else:
            # Direct import
            return self.source_data.name