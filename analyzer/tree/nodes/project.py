"""
Project Node - Atlas Rewrite

Root node representing the entire project.
"""

import ast
from typing import Dict, List, Optional, TYPE_CHECKING
from ..base import TreeNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from .package import PackageNode
    from .module import ModuleNode


class ProjectNode(TreeNode):
    """Root node representing the entire project."""
    
    def __init__(self, name: str):
        super().__init__(name, None)  # ProjectNode has no AST
        self._packages: Dict[str, 'PackageNode'] = {}
        self._modules: Dict[str, 'ModuleNode'] = {}  # Direct modules (no package)
    
    def create_package(self, name: str, path: str, ast_node: ast.Module) -> 'PackageNode':
        """Create and hook a new package."""
        from .package import PackageNode
        package = PackageNode(name, path, ast_node)
        package.parent = self
        self._packages[name] = package
        return package
    
    def create_module(self, name: str, path: str, ast_node: ast.Module) -> 'ModuleNode':
        """Create and hook a new module directly under project."""
        from .module import ModuleNode
        module = ModuleNode(name, path, ast_node)
        module.parent = self
        self._modules[name] = module
        return module
    
    def get_package(self, name: str) -> 'PackageNode':
        """Get a package by name."""
        if name not in self._packages:
            raise KeyError(f"Package '{name}' not found")
        return self._packages[name]
    
    def get_module(self, name: str) -> 'ModuleNode':
        """Get a direct module by name."""
        if name not in self._modules:
            raise KeyError(f"Module '{name}' not found")
        return self._modules[name]
    
    def list_packages(self) -> List['PackageNode']:
        """List all packages in the project."""
        return list(self._packages.values())
    
    def list_modules(self) -> List['ModuleNode']:
        """List all direct modules in the project."""
        return list(self._modules.values())