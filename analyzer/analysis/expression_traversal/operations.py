"""
Expression Operations - Atlas Analysis Phase

Defines the operations that constitute a Linear Operation Queue (LOQ).
Each operation represents a single step in traversing an expression.
"""

from abc import ABC, abstractmethod
from typing import Any


class Operation(ABC):
    """
    Base class for all operations in a Linear Operation Queue.
    
    An operation represents a single step in evaluating an expression,
    such as accessing a name, getting an attribute, or calling a function.
    """
    
    @abstractmethod
    def __repr__(self) -> str:
        """Return string representation for debugging."""
        pass


class GetName(Operation):
    """
    Operation representing access to a variable name.
    
    Example: In the expression `x.y()`, `x` is a GetName operation.
    """
    
    def __init__(self, name: str):
        """
        Initialize GetName operation.
        
        Args:
            name: The variable name being accessed
        """
        self.name = name
    
    def __repr__(self) -> str:
        return f"GetName('{self.name}')"


class Dot(Operation):
    """
    Operation representing dot access (attribute/method access).
    
    Example: In the expression `x.y()`, accessing `y` is a Dot operation.
    
    This operation corresponds directly to the .dot() navigation method
    on tree nodes, representing the fundamental operation of navigating
    from one node to a named child.
    """
    
    def __init__(self, attr_name: str):
        """
        Initialize Dot operation.
        
        Args:
            attr_name: The attribute/method name being accessed via dot notation
        """
        self.attr_name = attr_name
    
    def __repr__(self) -> str:
        return f"Dot('{self.attr_name}')"


class CallFunction(Operation):
    """
    Operation representing a function or method call.
    
    Example: In the expression `x.y()`, the `()` after `y` is a CallFunction operation.
    
    Note: We don't track arguments - only that a call occurred. For type inference,
    we only need to know the return type of the called function/method.
    """
    
    def __init__(self):
        """Initialize CallFunction operation."""
        pass
    
    def __repr__(self) -> str:
        return "CallFunction()"


class GetSubscript(Operation):
    """
    Operation representing subscript access (indexing).
    
    Examples:
        - list[0] - List indexing
        - dict["key"] - Dictionary key access
        - matrix[i][j] - Multi-dimensional indexing
    
    Note: We don't track the actual index/key value - only that a subscript
    access occurred. For type inference, we need to determine the element type
    of the container being subscripted.
    """
    
    def __init__(self):
        """Initialize GetSubscript operation."""
        pass
    
    def __repr__(self) -> str:
        return "GetSubscript()"