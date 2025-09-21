"""
Project Node - Atlas Rewrite

Root node representing the entire project.
Creates all PackageNodes and ModuleNodes from project structure.
"""

import ast
from typing import Dict, List, Optional, TYPE_CHECKING
from ..core import TreeNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from . import PackageNode, ModuleNode
    from ..reconnaissance.discovery import ProjectStructure


class ProjectNode(TreeNode):
    """Root node representing the entire project."""
    
    def __init__(self, name: str, structure: 'ProjectStructure'):
        if not structure:
            raise ValueError(f"ProjectNode '{name}' requires valid project structure")
        
        super().__init__(name, None)  # ProjectNode has no AST
        self.structure = structure
        self._packages: Dict[str, 'PackageNode'] = {}
        self._modules: Dict[str, 'ModuleNode'] = {}  # Direct modules (no package)
        
        # Create all children immediately
        self._create_children()
    
    def _create_children(self):
        """Create all PackageNodes and ModuleNodes from project structure."""
        print(f"\n=== BUILDING PROJECT TREE ===")
        print(f"Project: {self.name}")
        
        # Create direct modules
        for module_data in self.structure.direct_modules:
            self._create_module(module_data.name, module_data.ast_node)
        
        # Create packages (which will create their own children)
        for package_data in self.structure.packages:
            self._create_package(package_data.name, package_data.ast_node, package_data)
        
        print(f"Tree construction complete: {len(self.structure.direct_modules)} direct modules, {len(self.structure.packages)} packages")
    
    def _create_package(self, name: str, ast_node: ast.Module, package_data) -> 'PackageNode':
        """Create and hook a new package."""
        from . import PackageNode
        package = PackageNode(name, ast_node, package_data)
        package.parent = self
        self._packages[name] = package
        print(f"  Added package: {package.fqn}")
        return package
    
    def _create_module(self, name: str, ast_node: ast.Module) -> 'ModuleNode':
        """Create and hook a new module directly under project."""
        from . import ModuleNode
        module = ModuleNode(name, ast_node)
        module.parent = self
        self._modules[name] = module
        print(f"  Added module: {module.fqn}")
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