"""
Type Inference Engine - Atlas Analysis Phase

The core engine for traversing expressions and inferring types through
the Expression Traversal process defined in the Official Atlas Glossary.
"""

import ast
from typing import List, Optional

from .operations import Operation, GetName, GetAttribute, CallFunction, GetSubscript


class TypeInferenceEngine:
    """
    Core engine for expression traversal and type inference.
    
    This engine provides a single public method get_type() that determines
    the type of any Python expression by linearizing it into a Linear
    Operation Queue (LOQ) and evaluating it through Type Propagation.
    
    The engine is used by all analysis visitors (ModuleAnalysisVisitor,
    FunctionAnalysisVisitor, etc.) to determine types during AST traversal.
    
    Public API:
        get_type(expr, scope) -> Optional[str]
            Returns the type FQN for any expression
    """
    
    def __init__(self, project_node):
        """
        Initialize the type inference engine.
        
        Args:
            project_node: Root ProjectNode for resolving project-defined types
        """
        self.project = project_node
    
    def get_type(self, expr: ast.expr, scope) -> Optional[str]:
        """
        Get the type FQN of an expression.
        
        This is the main entry point for type inference. It linearizes the
        expression into a Linear Operation Queue, then evaluates it through
        Type Propagation to determine the resulting type.
        
        Args:
            expr: AST expression node to analyze
            scope: Current Scope for variable lookups
            
        Returns:
            Type FQN as string (e.g., "int", "str", "myproject.models.User")
            or None if type cannot be determined
            
        Example:
            >>> engine = TypeInferenceEngine(project)
            >>> type_fqn = engine.get_type(ast.parse("42").body[0].value, scope)
            >>> print(type_fqn)  # "int"
        """
        # Handle literals directly (no linearization needed)
        if isinstance(expr, ast.Constant):
            return self._infer_literal_type(expr.value)
        
        # Step 1: Linearize expression into operation queue
        loq = self._linearize(expr)
        
        # Step 2: Evaluate the queue to determine type
        return self._evaluate(loq, scope)
    
    def _linearize(self, expr: ast.expr) -> List[Operation]:
        """
        Convert a nested expression into a Linear Operation Queue.
        
        This is the first step of Expression Traversal. The LOQ provides
        a sequential representation of the operations within the expression,
        which can then be processed left-to-right with Type Propagation.
        
        Example:
            Expression: user.profile.get_status()
            LOQ: [GetName('user'), GetAttribute('profile'), 
                  GetAttribute('get_status'), CallFunction()]
        
        Args:
            expr: An ast.expr node representing the expression to linearize
            
        Returns:
            List of Operation objects representing the sequential steps
        """
        loq: List[Operation] = []
        
        # Basic dispatch based on expression type
        if isinstance(expr, ast.Name):
            loq.append(GetName(expr.id))
        
        elif isinstance(expr, ast.Attribute):
            # Recursively linearize the value, then add attribute access
            loq.extend(self._linearize(expr.value))
            loq.append(GetAttribute(expr.attr))
        
        elif isinstance(expr, ast.Call):
            # Recursively linearize the function being called, then add call
            loq.extend(self._linearize(expr.func))
            loq.append(CallFunction())
        
        elif isinstance(expr, ast.Subscript):
            # Recursively linearize the value being subscripted, then add subscript
            loq.extend(self._linearize(expr.value))
            loq.append(GetSubscript())
        
        else:
            # Other expression types will be added incrementally
            # For now, we handle the core cases: Name, Attribute, Call, Subscript
            pass
        
        return loq
    
    def _evaluate(self, loq: List[Operation], scope) -> Optional[str]:
        """
        Evaluate a Linear Operation Queue to determine the resulting type.
        
        This method performs Type Propagation: processing each operation
        in sequence, where the result of one operation becomes the input
        for the next.
        
        Args:
            loq: Linear Operation Queue from _linearize()
            scope: Current Scope for variable lookups
            
        Returns:
            Type FQN as string, or None if type cannot be determined
        """
        # Empty LOQ - cannot determine type
        if not loq:
            return None
        
        # TODO: Implement full Type Propagation through LOQ
        # For now, just handle simple variable lookup
        
        # If LOQ has exactly one GetName operation, look up in scope
        if len(loq) == 1 and isinstance(loq[0], GetName):
            return scope.lookup(loq[0].name)
        
        # More complex expressions not yet implemented
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