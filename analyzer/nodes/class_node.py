"""
Class Node - Atlas Rewrite

Node representing a Python class with automatic child creation.
Extremely focused implementation adhering to strict separation of concerns.
"""

import ast
from typing import List, TYPE_CHECKING
from ..core import TreeNode, BaseNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from . import FunctionNode, AttributeNode


class ClassNode(TreeNode):
    """Node representing a Python class."""
    
    def __init__(self, ast_node: ast.ClassDef, parent: BaseNode):
        if not ast_node:
            raise ValueError("ClassNode requires valid AST node")
        
        # Initialize collections before parent init (which calls _create_children)
        self._methods: List['FunctionNode'] = []
        self._attributes: List['AttributeNode'] = []
        
        # Self-extract name from AST
        super().__init__(ast_node.name, parent, ast_node)
    
    def _create_children(self):
        """Create child nodes using ClassReconnaissanceVisitor."""
        
        print(f"    Creating children in: {self.fqn}")
        
        # Use specialized visitor for class-level discovery
        from ..reconnaissance.visitors import ClassReconnaissanceVisitor
        visitor = ClassReconnaissanceVisitor(self)
        visitor.visit(self.ast_node)
    
    def create_method(self, method_ast: ast.FunctionDef) -> 'FunctionNode':
        """Create and hook a new method from AST node."""
        from . import FunctionNode
        method_node = FunctionNode(method_ast, parent=self)
        self._methods.append(method_node)
        return method_node
    
    def create_attribute(self, attr_ast: ast.AnnAssign) -> 'AttributeNode':
        """Create and hook a new attribute from AST node."""
        from . import AttributeNode
        attr_node = AttributeNode(attr_ast, parent=self)
        self._attributes.append(attr_node)
        return attr_node