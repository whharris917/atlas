"""
Import From Node - Atlas Rewrite

Container node for from-import statements (from x import y, z).
Creates AliasNode for each imported item.
"""

import ast
from typing import List, Optional, TYPE_CHECKING
from ..core import ContainerNode, BaseNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from .alias_node import AliasNode


class ImportFromNode(ContainerNode):
    """Container node for from-import statements."""
    
    def __init__(self, parent: BaseNode, source_data: ast.ImportFrom):
        if not isinstance(source_data, ast.ImportFrom):
            raise TypeError("ImportFromNode requires ast.ImportFrom as source_data")
        
        # Initialize collections before parent init (which calls _create_children)
        self._aliases: List['AliasNode'] = []
        
        # Parent class handles initialization
        super().__init__(parent, source_data)
    
    def _create_children(self):
        """Create AliasNode for each imported name."""
        for alias_ast in self.source_data.names:
            self.create_alias(alias_ast)
    
    def create_alias(self, alias_ast: ast.alias) -> 'AliasNode':
        """Create and hook a new alias from AST node."""
        from .alias_node import AliasNode
        alias_node = AliasNode(parent=self, source_data=alias_ast)
        self._aliases.append(alias_node)
        return alias_node