"""
Type Node - Atlas Rewrite

Node representing a type annotation with comprehensive type analysis.
Extremely focused implementation adhering to strict separation of concerns.
"""

import ast
from ..core import TreeNode, BaseNode


class TypeNode(TreeNode):
    """Node representing a type annotation."""
    
    def __init__(self, parent: BaseNode, source_data: ast.AST):
        if not isinstance(source_data, ast.AST):
            raise TypeError("TypeNode requires ast.AST as source_data")
        
        # Parent class handles name extraction and validation
        super().__init__(parent, source_data)
    
    def _extract_name(self) -> str:
        """Extract type representation from AST node."""
        try:
            return ast.unparse(self.source_data)
        except Exception:
            # Fallback for complex types that can't be unparsed
            return f"<{type(self.source_data).__name__}>"
    
    def _create_children(self):
        """TypeNode is a leaf node - no children to create."""
        pass