"""
Package Node - Atlas Rewrite

Node representing a Python package.
Creates all nested PackageNodes and ModuleNodes from package data.
"""

import ast
from typing import Dict, List, Optional, TYPE_CHECKING
from ..core import TreeNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from . import ModuleNode
    from ..reconnaissance.discovery import DiscoveredPackage


class PackageNode(TreeNode):
    """Node representing a Python package."""
    
    def __init__(self, name: str, ast_node: ast.Module, package_data: 'DiscoveredPackage'):
        super().__init__(name, ast_node)  # Store package AST as the node's AST
        self.package_data = package_data
        self._packages: Dict[str, 'PackageNode'] = {}  # Self-reference must be string
        self._modules: Dict[str, 'ModuleNode'] = {}
        
        # Create all children immediately
        self._create_children()
    
    def _create_children(self):
        """Create all nested PackageNodes and ModuleNodes from package data."""
        # Create modules in this package
        for module_data in self.package_data.modules:
            self._create_module(module_data.name, module_data.ast_node)
        
        # Create nested packages (which will create their own children)
        for nested_package_data in self.package_data.nested_packages:
            self._create_package(nested_package_data.name, nested_package_data.ast_node, nested_package_data)
    
    def _create_package(self, name: str, ast_node: ast.Module, package_data: 'DiscoveredPackage') -> 'PackageNode':
        """Create and hook a new nested package."""
        package = PackageNode(name, ast_node, package_data)
        package.parent = self
        self._packages[name] = package
        print(f"  Added package: {package.fqn}")
        return package
    
    def _create_module(self, name: str, ast_node: ast.Module) -> 'ModuleNode':
        """Create and hook a new module in this package."""
        from . import ModuleNode
        module = ModuleNode(name, ast_node)
        module.parent = self
        self._modules[name] = module
        print(f"  Added module: {module.fqn}")
        return module
    
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