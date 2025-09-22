"""
Container Node - Atlas Rewrite

Base class for nodes that exist solely to contain and create children.
These nodes represent AST parsing artifacts rather than named code entities.
"""

import ast
from typing import Optional


class ContainerNode:
    """
    Base class for nodes that exist solely as containers for other entities.
    
    ContainerNodes represent AST structural artifacts (like import statements)
    rather than named code entities. They have no meaningful individual identity
    and exist only to parse AST structures and create their child entities.
    """
    
    def __init__(self, ast_node: ast.AST):
        if not ast_node:
            raise ValueError(f"{self.__class__.__name__} requires valid AST node")
        
        self.ast_node = ast_node
        self.parent = None
        
        # Create all children immediately (self-creating pattern)
        self._create_children()
    
    def _create_children(self):
        """Create child entities from AST structure. Must be implemented by subclasses."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement _create_children()")
    
    @property
    def line_number(self) -> int:
        """Get line number from AST node, or 0 if not available."""
        if self.ast_node:
            return getattr(self.ast_node, 'lineno', 0)
        return 0
    
    def __repr__(self) -> str:
        """String representation showing container type and basic info."""
        container_type = self.__class__.__name__.replace('Node', '')
        return f"{container_type}Container(line {self.line_number})"