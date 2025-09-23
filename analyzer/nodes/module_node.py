"""
Module Node - Atlas Rewrite

Node representing a Python module with automatic child creation.
Creates all ClassNodes, FunctionNodes, StateNodes, ImportNodes immediately.
"""

import ast
from typing import Dict, List, Optional, TYPE_CHECKING, Union
from ..core import TreeNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from . import ClassNode, FunctionNode, StateNode, ImportNode, ImportFromNode


class ModuleNode(TreeNode):
    """Node representing a Python module."""
    
    def __init__(self, name: str, parent: TreeNode, ast_node: ast.Module):
        if not ast_node:
            raise ValueError(f"ModuleNode '{name}' requires valid AST node")
        
        super().__init__(name, parent, ast_node)
        self._classes: Dict[str, 'ClassNode'] = {}
        self._functions: Dict[str, 'FunctionNode'] = {}
        self._state: Dict[str, 'StateNode'] = {}
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
        if class_ast.name not in self._classes:
            from . import ClassNode
            class_node = ClassNode(class_ast, parent=self)
            self._classes[class_ast.name] = class_node
            return class_node
        return self._classes[class_ast.name]
    
    def create_function(self, func_ast: ast.FunctionDef) -> 'FunctionNode':
        """Create and hook a new function from AST node."""
        from . import FunctionNode
        function_node = FunctionNode(func_ast, parent=self)
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
        state_node = StateNode(name, parent=self, ast_node=ast_node)
        self._state[name] = state_node
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
        if name not in self._classes:
            raise KeyError(f"Class '{name}' not found in module '{self.name}'")
        return self._classes[name]
    
    def get_function(self, name: str) -> 'FunctionNode':
        """Get a function by name."""
        if name not in self._functions:
            raise KeyError(f"Function '{name}' not found in module '{self.name}'")
        return self._functions[name]
    
    def get_state(self, name: str) -> 'StateNode':
        """Get a state variable by name."""
        if name not in self._state:
            raise KeyError(f"State variable '{name}' not found in module '{self.name}'")
        return self._state[name]
    
    def list_classes(self) -> List['ClassNode']:
        """List all classes in this module."""
        return list(self._classes.values())
    
    def list_functions(self) -> List['FunctionNode']:
        """List all functions in this module."""
        return list(self._functions.values())
    
    def list_state(self) -> List['StateNode']:
        """List all state variables in this module."""
        return list(self._state.values())
    
    def list_imports(self) -> List[Union['ImportNode', 'ImportFromNode']]:
        """List all import containers in this module."""
        return self._imports
    
    def list_all(self) -> Dict[str, List]:
        """List all entities in this module organized by type."""
        return {
            'classes': self.list_classes(),
            'functions': self.list_functions(),
            'state': self.list_state(),
            'imports': self.list_imports()
        }