"""
Function Reconnaissance Visitor - Atlas Rewrite

Specialized AST visitor for function-level entity discovery.
Discovers: arguments, function signature analysis.
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
    
    def visit_arguments(self, node: ast.arguments):
        """Create argument nodes from function signature."""
        for arg in node.args:
            self.function_node.create_argument(arg)
            arg_type = ""
            if arg.annotation:
                try:
                    arg_type = ast.unparse(arg.annotation)
                except:
                    arg_type = "Unknown"
            print(f"        Found argument: {self.function_node.fqn}.{arg.arg} : {arg_type}")
        # Don't visit argument internals
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Handle nested functions if needed."""
        # For now, skip nested functions
        # Could be enabled later for complex analysis
        pass
    
    def generic_visit(self, node: ast.AST):
        """Visit function signature only - skip body for now."""
        # For reconnaissance, we only care about the signature
        # Body analysis deferred to Analysis Phase
        if isinstance(node, ast.arguments):
            super().generic_visit(node)
        # Skip function body during reconnaissance