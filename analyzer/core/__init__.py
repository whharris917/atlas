"""
Core Package - Atlas Rewrite

Foundation infrastructure for the Atlas static analysis tool.
Contains base classes and shared types.
"""

from .base import TreeNode
from .container_node import ContainerNode

__all__ = ['TreeNode', 'ContainerNode']