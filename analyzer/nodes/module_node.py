"""
Module Node - Atlas Rewrite

Node representing a Python module with automatic child creation.
Pure StateContainerNode architecture - no legacy state handling.
Pure self-extracting architecture with list storage.
"""

import ast
from typing import List, Union, Optional, Dict
from ..core import TreeNode, BaseNode
from ..reconnaissance.discovery import DiscoveredModule
from ..reconnaissance.visitors import ModuleReconnaissanceVisitor
from .class_node import ClassNode
from .function_node import FunctionNode
from .state_container_node import StateContainerNode
from .import_node import ImportNode
from .import_from_node import ImportFromNode


class ModuleNode(TreeNode):
    """Node representing a Python module."""
    
    def __init__(self, parent: BaseNode, source_data: DiscoveredModule):
        if not isinstance(source_data, DiscoveredModule):
            raise TypeError("ModuleNode requires DiscoveredModule as source_data")
        if not source_data.ast_node:
            raise ValueError("ModuleNode requires DiscoveredModule with valid ast_node")
        
        # Initialize collections before parent init (which calls _create_children)
        self._classes: List[ClassNode] = []
        self._functions: List[FunctionNode] = []
        self._state_containers: List[StateContainerNode] = []  # Pure architecture
        self._imports: List[Union[ImportNode, ImportFromNode]] = []
        
        # Parent class handles name extraction and validation
        super().__init__(parent, source_data)
    
    def _extract_name(self) -> str:
        """Extract module name from DiscoveredModule."""
        return self.source_data.name
    
    def _create_children(self):
        """Create child nodes using ModuleReconnaissanceVisitor."""
        # Use specialized visitor for module-level discovery
        visitor = ModuleReconnaissanceVisitor(self)
        # Visit the ast_node from the DiscoveredModule
        visitor.visit(self.source_data.ast_node)
    
    def analyze(self, parent_scope: Optional[Dict[str, str]] = None):
            """
            Analyze this module and cascade to all children.
            
            Creates ModuleAnalysisVisitor to analyze module-level code,
            infer variable types, and build scope for child nodes.
            """
            from ..analysis.visitors import ModuleAnalysisVisitor
            
            # Create visitor for this module
            visitor = ModuleAnalysisVisitor(self)
            
            # Visit the module's AST to build scope
            visitor.visit(self.source_data.ast_node)
            
            # Cascade to all children with visitor's scope
            for child in self._get_direct_children():
                child.analyze(parent_scope=visitor.scope)

    def create_class(self, class_ast: ast.ClassDef) -> ClassNode:
        """Create and hook a new class from AST node."""
        class_node = ClassNode(parent=self, source_data=class_ast)
        self._classes.append(class_node)
        return class_node
    
    def create_function(self, func_ast: ast.FunctionDef) -> FunctionNode:
        """Create and hook a new function from AST node."""
        function_node = FunctionNode(parent=self, source_data=func_ast)
        self._functions.append(function_node)
        return function_node
    
    def create_state_container(self, assignment_ast: ast.AST) -> StateContainerNode:
        """Create and hook state container from assignment AST node."""
        container = StateContainerNode(parent=self, source_data=assignment_ast)
        self._state_containers.append(container)
        return container
    
    def create_import(self, import_ast: Union[ast.Import, ast.ImportFrom]) -> Union[ImportNode, ImportFromNode]:
        """Create and hook import container from AST node."""
        if isinstance(import_ast, ast.Import):
            import_node = ImportNode(parent=self, source_data=import_ast)
            self._imports.append(import_node)
            return import_node
        else:  # ast.ImportFrom
            import_from_node = ImportFromNode(parent=self, source_data=import_ast)
            self._imports.append(import_from_node)
            return import_from_node