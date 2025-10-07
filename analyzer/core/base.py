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
            List of notes, optionally filtered by type
        
        Example:
            >>> function_node.get_notes()  # All notes
            >>> function_node.get_notes(TypeNote)  # Only TypeNote instances
        """
        if note_type is None:
            return self._notes
        return [n for n in self._notes if isinstance(n, note_type)]
    
    @property
    def line_number(self) -> int:
        """Get line number from source data if it's an AST node, or 0 if not available."""
        if isinstance(self.source_data, ast.AST):
            return getattr(self.source_data, 'lineno', 0)
        return 0
    
    def get_depth(self) -> int:
        """
        Calculate depth of this node in the tree.
        
        Returns the number of meaningful hierarchical levels from the project root
        to this node. Container nodes are treated as pass-through organizational
        structures that don't add to the conceptual depth.
        
        ContainerNode Behavior:
            Just like FQN computation, depth calculation skips ContainerNodes since they
            serve as AST organizational structures rather than meaningful hierarchical
            levels in the project namespace.
        
        Examples:
            ProjectNode: depth = 0
            PackageNode (direct child of project): depth = 1
            ModuleNode (in package): depth = 2
            ClassNode (in module): depth = 3
            FunctionNode (in class, with StateContainerNode parent): depth = 4
                (StateContainerNode doesn't add to depth - pass-through)
        
        Returns:
            int: Depth counting only meaningful hierarchical nodes
        """
        depth = 0
        current = getattr(self, 'parent', None)
        while current is not None:
            # Only count non-container nodes for depth
            if not isinstance(current, ContainerNode):
                depth += 1
            current = getattr(current, 'parent', None)
        return depth
    
    def _create_children(self):
        """
        Create all child nodes for this node.
        
        This is the heart of Atlas's self-creating cascade architecture. When a node is
        constructed, it automatically creates all of its children based on the source_data
        it was provided. This mandatory child creation is what enables a single ProjectNode
        creation to result in a complete, fully-populated tree representing an entire codebase.
        
        Architectural Benefits:
            - **Automatic Tree Population:** No manual tree building required
            - **Data Integrity:** Children created immediately with all required context
            - **Guaranteed Consistency:** Tree is always in valid state, never partially built
            - **Simplified Usage:** Users just create root node, everything else happens automatically
        
        Implementation Pattern:
            Subclasses override this method to:
            1. Discover what children should exist (from AST, filesystem, etc.)
            2. Instantiate child nodes with appropriate parent reference
            3. Store children in collections for navigation
        
        Common Patterns:
            - Parsing AST nodes to find nested definitions, often with the use of node visitors
            - Scanning filesystem to discover packages/modules
            - Iterating over data structures to create children
            - Conditionally creating type analysis nodes
        
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
        # ContainerNode case: no name, pass through to parent
        if not hasattr(self, 'name'):
            return self.parent.fqn if self.parent else ""
        
        # TreeNode/RootNode case: build dotted path
        parts = [self.name]
        current = self.parent
        while current is not None:
            # Skip container nodes - they don't contribute to FQN
            if not isinstance(current, ContainerNode):
                if hasattr(current, 'name'):
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
            source_data: ProjectStructure containing project discovery data
            
        Raises:
            ValueError: If extracted name is invalid
            TypeError: If source_data is not ProjectStructure
        """
        # Validate source_data is ProjectStructure        
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


class TreeNode(BaseNode):
    """
    Named entities with parent relationships forming the project tree.
    
    TreeNodes represent meaningful Python entities (modules, classes, functions, etc.)
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
            source_data: Valid AST node used to create children (cannot be None)
            
        Raises:
            ValueError: If parent is None
            TypeError: If parent is not a BaseNode instance or source_data is not ast.AST
        """
        if parent is None:
            raise ValueError("ContainerNode requires valid parent (cannot be None)")
        if not isinstance(parent, BaseNode):
            raise TypeError(f"ContainerNode parent must be BaseNode instance, got {type(parent)}")
        if not isinstance(source_data, ast.AST):
            raise TypeError(f"ContainerNode source_data must be ast.AST, got {type(source_data)}")
            
        super().__init__(source_data)
        self.parent = parent
        self._create_children()