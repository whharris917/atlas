"""Function Analysis Visitor - Type inference for function-level code."""

import ast
from .base_analysis_visitor import BaseAnalysisVisitor


class FunctionAnalysisVisitor(BaseAnalysisVisitor):
    """
    Analyzes function-level code and infers types for local variables.
    
    This visitor walks the function's AST to build a complete scope containing:
    - Function parameters (added to scope before body analysis)
    - Local variables from assignments (inherited from BaseAnalysisVisitor)
    - Nested function definitions
    - Nested class definitions
    
    Inherits all functionality from BaseAnalysisVisitor:
    - visit_Assign() - handles un-annotated assignments
    - visit_AnnAssign() - handles annotated assignments with validation
    - visit_ClassDef() - adds nested class definitions to scope
    - visit_FunctionDef() - adds nested function definitions to scope
    - visit_AsyncFunctionDef() - adds async nested function definitions to scope
    
    Also inherits shared functionality:
    - linearize() for expression processing
    - _infer_type() for type determination
    - _infer_literal_type() for literal handling
    - _extract_type_from_annotation() for type hint extraction
    - _resolve_annotation() for annotation-to-FQN resolution
    - _process_assignment() for unified assignment handling
    
    Extends BaseAnalysisVisitor by adding function parameters to scope before
    analyzing the function body.
    
    All analysis notes are attached to the FunctionNode (locality principle).
    """
    
    def __init__(self, function_node, parent_scope=None):
        """
        Initialize visitor for a specific function node.
        
        Args:
            function_node: The FunctionNode being analyzed (where notes attach)
            parent_scope: The scope from the parent visitor (Module/Class)
        """
        super().__init__(function_node, parent_scope)
        
        # Add function parameters to scope before analyzing body
        self._add_parameters_to_scope()
    
    def _add_parameters_to_scope(self):
        """
        Add function parameters to scope before analyzing function body.
        
        This ensures parameters are available for type inference within the function.
        For now, parameters are added with None type (no inference yet).
        
        Future enhancement: Infer parameter types from annotations.
        """
        for param in self.node.list_arguments():
            # Add parameter to scope
            # For now, we don't infer the type (would require annotation handling)
            # Just mark that the parameter exists
            self.scope.add(param.name, None)
            print(f"   Parameter: {param.name} (type unknown)")