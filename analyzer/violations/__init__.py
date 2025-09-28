"""
Atlas Code Standard Violations Package

Diagnostic ornaments that hang off the project tree but are not part of its structure.
These classes represent quality issues discovered during analysis phases.
UPDATED: Includes new attribute type hint violations and multi-target assignment violation.
"""

from .base import CodeStandardViolation
from .missing_argument_type_hint import MissingArgumentTypeHint
from .missing_return_type_hint import MissingReturnTypeHint
from .missing_class_attribute_type_hint import MissingClassAttributeTypeHintViolation
from .missing_instance_attribute_type_hint import MissingInstanceAttributeTypeHintViolation
from .multiple_target_attribute_assignment import MultipleTargetAttributeAssignmentViolation

# Public API exports
__all__ = [
    'CodeStandardViolation',
    'MissingArgumentTypeHint',
    'MissingReturnTypeHint',
    'MissingClassAttributeTypeHintViolation',
    'MissingInstanceAttributeTypeHintViolation',
    'MultipleTargetAttributeAssignmentViolation'
]