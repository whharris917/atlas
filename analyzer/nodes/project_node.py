"""
Project Node - Atlas Rewrite

Root node representing the entire project with automatic child creation.
Creates all top-level PackageNodes and ModuleNodes immediately.
"""

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
            raise ValueError(f"ProjectNode '{name}' requires valid ProjectStructure")
        
        # ProjectNode is the only node that can be parentless
        super().__init__(name, parent=None)
        self.structure = structure
        self._packages: Dict[str, 'PackageNode'] = {}
        self._modules: Dict[str, 'ModuleNode'] = {}
        
        # Create all children immediately
        self._create_children()
    
    def _create_children(self):
        """Create child nodes from ProjectStructure."""
        
        print(f"\n=== BUILDING PROJECT TREE ===")
        print(f"Project: {self.name}")
        
        # Create direct modules from ProjectStructure
        for module_data in self.structure.direct_modules:
            if module_data.ast_node:
                self.create_module(module_data.name, module_data.ast_node)
        
        # Create packages from ProjectStructure (which will create their own children)
        for package_data in self.structure.packages:
            self.create_package(package_data.name, package_data)
    
    def create_package(self, name: str, package_data) -> 'PackageNode':
        """Create and hook a top-level package from DiscoveredPackage."""
        from . import PackageNode
        package_node = PackageNode(name, parent=self, package_data=package_data)
        self._packages[name] = package_node
        return package_node
    
    def create_module(self, name: str, ast_module) -> 'ModuleNode':
        """Create and hook a top-level module from AST."""
        from . import ModuleNode
        module_node = ModuleNode(name, parent=self, ast_node=ast_module)
        self._modules[name] = module_node
        return module_node
    
    def get_package(self, name: str) -> 'PackageNode':
        """Get a package by name."""
        if name not in self._packages:
            raise KeyError(f"Package '{name}' not found in project '{self.name}'")
        return self._packages[name]
    
    def get_module(self, name: str) -> 'ModuleNode':
        """Get a module by name."""
        if name not in self._modules:
            raise KeyError(f"Module '{name}' not found in project '{self.name}'")
        return self._modules[name]
    
    def list_packages(self) -> List['PackageNode']:
        """List all packages in this project."""
        return list(self._packages.values())
    
    def list_modules(self) -> List['ModuleNode']:
        """List all modules in this project."""
        return list(self._modules.values())