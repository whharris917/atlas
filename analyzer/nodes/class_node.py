"""
Class Node - Atlas Rewrite

Node representing a Python class with automatic child creation.
Creates all FunctionNodes (methods) and AttributeNodes immediately.
"""

import ast
from typing import Dict, List, Optional, TYPE_CHECKING
from ..core import TreeNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from . import FunctionNode, AttributeNode


class ClassNode(TreeNode):
    """Node representing a Python class."""
    
    def __init__(self, ast_node: ast.ClassDef, parent: TreeNode):
        if not ast_node:
            raise ValueError("ClassNode requires valid AST node")
        
        super().__init__(ast_node.name, parent, ast_node)
        self._methods: Dict[str, 'FunctionNode'] = {}
        self._attributes: Dict[str, 'AttributeNode'] = {}
        
        # Create all children immediately
        self._create_children()
    
    def _create_children(self):
        """Create child nodes using ClassReconnaissanceVisitor."""
        
        print(f"    Creating methods in: {self.fqn}")
        
        # Use specialized visitor for class-level discovery
        from ..reconnaissance.visitors import ClassReconnaissanceVisitor
        visitor = ClassReconnaissanceVisitor(self)
        visitor.visit(self.ast_node)
    
    def create_method(self, func_ast: ast.FunctionDef) -> 'FunctionNode':
        """Create and hook a new method from AST node."""
        from . import FunctionNode
        method_node = FunctionNode(func_ast, parent=self, is_method=True)
        self._methods[func_ast.name] = method_node
        return method_node
    
    def create_attribute(self, name: str, ast_node: ast.AST) -> 'AttributeNode':
        """Create and hook a new attribute."""
        from . import AttributeNode
        attr_node = AttributeNode(name, parent=self, ast_node=ast_node)
        self._attributes[name] = attr_node
        return attr_node
    
    def get_method(self, name: str) -> 'FunctionNode':
        """Get a method by name."""
        if name not in self._methods:
            raise KeyError(f"Method '{name}' not found in class '{self.name}'")
        return self._methods[name]
    
    def list_methods(self) -> List['FunctionNode']:
        """List all methods in this class."""
        return list(self._methods.values())
    
    def list_attributes(self) -> List['AttributeNode']:
        """List all attributes in this class."""
        return list(self._attributes.values())