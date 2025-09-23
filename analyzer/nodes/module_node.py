"""
Module Node - Atlas Rewrite

Node representing a Python module with automatic child creation.
Creates all ClassNodes, FunctionNodes, StateNodes, ImportNodes immediately.
Pure self-extracting architecture with list storage.
"""

import ast
from typing import List, Optional, TYPE_CHECKING, Union
from ..core import TreeNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from . import ClassNode, FunctionNode, StateNode, ImportNode, ImportFromNode
    from ..reconnaissance.discovery import DiscoveredModule


class ModuleNode(TreeNode):
    """Node representing a Python module."""
    
    def __init__(self, module_data: 'DiscoveredModule', parent: TreeNode):
        if not module_data or not module_data.ast_node:
            raise ValueError("ModuleNode requires valid DiscoveredModule with AST")
        
        # Self-extract name from module data
        super().__init__(module_data.name, parent, module_data.ast_node)
        self._classes: List['ClassNode'] = []
        self._functions: List['FunctionNode'] = []
        self._state: List['StateNode'] = []
        self._imports: List[Union['ImportNode', 'ImportFromNode']] = []
        
        # Create all children immediately
        self._create_children()
    
    def _create_children(self):
        """Create child nodes using ModuleReconnaissanceVisitor."""
        
        print(f"  Creating children in: {self.fqn}")
        
        # Use specialized visitor for module-level discovery
        from ..reconnaissance.visitors import ModuleReconnaissanceVisitor
        visitor = ModuleReconnaissanceVisitor(self)
        visitor.visit(self.ast_node)
    
    def create_class(self, class_ast: ast.ClassDef) -> 'ClassNode':
        """Create and hook a new class from AST node."""
        from . import ClassNode
        class_node = ClassNode(class_ast, parent=self)
        self._classes.append(class_node)
        return class_node
    
    def create_function(self, func_ast: ast.FunctionDef) -> 'FunctionNode':
        """Create and hook a new function from AST node."""
        from . import FunctionNode
        function_node = FunctionNode(func_ast, parent=self)
        self._functions.append(function_node)
        return function_node
    
    def create_state(self, state_ast: ast.AST) -> 'StateNode':
        """Create and hook state variable from AST node."""
        from . import StateNode
        state_node = StateNode(state_ast, parent=self)
        self._state.append(state_node)
        return state_node
    
    def create_import(self, import_ast: Union[ast.Import, ast.ImportFrom]) -> Union['ImportNode', 'ImportFromNode']:
        """Create and hook import container from AST node."""
        if isinstance(import_ast, ast.Import):
            from . import ImportNode
            import_node = ImportNode(parent=self, ast_node=import_ast)
            self._imports.append(import_node)
            return import_node
        elif isinstance(import_ast, ast.ImportFrom):
            from . import ImportFromNode
            import_from_node = ImportFromNode(parent=self, ast_node=import_ast)
            self._imports.append(import_from_node)
            return import_from_node
    
    def get_class(self, name: str) -> 'ClassNode':
        """Get a class by name."""
        for class_node in self._classes:
            if class_node.name == name:
                return class_node
        raise KeyError(f"Class '{name}' not found in module '{self.name}'")
    
    def get_function(self, name: str) -> 'FunctionNode':
        """Get a function by name."""
        for function in self._functions:
            if function.name == name:
                return function
        raise KeyError(f"Function '{name}' not found in module '{self.name}'")
    
    def get_state(self, name: str) -> 'StateNode':
        """Get a state variable by name."""
        for state in self._state:
            if state.name == name:
                return state
        raise KeyError(f"State variable '{name}' not found in module '{self.name}'")
    
    def list_classes(self) -> List['ClassNode']:
        """List all classes in this module."""
        return self._classes
    
    def list_functions(self) -> List['FunctionNode']:
        """List all functions in this module."""
        return self._functions
    
    def list_state(self) -> List['StateNode']:
        """List all state variables in this module."""
        return self._state
    
    def list_imports(self) -> List[Union['ImportNode', 'ImportFromNode']]:
        """List all import containers in this module."""
        return self._imports
    
    def list_all(self) -> dict:
        """List all entities in this module organized by type."""
        return {
            'classes': self.list_classes(),
            'functions': self.list_functions(),
            'state': self.list_state(),
            'imports': self.list_imports()
        }