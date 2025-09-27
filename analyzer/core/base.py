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
        
        # Set ast_node if source_data is an AST node, otherwise None
        self.ast_node = source_data if isinstance(source_data, ast.AST) else None
    
    @property
    def line_number(self) -> int:
        """Get line number from AST node, or 0 if not available."""
        if self.ast_node:
            return getattr(self.ast_node, 'lineno', 0)
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
            project_node.get_depth()     # 0 (root)
            module_node.get_depth()      # 1 (under project)  
            class_node.get_depth()       # 2 (under module)
            function_node.get_depth()    # 3 (under class)
            argument_node.get_depth()    # 4 (under function)
            type_node.get_depth()        # 5 (under argument)
            
            # ContainerNodes are skipped in depth calculation:
            # module -> import_container -> alias
            # alias.get_depth() returns 2 (module=1 + alias=1, container skipped)
        """
        depth = 0
        current = self.parent
        
        while current is not None:
            # Only count nodes with meaningful names (TreeNode/RootNode)
            # Skip ContainerNodes just like FQN generation does
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
        
        **The Self-Creating Cascade:**
        Simply creating the root ProjectNode triggers a beautiful cascade where
        every node automatically discovers and creates its children, which in turn
        create their children, continuing recursively until the entire project
        tree is spontaneously generated and completely populated.
        
        **Architectural Benefits:**
        - **Guaranteed Completeness:** Nothing can be missed during tree generation
        - **Fail-Fast Discovery:** All structural issues detected immediately at creation
        - **Zero Manual Orchestration:** No need to remember to call creation methods
        - **Perfect Consistency:** Every node follows identical self-creating patterns
        - **Atomic Tree State:** Tree is always in a complete, valid state
        
        **Implementation Pattern:**
        Each node type overrides this method to:
        1. Initialize empty collections for child entities
        2. Discover relevant AST structures or project elements  
        3. Create child nodes immediately, passing self as parent
        4. Store children in appropriate collections (Dict for entities, List for containers)
        
        **The Magic of Mandatory Creation:**
        By calling this method automatically in every constructor, Atlas creates
        a self-sustaining ecosystem where:
        - ProjectNode → discovers and creates PackageNodes
        - PackageNode → discovers and creates ModuleNodes  
        - ModuleNode → discovers and creates ClassNodes, FunctionNodes, ImportContainers
        - ClassNode → discovers and creates MethodNodes, AttributeNodes
        - FunctionNode → discovers and creates ArgumentNodes, ReturnNodes
        - And so on, recursively, until every entity is discovered and represented
        
        The result: One `ProjectNode("MyProject")` call generates a complete,
        perfectly structured tree representing every discoverable entity in the
        entire codebase, with guaranteed completeness and zero manual effort.
        
        Override in subclasses to implement specific child discovery and creation logic.
        """
        pass
    
    def __repr__(self) -> str:
        """Nice string representation showing node type."""
        node_type = self.__class__.__name__.replace('Node', '')
        if hasattr(self, 'name'):
            return f"{node_type}({self.name})"
        return f"{node_type}()"

class RootNode(BaseNode):
    """
    Base for nodes that MUST exist without parents (project roots).
    
    RootNodes are required to have no parent - they are the foundation
    of the project tree hierarchy. Unlike TreeNodes which require parents,
    RootNodes explicitly reject parent relationships to maintain clean
    architectural boundaries.
    """
    
    def __init__(self, source_data: 'ProjectStructure'):
        """
        Initialize a root node with validation.
        
        Args:
            source_data: The ProjectStructure used to create children
            
        Raises:
            TypeError: If source_data is not a ProjectStructure
            ValueError: If extracted name is invalid
        """
        # Import here to avoid circular imports while still getting proper type checking
        from ..reconnaissance.discovery import ProjectStructure
        if not isinstance(source_data, ProjectStructure):
            raise TypeError(f"RootNode requires ProjectStructure as source_data, got {type(source_data)}")
            
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
            str: The name for this root node
            
        Raises:
            NotImplementedError: If subclass doesn't override this method
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement _extract_name()")

class TreeNode(BaseNode):
    """
    Named entities with mandatory parent relationships.
    
    TreeNodes represent meaningful code entities that must exist within
    the context of a parent node. They require both a valid parent
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
        
        # Validate source_data is appropriate for TreeNode
        # Import here to avoid circular imports while still getting proper type checking
        from ..reconnaissance.discovery import DiscoveredModule, DiscoveredPackage
        
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
        the source_data provided during construction. The extraction method
        depends on the specific source_data type:
        
        - AST nodes: Extract from node.name (ClassDef, FunctionDef) or node.arg (arg)
        - DiscoveredModule: Extract from module_data.name
        - DiscoveredPackage: Extract from package_data.name
        
        Returns:
            str: The name for this tree node
            
        Raises:
            NotImplementedError: If subclass doesn't override this method
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement _extract_name()")
    
    @property
    def fqn(self) -> str:
        """
        Generate Fully Qualified Name by walking up the parent chain.
        
        ContainerNodes do not contribute to FQN generation, maintaining their
        "pass-through" quality. Only named entities with meaningful names
        contribute to the fully qualified name path.
        
        Returns:
            str: Dot-separated fully qualified name from root to this node
            
        Examples:
            project_node.fqn           # "MyProject"
            module_node.fqn            # "MyProject.services.client"  
            class_node.fqn             # "MyProject.services.client.ApiClient"
            method_node.fqn            # "MyProject.services.client.ApiClient.make_request"
            argument_node.fqn          # "MyProject.services.client.ApiClient.make_request.timeout"
            type_node.fqn              # "MyProject.services.client.ApiClient.make_request.timeout.int"
            
            # ContainerNodes are skipped in FQN generation:
            # module -> import_container -> alias
            # alias.fqn becomes "MyProject.services.client.requests" 
            # (container is invisible in the qualified name)
        """
        parts = []
        current = self
        while current:
            if hasattr(current, 'name'):
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