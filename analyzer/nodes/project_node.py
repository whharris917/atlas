"""
Project Node - Atlas Rewrite

Root node representing the entire project with automatic child creation.
Creates all top-level PackageNodes and ModuleNodes immediately.
Pure self-extracting architecture - name from structure or default.
"""

from typing import List, Optional, TYPE_CHECKING
from ..core import TreeNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from . import PackageNode, ModuleNode
    from ..reconnaissance.discovery import ProjectStructure


class ProjectNode(TreeNode):
    """Root node representing the entire project."""
    
    def __init__(self, structure: 'ProjectStructure'):
        if not structure:
            raise ValueError("ProjectNode requires valid ProjectStructure")
        
        # Self-extract name from structure only
        project_name = structure.root_path.name
        if not project_name:
            raise ValueError("ProjectStructure must have valid root_path with name")
        
        # ProjectNode is the only node that can be parentless
        super().__init__(project_name, parent=None)
        self.structure = structure
        self._packages: List['PackageNode'] = []
        self._modules: List['ModuleNode'] = []
        
        # Create all children immediately
        self._create_children()
    
    def _create_children(self):
        """Create child nodes from ProjectStructure."""
        
        print(f"\n=== BUILDING PROJECT TREE ===")
        print(f"Project: {self.name}")
        
        # Create direct modules from ProjectStructure
        for module_data in self.structure.direct_modules:
            if module_data.ast_node:
                self.create_module(module_data)
        
        # Create packages from ProjectStructure (which will create their own children)
        for package_data in self.structure.packages:
            self.create_package(package_data)
    
    def create_package(self, package_data) -> 'PackageNode':
        """Create and hook a top-level package from DiscoveredPackage."""
        from . import PackageNode
        package_node = PackageNode(package_data, parent=self)
        self._packages.append(package_node)
        return package_node
    
    def create_module(self, module_data) -> 'ModuleNode':
        """Create and hook a top-level module from DiscoveredModule."""
        from . import ModuleNode
        module_node = ModuleNode(module_data, parent=self)
        self._modules.append(module_node)
        return module_node
    
    def get_package(self, name: str) -> 'PackageNode':
        """Get a package by name."""
        for package in self._packages:
            if package.name == name:
                return package
        raise KeyError(f"Package '{name}' not found in project '{self.name}'")
    
    def get_module(self, name: str) -> 'ModuleNode':
        """Get a module by name."""
        for module in self._modules:
            if module.name == name:
                return module
        raise KeyError(f"Module '{name}' not found in project '{self.name}'")
    
    def list_packages(self) -> List['PackageNode']:
        """List all packages in this project."""
        return self._packages
    
    def list_modules(self) -> List['ModuleNode']:
        """List all modules in this project."""
        return self._modules