"""Class Analysis Visitor - Type inference for class-level code."""

import ast
from .base_analysis_visitor import BaseAnalysisVisitor


class ClassAnalysisVisitor(BaseAnalysisVisitor):
    """
    Analyzes class-level code and infers types for class attributes.
    
    This visitor walks the class's AST to build a complete scope containing:
    - Class attributes from assignments (inherited from BaseAnalysisVisitor)
    - Method definitions
    - Nested class definitions
    
    Inherits all functionality from BaseAnalysisVisitor:
    - visit_Assign() - handles un-annotated assignments
    - visit_AnnAssign() - handles annotated assignments with validation
    - visit_ClassDef() - adds nested class definitions to scope
    - visit_FunctionDef() - adds method definitions to scope
    - visit_AsyncFunctionDef() - adds async method definitions to scope
    
    Also inherits shared functionality:
    - linearize() for expression processing
    - _infer_type() for type determination
    - _infer_literal_type() for literal handling
    - _extract_type_from_annotation() for type hint extraction
    - _resolve_annotation() for annotation-to-FQN resolution
    - _process_assignment() for unified assignment handling
    
    Extends BaseAnalysisVisitor by dispatching FunctionAnalysisVisitor for methods.
    
    All analysis notes are attached to the ClassNode (locality principle).
    """
    
    def __init__(self, class_node, parent_scope=None):
        """
        Initialize visitor for a specific class node.
        
        Args:
            class_node: The ClassNode being analyzed (where notes attach)
            parent_scope: The scope from the parent visitor (ModuleAnalysisVisitor)
        """
        super().__init__(class_node, parent_scope)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """
        Visit method definitions within the class.
        
        Overrides base implementation to dispatch FunctionAnalysisVisitor
        for analyzing method bodies with nested scope.
        """
        # FIRST: Call super() to add method to class scope
        super().visit_FunctionDef(node)
        
        # SECOND: Dispatch FunctionAnalysisVisitor to analyze method body
        method_node = self.node.get_method(node.name)
        if method_node:
            print(f"      Dispatching FunctionAnalysisVisitor for method: {node.name}")
            from .function_analysis_visitor import FunctionAnalysisVisitor
            visitor = FunctionAnalysisVisitor(method_node, self.scope)
            try:
                visitor.visit(method_node.source_data)
            finally:
                # Pop the child visitor's frame after it finishes
                self.scope.pop_frame()
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """
        Visit async method definitions within the class.
        
        Overrides base implementation to dispatch FunctionAnalysisVisitor
        for analyzing async method bodies with nested scope.
        """
        # FIRST: Call super() to add async method to class scope
        super().visit_AsyncFunctionDef(node)
        
        # SECOND: Dispatch FunctionAnalysisVisitor to analyze method body
        method_node = self.node.get_method(node.name)
        if method_node:
            print(f"      Dispatching FunctionAnalysisVisitor for async method: {node.name}")
            from .function_analysis_visitor import FunctionAnalysisVisitor
            visitor = FunctionAnalysisVisitor(method_node, self.scope)
            try:
                visitor.visit(method_node.source_data)
            finally:
                # Pop the child visitor's frame after it finishes
                self.scope.pop_frame()
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """
        Visit nested class definitions within the class.
        
        Overrides base implementation to dispatch ClassAnalysisVisitor
        for analyzing nested class bodies with nested scope.
        """
        # FIRST: Call super() to add nested class to scope
        super().visit_ClassDef(node)
        
        # SECOND: Dispatch ClassAnalysisVisitor to analyze nested class body
        nested_class = self.node.get_class(node.name)
        if nested_class:
            visitor = ClassAnalysisVisitor(nested_class, self.scope)
            try:
                visitor.visit(nested_class.source_data)
            finally:
                # Pop the child visitor's frame after it finishes
                self.scope.pop_frame()