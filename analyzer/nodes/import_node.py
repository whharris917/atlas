"""
Import Node - Atlas Rewrite

Container node for standard import statements (import x, y, z).
Creates AliasNode for each imported item.
"""

import ast
from typing import List, Optional
from ..core import ContainerNode, BaseNode
from .alias_node import AliasNode


class ImportNode(ContainerNode):
    """Container node for standard import statements."""
    
    def __init__(self, parent: BaseNode, source_data: ast.Import):
        if not isinstance(source_data, ast.Import):
            raise TypeError("ImportNode requires ast.Import as source_data")
        
        # Initialize collections before parent init (which calls _create_children)
        self._aliases: List[AliasNode] = []
        
        # Parent class handles initialization
        super().__init__(parent, source_data)
    
    def _create_children(self):
        """Create AliasNode for each imported name."""
        for alias_ast in self.source_data.names:
            self._create_alias(alias_ast)
    
    def _create_alias(self, alias_ast: ast.alias) -> AliasNode:
        """Create and hook a new alias from AST node (internal use only)."""
        alias_node = AliasNode(parent=self, source_data=alias_ast)
        self._aliases.append(alias_node)
        return alias_node