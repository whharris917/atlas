"""
Module Reconnaissance Visitor - Atlas Rewrite

Specialized AST visitor for module-level entity discovery.
Discovers: classes, functions, state variables, imports at module scope.
"""

import ast
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...nodes import ModuleNode


class ModuleReconnaissanceVisitor(ast.NodeVisitor):
    """
    Discovers module-level entities: classes, functions, state variables, imports.
    Only creates top-level entities - internal details handled by other visitors.
    """
    
    def __init__(self, module_node: 'ModuleNode'):
        self.module_node = module_node
        self.in_function = False
        self.in_class = False
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Create class node only if at module level."""
        if not self.in_function and not self.in_class:
            self.module_node.create_class(node)
            print(f"    Found class: {self.module_node.fqn}.{node.name}")
        # Don't visit class internals - handled by ClassReconnaissanceVisitor
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Create function node only if at module level."""
        if not self.in_function and not self.in_class:
            self.module_node.create_function(node)
            print(f"    Found function: {self.module_node.fqn}.{node.name}")
        # Don't visit function internals - handled by FunctionReconnaissanceVisitor
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Handle async functions same as regular functions."""
        if not self.in_function and not self.in_class:
            self.module_node.create_function(node)
            print(f"    Found async function: {self.module_node.fqn}.{node.name}")
        # Don't visit function internals - handled by FunctionReconnaissanceVisitor
    
    def visit_Assign(self, node: ast.Assign):
        """Create state variable if at module level."""
        if not self.in_function and not self.in_class:
            self.module_node.create_state(node)
            if node.targets and isinstance(node.targets[0], ast.Name):
                print(f"    Found state: {self.module_node.fqn}.{node.targets[0].id}")
        # Don't visit assignment internals
    
    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Create annotated state variable if at module level."""
        if not self.in_function and not self.in_class:
            self.module_node.create_state(node)
            if isinstance(node.target, ast.Name):
                print(f"    Found annotated state: {self.module_node.fqn}.{node.target.id}")
        # Don't visit assignment internals
    
    def visit_Import(self, node: ast.Import):
        """Create import node."""
        self.module_node.create_import(node)
        if node.names:
            first_import = node.names[0]
            import_name = first_import.asname if first_import.asname else first_import.name
            print(f"    Found import: {self.module_node.fqn}.{import_name} -> {first_import.name}")
        # Don't visit import internals
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Create from-import node."""
        self.module_node.create_import(node)
        if node.names and node.module:
            first_import = node.names[0]
            import_name = first_import.asname if first_import.asname else first_import.name
            full_module = f"{node.module}.{first_import.name}"
            print(f"    Found from-import: {self.module_node.fqn}.{import_name} -> {full_module}")
        # Don't visit import internals
    
    def generic_visit(self, node: ast.AST):
        """Continue visiting only control flow nodes that might contain module-level entities."""
        if isinstance(node, (
            ast.If, ast.While, ast.For, ast.With, ast.Try, 
            ast.ExceptHandler, ast.Module
        )):
            super().generic_visit(node)
        # Stop at entity boundaries - their internals handled by specialized visitors