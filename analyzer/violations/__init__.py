"""
Atlas Code Standard Violations - Minimalist Ornament System

Violations are simple ornaments that hang off nodes as labels.
They require only a parent - everything else can be derived.

This single module replaces all the separate violation modules with
extremely simple subclasses that contain no redundant data.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core import BaseNode


class CodeStandardViolation:
    """
    Base class for code standard violations.
    
    Violations are just ornaments - labels that hang off nodes.
    They contain only a parent reference, nothing else.
    """
    
    def __init__(self, parent: 'BaseNode'):
        """
        Create a violation ornament.
        
        Args:
            parent: The node this violation is attached to
        """
        if not parent:
            raise ValueError("CodeStandardViolation requires parent node")
        
        self.parent = parent
    
    def __repr__(self) -> str:
        """Simple string representation for debugging."""
        return f"{self.__class__.__name__}({self.parent.__class__.__name__})"


class MissingArgumentTypeHint(CodeStandardViolation):
    """Violation indicating a missing type hint on a function argument."""
    pass


class MissingReturnTypeHint(CodeStandardViolation):
    """Violation indicating a missing return type hint on a function."""
    pass


class MissingClassAttributeTypeHint(CodeStandardViolation):
    """Violation indicating a missing type hint on a class attribute."""
    pass


class MissingInstanceAttributeTypeHint(CodeStandardViolation):
    """Violation indicating a missing type hint on an instance attribute."""
    pass


class MultipleTargetAttributeAssignment(CodeStandardViolation):
    """Violation indicating an assignment with multiple targets (e.g., x = y = value)."""
    pass


class IncorrectTypeAnnotation(CodeStandardViolation):
    """
    Violation indicating a type annotation that doesn't match the inferred type.
    
    Example:
        user: User = "not a user"  # Annotation says User, value is str
        count: int = 3.14           # Annotation says int, value is float
    
    The annotation (type hint) doesn't match what the value actually is.
    This helps catch bugs where type hints are incorrect or misleading.
    """
    pass


# Public API exports
__all__ = [
    'CodeStandardViolation',
    'MissingArgumentTypeHint',
    'MissingReturnTypeHint',
    'MissingClassAttributeTypeHint', 
    'MissingInstanceAttributeTypeHint',
    'MultipleTargetAttributeAssignment',
    'IncorrectTypeAnnotation'
]