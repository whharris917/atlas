"""
Resolution Operations - The Quantum of Analysis

Defines the simple, semantic operations that a complex expression is broken
down into. This is a core component of the Unified Resolution Dispatcher.
"""

import ast
from dataclasses import dataclass
from typing import List, Any

@dataclass
class ResolutionOperation:
    """Base class for a semantic operation in a resolution chain."""
    pass

@dataclass
class AttributeOperation(ResolutionOperation):
    """Represents an attribute access (e.g., .foo)."""
    name: str

    def __repr__(self):
        return f"Attribute(name='{self.name}')"

@dataclass
class CallOperation(ResolutionOperation):
    """Represents a function or method call (e.g., ())."""
    args: List[ast.expr]
    keywords: List[ast.keyword]

    def __repr__(self):
        return f"Call(args={len(self.args)}, keywords={len(self.keywords)})"

@dataclass
class SubscriptOperation(ResolutionOperation):
    """Represents a subscript access (e.g., [key])."""
    key_node: ast.AST

    def __repr__(self):
        return f"Subscript(key_node={type(self.key_node).__name__})"
