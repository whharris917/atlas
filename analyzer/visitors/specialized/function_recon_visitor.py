"""
Function Reconnaissance Visitor - Code Atlas

Specialized visitor for processing function definitions and method extraction.
Part of the Phase 2 refactoring to break down the monolithic ReconVisitor.
"""

import ast
from typing import Dict, List, Any, Optional
from ...utils.logger import AnalysisLogger
from ...utils.naming import generate_function_fqn


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
        """Extract class attribute assignments from __init__ method with parameter type inference."""
        attributes = {}
        
        if not self.is_init_method(init_node):
            return attributes
        
        self.logger.log("[INIT_ATTRS] Extracting attributes from __init__", 3)
        
        # Build parameter type mapping for inference
        param_types = self._extract_parameter_types(init_node)
        
        # Walk through __init__ body looking for self.attr assignments
        for stmt in init_node.body:
            if isinstance(stmt, ast.Assign):
                attrs = self._process_init_assignment(stmt, param_types, type_inference_engine)
                attributes.update(attrs)
            elif isinstance(stmt, ast.AnnAssign):
                attrs = self._process_init_ann_assignment(stmt, param_types, type_inference_engine)
                attributes.update(attrs)
        
        self.logger.log(f"[INIT_ATTRS] Found {len(attributes)} attributes", 2)
        return attributes
    
    def _process_init_assignment(self, stmt: ast.Assign, param_types: Dict[str, str], type_inference_engine) -> Dict[str, Dict[str, Any]]:
        """Process assignment statement in __init__ method."""
        attributes = {}
        
        for target in stmt.targets:
            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                attr_name = target.attr
                inferred_type = self._infer_attribute_type(stmt.value, param_types, type_inference_engine)
                
                attributes[attr_name] = {
                    "type": inferred_type or "Unknown",
                    "source": "assignment"
                }
                
                self.logger.log(f"[ATTR_ASSIGN] {attr_name}: {inferred_type}", 3)
        
        return attributes
    
    def _process_init_ann_assignment(self, stmt: ast.AnnAssign, param_types: Dict[str, str], type_inference_engine) -> Dict[str, Dict[str, Any]]:
        """Process annotated assignment statement in __init__ method."""
        attributes = {}
        
        if isinstance(stmt.target, ast.Attribute) and isinstance(stmt.target.value, ast.Name) and stmt.target.value.id == "self":
            attr_name = stmt.target.attr
            
            # Use annotation if available, otherwise infer from value
            if stmt.annotation:
                try:
                    attr_type = ast.unparse(stmt.annotation)
                    attributes[attr_name] = {
                        "type": attr_type,
                        "source": "annotation"
                    }
                    self.logger.log(f"[ATTR_ANNOT] {attr_name}: {attr_type}", 3)
                except Exception:
                    pass
            
            # If no annotation or failed to parse, try to infer from value
            if attr_name not in attributes and stmt.value:
                inferred_type = self._infer_attribute_type(stmt.value, param_types, type_inference_engine)
                attributes[attr_name] = {
                    "type": inferred_type or "Unknown",
                    "source": "inferred"
                }
        
        return attributes
    
    def _infer_attribute_type(self, value_node: ast.AST, param_types: Dict[str, str], type_inference_engine) -> Optional[str]:
        """Infer attribute type from assignment value."""
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
            param_name = value_node.id
            if param_name in param_types:
                return param_types[param_name]
            return param_name
        
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
        
        # Fallback to type inference engine
        try:
            return type_inference_engine.infer_from_assignment_value(value_node)
        except Exception:
            return None
    
    def get_functions_data(self) -> Dict[str, Dict[str, Any]]:
        """Get collected function data."""
        return self.functions.copy()
