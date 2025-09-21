"""
Tree Builder - Atlas Rewrite

Builds Project -> Package -> Module tree structure from discovered data.
Pure tree construction without file I/O.
"""

from typing import Dict, List
from ..nodes import ProjectNode, PackageNode, ModuleNode
from .discovery import ProjectStructure, DiscoveredPackage, DiscoveredModule


class TreeBuilder:
    """Builds tree structure from discovered project data."""
    
    def __init__(self, project_name: str):
        self.project_name = project_name
    
    def build_project_tree(self, structure: ProjectStructure) -> ProjectNode:
        """Build Project -> Package -> Module tree from discovered structure."""
        print(f"\n=== BUILDING PROJECT TREE ===")
        print(f"Project: {self.project_name}")
        
        # Create root project node
        project = ProjectNode(self.project_name)
        
        # Add direct modules to project
        for module_data in structure.direct_modules:
            self._add_module_to_parent(project, module_data)
        
        # Add packages to project
        for package_data in structure.packages:
            self._add_package_to_parent(project, package_data)
        
        print(f"Tree construction complete: {len(structure.direct_modules)} direct modules, {len(structure.packages)} packages")
        return project
    
    def _add_package_to_parent(self, parent_node, package_data: DiscoveredPackage) -> PackageNode:
        """Add a package and its contents to a parent node."""
        # Create package node
        package_node = parent_node.create_package(
            name=package_data.name,
            ast_node=package_data.ast_node
        )
        
        print(f"  Added package: {package_node.fqn}")
        
        # Add modules to this package
        for module_data in package_data.modules:
            self._add_module_to_parent(package_node, module_data)
        
        # Add nested packages recursively
        for nested_package_data in package_data.nested_packages:
            self._add_package_to_parent(package_node, nested_package_data)
        
        return package_node
    
    def _add_module_to_parent(self, parent_node, module_data: DiscoveredModule) -> ModuleNode:
        """Add a module to a parent node."""
        module_node = parent_node.create_module(
            name=module_data.name,
            ast_node=module_data.ast_node
        )
        
        print(f"  Added module: {module_node.fqn}")
        return module_node


def build_project_tree(project_name: str, structure: ProjectStructure) -> ProjectNode:
    """Convenience function to build project tree."""
    builder = TreeBuilder(project_name)
    return builder.build_project_tree(structure)