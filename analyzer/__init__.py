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
    StateNode, ImportNode, ImportFromNode, AliasNode, ArgumentNode, AttributeNode
)

# Main Atlas Builder
from .builder import AtlasBuilder, build_complete_atlas, build_sample_project

# Reconnaissance Phase components (TreeBuilder removed)
from .reconnaissance import (
    ProjectDiscovery, discover_project_structure,
    ModuleReconnaissanceVisitor, ClassReconnaissanceVisitor, FunctionReconnaissanceVisitor
)

# Analysis Phase (future)
# from .analysis import ...

__all__ = [
    # Core
    'TreeNode',
    
    # Nodes
    'ProjectNode', 'PackageNode', 'ModuleNode', 'ClassNode', 'FunctionNode',
    'StateNode', 'ImportNode', 'ImportFromNode', 'AliasNode', 'ArgumentNode', 'AttributeNode',
    
    # Main Atlas Builder
    'AtlasBuilder', 'build_complete_atlas', 'build_sample_project',
    
    # Reconnaissance components
    'ProjectDiscovery', 'discover_project_structure',
    'ModuleReconnaissanceVisitor', 'ClassReconnaissanceVisitor', 'FunctionReconnaissanceVisitor'
]