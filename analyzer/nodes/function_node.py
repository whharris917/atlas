"""
Function Node - Atlas Rewrite

Node representing a Python function or method with automatic child creation.
Creates all ArgumentNodes immediately.
"""

import ast
from typing import Dict, List, Optional, TYPE_CHECKING
from ..core import TreeNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from . import ArgumentNode


class FunctionNode(TreeNode):
    """Node representing a Python function or method."""
    
    def __init__(self, ast_node: ast.FunctionDef, parent: TreeNode, is_method: bool = False):
        if not ast_node:
            raise ValueError("FunctionNode requires valid AST node")
        
        super().__init__(ast_node.name, parent, ast_node)
        self.is_method = is_method
        self._arguments: Dict[str, 'ArgumentNode'] = {}
        
        # Create all children immediately
        self._create_children()
    
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
        self._arguments[arg_ast.arg] = arg_node
        return arg_node
    
    def list_arguments(self) -> List['ArgumentNode']:
        """List all arguments for this function."""
        return list(self._arguments.values())