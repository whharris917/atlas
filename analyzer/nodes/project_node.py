"""
Project Node - Atlas Rewrite

Root node representing the entire project with automatic child creation.
Now includes serialization capability via mixin and FQN navigation.
"""

from typing import List, Optional, Dict
from ..core import RootNode, BaseNode
from ..reconnaissance.discovery import ProjectStructure, DiscoveredPackage, DiscoveredModule
from .package_node import PackageNode
from .module_node import ModuleNode
from ..visualization import SerializationMixin


class ProjectNode(SerializationMixin, RootNode):
    """
    Root node representing the entire project.
    
    Inherits from SerializationMixin to provide .dump() capability
    for complete JSON serialization of the project tree.
    """
    
    def __init__(self, source_data: ProjectStructure):
        # Initialize collections before parent init (which calls _create_children)
        self._packages: List[PackageNode] = []
        self._modules: List[ModuleNode] = []
        
        # Parent class handles name extraction and validation
        super().__init__(source_data)
    
    def _extract_name(self) -> str:
        """Extract project name from ProjectStructure root_path."""
        project_name = self.source_data.root_path.name
        if not project_name:
            raise ValueError("ProjectStructure must have valid root_path with name")
        return project_name
    
    def analyze(self, parent_scope: Optional[Dict[str, str]] = None):
        """
        Analyze this project and cascade to all children.
        
        Project is the root of analysis, so parent_scope is always empty.
        Cascades analysis to all packages and modules with empty scope.
        """
        # Project has no parent scope, start with empty dict
        scope = {}
        
        # Cascade to all children
        for child in self._get_direct_children():
            child.analyze(parent_scope=scope)
    
    def _create_children(self):
        """Create child nodes from ProjectStructure."""
        # Create direct modules from ProjectStructure
        for module_data in self.source_data.direct_modules:
            if module_data.ast_node:
                self.create_module(module_data)
        
        # Create packages from ProjectStructure (which will create their own children)
        for package_data in self.source_data.packages:
            self.create_package(package_data)
    
    def create_package(self, package_data: DiscoveredPackage) -> PackageNode:
        """Create and hook a top-level package from DiscoveredPackage."""
        package_node = PackageNode(parent=self, source_data=package_data)
        self._packages.append(package_node)
        return package_node
    
    def create_module(self, module_data: DiscoveredModule) -> ModuleNode:
        """Create and hook a top-level module from DiscoveredModule."""
        module_node = ModuleNode(parent=self, source_data=module_data)
        self._modules.append(module_node)
        return module_node
    
    # ========================================================================
    # Visualization Methods - Session 28
    # ========================================================================
    
    def print(self) -> None:
        """Print hierarchical tree representation to terminal."""
        from ..visualization import TreeVisualizer
        visualizer = TreeVisualizer()
        visualizer.print(self)
    
    def view(self) -> str:
        """Get hierarchical tree representation as string."""
        from ..visualization import TreeVisualizer
        visualizer = TreeVisualizer()
        return visualizer.view(self)
    
    # ========================================================================
    # FQN Navigation - Session 34
    # ========================================================================
    
    def get_node_by_fqn(self, fqn: str) -> Optional[BaseNode]:
        """
        Navigate the project tree to find a node by its fully qualified name.
        
        This method performs a depth-first search through the tree structure,
        trying all possible node types at each level (packages, modules, classes,
        functions, methods, attributes, state variables).
        
        Args:
            fqn: Fully qualified name, e.g., "sample_files.models.User.validate"
                 or "sample_files.core.utils.format_timestamp"
        
        Returns:
            The node with the given FQN, or None if not found
        
        Examples:
            >>> project.get_node_by_fqn("sample_files.models.User")
            <ClassNode: User>
            
            >>> project.get_node_by_fqn("sample_files.models.User.validate")
            <FunctionNode: validate>
            
            >>> project.get_node_by_fqn("sample_files.models.User.email")
            <InstanceAttributeNode: email>
            
            >>> project.get_node_by_fqn("sample_files.VERSION")
            <StateNode: VERSION>
        """
        parts = fqn.split('.')
        
        # Start at project root
        current = self
        
        # Skip first part if it matches project name
        start_index = 1 if parts[0] == self.name else 0
        
        # Navigate through each part of the FQN
        for part in parts[start_index:]:
            next_node = self._find_child_by_name(current, part)
            
            if next_node is None:
                return None  # Path doesn't exist
            
            current = next_node
        
        return current
    
    def _find_child_by_name(self, node: BaseNode, name: str) -> Optional[BaseNode]:
        """
        Find a child node by name, trying all possible node types.
        
        This helper method encapsulates the logic of checking different
        node types based on what the current node can contain.
        
        IMPORTANT: For PackageNodes, this implements a fallback strategy
        to handle package-level imports (e.g., `from .user import User`
        making User available as `models.User`). Since we don't currently
        process __init__.py imports during reconnaissance, we fall back to
        searching ALL modules within the package for a matching class/function.
        
        This is a MAKESHIFT SOLUTION that assumes everything is exported.
        TODO: Properly process __init__.py imports during reconnaissance phase.
        
        Args:
            node: The current node to search within
            name: The name of the child to find
        
        Returns:
            The child node if found, None otherwise
        """
        from .package_node import PackageNode
        from .module_node import ModuleNode
        from .class_node import ClassNode
        from .function_node import FunctionNode
        
        # ProjectNode can contain: packages, modules
        if isinstance(node, ProjectNode):
            return node.get_package(name) or node.get_module(name)
        
        # PackageNode can contain: packages, modules
        # PLUS: fallback search for exported classes/functions
        elif isinstance(node, PackageNode):
            # First: Try direct children (sub-packages, sub-modules)
            direct_child = node.get_package(name) or node.get_module(name)
            if direct_child:
                return direct_child
            
            # Second: FALLBACK - Search all modules in package for class/function
            # This handles: from .user import User → models.User
            # We assume everything is exported (no __init__.py processing yet)
            for module in node.list_modules():
                # Try to find class in this module
                found = module.get_class(name) or module.get_function(name)
                if found:
                    return found
            
            return None
        
        # ModuleNode can contain: classes, functions, state variables
        elif isinstance(node, ModuleNode):
            return (node.get_class(name) or 
                    node.get_function(name) or
                    node.get_state(name))
        
        # ClassNode can contain: methods, class attributes, instance attributes
        elif isinstance(node, ClassNode):
            return (node.get_method(name) or
                    node.get_class_attribute(name) or
                    node.get_instance_attribute(name))
        
        # FunctionNode can contain: arguments, return
        # Note: Typically you don't navigate INTO functions via FQN,
        # but we support it for completeness
        elif isinstance(node, FunctionNode):
            if name == "return":
                return node.get_return()
            return node.get_argument(name)
        
        # Other node types (StateNode, AttributeNode, etc.) are leaves
        else:
            return None