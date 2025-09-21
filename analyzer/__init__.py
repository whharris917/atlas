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

# Reconnaissance Phase
from .reconnaissance import (
    ProjectBuilder, build_sample_project,
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
    
    # Reconnaissance
    'ProjectBuilder', 'build_sample_project',
    'ProjectDiscovery', 'discover_project_structure', 
    'TreeBuilder', 'build_project_tree',
    'ModuleReconnaissanceVisitor', 'ClassReconnaissanceVisitor', 'FunctionReconnaissanceVisitor'
]