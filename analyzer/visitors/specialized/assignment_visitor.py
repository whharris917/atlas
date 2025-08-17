"""
Assignment Visitor - Code Atlas

Specialized visitor for variable assignment tracking and symbol table updates.
"""

import ast
from typing import Dict, List, Any, Optional


class AssignmentVisitor:
    """Specialized visitor for assignment analysis and symbol table management."""
    
    def __init__(self, name_resolver, type_inference, symbol_manager, 
                 current_function_report, module_report, logger):
        self.name_resolver = name_resolver
        self.type_inference = type_inference
        self.symbol_manager = symbol_manager
        self.current_function_report = current_function_report
        self.module_report = module_report
        self.logger = logger
    
    def process_assign(self, node: ast.Assign, context: Dict[str, Any], 
                      current_class: Optional[str] = None) -> None:
        """Process assignments for both module state and local variables."""
        if not current_class and not self.current_function_report:
            # Module-level state
            self._process_module_state_assign(node)
        elif self.current_function_report:
            # Function-level assignments - update symbol table
            self._process_function_assign(node, context)
    
    def process_ann_assign(self, node: ast.AnnAssign, context: Dict[str, Any],
                          current_class: Optional[str] = None) -> None:
        """Process annotated assignments."""
        if (not current_class and not self.current_function_report and
            isinstance(node.target, ast.Name)):
            # Module-level annotated assignment
            self._process_module_state_ann_assign(node)
        elif self.current_function_report and isinstance(node.target, ast.Name):
            # Function-level annotated assignment
            self._process_function_ann_assign(node, context)
    
    def _process_module_state_assign(self, node: ast.Assign) -> None:
        """Process module-level assignments for state tracking."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                try:
                    state_entry = {
                        "name": target.id,
                        "value": ast.unparse(node.value) if node.value else "None"
                    }
                    self.module_report["module_state"].append(state_entry)
                    self.logger.log(f"[MODULE_STATE] {target.id} = {state_entry['value']}", 2)
                except Exception:
                    pass
    
    def _process_module_state_ann_assign(self, node: ast.AnnAssign) -> None:
        """Process module-level annotated assignments for state tracking."""
        try:
            state_entry = {
                "name": node.target.id,
                "value": ast.unparse(node.value) if node.value else "None"
            }
            self.module_report["module_state"].append(state_entry)
            annotation_str = ast.unparse(node.annotation) if node.annotation else 'Unknown'
            self.logger.log(f"[MODULE_STATE] {node.target.id} : {annotation_str} = {state_entry['value']}", 2)
        except Exception:
            pass
    
    def _process_function_assign(self, node: ast.Assign, context: Dict[str, Any]) -> None:
        """Process function-level assignments and update symbol table."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                try:
                    self.logger.log(f"[ASSIGNMENT] Processing: {target.id} = ...", 3)
                    
                    if isinstance(node.value, ast.Call):
                        # This is a function call assignment
                        self.logger.log(f"[ASSIGNMENT] Call assignment detected", 4)
                        var_type = self.type_inference.infer_from_call(node.value, self.name_resolver, context)
                        if var_type:
                            self.symbol_manager.update_variable_type(target.id, var_type)
                            self.logger.log(f"[ASSIGNMENT] RESOLVED Updated symbol table: {target.id} = {var_type}", 4)
                        else:
                            self.logger.log(f"[ASSIGNMENT] FAILED Could not infer type for {target.id}", 4)
                    else:
                        self.logger.log(f"[ASSIGNMENT] Non-call assignment", 4)
                except Exception as e:
                    self.logger.log(f"[ASSIGNMENT] ERROR: {e}", 4)
    
    def _process_function_ann_assign(self, node: ast.AnnAssign, context: Dict[str, Any]) -> None:
        """Process function-level annotated assignments."""
        try:
            if node.annotation:
                annotation_str = ast.unparse(node.annotation)
                self.logger.log(f"[ANNOTATED_ASSIGNMENT] {node.target.id} : {annotation_str}", 3)
                
                type_parts = self.name_resolver.extract_name_parts(node.annotation)
                if type_parts:
                    resolved_type = self._cached_resolve_name(type_parts, context)
                    if resolved_type:
                        self.symbol_manager.update_variable_type(node.target.id, resolved_type)
                        self.logger.log(f"-> Updated symbol table: {node.target.id} : {resolved_type}", 4)
                    else:
                        self.logger.log(f"-> Could not resolve type annotation", 4)
        except Exception as e:
            self.logger.log(f"[ANNOTATED_ASSIGNMENT] ERROR: {e}", 3)
    
    def _cached_resolve_name(self, name_parts: List[str], context: Dict[str, Any]) -> Optional[str]:
        """Resolve name using the name resolver."""
        return self.name_resolver.resolve_name(name_parts, context)
