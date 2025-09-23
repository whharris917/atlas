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
        print(f"=== ATLAS STATIC ANALYSIS PIPELINE ===")
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
        
        # Phase 2: Create ProjectNode (which creates entire tree automatically)
        print(f"Phase 2: Tree Construction with Entity Discovery")
        project = ProjectNode(structure)  # Pure self-extraction
        
        print(f"RECONNAISSANCE PHASE COMPLETE")
        return project


def build_complete_atlas(target_dir: str = "sample_files") -> ProjectNode:
    """Convenience function to build complete Atlas code map."""
    builder = AtlasBuilder()
    return builder.build_complete_atlas(target_dir)


# Backward compatibility for existing demos
def build_sample_project() -> ProjectNode:
    """Legacy convenience function - use build_complete_atlas() instead."""
    return build_complete_atlas("sample_files")