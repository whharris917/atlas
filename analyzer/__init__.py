"""
Atlas Python Static Analysis Tool

Comprehensive static analysis framework for Python codebases featuring
tree-based reconnaissance, advanced navigation, and precise type analysis.

Enhanced with comprehensive attribute discovery for both class-level
and instance attributes with violation detection.

NEW: Simple tree visualization via ProjectNode.print() and ProjectNode.view().
"""

# Core base classes
from .core import BaseNode, RootNode, TreeNode, ContainerNode

# All node types
from .nodes import (
    ProjectNode, PackageNode, ModuleNode, ClassNode, FunctionNode,
    StateNode, StateContainerNode, ImportNode, ImportFromNode, 
    AliasNode, ArgumentNode, BaseAttributeNode, ClassAttributeNode, InstanceAttributeNode,
    ReturnNode, TypeNode
)

# Main Atlas Builder
from .builder import AtlasBuilder, build_complete_atlas, build_sample_project

# Violation system
from .violations import (
    CodeStandardViolation, MissingArgumentTypeHint, MissingReturnTypeHint,
    MissingClassAttributeTypeHint, MissingInstanceAttributeTypeHint,
    MultipleTargetAttributeAssignment, IncorrectTypeAnnotation
)

# Navigation system
from .core.navigation import NavigationMixin, TraversalScope, NavigationQuery

# Visualization system (simple access via ProjectNode.print())
from .visualization import TreeVisualizer

# Public API exports
__all__ = [
    # Core classes
    'BaseNode', 'RootNode', 'TreeNode', 'ContainerNode',
    
    # Node types
    'ProjectNode', 'PackageNode', 'ModuleNode', 'ClassNode', 'FunctionNode',
    'StateNode', 'StateContainerNode', 'ImportNode', 'ImportFromNode',
    'AliasNode', 'ArgumentNode', 'BaseAttributeNode', 'ClassAttributeNode', 'InstanceAttributeNode',
    'ReturnNode', 'TypeNode',
    
    # Main builder
    'AtlasBuilder', 'build_complete_atlas', 'build_sample_project',
    
    # Violations
    'CodeStandardViolation', 'MissingArgumentTypeHint', 'MissingReturnTypeHint',
    'MissingClassAttributeTypeHint', 'MissingInstanceAttributeTypeHint',
    'MultipleTargetAttributeAssignment', 'IncorrectTypeAnnotation',
    
    # Navigation
    'NavigationMixin', 'TraversalScope', 'NavigationQuery',
    
    # Visualization
    'TreeVisualizer'
]