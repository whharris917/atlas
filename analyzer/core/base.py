"""
Core Base Classes - Atlas Rewrite

Foundation classes for all tree nodes with refined hierarchy.
BaseNode provides shared functionality, RootNode for parentless nodes,
TreeNode for entities requiring parents, ContainerNode for AST artifacts.
"""

import ast
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    pass  # Remove unused Self import


class BaseNode:
    """Foundation for all Atlas nodes with shared functionality."""
    
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
        if not name:
            raise ValueError(f"{self.__class__.__name__} requires non-empty name")
        
        super().__init__(ast_node)
        self.name = name
        self.parent = None
        
        # Automatic child creation
        self._create_children()
    
    def _create_children(self):
        """Subclasses implement child creation logic. Base does nothing."""
        pass  # Default implementation does nothing
    
    @property
    def fqn(self) -> str:
        """Root nodes have FQN equal to their name."""
        return self.name


class TreeNode(BaseNode):
    """Base class for named entities with mandatory parent relationships."""
    
    def __init__(self, name: str, parent: BaseNode, ast_node: Optional[ast.AST] = None):
        if not name:
            raise ValueError(f"{self.__class__.__name__} requires non-empty name")
        if not parent:
            raise ValueError(f"{self.__class__.__name__} requires parent")
        
        super().__init__(ast_node)
        self.name = name
        self.parent = parent
        
        # Automatic child creation
        self._create_children()
    
    def _create_children(self):
        """Subclasses implement child creation logic. Base does nothing."""
        pass  # Default implementation does nothing (for leaf nodes)
    
    @property
    def fqn(self) -> str:
        """Generate FQN by walking up the tree, skipping ContainerNodes."""
        parts = [self.name]
        current = self.parent
        
        # Walk up the hierarchy, skipping ContainerNodes (they don't contribute to FQN)
        while current and not isinstance(current, RootNode):
            # Only include nodes with names in FQN, skip ContainerNodes
            if hasattr(current, 'name') and current.name:
                parts.append(current.name)
            current = getattr(current, 'parent', None)
        
        # Add root name if it exists
        if current and hasattr(current, 'name'):
            parts.append(current.name)
        
        return ".".join(reversed(parts))
    
    def __repr__(self) -> str:
        """Nice string representation showing node type and FQN."""
        node_type = self.__class__.__name__.replace('Node', '')
        return f"{node_type}({self.fqn})"


class ContainerNode(BaseNode):
    """Base for nodes that exist solely to contain and create children."""
    
    def __init__(self, parent: BaseNode, ast_node: ast.AST):
        if not parent:
            raise ValueError(f"{self.__class__.__name__} requires parent")
        if not ast_node:
            raise ValueError(f"{self.__class__.__name__} requires valid AST node")
        
        super().__init__(ast_node)
        self.parent = parent
        self._create_children()  # Always create children immediately
    
    def _create_children(self):
        """Subclasses implement child creation logic."""
        raise NotImplementedError