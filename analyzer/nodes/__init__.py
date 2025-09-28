"""
Atlas Nodes Package

Consolidated imports for all node types including enhanced attribute discovery.
Updated with BaseAttributeNode, ClassAttributeNode and InstanceAttributeNode for comprehensive attribute analysis.
"""

# Core node types
from .project_node import ProjectNode
from .package_node import PackageNode  
from .module_node import ModuleNode
from .class_node import ClassNode
from .function_node import FunctionNode
from .argument_node import ArgumentNode
from .base_attribute_node import BaseAttributeNode
from .class_attribute_node import ClassAttributeNode
from .instance_attribute_node import InstanceAttributeNode
from .state_node import StateNode
from .return_node import ReturnNode

# Import system nodes
from .alias_node import AliasNode
from .import_node import ImportNode
from .import_from_node import ImportFromNode

# Container nodes  
from .state_container_node import StateContainerNode

# Type analysis nodes
from .type_node import TypeNode

# Public API exports
__all__ = [
    # Tree structure nodes
    'ProjectNode', 
    'PackageNode', 
    'ModuleNode',
    'ClassNode', 
    'FunctionNode', 
    'ArgumentNode',
    'BaseAttributeNode',
    'ClassAttributeNode',
    'InstanceAttributeNode',
    'StateNode',
    'ReturnNode',
    
    # Import system
    'AliasNode',
    'ImportNode', 
    'ImportFromNode',
    
    # Container nodes
    'StateContainerNode',
    
    # Type analysis
    'TypeNode'
]