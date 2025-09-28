"""
Argument Node - Atlas Rewrite

Node representing a function argument with type analysis as final Reconnaissance Phase step.
Extremely focused implementation adhering to strict separation of concerns.
"""

import ast
from typing import Optional, List
from ..core import TreeNode, BaseNode
from .type_node import TypeNode
from ..violations import MissingArgumentTypeHint


class ArgumentNode(TreeNode):
    """Node representing a function argument with type analysis."""
    
    def __init__(self, parent: BaseNode, source_data: ast.arg):
        if not isinstance(source_data, ast.arg):
            raise TypeError("ArgumentNode requires ast.arg as source_data")
        
        # Initialize collections before parent init (which calls _create_children)
        self._type: Optional[TypeNode] = None
        self._violations: List[MissingArgumentTypeHint] = []
        
        # Parent class handles name extraction and validation
        super().__init__(parent, source_data)
    
    def _extract_name(self) -> str:
        """Extract argument name from ast.arg node."""
        return self.source_data.arg
    
    def _create_children(self):
        """
        Final step of Reconnaissance Phase: analyze type information.
        Creates either TypeNode child or MissingArgumentTypeHint violation.
        """
        if self.source_data.annotation:
            # Type annotation exists - create TypeNode
            self._create_type_node(self.source_data.annotation)
        else:
            # No type annotation - create MissingArgumentTypeHint violation
            self._create_missing_type_violation()
    
    def _create_type_node(self, type_ast: ast.AST) -> TypeNode:
        """Create TypeNode child from type annotation AST."""
        self._type = TypeNode(parent=self, source_data=type_ast)
        return self._type
    
    def _create_missing_type_violation(self) -> MissingArgumentTypeHint:
        """Create MissingArgumentTypeHint violation ornament."""
        violation = MissingArgumentTypeHint(parent=self, argument_name=self.name)
        self._violations.append(violation)
        return violation