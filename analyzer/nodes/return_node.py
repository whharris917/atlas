"""
Return Node - Atlas Rewrite

Node representing a function's return position with type analysis.

ARCHITECTURAL PRINCIPLE: Every Python function returns something.

Python's fundamental semantics guarantee that ALL functions return a value:
- Functions with explicit `return x` return that value
- Functions with bare `return` return None
- Functions with NO return statement implicitly return None

This universal truth means every function has a "return position" that should
be documented with a type hint. Atlas models this reality by creating a 
ReturnNode for every function, making return positions first-class entities
in the project tree.

SEMANTIC vs AST REPRESENTATION:

While Python's AST stores return type hints as an optional attribute 
(ast.FunctionDef.returns), Atlas treats "the return position" as a mandatory
first-class entity for three reasons:

1. SEMANTIC REALITY: Every function returns something (explicit or implicit None)
2. TYPE ANALYSIS COMPLETENESS: Every return should be documented with type hints
3. API CONSISTENCY: Provides symmetric navigation with ArgumentNode

Every function has exactly one ReturnNode, which creates either:
- TypeNode child (when return type hint exists, including `-> None`)
- MissingReturnTypeHint violation ornament (when type hint is missing)

This design choice prioritizes semantic accuracy and completeness over strict
AST node correspondence, treating Atlas as a semantic model rather than just
an AST wrapper.

EXAMPLES:

    # Explicit return with type hint
    def calculate(x: int) -> float:
        return x * 1.5
    # ReturnNode → TypeNode(type_string="float")
    
    # Explicit None for side effects
    def log_message(msg: str) -> None:
        print(msg)
    # ReturnNode → TypeNode(type_string="None")
    
    # Implicit None return, missing type hint (VIOLATION)
    def define_one():
        x = 1
    # ReturnNode → MissingReturnTypeHint violation
    
    # Meaningful None with Optional
    def find_user(id: int) -> Optional[User]:
        return user if found else None
    # ReturnNode → TypeNode(type_string="Optional[User]")
"""

import ast
from typing import Optional, List, Union
from ..core import TreeNode, BaseNode
from .type_node import TypeNode
from ..violations import MissingReturnTypeHint


class ReturnNode(TreeNode):
    """
    Node representing a function's return position with type analysis.
    
    ReturnNode is a first-class semantic entity representing the universal
    truth that every Python function returns something. Even functions with
    no return statement implicitly return None, making the return position
    a mandatory aspect of every function that should be documented with type
    hints.
    
    This semantic abstraction provides consistency with ArgumentNode and
    enables complete type analysis coverage across all function signatures.
    Every function has exactly one ReturnNode, which always creates either
    a TypeNode child or a MissingReturnTypeHint violation ornament.
    
    Note: ReturnNode's source_data is ast.FunctionDef because Python's AST
    stores return type hints as an optional attribute (.returns) rather than
    as a dedicated node. This is an intentional architectural decision where
    Atlas creates semantic entities beyond raw AST structure to model the
    reality that return positions always exist, even when type hints don't.
    """
    
    def __init__(self, parent: BaseNode, source_data: Union[ast.FunctionDef, ast.AsyncFunctionDef]):
        """
        Initialize ReturnNode for a function's return position.
        
        Args:
            parent: The FunctionNode this return belongs to
            source_data: The function definition containing return type info
            
        Note: source_data is the function definition itself because Python's
        AST doesn't have a dedicated node type for return positions. The
        return type hint (if present) is accessed via source_data.returns.
        """
        if not isinstance(source_data, (ast.FunctionDef, ast.AsyncFunctionDef)):
            raise TypeError(
                "ReturnNode requires ast.FunctionDef or ast.AsyncFunctionDef as source_data. "
                "This represents the function whose return position is being analyzed."
            )
        
        # Initialize collections before parent init (which calls _create_children)
        self._type: Optional[TypeNode] = None
        self._violations: List[MissingReturnTypeHint] = []
        
        # Parent class handles name extraction and validation
        super().__init__(parent, source_data)
    
    def _extract_name(self) -> str:
        """
        ReturnNode always has name 'return' for consistency.
        
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
        violation = MissingReturnTypeHint(parent=self, function_name=self.parent.name)
        self._violations.append(violation)
        return violation