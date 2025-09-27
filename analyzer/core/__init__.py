"""
Core Package - Atlas Rewrite

Foundation infrastructure for Atlas tree nodes.
Refined hierarchy: BaseNode → RootNode/TreeNode/ContainerNode
Enhanced navigation system with three-tier scope control.

REORGANIZED: Navigation system extracted to navigation.py for focused organization.
"""

from .base import BaseNode, RootNode, TreeNode, ContainerNode

__all__ = ['BaseNode', 'RootNode', 'TreeNode', 'ContainerNode']