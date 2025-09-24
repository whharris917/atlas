"""
Package Node - Atlas Rewrite

Node representing a Python package with automatic child creation.
Creates all nested PackageNodes and ModuleNodes immediately.
Pure self-extracting architecture - name from package_data.
"""

from typing import List, Optional, TYPE_CHECKING
from ..core import TreeNode, BaseNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from . import ModuleNode
    from ..reconnaissance.discovery import DiscoveredPackage


class PackageNode(TreeNode):
    """Node representing a Python package."""
    
    def __init__(self, package_data: 'DiscoveredPackage', parent: BaseNode):
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