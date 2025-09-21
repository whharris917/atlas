"""
Tree Package - Atlas Rewrite

Tree-based project structure with fluent navigation API.
Reconnaissance Phase foundation with ReconnaissanceVisitor.
"""

from .base import TreeNode
from .nodes import (
    ProjectNode, PackageNode, ModuleNode, ClassNode, FunctionNode,
    StateNode, ImportNode, ArgumentNode, AttributeNode
)
from .discovery import ProjectDiscovery, discover_project_structure
from .tree_builder import TreeBuilder, build_project_tree
from .reconnaissance_visitor import (
    ModuleReconnaissanceVisitor, ClassReconnaissanceVisitor, FunctionReconnaissanceVisitor
)
from .builder import ProjectBuilder, build_sample_project

__all__ = [
    # Base classes
    'TreeNode',
    
    # Node types
    'ProjectNode', 'PackageNode', 'ModuleNode', 'ClassNode', 'FunctionNode',
    'StateNode', 'ImportNode', 'ArgumentNode', 'AttributeNode',
    
    # Discovery components
    'ProjectDiscovery', 'discover_project_structure',
    'TreeBuilder', 'build_project_tree', 
    'ModuleReconnaissanceVisitor', 'ClassReconnaissanceVisitor', 'FunctionReconnaissanceVisitor',
    
    # Main orchestrator
    'ProjectBuilder', 'build_sample_project'
]