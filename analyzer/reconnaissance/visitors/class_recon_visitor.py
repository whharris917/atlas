"""
Class Reconnaissance Visitor - Atlas Rewrite

Enhanced specialized AST visitor for comprehensive class-level entity discovery.
Discovers: methods, class-level attributes, and instance attributes from __init__.
"""

import ast
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from ...nodes import ClassNode


class ClassReconnaissanceVisitor(ast.NodeVisitor):
    """
    Discovers class-level entities: methods, class attributes, instance attributes.
    Focused on comprehensive class body and __init__ method discovery.
    """
    
    def __init__(self, class_node: 'ClassNode'):
        self.class_node = class_node
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Create method node and analyze __init__ for instance attributes."""
        self.class_node.create_method(node)
        print(f"      Found method: {self.class_node.fqn}.{node.name}")
        
        # Special handling for __init__ method to discover instance attributes
        if node.name == "__init__":
            self._analyze_init_for_instance_attributes(node)
        
        # Don't visit method internals - handled by FunctionReconnaissanceVisitor
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Create async method node and analyze async __init__ if applicable."""
        self.class_node.create_method(node)
        print(f"      Found async method: {self.class_node.fqn}.{node.name}")
        
        # Special handling for async __init__ method (rare but possible)
        if node.name == "__init__":
            self._analyze_init_for_instance_attributes(node)
        
        # Don't visit method internals
    
    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Create class-level annotated attribute."""
        if isinstance(node.target, ast.Name):
            # Simple class attribute: attr: Type = value
            self.class_node.create_class_attribute(node)
            print(f"        Found class attribute: {self.class_node.fqn}.{node.target.id}")
        else:
            # Complex target pattern - not a simple class attribute
            print(f"        Skipping complex annotated assignment target: {ast.unparse(node.target)}")
    
    def visit_Assign(self, node: ast.Assign):
        """Create class-level unannotated attribute or violation for multi-target."""
        if len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                # Simple class attribute: attr = value
                self.class_node.create_class_attribute(node)
                print(f"        Found class attribute: {self.class_node.fqn}.{target.id}")
            else:
                # Complex target pattern - not a simple class attribute
                print(f"        Skipping complex assignment target: {ast.unparse(target)}")
        else:
            # Multi-target assignment: x = y = z = value
            target_names = []
            for target in node.targets:
                if isinstance(target, ast.Name):
                    target_names.append(target.id)
                else:
                    target_names.append(f"<complex:{ast.unparse(target)}>")
            
            self.class_node.create_multiple_target_attribute_violation(
                target_names=target_names,
                assignment_context="class-level"
            )
            print(f"        Created violation for multi-target class assignment: {', '.join(target_names)}")
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """
        Handle ClassDef nodes - traverse body for the main class, skip nested classes.
        
        This method is called in two scenarios:
        1. Initially with the main class (self.class_node.source_data) from ClassNode._create_children()
        2. During traversal when encountering nested classes within the main class body
        
        We use identity comparison (is not) to distinguish between these cases because:
        - The main class is the specific AST node we were initialized to analyze
        - Nested classes are different AST node objects encountered during traversal
        
        Design Decision: Skip nested classes for now to keep reconnaissance phase focused.
        Complex nested class relationships are better handled in the analysis phase.
        """
        if node is not self.class_node.source_data:
            return  # Skip nested classes - do not traverse their contents
        
        # This is the main class we were initialized to analyze
        # Use standard AST traversal to find all direct children:
        # - ast.FunctionDef nodes -> triggers visit_FunctionDef() for method discovery
        # - ast.AnnAssign nodes -> triggers visit_AnnAssign() for class attributes  
        # - ast.Assign nodes -> triggers visit_Assign() for class attributes
        # - ast.ClassDef nodes -> triggers visit_ClassDef() again (will be skipped above)
        self.generic_visit(node)
        
        # Future Enhancement: To enable nested class support, add logic here:
        # if ENABLE_NESTED_CLASSES and node is not self.class_node.source_data:
        #     # Create nested class node and recursively analyze it
        #     nested_class_node = self.class_node.create_nested_class(node)
        #     nested_visitor = ClassReconnaissanceVisitor(nested_class_node)
        #     nested_visitor.visit(node)
        #     return

    def _analyze_init_for_instance_attributes(self, init_node: ast.FunctionDef):
        """
        Extract instance attributes from __init__ method body.
        
        Analyzes direct statements in __init__ body for self.attr assignments.
        Ignores nested control flow to keep reconnaissance phase focused.
        """
        print(f"        Analyzing __init__ for instance attributes...")
        
        for stmt in init_node.body:
            self._analyze_init_statement(stmt)
    
    def _analyze_init_statement(self, stmt: ast.AST):
        """Analyze individual statement in __init__ for instance attributes."""
        if isinstance(stmt, ast.Assign):
            self._handle_init_assign(stmt)
        elif isinstance(stmt, ast.AnnAssign):
            self._handle_init_ann_assign(stmt)
        # Ignore other statement types (if, while, try, etc.) for now
    
    def _handle_init_assign(self, node: ast.Assign):
        """Handle ast.Assign in __init__ method for instance attribute discovery."""
        if len(node.targets) == 1:
            target = node.targets[0]
            if self._is_self_attribute_target(target):
                # Instance attribute: self.attr = value
                self.class_node.create_instance_attribute(node)
                attr_name = target.attr
                print(f"          Found instance attribute: {self.class_node.fqn}.{attr_name}")
            # Ignore non-self assignments (local variables, other object attributes)
        else:
            # Multi-target assignment in __init__
            self_targets = []
            for target in node.targets:
                if self._is_self_attribute_target(target):
                    self_targets.append(target.attr)
            
            if self_targets:
                # At least some targets are self.attr - create violation
                self.class_node.create_multiple_target_attribute_violation(
                    target_names=self_targets,
                    assignment_context="instance-level"
                )
                print(f"          Created violation for multi-target instance assignment: {', '.join(self_targets)}")
    
    def _handle_init_ann_assign(self, node: ast.AnnAssign):
        """Handle ast.AnnAssign in __init__ method for annotated instance attributes."""
        if self._is_self_attribute_target(node.target):
            # Annotated instance attribute: self.attr: Type = value
            self.class_node.create_instance_attribute(node)
            attr_name = node.target.attr
            print(f"          Found annotated instance attribute: {self.class_node.fqn}.{attr_name}")
        # Ignore non-self annotated assignments
    
    def _is_self_attribute_target(self, target: ast.AST) -> bool:
        """Check if target is a self.attribute pattern."""
        return (isinstance(target, ast.Attribute) and 
                isinstance(target.value, ast.Name) and 
                target.value.id == "self")
    
    def _extract_target_names(self, targets: List[ast.AST]) -> List[str]:
        """Extract names from assignment targets for violation reporting."""
        names = []
        for target in targets:
            if isinstance(target, ast.Name):
                names.append(target.id)
            elif isinstance(target, ast.Attribute) and self._is_self_attribute_target(target):
                names.append(target.attr)
            else:
                names.append(f"<complex:{ast.unparse(target)}>")
        return names