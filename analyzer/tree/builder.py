"""
Project Builder - Atlas Rewrite

Orchestrates the complete Reconnaissance Phase using self-discovering tree nodes.
Clean separation: Discovery -> Tree Building -> Lazy Child Discovery.
"""

from .nodes import ProjectNode
from .discovery import discover_project_structure
from .tree_builder import build_project_tree


class ProjectBuilder:
    """Orchestrates the complete Reconnaissance Phase with self-discovering nodes."""
    
    def __init__(self, project_name: str, root_path: str = "."):
        self.project_name = project_name
        self.root_path = root_path
    
    def execute_reconnaissance_phase(self, target_dir: str = "sample_files") -> ProjectNode:
        """Execute the complete Reconnaissance Phase with lazy discovery."""
        print(f"=== EXECUTING RECONNAISSANCE PHASE ===")
        print(f"Project: {self.project_name}")
        print(f"Target: {target_dir}")
        
        # Phase 1: File I/O and Discovery - gather all data without building tree
        print(f"\n--- Phase 1: Project Structure Discovery ---")
        structure = discover_project_structure(target_dir)
        
        # Phase 2: Tree Building - create Project -> Package -> Module hierarchy with AST
        print(f"\n--- Phase 2: Tree Construction ---")
        project = build_project_tree(self.project_name, structure)
        
        # Phase 3: Trigger discovery on all modules to populate children
        print(f"\n--- Phase 3: Child Entity Discovery ---")
        self._discover_all_children(project)
        
        print(f"\n=== RECONNAISSANCE PHASE COMPLETE ===")
        return project
    
    def _discover_all_children(self, project: ProjectNode):
        """Trigger child discovery on all modules in the project."""
        print("Triggering child discovery on all modules...")
        
        # Discover children in direct modules
        for module in project.list_modules():
            module.discover_children()
            self._discover_nested_children(module)
        
        # Discover children in package modules
        for package in project.list_packages():
            self._discover_package_children(package)
    
    def _discover_package_children(self, package):
        """Recursively discover children in package modules."""
        # Discover in direct modules
        for module in package.list_modules():
            module.discover_children()
            self._discover_nested_children(module)
        
        # Discover in nested packages
        for nested_package in package.list_packages():
            self._discover_package_children(nested_package)
    
    def _discover_nested_children(self, module):
        """Discover children in classes and functions within a module."""
        # Trigger class method discovery
        for class_node in module.list_classes():
            class_node.discover_children()
            # Trigger argument discovery for methods
            for method in class_node.list_methods():
                method.discover_children()
        
        # Trigger argument discovery for module functions
        for function in module.list_functions():
            function.discover_children()


def build_sample_project() -> ProjectNode:
    """Convenience function to execute reconnaissance phase on sample project."""
    builder = ProjectBuilder("sample_project")
    return builder.execute_reconnaissance_phase("sample_files")