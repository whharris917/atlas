"""
Function Node - Atlas Rewrite

Node representing a Python function or method with automatic child creation.
ENHANCED: Creates ReturnNode for complete type analysis coverage.
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
    
    def __init__(self, ast_node: ast.FunctionDef, parent: BaseNode):
        if not ast_node:
            raise ValueError("FunctionNode requires valid AST node")
        
        # Initialize collections before parent init (which calls _create_children)
        self._arguments: List['ArgumentNode'] = []
        self._return: Optional['ReturnNode'] = None
        
        # Self-extract name from AST
        super().__init__(ast_node.name, parent, ast_node)
    
    def _create_children(self):
        """Create child nodes using FunctionReconnaissanceVisitor plus ReturnNode."""
        
        print(f"      Creating arguments and return type in: {self.fqn}")
        
        # Use specialized visitor for function-level discovery
        from ..reconnaissance.visitors import FunctionReconnaissanceVisitor
        visitor = FunctionReconnaissanceVisitor(self)
        visitor.visit(self.ast_node)
        
        # NEW: Always create ReturnNode for type analysis
        self._create_return_node()
    
    def create_argument(self, arg_ast: ast.arg) -> 'ArgumentNode':
        """Create and hook a new argument from AST node."""
        from . import ArgumentNode
        arg_node = ArgumentNode(arg_ast, parent=self)
        self._arguments.append(arg_node)
        return arg_node
    
    def _create_return_node(self) -> 'ReturnNode':
        """Create ReturnNode for return type analysis."""
        from . import ReturnNode
        self._return = ReturnNode(self.ast_node, parent=self)
        return self._return