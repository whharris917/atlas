"""
Base Analysis Visitor - Shared functionality for all analysis visitors.

All analysis visitors (ModuleAnalysisVisitor, FunctionAnalysisVisitor, etc.)
inherit from this base class to access shared linearization and type inference.
"""

import ast
from typing import Optional

from ..scope import Scope
from ..type_inference import TypeInferenceEngine

from ...notes import (
    ScopeAddition,
    TypeInference,
    TypeInferenceFailure,
    IncorrectTypeAnnotation
)


class BaseAnalysisVisitor(ast.NodeVisitor):
    """
    Base class for all analysis visitors providing shared functionality.
    
    All analysis visitors inherit from this class to access:
    - Expression linearization (converting nested AST to Linear Operation Queue)
    - Type inference from literals, expressions, and annotations
    - Scope management for variable type tracking
    - Scope population (imports, classes, functions)
    - Future shared utilities for analysis
    
    Subclasses should call super().__init__(node, parent_scope) to initialize
    the base visitor, where node is the specific node being analyzed and
    parent_scope is the optional scope from the parent visitor.

    
    OVERRIDE PATTERN FOR SUBCLASSES:
    
    The base class handles scope population (adding entities to scope as they're
    encountered during traversal). Subclasses override visit_* methods to add
    specialized behavior like dispatching child visitors.
    
    The pattern is ALWAYS:
        1. Call super().visit_*() FIRST to handle scope building
        2. Then add specialized logic (usually child visitor dispatch)
    
    This order is critical because:
        - Entities must be in scope BEFORE analyzing their bodies
        - Enables self-reference (class can reference itself)
        - Maintains use-before-definition detection
    
    Methods that subclasses commonly override:
        - visit_ClassDef: Dispatch ClassAnalysisVisitor to analyze class body
        - visit_FunctionDef: Dispatch FunctionAnalysisVisitor to analyze function body
        - visit_AsyncFunctionDef: Same as FunctionDef for async functions
    
    Methods that subclasses typically DON'T override:
        - visit_Import, visit_ImportFrom: Imports fully handled in base
        - visit_Assign, visit_AnnAssign: Assignments fully handled in base
        - _process_assignment: Override this if you need custom assignment logic
    """
    
    def __init__(self, node, parent_scope: Optional[Scope] = None):
        """
        Initialize base visitor with the node being analyzed.
        
        All analysis visitors need access to their node to navigate to the
        project for FQN resolution during type inference.
        
        Args:
            node: The tree node being analyzed (ModuleNode, FunctionNode, ClassNode, etc.)
            parent_scope: Optional Scope from parent visitor. If provided, inherits parent's
                         scope and pushes a new frame for this level. If None, creates a
                         fresh Scope (used by root-level ModuleAnalysisVisitor).
        """
        self.node = node
        
        # Scope inheritance: child visitors inherit parent scope
        if parent_scope:
            # Child visitor: inherit parent scope and push new frame
            self.scope = parent_scope
            self.scope.push_frame()
        else:
            # Root visitor: create fresh scope and push initial frame
            self.scope = Scope()
            self.scope.push_frame()
        
        # Initialize type inference engine
        self.type_engine = TypeInferenceEngine(self.node, self.scope)
    
    # ========================================================================
    # Assignment Processing - Inherited by All Visitors
    # ========================================================================
    
    def visit_Assign(self, node: ast.Assign):
        """
        Visit un-annotated assignments: x = 5
        
        Delegates to unified assignment processing.
        
        Subclasses typically do NOT need to override this method.
        The base implementation handles:
        - Type inference from values
        - Scope population
        - All common assignment patterns
        
        If you have specialized assignment handling needs, override
        _process_assignment() instead of this method.
        """
        self._process_assignment(node, annotated=False)
    
    def visit_AnnAssign(self, node: ast.AnnAssign):
        """
        Visit annotated assignments: x: int = 5
        
        Delegates to unified assignment processing with annotation validation.
        
        Subclasses typically do NOT need to override this method.
        The base implementation handles:
        - Type inference from values
        - Annotation resolution to FQNs
        - Annotation vs inferred type validation
        - Violation creation on mismatch
        - Scope population
        
        If you have specialized assignment handling needs, override
        _process_assignment() instead of this method.
        """
        self._process_assignment(node, annotated=True)
    
    def _process_assignment(self, node, annotated: bool):
        """
        Unified assignment processing for both annotated and un-annotated assignments.
        
        Handles:
        - Type inference from values
        - Annotation resolution to FQNs
        - Annotation vs inferred type validation
        - Violation creation on mismatch
        - Scope population
        
        Args:
            node: ast.Assign or ast.AnnAssign node
            annotated: True for AnnAssign, False for Assign
        """
        # Extract target (different structure for Assign vs AnnAssign)
        if annotated:
            # AnnAssign: node.target (single target)
            if not isinstance(node.target, ast.Name):
                self.generic_visit(node)
                return
            var_name = node.target.id
        else:
            # Assign: node.targets (list of targets)
            if len(node.targets) != 1:
                self.generic_visit(node)
                return
            target = node.targets[0]
            if not isinstance(target, ast.Name):
                self.generic_visit(node)
                return
            var_name = target.id
        
        # Extract and resolve annotation if present
        annotation_fqn = None
        if annotated and hasattr(node, 'annotation'):
            annotation_str = self.type_engine.extract_type_from_annotation(node.annotation)
            if annotation_str:
                annotation_fqn = self.type_engine.resolve_annotation(annotation_str)
        
        # Infer type from value if present
        inferred_type = None
        if hasattr(node, 'value') and node.value:
            inferred_type = self.type_engine.infer_type(node.value)
            if inferred_type:
                note = TypeInference(
                    parent=self.node,
                    variable_name=var_name,
                    inferred_type=inferred_type,
                    line_number=node.lineno
                )
                self.node.add_note(note)
        
        # Determine which type to use in scope
        type_for_scope = None
        
        if annotation_fqn and inferred_type:
            # Both annotation and inferred type available - compare them
            if annotation_fqn != inferred_type:
                # Mismatch! Create violation
                note = IncorrectTypeAnnotation(
                    parent=self.node,
                    variable_name=var_name,
                    annotation=annotation_fqn,
                    inferred=inferred_type,
                    line_number=node.lineno
                )
                self.node.add_note(note)
            
            # Use inferred type (ground truth is runtime behavior)
            type_for_scope = inferred_type
        
        elif annotation_fqn:
            # Only annotation available (no value, or couldn't infer)
            type_for_scope = annotation_fqn
        
        elif inferred_type:
            # Only inferred type available (no annotation, or couldn't extract)
            type_for_scope = inferred_type
        
        # Add to scope if we have a type
        if type_for_scope:
            self.scope.add(var_name, type_for_scope)
            note = TypeInference(
                parent=self.node,
                variable_name=var_name,
                inferred_type=type_for_scope,
                line_number=node.lineno
            )
            self.node.add_note(note)
        else:
            note = TypeInferenceFailure(
                parent=self.node,
                variable_name=var_name,
                line_number=node.lineno
            )
            self.node.add_note(note)
        
        self.generic_visit(node)
    
    # ========================================================================
    # Scope Population Methods - Inherited by All Visitors
    # ========================================================================
    
    def visit_Import(self, node: ast.Import):
        """
        Visit import statements: import json, import os.path
        
        Adds imported names to scope. For simple imports like 'import json',
        the name 'json' maps to 'json'. For 'import os.path', the name 'os'
        maps to 'os'.
        
        Subclasses typically do NOT need to override this method.
        Imports don't have bodies to analyze, so no child visitor dispatch needed.
        The base implementation handles all import scope population.
        
        If you do override (rarely needed), call super() to ensure imports
        are added to scope:
            def visit_Import(self, node):
                super().visit_Import(node)  # Add to scope
                # Your specialized logic here
        """
        for alias in node.names:
            # Use alias if provided (import json as j), otherwise use module name
            name = alias.asname if alias.asname else alias.name
            
            # For imports, store the module name as-is
            # Examples: 'import json' → scope['json'] = 'json'
            #           'import os.path' → scope['os'] = 'os'
            self.scope.add(name, alias.name)
            note = ScopeAddition(
                parent=self.node,
                entity_name=name,
                entity_fqn=alias.name,
                entity_type="import"
            )
            self.node.add_note(note)
        
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """
        Visit from-import statements: from models import User
        
        Resolves imported names to their FQNs and adds to scope.
        Handles both absolute and relative imports.
        
        Subclasses typically do NOT need to override this method.
        Imports don't have bodies to analyze, so no child visitor dispatch needed.
        The base implementation handles all import scope population.
        
        If you do override (rarely needed), call super() to ensure imports
        are added to scope:
            def visit_ImportFrom(self, node):
                super().visit_ImportFrom(node)  # Add to scope
                # Your specialized logic here
        """
        # Determine the base module being imported from
        if node.module:
            # Absolute or relative import with explicit module
            if node.level > 0:
                # Relative import: from .models import User
                # Need to resolve relative to current module
                base_module = self._resolve_relative_import(node.module, node.level)
            else:
                # Absolute import: from models import User
                base_module = node.module
        else:
            # Relative import without module: from . import utils
            # Imports from parent package
            base_module = self._resolve_relative_import(None, node.level)
        
        # Add each imported name to scope
        for alias in node.names:
            if alias.name == '*':
                # from models import * - skip for now
                print(f"   ImportFrom: * (wildcard imports not tracked)")
                continue
            
            # Use alias if provided, otherwise use imported name
            name = alias.asname if alias.asname else alias.name
            
            # Build FQN: base_module.name
            if base_module:
                fqn = f"{base_module}.{alias.name}"
            else:
                fqn = alias.name
            
            self.scope.add(name, fqn)
            note = ScopeAddition(
                parent=self.node,
                entity_name=name,
                entity_fqn=fqn,
                entity_type="import"
            )
            self.node.add_note(note)
        
        self.generic_visit(node)
    
    def _resolve_relative_import(self, module: str, level: int) -> str:
        """
        Resolve a relative import to absolute module path.
        
        Args:
            module: The module name (or None for package imports)
            level: Number of dots (1 = current package, 2 = parent, etc.)
            
        Returns:
            Resolved absolute module path
        """
        # Get the current node's FQN
        current_fqn = self.node.fqn
        
        # Split into parts: sample_files.models.user → ['sample_files', 'models', 'user']
        parts = current_fqn.split('.')
        
        # Remove 'level' parts from the end (including current module name)
        # level=1 means current package, level=2 means parent package
        base_parts = parts[:-level] if level <= len(parts) else []
        
        # Add the module if specified
        if module:
            base_parts.append(module)
        
        return '.'.join(base_parts) if base_parts else ''
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """
        Visit class definitions: class User:
        
        Base implementation adds class name to scope with its FQN.
        Does not traverse into class body.
        
        Subclasses should override this method to dispatch child visitors:
        
        Example override in ModuleAnalysisVisitor:
            def visit_ClassDef(self, node):
                # FIRST: Call super() to add class to scope
                super().visit_ClassDef(node)
                
                # SECOND: Dispatch ClassAnalysisVisitor to analyze class body
                class_node = self.node.get_class(node.name)
                ClassAnalysisVisitor(class_node, self.scope).visit(...)
        
        Why this order matters:
        - Class must be in scope BEFORE analyzing its body
        - Body analysis can reference the class itself (self-reference)
        - Maintains use-before-definition detection
        """
        class_name = node.name
        
        # Build FQN: parent_fqn.class_name
        class_fqn = f"{self.node.fqn}.{class_name}"
        
        self.scope.add(class_name, class_fqn)
        note = ScopeAddition(
            parent=self.node,
            entity_name=class_name,
            entity_fqn=class_fqn,
            entity_type="class"
        )
        self.node.add_note(note)
        
        # Don't traverse into class body by default
        # Subclasses can override this behavior
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """
        Visit function definitions: def process():
        
        Base implementation adds function name to scope with its FQN.
        Does not traverse into function body.
        
        Subclasses should override this method to dispatch child visitors:
        
        Example override in ModuleAnalysisVisitor:
            def visit_FunctionDef(self, node):
                # FIRST: Call super() to add function to scope
                super().visit_FunctionDef(node)
                
                # SECOND: Dispatch FunctionAnalysisVisitor to analyze function body
                func_node = self.node.get_function(node.name)
                FunctionAnalysisVisitor(func_node, self.scope).visit(...)
        
        Example override in ClassAnalysisVisitor (for methods):
            def visit_FunctionDef(self, node):
                # FIRST: Call super() to add method to class scope
                super().visit_FunctionDef(node)
                
                # SECOND: Dispatch FunctionAnalysisVisitor to analyze method body
                method_node = self.node.get_method(node.name)
                FunctionAnalysisVisitor(method_node, self.scope).visit(...)
        
        Why this order matters:
        - Function must be in scope BEFORE analyzing its body
        - Enables recursive function calls (function can call itself)
        - Maintains use-before-definition detection
        """
        func_name = node.name
        
        # Build FQN: parent_fqn.func_name
        func_fqn = f"{self.node.fqn}.{func_name}"
        
        self.scope.add(func_name, func_fqn)
        note = ScopeAddition(
            parent=self.node,
            entity_name=func_name,
            entity_fqn=func_fqn,
            entity_type="function"
        )
        self.node.add_note(note)
        
        # Don't traverse into function body by default
        # Subclasses can override this behavior
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """
        Visit async function definitions: async def fetch():
        
        Base implementation adds function name to scope with its FQN.
        Does not traverse into function body.
        
        Subclasses should override this method to dispatch child visitors
        (same pattern as visit_FunctionDef):
        
        Example override:
            def visit_AsyncFunctionDef(self, node):
                # FIRST: Call super() to add async function to scope
                super().visit_AsyncFunctionDef(node)
                
                # SECOND: Dispatch FunctionAnalysisVisitor to analyze body
                func_node = self.node.get_function(node.name)
                FunctionAnalysisVisitor(func_node, self.scope).visit(...)
        
        Why this order matters:
        - Async function must be in scope BEFORE analyzing its body
        - Same rationale as regular function definitions
        """
        func_name = node.name
        
        # Build FQN: parent_fqn.func_name
        func_fqn = f"{self.node.fqn}.{func_name}"
        
        self.scope.add(func_name, func_fqn)
        note = ScopeAddition(
            parent=self.node,
            entity_name=func_name,
            entity_fqn=func_fqn,
            entity_type="function"
        )
        self.node.add_note(note)
        
        # Don't traverse into function body by default
        # Subclasses can override this behavior