"""
Return Node - Atlas Rewrite

Node representing a function's return position with type analysis.
Every function has exactly one return position, even if implicitly returning None.
"""

import ast
from typing import Optional, Dict
from ..core import TreeNode, BaseNode
from .type_node import TypeNode
from ..notes import MissingReturnTypeHint


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
            # No return type annotation - create MissingReturnTypeHint note
            # Even functions with implicit None returns should document with -> None
            self._create_missing_return_type_note()
    
    def analyze(self, parent_scope: Optional[Dict[str, str]] = None):
        """
        Analyze this return node.
        
        Return nodes represent function return type.
        Type information already captured during reconnaissance.
        """
        # No analysis needed yet (leaf node)
        # Cascade to children (TypeNode if present)
        for child in self._get_direct_children():
            child.analyze(parent_scope=parent_scope or {})

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
    
    def _create_missing_return_type_note(self):
        """
        Create MissingReturnTypeHint note.
        
        Private method - only called internally when no type hint exists.
        This includes functions that implicitly return None without documenting
        it, as best practice requires explicit `-> None` annotation even for
        side-effect-only functions.
        
        Notes are lightweight ornamental objects that attach to nodes but aren't
        part of the structural tree hierarchy (reserved for BaseNode subclasses).
        """
        note = MissingReturnTypeHint(self)
        self.add_note(note)