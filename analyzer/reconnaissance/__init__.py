"""
Reconnaissance Package - Atlas Rewrite

Reconnaissance Phase implementation with focused organization.
Handles project discovery and AST-based entity discovery.

Note: TreeBuilder removed - logic moved to ProjectNode and PackageNode.
Main orchestration handled by analyzer/builder.py.
"""

from .discovery import ProjectDiscovery, discover_project_structure
from .visitors import (
    ModuleReconnaissanceVisitor, 
    ClassReconnaissanceVisitor, 
    FunctionReconnaissanceVisitor
)

__all__ = [
    # Discovery components
    'ProjectDiscovery', 'discover_project_structure',
    
    # Specialized visitors
    'ModuleReconnaissanceVisitor', 'ClassReconnaissanceVisitor', 'FunctionReconnaissanceVisitor'
]