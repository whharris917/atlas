"""
Atlas Nodes Package

Consolidated imports for all node types including new type analysis classes.
Maintains backward compatibility while adding type analysis capabilities.
"""

# Core node types
from .project_node import ProjectNode
from .package_node import PackageNode  
from .module_node import ModuleNode
from .class_node import ClassNode
from .function_node import FunctionNode
from .argument_node import ArgumentNode
from .attribute_node import AttributeNode
from .state_node import StateNode
from .return_node import ReturnNode

# Import system nodes
from .alias_node import AliasNode
from .import_node import ImportNode
from .import_from_node import ImportFromNode

# Container nodes  
from .state_container_node import StateContainerNode

# Type analysis nodes (NEW)
from .type_node import TypeNode

# Note: CodeStandardViolation classes moved to ../violations package

# Public API exports
__all__ = [
    # Tree structure nodes
    'ProjectNode', 
    'PackageNode', 
    'ModuleNode',
    'ClassNode', 
    'FunctionNode', 
    'ArgumentNode',
    'AttributeNode',
    'StateNode',
    'ReturnNode',
    
    # Import system
    'AliasNode',
    'ImportNode', 
    'ImportFromNode',
    
    # Container nodes
    'StateContainerNode',
    
    # Type analysis (NEW)
    'TypeNode'
    
    # Note: CodeStandardViolation classes are in ../violations package
]