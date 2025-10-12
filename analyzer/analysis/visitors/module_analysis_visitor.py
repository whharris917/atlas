"""Module Analysis Visitor - Type inference for module-level code."""

import ast
from .base_analysis_visitor import BaseAnalysisVisitor
from ..scope import Scope
from ..expression_traversal import TypeInferenceEngine


class ModuleAnalysisVisitor(BaseAnalysisVisitor):
    """
    Analyzes module-level code and infers types for assignments.
    
    This visitor walks the module's AST to infer types of module-level
    variables and build a scope that child visitors can inherit.
    
    Inherits from BaseAnalysisVisitor to access shared linearize() method.
    
    All analysis notes are attached to the ModuleNode (locality principle).
    """
    
    def __init__(self, module_node):
        """
        Initialize visitor for a specific module node.
        
        Args:
            module_node: The ModuleNode being analyzed (where notes attach)
        """
        self.module_node = module_node
        
        # Create TypeInferenceEngine using project reference from tree
        project = module_node.get_project()
        self.engine = TypeInferenceEngine(project)
        
        self.scope = Scope()
        self.scope.push_frame()  # Create the module-level scope frame
        self.assignment_count = 0
    
    def visit_Assign(self, node: ast.Assign):
        """
        Visit module-level assignments: x = 5
        
        Infers the type of the value and adds it to the scope.
        """
        self.assignment_count += 1
        
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
        
        # Use engine to infer type from the value expression
        type_fqn = self.engine.get_type(node.value, self.scope)
        
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
        
        Infers the type from the value (annotation parsing comes later).
        """
        self.assignment_count += 1
        
        # Only handle simple Name targets
        if not isinstance(node.target, ast.Name):
            self.generic_visit(node)
            return
        
        var_name = node.target.id
        
        # Use engine to infer type from value if present
        if node.value:
            type_fqn = self.engine.get_type(node.value, self.scope)
            
            if type_fqn:
                self.scope.add(var_name, type_fqn)
                print(f"   Inferred: {var_name} = {type_fqn} (line {node.lineno})")
            else:
                print(f"   Could not infer type for: {var_name} (line {node.lineno})")
        
        self.generic_visit(node)