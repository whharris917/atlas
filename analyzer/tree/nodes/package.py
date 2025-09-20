"""
Package Node - Atlas Rewrite

Node representing a Python package.
"""

import ast
from typing import Dict, List, Optional, TYPE_CHECKING
from ..base import TreeNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from .module import ModuleNode


class PackageNode(TreeNode):
    """Node representing a Python package."""
    
    def __init__(self, name: str, path: str = "", init_ast: Optional[ast.Module] = None):
        super().__init__(name, init_ast)  # Store init AST as the package's AST node
        self.path = path
        self.init_ast = init_ast  # Also keep separate reference for clarity
        self._packages: Dict[str, 'PackageNode'] = {}  # Self-reference must be string
        self._modules: Dict[str, 'ModuleNode'] = {}
    
    def create_package(self, name: str, path: str = "", init_ast: Optional[ast.Module] = None) -> 'PackageNode':
        """Create and hook a new nested package."""
        package = PackageNode(name, path, init_ast)
        package.parent = self
        self._packages[name] = package
        return package
    
    def create_module(self, name: str, path: str = "", ast_node: Optional[ast.Module] = None) -> 'ModuleNode':
        """Create and hook a new module in this package."""
        from .module import ModuleNode
        module = ModuleNode(name, path, ast_node)
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