"""Module Analysis Visitor - Type inference for module-level code."""

import ast
from .base_analysis_visitor import BaseAnalysisVisitor


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
    - visit_ClassDef() - adds class definitions to scope (overridden for cascade)
    - visit_FunctionDef() - adds function definitions to scope (overridden for cascade)
    - visit_AsyncFunctionDef() - adds async function definitions to scope
    
    Also inherits shared functionality:
    - linearize() for expression processing
    - _infer_type() for type determination (with Dot and CallFunction support)
    - _infer_literal_type() for literal handling
    - _extract_type_from_annotation() for type hint extraction
    - _resolve_annotation() for annotation-to-FQN resolution
    - _process_assignment() for unified assignment handling
    
    Extends BaseAnalysisVisitor by cascading to child nodes for nested scope analysis.
    Instead of directly dispatching child visitors, delegates to node.analyze() which
    follows the established cascade pattern.
    
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
        Visit class definitions and cascade to node.analyze().
        
        Overrides base implementation to:
        1. Add class to module scope (via super())
        2. Delegate to ClassNode.analyze() for nested scope analysis
        """
        # FIRST: Call super() to add class to module scope
        super().visit_ClassDef(node)
        
        # SECOND: Cascade to child node via analyze()
        class_node = self.node.get_class(node.name)
        if not class_node:
            raise ValueError(f"ClassNode for '{node.name}' not found in tree")
        class_node.analyze(parent_scope=self.scope)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """
        Visit function definitions and cascade to node.analyze().
        
        Overrides base implementation to:
        1. Add function to module scope (via super())
        2. Delegate to FunctionNode.analyze() for nested scope analysis
        """
        # FIRST: Call super() to add function to module scope
        super().visit_FunctionDef(node)
        
        # SECOND: Cascade to child node via analyze()
        function_node = self.node.get_function(node.name)
        if not function_node:
            raise ValueError(f"FunctionNode for '{node.name}' not found in tree")
        function_node.analyze(parent_scope=self.scope)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """
        Visit async function definitions and cascade to node.analyze().
        
        Overrides base implementation to:
        1. Add async function to module scope (via super())
        2. Delegate to FunctionNode.analyze() for nested scope analysis
        """
        # FIRST: Call super() to add function to module scope
        super().visit_AsyncFunctionDef(node)
        
        # SECOND: Cascade to child node via analyze()
        function_node = self.node.get_function(node.name)
        if not function_node:
            raise ValueError(f"FunctionNode for '{node.name}' not found in tree")
        function_node.analyze(parent_scope=self.scope)