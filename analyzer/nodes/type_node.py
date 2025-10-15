"""
Type Node - Atlas Rewrite

Node representing a type annotation with comprehensive type analysis.
Extremely focused implementation adhering to strict separation of concerns.

ENHANCED: Now stores the actual type hint string during Reconnaissance Phase,
eliminating the need for repeated ast.unparse() calls during Analysis Phase.
"""

import ast
from typing import Optional, Dict
from ..core import TreeNode, BaseNode


class TypeNode(TreeNode):
    """
    Node representing a type annotation.
    
    Attributes:
        type_string: The actual type hint string (e.g., "int", "List[User]", "Optional[str]")
                    extracted during reconnaissance for convenient Analysis Phase access.
    """
    
    def __init__(self, parent: BaseNode, source_data: ast.AST):
        if not isinstance(source_data, ast.AST):
            raise TypeError("TypeNode requires ast.AST as source_data")
        
        # Parent class handles name extraction and validation
        super().__init__(parent, source_data)
        
        # ENHANCEMENT: Store the actual type hint string during Reconnaissance Phase
        # This eliminates the need for repeated ast.unparse() calls during Analysis Phase
        self.type_string: str = ast.unparse(source_data)
    
    def _extract_name(self) -> str:
        """
        Return canonical name for type position.
        
        Returns "type" as the canonical name for all TypeNodes, enabling
        predictable navigation patterns like:
        - arg_node.dot("type") 
        - return_node.dot("type")
        - attribute_node.dot("type")
        
        This mirrors ReturnNode's canonical "return" name for consistency.
        
        Note: The actual type information is now stored in self.type_string
        for convenient access without needing ast.unparse(self.source_data).
        """
        return "type"
    
    def _create_children(self):
        """TypeNode is a leaf node - no children to create."""
        pass

    def analyze(self, parent_scope: Optional[Dict[str, str]] = None):
        """
        Analyze this type node.
        
        Type nodes are leaf nodes representing type information.
        No analysis needed - already captured during reconnaissance.
        """
        # No analysis needed (leaf node, no children)
        pass