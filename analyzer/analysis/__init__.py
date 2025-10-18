"""
Analysis Phase Package - Atlas

Contains all analysis infrastructure including:
- Base note system for analysis artifacts
- Type inference engine for type analysis
- Scope management for variable tracking
- Analysis visitors for AST traversal
"""

from .base_note import BaseNote
from .scope import Scope, ScopeFrame
from .type_inference import TypeInferenceEngine

__all__ = [
    'BaseNote',
    'Scope',
    'ScopeFrame',
    'TypeInferenceEngine',
]