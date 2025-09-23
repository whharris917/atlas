"""
Alias Node - Atlas Rewrite

Node representing an import alias with pure self-extracting architecture.
Self-extracts name and calculates full_name from parent context.
Pure architecture - no redundant parameters.
"""

import ast
from typing import Optional, TYPE_CHECKING
from ..core import TreeNode, BaseNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    pass


class AliasNode(TreeNode):
    """Node representing an import alias."""
    
    def __init__(self, alias_ast: ast.alias, parent: BaseNode):
        if not alias_ast:
            raise ValueError("AliasNode requires valid ast.alias node")
        if not isinstance(alias_ast, ast.alias):
            raise ValueError("AliasNode requires ast.alias node")
        
        # Use alias name if provided, otherwise use the imported name
        display_name = alias_ast.asname if alias_ast.asname else alias_ast.name
        
        # Pure self-extraction from AST
        super().__init__(display_name, parent, alias_ast)
    
    @property
    def imported_name(self) -> str:
        """Get the actual name being imported (before any aliasing)."""
        return self.ast_node.name
    
    @property
    def alias_name(self) -> Optional[str]:
        """Get the alias name (after 'as'), if any."""
        return self.ast_node.asname
    
    @property
    def full_name(self) -> str:
        """Calculate full qualified name from parent import context."""
        if hasattr(self.parent, 'ast_node'):
            parent_ast = self.parent.ast_node
            
            if isinstance(parent_ast, ast.ImportFrom):
                # from package.module import name
                module = parent_ast.module or ""
                if module:
                    return f"{module}.{self.imported_name}"
                else:
                    return self.imported_name
            else:
                # import name
                return self.imported_name
        else:
            return self.imported_name
    
    def list_all(self) -> dict:
        """Get comprehensive alias information."""
        return {
            'name': self.name,
            'imported_name': self.imported_name,
            'alias_name': self.alias_name,
            'full_name': self.full_name,
            'line_number': self.line_number
        }