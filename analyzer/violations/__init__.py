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


class UnsupportedExpressionType(CodeStandardViolation):
    """
    Violation indicating an expression type that cannot be linearized for type inference.
    
    The linearization engine converts nested expressions into a Linear Operation Queue (LOQ)
    for type propagation. When it encounters an AST node type that isn't yet implemented,
    it creates this violation to alert that type inference will be incomplete.
    
    Examples of currently unsupported expressions:
        - Binary operations: user.age + 10, x * y
        - Boolean operations: user.is_active and user.is_verified
        - Comparison operations: user.age > 18
        - Unary operations: -balance, not is_active
        - Conditional expressions: "admin" if is_admin else "user"
        - Comprehensions: [x.name for x in users]
        - Lambda expressions: lambda x: x.name
        - Await expressions: await fetch_data()
    
    The violation stores the AST node type name to help prioritize future implementation.
    """
    
    def __init__(self, parent: 'BaseNode', expression_type: str, line_number: int):
        """
        Create an unsupported expression type violation.
        
        Args:
            parent: The node where type inference was attempted
            expression_type: The AST node class name (e.g., "BinOp", "Compare")
            line_number: Line number where the unsupported expression appears
        """
        super().__init__(parent)
        self.expression_type = expression_type
        self.line_number = line_number
    
    def __repr__(self) -> str:
        """Enhanced representation including expression type and line number."""
        return (f"UnsupportedExpressionType(parent={self.parent.__class__.__name__}, "
                f"type={self.expression_type}, line={self.line_number})")


# Public API exports
__all__ = [
    'CodeStandardViolation',
    'MissingArgumentTypeHint',
    'MissingReturnTypeHint',
    'MissingClassAttributeTypeHint', 
    'MissingInstanceAttributeTypeHint',
    'MultipleTargetAttributeAssignment',
    'IncorrectTypeAnnotation',
    'UnsupportedExpressionType'
]