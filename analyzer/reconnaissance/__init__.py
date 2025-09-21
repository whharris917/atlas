"""
Reconnaissance Package - Atlas Rewrite

Complete Reconnaissance Phase implementation with focused organization.
Handles project discovery, tree building, and AST-based entity discovery.
"""

from .discovery import ProjectDiscovery, discover_project_structure
from .tree_builder import TreeBuilder, build_project_tree
from .builder import ProjectBuilder, build_sample_project
from .visitors import (
    ModuleReconnaissanceVisitor, 
    ClassReconnaissanceVisitor, 
    FunctionReconnaissanceVisitor
)

__all__ = [
    # Discovery components
    'ProjectDiscovery', 'discover_project_structure',
    'TreeBuilder', 'build_project_tree',
    
    # Specialized visitors
    'ModuleReconnaissanceVisitor', 'ClassReconnaissanceVisitor', 'FunctionReconnaissanceVisitor',
    
    # Main orchestrator
    'ProjectBuilder', 'build_sample_project'
]