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
    - Type inference from literals and expressions
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
            expr: An ast.expr node representing the expression to linearize
            
        Returns:
            List of Operation objects representing the sequential steps
            
        Examples:
            >>> # Simple: user
            >>> ops = self.linearize(user_ast)
            >>> # Result: [GetName('user')]
            
            >>> # Chained: user.profile.email
            >>> ops = self.linearize(user_profile_email_ast)
            >>> # Result: [GetName('user'), Dot('profile'), Dot('email')]
            
            >>> # Method call: user.validate()
            >>> ops = self.linearize(user_validate_ast)
            >>> # Result: [GetName('user'), Dot('validate'), CallFunction()]
        """
        loq: List[Operation] = []
        
        # Basic dispatch based on expression type
        if isinstance(expr, ast.Name):
            # Variable/name access: x, user, count
            loq.append(GetName(expr.id))
        
        elif isinstance(expr, ast.Attribute):
            # Attribute access: obj.attr
            # Recursively linearize the value, then add dot operation
            loq.extend(self.linearize(expr.value))
            loq.append(Dot(expr.attr))
        
        elif isinstance(expr, ast.Call):
            # Function/method call: func() or obj.method()
            # Recursively linearize the function being called, then add call
            loq.extend(self.linearize(expr.func))
            loq.append(CallFunction())
        
        elif isinstance(expr, ast.Subscript):
            # Subscript access: obj[key] or list[0]
            # Recursively linearize the value being subscripted, then add subscript
            loq.extend(self.linearize(expr.value))
            loq.append(GetSubscript())
        
        else:
            # Other expression types will be added incrementally
            # For now, we handle the core cases: Name, Attribute, Call, Subscript
            # Unhandled expressions result in empty LOQ
            pass
        
        return loq
    
    def _infer_type(self, expr: ast.expr) -> Optional[str]:
        """
        Infer the type of an expression.
        
        This method handles:
        - Literals (int, str, bool, float, None)
        - Variable lookups (from scope)
        - Future: complex expressions via LOQ navigation
        
        Subclasses must have self.scope attribute for variable lookups.
        
        Args:
            expr: AST expression node
            
        Returns:
            Type FQN as string, or None if type cannot be determined
        """
        # Handle literals directly
        if isinstance(expr, ast.Constant):
            return self._infer_literal_type(expr.value)
        
        # Handle variables and complex expressions via linearization
        loq = self.linearize(expr)
        
        # For now, only handle simple variable lookup
        if len(loq) == 1 and isinstance(loq[0], GetName):
            return self.scope.lookup(loq[0].name)
        
        # Complex expressions not yet implemented
        return None
    
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