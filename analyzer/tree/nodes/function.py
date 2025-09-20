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
    
    def __init__(self, name: str, line_number: int = 0, ast_node: Optional[ast.FunctionDef] = None, is_method: bool = False):
        super().__init__(name, ast_node)
        self.line_number = line_number
        self.is_method = is_method
        self._arguments: Dict[str, ArgumentNode] = {}
        self._children_discovered = False
    
    def discover_children(self):
        """Discover and create argument nodes from function AST."""
        if self._children_discovered or not self.ast_node:
            return
        
        print(f"      Discovering arguments in: {self.fqn}")
        
        # Extract arguments from function
        for arg in self.ast_node.args.args:
            arg_type = ""
            if arg.annotation:
                try:
                    arg_type = ast.unparse(arg.annotation)
                except:
                    arg_type = "Unknown"
            
            from .argument import ArgumentNode
            arg_node = ArgumentNode(arg.arg, arg_type, arg)
            arg_node.parent = self
            self._arguments[arg.arg] = arg_node
            print(f"        Found argument: {arg_node.fqn} : {arg_type}")
        
        self._children_discovered = True
    
    def create_argument(self, name: str, arg_type: str = "", ast_node: Optional[ast.arg] = None) -> ArgumentNode:
        """Create and hook a new argument."""
        from .argument import ArgumentNode
        arg_node = ArgumentNode(name, arg_type, ast_node)
        arg_node.parent = self
        self._arguments[name] = arg_node
        return arg_node
    
    def list_arguments(self) -> List[ArgumentNode]:
        """List all arguments for this function."""
        self.discover_children()  # Ensure children are discovered
        return list(self._arguments.values())