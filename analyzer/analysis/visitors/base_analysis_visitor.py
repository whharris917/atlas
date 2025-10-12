"""
Base Analysis Visitor - Shared functionality for all analysis visitors.

All analysis visitors (ModuleAnalysisVisitor, FunctionAnalysisVisitor, etc.)
inherit from this base class to access shared linearization functionality.
"""

import ast
from typing import List

from ..expression_traversal.operations import Operation, GetName, GetAttribute, CallFunction, GetSubscript


class BaseAnalysisVisitor(ast.NodeVisitor):
    """
    Base class for all analysis visitors providing shared functionality.
    
    All analysis visitors inherit from this class to access:
    - Expression linearization (converting nested AST to Linear Operation Queue)
    - Future shared utilities for type inference and analysis
    
    Subclasses should override visit_* methods for specific AST node types
    they need to analyze.
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
            >>> # Result: [GetName('user'), GetAttribute('profile'), GetAttribute('email')]
            
            >>> # Method call: user.validate()
            >>> ops = self.linearize(user_validate_ast)
            >>> # Result: [GetName('user'), GetAttribute('validate'), CallFunction()]
            
            >>> # Complex: admin_user.email.lower().strip()
            >>> ops = self.linearize(complex_ast)
            >>> # Result: [GetName('admin_user'), GetAttribute('email'), 
            >>>           GetAttribute('lower'), CallFunction(),
            >>>           GetAttribute('strip'), CallFunction()]
        """
        loq: List[Operation] = []
        
        # Basic dispatch based on expression type
        if isinstance(expr, ast.Name):
            # Variable/name access: x, user, count
            loq.append(GetName(expr.id))
        
        elif isinstance(expr, ast.Attribute):
            # Attribute access: obj.attr
            # Recursively linearize the value, then add attribute access
            loq.extend(self.linearize(expr.value))
            loq.append(GetAttribute(expr.attr))
        
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