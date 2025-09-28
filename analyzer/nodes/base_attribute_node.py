"""
Base Attribute Node - Atlas Rewrite

Abstract base class for attribute nodes with common type analysis patterns.
Provides shared functionality for both class-level and instance attributes.
"""

import ast
from abc import abstractmethod
from typing import Union, Optional, List
from ..core import TreeNode, BaseNode
from .type_node import TypeNode
from ..violations import CodeStandardViolation


class BaseAttributeNode(TreeNode):
    """
    Abstract base class for attribute nodes.
    
    Provides common functionality for both ClassAttributeNode and InstanceAttributeNode,
    including type analysis patterns and annotation handling.
    """
    
    def __init__(self, parent: BaseNode, source_data: Union[ast.AnnAssign, ast.Assign]):
        if not isinstance(source_data, (ast.AnnAssign, ast.Assign)):
            raise TypeError("BaseAttributeNode requires ast.AnnAssign or ast.Assign as source_data")
        
        # Initialize collections before parent init (which calls _create_children)
        self._type: Optional[TypeNode] = None
        self._violations: List[CodeStandardViolation] = []
        
        # Parent class handles name extraction and validation
        super().__init__(parent, source_data)
    
    @abstractmethod
    def _extract_name(self) -> str:
        """Extract attribute name from assignment AST node - implemented by subclasses."""
        pass
    
    @abstractmethod
    def _create_missing_type_hint_violation(self) -> CodeStandardViolation:
        """Create appropriate missing type hint violation - implemented by subclasses."""
        pass
    
    def _create_children(self):
        """
        Final step of Reconnaissance Phase: analyze type information.
        
        Every BaseAttributeNode creates exactly one child, enforcing complete type
        analysis coverage:
        
        - TypeNode: when attribute has type annotation
        - MissingTypeHint violation: when type hint is missing
        
        This ensures Atlas identifies ALL attributes requiring type documentation.
        """
        annotation = self._get_annotation()
        if annotation is not None:
            # Type annotation exists - create TypeNode child
            self._create_type_node(annotation)
        else:
            # No type annotation - create violation ornament
            self._create_missing_type_hint_violation()
    
    def _get_annotation(self) -> Optional[ast.AST]:
        """Get the type annotation AST node, or None if no annotation exists."""
        if isinstance(self.source_data, ast.AnnAssign):
            return self.source_data.annotation
        else:  # ast.Assign
            return None  # Plain assignments have no type annotations
    
    def _create_type_node(self, type_ast: ast.AST) -> TypeNode:
        """
        Create TypeNode child from type annotation AST.
        
        Private method - only called internally during type analysis.
        
        Args:
            type_ast: The AST node representing the type annotation
        
        Returns:
            The created TypeNode
        """
        self._type = TypeNode(parent=self, source_data=type_ast)
        return self._type