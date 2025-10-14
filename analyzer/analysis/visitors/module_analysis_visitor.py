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
    - visit_ClassDef() - adds class definitions to scope
    - visit_FunctionDef() - adds function definitions to scope
    - visit_AsyncFunctionDef() - adds async function definitions to scope
    
    Also inherits shared functionality:
    - linearize() for expression processing
    - _infer_type() for type determination (with Dot and CallFunction support)
    - _infer_literal_type() for literal handling
    - _extract_type_from_annotation() for type hint extraction
    - _resolve_annotation() for annotation-to-FQN resolution
    - _process_assignment() for unified assignment handling
    
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