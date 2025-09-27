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
    
    def __init__(self, parent: BaseNode, source_data: ast.ClassDef):
        if not isinstance(source_data, ast.ClassDef):
            raise TypeError("ClassNode requires ast.ClassDef as source_data")
        
        # Initialize collections before parent init (which calls _create_children)
        self._methods: List['FunctionNode'] = []
        self._attributes: List['AttributeNode'] = []
        
        # Parent class handles name extraction and validation
        super().__init__(parent, source_data)
    
    def _extract_name(self) -> str:
        """Extract class name from ast.ClassDef node."""
        return self.source_data.name
    
    def _create_children(self):
        """Create child nodes using ClassReconnaissanceVisitor."""
        
        print(f"    Creating children in: {self.fqn}")
        
        # Use specialized visitor for class-level discovery
        from ..reconnaissance.visitors import ClassReconnaissanceVisitor
        visitor = ClassReconnaissanceVisitor(self)
        visitor.visit(self.source_data)
    
    def create_method(self, method_ast: ast.FunctionDef) -> 'FunctionNode':
        """Create and hook a new method from AST node."""
        from . import FunctionNode
        method_node = FunctionNode(parent=self, source_data=method_ast)
        self._methods.append(method_node)
        return method_node
    
    def create_attribute(self, attr_ast: ast.AnnAssign) -> 'AttributeNode':
        """Create and hook a new attribute from AST node."""
        from . import AttributeNode
        attr_node = AttributeNode(parent=self, source_data=attr_ast)
        self._attributes.append(attr_node)
        return attr_node