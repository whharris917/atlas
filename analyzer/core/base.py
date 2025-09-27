"""
Core Base Classes - Atlas Rewrite

Foundation classes for all tree nodes with refined hierarchy.
BaseNode provides shared functionality with enhanced query-based navigation system.
RootNode for parentless nodes, TreeNode for entities requiring parents, 
ContainerNode for AST artifacts.

REORGANIZED: Navigation system extracted to navigation.py for focused organization.
Core hierarchy classes remain here with BaseNode as the primary integration class.
"""

import ast
from typing import Optional

from .navigation import NavigationMixin

class BaseNode(NavigationMixin):
    """Foundation for all Atlas nodes with shared functionality and enhanced navigation."""
    
    def __init__(self, ast_node: Optional[ast.AST] = None):
        self.ast_node = ast_node
    
    @property
    def line_number(self) -> int:
        """Get line number from AST node, or 0 if not available."""
        if self.ast_node:
            return getattr(self.ast_node, 'lineno', 0)
        return 0
    
    def __repr__(self) -> str:
        """Nice string representation showing node type."""
        node_type = self.__class__.__name__.replace('Node', '')
        if hasattr(self, 'name'):
            return f"{node_type}({self.name})"
        return f"{node_type}()"

class RootNode(BaseNode):
    """Base for nodes that can exist without parents (project roots)."""
    
    def __init__(self, name: str, ast_node: Optional[ast.AST] = None):
        super().__init__(ast_node)
        self.name = name
        self.parent = None
        self._create_children()
    
    def _create_children(self):
        """Initialize child collections. Override in subclasses."""
        pass

class TreeNode(BaseNode):
    """Named entities with mandatory parent relationships."""
    
    def __init__(self, name: str, parent: 'BaseNode', ast_node: Optional[ast.AST] = None):
        super().__init__(ast_node)
        self.name = name
        self.parent = parent
        self._create_children()
    
    def _create_children(self):
        """Initialize child collections. Override in subclasses."""
        pass
    
    @property
    def fqn(self) -> str:
        """Generate Fully Qualified Name by walking up the parent chain."""
        parts = []
        current = self
        while current:
            if hasattr(current, 'name'):
                parts.append(current.name)
            current = getattr(current, 'parent', None)
        return ".".join(reversed(parts))

class ContainerNode(BaseNode):
    """AST parsing artifacts that group related items but have no meaningful identity."""
    
    def __init__(self, parent: 'BaseNode', ast_node: Optional[ast.AST] = None):
        super().__init__(ast_node)
        self.parent = parent
        self._create_children()
    
    def _create_children(self):
        """Initialize child collections. Override in subclasses."""
        pass