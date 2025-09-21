"""
Atlas Project Builder - Main Orchestrator

Coordinates the complete Atlas analysis pipeline:
- Reconnaissance Phase (structural discovery)
- Analysis Phase (behavioral relationships) 
- Final Atlas Code Map generation

This is the main entry point for Atlas analysis.
"""

from .nodes import ProjectNode
from .reconnaissance.discovery import discover_project_structure
from .reconnaissance.tree_builder import build_project_tree


class AtlasBuilder:
    """Main orchestrator for the complete Atlas analysis pipeline."""
    
    def __init__(self, project_name: str, root_path: str = "."):
        self.project_name = project_name
        self.root_path = root_path
    
    def build_complete_atlas(self, target_dir: str = "sample_files") -> ProjectNode:
        """Build complete Atlas code map through all phases."""
        print(f"=== ATLAS STATIC ANALYSIS PIPELINE ===")
        print(f"Project: {self.project_name}")
        print(f"Target: {target_dir}")
        
        # Phase 1: Reconnaissance (structural discovery)
        project = self._execute_reconnaissance_phase(target_dir)
        
        # Phase 2: Analysis (behavioral relationships) - Future implementation
        # project = self._execute_analysis_phase(project)
        
        # Phase 3: Atlas Code Map Generation - Future implementation
        # atlas_map = self._generate_atlas_code_map(project)
        
        print(f"\n=== ATLAS ANALYSIS COMPLETE ===")
        return project
    
    def _execute_reconnaissance_phase(self, target_dir: str) -> ProjectNode:
        """Execute the Reconnaissance Phase (structural discovery)."""
        print(f"\n--- RECONNAISSANCE PHASE ---")
        
        # Phase 1: File I/O and Discovery
        print(f"Phase 1: Project Structure Discovery")
        structure = discover_project_structure(target_dir)
        
        # Phase 2: Tree Building
        print(f"Phase 2: Tree Construction")
        project = build_project_tree(self.project_name, structure)
        
        # Phase 3: Entity Discovery
        print(f"Phase 3: Visitor-Based Entity Creation")
        self._create_all_children(project)
        
        print(f"RECONNAISSANCE PHASE COMPLETE")
        return project
    
    def _create_all_children(self, project: ProjectNode):
        """Trigger visitor-based child creation on all modules in the project."""
        print("Triggering visitor-based child creation on all modules...")
        
        # Create children in direct modules
        for module in project.list_modules():
            module.create_children()
            self._create_nested_children(module)
        
        # Create children in package modules
        for package in project.list_packages():
            self._create_package_children(package)
    
    def _create_package_children(self, package):
        """Recursively create children in package modules."""
        # Create in direct modules
        for module in package.list_modules():
            module.create_children()
            self._create_nested_children(module)
        
        # Create in nested packages
        for nested_package in package.list_packages():
            self._create_package_children(nested_package)
    
    def _create_nested_children(self, module):
        """Create children in classes and functions within a module."""
        # Trigger class method creation
        for class_node in module.list_classes():
            class_node.create_children()
            # Trigger argument creation for methods
            for method in class_node.list_methods():
                method.create_children()
        
        # Trigger argument creation for module functions
        for function in module.list_functions():
            function.create_children()


def build_complete_atlas(project_name: str = "sample_project", target_dir: str = "sample_files") -> ProjectNode:
    """Convenience function to build complete Atlas code map."""
    builder = AtlasBuilder(project_name)
    return builder.build_complete_atlas(target_dir)


# Backward compatibility for existing demos
def build_sample_project() -> ProjectNode:
    """Legacy convenience function - use build_complete_atlas() instead."""
    return build_complete_atlas("sample_project", "sample_files")