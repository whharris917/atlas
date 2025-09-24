"""
Atlas Code Standard Violations Package

Diagnostic ornaments that hang off the project tree but are not part of its structure.
These classes represent quality issues discovered during analysis phases.
"""

from .base import CodeStandardViolation
from .missing_type_hint import MissingTypeHint

# Public API exports
__all__ = [
    'CodeStandardViolation',
    'MissingTypeHint'
]