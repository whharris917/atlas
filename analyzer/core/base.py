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
from typing import Union, Optional, Dict, List, TYPE_CHECKING

from .navigation import NavigationMixin
from ..reconnaissance.discovery import ProjectStructure, DiscoveredModule, DiscoveredPackage

if TYPE_CHECKING:
    from ..analysis.base_note import BaseNote


class BaseNode(NavigationMixin):
    """Foundation for all Atlas nodes with shared functionality and enhanced navigation."""
    
    def __init__(self, source_data: Union[ast.AST, ProjectStructure, DiscoveredModule, DiscoveredPackage]):
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
        if not isinstance(source_data, (ast.AST, ProjectStructure, DiscoveredModule, DiscoveredPackage)):
            raise TypeError(
                f"BaseNode source_data must be ast.AST, ProjectStructure, DiscoveredModule, "
                f"or DiscoveredPackage, got {type(source_data)}"
            )
            
        self.source_data = source_data
        self._notes: List['BaseNote'] = []  # Analysis artifacts attached to this node
    
    def analyze(self, parent_scope: Optional[Dict[str, str]] = None):
        """
        Analyze this node and cascade analysis to all children.
        
        This method establishes the Analysis Phase contract that all nodes must implement.
        It receives scope information from the parent and is responsible for:
        1. Performing node-specific analysis (via visitors or other mechanisms)
        2. Cascading analysis to all children with updated scope
        
        Args:
            parent_scope: Dictionary mapping variable names to type strings, representing
                         all variables accessible from parent scopes. None for root nodes.
        
        Design Pattern:
            The analyze() method follows the same cascading pattern as _create_children()
            in the Reconnaissance Phase. Each node analyzes itself, then ensures all its
            children are analyzed with appropriate scope information.
        
        Implementation Requirement:
            All TreeNode subclasses must implement this method. The base implementation
            raises NotImplementedError to enforce this contract.
        
        Example:
            >>> project = ProjectBuilder("sample_files/").build()
            >>> project.analyze()  # Cascades through entire tree
        """
        raise NotImplementedError(f"{type(self).__name__} must implement analyze()")
    
    def get_notes(self, note_type: Optional[type] = None) -> List['BaseNote']:
        """
        Query analysis notes attached to this node.
        
        Args:
            note_type: Optional note class to filter by (e.g., TypeNote).
                      If None, returns all notes.
        
        Returns:
            List of notes (filtered by type if specified)
        """
        if note_type is None:
            return self._notes
        return [note for note in self._notes if isinstance(note, note_type)]
    
    @property
    def line_number(self) -> int:
        """Get line number from source data if it's an AST node, or 0 if not available."""
        if isinstance(self.source_data, ast.AST):
            return getattr(self.source_data, 'lineno', 0)
        return 0
    
    def get_depth(self) -> int:
        """
        Calculate tree depth from project root to this node.
        
        Counts meaningful hierarchical levels while treating ContainerNodes
        as pass-through organizational structures (similar to FQN generation).
        ContainerNodes don't contribute to depth as they're structural scaffolding
        rather than meaningful Python entities.
        
        Examples:
            ProjectNode: depth 0 (root)
            PackageNode: depth 1
            ModuleNode in package: depth 2
            ClassNode in module: depth 3
            Method in class: depth 4
            ContainerNode: same depth as parent (pass-through)
        
        Returns:
            int: Hierarchical depth from root, skipping ContainerNodes
        """
        depth = 0
        current = getattr(self, 'parent', None)
        while current is not None:
            # Only count non-container nodes for depth
            if not isinstance(current, ContainerNode):
                depth += 1
            current = getattr(current, 'parent', None)
        return depth
    
    def get_project(self):
        """
        Get the ProjectNode at the root of this tree.
        
        Walks up the parent chain to find the ProjectNode. Every node
        in the Atlas tree is part of a project, so this method enables
        any node to access the complete project tree for navigation
        and type resolution.
        
        Any node in the tree can use this to access project-level functionality:
        - Type resolution via get_node_by_fqn()
        - Project-wide searches
        - Global type information
        
        Returns:
            ProjectNode: The root project node
            
        Raises:
            RuntimeError: If no ProjectNode is found in parent chain
        """
        from ..nodes.project_node import ProjectNode
        
        current = self
        while current is not None:
            if isinstance(current, ProjectNode):
                return current
            current = getattr(current, 'parent', None)
        
        # Should never happen in a properly constructed tree
        raise RuntimeError(f"No ProjectNode found in parent chain for {self}")
    
    def _create_children(self):
        """
        Create all child nodes via self-creating cascade.
        
        This method is the cornerstone of Atlas's self-creating architecture.
        It is called automatically during node construction and must create
        all appropriate child nodes based on the source_data.
        
        The Self-Creating Cascade:
            When a ProjectNode is created, it creates PackageNodes and ModuleNodes.
            Those nodes create ClassNodes and FunctionNodes. Those nodes create
            their children... continuing until the entire tree is populated.
            
            This happens automatically. The caller creates only the root ProjectNode,
            and the entire tree materializes through the cascade.
        
        Why Mandatory Child Creation Matters:
            - Tree is always complete (no partial/lazy initialization)
            - No need to check "has this been populated yet?"
            - Navigation works immediately after construction
            - Architectural simplicity and predictability
        
        Implementation Pattern:
            Subclasses examine their source_data (AST nodes or discovery classes)
            and create appropriate child nodes. For example:
            
            - ClassNode examines ast.ClassDef for methods and attributes
            - FunctionNode examines ast.FunctionDef for arguments and returns
            - ModuleNode examines discovered classes and functions
        
        The Magic:
            By requiring every node to create its children during __init__,
            we ensure that a single root node creation cascades through the
            entire structure, creating a complete representation of the codebase.
            This is foundational to Atlas's architecture.
        
        Subclasses must override this method to implement their specific child
        creation logic.
        
        Raises:
            NotImplementedError: If subclass doesn't override this method
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement _create_children()")
    
    @property
    def fqn(self) -> str:
        """
        Build the fully qualified name from project root to this node.
        
        Constructs a dotted path representing the complete hierarchical location
        of this node within the project structure.
        
        For example: "myproject.services.auth.TokenManager.validate_token"
        
        Implementation:
            - For nodes with names (RootNode, TreeNode): Builds dotted path from root to node
            - For ContainerNodes without names: Passes through to parent's FQN
            - ContainerNodes are skipped during path building (pass-through organizational nodes)
        
        ContainerNode Behavior:
            Container nodes (ImportNode, StateContainerNode, etc.) don't contribute to the FQN.
            They serve as organizational structures within the AST but don't represent meaningful
            Python entities in the namespace hierarchy.
        
        Examples:
            RootNode (ProjectNode): "myproject"
            PackageNode: "myproject.services"
            ModuleNode: "myproject.services.database.connection"
            ClassNode: "myproject.services.database.connection.ConnectionPool"
            Method: "myproject.services.database.connection.ConnectionPool.execute_query"
            ContainerNode: "myproject.services" (same as parent module - pass-through)
        
        Returns:
            str: The fully qualified name from project root to this node
        """
        return self._build_fqn(extended=False, include_containers=False)
    
    @property
    def xfqn(self) -> str:
        """
        Extended Fully Qualified Name with type information.
        
        Skips ContainerNodes but shows node types for disambiguation.
        This resolves ambiguity in traditional dot notation where a.b.c
        could be Package.Module.Class or Module.Class.Function.
        
        Example:
            "Project(sample_files).Package(models).Module(user).Class(User).Function(get_email)"
        
        Returns:
            str: Extended FQN with type prefixes for named nodes
        """
        return self._build_fqn(extended=True, include_containers=False)
    
    @property
    def cfqn(self) -> str:
        """
        Complete Fully Qualified Name with all nodes including containers.
        
        Shows every node in the path, including ContainerNodes, with type
        information. Useful for debugging and understanding the complete
        tree structure.
        
        Example:
            "Project(sample_files).Package(models).Module(user).StateContainer().State(User)"
        
        Returns:
            str: Complete FQN including ContainerNodes with type information
        """
        return self._build_fqn(extended=True, include_containers=True)
    
    def _build_fqn(self, extended: bool = False, include_containers: bool = False) -> str:
        """
        Internal method to build FQN variants.
        
        This unified implementation powers all three FQN properties (fqn, xfqn, cfqn)
        with different formatting and filtering options.
        
        Args:
            extended: If True, include node types (e.g., "Class(User)")
            include_containers: If True, include ContainerNodes in path
        
        Returns:
            str: Formatted FQN based on options
        """
        # ContainerNode case: pass through to parent or format with type info
        if not (hasattr(self, 'name') and self.name):
            if extended:
                # Show container type even without name
                node_type = self.__class__.__name__.replace('Node', '')
                parent_fqn = self.parent.fqn if self.parent else ""
                return f"{parent_fqn}.{node_type}()" if parent_fqn else f"{node_type}()"
            else:
                # For standard format, pass through to parent
                return self.parent.fqn if self.parent else ""
        
        # TreeNode/RootNode case: build dotted path
        parts = []
        current = self
        
        while current is not None:
            # Check if this node should be included
            should_include = True
            
            if not include_containers:
                # Skip nodes without names (ContainerNodes)
                if not (hasattr(current, 'name') and current.name):
                    should_include = False
            
            if should_include:
                if extended:
                    # Extended format: NodeType(name)
                    node_type = current.__class__.__name__.replace('Node', '')
                    if hasattr(current, 'name') and current.name:
                        parts.append(f"{node_type}({current.name})")
                    else:
                        # Container without name
                        parts.append(f"{node_type}()")
                else:
                    # Standard format: just name
                    if hasattr(current, 'name') and current.name:
                        parts.append(current.name)
            
            current = getattr(current, 'parent', None)
        
        return '.'.join(reversed(parts))
    
    def __repr__(self) -> str:
        """Nice string representation showing node type and name if available."""
        node_type = self.__class__.__name__.replace('Node', '')
        if hasattr(self, 'name'):
            return f"{node_type}({self.name})"
        return f"{node_type}()"


class RootNode(BaseNode):
    """
    Base for parentless nodes like ProjectNode.
    
    Root nodes MUST exist without parents - they are the entry points to tree hierarchies.
    They still require source material for child creation.
    """
    
    def __init__(self, source_data: ProjectStructure):
        """
        Initialize a root node with comprehensive validation.
        
        Args:
            source_data: ProjectStructure containing project metadata and filesystem info
            
        Raises:
            ValueError: If extracted name is invalid
            TypeError: If source_data is not a ProjectStructure instance
        """
        # Validate source_data is ProjectStructure
        if not isinstance(source_data, ProjectStructure):
            raise TypeError(f"RootNode requires ProjectStructure as source_data, got {type(source_data)}")
        
        super().__init__(source_data)
        self.parent = None  # RootNodes explicitly have no parent
        
        # Extract and validate name
        self.name = self._extract_name()
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


class TreeNode(BaseNode):
    """
    Base for named entities within tree hierarchy.
    
    Tree nodes represent meaningful Python entities (modules, classes, functions, etc.)
    that have names and exist within a hierarchical structure. They require both a valid parent
    and source material for child creation.
    """
    
    def __init__(self, parent: BaseNode, source_data: Union[ast.AST, DiscoveredModule, DiscoveredPackage]):
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


class ContainerNode(BaseNode):
    """
    AST parsing artifacts without meaningful identity.
    
    Container nodes organize other nodes but don't represent named Python entities
    themselves. They exist solely to organize AST structures and create child
    entities. Examples: StateContainerNode (holds module-level assignments), ImportNode (holds aliases).
    They require a parent but have no name.
    """
    
    def __init__(self, parent: BaseNode, source_data: ast.AST):
        """
        Initialize a container node with comprehensive validation.
        
        Args:
            parent: Valid BaseNode parent (cannot be None)
            source_data: AST node used to create children (cannot be None)
            
        Raises:
            ValueError: If parent is None
            TypeError: If parent is not a BaseNode or source_data is not ast.AST
        """
        if parent is None:
            raise ValueError("ContainerNode requires valid parent (cannot be None)")
        if not isinstance(parent, BaseNode):
            raise TypeError(f"ContainerNode parent must be BaseNode instance, got {type(parent)}")
        if not isinstance(source_data, ast.AST):
            raise TypeError(f"ContainerNode requires ast.AST as source_data, got {type(source_data)}")
            
        super().__init__(source_data)
        self.parent = parent
        self._create_children()