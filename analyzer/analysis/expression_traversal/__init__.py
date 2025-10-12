"""
Expression Traversal Package - Atlas Analysis Phase

Implements the unified Expression Traversal engine for resolving identities
and evaluating types of Python expressions, as defined in the Official Atlas
Project Glossary.

Core Components:
- Operation classes: Represent steps in the Linear Operation Queue (LOQ)
"""

from .operations import (
    Operation,
    GetName,
    Dot,
    CallFunction,
    GetSubscript,
)

__all__ = [
    'Operation',
    'GetName',
    'Dot',
    'CallFunction',
    'GetSubscript',
]