"""
Argument Node - Atlas Rewrite

Node representing a function argument with type analysis as final Reconnaissance Phase step.
Creates either TypeNode child (if type annotation exists) or MissingTypeHint violation.
Pure self-extracting architecture - no name or type parameters.
"""

import ast
from typing import Optional, List, Union, TYPE_CHECKING
from ..core import TreeNode, BaseNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from .type_node import TypeNode
    from ..violations import MissingTypeHint


class ArgumentNode(TreeNode):
    """Node representing a function argument with type analysis."""
    
    def __init__(self, arg_ast: ast.arg, parent: BaseNode):
        if not arg_ast:
            raise ValueError("ArgumentNode requires valid ast.arg node")
        if not isinstance(arg_ast, ast.arg):
            raise ValueError("ArgumentNode requires ast.arg node")
        
        # Initialize collections before parent init (which calls _create_children)
        self._type: Optional['TypeNode'] = None
        self._violations: List['MissingTypeHint'] = []
        
        # Pure self-extraction from AST
        super().__init__(arg_ast.arg, parent, arg_ast)
    
    def _create_children(self):
        """
        Final step of Reconnaissance Phase: analyze type information.
        Creates either TypeNode child or MissingTypeHint violation.
        """
        if self.ast_node.annotation:
            # Type annotation exists - create TypeNode
            self._create_type_node(self.ast_node.annotation)
        else:
            # No type annotation - create MissingTypeHint violation
            self._create_missing_type_violation()
    
    def _create_type_node(self, type_ast: ast.AST) -> 'TypeNode':
        """Create TypeNode child from type annotation AST."""
        from .type_node import TypeNode
        self._type = TypeNode(type_ast, parent=self)
        return self._type
    
    def _create_missing_type_violation(self) -> 'MissingTypeHint':
        """Create MissingTypeHint violation ornament."""
        from ..violations import MissingTypeHint
        violation = MissingTypeHint(parent=self, argument_name=self.name)
        self._violations.append(violation)
        return violation
    
    @property
    def has_type_annotation(self) -> bool:
        """Check if this argument has a type annotation."""
        return self._type is not None
    
    @property
    def type_node(self) -> Optional['TypeNode']:
        """Get the TypeNode child if type annotation exists."""
        return self._type
    
    @property
    def violations(self) -> List['MissingTypeHint']:
        """Get list of violations (ornaments hanging off this argument)."""
        return self._violations.copy()
    
    def list_all(self) -> dict:
        """Get comprehensive argument information including type analysis."""
        result = {
            'name': self.name,
            'line_number': self.line_number,
            'has_type_annotation': self.has_type_annotation
        }
        
        if self._type:
            result['type'] = {
                'representation': self._type.type_representation,
                'ast_type': self._type.ast_node.__class__.__name__
            }
        
        if self._violations:
            result['violations'] = [
                {
                    'type': violation.violation_type,
                    'message': violation.message,
                    'suggested_fix': violation.suggested_fix
                }
                for violation in self._violations
            ]
        
        return result