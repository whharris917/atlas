"""
Base Analysis Visitor - Shared functionality for all analysis visitors.

All analysis visitors (ModuleAnalysisVisitor, FunctionAnalysisVisitor, etc.)
inherit from this base class to access shared linearization and type inference.
"""

import ast
from typing import List, Optional

from ..expression_traversal.operations import Operation, GetName, Dot, CallFunction, GetSubscript
from ..scope import Scope
from ...nodes import ClassNode

BUILTIN_CONSTRUCTORS = {
    'list', 'dict', 'set', 'tuple', 'frozenset',
    'str', 'int', 'float', 'bool', 'bytes', 'bytearray',
    'object', 'type', 'range', 'slice',
    'complex', 'memoryview'
}


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
    
    def linearize(self, expr: ast.expr) -> List[Operation]:
        """
        Convert a nested expression into a Linear Operation Queue (LOQ).
        
        This method provides a sequential representation of the operations
        within an expression, which can then be processed left-to-right.
        
        The linearization process is shared by all analysis visitors since
        any visitor may need to analyze expressions (assignments, calls,
        returns, etc.).
        
        CRITICAL: When encountering unsupported AST node types, this method
        creates an UnsupportedExpressionType violation on self.node instead
        of silently failing. This ensures developers are alerted to incomplete
        type inference.
        
        Args:
            expr: AST expression node (Name, Attribute, Call, Subscript, etc.)
            
        Returns:
            List of Operation objects representing the expression in sequence.
            May be incomplete if unsupported node types were encountered.
            
        Example:
            user.profile.email → [GetName('user'), Dot('profile'), Dot('email')]
            obj.method() → [GetName('obj'), Dot('method'), CallFunction()]
            users[0] → [GetName('users'), GetSubscript()]
            [1, 2, 3] → [] (container literals handled directly in _infer_type)
        """
        operations = []
        
        def traverse(node):
            """
            Recursively traverse AST node to build operation queue.
            
            Creates violations for unsupported node types instead of silently
            skipping them, ensuring incomplete type inference is visible.
            
            Supported node types:
            - ast.Name: Variable access (x, user, config)
            - ast.Attribute: Dot access (user.email, obj.method)
            - ast.Call: Function calls (func(), obj.method())
            - ast.Subscript: Index access (list[0], dict["key"])
            - ast.Constant: Literals (5, "hello", True, None)
            - ast.List, ast.Dict, ast.Set, ast.Tuple: Container literals
            
            Examples:
                user.profile.email → Name, Attribute, Attribute
                obj.method() → Name, Attribute, Call
                list[0] → Name, Subscript
                {"key": "value"} → Dict (no operations, handled directly)
            """
            if isinstance(node, ast.Name):
                # Variable name access: x, user, config
                operations.append(GetName(node.id))
            
            elif isinstance(node, ast.Attribute):
                # Attribute access: user.email, obj.method, self.name
                # First process the object being accessed, then the attribute
                traverse(node.value)
                operations.append(Dot(node.attr))
            
            elif isinstance(node, ast.Call):
                # Function/method call: func(), obj.method(), User()
                # First process what's being called, then add the call operation
                traverse(node.func)
                operations.append(CallFunction())
            
            elif isinstance(node, ast.Subscript):
                # Subscript access: list[0], dict["key"], matrix[i][j]
                # First process the container, then add subscript operation
                traverse(node.value)
                operations.append(GetSubscript())
            
            elif isinstance(node, ast.Constant):
                # Literal values: 5, "hello", True, None, 3.14
                # Handled separately in _infer_type() via _infer_literal_type()
                # No operation needed - just skip
                pass
            
            # NEW: Container literals
            elif isinstance(node, (ast.List, ast.Dict, ast.Set, ast.Tuple)):
                # Container literals: [], {}, set(), ()
                # Examples:
                #   [1, 2, 3] → ast.List
                #   {"key": "value"} → ast.Dict
                #   {1, 2, 3} → ast.Set
                #   (1, 2) → ast.Tuple
                #
                # These are terminal expressions (don't chain), so they're
                # handled directly in _infer_type() with no operations needed.
                # They return simple builtin type names: 'list', 'dict', 'set', 'tuple'
                pass
            
            else:
                # UNSUPPORTED EXPRESSION TYPE
                # Create violation to alert that type inference will be incomplete
                from ...violations import UnsupportedExpressionType
                
                line_number = node.lineno if hasattr(node, 'lineno') else self.node.line_number
                expression_type = node.__class__.__name__
                
                violation = UnsupportedExpressionType(
                    parent=self.node,
                    expression_type=expression_type,
                    line_number=line_number
                )
                self.node.add_violation(violation)
                
                print(f"   VIOLATION: Unsupported expression type '{expression_type}' "
                    f"at line {line_number}. Type inference may be incomplete.")
        
        traverse(expr)
        return operations

    def _infer_type(self, expr: ast.expr) -> Optional[str]:
        """
        Infer the type of an expression by navigating the tree.
        
        This method handles:
            - Literals (int, str, bool, float, None)
            - Container literals (list, dict, set, tuple)
            - Variable lookups (from scope)
            - Attribute access chains (user.profile.email, self.name)
            - Method calls (obj.method())
            - Subscript operations (list[0])
            
        Uses the tree navigation approach: linearize the expression into
        operations, then navigate the tree directly using .dot() rather
        than interpreting operations.
        
        Special handling for attributes: When navigation encounters an
        InstanceAttributeNode or ClassAttributeNode, it extracts the TYPE
        of that attribute for further navigation, enabling self.name.upper()
        style chains.
        
        Examples:
            5 → 'int'
            "hello" → 'str'
            [1, 2, 3] → 'list'
            {"key": "value"} → 'dict'
            user → 'sample_files.models.user.User' (from scope)
            user.email → 'str' (from User's email attribute type)
            User() → 'sample_files.models.user.User' (constructor)
            list() → 'list' (builtin constructor)
        
        Args:
            expr: AST expression node to analyze
            
        Returns:
            Type FQN as string, or None if type cannot be determined
        """
        # Handle simple literals directly (no linearization needed)
        # Examples: 5 → 'int', "hello" → 'str', True → 'bool', None → 'NoneType'
        if isinstance(expr, ast.Constant):
            return self._infer_literal_type(expr.value)
        
        # NEW: Handle container literals
        # These return builtin type names directly since they're terminal expressions
        
        if isinstance(expr, ast.List):
            # List literal: [1, 2, 3], [], [x, y, z]
            # Future enhancement: could analyze elements for List[int], List[User], etc.
            return 'list'
        
        if isinstance(expr, ast.Dict):
            # Dict literal: {"key": "value"}, {}, {1: "one", 2: "two"}
            # Future enhancement: could analyze keys/values for Dict[str, int], etc.
            return 'dict'
        
        if isinstance(expr, ast.Set):
            # Set literal: {1, 2, 3}, set()
            # Note: {} is ast.Dict (empty dict), not set
            # Future enhancement: could analyze elements for Set[int], etc.
            return 'set'
        
        if isinstance(expr, ast.Tuple):
            # Tuple literal: (1, 2), (x, y, z), ()
            # Future enhancement: could analyze elements for Tuple[int, str], etc.
            return 'tuple'
        
        # Linearize expression into operation queue
        # This converts nested expressions into sequential operations
        operations = self.linearize(expr)
        
        # Empty operation queue - cannot infer type
        if not operations:
            return None
        
        # Navigate the tree using the operation queue
        # Process each operation in sequence, where output of one becomes input of next
        current_type = None
        current_node = None
        project = self.node.get_project()
        
        for op in operations:
            if isinstance(op, GetName):
                # Variable lookup in scope
                # Example: 'user' → 'sample_files.models.user.User'
                current_type = self.scope.lookup(op.name)
                if current_type:
                    # Try to get tree node for further navigation
                    current_node = project.get_node_by_fqn(current_type)
                else:
                    # Variable not in scope - cannot continue
                    return None
            
            elif isinstance(op, Dot):
                # Navigate to child via .dot() method
                # Example: user.email → navigate from User node to email attribute
                if current_node:
                    child = current_node.dot(op.attr_name)
                    if child:
                        current_node = child
                        current_type = child.fqn if hasattr(child, 'fqn') else None
                    else:
                        # Navigation failed - child not found
                        return None
                else:
                    # No current node to navigate from
                    return None
            
            elif isinstance(op, CallFunction):
                # Three-case constructor/function resolution
                
                # CASE 1: CLASS CONSTRUCTOR
                # If current_node is a ClassNode, calling it creates an instance
                # Example: User() → returns instance of User class
                if current_node and isinstance(current_node, ClassNode):
                    # Constructor call returns instance of the class
                    current_type = current_node.fqn
                    # Keep current_node for chaining: User().get_email()
                
                # CASE 2: BUILTIN CONSTRUCTOR
                # If current_type is a builtin constructor name
                # Example: list() → 'list', dict() → 'dict'
                elif current_type in BUILTIN_CONSTRUCTORS:
                    # list() → 'list', dict() → 'dict'
                    # current_type already correct
                    # No tree node means no further navigation possible
                    current_node = None
                    # Continue to next operation (or return at loop end)
                
                # CASE 3: FUNCTION/METHOD CALL
                # Regular functions/methods have return type annotations
                # Example: get_user() → navigate to return type annotation
                elif current_node:
                    # Navigate to the return type annotation
                    return_node = current_node.dot("return")
                    if not return_node:
                        # No return node found (no annotation or doesn't exist)
                        return None
                    
                    type_node = return_node.dot("type")
                    if not type_node:
                        # Return node exists but no type annotation
                        return None
                    
                    # Extract the return type from TypeNode
                    current_type = ast.unparse(type_node.source_data)
                    
                    # Try to resolve return type to tree node for chaining
                    # Example: get_user().get_email() continues navigation
                    current_node = project.get_node_by_fqn(current_type)
                    
                    if not current_node:
                        # Type exists but no node (builtin or external)
                        # Can't navigate further but have the type
                        return current_type
                
                else:
                    # No current_node and not a builtin - cannot infer
                    # This happens when we have expressions like undefined_var()
                    return None
            
            elif isinstance(op, GetSubscript):
                # Subscript operation: list[0], dict["key"], matrix[i][j]
                # For now, we can't infer the element type
                # This requires extracting element types from generic annotations
                # Future enhancement: List[User] → User, Dict[str, int] → int
                return None
        
        return current_type
    
    def _infer_literal_type(self, value) -> str:
        """
        Infer type from a literal value.
        
        Args:
            value: The literal value from ast.Constant
            
        Returns:
            Type name as string (e.g., "int", "str", "bool", "NoneType")
        """
        return type(value).__name__
    
    def _extract_type_from_annotation(self, annotation: ast.expr) -> Optional[str]:
        """
        Extract type from a type annotation node.
        
        Handles both simple types (int, str) and complex generic types
        (List[int], Dict[str, User], Optional[str]).
        
        Args:
            annotation: The ast.annotation node from AnnAssign
            
        Returns:
            Type as string, or None if extraction fails
        """
        try:
            return ast.unparse(annotation)
        except Exception:
            return None
    
    def _resolve_annotation(self, annotation_str: str) -> str:
        """
        Resolve an annotation string to its FQN.
        
        Takes an annotation like "User" and resolves it to its full FQN
        like "sample_files.models.User" by looking it up in scope.
        
        For simple type names, uses scope lookup.
        For complex types like List[User], recursively resolves inner types.
        For builtins and already-qualified names, returns as-is.
        
        Args:
            annotation_str: The annotation string (e.g., "User", "List[User]")
            
        Returns:
            Resolved FQN or annotation string
        """
        # If it's a simple name (no dots, no brackets), try scope lookup
        if '.' not in annotation_str and '[' not in annotation_str:
            resolved = self.scope.lookup(annotation_str)
            if resolved:
                return resolved
            # If not in scope, return as-is (might be external type)
            return annotation_str
        
        # If it has brackets, it's a generic type like List[User] or Optional[User]
        # For now, return as-is - we can add recursive resolution later
        # TODO: Parse and resolve inner types (e.g., "List[User]" → "List[sample_files.models.User]")
        return annotation_str
    
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
            annotation_str = self._extract_type_from_annotation(node.annotation)
            if annotation_str:
                annotation_fqn = self._resolve_annotation(annotation_str)
                print(f"   Annotation: {var_name}: {annotation_str} → {annotation_fqn}")
        
        # Infer type from value if present
        inferred_type = None
        if hasattr(node, 'value') and node.value:
            inferred_type = self._infer_type(node.value)
            if inferred_type:
                print(f"   Inferred from value: {var_name} = {inferred_type}")
        
        # Determine which type to use in scope
        type_for_scope = None
        
        if annotation_fqn and inferred_type:
            # Both annotation and inferred type available - compare them
            if annotation_fqn != inferred_type:
                # Mismatch! Create violation
                from ...violations import IncorrectTypeAnnotation
                violation = IncorrectTypeAnnotation(self.node)
                # TODO: Attach violation to node (needs violation infrastructure)
                print(f"   VIOLATION: Annotation '{annotation_fqn}' doesn't match inferred '{inferred_type}' (line {node.lineno})")
            
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
            print(f"   Added to scope: {var_name} = {type_for_scope} (line {node.lineno})")
        else:
            print(f"   Could not determine type for: {var_name} (line {node.lineno})")
        
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
            print(f"   Import: {name} → {alias.name}")
        
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
            print(f"   ImportFrom: {name} → {fqn}")
        
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
        print(f"   ClassDef: {class_name} → {class_fqn}")
        
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
        print(f"   FunctionDef: {func_name} → {func_fqn}")
        
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
        print(f"   AsyncFunctionDef: {func_name} → {func_fqn}")