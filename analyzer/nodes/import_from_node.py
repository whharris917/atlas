"""
Import From Node - Atlas Rewrite

ContainerNode representing a from-import statement.
Creates all AliasNodes immediately.
"""

import ast
from typing import List, TYPE_CHECKING
from ..core import ContainerNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from . import AliasNode
    from ..core import TreeNode


class ImportFromNode(ContainerNode):
    """ContainerNode representing a from-import statement."""
    
    def __init__(self, parent: 'TreeNode', ast_node: ast.ImportFrom):
        if not isinstance(ast_node, ast.ImportFrom):
            raise ValueError("ImportFromNode requires ast.ImportFrom node")
        
        # Initialize _aliases BEFORE calling super() because ContainerNode.__init__ calls _create_children immediately
        self._aliases: List['AliasNode'] = []
        super().__init__(parent, ast_node)
    
    def _create_children(self):
        """Create AliasNodes for each imported name."""
        
        print(f"    Creating aliases in from-import statement")
        
        module_name = self.ast_node.module or ""
        for alias in self.ast_node.names:
            if alias.name == "*":
                # Handle wildcard imports
                full_name = f"{module_name}.*"
                self.create_alias(alias, full_name)
            else:
                full_name = f"{module_name}.{alias.name}" if module_name else alias.name
                self.create_alias(alias, full_name)
    
    def create_alias(self, alias_ast: ast.alias, full_name: str) -> 'AliasNode':
        """Create and hook an alias from from-import."""
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
        raise KeyError(f"Alias '{name}' not found in from-import statement")
    
    def list_aliases(self) -> List['AliasNode']:
        """List all aliases created by this from-import."""
        return self._aliases
    
    def __repr__(self) -> str:
        """Enhanced string representation showing from module."""
        module_name = self.ast_node.module or ""
        if module_name:
            return f"ImportFromContainer(from {module_name}, line {self.line_number})"
        else:
            return f"ImportFromContainer(line {self.line_number})"