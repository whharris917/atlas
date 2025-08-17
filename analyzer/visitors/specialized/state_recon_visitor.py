"""
State Reconnaissance Visitor - Code Atlas

Specialized visitor for processing module-level state variables and assignments.
Part of the Phase 2 refactoring to break down the monolithic ReconVisitor.
"""

import ast
from typing import Dict, List, Any, Optional
from ...utils.logger import AnalysisLogger
from ...utils.naming import generate_fqn


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
                    state_info = self._process_module_state_assignment(target, node.value)
                    processed_items[target.id] = state_info
        else:
            # Class level assignments - class attributes
            self.logger.log(f"[CLASS_ASSIGN] Processing class-level assignment in {self.current_class}", 3)
            for target in node.targets:
                if isinstance(target, ast.Name):
                    # Simple assignment: attr = value
                    attr_info = self._process_class_attribute_assignment(target.id, node.value)
                    if class_attr_callback:
                        class_attr_callback(target.id, attr_info)
                    processed_items[target.id] = attr_info
                    
                elif isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                    # Self assignment: self.attr = value
                    attr_info = self._process_class_attribute_assignment(target.attr, node.value)
                    if class_attr_callback:
                        class_attr_callback(target.attr, attr_info)
                    processed_items[target.attr] = attr_info
        
        return processed_items
    
    def process_ann_assign(self, node: ast.AnnAssign, class_attr_callback=None) -> Dict[str, Any]:
        """Process annotated assignments for class attributes and state variables."""
        processed_items = {}
        
        if self.current_class is None and isinstance(node.target, ast.Name):
            # Module level annotated assignment
            self.logger.log("[STATE_ANN_ASSIGN] Processing module-level annotated assignment", 3)
            state_info = self._process_module_ann_state_assignment(node)
            processed_items[node.target.id] = state_info
            
        elif self.current_class and isinstance(node.target, ast.Attribute):
            # Class level annotated assignment
            if isinstance(node.target.value, ast.Name) and node.target.value.id == "self":
                self.logger.log(f"[CLASS_ANN_ASSIGN] Processing class annotated assignment in {self.current_class}", 3)
                attr_info = self._process_class_ann_attribute_assignment(node)
                if class_attr_callback:
                    class_attr_callback(node.target.attr, attr_info)
                processed_items[node.target.attr] = attr_info
        
        return processed_items
    
    def _process_module_state_assignment(self, target: ast.Name, value: ast.AST) -> Dict[str, Any]:
        """Process module-level state variable assignment."""
        fqn = generate_fqn(self.module_name, None, target.id)
        inferred_type = self.type_inference.infer_from_assignment_value(value)
        
        state_info = {
            "type": inferred_type,
            "inferred_from_value": bool(inferred_type)
        }
        
        self.state[fqn] = state_info
        self.logger.log(f"[MODULE_STATE] {target.id}: {inferred_type or 'Unknown'}", 2)
        
        return state_info
    
    def _process_module_ann_state_assignment(self, node: ast.AnnAssign) -> Dict[str, Any]:
        """Process module-level annotated state variable assignment."""
        fqn = generate_fqn(self.module_name, None, node.target.id)
        
        # Try to get type from annotation first
        annotation_type = None
        if node.annotation:
            try:
                annotation_type = ast.unparse(node.annotation)
            except Exception as e:
                self.logger.log(f"[ANN_STATE] Error parsing annotation: {e}", 1)
        
        # Fallback to value inference if no annotation or parsing failed
        inferred_type = annotation_type
        if not inferred_type and node.value:
            inferred_type = self.type_inference.infer_from_assignment_value(node.value)
        
        state_info = {
            "type": inferred_type,
            "annotated": bool(annotation_type),
            "inferred_from_value": bool(not annotation_type and inferred_type)
        }
        
        self.state[fqn] = state_info
        self.logger.log(f"[MODULE_ANN_STATE] {node.target.id}: {inferred_type or 'Unknown'}", 2)
        
        return state_info
    
    def _process_class_attribute_assignment(self, attr_name: str, value: ast.AST) -> Dict[str, Any]:
        """Process class attribute assignment."""
        inferred_type = self.type_inference.infer_from_assignment_value(value)
        
        attr_info = {
            "type": inferred_type or "Unknown",
            "source": "assignment"
        }
        
        self.logger.log(f"[CLASS_ATTR] {attr_name}: {inferred_type or 'Unknown'}", 3)
        return attr_info
    
    def _process_class_ann_attribute_assignment(self, node: ast.AnnAssign) -> Dict[str, Any]:
        """Process class annotated attribute assignment."""
        # Try to get type from annotation first
        annotation_type = None
        if node.annotation:
            try:
                annotation_type = ast.unparse(node.annotation)
            except Exception as e:
                self.logger.log(f"[CLASS_ANN_ATTR] Error parsing annotation: {e}", 1)
        
        # Fallback to value inference if no annotation or parsing failed
        inferred_type = annotation_type
        if not inferred_type and node.value:
            inferred_type = self.type_inference.infer_from_assignment_value(node.value)
        
        attr_info = {
            "type": inferred_type or "Unknown",
            "source": "annotation" if annotation_type else "inferred",
            "annotated": bool(annotation_type)
        }
        
        self.logger.log(f"[CLASS_ANN_ATTR] {node.target.attr}: {inferred_type or 'Unknown'}", 3)
        return attr_info
    
    def get_state_data(self) -> Dict[str, Dict[str, Any]]:
        """Get collected state data."""
        return self.state.copy()
