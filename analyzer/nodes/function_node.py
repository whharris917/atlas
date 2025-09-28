"""
Function Node - Atlas Rewrite

Node representing a function/method with automatic child creation.
Extremely focused implementation adhering to strict separation of concerns.
"""

import ast
from typing import List, Optional
from ..core import TreeNode, BaseNode
from .argument_node import ArgumentNode
from .return_node import ReturnNode


class FunctionNode(TreeNode):
    """Node representing a function or method."""
    
    def __init__(self, parent: BaseNode, source_data: ast.FunctionDef):
        if not isinstance(source_data, (ast.FunctionDef, ast.AsyncFunctionDef)):
            raise TypeError("FunctionNode requires ast.FunctionDef or ast.AsyncFunctionDef as source_data")
        
        # Initialize collections before parent init (which calls _create_children)
        self._arguments: List[ArgumentNode] = []
        self._return: Optional[ReturnNode] = None
        
        # Parent class handles name extraction and validation
        super().__init__(parent, source_data)
    
    def _extract_name(self) -> str:
        """Extract function name from ast.FunctionDef node."""
        return self.source_data.name
    
    def _create_children(self):
        """Create argument and return nodes directly from function signature."""
        print(f"      Creating children in: {self.fqn}")
        
        # Create arguments directly from function signature
        for arg in self.source_data.args.args:
            self._create_argument(arg)
        
        # Create return node for return type analysis
        self._create_return()
    
    def _create_argument(self, arg_ast: ast.arg) -> ArgumentNode:
        """Create and hook a new argument from AST node (internal use only)."""
        arg_node = ArgumentNode(parent=self, source_data=arg_ast)
        self._arguments.append(arg_node)
        print(f"        Found argument: {self.fqn}.{arg_ast.arg}")
        return arg_node
    
    def _create_return(self) -> ReturnNode:
        """Create and hook return node for this function (internal use only)."""
        self._return = ReturnNode(parent=self, source_data=self.source_data)
        return self._return