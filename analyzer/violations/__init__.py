"""
Atlas Code Standard Violations Package

Diagnostic ornaments that hang off the project tree but are not part of its structure.
These classes represent quality issues discovered during analysis phases.
UPDATED: Includes renamed MissingArgumentTypeHint and new MissingReturnTypeHint.
"""

from .base import CodeStandardViolation
from .missing_argument_type_hint import MissingArgumentTypeHint
from .missing_return_type_hint import MissingReturnTypeHint

# Public API exports
__all__ = [
    'CodeStandardViolation',
    'MissingArgumentTypeHint',
    'MissingReturnTypeHint'
]