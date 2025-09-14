"""
Defines the ScopeManager and ScopeFrame for lexical scope tracking.

This module provides the necessary classes to model lexical scoping during
the analysis of Python code. The ScopeManager maintains a stack of
ScopeFrames, corresponding to the nested structure of function and class
definitions. This allows the analysis engine to correctly resolve local
variable names according to Python's scoping rules.
"""

from typing import List, Dict, Optional
from .logger import get_logger

logger = get_logger()

class ScopeFrame:
    """
    Represents a single lexical scope, such as a function body.

    It holds a simple dictionary that maps local variable names declared
    within this scope to their determined type FQNs.
    """
    def __init__(self):
        self.variables: Dict[str, str] = {}

class ScopeManager:
    """
    Manages the stack of lexical scopes during AST traversal.

    As the analyzer enters nested functions or classes, it pushes a new
    ScopeFrame onto the stack. When it exits, it pops the frame. This

    ensures that variable lookups correctly follow lexical scoping rules.
    """
    def __init__(self):
        self.scope_stack: List[ScopeFrame] = []

    def push_scope(self):
        """
        Enters a new lexical scope by pushing a new ScopeFrame onto the stack.
        """
        self.scope_stack.append(ScopeFrame())
        logger.debug(f"Entered new scope. Scope depth is now {len(self.scope_stack)}.")

    def pop_scope(self):
        """
        Exits the current lexical scope by popping the top ScopeFrame.
        """
        if self.scope_stack:
            self.scope_stack.pop()
            logger.debug(f"Exited scope. Scope depth is now {len(self.scope_stack)}.")
        else:
            logger.warning("Attempted to pop from an empty scope stack.")

    def add_variable_type(self, name: str, type_fqn: str):
        """
        Adds or updates a variable's type in the current, top-most scope.

        This is the primary method for MUTATING the scope state, used by
        analyzers like the AssignmentAnalyzer.

        Args:
            name: The string name of the variable.
            type_fqn: The FQN of the variable's type.
        """
        if self.scope_stack:
            self.scope_stack[-1].variables[name] = type_fqn
            logger.debug(f"Variable '{name}' of type '{type_fqn}' added to current scope.")
        else:
            logger.warning("Attempted to add a variable with no active scope.")

    def lookup_variable_type(self, name: str) -> Optional[str]:
        """
        Looks up a variable's type, searching from the innermost to outermost scope.

        This correctly models how Python's lexical scoping works.

        Args:
            name: The string name of the variable to look up.

        Returns:
            The FQN of the variable's type, or None if not found in any scope.
        """
        # Iterate backwards through the stack to go from innermost to outermost scope
        for frame in reversed(self.scope_stack):
            if name in frame.variables:
                return frame.variables[name]
        return None
