"""
Atlas Python Static Analysis Tool

Comprehensive static analysis framework for Python codebases featuring
tree-based reconnaissance, advanced navigation, and precise type analysis.

Enhanced with comprehensive attribute discovery for both class-level
and instance attributes with note-based discovery tracking.

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

# Note system - unified hierarchy for all analysis artifacts
from .notes import (
    # Base classes
    Note,
    CodeStandardViolation,
    Warning,
    AtlasLimitation,
    AnalysisResult,
    AnalysisSuccess,
    AnalysisFailure,
    
    # Code standard violations
    MissingArgumentTypeHint,
    MissingReturnTypeHint,
    MissingClassAttributeTypeHint,
    MissingInstanceAttributeTypeHint,
    MultipleTargetAttributeAssignment,
    
    # Warnings
    IncorrectTypeAnnotation,
    
    # Atlas limitations
    UnsupportedExpressionType,
    
    # Analysis successes
    ScopeAddition,
    BaseClassResolution,
    TypeInference,
    ParameterDiscovery,
    
    # Analysis failures
    TypeInferenceFailure,
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
    
    # Note system - base classes
    'Note',
    'CodeStandardViolation',
    'Warning',
    'AtlasLimitation',
    'AnalysisResult',
    'AnalysisSuccess',
    'AnalysisFailure',
    
    # Code standard violations
    'MissingArgumentTypeHint',
    'MissingReturnTypeHint',
    'MissingClassAttributeTypeHint',
    'MissingInstanceAttributeTypeHint',
    'MultipleTargetAttributeAssignment',
    
    # Warnings
    'IncorrectTypeAnnotation',
    
    # Atlas limitations
    'UnsupportedExpressionType',
    
    # Analysis successes
    'ScopeAddition',
    'BaseClassResolution',
    'TypeInference',
    'ParameterDiscovery',
    
    # Analysis failures
    'TypeInferenceFailure',
    
    # Navigation
    'NavigationMixin', 'TraversalScope', 'NavigationQuery',
    
    # Visualization
    'TreeVisualizer'
]