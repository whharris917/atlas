"""
Core Base Classes - Atlas Rewrite

Foundation classes for all tree nodes with dynamic FQN generation.
Updated to handle ContainerNode parents in FQN hierarchy.
"""

import ast
from typing import Optional


class TreeNode:
    """Base class for all tree nodes."""
    
    def __init__(self, name: str, ast_node: Optional[ast.AST] = None):
        if not name:
            raise ValueError(f"{self.__class__.__name__} requires non-empty name")
        
        self.name = name
        self.ast_node = ast_node
        self.parent = None
    
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