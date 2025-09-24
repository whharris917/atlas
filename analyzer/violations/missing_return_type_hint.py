"""
Missing Return Type Hint Violation - Atlas Rewrite

Violation indicating a missing return type hint on a function.
Created when ReturnNode discovers a function without return type annotation.
"""

from typing import TYPE_CHECKING
from .base import CodeStandardViolation

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from ..core import BaseNode


class MissingReturnTypeHint(CodeStandardViolation):
    """
    Violation indicating a missing return type hint on a function.
    Created when ReturnNode discovers a function without return type annotation.
    """
    
    def __init__(self, parent: 'BaseNode', function_name: str):
        message = f"Missing return type hint for function '{function_name}'"
        super().__init__(parent, message)
        self.function_name = function_name
    
    @property
    def suggested_fix(self) -> str:
        """Suggest how to fix this violation."""
        return f"Add return type annotation: def {self.function_name}(...) -> ReturnType:"