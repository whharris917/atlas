"""
Analysis Phase Package - Atlas

Contains all analysis infrastructure including:
- Base note system for analysis artifacts
- Expression traversal engine for type inference
- Scope management for variable tracking
- Analysis visitors for AST traversal
"""

from .base_note import BaseNote
from .scope import Scope, ScopeFrame

__all__ = [
    'BaseNote',
    'Scope',
    'ScopeFrame',
]