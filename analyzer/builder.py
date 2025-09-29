"""
Atlas Project Builder - Main Orchestrator

Coordinates the complete Atlas analysis pipeline:
- Reconnaissance Phase (structural discovery)
- Analysis Phase (behavioral relationships) 
- Final Atlas Code Map generation

Updated for pure self-extracting TreeNode architecture.
"""

from .nodes import ProjectNode
from .reconnaissance.discovery import discover_project_structure


class AtlasBuilder:
    """Main orchestrator for the complete Atlas analysis pipeline."""
    
    def __init__(self, root_path: str = "."):
        self.root_path = root_path
    
    def build_complete_atlas(self, target_dir: str = "sample_files") -> ProjectNode:
        """Build complete Atlas code map through all phases."""
        # Phase 1: Reconnaissance (structural discovery)
        project = self._execute_reconnaissance_phase(target_dir)
        
        # Phase 2: Analysis (behavioral relationships) - Future implementation
        # project = self._execute_analysis_phase(project)
        
        # Phase 3: Atlas Code Map Generation - Future implementation
        # atlas_map = self._generate_atlas_code_map(project)
        
        return project
    
    def _execute_reconnaissance_phase(self, target_dir: str) -> ProjectNode:
        """Execute the Reconnaissance Phase (structural discovery)."""
        structure = discover_project_structure(target_dir)
        project = ProjectNode(structure)  # Pure self-extraction
        return project


def build_complete_atlas(target_dir: str = "sample_files") -> ProjectNode:
    """Convenience function to build complete Atlas code map."""
    builder = AtlasBuilder()
    return builder.build_complete_atlas(target_dir)


# Backward compatibility for existing demos
def build_sample_project() -> ProjectNode:
    """Legacy convenience function - use build_complete_atlas() instead."""
    return build_complete_atlas("sample_files")