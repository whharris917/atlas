"""
Function Reconnaissance Visitor - Code Atlas

Specialized visitor for processing function definitions and method extraction.
Part of the Phase 2 refactoring to break down the monolithic ReconVisitor.

EMERGENCY FIX: Added missing __init__ attribute extraction logic to match original implementation.
"""

import ast
from typing import Dict, List, Any, Optional
from ...utils_new.logger import AnalysisLogger
from ...utils_new.naming import generate_function_fqn


class FunctionReconVisitor:
    """Specialized visitor for function definition processing during reconnaissance pass."""
    
    def __init__(self, module_name: str, logger: AnalysisLogger):
        self.module_name = module_name
        self.logger = logger
        
        # Function tracking
        self.functions = {}
        
        # Context tracking
        self.current_class = None
    
    def set_class_context(self, class_fqn: Optional[str]):
        """Set current class context for method processing."""
        self.current_class = class_fqn
    
    def process_function_def(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Process function definitions and extract signature information."""
        # Determine function FQN based on context
        if self.current_class:
            fqn = f"{self.current_class}.{node.name}"
            context = "method"
        else:
            fqn = f"{self.module_name}.{node.name}"
            context = "function"
        
        self.logger.log(f"[FUNCTION_RECON] Processing {context}: {node.name}", 2)
        
        # Extract return type
        return_type = self._extract_return_type(node)
        
        # Extract parameter types
        param_types = self._extract_parameter_types(node)
        
        # Store function with type information
        function_info = {
            "return_type": return_type,
            "param_types": param_types
        }
        
        self.functions[fqn] = function_info
        self.logger.log(f"[FUNCTION_RECON] Stored {context}: {fqn}", 2)
        
        return function_info
    
    def _extract_return_type(self, node: ast.FunctionDef) -> Optional[str]:
        """Extract return type annotation from function definition."""
        if node.returns:
            try:
                return_type = ast.unparse(node.returns)
                self.logger.log(f"[RETURN_TYPE] Found return type: {return_type}", 3)
                return return_type
            except Exception as e:
                self.logger.log(f"[RETURN_TYPE] Error extracting return type: {e}", 1)
        
        return None
    
    def _extract_parameter_types(self, node: ast.FunctionDef) -> Dict[str, str]:
        """Extract parameter type annotations from function definition."""
        param_types = {}
        
        for arg in node.args.args:
            if arg.annotation:
                try:
                    param_type = ast.unparse(arg.annotation)
                    param_types[arg.arg] = param_type
                    self.logger.log(f"[PARAM_TYPE] {arg.arg}: {param_type}", 3)
                except Exception as e:
                    self.logger.log(f"[PARAM_TYPE] Error extracting type for {arg.arg}: {e}", 1)
        
        return param_types
    
    def is_init_method(self, node: ast.FunctionDef) -> bool:
        """Check if function is an __init__ method."""
        return self.current_class and node.name == "__init__"
    
    def extract_init_attributes(self, init_node: ast.FunctionDef, type_inference_engine) -> Dict[str, Dict[str, Any]]:
        """
        Extract class attribute assignments from __init__ method with parameter type inference.
        
        FIXED: This method was missing the core logic from the original implementation.
        """
        attributes = {}
        
        if not self.is_init_method(init_node):
            return attributes
        
        self.logger.log("[INIT_ATTRS] Extracting attributes from __init__", 2)
        
        # FIXED: Build parameter type mapping for inference (from original)
        param_types = {}
        for arg in init_node.args.args:
            if arg.arg != 'self' and arg.annotation:
                try:
                    param_type = ast.unparse(arg.annotation)
                    param_types[arg.arg] = param_type
                    self.logger.log(f"[INIT_PARAM] Parameter {arg.arg} has type hint: {param_type}", 3)
                except Exception as e:
                    self.logger.log(f"[INIT_PARAM] Failed to extract type for {arg.arg}: {e}", 1)
        
        self.logger.log(f"[INIT_ANALYSIS] Found {len(param_types)} parameter type hints", 2)
        
        # FIXED: Only look at direct statements in __init__ body, not nested statements
        for stmt in init_node.body:
            if isinstance(stmt, ast.Assign):
                # Handle self.attr = value assignments
                for target in stmt.targets:
                    if (isinstance(target, ast.Attribute) and 
                        isinstance(target.value, ast.Name) and 
                        target.value.id == "self"):
                        
                        attr_name = target.attr
                        resolved_type = None
                        
                        # Check if assignment is from a parameter with type hint
                        if (isinstance(stmt.value, ast.Name) and 
                            stmt.value.id in param_types):
                            resolved_type = param_types[stmt.value.id]
                            self.logger.log(f"[ATTR_FROM_PARAM] {attr_name} = {stmt.value.id} : {resolved_type}", 3)
                        else:
                            # Fallback to value-based inference
                            resolved_type = self._infer_init_attribute_type(stmt.value)
                            self.logger.log(f"[ATTR_FROM_VALUE] {attr_name} inferred as: {resolved_type}", 3)
                        
                        attributes[attr_name] = {
                            "type": resolved_type or "Unknown"
                        }
            
            elif isinstance(stmt, ast.AnnAssign):
                # Handle self.attr: Type = value assignments
                if (isinstance(stmt.target, ast.Attribute) and 
                    isinstance(stmt.target.value, ast.Name) and 
                    stmt.target.value.id == "self"):
                    
                    attr_name = stmt.target.attr
                    type_annotation = None
                    
                    if stmt.annotation:
                        try:
                            type_annotation = ast.unparse(stmt.annotation)
                            self.logger.log(f"[ATTR_ANNOT] {attr_name}: {type_annotation}", 3)
                        except Exception as e:
                            self.logger.log(f"[ATTR_ANNOT] Failed to extract annotation for {attr_name}: {e}", 1)
                    
                    attributes[attr_name] = {
                        "type": type_annotation or "Unknown"
                    }
        
        self.logger.log(f"[INIT_ATTRS] Found {len(attributes)} attributes", 2)
        return attributes
    
    def _infer_init_attribute_type(self, value_node: ast.AST) -> Optional[str]:
        """
        Infer attribute type from assignment value.
        
        FIXED: This was missing from the refactored implementation.
        """
        if isinstance(value_node, ast.Call):
            # Constructor call: self.attr = SomeClass()
            try:
                if isinstance(value_node.func, ast.Name):
                    return value_node.func.id
                elif isinstance(value_node.func, ast.Attribute):
                    parts = []
                    current = value_node.func
                    while isinstance(current, ast.Attribute):
                        parts.insert(0, current.attr)
                        current = current.value
                    if isinstance(current, ast.Name):
                        parts.insert(0, current.id)
                    return ".".join(parts)
            except Exception:
                pass
        
        elif isinstance(value_node, ast.Name):
            # Assignment from parameter: self.attr = param
            return value_node.id
        
        elif isinstance(value_node, ast.Constant):
            # Literal assignment: self.attr = "string" or self.attr = 42
            if isinstance(value_node.value, str):
                return "str"
            elif isinstance(value_node.value, int):
                return "int"
            elif isinstance(value_node.value, float):
                return "float"
            elif isinstance(value_node.value, bool):
                return "bool"
        
        elif isinstance(value_node, ast.List):
            return "list"
        elif isinstance(value_node, ast.Dict):
            return "dict"
        elif isinstance(value_node, ast.Subscript):
            # Handle subscript access like: self.attr = some_dict[key]
            try:
                return ast.unparse(value_node)
            except Exception:
                pass
        
        return None
    
    def get_functions_data(self) -> Dict[str, Dict[str, Any]]:
        """Get collected function data."""
        return self.functions.copy()
