"""
Attribute Node - Atlas Rewrite

Node representing a class attribute with type analysis.
Extremely focused implementation adhering to strict separation of concerns.
"""

import ast
from typing import Optional, TYPE_CHECKING
from ..core import TreeNode, BaseNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from .type_node import TypeNode


class AttributeNode(TreeNode):
    """Node representing a class attribute."""
    
    def __init__(self, parent: BaseNode, source_data: ast.AnnAssign):
        if not isinstance(source_data, ast.AnnAssign):
            raise TypeError("AttributeNode requires ast.AnnAssign as source_data")
        if not isinstance(source_data.target, ast.Name):
            raise ValueError("AttributeNode requires ast.AnnAssign with ast.Name target")
        
        # Initialize collections before parent init (which calls _create_children)
        self._type: Optional['TypeNode'] = None
        
        # Parent class handles name extraction and validation
        super().__init__(parent, source_data)
    
    def _extract_name(self) -> str:
        """Extract attribute name from ast.AnnAssign target."""
        return self.source_data.target.id
    
    def _create_children(self):
        """Create TypeNode child from annotation."""
        if self.source_data.annotation:
            self._create_type_node(self.source_data.annotation)
    
    def _create_type_node(self, type_ast: ast.AST) -> 'TypeNode':
        """Create TypeNode child from type annotation AST."""
        from .type_node import TypeNode
        self._type = TypeNode(parent=self, source_data=type_ast)
        return self._type