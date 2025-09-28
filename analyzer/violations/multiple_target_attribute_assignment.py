"""
Multiple Target Attribute Assignment Violation - Atlas Rewrite

Code standard violation for attribute assignments with multiple targets.
Created by ClassReconnaissanceVisitor when encountering complex assignment patterns.
"""

from typing import List
from .base import CodeStandardViolation


class MultipleTargetAttributeAssignmentViolation(CodeStandardViolation):
    """
    Code standard violation for attribute assignments with multiple targets.
    
    This violation flags assignment statements that have multiple targets,
    which are not supported for attribute node creation. Such assignments
    should be split into separate statements for clarity.
    
    Examples that trigger this violation:
    Class-level: class_var1 = class_var2 = "value"
    Instance-level: self.attr1 = self.attr2 = value
    Mixed: self.name = other.name = "value"
    
    Recommended fix:
    Split into separate assignments:
    - class_var1 = "value"
    - class_var2 = "value"
    
    Or:
    - self.attr1 = value
    - self.attr2 = value
    """
    
    def __init__(self, parent, target_names: List[str], assignment_context: str):
        """
        Initialize violation ornament.
        
        Args:
            parent: The ClassNode where the violation was detected
            target_names: List of target names in the multi-target assignment
            assignment_context: Context description ("class-level" or "instance-level")
        """
        targets_str = ", ".join(target_names)
        
        message = (
            f"Multiple target {assignment_context} attribute assignment detected: {targets_str}. "
            f"Split into separate assignments for clarity and proper attribute node creation."
        )
        
        suggestion = f"Split into separate assignments: " + "; ".join(f"{name} = <value>" for name in target_names)
        
        super().__init__(
            parent=parent,
            violation_type="multiple_target_attribute_assignment",
            message=message,
            suggestion=suggestion
        )
        
        self.target_names = target_names
        self.assignment_context = assignment_context