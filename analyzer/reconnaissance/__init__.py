"""
Reconnaissance Package - Atlas Rewrite

Reconnaissance Phase implementation with focused organization.
Handles project discovery, tree building, and AST-based entity discovery.

Note: Main orchestration moved to analyzer/builder.py for clean separation.
"""

from .discovery import ProjectDiscovery, discover_project_structure
from .tree_builder import TreeBuilder, build_project_tree
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
    'ModuleReconnaissanceVisitor', 'ClassReconnaissanceVisitor', 'FunctionReconnaissanceVisitor'
]