"""
Module Node - Atlas Rewrite

Node representing a Python module with automatic child creation.
Pure StateContainerNode architecture - no legacy state handling.
Pure self-extracting architecture with list storage.

File: analyzer/nodes/module_node.py
"""

import ast
from typing import List, Optional, TYPE_CHECKING, Union
from ..core import TreeNode, BaseNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from . import ClassNode, FunctionNode, StateNode, StateContainerNode
    from . import ImportNode, ImportFromNode
    from ..reconnaissance.discovery import DiscoveredModule


class ModuleNode(TreeNode):
    """Node representing a Python module."""
    
    def __init__(self, module_data: 'DiscoveredModule', parent: BaseNode):
        if not module_data or not module_data.ast_node:
            raise ValueError("ModuleNode requires valid DiscoveredModule with AST")
        
        # Initialize collections before parent init (which calls _create_children)
        self._classes: List['ClassNode'] = []
        self._functions: List['FunctionNode'] = []
        self._state_containers: List['StateContainerNode'] = []  # Pure architecture
        self._imports: List[Union['ImportNode', 'ImportFromNode']] = []
        
        # Self-extract name from module data
        super().__init__(module_data.name, parent, module_data.ast_node)
    
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
    
    def create_state_container(self, assignment_ast: ast.AST) -> 'StateContainerNode':
        """Create and hook state container from assignment AST node."""
        from .state_container_node import StateContainerNode
        container = StateContainerNode(parent=self, ast_node=assignment_ast)
        self._state_containers.append(container)
        return container
    
    def create_import(self, import_ast: Union[ast.Import, ast.ImportFrom]) -> Union['ImportNode', 'ImportFromNode']:
        """Create and hook import container from AST node."""
        if isinstance(import_ast, ast.Import):
            from .import_node import ImportNode
            import_node = ImportNode(parent=self, ast_node=import_ast)
            self._imports.append(import_node)
            return import_node
        else:  # ast.ImportFrom
            from .import_from_node import ImportFromNode
            import_from_node = ImportFromNode(parent=self, ast_node=import_ast)
            self._imports.append(import_from_node)
            return import_from_node