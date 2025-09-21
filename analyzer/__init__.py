"""
Analyzer Package - Atlas Rewrite

Main entry point for the Atlas static analysis tool.
Clean package structure with focused responsibilities.
"""

# Core infrastructure
from .core import TreeNode

# All node types
from .nodes import (
    ProjectNode, PackageNode, ModuleNode, ClassNode, FunctionNode,
    StateNode, ImportNode, ArgumentNode, AttributeNode
)

# Main Atlas Builder (moved from reconnaissance)
from .builder import AtlasBuilder, build_complete_atlas, build_sample_project

# Reconnaissance Phase components
from .reconnaissance import (
    ProjectDiscovery, discover_project_structure,
    TreeBuilder, build_project_tree,
    ModuleReconnaissanceVisitor, ClassReconnaissanceVisitor, FunctionReconnaissanceVisitor
)

# Analysis Phase (future)
# from .analysis import ...

__all__ = [
    # Core
    'TreeNode',
    
    # Nodes
    'ProjectNode', 'PackageNode', 'ModuleNode', 'ClassNode', 'FunctionNode',
    'StateNode', 'ImportNode', 'ArgumentNode', 'AttributeNode',
    
    # Main Atlas Builder
    'AtlasBuilder', 'build_complete_atlas', 'build_sample_project',
    
    # Reconnaissance components
    'ProjectDiscovery', 'discover_project_structure', 
    'TreeBuilder', 'build_project_tree',
    'ModuleReconnaissanceVisitor', 'ClassReconnaissanceVisitor', 'FunctionReconnaissanceVisitor'
]