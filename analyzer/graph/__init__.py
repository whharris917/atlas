"""
Graph Package - Atlas Rewrite

Hierarchical graph system for representing codebase structure and relationships.
"""

from .base import Node, Edge
from .core import CodebaseGraph
from .nodes import (
    ProjectNode, PackageNode, ModuleNode, ClassNode, 
    FunctionNode, ImportNode, StateNode, ArgumentNode, AttributeNode
)
from .edges import (
    HasPackageEdge, HasModuleEdge, HasClassEdge, HasFunctionEdge,
    HasImportEdge, HasStateEdge, HasArgumentEdge, HasAttributeEdge,
    InheritsFromEdge, CallsMethodEdge, AccessesStateEdge, 
    InstantiatesClassEdge, ReturnsTypeEdge, ParameterTypeEdge
)

__all__ = [
    # Base classes
    'Node', 'Edge', 'CodebaseGraph',
    
    # Node types
    'ProjectNode', 'PackageNode', 'ModuleNode', 'ClassNode',
    'FunctionNode', 'ImportNode', 'StateNode', 'ArgumentNode', 'AttributeNode',
    
    # Edge types
    'HasPackageEdge', 'HasModuleEdge', 'HasClassEdge', 'HasFunctionEdge',
    'HasImportEdge', 'HasStateEdge', 'HasArgumentEdge', 'HasAttributeEdge',
    'InheritsFromEdge', 'CallsMethodEdge', 'AccessesStateEdge',
    'InstantiatesClassEdge', 'ReturnsTypeEdge', 'ParameterTypeEdge'
]
