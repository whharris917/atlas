"""Module Analysis Visitor - Type inference for module-level code."""

import ast
from .base_analysis_visitor import BaseAnalysisVisitor


class ModuleAnalysisVisitor(BaseAnalysisVisitor):
    """
    Analyzes module-level code and infers types for assignments.
    
    This visitor walks the module's AST to build a complete scope containing:
    - Variables from assignments
    - Imported names (modules and specific imports)
    - Class definitions
    - Function definitions
    
    Inherits all scope population methods from BaseAnalysisVisitor:
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
    
    def visit_Assign(self, node: ast.Assign):
        """
        Visit module-level assignments: x = 5
        
        Infers the type of the value and adds it to the scope.
        """
        # Only handle simple single-target assignments for now
        if len(node.targets) != 1:
            self.generic_visit(node)
            return
        
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            self.generic_visit(node)
            return
        
        # Extract variable name
        var_name = target.id
        
        # Infer type using inherited method (now handles Dot and CallFunction!)
        type_fqn = self._infer_type(node.value)
        
        # If we got a type, add it to scope
        if type_fqn:
            self.scope.add(var_name, type_fqn)
            print(f"   Inferred: {var_name} = {type_fqn} (line {node.lineno})")
        else:
            print(f"   Could not infer type for: {var_name} (line {node.lineno})")
        
        self.generic_visit(node)
    
    def visit_AnnAssign(self, node: ast.AnnAssign):
        """
        Visit annotated assignments: x: int = 5
        
        Prioritizes the annotation over value inference, but falls back
        to value inference if annotation extraction fails.
        """
        # Only handle simple Name targets
        if not isinstance(node.target, ast.Name):
            self.generic_visit(node)
            return
        
        var_name = node.target.id
        
        # Try to extract type from annotation first
        type_fqn = self._extract_type_from_annotation(node.annotation)
        
        # Fallback: Try value inference
        if not type_fqn and node.value:
            type_fqn = self._infer_type(node.value)
        
        # If we got a type, add it to scope
        if type_fqn:
            self.scope.add(var_name, type_fqn)
            print(f"   Inferred: {var_name} = {type_fqn} (line {node.lineno})")
        else:
            print(f"   Could not infer type for: {var_name} (line {node.lineno})")
        
        self.generic_visit(node)