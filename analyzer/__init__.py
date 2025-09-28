"""
Atlas Python Static Analysis Tool

Comprehensive static analysis framework for Python codebases featuring
tree-based reconnaissance, advanced navigation, and precise type analysis.

Enhanced with comprehensive attribute discovery for both class-level
and instance attributes with violation detection.
"""

# Core base classes
from .core import BaseNode, RootNode, TreeNode, ContainerNode

# All node types
from .nodes import (
    ProjectNode, PackageNode, ModuleNode, ClassNode, FunctionNode,
    StateNode, StateContainerNode, ImportNode, ImportFromNode, 
    AliasNode, ArgumentNode, ClassAttributeNode, InstanceAttributeNode,
    ReturnNode, TypeNode
)

# Main Atlas Builder
from .builder import AtlasBuilder, build_complete_atlas, build_sample_project

# Violation system
from .violations import (
    CodeStandardViolation, MissingArgumentTypeHint, MissingReturnTypeHint,
    MissingClassAttributeTypeHintViolation, MissingInstanceAttributeTypeHintViolation,
    MultipleTargetAttributeAssignmentViolation
)

# Navigation system
from .core.navigation import NavigationMixin, TraversalScope, NavigationQuery

# Public API exports
__all__ = [
    # Core classes
    'BaseNode', 'RootNode', 'TreeNode', 'ContainerNode',
    
    # Node types
    'ProjectNode', 'PackageNode', 'ModuleNode', 'ClassNode', 'FunctionNode',
    'StateNode', 'StateContainerNode', 'ImportNode', 'ImportFromNode',
    'AliasNode', 'ArgumentNode', 'ClassAttributeNode', 'InstanceAttributeNode',
    'ReturnNode', 'TypeNode',
    
    # Main builder
    'AtlasBuilder', 'build_complete_atlas', 'build_sample_project',
    
    # Violations
    'CodeStandardViolation', 'MissingArgumentTypeHint', 'MissingReturnTypeHint',
    'MissingClassAttributeTypeHintViolation', 'MissingInstanceAttributeTypeHintViolation',
    'MultipleTargetAttributeAssignmentViolation',
    
    # Navigation
    'NavigationMixin', 'TraversalScope', 'NavigationQuery'
]