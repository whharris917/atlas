"""Module Analysis Visitor - Minimal skeleton for testing."""

import ast
from typing import Dict


class ModuleAnalysisVisitor(ast.NodeVisitor):
    """
    Analyzes module-level code (minimal skeleton).
    
    This visitor walks the module's AST to demonstrate the visitor pattern.
    Future versions will infer types and create analysis notes.
    
    All analysis notes are attached to the ModuleNode (locality principle).
    """
    
    def __init__(self, module_node):
        """
        Initialize visitor for a specific module node.
        
        Args:
            module_node: The ModuleNode being analyzed (where notes attach)
        """
        self.module_node = module_node
        self.scope: Dict[str, str] = {}
        self.assignment_count = 0
    
    def visit_Assign(self, node: ast.Assign):
        """
        Visit module-level assignments: x = 5
        
        Currently just counts assignments to demonstrate visitor is working.
        """
        self.assignment_count += 1
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id
            print(f"   Found assignment: {var_name} = ... (line {node.lineno})")
        
        self.generic_visit(node)
    
    def visit_AnnAssign(self, node: ast.AnnAssign):
        """
        Visit annotated assignments: x: int = 5
        
        Currently just counts to demonstrate visitor is working.
        """
        self.assignment_count += 1
        if isinstance(node.target, ast.Name):
            var_name = node.target.id
            print(f"   Found annotated assignment: {var_name}: ... = ... (line {node.lineno})")
        
        self.generic_visit(node)