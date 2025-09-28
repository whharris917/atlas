"""
Missing Instance Attribute Type Hint Violation - Atlas Rewrite

Code standard violation for instance attributes lacking type annotations.
Ornament that hangs off InstanceAttributeNode to flag missing type documentation.
"""

from .base import CodeStandardViolation


class MissingInstanceAttributeTypeHintViolation(CodeStandardViolation):
    """
    Code standard violation for instance attributes missing type hints.
    
    This violation flags instance attributes defined in __init__ methods
    that lack explicit type annotations, which are required for clear code
    documentation and static analysis.
    
    Examples that trigger this violation:
    - self.name = name      # Missing type hint
    - self.items = []       # Missing type hint
    - self.count = 0        # Missing type hint
    
    Recommended fix:
    - self.name: str = name
    - self.items: List[str] = []
    - self.count: int = 0
    """
    
    def __init__(self, parent, attribute_name: str, class_name: str):
        """
        Initialize violation ornament.
        
        Args:
            parent: The InstanceAttributeNode missing the type hint
            attribute_name: Name of the attribute missing type annotation
            class_name: Name of the class containing the attribute
        """
        message = (
            f"Instance attribute '{attribute_name}' in class '{class_name}' "
            f"lacks type annotation. Add explicit type hint for better code documentation."
        )
        
        suggestion = f"Add type annotation: self.{attribute_name}: <type> = <value>"
        
        super().__init__(
            parent=parent,
            violation_type="missing_instance_attribute_type_hint",
            message=message,
            suggestion=suggestion
        )
        
        self.attribute_name = attribute_name
        self.class_name = class_name