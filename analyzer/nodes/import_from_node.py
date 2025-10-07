"""
Import From Node - Atlas Rewrite

Container node for from-import statements (from x import y, z).
Creates AliasNode for each imported item.
"""

import ast
from typing import List, Optional, Dict
from ..core import ContainerNode, BaseNode
from .alias_node import AliasNode


class ImportFromNode(ContainerNode):
    """Container node for from-import statements."""
    
    def __init__(self, parent: BaseNode, source_data: ast.ImportFrom):
        if not isinstance(source_data, ast.ImportFrom):
            raise TypeError("ImportFromNode requires ast.ImportFrom as source_data")
        
        # Initialize collections before parent init (which calls _create_children)
        self._aliases: List[AliasNode] = []
        
        # Parent class handles initialization
        super().__init__(parent, source_data)
    
    def _create_children(self):
        """Create AliasNode for each imported name."""
        for alias_ast in self.source_data.names:
            self._create_alias(alias_ast)
    
    def analyze(self, parent_scope: Optional[Dict[str, str]] = None):
        """
        Analyze this import-from container and cascade to aliases.
        
        Import-from containers organize alias nodes.
        """
        # Cascade to all alias children
        for child in self._get_direct_children():
            child.analyze(parent_scope=parent_scope or {})

    def _create_alias(self, alias_ast: ast.alias) -> AliasNode:
        """Create and hook a new alias from AST node (internal use only)."""
        alias_node = AliasNode(parent=self, source_data=alias_ast)
        self._aliases.append(alias_node)
        return alias_node