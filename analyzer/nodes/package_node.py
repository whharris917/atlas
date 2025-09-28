"""
Package Node - Atlas Rewrite

Node representing a Python package with automatic child creation.
Extremely focused implementation adhering to strict separation of concerns.
"""

from typing import List
from ..core import TreeNode, BaseNode
from ..reconnaissance.discovery import DiscoveredPackage, DiscoveredModule
from .module_node import ModuleNode


class PackageNode(TreeNode):
    """Node representing a Python package."""
    
    def __init__(self, parent: BaseNode, source_data: DiscoveredPackage):
        if not isinstance(source_data, DiscoveredPackage):
            raise TypeError("PackageNode requires DiscoveredPackage as source_data")
        
        # Initialize collections before parent init (which calls _create_children)
        self._packages: List[PackageNode] = []
        self._modules: List[ModuleNode] = []
        
        # Parent class handles name extraction and validation
        super().__init__(parent, source_data)
    
    def _extract_name(self) -> str:
        """Extract package name from DiscoveredPackage."""
        return self.source_data.name
    
    def _create_children(self):
        """Create child nodes from DiscoveredPackage."""
        print(f"  Creating children in package: {self.fqn}")
        
        # Create nested packages
        for nested_package in self.source_data.nested_packages:
            self.create_package(nested_package)
        
        # Create direct modules
        for module_data in self.source_data.modules:
            if module_data.ast_node:
                self.create_module(module_data)
    
    def create_package(self, package_data: DiscoveredPackage) -> 'PackageNode':
        """Create and hook a nested package from DiscoveredPackage."""
        package_node = PackageNode(parent=self, source_data=package_data)
        self._packages.append(package_node)
        return package_node
    
    def create_module(self, module_data: DiscoveredModule) -> ModuleNode:
        """Create and hook a module from DiscoveredModule."""
        module_node = ModuleNode(parent=self, source_data=module_data)
        self._modules.append(module_node)
        return module_node