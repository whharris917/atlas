"""
Module Node - Atlas Rewrite

Node representing a Python module with automatic child creation.
Pure StateContainerNode architecture - no legacy state handling.
Pure self-extracting architecture with list storage.
"""

import ast
from typing import List, Union, TYPE_CHECKING
from ..core import TreeNode, BaseNode

# Import types only for type checking (no runtime cost)
if TYPE_CHECKING:
    from . import ClassNode, FunctionNode, StateNode, StateContainerNode
    from . import ImportNode, ImportFromNode
    from ..reconnaissance.discovery import DiscoveredModule


class ModuleNode(TreeNode):
    """Node representing a Python module."""
    
    def __init__(self, parent: BaseNode, source_data: 'DiscoveredModule'):
        # Import here to avoid circular imports while still getting proper type checking
        from ..reconnaissance.discovery import DiscoveredModule
        if not isinstance(source_data, DiscoveredModule):
            raise TypeError("ModuleNode requires DiscoveredModule as source_data")
        if not source_data.ast_node:
            raise ValueError("ModuleNode requires DiscoveredModule with valid ast_node")
        
        # Initialize collections before parent init (which calls _create_children)
        self._classes: List['ClassNode'] = []
        self._functions: List['FunctionNode'] = []
        self._state_containers: List['StateContainerNode'] = []  # Pure architecture
        self._imports: List[Union['ImportNode', 'ImportFromNode']] = []
        
        # Parent class handles name extraction and validation
        super().__init__(parent, source_data)
    
    def _extract_name(self) -> str:
        """Extract module name from DiscoveredModule."""
        return self.source_data.name
    
    def _create_children(self):
        """Create child nodes using ModuleReconnaissanceVisitor."""
        
        print(f"  Creating children in: {self.fqn}")
        
        # Use specialized visitor for module-level discovery
        from ..reconnaissance.visitors import ModuleReconnaissanceVisitor
        visitor = ModuleReconnaissanceVisitor(self)
        # Visit the ast_node from the DiscoveredModule
        visitor.visit(self.source_data.ast_node)
    
    def create_class(self, class_ast: ast.ClassDef) -> 'ClassNode':
        """Create and hook a new class from AST node."""
        from . import ClassNode
        class_node = ClassNode(parent=self, source_data=class_ast)
        self._classes.append(class_node)
        return class_node
    
    def create_function(self, func_ast: ast.FunctionDef) -> 'FunctionNode':
        """Create and hook a new function from AST node."""
        from . import FunctionNode
        function_node = FunctionNode(parent=self, source_data=func_ast)
        self._functions.append(function_node)
        return function_node
    
    def create_state_container(self, assignment_ast: ast.AST) -> 'StateContainerNode':
        """Create and hook state container from assignment AST node."""
        from .state_container_node import StateContainerNode
        container = StateContainerNode(parent=self, source_data=assignment_ast)
        self._state_containers.append(container)
        return container
    
    def create_import(self, import_ast: Union[ast.Import, ast.ImportFrom]) -> Union['ImportNode', 'ImportFromNode']:
        """Create and hook import container from AST node."""
        if isinstance(import_ast, ast.Import):
            from .import_node import ImportNode
            import_node = ImportNode(parent=self, source_data=import_ast)
            self._imports.append(import_node)
            return import_node
        else:  # ast.ImportFrom
            from .import_from_node import ImportFromNode
            import_from_node = ImportFromNode(parent=self, source_data=import_ast)
            self._imports.append(import_from_node)
            return import_from_node