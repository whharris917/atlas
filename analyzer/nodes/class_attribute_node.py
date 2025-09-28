"""
Class Attribute Node - Atlas Rewrite

Node representing a class-level attribute with type analysis.
Handles both annotated (class_var: Type = value) and unannotated (class_var = value) attributes.
"""

import ast
from typing import Union
from .base_attribute_node import BaseAttributeNode
from ..core import BaseNode
from ..violations import MissingClassAttributeTypeHint


class ClassAttributeNode(BaseAttributeNode):
    """
    Node representing a class-level attribute.
    
    Class attributes are defined directly in the class body and are shared
    across all instances. They can be either annotated or unannotated.
    
    Examples:
    - class_var: str = "default"     # Annotated class attribute
    - MAX_ITEMS = 100                # Unannotated class attribute
    """
    
    def __init__(self, parent: BaseNode, source_data: Union[ast.AnnAssign, ast.Assign]):
        # Validate that assignment has simple class attribute target pattern
        if isinstance(source_data, ast.AnnAssign):
            if not isinstance(source_data.target, ast.Name):
                raise ValueError("ClassAttributeNode requires ast.AnnAssign with ast.Name target")
        elif isinstance(source_data, ast.Assign):
            if len(source_data.targets) != 1 or not isinstance(source_data.targets[0], ast.Name):
                raise ValueError("ClassAttributeNode requires ast.Assign with single ast.Name target")
        
        # Parent class handles common validation and initialization
        super().__init__(parent, source_data)
    
    def _extract_name(self) -> str:
        """Extract attribute name from assignment AST node."""
        if isinstance(self.source_data, ast.AnnAssign):
            # Annotated assignment: class_var: Type = value
            return self.source_data.target.id
        else:  # ast.Assign
            # Regular assignment: class_var = value
            # ClassReconnaissanceVisitor ensures single target
            return self.source_data.targets[0].id
    
    def _create_missing_type_hint_violation(self) -> MissingClassAttributeTypeHint:
        """
        Create MissingClassAttributeTypeHint violation ornament.
        
        Private method - only called internally when no type hint exists.
        Best practice requires explicit type annotations for all class attributes.
        """
        violation = MissingClassAttributeTypeHint(self)
        self._violations.append(violation)
        return violation