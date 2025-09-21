"""
Function Node - Atlas Rewrite

Node representing a Python function or method with argument discovery.
"""

import ast
from typing import Dict, List, Optional, TYPE_CHECKING
from ..base import TreeNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from .argument import ArgumentNode


class FunctionNode(TreeNode):
    """Node representing a Python function or method."""
    
    def __init__(self, ast_node: ast.FunctionDef, is_method: bool = False):
        super().__init__(ast_node.name, ast_node)
        self.is_method = is_method
        self._arguments: Dict[str, 'ArgumentNode'] = {}
        self._children_created = False
    
    def create_children(self):
        """Create argument nodes from function AST."""
        if self._children_created or not self.ast_node:
            return
        
        print(f"      Creating arguments in: {self.fqn}")
        
        # Extract arguments from function
        for arg in self.ast_node.args.args:
            self.create_argument(arg)
        
        self._children_created = True
    
    def create_argument(self, arg_ast: ast.arg) -> 'ArgumentNode':
        """Create and hook a new argument from AST node."""
        arg_type = ""
        if arg_ast.annotation:
            try:
                arg_type = ast.unparse(arg_ast.annotation)
            except:
                arg_type = "Unknown"
        
        from .argument import ArgumentNode
        arg_node = ArgumentNode(arg_ast, arg_type)
        arg_node.parent = self
        self._arguments[arg_ast.arg] = arg_node
        print(f"        Found argument: {arg_node.fqn} : {arg_type}")
        return arg_node
    
    def list_arguments(self) -> List['ArgumentNode']:
        """List all arguments for this function."""
        self.create_children()  # Ensure children are created
        return list(self._arguments.values())