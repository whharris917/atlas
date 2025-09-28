"""
Function Reconnaissance Visitor - Atlas Rewrite

Specialized AST visitor for function-level entity discovery.
Currently unused as arguments and returns are accessed directly from function signature.
Kept as skeleton for potential future functionality (e.g., nested functions).
"""

import ast
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...nodes import FunctionNode
    
    
class FunctionReconnaissanceVisitor(ast.NodeVisitor):
    """
    Skeleton visitor for function-level entity discovery.
    
    Currently not used - FunctionNode creates arguments and returns directly
    from function signature via direct attribute access (node.args.args, node.returns).
    
    Reserved for potential future functionality such as:
    - Discovering nested function definitions
    - Analyzing function body for additional metadata
    - Other complex function-internal reconnaissance
    """
    
    def __init__(self, function_node: 'FunctionNode'):
        self.function_node = function_node