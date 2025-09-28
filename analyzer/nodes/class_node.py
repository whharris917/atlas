"""
Class Node - Atlas Rewrite

Node representing a Python class with automatic child creation.
Extremely focused implementation adhering to strict separation of concerns.
"""

import ast
from typing import List
from ..core import TreeNode, BaseNode
from ..reconnaissance.visitors import ClassReconnaissanceVisitor
from .function_node import FunctionNode
from .attribute_node import AttributeNode


class ClassNode(TreeNode):
    """Node representing a Python class."""
    
    def __init__(self, parent: BaseNode, source_data: ast.ClassDef):
        if not isinstance(source_data, ast.ClassDef):
            raise TypeError("ClassNode requires ast.ClassDef as source_data")
        
        # Initialize collections before parent init (which calls _create_children)
        self._methods: List[FunctionNode] = []
        self._attributes: List[AttributeNode] = []
        
        # Parent class handles name extraction and validation
        super().__init__(parent, source_data)
    
    def _extract_name(self) -> str:
        """Extract class name from ast.ClassDef node."""
        return self.source_data.name
    
    def _create_children(self):
        """Create child nodes using ClassReconnaissanceVisitor."""
        print(f"    Creating children in: {self.fqn}")
        
        # Use specialized visitor for class-level discovery
        visitor = ClassReconnaissanceVisitor(self)
        visitor.visit(self.source_data)
    
    def create_method(self, method_ast: ast.FunctionDef) -> FunctionNode:
        """Create and hook a new method from AST node."""
        method_node = FunctionNode(parent=self, source_data=method_ast)
        self._methods.append(method_node)
        return method_node
    
    def create_attribute(self, attr_ast: ast.AnnAssign) -> AttributeNode:
        """Create and hook a new attribute from AST node."""
        attr_node = AttributeNode(parent=self, source_data=attr_ast)
        self._attributes.append(attr_node)
        return attr_node