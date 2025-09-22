"""
Import Node - Atlas Rewrite

Container for simple import statements (ast.Import).
Creates AliasNodes for each import in the statement.
Examples: import requests, import os, sys as system
"""

import ast
from typing import Dict, List, TYPE_CHECKING
from ..core import ContainerNode

if TYPE_CHECKING:
    from . import AliasNode


class ImportNode(ContainerNode):
    """Container for simple import statements with automatic alias creation."""
    
    def __init__(self, ast_node: ast.Import):
        if not isinstance(ast_node, ast.Import):
            raise ValueError("ImportNode requires ast.Import node, not ast.ImportFrom")
        
        self._aliases: Dict[str, 'AliasNode'] = {}
        super().__init__(ast_node)
    
    def _create_children(self):
        """Create AliasNode for each alias in the import statement."""
        print(f"    Creating aliases for import statement")
        
        for alias in self.ast_node.names:
            self._create_alias(alias)
    
    def _create_alias(self, alias: ast.alias) -> 'AliasNode':
        """Create and hook a new AliasNode."""
        from . import AliasNode
        alias_node = AliasNode(alias, "import")
        alias_node.parent = self
        self._aliases[alias_node.name] = alias_node
        print(f"      Found alias: {alias_node.name} -> {alias_node.module_name}")
        return alias_node
    
    def get_alias(self, name: str) -> 'AliasNode':
        """Get an alias by local name."""
        if name not in self._aliases:
            raise KeyError(f"Alias '{name}' not found in import statement")
        return self._aliases[name]
    
    def list_aliases(self) -> List['AliasNode']:
        """List all aliases in this import statement."""
        return list(self._aliases.values())