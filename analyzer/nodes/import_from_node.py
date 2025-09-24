"""
Import From Node - Atlas Rewrite

Container node for import-from statements with automatic alias creation.
Extremely focused implementation adhering to strict separation of concerns.
"""

import ast
from typing import List, TYPE_CHECKING
from ..core import ContainerNode, BaseNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from . import AliasNode


class ImportFromNode(ContainerNode):
    """Container node representing from-import statement (from x import y, z)."""
    
    def __init__(self, parent: BaseNode, ast_node: ast.ImportFrom):
        if not isinstance(ast_node, ast.ImportFrom):
            raise ValueError("ImportFromNode requires ast.ImportFrom node")
        
        # Initialize collections before parent init (which calls _create_children)
        self._aliases: List['AliasNode'] = []
        
        super().__init__(parent, ast_node)
    
    def _create_children(self):
        """Create alias nodes from import-from statement."""
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