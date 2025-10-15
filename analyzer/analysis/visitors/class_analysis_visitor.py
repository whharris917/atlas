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
    - visit_FunctionDef() - adds method definitions to scope (overridden for cascade)
    - visit_AsyncFunctionDef() - adds async method definitions to scope
    
    Also inherits shared functionality:
    - linearize() for expression processing
    - _infer_type() for type determination
    - _infer_literal_type() for literal handling
    - _extract_type_from_annotation() for type hint extraction
    - _resolve_annotation() for annotation-to-FQN resolution
    - _process_assignment() for unified assignment handling
    
    Extends BaseAnalysisVisitor by cascading to child nodes for nested scope analysis:
    - Methods via FunctionNode.analyze()
    - Nested classes via ClassNode.analyze()
    
    Instead of directly dispatching child visitors, delegates to node.analyze() which
    follows the Session 32 cascade pattern.
    
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
        Visit method definitions and cascade to node.analyze().
        
        Overrides base implementation to:
        1. Add method to class scope (via super())
        2. Delegate to FunctionNode.analyze() for nested scope analysis
        """
        # FIRST: Call super() to add method to class scope
        super().visit_FunctionDef(node)
        
        # SECOND: Cascade to child node via analyze()
        method_node = self.node.get_method(node.name)
        if not method_node:
            raise ValueError(f"FunctionNode for method '{node.name}' not found in tree")
        method_node.analyze(parent_scope=self.scope)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """
        Visit async method definitions and cascade to node.analyze().
        
        Overrides base implementation to:
        1. Add async method to class scope (via super())
        2. Delegate to FunctionNode.analyze() for nested scope analysis
        """
        # FIRST: Call super() to add method to class scope
        super().visit_AsyncFunctionDef(node)
        
        # SECOND: Cascade to child node via analyze()
        method_node = self.node.get_method(node.name)
        if not method_node:
            raise ValueError(f"FunctionNode for async method '{node.name}' not found in tree")
        method_node.analyze(parent_scope=self.scope)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """
        Visit nested class definitions and cascade to node.analyze().
        
        Overrides base implementation to:
        1. Add nested class to class scope (via super())
        2. Delegate to nested ClassNode.analyze() for nested scope analysis
        """
        # FIRST: Call super() to add nested class to scope
        super().visit_ClassDef(node)
        
        # SECOND: Cascade to child node via analyze()
        nested_class_node = self.node.get_class(node.name)
        if not nested_class_node:
            raise ValueError(f"Nested ClassNode for '{node.name}' not found in tree")
        nested_class_node.analyze(parent_scope=self.scope)