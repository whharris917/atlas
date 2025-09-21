"""
Module Node - Atlas Rewrite

Node representing a Python module with automatic child creation.
Creates all ClassNodes, FunctionNodes, StateNodes, ImportNodes immediately.
"""

import ast
from typing import Dict, List, Optional, TYPE_CHECKING
from ..core import TreeNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from . import ClassNode, FunctionNode, StateNode, ImportNode


class ModuleNode(TreeNode):
    """Node representing a Python module."""
    
    def __init__(self, name: str, ast_node: ast.Module):
        super().__init__(name, ast_node)
        self._classes: Dict[str, 'ClassNode'] = {}
        self._functions: Dict[str, 'FunctionNode'] = {}
        self._state: Dict[str, 'StateNode'] = {}
        self._imports: Dict[str, 'ImportNode'] = {}
        
        # Create all children immediately
        self._create_children()
    
    def _create_children(self):
        """Create child nodes using ModuleReconnaissanceVisitor."""
        if not self.ast_node:
            return
        
        print(f"  Creating children in: {self.fqn}")
        
        # Use specialized visitor for module-level discovery
        from ..reconnaissance.visitors import ModuleReconnaissanceVisitor
        visitor = ModuleReconnaissanceVisitor(self)
        visitor.visit(self.ast_node)
    
    def create_class(self, class_ast: ast.ClassDef) -> 'ClassNode':
        """Create and hook a new class from AST node."""
        if class_ast.name not in self._classes:
            from . import ClassNode
            class_node = ClassNode(class_ast)
            class_node.parent = self
            self._classes[class_ast.name] = class_node
            return class_node
        return self._classes[class_ast.name]
    
    def create_function(self, func_ast: ast.FunctionDef) -> 'FunctionNode':
        """Create and hook a new function from AST node."""
        from . import FunctionNode
        function_node = FunctionNode(func_ast)
        function_node.parent = self
        self._functions[func_ast.name] = function_node
        return function_node
    
    def create_state(self, state_ast: ast.AST) -> 'StateNode':
        """Create and hook state variable(s) from AST node."""
        if isinstance(state_ast, ast.Assign):
            for target in state_ast.targets:
                if isinstance(target, ast.Name):
                    return self._create_state_node(target.id, state_ast)
        elif isinstance(state_ast, ast.AnnAssign) and isinstance(state_ast.target, ast.Name):
            return self._create_state_node(state_ast.target.id, state_ast)
    
    def _create_state_node(self, name: str, ast_node: ast.AST) -> 'StateNode':
        """Helper to create individual StateNode."""
        from . import StateNode
        state_node = StateNode(name, ast_node)
        state_node.parent = self
        self._state[name] = state_node
        return state_node
    
    def create_import(self, import_ast: ast.AST) -> 'ImportNode':
        """Create and hook import(s) from AST node."""
        from . import ImportNode
        
        if isinstance(import_ast, ast.Import):
            for alias in import_ast.names:
                import_name = alias.asname if alias.asname else alias.name
                import_node = ImportNode(import_name, alias.name, import_ast)
                import_node.parent = self
                self._imports[import_name] = import_node
                return import_node  # Return first one created
        
        elif isinstance(import_ast, ast.ImportFrom) and import_ast.module:
            for alias in import_ast.names:
                import_name = alias.asname if alias.asname else alias.name
                full_module = f"{import_ast.module}.{alias.name}"
                import_node = ImportNode(import_name, full_module, import_ast)
                import_node.parent = self
                self._imports[import_name] = import_node
                return import_node  # Return first one created
    
    def get_class(self, name: str) -> 'ClassNode':
        """Get a class by name."""
        if name not in self._classes:
            raise KeyError(f"Class '{name}' not found in module '{self.name}'")
        return self._classes[name]
    
    def get_function(self, name: str) -> 'FunctionNode':
        """Get a function by name."""
        if name not in self._functions:
            raise KeyError(f"Function '{name}' not found in module '{self.name}'")
        return self._functions[name]
    
    def list_classes(self) -> List['ClassNode']:
        """List all classes in this module."""
        return list(self._classes.values())
    
    def list_functions(self) -> List['FunctionNode']:
        """List all functions in this module."""
        return list(self._functions.values())
    
    def list_state(self) -> List['StateNode']:
        """List all state variables in this module."""
        return list(self._state.values())
    
    def list_imports(self) -> List['ImportNode']:
        """List all imports in this module."""
        return list(self._imports.values())
    
    def list_all(self) -> Dict[str, List]:
        """List everything contained in this module."""
        return {
            'classes': self.list_classes(),
            'functions': self.list_functions(),
            'state': self.list_state(),
            'imports': self.list_imports()
        }