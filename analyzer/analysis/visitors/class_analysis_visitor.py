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
        
        # Add "self" to class scope, mapped to this class's FQN
        # This enables method bodies to resolve self.attribute naturally
        self.scope.add("self", self.node.fqn)
        
        # Resolve base class names to FQNs and populate base_class_fqns
        # This enables inheritance resolution during navigation
        self._resolve_base_classes()
    
    def _resolve_base_classes(self):
        """
        Resolve base class names to FQNs using scope lookup.
        
        Takes the unresolved base class names from Reconnaissance Phase
        (e.g., "BaseEntity", "LoggingMixin") and resolves them to FQNs
        (e.g., "sample_files.core.base.BaseEntity") using the current scope.
        
        Handles both simple names and qualified names:
        - Simple: "BaseEntity" → scope.lookup() → "sample_files.core.base.BaseEntity"
        - Qualified: "collections.abc.Mapping" → used as-is (already a FQN)
        
        Stores resolved FQNs in self.node.base_class_fqns dictionary mapping
        base class name to resolved FQN. This enables debugging and validation
        of resolution while providing natural idempotency for multi-pass analysis.
        
        The dictionary structure:
        - Key: base class name as it appears in source (e.g., "BaseEntity")
        - Value: resolved FQN (e.g., "sample_files.core.base.BaseEntity")
        
        This runs during Analysis Phase initialization, so subsequent
        navigation operations can use the resolved FQNs via .values().
        """
        for base_name in self.node.base_classes:
            base_fqn = self.scope.lookup(base_name)
            
            # If not found in scope but name is already qualified (has dots),
            # treat it as a valid FQN (e.g., collections.abc.Mapping)
            if not base_fqn and '.' in base_name:
                base_fqn = base_name
            
            if base_fqn:
                # CHANGED: Dict assignment instead of list append
                # This is naturally idempotent - multi-pass safe!
                self.node.base_class_fqns[base_name] = base_fqn
                print(f"      Resolved base class: {base_name} → {base_fqn}")
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """
        Visit method definitions and cascade to node.analyze().
        
        Overrides base implementation to:
        1. Add method to class scope (via super())
        2. Cascade to method's analyze() for function-level analysis
        
        The cascade follows established pattern where nodes orchestrate
        their own analysis by creating appropriate visitors.
        
        Args:
            node: ast.FunctionDef for method definition
        """
        # First: Call super() to add method to scope
        super().visit_FunctionDef(node)
        
        # Second: Cascade to method's analyze() if it exists
        method_node = self.node.get_method(node.name)
        if not method_node:
            raise ValueError(f"FunctionNode for method '{node.name}' not found in tree")
        method_node.analyze(parent_scope=self.scope)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """
        Visit async method definitions and cascade to node.analyze().
        
        Same pattern as visit_FunctionDef but for async methods.
        
        Args:
            node: ast.AsyncFunctionDef for async method definition
        """
        # First: Call super() to add method to scope
        super().visit_AsyncFunctionDef(node)
        
        # Second: Cascade to method's analyze() if it exists
        method_node = self.node.get_method(node.name)
        if not method_node:
            raise ValueError(f"FunctionNode for async method '{node.name}' not found in tree")
        method_node.analyze(parent_scope=self.scope)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """
        Visit nested class definitions and cascade to node.analyze().
        
        Same pattern as visit_FunctionDef but for nested classes.
        
        Args:
            node: ast.ClassDef for nested class definition
        """
        # First: Call super() to add class to scope
        super().visit_ClassDef(node)
        
        # Second: Cascade to nested class's analyze() if it exists
        nested_class = self.node.get_class(node.name)
        if not nested_class:
            raise ValueError(f"Nested ClassNode for '{node.name}' not found in tree")
        nested_class.analyze(parent_scope=self.scope)