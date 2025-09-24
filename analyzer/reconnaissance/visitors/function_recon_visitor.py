"""
Function Reconnaissance Visitor - Atlas Rewrite

Specialized AST visitor for function-level entity discovery.
Discovers: arguments, function signature analysis.
Pure structural discovery - no type inference.
"""

import ast
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...nodes import FunctionNode
    
    
class FunctionReconnaissanceVisitor(ast.NodeVisitor):
    """
    Discovers function-level entities: arguments, local variables (future), nested functions.
    Focused on function signature and body discovery.
    """
    
    def __init__(self, function_node: 'FunctionNode'):
        self.function_node = function_node
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Process the function definition - visit the arguments."""
        # Visit the arguments of this function
        self.visit(node.args)
        # Don't visit the function body during reconnaissance
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Process async function definition - visit the arguments."""
        # Visit the arguments of this async function
        self.visit(node.args)
        # Don't visit the function body during reconnaissance
    
    def visit_arguments(self, node: ast.arguments):
        """Create argument nodes from function signature."""
        for arg in node.args:
            self.function_node.create_argument(arg)
            print(f"        Found argument: {self.function_node.fqn}.{arg.arg}")
        # Don't visit argument internals
 