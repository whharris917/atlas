"""
Package Node - Atlas Rewrite

Node representing a Python package with automatic child creation.
Creates all nested PackageNodes and ModuleNodes immediately.
Pure self-extracting architecture - name from package_data.
"""

from typing import List, Optional, TYPE_CHECKING
from ..core import TreeNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from . import ModuleNode
    from ..reconnaissance.discovery import DiscoveredPackage


class PackageNode(TreeNode):
    """Node representing a Python package."""
    
    def __init__(self, package_data: 'DiscoveredPackage', parent: TreeNode):
        if not package_data:
            raise ValueError("PackageNode requires valid DiscoveredPackage")
        
        # Initialize collections before parent init (which calls _create_children)
        self.package_data = package_data
        self._packages: List['PackageNode'] = []
        self._modules: List['ModuleNode'] = []
        
        # Self-extract name from package data
        super().__init__(package_data.name, parent, package_data.ast_node)
    
    def _create_children(self):
        """Create child nodes from DiscoveredPackage data."""
        
        print(f"  Creating children in: {self.fqn}")
        
        # Create nested packages from DiscoveredPackage
        for nested_package_data in self.package_data.nested_packages:
            self.create_package(nested_package_data)
        
        # Create modules from DiscoveredPackage
        for module_data in self.package_data.modules:
            if module_data.ast_node:
                self.create_module(module_data)
    
    def create_package(self, package_data: 'DiscoveredPackage') -> 'PackageNode':
        """Create and hook a nested package from DiscoveredPackage."""
        package_node = PackageNode(package_data, parent=self)
        self._packages.append(package_node)
        return package_node
    
    def create_module(self, module_data) -> 'ModuleNode':
        """Create and hook a module from DiscoveredModule."""
        from . import ModuleNode
        module_node = ModuleNode(module_data, parent=self)
        self._modules.append(module_node)
        return module_node
    
    def get_package(self, name: str) -> 'PackageNode':
        """Get a nested package by name."""
        for package in self._packages:
            if package.name == name:
                return package
        raise KeyError(f"Package '{name}' not found in package '{self.name}'")
    
    def get_module(self, name: str) -> 'ModuleNode':
        """Get a module by name."""
        for module in self._modules:
            if module.name == name:
                return module
        raise KeyError(f"Module '{name}' not found in package '{self.name}'")
    
    def list_packages(self) -> List['PackageNode']:
        """List all nested packages in this package."""
        return self._packages
    
    def list_modules(self) -> List['ModuleNode']:
        """List all modules in this package."""
        return self._modules
    
    def list_all(self) -> dict:
        """Get comprehensive package structure."""
        return {
            'packages': [pkg.name for pkg in self._packages],
            'modules': [mod.name for mod in self._modules]
        }