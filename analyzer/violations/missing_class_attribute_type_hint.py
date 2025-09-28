"""
Missing Class Attribute Type Hint Violation - Atlas Rewrite

Code standard violation for class attributes lacking type annotations.
Ornament that hangs off ClassAttributeNode to flag missing type documentation.
"""

from .base import CodeStandardViolation


class MissingClassAttributeTypeHintViolation(CodeStandardViolation):
    """
    Code standard violation for class attributes missing type hints.
    
    This violation flags class-level attributes that lack explicit type annotations,
    which are required for clear code documentation and static analysis.
    
    Examples that trigger this violation:
    - class_var = "value"  # Missing type hint
    - MAX_ITEMS = 100      # Missing type hint
    
    Recommended fix:
    - class_var: str = "value"
    - MAX_ITEMS: int = 100
    """
    
    def __init__(self, parent, attribute_name: str, class_name: str):
        """
        Initialize violation ornament.
        
        Args:
            parent: The ClassAttributeNode missing the type hint
            attribute_name: Name of the attribute missing type annotation
            class_name: Name of the class containing the attribute
        """
        message = (
            f"Class attribute '{attribute_name}' in class '{class_name}' "
            f"lacks type annotation. Add explicit type hint for better code documentation."
        )
        
        suggestion = f"Add type annotation: {attribute_name}: <type> = <value>"
        
        super().__init__(
            parent=parent,
            violation_type="missing_class_attribute_type_hint",
            message=message,
            suggestion=suggestion
        )
        
        self.attribute_name = attribute_name
        self.class_name = class_name