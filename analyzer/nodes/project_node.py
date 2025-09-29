"""
Project Node - Atlas Rewrite

Root node representing the entire project with automatic child creation.
Now includes serialization capability via mixin.
"""

from typing import List
from ..core import RootNode
from ..reconnaissance.discovery import ProjectStructure, DiscoveredPackage, DiscoveredModule
from .package_node import PackageNode
from .module_node import ModuleNode
from ..visualization import TreeVisualizer, SerializationMixin


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
    
    def _create_children(self):
        """Create child nodes from ProjectStructure."""
        print(f"\n=== BUILDING PROJECT TREE ===")
        print(f"Project: {self.name}")
        
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
    
    # ========== Visualization Methods ==========
    
    def print(self) -> None:
        """Print hierarchical tree representation to terminal."""
        visualizer = TreeVisualizer()
        visualizer.print(self)

    def view(self) -> str:
        """Get hierarchical tree representation as string."""
        visualizer = TreeVisualizer()
        return visualizer.view(self)
    
    # dump() method is provided by SerializationMixin