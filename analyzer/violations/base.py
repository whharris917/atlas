"""
Base Code Standard Violation - Atlas Rewrite

Base class for all code standard violations.
These are diagnostic ornaments that decorate the tree but don't form part of its structure.
Like Christmas tree ornaments - they hang off the tree but aren't branches.
"""

from typing import Optional, TYPE_CHECKING

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from ..core import BaseNode


class CodeStandardViolation:
    """
    Base class for code standard violations.
    These are diagnostic ornaments that decorate the tree but don't form part of its structure.
    Like Christmas tree ornaments - they hang off the tree but aren't branches.
    """
    
    def __init__(self, parent: 'BaseNode', message: str, line_number: Optional[int] = None):
        if not parent:
            raise ValueError("CodeStandardViolation requires parent node")
        if not message:
            raise ValueError("CodeStandardViolation requires non-empty message")
        
        self.parent = parent
        self.message = message
        self.line_number = line_number or getattr(parent, 'line_number', 0)
    
    @property
    def violation_type(self) -> str:
        """Get the type of violation for reporting."""
        return self.__class__.__name__
    
    @property
    def location(self) -> str:
        """Get human-readable location of the violation."""
        if hasattr(self.parent, 'fqn'):
            return f"{self.parent.fqn}:{self.line_number}"
        else:
            return f"line {self.line_number}"
    
    def __repr__(self) -> str:
        """String representation for debugging and reporting."""
        return f"{self.violation_type}({self.location}): {self.message}"