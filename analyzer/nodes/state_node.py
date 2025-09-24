"""
State Node - Atlas Rewrite

Node representing a module-level state variable with pure self-extracting architecture.
Extremely focused implementation adhering to strict separation of concerns.
"""

import ast
from typing import Optional, TYPE_CHECKING
from ..core import TreeNode, BaseNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    pass


class StateNode(TreeNode):
    """Node representing a module-level state variable."""
    
    def __init__(self, name: str, parent: BaseNode, ast_node: Optional[ast.AST] = None):
        if not name:
            raise ValueError("StateNode requires non-empty name")
        
        # Pure construction - no extraneous logic
        super().__init__(name, parent, ast_node)