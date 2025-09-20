"""
Tree Package - Atlas Rewrite

Tree-based project structure with fluent navigation API.
Reconnaissance Phase foundation with clean modular architecture.
"""

from .base import TreeNode
from .nodes import (
    ProjectNode, PackageNode, ModuleNode, ClassNode, FunctionNode,
    StateNode, ImportNode, ArgumentNode, AttributeNode
)
from .discovery import ProjectDiscovery, discover_project_structure
from .tree_builder import TreeBuilder, build_project_tree
from .entity_discovery import EntityDiscovery, discover_all_entities
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
    'EntityDiscovery', 'discover_all_entities',
    
    # Main orchestrator
    'ProjectBuilder', 'build_sample_project'
]