"""
Class Node - Atlas Rewrite

Node representing a Python class with method discovery.
"""

import ast
from typing import Dict, List, Optional, TYPE_CHECKING
from ..base import TreeNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from .function import FunctionNode
    from .attribute import AttributeNode


class ClassNode(TreeNode):
    """Node representing a Python class."""
    
    def __init__(self, name: str, line_number: int = 0, ast_node: Optional[ast.ClassDef] = None):
        super().__init__(name, ast_node)
        self.line_number = line_number
        self._methods: Dict[str, 'FunctionNode'] = {}
        self._attributes: Dict[str, 'AttributeNode'] = {}
        self._children_discovered = False
    
    def discover_children(self):
        """Discover and create method nodes from class AST without full population."""
        if self._children_discovered or not self.ast_node:
            return
        
        print(f"    Discovering methods in: {self.fqn}")
        
        # Extract methods from class body
        for node in self.ast_node.body:
            if isinstance(node, ast.FunctionDef):
                from .function import FunctionNode
                method_node = FunctionNode(node.name, getattr(node, 'lineno', 0), node, is_method=True)
                method_node.parent = self
                self._methods[node.name] = method_node
                print(f"      Found method: {method_node.fqn}")
        
        self._children_discovered = True
    
    def create_method(self, name: str, line_number: int = 0, ast_node: Optional[ast.FunctionDef] = None) -> 'FunctionNode':
        """Create and hook a new method."""
        from .function import FunctionNode
        method_node = FunctionNode(name, line_number, ast_node, is_method=True)
        method_node.parent = self
        self._methods[name] = method_node
        return method_node
    
    def create_attribute(self, name: str, attribute_type: str = "", ast_node: Optional[ast.AST] = None) -> 'AttributeNode':
        """Create and hook a new attribute."""
        from .attribute import AttributeNode
        attr_node = AttributeNode(name, attribute_type, ast_node)
        attr_node.parent = self
        self._attributes[name] = attr_node
        return attr_node
    
    def get_method(self, name: str) -> 'FunctionNode':
        """Get a method by name."""
        self.discover_children()  # Ensure children are discovered
        if name not in self._methods:
            raise KeyError(f"Method '{name}' not found in class '{self.name}'")
        return self._methods[name]
    
    def list_methods(self) -> List['FunctionNode']:
        """List all methods in this class."""
        self.discover_children()  # Ensure children are discovered
        return list(self._methods.values())
    
    def list_attributes(self) -> List['AttributeNode']:
        """List all attributes in this class."""
        self.discover_children()  # Ensure children are discovered
        return list(self._attributes.values())