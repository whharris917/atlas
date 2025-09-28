"""
Instance Attribute Node - Atlas Rewrite

Node representing an instance attribute with type analysis.
Handles both annotated and unannotated instance attributes defined in __init__ method.
"""

import ast
from typing import Union, Optional, TYPE_CHECKING
from ..core import TreeNode
from .type_node import TypeNode

if TYPE_CHECKING:
    from .class_node import ClassNode


class InstanceAttributeNode(TreeNode):
    """Node representing an instance attribute."""
    
    def __init__(self, parent: 'ClassNode', source_data: Union[ast.AnnAssign, ast.Assign]):
        if not isinstance(source_data, (ast.AnnAssign, ast.Assign)):
            raise TypeError("InstanceAttributeNode requires ast.AnnAssign or ast.Assign as source_data")
        
        # Validate that assignment has self.attr target pattern
        # (We trust ClassReconnaissanceVisitor to provide valid instance attribute assignments)
        if isinstance(source_data, ast.AnnAssign):
            if not (isinstance(source_data.target, ast.Attribute) and 
                    isinstance(source_data.target.value, ast.Name) and 
                    source_data.target.value.id == "self"):
                raise ValueError("InstanceAttributeNode requires ast.AnnAssign with self.attr target")
        elif isinstance(source_data, ast.Assign):
            target = source_data.targets[0]  # Trust visitor provided valid single target
            if not (isinstance(target, ast.Attribute) and 
                    isinstance(target.value, ast.Name) and 
                    target.value.id == "self"):
                raise ValueError("InstanceAttributeNode requires ast.Assign with self.attr target")
        
        # Initialize collections before parent init (which calls _create_children)
        self._type: Optional[TypeNode] = None
        self._violations: list = []
        
        # Parent class handles name extraction and validation
        super().__init__(parent, source_data)
    
    def _extract_name(self) -> str:
        """Extract attribute name from AST node."""
        if isinstance(self.source_data, ast.AnnAssign):
            return self.source_data.target.attr
        else:  # ast.Assign
            return self.source_data.targets[0].attr
    
    def _create_children(self):
        """
        Create TypeNode child from annotation or violation for missing type hint.
        
        Every InstanceAttributeNode creates exactly one child, enforcing complete type
        analysis coverage:
        
        - TypeNode: when instance attribute has type annotation
        - MissingInstanceAttributeTypeHintViolation: when type hint is missing
        
        This ensures Atlas identifies ALL instance attributes requiring type documentation.
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
    
    def _create_missing_type_hint_violation(self):
        """
        Create MissingInstanceAttributeTypeHintViolation ornament.
        
        Private method - only called internally when no type hint exists.
        Best practice requires explicit type annotations for all instance attributes.
        
        Violation ornaments hang off the tree but aren't considered part
        of the structural tree hierarchy (reserved for BaseNode subclasses).
        """
        # Import here to avoid circular imports
        from ..violations import MissingInstanceAttributeTypeHintViolation
        
        violation = MissingInstanceAttributeTypeHintViolation(
            parent=self, 
            attribute_name=self.name,
            class_name=self.parent.name
        )
        self._violations.append(violation)
        return violation