"""
Import Node - Atlas Rewrite

Container node for import statements with automatic alias creation.
Extremely focused implementation adhering to strict separation of concerns.
"""

import ast
from typing import List, TYPE_CHECKING
from ..core import ContainerNode, BaseNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from . import AliasNode


class ImportNode(ContainerNode):
    """Container node representing import statement (import x, y, z)."""
    
    def __init__(self, parent: BaseNode, ast_node: ast.Import):
        if not isinstance(ast_node, ast.Import):
            raise ValueError("ImportNode requires ast.Import node")
        
        # Initialize collections before parent init (which calls _create_children)
        self._aliases: List['AliasNode'] = []
        
        super().__init__(parent, ast_node)
    
    def _create_children(self):
        """Create alias nodes from import statement."""
        from . import AliasNode
        
        for alias in self.ast_node.names:
            alias_node = AliasNode(alias, parent=self)
            self._aliases.append(alias_node)
    
    def create_alias(self, alias_ast: ast.alias) -> 'AliasNode':
        """Create and hook a new alias from AST node."""
        from . import AliasNode
        alias_node = AliasNode(alias_ast, parent=self)
        self._aliases.append(alias_node)
        return alias_node