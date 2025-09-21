"""
Class Reconnaissance Visitor - Atlas Rewrite

Specialized AST visitor for class-level entity discovery.
Discovers: methods, nested classes, class variables within class scope.
"""

import ast
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...nodes import ClassNode


class ClassReconnaissanceVisitor(ast.NodeVisitor):
    """
    Discovers class-level entities: methods, nested classes, class variables.
    Focused on class body discovery.
    """
    
    def __init__(self, class_node: 'ClassNode'):
        self.class_node = class_node
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Create method node."""
        self.class_node.create_method(node)
        print(f"      Found method: {self.class_node.fqn}.{node.name}")
        # Don't visit method internals - handled by FunctionReconnaissanceVisitor
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Create async method node."""
        self.class_node.create_method(node)
        print(f"      Found async method: {self.class_node.fqn}.{node.name}")
        # Don't visit method internals - handled by FunctionReconnaissanceVisitor
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Create nested class node if needed."""
        # For now, skip nested classes as requested
        # Could be enabled later: self.class_node.create_nested_class(node)
        pass
    
    def visit_Assign(self, node: ast.Assign):
        """Create class variable if appropriate."""
        # Future enhancement: detect class variables vs instance variables
        # For now, defer to avoid complexity
        pass
    
    def generic_visit(self, node: ast.AST):
        """Visit class body directly - no control flow filtering needed at class level."""
        # Class bodies are simpler - just visit direct children
        super().generic_visit(node)