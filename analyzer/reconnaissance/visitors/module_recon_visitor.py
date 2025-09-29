"""
Module Reconnaissance Visitor - Atlas Rewrite - FIXED

Fixed to use BaseNode's unified navigation API instead of calling methods directly on containers.
All API access goes through BaseNode's universal interface.
"""

import ast
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...nodes import ModuleNode


class ModuleReconnaissanceVisitor(ast.NodeVisitor):
    """
    Discovers module-level entities: classes, functions, state, imports within module scope.
    Updated to use BaseNode unified navigation API for all access.
    """
    
    def __init__(self, module_node: 'ModuleNode'):
        self.module_node = module_node
        self.in_class = False
        self.in_function = False
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Create class node."""
        self.module_node.create_class(node)
        # Don't visit class internals - handled by ClassReconnaissanceVisitor
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Create function node if at module level."""
        if not self.in_function and not self.in_class:
            self.module_node.create_function(node)
        # Don't visit function internals - handled by FunctionReconnaissanceVisitor
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Create async function node if at module level."""
        if not self.in_function and not self.in_class:
            self.module_node.create_function(node)
        # Don't visit function internals
    
    def visit_Assign(self, node: ast.Assign):
        """Create state container for module-level assignments.""" 
        if not self.in_function and not self.in_class:
            self.module_node.create_state_container(node)
        # Don't visit assignment internals
    
    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Create state container for module-level annotated assignments."""
        if not self.in_function and not self.in_class:
            self.module_node.create_state_container(node)
        # Don't visit assignment internals
    
    def visit_Import(self, node: ast.Import):
        """Create import node."""
        self.module_node.create_import(node)
        # Don't visit import internals
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Create from-import node."""
        self.module_node.create_import(node)
        # Don't visit import internals
    
    def generic_visit(self, node: ast.AST):
        """Continue visiting only control flow nodes that might contain module-level entities."""
        if isinstance(node, (
            ast.If, ast.While, ast.For, ast.With, ast.Try, 
            ast.ExceptHandler, ast.Module
        )):
            super().generic_visit(node)
        # Stop at entity boundaries - their internals handled by specialized visitors