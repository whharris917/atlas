"""
Class Attribute Node - Atlas Rewrite

Node representing a class-level attribute with type analysis.
Handles both annotated and unannotated class attributes defined in class body.
"""

import ast
from typing import Union, Optional, TYPE_CHECKING
from ..core import TreeNode
from .type_node import TypeNode

if TYPE_CHECKING:
    from .class_node import ClassNode


class ClassAttributeNode(TreeNode):
    """Node representing a class-level attribute."""
    
    def __init__(self, parent: 'ClassNode', source_data: Union[ast.AnnAssign, ast.Assign]):
        if not isinstance(source_data, (ast.AnnAssign, ast.Assign)):
            raise TypeError("ClassAttributeNode requires ast.AnnAssign or ast.Assign as source_data")
        
        # Validate that assignment has simple class attribute target pattern
        # (We trust ClassReconnaissanceVisitor to provide valid class attribute assignments)
        if isinstance(source_data, ast.AnnAssign):
            if not isinstance(source_data.target, ast.Name):
                raise ValueError("ClassAttributeNode requires ast.AnnAssign with ast.Name target")
        elif isinstance(source_data, ast.Assign):
            target = source_data.targets[0]  # Trust visitor provided valid single target
            if not isinstance(target, ast.Name):
                raise ValueError("ClassAttributeNode requires ast.Assign with ast.Name target")
        
        # Initialize collections before parent init (which calls _create_children)
        self._type: Optional[TypeNode] = None
        self._violations: list = []
        
        # Parent class handles name extraction and validation
        super().__init__(parent, source_data)
    
    def _extract_name(self) -> str:
        """Extract attribute name from AST node."""
        if isinstance(self.source_data, ast.AnnAssign):
            return self.source_data.target.id
        else:  # ast.Assign
            return self.source_data.targets[0].id
    
    def _create_children(self):
        """
        Create TypeNode child from annotation or violation for missing type hint.
        
        Every ClassAttributeNode creates exactly one child, enforcing complete type
        analysis coverage:
        
        - TypeNode: when class attribute has type annotation
        - MissingClassAttributeTypeHintViolation: when type hint is missing
        
        This ensures Atlas identifies ALL class attributes requiring type documentation.
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
        Create MissingClassAttributeTypeHintViolation ornament.
        
        Private method - only called internally when no type hint exists.
        Best practice requires explicit type annotations for all class attributes.
        
        Violation ornaments hang off the tree but aren't considered part
        of the structural tree hierarchy (reserved for BaseNode subclasses).
        """
        # Import here to avoid circular imports
        from ..violations import MissingClassAttributeTypeHintViolation
        
        violation = MissingClassAttributeTypeHintViolation(
            parent=self, 
            attribute_name=self.name,
            class_name=self.parent.name
        )
        self._violations.append(violation)
        return violation