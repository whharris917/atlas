"""
Assignment Analyzer - Code Atlas (Transitional Version)

Handles the logic for processing `ast.Assign` and `ast.AnnAssign` nodes using
the new architectural pattern while working with existing components.

This version demonstrates the "Analyze & Register" pattern and proper scope
integration while serving as a bridge to full Expression Traversal implementation.

UPDATED: Uses ScopeManager and demonstrates future architectural patterns.
"""

import ast
from typing import Dict, Any, Optional

from .logger import get_logger, LogLevel
from .utils import get_source


class AssignmentAnalyzer:
    """
    Analyzes assignment nodes using the new architectural pattern.
    
    This transitional implementation demonstrates:
    - Clean "Analyze & Register" pattern
    - Direct ScopeManager integration
    - Separation of concerns between analysis and mutation
    - Foundation for Expression Traversal integration
    """

    def __init__(self, recon_data: Dict[str, Any], visitor):
        self.recon_data = recon_data
        self.visitor = visitor
        self.logger = get_logger()

    def _log(self, level: LogLevel, message: str, extra: Optional[Dict[str, Any]] = None):
        """Enhanced log with automatic source detection and correct module tracking."""
        getattr(get_logger(), level.name.lower())(message, get_source(), extra)

    def analyze_assignment(self, node: ast.Assign):
        """
        Analyze standard assignment using the new architectural pattern.
        
        This method demonstrates the "Analyze & Register" pattern:
        1. ANALYZE: Determine what the assignment means
        2. REGISTER: Record the findings appropriately
        """
        self._log(LogLevel.DEBUG, "Analyzing standard assignment")
        
        # ANALYZE PHASE: Understand the assignment context and type
        analysis_result = self._analyze_assignment_context(node)
        
        if analysis_result:
            # REGISTER PHASE: Record findings based on context
            self._register_assignment_findings(node, analysis_result)

    def analyze_annotated_assignment(self, node: ast.AnnAssign):
        """
        Analyze annotated assignment using the new architectural pattern.
        
        For annotated assignments, the annotation is the primary source of truth.
        """
        self._log(LogLevel.DEBUG, "Analyzing annotated assignment")
        
        # ANALYZE PHASE: Process the annotation
        analysis_result = self._analyze_annotated_assignment_context(node)
        
        if analysis_result:
            # REGISTER PHASE: Record findings based on context
            self._register_annotated_assignment_findings(node, analysis_result)

    def _analyze_assignment_context(self, node: ast.Assign) -> Optional[Dict[str, Any]]:
        """
        ANALYZE PHASE: Determine assignment context and type.
        
        Returns analysis result with context and inferred type information.
        """
        # Only handle single-target assignments for now
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            self._log(LogLevel.TRACE, "Skipping complex assignment (multiple targets or non-name target)")
            return None
        
        target_name = node.targets[0].id
        
        # Determine assignment context
        current_class = self.visitor.scope_manager.get_current_class_fqn()
        is_in_function = self.visitor.current_function_report is not None
        
        context_type = self._determine_assignment_context(current_class, is_in_function)
        
        # Attempt type inference for function calls
        inferred_type = None
        if is_in_function and isinstance(node.value, ast.Call):
            inferred_type = self._infer_assignment_type(node.value)
        
        return {
            "target_name": target_name,
            "context_type": context_type,
            "inferred_type": inferred_type,
            "value_node": node.value
        }

    def _analyze_annotated_assignment_context(self, node: ast.AnnAssign) -> Optional[Dict[str, Any]]:
        """
        ANALYZE PHASE: Process annotated assignment context.
        
        For annotated assignments, we prioritize the annotation over value inference.
        """
        if not isinstance(node.target, ast.Name):
            self._log(LogLevel.TRACE, "Skipping complex annotated assignment (non-name target)")
            return None
        
        target_name = node.target.id
        
        # Determine assignment context
        current_class = self.visitor.scope_manager.get_current_class_fqn()
        is_in_function = self.visitor.current_function_report is not None
        
        context_type = self._determine_assignment_context(current_class, is_in_function)
        
        # Resolve annotation type
        resolved_annotation_type = None
        if node.annotation:
            resolved_annotation_type = self._resolve_annotation_type(node.annotation)
        
        return {
            "target_name": target_name,
            "context_type": context_type,
            "annotation_type": resolved_annotation_type,
            "value_node": node.value
        }

    def _determine_assignment_context(self, current_class: Optional[str], is_in_function: bool) -> str:
        """Determine the context type of an assignment."""
        if not current_class and not is_in_function:
            return "module_state"
        elif is_in_function:
            return "function_local"
        else:
            return "class_attribute"

    def _infer_assignment_type(self, value_node: ast.Call) -> Optional[str]:
        """
        Infer type from function call assignment using existing type inference.
        
        This is a transitional method that bridges to Expression Traversal.
        """
        try:
            context = self.visitor._get_context()
            var_type = self.visitor.type_inference.infer_from_call(
                value_node, self.visitor.name_resolver, context
            )
            
            if var_type:
                self._log(LogLevel.TRACE, f"Successfully inferred type: {var_type}")
                return var_type
            else:
                self._log(LogLevel.TRACE, "Could not infer type from function call")
                return None
                
        except Exception as e:
            self._log(LogLevel.ERROR, f"Error during type inference: {e}")
            return None

    def _resolve_annotation_type(self, annotation_node: ast.expr) -> Optional[str]:
        """
        Resolve annotation type using existing name resolution.
        
        This is a transitional method that bridges to Expression Traversal.
        """
        try:
            context = self.visitor._get_context()
            type_parts = self.visitor.name_resolver.extract_name_parts(annotation_node)
            
            if type_parts:
                resolved_type = self.visitor._cached_resolve_name(type_parts, context)
                if resolved_type:
                    self._log(LogLevel.TRACE, f"Successfully resolved annotation: {resolved_type}")
                    return resolved_type
                else:
                    annotation_str = ast.unparse(annotation_node)
                    self._log(LogLevel.WARNING, f"Could not resolve annotation: {annotation_str}")
                    return None
            else:
                self._log(LogLevel.WARNING, "Could not extract type parts from annotation")
                return None
                
        except Exception as e:
            self._log(LogLevel.ERROR, f"Error resolving annotation: {e}")
            return None

    def _register_assignment_findings(self, node: ast.Assign, analysis_result: Dict[str, Any]):
        """
        REGISTER PHASE: Record assignment findings based on context.
        
        This method demonstrates clean separation between analysis and registration.
        """
        target_name = analysis_result["target_name"]
        context_type = analysis_result["context_type"]
        inferred_type = analysis_result["inferred_type"]
        value_node = analysis_result["value_node"]
        
        if context_type == "module_state":
            self._register_module_state_assignment(target_name, value_node)
        elif context_type == "function_local":
            self._register_function_local_assignment(target_name, inferred_type)
        else:
            self._log(LogLevel.TRACE, f"Unhandled assignment context: {context_type}")

    def _register_annotated_assignment_findings(self, node: ast.AnnAssign, analysis_result: Dict[str, Any]):
        """
        REGISTER PHASE: Record annotated assignment findings.
        """
        target_name = analysis_result["target_name"]
        context_type = analysis_result["context_type"]
        annotation_type = analysis_result["annotation_type"]
        value_node = analysis_result["value_node"]
        
        if context_type == "module_state":
            self._register_module_state_annotated_assignment(target_name, node.annotation, value_node)
        elif context_type == "function_local":
            self._register_function_local_annotated_assignment(target_name, annotation_type)
        else:
            self._log(LogLevel.TRACE, f"Unhandled annotated assignment context: {context_type}")

    def _register_module_state_assignment(self, target_name: str, value_node: ast.expr):
        """Register module-level state assignment."""
        try:
            state_entry = {
                "name": target_name,
                "value": ast.unparse(value_node) if value_node else "None"
            }
            self.visitor.module_report["module_state"].append(state_entry)
            self._log(LogLevel.DEBUG, f"Registered module state: {target_name} = {state_entry['value']}")
        except Exception as e:
            self._log(LogLevel.ERROR, f"Error registering module state assignment: {e}")

    def _register_module_state_annotated_assignment(self, target_name: str, annotation_node: ast.expr, value_node: Optional[ast.expr]):
        """Register module-level annotated state assignment."""
        try:
            state_entry = {
                "name": target_name,
                "value": ast.unparse(value_node) if value_node else "None"
            }
            self.visitor.module_report["module_state"].append(state_entry)
            
            annotation_str = ast.unparse(annotation_node) if annotation_node else 'Unknown'
            self._log(LogLevel.DEBUG, f"Registered module annotated state: {target_name} : {annotation_str} = {state_entry['value']}")
        except Exception as e:
            self._log(LogLevel.ERROR, f"Error registering module annotated assignment: {e}")

    def _register_function_local_assignment(self, target_name: str, inferred_type: Optional[str]):
        """Register function-local variable assignment using ScopeManager."""
        if inferred_type:
            # DEMONSTRATE: Direct ScopeManager usage for variable registration
            self.visitor.scope_manager.update_variable_type(target_name, inferred_type)
            self._log(LogLevel.TRACE, f"Registered function local variable: {target_name} -> {inferred_type}")
        else:
            self._log(LogLevel.TRACE, f"Could not register type for function local variable: {target_name}")

    def _register_function_local_annotated_assignment(self, target_name: str, annotation_type: Optional[str]):
        """Register function-local annotated variable assignment using ScopeManager."""
        if annotation_type:
            # DEMONSTRATE: Direct ScopeManager usage for variable registration
            self.visitor.scope_manager.update_variable_type(target_name, annotation_type)
            self._log(LogLevel.TRACE, f"Registered function local annotated variable: {target_name} -> {annotation_type}")
        else:
            self._log(LogLevel.WARNING, f"Could not register annotation type for variable: {target_name}")
