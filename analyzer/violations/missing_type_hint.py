"""
Missing Type Hint Violation - Atlas Rewrite

Violation indicating a missing type hint on a function argument.
Created when ArgumentNode discovers an argument without type annotation.
"""

from typing import TYPE_CHECKING
from .base import CodeStandardViolation

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from ..core import BaseNode


class MissingTypeHint(CodeStandardViolation):
    """
    Violation indicating a missing type hint on a function argument.
    Created when ArgumentNode discovers an argument without type annotation.
    """
    
    def __init__(self, parent: 'BaseNode', argument_name: str):
        message = f"Missing type hint for argument '{argument_name}'"
        super().__init__(parent, message)
        self.argument_name = argument_name
    
    @property
    def suggested_fix(self) -> str:
        """Suggest how to fix this violation."""
        return f"Add type annotation: {self.argument_name}: TypeName"