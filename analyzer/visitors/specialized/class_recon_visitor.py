"""
Class Reconnaissance Visitor - Code Atlas

Specialized visitor for processing class definitions with inheritance tracking.
Part of the Phase 2 refactoring to break down the monolithic ReconVisitor.

EMERGENCY FIX: Fixed class context management and attribute finalization to match original implementation.
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
        
        # Context stack for nested classes
        self.class_stack = []
    
    def process_class_def(self, node: ast.ClassDef) -> Dict[str, Any]:
        """Process class definitions with inheritance capture and attribute cataloging."""
        class_fqn = generate_class_fqn(self.module_name, node.name)
        self.logger.log(f"[CLASS_RECON] Processing class: {node.name}", 2)
        
        # Capture inheritance information
        parent_classes = self._extract_inheritance(node)
        
        # FIXED: Don't initialize attributes here, let enter_class_context handle it
        # The class body will be processed by other visitors
        # We just return the structure here
        class_info = {
            "fqn": class_fqn,
            "parents": parent_classes,
            "attributes": {}  # Will be filled later
        }
        
        # FIXED: Store class reference for later finalization
        self.classes.append(class_info)
        self.logger.log(f"[CLASS_RECON] Stored class: {class_fqn} with {len(parent_classes)} parents", 2)
        
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
            self.logger.log(f"[CLASS_ATTR] Added attribute {name} to {self.current_class}: {type_info}", 3)
    
    def enter_class_context(self, class_fqn: str):
        """Enter class processing context."""
        # FIXED: Push current context to stack for nested class support
        self.class_stack.append((self.current_class, self.current_class_attributes))
        
        self.current_class = class_fqn
        self.current_class_attributes = {}
        self.logger.log(f"[CLASS_CONTEXT] Entered class: {class_fqn}", 3)
    
    def exit_class_context(self):
        """Exit class processing context and finalize attributes."""
        if self.current_class:
            self.logger.log(f"[CLASS_CONTEXT] Exiting class: {self.current_class}", 3)
            
            # FIXED: Finalize attributes for the current class
            self._finalize_class_attributes()
            
            # FIXED: Restore previous context from stack
            if self.class_stack:
                self.current_class, self.current_class_attributes = self.class_stack.pop()
            else:
                self.current_class = None
                self.current_class_attributes = {}
    
    def _finalize_class_attributes(self):
        """Finalize attributes for the current class."""
        if not self.current_class:
            return
        
        # FIXED: Find the class info and update its attributes
        for class_info in self.classes:
            if class_info["fqn"] == self.current_class:
                class_info["attributes"] = self.current_class_attributes.copy()
                self.logger.log(f"[CLASS_FINALIZE] Updated {self.current_class} with {len(self.current_class_attributes)} attributes", 2)
                break
    
    def get_classes_data(self) -> List[Dict[str, Any]]:
        """Get collected class data."""
        return self.classes.copy()
