"""
Instance Attribute Node - Atlas Rewrite

Node representing an instance attribute with type analysis.
Handles both annotated (self.attr: Type = value) and unannotated (self.attr = value) attributes.
"""

import ast
from typing import Union
from .base_attribute_node import BaseAttributeNode
from ..core import BaseNode
from ..notes import MissingInstanceAttributeTypeHint


class InstanceAttributeNode(BaseAttributeNode):
    """
    Node representing an instance attribute.
    
    Instance attributes are defined in __init__ methods and are unique
    to each instance. They can be either annotated or unannotated.
    
    Examples:
    - self.name: str = name          # Annotated instance attribute
    - self.items = []                # Unannotated instance attribute
    """
    
    def __init__(self, parent: BaseNode, source_data: Union[ast.AnnAssign, ast.Assign]):
        # Validate that assignment has self.attr target pattern
        if isinstance(source_data, ast.AnnAssign):
            if not (isinstance(source_data.target, ast.Attribute) and
                    isinstance(source_data.target.value, ast.Name) and
                    source_data.target.value.id == "self"):
                raise ValueError("InstanceAttributeNode requires ast.AnnAssign with self.attr target")
        elif isinstance(source_data, ast.Assign):
            if (len(source_data.targets) != 1 or
                not isinstance(source_data.targets[0], ast.Attribute) or
                not isinstance(source_data.targets[0].value, ast.Name) or
                source_data.targets[0].value.id != "self"):
                raise ValueError("InstanceAttributeNode requires ast.Assign with single self.attr target")
        
        # Parent class handles common validation and initialization
        super().__init__(parent, source_data)
    
    def _extract_name(self) -> str:
        """Extract attribute name from assignment AST node."""
        if isinstance(self.source_data, ast.AnnAssign):
            # Annotated assignment: self.attr: Type = value
            return self.source_data.target.attr
        else:  # ast.Assign
            # Regular assignment: self.attr = value
            # ClassReconnaissanceVisitor ensures single target
            return self.source_data.targets[0].attr
    
    def _create_missing_type_hint_note(self):
        """
        Create MissingInstanceAttributeTypeHint note.
        
        Private method - only called internally when no type hint exists.
        Best practice requires explicit type annotations for all instance attributes.
        """
        note = MissingInstanceAttributeTypeHint(self)
        self.add_note(note)