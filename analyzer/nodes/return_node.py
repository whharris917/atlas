"""
Return Node - Atlas Rewrite

Node representing a function's return position with type analysis.
Every function has exactly one return position, even if implicitly returning None.
"""

import ast
from typing import Optional, List
from ..core import TreeNode, BaseNode
from .type_node import TypeNode
from ..violations import MissingReturnTypeHint


class ReturnNode(TreeNode):
    """
    Node representing a function's return position.
    
    ReturnNode is a semantic abstraction representing the concept of a function's
    return position, even though Python's AST doesn't provide a dedicated node
    for this concept. Every function has exactly one return position.
    """
    
    def __init__(self, parent: BaseNode, source_data: ast.FunctionDef):
        if not isinstance(source_data, (ast.FunctionDef, ast.AsyncFunctionDef)):
            raise TypeError("ReturnNode requires ast.FunctionDef or ast.AsyncFunctionDef as source_data")
        
        # Initialize collections before parent init (which calls _create_children)
        self._type: Optional[TypeNode] = None
        self._violations: List[MissingReturnTypeHint] = []
        
        # Parent class handles name extraction and validation
        super().__init__(parent, source_data)
    
    def _extract_name(self) -> str:
        """
        Extract semantic name for return position.
        
        Returns "return" as the canonical name for function return positions.
        This provides symmetric FQN patterns:
        - module.function.arg_name (for arguments)
        - module.function.return (for return position)
        """
        return "return"
    
    def _create_children(self):
        """
        Final step of Reconnaissance Phase: analyze return type information.
        
        Every ReturnNode creates exactly one child, enforcing complete type
        analysis coverage:
        
        - TypeNode: when function has return type annotation (including -> None)
        - MissingReturnTypeHint: when type hint is missing entirely
        
        This ensures Atlas identifies ALL locations requiring type documentation,
        including functions that implicitly return None without documenting it.
        """
        if self.source_data.returns:
            # Return type annotation exists - create TypeNode child
            # This includes explicit `-> None` annotations for side-effect functions
            self._create_type_node(self.source_data.returns)
        else:
            # No return type annotation - create MissingReturnTypeHint violation
            # Even functions with implicit None returns should document with -> None
            self._create_missing_return_type_violation()
    
    def _create_type_node(self, type_ast: ast.AST) -> TypeNode:
        """
        Create TypeNode child from return type annotation AST.
        
        Private method - only called internally during type analysis.
        
        Args:
            type_ast: The AST node representing the return type annotation
                     (from func_def.returns). Can represent any valid type
                     including None, Optional[T], Union types, etc.
        
        Returns:
            The created TypeNode
        """
        self._type = TypeNode(parent=self, source_data=type_ast)
        return self._type
    
    def _create_missing_return_type_violation(self) -> MissingReturnTypeHint:
        """
        Create MissingReturnTypeHint violation ornament.
        
        Private method - only called internally when no type hint exists.
        This includes functions that implicitly return None without documenting
        it, as best practice requires explicit `-> None` annotation even for
        side-effect-only functions.
        
        Violation ornaments hang off the tree but aren't considered part
        of the structural tree hierarchy (reserved for BaseNode subclasses).
        
        Returns:
            The created violation ornament
        """
        violation = MissingReturnTypeHint(self)
        self._violations.append(violation)
        return violation