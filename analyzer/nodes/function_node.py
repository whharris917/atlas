"""
Function Node - Atlas Rewrite

Node representing a Python function or method with automatic child creation.
Extremely focused implementation adhering to strict separation of concerns.
"""

import ast
from typing import List, TYPE_CHECKING
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