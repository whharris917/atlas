"""
Function Reconnaissance Visitor - Code Atlas

Specialized visitor for processing function and method definitions during reconnaissance.
Part of the Phase 2 refactoring to break down the monolithic ReconVisitor.

CRITICAL FIX: Added support for async functions to prevent missing method detection.
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
        self.current_class = None
    
    def set_class_context(self, class_fqn: Optional[str]):
        """Set current class context for method processing."""
        self.current_class = class_fqn
        if class_fqn:
            self.logger.log(f"[FUNC_CONTEXT] Set class context: {class_fqn}", 3)
    
    def process_function_def(self, node: ast.FunctionDef):
        """Process regular function definitions."""
        if self.current_class:
            fqn = f"{self.current_class}.{node.name}"
        else:
            fqn = f"{self.module_name}.{node.name}"
        
        # Extract return type
        return_type = None
        if node.returns:
            try:
                return_type = ast.unparse(node.returns)
            except Exception:
                pass
        
        # Extract parameter types
        param_types = {}
        for arg in node.args.args:
            if arg.annotation:
                try:
                    param_type = ast.unparse(arg.annotation)
                    param_types[arg.arg] = param_type
                except Exception:
                    pass
        
        # Store function information
        self.functions[fqn] = {
            "return_type": return_type,
            "param_types": param_types
        }
        
        self.logger.log(f"[FUNC_RECON] Function: {fqn}", 2)
        
        # Special handling for __init__ methods
        if self.current_class and node.name == "__init__":
            self.logger.log(f"[INIT_RECON] Processing __init__ for {self.current_class}", 2)
    
    def process_async_function_def(self, node: ast.AsyncFunctionDef):
        """
        Process async function definitions.
        
        CRITICAL FIX: This method was missing, causing async methods to be lost
        in the reconnaissance data, leading to function count mismatches.
        """
        if self.current_class:
            fqn = f"{self.current_class}.{node.name}"
        else:
            fqn = f"{self.module_name}.{node.name}"
        
        # Extract return type (same as regular functions)
        return_type = None
        if node.returns:
            try:
                return_type = ast.unparse(node.returns)
            except Exception:
                pass
        
        # Extract parameter types (same as regular functions)
        param_types = {}
        for arg in node.args.args:
            if arg.annotation:
                try:
                    param_type = ast.unparse(arg.annotation)
                    param_types[arg.arg] = param_type
                except Exception:
                    pass
        
        # Store async function information (mark as async)
        self.functions[fqn] = {
            "return_type": return_type,
            "param_types": param_types,
            "is_async": True  # Flag to distinguish async functions
        }
        
        self.logger.log(f"[ASYNC_FUNC_RECON] Async function: {fqn}", 2)
    
    def extract_init_attributes(self, init_node: ast.FunctionDef, type_inference) -> Dict[str, Any]:
        """
        Extract class attribute assignments from __init__ method.
        
        This method analyzes __init__ method bodies to find self.attribute = value
        assignments and infer their types.
        """
        attributes = {}
        
        self.logger.log(f"[INIT_EXTRACT] Extracting attributes from __init__", 3)
        
        for stmt in init_node.body:
            if isinstance(stmt, ast.Assign):
                # Look for self.attribute assignments
                for target in stmt.targets:
                    if (isinstance(target, ast.Attribute) and 
                        isinstance(target.value, ast.Name) and 
                        target.value.id == "self"):
                        
                        attr_name = target.attr
                        
                        # Try to infer type from assignment
                        inferred_type = "Unknown"
                        try:
                            if isinstance(stmt.value, ast.Constant):
                                # Direct value assignment
                                inferred_type = type(stmt.value.value).__name__
                            elif isinstance(stmt.value, ast.Name):
                                # Variable assignment - try to infer from parameter
                                var_name = stmt.value.id
                                for arg in init_node.args.args:
                                    if arg.arg == var_name and arg.annotation:
                                        inferred_type = ast.unparse(arg.annotation)
                                        break
                            elif isinstance(stmt.value, ast.Call):
                                # Constructor call - try to get type from function name
                                if isinstance(stmt.value.func, ast.Name):
                                    inferred_type = stmt.value.func.id
                                elif isinstance(stmt.value.func, ast.Attribute):
                                    # Handle module.Class() calls
                                    try:
                                        inferred_type = ast.unparse(stmt.value.func)
                                    except Exception:
                                        pass
                            elif isinstance(stmt.value, ast.List):
                                inferred_type = "list"
                            elif isinstance(stmt.value, ast.Dict):
                                inferred_type = "dict"
                            else:
                                # Use type inference engine for complex cases
                                inferred_type = type_inference.infer_type(stmt.value)
                        except Exception as e:
                            self.logger.log(f"[INIT_EXTRACT] Type inference error for {attr_name}: {e}", 3)
                        
                        attributes[attr_name] = {
                            "type": inferred_type
                        }
                        
                        self.logger.log(f"[INIT_EXTRACT] Found attribute: {attr_name} -> {inferred_type}", 3)
            
            elif isinstance(stmt, ast.AnnAssign):
                # Annotated assignments: self.attr: Type = value
                if (isinstance(stmt.target, ast.Attribute) and 
                    isinstance(stmt.target.value, ast.Name) and 
                    stmt.target.value.id == "self"):
                    
                    attr_name = stmt.target.attr
                    
                    # Get type from annotation
                    attr_type = "Unknown"
                    if stmt.annotation:
                        try:
                            attr_type = ast.unparse(stmt.annotation)
                        except Exception:
                            pass
                    
                    attributes[attr_name] = {
                        "type": attr_type
                    }
                    
                    self.logger.log(f"[INIT_EXTRACT] Found annotated attribute: {attr_name} -> {attr_type}", 3)
        
        self.logger.log(f"[INIT_EXTRACT] Extracted {len(attributes)} attributes", 2)
        return attributes
    
    def get_functions_data(self) -> Dict[str, Any]:
        """Get collected function data."""
        return self.functions.copy()
