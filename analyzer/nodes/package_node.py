"""
Package Node - Atlas Rewrite

Node representing a Python package with automatic child creation.
Creates all nested PackageNodes and ModuleNodes immediately.
"""

from typing import Dict, List, Optional, TYPE_CHECKING
from ..core import TreeNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from . import ModuleNode
    from ..reconnaissance.discovery import DiscoveredPackage


class PackageNode(TreeNode):
    """Node representing a Python package."""
    
    def __init__(self, name: str, parent: TreeNode, package_data: 'DiscoveredPackage'):
        if not package_data:
            raise ValueError(f"PackageNode '{name}' requires valid DiscoveredPackage")
        
        super().__init__(name, parent, package_data.ast_node)
        self.package_data = package_data
        self._packages: Dict[str, 'PackageNode'] = {}
        self._modules: Dict[str, 'ModuleNode'] = {}
        
        # Create all children immediately
        self._create_children()
    
    def _create_children(self):
        """Create child nodes from DiscoveredPackage data."""
        
        print(f"  Creating children in: {self.fqn}")
        
        # Create nested packages from DiscoveredPackage
        for nested_package_data in self.package_data.nested_packages:
            self.create_package(nested_package_data.name, nested_package_data)
        
        # Create modules from DiscoveredPackage
        for module_data in self.package_data.modules:
            if module_data.ast_node:
                self.create_module(module_data.name, module_data.ast_node)
    
    def create_package(self, name: str, package_data: 'DiscoveredPackage') -> 'PackageNode':
        """Create and hook a nested package from DiscoveredPackage."""
        package_node = PackageNode(name, parent=self, package_data=package_data)
        self._packages[name] = package_node
        return package_node
    
    def create_module(self, name: str, ast_module) -> 'ModuleNode':
        """Create and hook a module from AST."""
        from . import ModuleNode
        module_node = ModuleNode(name, parent=self, ast_node=ast_module)
        self._modules[name] = module_node
        return module_node
    
    def get_package(self, name: str) -> 'PackageNode':
        """Get a nested package by name."""
        if name not in self._packages:
            raise KeyError(f"Package '{name}' not found in package '{self.name}'")
        return self._packages[name]
    
    def get_module(self, name: str) -> 'ModuleNode':
        """Get a module by name."""
        if name not in self._modules:
            raise KeyError(f"Module '{name}' not found in package '{self.name}'")
        return self._modules[name]
    
    def list_packages(self) -> List['PackageNode']:
        """List all nested packages in this package."""
        return list(self._packages.values())
    
    def list_modules(self) -> List['ModuleNode']:
        """List all modules in this package."""
        return list(self._modules.values())