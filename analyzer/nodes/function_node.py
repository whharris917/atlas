"""
Function Node - Atlas Rewrite

Node representing a Python function or method with automatic child creation.
Creates all ArgumentNodes immediately.
Pure self-extracting architecture - no name or is_method parameters.
"""

import ast
from typing import List, Optional, TYPE_CHECKING
from ..core import TreeNode, BaseNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from . import ArgumentNode


class FunctionNode(TreeNode):
    """Node representing a Python function or method."""
    
    def __init__(self, ast_node: ast.FunctionDef, parent: BaseNode):
        if not ast_node:
            raise ValueError("FunctionNode requires valid AST node")
        
        # Initialize collections before parent init (which calls _create_children)
        self._arguments: List['ArgumentNode'] = []
        
        # Self-extract name from AST
        super().__init__(ast_node.name, parent, ast_node)
    
    @property
    def is_method(self) -> bool:
        """Determine if this is a method by checking parent type."""
        return self.parent.__class__.__name__ == 'ClassNode'
    
    def _create_children(self):
        """Create child nodes using FunctionReconnaissanceVisitor."""
        
        print(f"      Creating arguments in: {self.fqn}")
        
        # Use specialized visitor for function-level discovery
        from ..reconnaissance.visitors import FunctionReconnaissanceVisitor
        visitor = FunctionReconnaissanceVisitor(self)
        visitor.visit(self.ast_node)
    
    def create_argument(self, arg_ast: ast.arg) -> 'ArgumentNode':
        """Create and hook a new argument from AST node."""
        from . import ArgumentNode
        arg_node = ArgumentNode(arg_ast, parent=self)
        self._arguments.append(arg_node)
        return arg_node
    
    def list_arguments(self) -> List['ArgumentNode']:
        """List all arguments for this function."""
        return self._arguments
    
    def get_argument(self, name: str) -> 'ArgumentNode':
        """Get an argument by name."""
        for argument in self._arguments:
            if argument.name == name:
                return argument
        raise KeyError(f"Argument '{name}' not found in function '{self.name}'")
    
    def list_all(self) -> dict:
        """Get comprehensive function structure."""
        return {
            'arguments': [arg.name for arg in self._arguments]
        }