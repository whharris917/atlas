"""
Return Node - Atlas Rewrite

Node representing a function return type with type analysis as final Reconnaissance Phase step.
Extremely focused implementation adhering to strict separation of concerns.
"""

import ast
from typing import Optional, List, TYPE_CHECKING
from ..core import TreeNode, BaseNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from .type_node import TypeNode
    from ..violations import MissingReturnTypeHint


class ReturnNode(TreeNode):
    """Node representing a function return type with type analysis."""
    
    def __init__(self, parent: BaseNode, source_data: ast.FunctionDef):
        if not isinstance(source_data, ast.FunctionDef):
            raise TypeError("ReturnNode requires ast.FunctionDef as source_data")
        
        # Initialize collections before parent init (which calls _create_children)
        self._type: Optional['TypeNode'] = None
        self._violations: List['MissingReturnTypeHint'] = []
        
        # Parent class handles name extraction and validation
        super().__init__(parent, source_data)
    
    def _extract_name(self) -> str:
        """ReturnNode always has name 'return' for consistency."""
        return "return"
    
    def _create_children(self):
        """
        Final step of Reconnaissance Phase: analyze return type information.
        Creates either TypeNode child or MissingReturnTypeHint violation.
        """
        if self.source_data.returns:
            # Return type annotation exists - create TypeNode
            self._create_type_node(self.source_data.returns)
        else:
            # No return type annotation - create MissingReturnTypeHint violation
            self._create_missing_return_type_violation()
    
    def _create_type_node(self, type_ast: ast.AST) -> 'TypeNode':
        """Create TypeNode child from return type annotation AST."""
        from .type_node import TypeNode
        self._type = TypeNode(parent=self, source_data=type_ast)
        return self._type
    
    def _create_missing_return_type_violation(self) -> 'MissingReturnTypeHint':
        """Create MissingReturnTypeHint violation ornament."""
        from ..violations import MissingReturnTypeHint
        violation = MissingReturnTypeHint(parent=self, function_name=self.parent.name)
        self._violations.append(violation)
        return violation