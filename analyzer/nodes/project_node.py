"""
Project Node - Atlas Rewrite

Root node representing the entire project with automatic child creation.
Extremely focused implementation adhering to strict separation of concerns.
"""

from typing import List, TYPE_CHECKING
from ..core import RootNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from . import PackageNode, ModuleNode
    from ..reconnaissance.discovery import ProjectStructure


class ProjectNode(RootNode):
    """Root node representing the entire project."""
    
    def __init__(self, structure: 'ProjectStructure'):
        if not structure:
            raise ValueError("ProjectNode requires valid ProjectStructure")
        
        # Self-extract name from structure only
        project_name = structure.root_path.name
        if not project_name:
            raise ValueError("ProjectStructure must have valid root_path with name")
        
        # Initialize collections before parent init (which calls _create_children)
        self.structure = structure
        self._packages: List['PackageNode'] = []
        self._modules: List['ModuleNode'] = []
        
        # RootNode handles parentless construction
        super().__init__(project_name)
    
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