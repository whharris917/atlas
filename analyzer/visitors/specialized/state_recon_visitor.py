"""
State Reconnaissance Visitor - Code Atlas

Specialized visitor for processing module-level state variables and assignments.
Part of the Phase 2 refactoring to break down the monolithic ReconVisitor.

EMERGENCY FIX: Added missing extraction logic to match original implementation.
"""

import ast
from typing import Dict, List, Any, Optional
from ...utils_new.logger import AnalysisLogger
from ...utils_new.naming import generate_fqn


class StateReconVisitor:
    """Specialized visitor for state variable processing during reconnaissance pass."""
    
    def __init__(self, module_name: str, logger: AnalysisLogger, type_inference_engine):
        self.module_name = module_name
        self.logger = logger
        self.type_inference = type_inference_engine
        
        # State tracking
        self.state = {}
        
        # Context tracking
        self.current_class = None
    
    def set_class_context(self, class_fqn: Optional[str]):
        """Set current class context."""
        self.current_class = class_fqn
    
    def process_assign(self, node: ast.Assign, class_attr_callback=None) -> Dict[str, Any]:
        """Process assignments for state variables and class attributes."""
        processed_items = {}
        
        if self.current_class is None:
            # Module level assignments - state variables
            self.logger.log("[STATE_ASSIGN] Processing module-level assignment", 3)
            for target in node.targets:
                if isinstance(target, ast.Name):
                    # FIXED: Use the same logic as original implementation
                    fqn = f"{self.module_name}.{target.id}"
                    inferred_type = self.type_inference.infer_from_assignment_value(node.value)
                    state_info = {
                        "type": inferred_type,
                        "inferred_from_value": bool(inferred_type)
                    }
                    self.state[fqn] = state_info
                    processed_items[target.id] = state_info
                    self.logger.log(f"[MODULE_STATE] {target.id}: {inferred_type or 'Unknown'}", 2)
        else:
            # Class level assignments - class attributes
            self.logger.log(f"[CLASS_ASSIGN] Processing class-level assignment in {self.current_class}", 3)
            for target in node.targets:
                if isinstance(target, ast.Name):
                    # FIXED: Simple assignment: attr = value (like enum values)
                    inferred_type = self.type_inference.infer_from_assignment_value(node.value)
                    attr_info = {
                        "type": inferred_type or "Unknown"
                    }
                    if class_attr_callback:
                        class_attr_callback(target.id, attr_info)
                    processed_items[target.id] = attr_info
                    self.logger.log(f"[CLASS_ATTR] {target.id}: {inferred_type or 'Unknown'}", 3)
                    
                elif isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                    # FIXED: Self assignment: self.attr = value
                    inferred_type = self.type_inference.infer_from_assignment_value(node.value)
                    attr_info = {
                        "type": inferred_type or "Unknown"
                    }
                    if class_attr_callback:
                        class_attr_callback(target.attr, attr_info)
                    processed_items[target.attr] = attr_info
                    self.logger.log(f"[CLASS_SELF_ATTR] {target.attr}: {inferred_type or 'Unknown'}", 3)
        
        return processed_items
    
    def process_ann_assign(self, node: ast.AnnAssign, class_attr_callback=None) -> Dict[str, Any]:
        """Process annotated assignments for class attributes and state variables."""
        processed_items = {}
        
        if self.current_class is None and isinstance(node.target, ast.Name):
            # FIXED: Module level annotated assignment - exact original logic
            fqn = f"{self.module_name}.{node.target.id}"
            type_annotation = None
            if node.annotation:
                try:
                    type_annotation = ast.unparse(node.annotation)
                except Exception:
                    pass
            
            state_info = {
                "type": type_annotation,
                "inferred_from_value": False
            }
            self.state[fqn] = state_info
            processed_items[node.target.id] = state_info
            self.logger.log(f"[MODULE_ANN_STATE] {node.target.id}: {type_annotation or 'Unknown'}", 2)
            
        elif self.current_class is not None:
            # FIXED: Class level annotated assignment - exact original logic
            if isinstance(node.target, ast.Name):
                # Direct assignment: attr: Type = value
                type_annotation = None
                if node.annotation:
                    try:
                        type_annotation = ast.unparse(node.annotation)
                    except Exception:
                        pass
                
                attr_info = {
                    "type": type_annotation or "Unknown"
                }
                if class_attr_callback:
                    class_attr_callback(node.target.id, attr_info)
                processed_items[node.target.id] = attr_info
                self.logger.log(f"[CLASS_ANN_ATTR] {node.target.id}: {type_annotation or 'Unknown'}", 3)
                
            elif isinstance(node.target, ast.Attribute) and isinstance(node.target.value, ast.Name) and node.target.value.id == "self":
                # Self assignment: self.attr: Type = value
                type_annotation = None
                if node.annotation:
                    try:
                        type_annotation = ast.unparse(node.annotation)
                    except Exception:
                        pass
                
                attr_info = {
                    "type": type_annotation or "Unknown"
                }
                if class_attr_callback:
                    class_attr_callback(node.target.attr, attr_info)
                processed_items[node.target.attr] = attr_info
                self.logger.log(f"[CLASS_SELF_ANN_ATTR] {node.target.attr}: {type_annotation or 'Unknown'}", 3)
        
        return processed_items
    
    def get_state_data(self) -> Dict[str, Dict[str, Any]]:
        """Get collected state data."""
        return self.state.copy()
