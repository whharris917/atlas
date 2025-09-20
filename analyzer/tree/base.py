"""
Tree Base Classes - Atlas Rewrite

Core base class for all tree nodes with dynamic FQN generation.
"""

import ast
from typing import Optional


class TreeNode:
    """Base class for all tree nodes."""
    
    def __init__(self, name: str, ast_node: Optional[ast.AST] = None):
        self.name = name
        self.ast_node = ast_node
        self.parent: Optional['TreeNode'] = None
    
    @property
    def fqn(self) -> str:
        """Generate FQN by walking up the tree."""
        parts = [self.name]
        current = self.parent
        # Check by class name to avoid circular import
        while current and current.__class__.__name__ != 'ProjectNode':
            parts.append(current.name)
            current = current.parent
        return ".".join(reversed(parts))
    
    def __repr__(self) -> str:
        """Nice string representation showing node type and FQN."""
        node_type = self.__class__.__name__.replace('Node', '')
        return f"{node_type}({self.fqn})"