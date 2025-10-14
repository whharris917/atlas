"""
Base Analysis Visitor - Shared functionality for all analysis visitors.

All analysis visitors (ModuleAnalysisVisitor, FunctionAnalysisVisitor, etc.)
inherit from this base class to access shared linearization and type inference.
"""

import ast
from typing import List, Optional

from ..expression_traversal.operations import Operation, GetName, Dot, CallFunction, GetSubscript
from ..scope import Scope


class BaseAnalysisVisitor(ast.NodeVisitor):
    """
    Base class for all analysis visitors providing shared functionality.
    
    All analysis visitors inherit from this class to access:
    - Expression linearization (converting nested AST to Linear Operation Queue)
    - Type inference from literals, expressions, and annotations
    - Scope management for variable type tracking
    - Scope population (imports, classes, functions)
    - Future shared utilities for analysis
    
    Subclasses should call super().__init__(node) to initialize the base visitor,
    where node is the specific node being analyzed (ModuleNode, FunctionNode, etc.).
    """
    
    def __init__(self, node):
        """
        Initialize base visitor with the node being analyzed.
        
        All analysis visitors need access to their node to navigate to the
        project for FQN resolution during type inference.
        
        Args:
            node: The tree node being analyzed (ModuleNode, FunctionNode, ClassNode, etc.)
        """
        self.node = node
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
        
        Args:
            expr: AST expression node (Name, Attribute, Call, Subscript)
            
        Returns:
            List of Operation objects representing the expression in sequence
            
        Example:
            user.profile.email → [GetName('user'), Dot('profile'), Dot('email')]
            obj.method() → [GetName('obj'), Dot('method'), CallFunction()]
        """
        operations = []
        
        def traverse(node):
            """Recursively traverse AST node to build operation queue."""
            if isinstance(node, ast.Name):
                operations.append(GetName(node.id))
            
            elif isinstance(node, ast.Attribute):
                traverse(node.value)
                operations.append(Dot(node.attr))
            
            elif isinstance(node, ast.Call):
                traverse(node.func)
                operations.append(CallFunction())
            
            elif isinstance(node, ast.Subscript):
                traverse(node.value)
                operations.append(GetSubscript())
        
        traverse(expr)
        return operations
    
    def _infer_type(self, expr: ast.expr) -> Optional[str]:
        """
        Infer the type of an expression using direct tree navigation.
        
        This method handles:
        - Literals (int, str, bool, float, None)
        - Variable lookups (from scope)
        - Attribute access chains (user.profile.email)
        - Method calls (obj.method())
        - Subscript operations (list[0])
        
        Uses the tree navigation approach: linearize the expression into
        operations, then navigate the tree directly using .dot() rather
        than interpreting operations.
        
        Args:
            expr: AST expression node
            
        Returns:
            Type FQN as string, or None if type cannot be determined
        """
        # Handle literals directly
        if isinstance(expr, ast.Constant):
            return self._infer_literal_type(expr.value)
        
        # Linearize expression into operations
        loq = self.linearize(expr)
        
        # Start by resolving the initial GetName operation
        if not loq or not isinstance(loq[0], GetName):
            return None
        
        # Look up the base variable in scope
        current_type = self.scope.lookup(loq[0].name)
        if not current_type:
            return None
        
        # If just a simple variable, we're done
        if len(loq) == 1:
            return current_type
        
        # For complex expressions, we need to navigate the tree
        # Get the project to find nodes by FQN
        project = self.node.get_project()
        current_node = project.get_node_by_fqn(current_type)
        
        if not current_node:
            # Type exists in scope but node not found (likely builtin)
            return current_type
        
        # Process each operation by navigating the tree
        for op in loq[1:]:
            if isinstance(op, Dot):
                # Navigate to the named child
                current_node = current_node.dot(op.attr_name)
                if not current_node:
                    return None
                
                # Update current type to this node's FQN
                current_type = current_node.fqn
            
            elif isinstance(op, CallFunction):
                # Navigate to the return node, then to its type
                return_node = current_node.dot("return")
                if not return_node:
                    return None
                
                type_node = return_node.dot("type")
                if not type_node:
                    return None
                
                # Extract the type from the TypeNode
                current_type = ast.unparse(type_node.source_data)
                
                # Try to resolve the type to a node for further navigation
                current_node = project.get_node_by_fqn(current_type)
                if not current_node:
                    # Type is a string but no node exists (builtin or external)
                    # Can't navigate further, but we have the type
                    return current_type
            
            elif isinstance(op, GetSubscript):
                # Subscript operation - for now, we can't infer the element type
                # This requires more sophisticated type tracking
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
    # Scope Population Methods - Inherited by All Visitors
    # ========================================================================
    
    def visit_Import(self, node: ast.Import):
        """
        Visit import statements: import json, import os.path
        
        Adds imported names to scope. For simple imports like 'import json',
        the name 'json' maps to 'json'. For 'import os.path', the name 'os'
        maps to 'os'.
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
        
        Adds class name to scope with its FQN.
        Does not traverse into class body - subclasses can override for deeper analysis.
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
        
        Adds function name to scope with its FQN.
        Does not traverse into function body - subclasses can override for deeper analysis.
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
        
        Adds function name to scope with its FQN.
        """
        func_name = node.name
        
        # Build FQN: parent_fqn.func_name
        func_fqn = f"{self.node.fqn}.{func_name}"
        
        self.scope.add(func_name, func_fqn)
        print(f"   AsyncFunctionDef: {func_name} → {func_fqn}")