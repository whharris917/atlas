"""Module Analysis Visitor - Type inference for module-level code."""

import ast
from .base_analysis_visitor import BaseAnalysisVisitor
from .class_analysis_visitor import ClassAnalysisVisitor
from .function_analysis_visitor import FunctionAnalysisVisitor


class ModuleAnalysisVisitor(BaseAnalysisVisitor):
    """
    Analyzes module-level code and infers types for assignments.
    
    This visitor walks the module's AST to build a complete scope containing:
    - Variables from assignments (inherited from BaseAnalysisVisitor)
    - Imported names (modules and specific imports)
    - Class definitions
    - Function definitions
    
    Inherits all functionality from BaseAnalysisVisitor:
    - visit_Assign() - handles un-annotated assignments
    - visit_AnnAssign() - handles annotated assignments with validation
    - visit_Import() - handles import statements
    - visit_ImportFrom() - handles from-import statements
    - visit_ClassDef() - adds class definitions to scope (overridden for dispatch)
    - visit_FunctionDef() - adds function definitions to scope (overridden for dispatch)
    - visit_AsyncFunctionDef() - adds async function definitions to scope
    
    Also inherits shared functionality:
    - linearize() for expression processing
    - _infer_type() for type determination (with Dot and CallFunction support)
    - _infer_literal_type() for literal handling
    - _extract_type_from_annotation() for type hint extraction
    - _resolve_annotation() for annotation-to-FQN resolution
    - _process_assignment() for unified assignment handling
    
    Extends BaseAnalysisVisitor by dispatching child visitors for nested scopes:
    - ClassAnalysisVisitor for analyzing class bodies
    - FunctionAnalysisVisitor for analyzing function bodies
    
    Traverses in AST order to ensure names are only available after definition,
    providing inherent code checking for use-before-definition.
    
    All analysis notes are attached to the ModuleNode (locality principle).
    """
    
    def __init__(self, module_node):
        """
        Initialize visitor for a specific module node.
        
        Args:
            module_node: The ModuleNode being analyzed (where notes attach)
        """
        super().__init__(module_node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """
        Visit class definitions and dispatch ClassAnalysisVisitor.
        
        Overrides base implementation to:
        1. Add class to module scope (via super())
        2. Dispatch ClassAnalysisVisitor to analyze class body
        """
        # FIRST: Call super() to add class to module scope
        super().visit_ClassDef(node)
        
        # SECOND: Dispatch ClassAnalysisVisitor to analyze class body
        class_node = self.node.get_class(node.name)
        if class_node:
            print(f"   Dispatching ClassAnalysisVisitor for: {node.name}")
            visitor = ClassAnalysisVisitor(class_node, self.scope)
            try:
                visitor.visit(class_node.source_data)
            finally:
                # Pop the child visitor's frame after it finishes
                self.scope.pop_frame()
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """
        Visit function definitions and dispatch FunctionAnalysisVisitor.
        
        Overrides base implementation to:
        1. Add function to module scope (via super())
        2. Dispatch FunctionAnalysisVisitor to analyze function body
        """
        # FIRST: Call super() to add function to module scope
        super().visit_FunctionDef(node)
        
        # SECOND: Dispatch FunctionAnalysisVisitor to analyze function body
        func_node = self.node.get_function(node.name)
        if func_node:
            print(f"   Dispatching FunctionAnalysisVisitor for: {node.name}")
            visitor = FunctionAnalysisVisitor(func_node, self.scope)
            try:
                visitor.visit(func_node.source_data)
            finally:
                # Pop the child visitor's frame after it finishes
                self.scope.pop_frame()
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """
        Visit async function definitions and dispatch FunctionAnalysisVisitor.
        
        Overrides base implementation to:
        1. Add async function to module scope (via super())
        2. Dispatch FunctionAnalysisVisitor to analyze function body
        """
        # FIRST: Call super() to add async function to module scope
        super().visit_AsyncFunctionDef(node)
        
        # SECOND: Dispatch FunctionAnalysisVisitor to analyze async function body
        func_node = self.node.get_function(node.name)
        if func_node:
            print(f"   Dispatching FunctionAnalysisVisitor for: {node.name} (async)")
            visitor = FunctionAnalysisVisitor(func_node, self.scope)
            try:
                visitor.visit(func_node.source_data)
            finally:
                # Pop the child visitor's frame after it finishes
                self.scope.pop_frame()