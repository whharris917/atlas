"""
Class Reconnaissance Visitor - Code Atlas

Specialized visitor for processing class definitions with inheritance tracking.
Part of the Phase 2 refactoring to break down the monolithic ReconVisitor.
"""

import ast
from typing import Dict, List, Any, Optional
from ...utils.logger import AnalysisLogger
from ...utils.naming import generate_class_fqn


class ClassReconVisitor:
    """Specialized visitor for class definition processing during reconnaissance pass."""
    
    def __init__(self, module_name: str, logger: AnalysisLogger):
        self.module_name = module_name
        self.logger = logger
        
        # Class tracking
        self.classes = []
        self.current_class = None
        self.current_class_attributes = {}
    
    def process_class_def(self, node: ast.ClassDef) -> Dict[str, Any]:
        """Process class definitions with inheritance capture and attribute cataloging."""
        class_fqn = generate_class_fqn(self.module_name, node.name)
        self.logger.log(f"[CLASS_RECON] Processing class: {node.name}", 2)
        
        # Capture inheritance information
        parent_classes = self._extract_inheritance(node)
        
        # Initialize attribute tracking for this class
        old_class = self.current_class
        old_attributes = self.current_class_attributes
        self.current_class = class_fqn
        self.current_class_attributes = {}
        
        try:
            # The class body will be processed by other visitors
            # We just set up the structure here
            pass
        finally:
            # Store class with inheritance info and attributes
            class_info = {
                "fqn": class_fqn,
                "parents": parent_classes,
                "attributes": self.current_class_attributes.copy()
            }
            
            self.classes.append(class_info)
            self.logger.log(f"[CLASS_RECON] Stored class: {class_fqn} with {len(parent_classes)} parents", 2)
            
            # Restore previous context
            self.current_class = old_class
            self.current_class_attributes = old_attributes
        
        return class_info
    
    def _extract_inheritance(self, node: ast.ClassDef) -> List[str]:
        """Extract inheritance information from class definition."""
        parent_classes = []
        
        for base in node.bases:
            try:
                if isinstance(base, ast.Name):
                    # Simple inheritance: class Child(Parent)
                    parent_classes.append(base.id)
                    self.logger.log(f"[INHERITANCE] Simple parent: {base.id}", 3)
                    
                elif isinstance(base, ast.Attribute):
                    # Module inheritance: class Child(module.Parent)
                    base_parts = self._extract_attribute_chain(base)
                    if base_parts:
                        parent_name = ".".join(base_parts)
                        parent_classes.append(parent_name)
                        self.logger.log(f"[INHERITANCE] Module parent: {parent_name}", 3)
                        
            except Exception as e:
                self.logger.log(f"[INHERITANCE] Error processing base class: {e}", 1)
        
        return parent_classes
    
    def _extract_attribute_chain(self, node: ast.Attribute) -> List[str]:
        """Extract attribute chain from ast.Attribute node."""
        base_parts = []
        current = node
        
        while isinstance(current, ast.Attribute):
            base_parts.insert(0, current.attr)
            current = current.value
            
        if isinstance(current, ast.Name):
            base_parts.insert(0, current.id)
            
        return base_parts
    
    def add_class_attribute(self, name: str, type_info: Dict[str, Any]):
        """Add attribute to current class."""
        if self.current_class:
            self.current_class_attributes[name] = type_info
            self.logger.log(f"[CLASS_ATTR] Added attribute {name} to {self.current_class}", 3)
    
    def enter_class_context(self, class_fqn: str):
        """Enter class processing context."""
        self.current_class = class_fqn
        self.current_class_attributes = {}
        self.logger.log(f"[CLASS_CONTEXT] Entered class: {class_fqn}", 3)
    
    def exit_class_context(self):
        """Exit class processing context."""
        if self.current_class:
            self.logger.log(f"[CLASS_CONTEXT] Exited class: {self.current_class}", 3)
        self.current_class = None
        self.current_class_attributes = {}
    
    def get_classes_data(self) -> List[Dict[str, Any]]:
        """Get collected class data."""
        return self.classes.copy()
