"""
Tree Foundation - Atlas Rewrite

Basic tree structure for Project -> Package -> Module hierarchy.
Reconnaissance Phase foundation with fluent navigation API.
"""

import ast
from typing import Dict, List, Optional
from pathlib import Path


class TreeNode:
    """Base class for all tree nodes."""
    
    def __init__(self, name: str, ast_node: Optional[ast.AST] = None):
        self.name = name
        self.ast_node = ast_node
        self.parent: Optional['TreeNode'] = None
    
    @property
    def fqn(self) -> str:
        """Generate FQN by walking up the tree."""
        parts = [self.name]
        current = self.parent
        while current and not isinstance(current, ProjectNode):
            parts.append(current.name)
            current = current.parent
        return ".".join(reversed(parts))
    
    def __repr__(self) -> str:
        """Nice string representation showing node type and FQN."""
        node_type = self.__class__.__name__.replace('Node', '')
        return f"{node_type}({self.fqn})"


class ProjectNode(TreeNode):
    """Root node representing the entire project."""
    
    def __init__(self, name: str):
        super().__init__(name)
        self._packages: Dict[str, 'PackageNode'] = {}
        self._modules: Dict[str, 'ModuleNode'] = {}  # Direct modules (no package)
    
    def create_package(self, name: str, init_ast: Optional[ast.Module] = None) -> 'PackageNode':
        """Create and hook a new package."""
        package = PackageNode(name, init_ast=init_ast)
        package.parent = self
        self._packages[name] = package
        return package
    
    def create_module(self, name: str, path: str = "", ast_node: Optional[ast.Module] = None) -> 'ModuleNode':
        """Create and hook a new module directly under project."""
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


class PackageNode(TreeNode):
    """Node representing a Python package."""
    
    def __init__(self, name: str, path: str = "", init_ast: Optional[ast.Module] = None):
        super().__init__(name, init_ast)  # Store init AST as the package's AST node
        self.path = path
        self.init_ast = init_ast  # Also keep separate reference for clarity
        self._packages: Dict[str, 'PackageNode'] = {}  # Nested packages
        self._modules: Dict[str, 'ModuleNode'] = {}
    
    def create_package(self, name: str, path: str = "", init_ast: Optional[ast.Module] = None) -> 'PackageNode':
        """Create and hook a new nested package."""
        package = PackageNode(name, path, init_ast)
        package.parent = self
        self._packages[name] = package
        return package
    
    def create_module(self, name: str, path: str = "", ast_node: Optional[ast.Module] = None) -> 'ModuleNode':
        """Create and hook a new module in this package."""
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


class ModuleNode(TreeNode):
    """Node representing a Python module."""
    
    def __init__(self, name: str, path: str = "", ast_node: Optional[ast.Module] = None):
        super().__init__(name, ast_node)
        self.path = path