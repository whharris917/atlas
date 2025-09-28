"""
Core Base Classes - Atlas Static Analysis Framework

Foundation classes for all tree nodes in Atlas's self-creating project tree architecture.

This module provides the fundamental base classes that enable Atlas's elegant
self-creating cascade where a single ProjectNode creation results in complete
automatic discovery and representation of an entire Python codebase.

Classes:
    BaseNode: Universal foundation with shared functionality and enhanced navigation
    RootNode: Base for parentless nodes (project roots) 
    TreeNode: Named entities requiring parent relationships
    ContainerNode: AST parsing artifacts without meaningful identity

Architecture:
    BaseNode integrates with NavigationMixin to provide comprehensive tree navigation
    capabilities while maintaining clean separation between core hierarchy logic
    and navigation functionality. All nodes require source material for child
    creation, ensuring the self-creating cascade has the data needed for complete
    tree population.

Type Safety:
    All constructors enforce strict type validation with comprehensive isinstance
    checks and clear error messages. Union types are validated at runtime to
    ensure nodes receive appropriate source material for their child creation needs.
"""

import ast
from typing import Union, TYPE_CHECKING

from .navigation import NavigationMixin

if TYPE_CHECKING:
    from ..reconnaissance.discovery import ProjectStructure, DiscoveredModule, DiscoveredPackage

class BaseNode(NavigationMixin):
    """Foundation for all Atlas nodes with shared functionality and enhanced navigation."""
    
    def __init__(self, source_data: Union[ast.AST, 'ProjectStructure', 'DiscoveredModule', 'DiscoveredPackage']):
        """
        Initialize BaseNode with source data for child creation.
        
        Args:
            source_data: The source material used to create this node and its children.
                        Can be an AST node or a discovery data class.
                        
        Raises:
            ValueError: If source_data is None
            TypeError: If source_data is not one of the allowed types
        """
        if source_data is None:
            raise ValueError("BaseNode requires valid source_data (cannot be None)")
        
        # Validate source_data is one of the allowed types
        # Import here to avoid circular imports while still getting proper type checking
        from ..reconnaissance.discovery import ProjectStructure, DiscoveredModule, DiscoveredPackage
        
        if not isinstance(source_data, (ast.AST, ProjectStructure, DiscoveredModule, DiscoveredPackage)):
            raise TypeError(
                f"BaseNode source_data must be ast.AST, ProjectStructure, DiscoveredModule, "
                f"or DiscoveredPackage, got {type(source_data)}"
            )
            
        self.source_data = source_data
    
    @property
    def line_number(self) -> int:
        """Get line number from source data if it's an AST node, or 0 if not available."""
        if isinstance(self.source_data, ast.AST):
            return getattr(self.source_data, 'lineno', 0)
        return 0
    
    def get_depth(self) -> int:
        """
        Calculate depth within the project tree.
        
        ContainerNodes do not contribute to depth calculations, maintaining their
        "pass-through" quality just like in FQN generation. Only named entities
        with meaningful names contribute to depth.
        
        Returns:
            int: Depth of this node (0 for project root, 1 for modules, etc.)
            
        Examples:
            >>> # ProjectNode (root)
            >>> project.get_depth()
            0
            
            >>> # ModuleNode depth (no packages)
            >>> module.get_depth()  
            1
            
            >>> # ModuleNode depth (nested in packages)
            >>> deep_module.get_depth()
            3  # project -> pkg1 -> pkg2 -> module
            
            >>> # ClassNode depth  
            >>> class_node.get_depth()
            2  # project -> module -> class
            
            >>> # FunctionNode depth (method)
            >>> method.get_depth()
            3  # project -> module -> class -> method
            
            >>> # ContainerNodes don't add to depth
            >>> import_node.get_depth()
            2  # same as parent module (containers are pass-through)
        """
        depth = 0
        current = self.parent
        
        while current is not None:
            # Only count nodes with meaningful names (skip ContainerNodes)
            if hasattr(current, 'name') and current.name:
                depth += 1
            current = getattr(current, 'parent', None)
        
        return depth
    
    def _create_children(self):
        """
        Initialize child collections and trigger the self-creating cascade.
        
        This method is a fundamental architectural pillar of Atlas's self-creating
        tree generation system. By making child creation mandatory at construction
        time, Atlas ensures complete and automatic tree population with zero
        possibility of incomplete or missed entities.
        
        Implementation Pattern:
            Subclasses override this method to implement their specific child
            creation logic. This typically involves:
            1. Using visitors to discover entities in AST nodes
            2. Iterating over data structures to create children
            3. Conditionally creating type analysis nodes
        
        Design Philosophy:
            The entire Atlas tree self-populates automatically from a single
            ProjectNode creation. When you create the root, it creates packages,
            which create modules, which create classes, which create methods,
            which create arguments with type analysis - all automatically through
            the cascading execution of _create_children() at each level.
        
        Execution Timing:
            This method is called automatically during node construction, after
            all attributes are initialized but before the constructor returns.
            This ensures the tree is immediately navigable after construction.
        """
        pass  # Default: no children (leaf nodes override as needed)
    
    def __repr__(self) -> str:
        """Nice string representation showing node type and name if available."""
        node_type = self.__class__.__name__.replace('Node', '')
        if hasattr(self, 'name'):
            return f"{node_type}({self.name})"
        return f"{node_type}()"


class RootNode(BaseNode):
    """
    Base for parentless nodes like ProjectNode.
    
    Root nodes are the entry points to tree hierarchies and do not have parent
    relationships. They still require source material for child creation.
    """
    
    def __init__(self, source_data: 'ProjectStructure'):
        """
        Initialize a root node with comprehensive validation.
        
        Args:
            source_data: ProjectStructure containing project discovery data
            
        Raises:
            ValueError: If extracted name is invalid
            TypeError: If source_data is not ProjectStructure
        """
        # Validate source_data is ProjectStructure
        # Import here to avoid circular imports while still getting proper type checking
        from ..reconnaissance.discovery import ProjectStructure
        
        if not isinstance(source_data, ProjectStructure):
            raise TypeError(f"RootNode source_data must be ProjectStructure, got {type(source_data)}")
            
        super().__init__(source_data)
        self.parent = None  # RootNodes explicitly have no parent
        
        # Extract name from source_data
        self.name = self._extract_name()
        
        # Validate extracted name (including whitespace check)
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError(f"{self.__class__.__name__} extracted invalid name: {repr(self.name)}")
        
        self._create_children()
    
    def _extract_name(self) -> str:
        """
        Extract name from source_data.
        
        Subclasses must override this method to extract their name from
        the source_data provided during construction.
        
        Returns:
            str: The extracted name
            
        Raises:
            NotImplementedError: If subclass doesn't override this method
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement _extract_name()")
    
    @property
    def fqn(self) -> str:
        """Return just the name for root nodes."""
        return self.name


class TreeNode(BaseNode):
    """
    Named entities with parent relationships forming the project tree.
    
    TreeNodes represent meaningful Python entities (modules, classes, functions, etc.)
    that have names and exist within a hierarchical structure. They require both a valid parent
    and source material for child creation.
    """
    
    def __init__(self, parent: 'BaseNode', source_data: Union[ast.AST, 'DiscoveredModule', 'DiscoveredPackage']):
        """
        Initialize a tree node with comprehensive validation.
        
        Args:
            parent: Valid BaseNode parent (cannot be None)
            source_data: The source material used to create children.
                        - AST nodes (ast.ClassDef, ast.FunctionDef, etc.) for most entities
                        - DiscoveredModule for ModuleNode (combines name + ast.Module)
                        - DiscoveredPackage for PackageNode (combines name + ast.Module + children)
            
        Raises:
            ValueError: If parent is None or extracted name is invalid
            TypeError: If parent is not a BaseNode instance or source_data is invalid type
        """
        if parent is None:
            raise ValueError("TreeNode requires valid parent (cannot be None)")
        if not isinstance(parent, BaseNode):
            raise TypeError(f"TreeNode parent must be BaseNode instance, got {type(parent)}")
        
        # Import here to avoid circular imports while still getting proper type checking
        from ..reconnaissance.discovery import DiscoveredModule, DiscoveredPackage
        
        # Validate source_data is appropriate for TreeNode
        if not isinstance(source_data, (ast.AST, DiscoveredModule, DiscoveredPackage)):
            raise TypeError(
                f"TreeNode source_data must be ast.AST, DiscoveredModule, or DiscoveredPackage, "
                f"got {type(source_data)}"
            )
            
        super().__init__(source_data)
        self.parent = parent
        
        # Extract name from source_data
        self.name = self._extract_name()
        
        # Validate extracted name (including whitespace check)
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError(f"{self.__class__.__name__} extracted invalid name: {repr(self.name)}")
        
        self._create_children()
    
    def _extract_name(self) -> str:
        """
        Extract name from source_data.
        
        Subclasses must override this method to extract their name from
        the source_data provided during construction.
        
        Returns:
            str: The extracted name
            
        Raises:
            NotImplementedError: If subclass doesn't override this method
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement _extract_name()")
    
    @property
    def fqn(self) -> str:
        """
        Generate Fully Qualified Name by walking up the tree.
        
        ContainerNodes do not contribute to FQN generation, maintaining their
        "pass-through" quality. Only named entities with meaningful names
        contribute to the fully qualified name path.
        
        Returns:
            str: Fully qualified name (e.g., "myproject.services.api.HTTPClient")
            
        Examples:
            >>> # Simple path: project -> module -> class
            >>> class_node.fqn
            'myproject.utils.Logger'
            
            >>> # Nested packages: project -> pkg1 -> pkg2 -> module -> class
            >>> nested_class.fqn
            'myproject.services.api.models.User'
            
            >>> # ContainerNodes don't appear in FQN
            >>> import_node.fqn
            'myproject.utils'  # Same as parent module
            
            >>> # Method inside class
            >>> method.fqn
            'myproject.utils.Logger.log_message'
        """
        parts = []
        current = self
        
        while current is not None:
            # Only include nodes with meaningful names (skip ContainerNodes)
            if hasattr(current, 'name') and current.name:
                parts.append(current.name)
            current = getattr(current, 'parent', None)
        
        return ".".join(reversed(parts))

class ContainerNode(BaseNode):
    """
    AST parsing artifacts that group related items but have no meaningful identity.
    
    ContainerNodes exist solely to organize AST structures and create child
    entities. They require a valid parent and source AST node for processing.
    """
    
    def __init__(self, parent: 'BaseNode', source_data: ast.AST):
        """
        Initialize a container node with validation.
        
        Args:
            parent: Valid BaseNode parent (cannot be None)  
            source_data: Valid AST node used to create children (cannot be None)
            
        Raises:
            ValueError: If parent is None
            TypeError: If parent is not a BaseNode instance or source_data is not an AST node
        """
        if parent is None:
            raise ValueError("ContainerNode requires valid parent (cannot be None)")
        if not isinstance(parent, BaseNode):
            raise TypeError(f"ContainerNode parent must be BaseNode instance, got {type(parent)}")
        if not isinstance(source_data, ast.AST):
            raise TypeError(f"ContainerNode source_data must be AST node, got {type(source_data)}")
            
        super().__init__(source_data)
        self.parent = parent
        self._create_children()
    
    @property
    def fqn(self) -> str:
        """
        Pass-through FQN to parent since containers have no meaningful identity.
        
        ContainerNodes are organizational artifacts without their own names,
        so they transparently inherit their parent's fully qualified name.
        
        Returns:
            str: Parent's FQN
            
        Examples:
            >>> # ImportNode container
            >>> import_container.fqn
            'myproject.utils'  # Same as parent module
            
            >>> # StateContainerNode
            >>> state_container.fqn  
            'myproject.config'  # Same as parent module
        """
        return self.parent.fqn if self.parent else ""