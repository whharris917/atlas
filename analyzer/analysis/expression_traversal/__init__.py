"""
Expression Traversal Package - Atlas Analysis Phase

Implements the unified Expression Traversal engine for resolving identities
and evaluating types of Python expressions, as defined in the Official Atlas
Project Glossary.

Core Components:
- TypeInferenceEngine: Main engine for expression traversal
- Operation classes: Represent steps in the Linear Operation Queue (LOQ)
"""

from .engine import TypeInferenceEngine
from .operations import (
    Operation,
    GetName,
    GetAttribute,
    CallFunction,
    GetSubscript,
)

__all__ = [
    'TypeInferenceEngine',
    'Operation',
    'GetName',
    'GetAttribute',
    'CallFunction',
    'GetSubscript',
]