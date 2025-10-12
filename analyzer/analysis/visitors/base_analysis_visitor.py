"""
Base Analysis Visitor - Shared functionality for all analysis visitors.

All analysis visitors (ModuleAnalysisVisitor, FunctionAnalysisVisitor, etc.)
inherit from this base class to access shared linearization and type inference.
"""

import ast
from typing import List, Optional

from ..expression_traversal.operations import Operation, GetName, Dot, CallFunction, GetSubscript


class BaseAnalysisVisitor(ast.NodeVisitor):
    """
    Base class for all analysis visitors providing shared functionality.
    
    All analysis visitors inherit from this class to access:
    - Expression linearization (converting nested AST to Linear Operation Queue)
    - Type inference from literals, expressions, and annotations
    - Future shared utilities for analysis
    
    Subclasses should override visit_* methods for specific AST node types
    they need to analyze, and must provide self.scope for type inference.
    """
    
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
        
        Subclasses must have self.scope attribute for variable lookups.
        
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
        if not hasattr(self, 'module_node'):
            return None
        
        project = self.module_node.get_project()
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
            Type name as string (e.g., "int", "str", "bool")
        """
        if isinstance(value, bool):
            # Must check bool before int (bool is subclass of int)
            return "bool"
        elif isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, str):
            return "str"
        elif value is None:
            return "NoneType"
        else:
            # Fallback for other literal types
            return type(value).__name__
    
    def _extract_type_from_annotation(self, annotation: ast.expr) -> Optional[str]:
        """
        Extract type string from an annotation node.
        
        Handles various annotation formats:
        - Simple names: int, str, bool
        - Subscripts: List[int], Dict[str, int]
        - Attributes: typing.Optional[str]
        
        Args:
            annotation: AST annotation node (from ast.AnnAssign.annotation)
            
        Returns:
            Type string extracted from annotation, or None if unparseable
        """
        try:
            # Use ast.unparse to convert annotation AST back to string
            return ast.unparse(annotation)
        except Exception:
            # If unparsing fails, return None
            return None