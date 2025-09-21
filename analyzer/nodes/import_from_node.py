"""
Import From Node - Atlas Rewrite

Node representing a from-import statement (ast.ImportFrom).
Creates AliasNodes for each import in the statement.
Examples: from os import path, from os.path import join, exists as path_exists
"""

import ast
from typing import Dict, List, TYPE_CHECKING
from ..core import TreeNode

if TYPE_CHECKING:
    from . import AliasNode


class ImportFromNode(TreeNode):
    """Node representing a from-import statement with automatic alias creation."""
    
    def __init__(self, ast_node: ast.ImportFrom):
        if not ast_node:
            raise ValueError("ImportFromNode requires valid ast.ImportFrom node")
        if not isinstance(ast_node, ast.ImportFrom):
            raise ValueError("ImportFromNode requires ast.ImportFrom node, not ast.Import")
        
        super().__init__("from_import", ast_node)
        self.from_module = ast_node.module or ""  # Module being imported from
        self._aliases: Dict[str, 'AliasNode'] = {}
        
        # Create all alias children immediately
        self._create_children()
    
    def _create_children(self):
        """Create AliasNode for each alias in the from-import statement."""
        print(f"    Creating aliases for from-import statement")
        
        for alias in self.ast_node.names:
            self._create_alias(alias)
    
    def _create_alias(self, alias: ast.alias) -> 'AliasNode':
        """Create and hook a new AliasNode."""
        from . import AliasNode
        alias_node = AliasNode(alias, "from_import", self.from_module)
        alias_node.parent = self
        self._aliases[alias_node.name] = alias_node
        print(f"      Found alias: {alias_node.name} -> {alias_node.module_name}")
        return alias_node
    
    def get_alias(self, name: str) -> 'AliasNode':
        """Get an alias by local name."""
        if name not in self._aliases:
            raise KeyError(f"Alias '{name}' not found in from-import statement")
        return self._aliases[name]
    
    def list_aliases(self) -> List['AliasNode']:
        """List all aliases in this from-import statement."""
        return list(self._aliases.values())