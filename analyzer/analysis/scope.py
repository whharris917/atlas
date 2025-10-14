"""
Scope Infrastructure - Atlas Analysis Phase

Provides lexical scope management for tracking variable-to-type bindings
during expression analysis.

Classes:
- ScopeFrame: Single lexical level (simple dict wrapper)
- Scope: Stack of ScopeFrames with lookup traversal
"""

import builtins
from typing import Optional, Dict


class ScopeFrame:
    """
    A single lexical scope level.
    
    Simple wrapper around a dictionary mapping variable names to type FQNs.
    """
    
    def __init__(self):
        """Initialize an empty scope frame."""
        self._bindings: Dict[str, str] = {}
    
    def add(self, name: str, type_fqn: str) -> None:
        """
        Add a name-to-type binding in this frame.
        
        Args:
            name: Variable name
            type_fqn: Fully qualified name of the type
        """
        self._bindings[name] = type_fqn
    
    def get(self, name: str) -> Optional[str]:
        """
        Look up a name in this frame only.
        
        Args:
            name: Variable name to look up
            
        Returns:
            Type FQN if found, None otherwise
        """
        return self._bindings.get(name)


class Scope:
    """
    Stack of scope frames representing complete lexical visibility.
    
    Manages a stack of ScopeFrames, searching from innermost to outermost
    during lookup. Used by analysis visitors to track variable types.
    
    Lookup falls back to Python builtins if name not found in any frame.
    """
    
    def __init__(self):
        """Initialize with empty frame stack."""
        self._frames: list[ScopeFrame] = []
    
    def push_frame(self) -> None:
        """Push a new scope frame onto the stack."""
        self._frames.append(ScopeFrame())
    
    def pop_frame(self) -> None:
        """Pop the innermost scope frame from the stack."""
        if self._frames:
            self._frames.pop()
    
    def add(self, name: str, type_fqn: str) -> None:
        """
        Add a binding to the current (innermost) frame.
        
        Args:
            name: Variable name
            type_fqn: Fully qualified name of the type
        """
        if self._frames:
            self._frames[-1].add(name, type_fqn)
    
    def lookup(self, name: str) -> Optional[str]:
        """
        Look up a name by searching frames from innermost to outermost.
        
        Falls back to checking Python builtins if not found in any frame.
        Uses the builtins module to dynamically check for builtin names,
        avoiding the need for a hardcoded list.
        
        Args:
            name: Variable name to look up
            
        Returns:
            Type FQN if found in any frame or builtins, None otherwise
        """
        # Search from innermost (end of list) to outermost (start of list)
        for frame in reversed(self._frames):
            type_fqn = frame.get(name)
            if type_fqn is not None:
                return type_fqn
        
        # Fallback: check if it's a Python builtin
        if hasattr(builtins, name):
            return name  # Builtins return as-is (e.g., "int", "str")
        
        return None