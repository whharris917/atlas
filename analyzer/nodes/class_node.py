"""
Class Node - Atlas Rewrite

Node representing a Python class with ClassReconnaissanceVisitor-based discovery.
"""

import ast
from typing import Dict, List, Optional, TYPE_CHECKING
from ..core import TreeNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from . import FunctionNode, AttributeNode


class ClassNode(TreeNode):
    """Node representing a Python class."""
    
    def __init__(self, ast_node: ast.ClassDef):
        super().__init__(ast_node.name, ast_node)
        self._methods: Dict[str, 'FunctionNode'] = {}
        self._attributes: Dict[str, 'AttributeNode'] = {}
        self._children_created = False
    
    def create_children(self):
        """Create child nodes using ClassReconnaissanceVisitor."""
        if self._children_created or not self.ast_node:
            return
        
        print(f"    Creating methods in: {self.fqn}")
        
        # Use specialized visitor for class-level discovery
        from ..reconnaissance.visitors import ClassReconnaissanceVisitor
        visitor = ClassReconnaissanceVisitor(self)
        visitor.visit(self.ast_node)
        
        self._children_created = True
    
    def create_method(self, func_ast: ast.FunctionDef) -> 'FunctionNode':
        """Create and hook a new method from AST node."""
        from . import FunctionNode
        method_node = FunctionNode(func_ast, is_method=True)
        method_node.parent = self
        self._methods[func_ast.name] = method_node
        return method_node
    
    def create_attribute(self, name: str, attribute_type: str, ast_node: ast.AST) -> 'AttributeNode':
        """Create and hook a new attribute."""
        from . import AttributeNode
        attr_node = AttributeNode(name, attribute_type, ast_node)
        attr_node.parent = self
        self._attributes[name] = attr_node
        return attr_node
    
    def get_method(self, name: str) -> 'FunctionNode':
        """Get a method by name."""
        self.create_children()  # Ensure children are created
        if name not in self._methods:
            raise KeyError(f"Method '{name}' not found in class '{self.name}'")
        return self._methods[name]
    
    def list_methods(self) -> List['FunctionNode']:
        """List all methods in this class."""
        self.create_children()  # Ensure children are created
        return list(self._methods.values())
    
    def list_attributes(self) -> List['AttributeNode']:
        """List all attributes in this class."""
        self.create_children()  # Ensure children are created
        return list(self._attributes.values())