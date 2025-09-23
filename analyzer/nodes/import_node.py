"""
Import Node - Atlas Rewrite

ContainerNode representing an import statement.
Creates all AliasNodes immediately.
"""

import ast
from typing import List, TYPE_CHECKING
from ..core import ContainerNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from . import AliasNode
    from ..core import TreeNode


class ImportNode(ContainerNode):
    """ContainerNode representing an import statement."""
    
    def __init__(self, parent: 'TreeNode', ast_node: ast.Import):
        if not isinstance(ast_node, ast.Import):
            raise ValueError("ImportNode requires ast.Import node")
        
        # Initialize _aliases BEFORE calling super() because ContainerNode.__init__ calls _create_children immediately
        self._aliases: List['AliasNode'] = []
        super().__init__(parent, ast_node)
    
    def _create_children(self):
        """Create AliasNodes for each imported name."""
        
        print(f"    Creating aliases in import statement")
        
        for alias in self.ast_node.names:
            self.create_alias(alias, alias.name)
    
    def create_alias(self, alias_ast: ast.alias, full_name: str) -> 'AliasNode':
        """Create and hook an alias from import."""
        from . import AliasNode
        alias_name = alias_ast.asname if alias_ast.asname else alias_ast.name
        alias_node = AliasNode(alias_name, parent=self.parent, full_name=full_name, ast_node=alias_ast)
        self._aliases.append(alias_node)
        return alias_node
    
    def get_alias(self, name: str) -> 'AliasNode':
        """Get an alias by local name."""
        for alias in self._aliases:
            if alias.name == name:
                return alias
        raise KeyError(f"Alias '{name}' not found in import statement")
    
    def list_aliases(self) -> List['AliasNode']:
        """List all aliases created by this import."""
        return self._aliases