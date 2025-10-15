"""
Function Node - Atlas Rewrite

Node representing a function/method with automatic child creation.
Extremely focused implementation adhering to strict separation of concerns.
"""

import ast
from typing import List, Optional, Dict
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
        # Create arguments directly from function signature
        for arg in self.source_data.args.args:
            self._create_argument(arg)
        
        # Create return node for return type analysis
        self._create_return()
    
    def analyze(self, parent_scope=None):
        """
        Analyze this function by running FunctionAnalysisVisitor.
        
        Creates a FunctionAnalysisVisitor for this node and runs it to perform
        type inference and scope building for function-level code. The visitor
        pushes a new scope frame in its __init__, which we pop after analysis.
        
        The visitor also populates the scope with function parameters before
        analyzing the function body.
        
        Args:
            parent_scope: Scope from parent visitor (Module/ClassAnalysisVisitor)
        """
        from ..analysis.visitors import FunctionAnalysisVisitor
        
        print(f"      Analyzing function: {self.name}")
        visitor = FunctionAnalysisVisitor(self, parent_scope)
        
        try:
            # Visit the function BODY, not the FunctionDef itself
            # This prevents the visitor from seeing the function definition again
            for item in self.source_data.body:
                visitor.visit(item)
        finally:
            # Pop the frame that FunctionAnalysisVisitor pushed in __init__
            if parent_scope:
                parent_scope.pop_frame()
        
        print(f"      Function analysis complete: {self.name}")

    def _create_argument(self, arg_ast: ast.arg) -> ArgumentNode:
        """Create and hook a new argument from AST node (internal use only)."""
        arg_node = ArgumentNode(parent=self, source_data=arg_ast)
        self._arguments.append(arg_node)
        return arg_node
    
    def _create_return(self) -> ReturnNode:
        """Create and hook return node for this function (internal use only)."""
        self._return = ReturnNode(parent=self, source_data=self.source_data)
        return self._return