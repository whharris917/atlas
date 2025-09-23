"""
Core Base Classes - Atlas Rewrite

Foundation classes for all tree nodes with mandatory parent relationships.
BREAKING CHANGE: All TreeNodes except ProjectNode must specify parent at construction.
"""

import ast
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Self


class TreeNode:
    """Base class for all tree nodes with mandatory parent relationship."""
    
    def __init__(self, name: str, parent: Optional['TreeNode'] = None, ast_node: Optional[ast.AST] = None):
        if not name:
            raise ValueError(f"{self.__class__.__name__} requires non-empty name")
        
        # CRITICAL: All nodes except ProjectNode must have a parent
        if parent is None and self.__class__.__name__ != 'ProjectNode':
            raise ValueError(f"{self.__class__.__name__} requires parent - only ProjectNode can be parentless")
        
        self.name = name
        self.parent = parent
        self.ast_node = ast_node
    
    @property
    def fqn(self) -> str:
        """Generate FQN by walking up the tree, skipping ContainerNodes."""
        parts = [self.name]
        current = self.parent
        
        # Walk up the hierarchy, skipping ContainerNodes (they don't contribute to FQN)
        while current and current.__class__.__name__ != 'ProjectNode':
            # Only include TreeNodes in FQN, skip ContainerNodes
            if hasattr(current, 'name') and current.name:
                parts.append(current.name)
            current = current.parent
        
        return ".".join(reversed(parts))
    
    @property
    def line_number(self) -> int:
        """Get line number from AST node, or 0 if not available."""
        if self.ast_node:
            return getattr(self.ast_node, 'lineno', 0)
        return 0
    
    def __repr__(self) -> str:
        """Nice string representation showing node type and FQN."""
        node_type = self.__class__.__name__.replace('Node', '')
        return f"{node_type}({self.fqn})"


class ContainerNode:
    """Base for nodes that exist solely to contain and create children."""
    
    def __init__(self, parent: TreeNode, ast_node: ast.AST):
        if not parent:
            raise ValueError(f"{self.__class__.__name__} requires parent TreeNode")
        if not ast_node:
            raise ValueError(f"{self.__class__.__name__} requires valid AST node")
        
        self.parent = parent
        self.ast_node = ast_node
        self._create_children()  # Always create children immediately
    
    def _create_children(self):
        """Subclasses implement child creation logic."""
        raise NotImplementedError
    
    @property
    def line_number(self) -> int:
        """Get line number from AST node, or 0 if not available."""
        if self.ast_node:
            return getattr(self.ast_node, 'lineno', 0)
        return 0