"""
Package Node - Atlas Rewrite

Node representing a Python package.
"""

import ast
from typing import Dict, List, Optional, TYPE_CHECKING
from ..core import TreeNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from . import ModuleNode


class PackageNode(TreeNode):
    """Node representing a Python package."""
    
    def __init__(self, name: str, ast_node: ast.Module):
        super().__init__(name, ast_node)  # Store package AST as the node's AST
        self._packages: Dict[str, 'PackageNode'] = {}  # Self-reference must be string
        self._modules: Dict[str, 'ModuleNode'] = {}
    
    def create_package(self, name: str, ast_node: ast.Module) -> 'PackageNode':
        """Create and hook a new nested package."""
        package = PackageNode(name, ast_node)
        package.parent = self
        self._packages[name] = package
        return package
    
    def create_module(self, name: str, ast_node: ast.Module) -> 'ModuleNode':
        """Create and hook a new module in this package."""
        from . import ModuleNode
        module = ModuleNode(name, ast_node)
        module.parent = self
        self._modules[name] = module
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