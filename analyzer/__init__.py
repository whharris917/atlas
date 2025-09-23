"""
Analyzer Package - Atlas Rewrite

Main entry point for the Atlas static analysis tool.
Clean package structure with refined node hierarchy.
"""

# Core infrastructure
from .core import BaseNode, RootNode, TreeNode, ContainerNode

# All node types
from .nodes import (
    ProjectNode, PackageNode, ModuleNode, ClassNode, FunctionNode,
    StateNode, StateContainerNode, ImportNode, ImportFromNode, 
    AliasNode, ArgumentNode, AttributeNode
)

# Main Atlas Builder
from .builder import AtlasBuilder, build_complete_atlas, build_sample_project

# Reconnaissance Phase components
from .reconnaissance import (
    ProjectDiscovery, discover_project_structure,
    ModuleReconnaissanceVisitor, ClassReconnaissanceVisitor, FunctionReconnaissanceVisitor
)

# Analysis Phase (future)
# from .analysis import ...

__all__ = [
    # Core
    'BaseNode', 'RootNode', 'TreeNode', 'ContainerNode',
    
    # Nodes
    'ProjectNode', 'PackageNode', 'ModuleNode', 'ClassNode', 'FunctionNode',
    'StateNode', 'StateContainerNode', 'ImportNode', 'ImportFromNode', 
    'AliasNode', 'ArgumentNode', 'AttributeNode',
    
    # Main Atlas Builder
    'AtlasBuilder', 'build_complete_atlas', 'build_sample_project',
    
    # Reconnaissance components
    'ProjectDiscovery', 'discover_project_structure',
    'ModuleReconnaissanceVisitor', 'ClassReconnaissanceVisitor', 'FunctionReconnaissanceVisitor'
]