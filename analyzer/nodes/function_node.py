"""
Function Node - Atlas Rewrite

Node representing a Python function/method with automatic child creation.
Extremely focused implementation adhering to strict separation of concerns.
"""

import ast
from typing import List, Optional, TYPE_CHECKING
from ..core import TreeNode, BaseNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from . import ArgumentNode, ReturnNode


class FunctionNode(TreeNode):
    """Node representing a Python function or method."""
    
    def __init__(self, parent: BaseNode, source_data: ast.FunctionDef):
        if not isinstance(source_data, ast.FunctionDef):
            raise TypeError("FunctionNode requires ast.FunctionDef as source_data")
        
        # Initialize collections before parent init (which calls _create_children)
        self._arguments: List['ArgumentNode'] = []
        self._return: Optional['ReturnNode'] = None
        
        # Parent class handles name extraction and validation
        super().__init__(parent, source_data)
    
    def _extract_name(self) -> str:
        """Extract function name from ast.FunctionDef node."""
        return self.source_data.name
    
    def _create_children(self):
        """Create child nodes using FunctionReconnaissanceVisitor."""
        
        print(f"      Creating children in: {self.fqn}")
        
        # Use specialized visitor for function-level discovery
        from ..reconnaissance.visitors import FunctionReconnaissanceVisitor
        visitor = FunctionReconnaissanceVisitor(self)
        visitor.visit(self.source_data)
    
    def create_argument(self, arg_ast: ast.arg) -> 'ArgumentNode':
        """
        Create and hook a new argument from AST node.
        
        Public method because it's called by FunctionReconnaissanceVisitor
        during automatic function discovery.
        """
        from . import ArgumentNode
        arg_node = ArgumentNode(parent=self, source_data=arg_ast)
        self._arguments.append(arg_node)
        return arg_node
    
    def create_return(self) -> 'ReturnNode':
        """
        Create and hook return node for type analysis.
        
        Public method because it's called by FunctionReconnaissanceVisitor
        to automatically create ReturnNode during function discovery.
        """
        from .return_node import ReturnNode
        self._return = ReturnNode(parent=self, source_data=self.source_data)
        return self._return