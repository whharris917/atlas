"""
Type Inference Engine - Code Atlas

Handles the logic for inferring variable and expression types from
various AST patterns like function calls and assignments.
"""

import ast
from typing import Dict, List, Optional, Any
    

class TypeInferenceEngine:
    """Handles type inference from various AST patterns."""
    
    def __init__(self, recon_data: Dict[str, Any]):
        self.recon_data = recon_data
    
    def extract_core_type(self, type_string: str) -> Optional[str]:
        """Extract core type from generic annotations."""
        if not type_string:
            return None
        
        type_string = type_string.strip()
        
        # Handle common patterns
        if type_string.startswith("Optional[") and type_string.endswith("]"):
            return type_string[9:-1].strip()
        if type_string.startswith("List[") and type_string.endswith("]"):
            return type_string[5:-1].strip()
        if type_string.startswith("'") and type_string.endswith("'"):
            return type_string[1:-1].strip()
        if type_string.startswith('"') and type_string.endswith('"'):
            return type_string[1:-1].strip()
        
        return type_string
    
    def infer_from_call(self, call_node: ast.Call, name_resolver, context: Dict[str, Any]) -> Optional[str]:
        """Infer type from function call."""
        name_parts = self._extract_name_parts(call_node.func)
        if not name_parts:
            print("      [TYPE_INFERENCE] No name parts extracted from call")
            return None
        
        print(f"      [TYPE_INFERENCE] Attempting to infer type from call: {'.'.join(name_parts)}")
        
        resolved_fqn = name_resolver.resolve_name(name_parts, context)
        if not resolved_fqn:
            print(f"      [TYPE_INFERENCE] Could not resolve call FQN")
            return None
        
        print(f"      [TYPE_INFERENCE] Call resolved to: {resolved_fqn}")
        
        # Class instantiation
        if (resolved_fqn in self.recon_data["classes"] or 
            resolved_fqn in self.recon_data.get("external_classes", {})):
            print(f"      [TYPE_INFERENCE] RESOLVED Inferred type: {resolved_fqn} (class instantiation)")
            return resolved_fqn
        
        # Function call - use return type
        if (resolved_fqn in self.recon_data["functions"] or
            resolved_fqn in self.recon_data.get("external_functions", {})):
            
            func_info = None
            if resolved_fqn in self.recon_data["functions"]:
                func_info = self.recon_data["functions"][resolved_fqn]
            elif resolved_fqn in self.recon_data.get("external_functions", {}):
                func_info = self.recon_data["external_functions"][resolved_fqn]
            
            if func_info:
                return_type = func_info.get("return_type")
                if return_type:
                    core_type = self.extract_core_type(return_type)
                    if core_type:
                        # **ENHANCED: Resolve the return type to its full FQN**
                        resolved_return_type = self._resolve_return_type_to_fqn(core_type, context)
                        if resolved_return_type:
                            print(f"      [TYPE_INFERENCE] RESOLVED Inferred type: {resolved_return_type} (from return type)")
                            return resolved_return_type
                        else:
                            print(f"      [TYPE_INFERENCE] Could not resolve return type '{core_type}' to FQN")
                            # Fallback to the original core_type
                            print(f"      [TYPE_INFERENCE] RESOLVED Inferred type: {core_type} (from return type - unresolved)")
                            return core_type
                    else:
                        print(f"      [TYPE_INFERENCE] Could not extract core type from '{return_type}'")
                else:
                    print(f"      [TYPE_INFERENCE] Function has no return type annotation")
        
        print(f"      [TYPE_INFERENCE] FAILED Could not infer type")
        return None

    def _resolve_return_type_to_fqn(self, return_type: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve return type string to its full FQN."""
        print(f"        [RETURN_TYPE_RESOLUTION] Resolving return type: {return_type}")
        
        # If already fully qualified, check if it exists
        if "." in return_type:
            if (return_type in self.recon_data["classes"] or 
                return_type in self.recon_data.get("external_classes", {})):
                print(f"        [RETURN_TYPE_RESOLUTION] Already FQN and exists: {return_type}")
                return return_type
        
        # Try to resolve simple class name to FQN
        if "." not in return_type:
            # First try current module
            current_module = context.get('current_module', '')
            candidate = f"{current_module}.{return_type}"
            
            if candidate in self.recon_data["classes"]:
                print(f"        [RETURN_TYPE_RESOLUTION] Found in current module: {candidate}")
                return candidate
            
            # Search all modules for this class name
            for class_fqn in self.recon_data["classes"]:
                if class_fqn.endswith(f".{return_type}"):
                    print(f"        [RETURN_TYPE_RESOLUTION] Found in other module: {class_fqn}")
                    return class_fqn
            
            # Search external classes
            for class_fqn in self.recon_data.get("external_classes", {}):
                if class_fqn.endswith(f".{return_type}"):
                    print(f"        [RETURN_TYPE_RESOLUTION] Found in external classes: {class_fqn}")
                    return class_fqn
            
            print(f"        [RETURN_TYPE_RESOLUTION] Class '{return_type}' not found in any module")
        
        # Handle quoted strings like "'NetworkClient'"
        if return_type.startswith("'") and return_type.endswith("'"):
            unquoted = return_type[1:-1]
            return self._resolve_return_type_to_fqn(unquoted, context)
        
        print(f"        [RETURN_TYPE_RESOLUTION] Could not resolve return type: {return_type}")
        return None
    
    def infer_from_assignment_value(self, value_node: ast.AST) -> Optional[str]:
        """Infer type from assignment value during reconnaissance."""
        if isinstance(value_node, ast.Call):
            if isinstance(value_node.func, ast.Name):
                return value_node.func.id
            elif isinstance(value_node.func, ast.Attribute):
                parts = self._extract_name_parts(value_node.func)
                return ".".join(parts) if parts else None
        elif isinstance(value_node, ast.Name):
            return value_node.id
        elif isinstance(value_node, ast.Attribute):
            parts = self._extract_name_parts(value_node)
            return ".".join(parts) if parts else None
        
        return None
    
    def _extract_name_parts(self, node: ast.AST) -> Optional[List[str]]:
        """Extract name parts from AST node."""
        if isinstance(node, ast.Name):
            return [node.id]
        elif isinstance(node, ast.Attribute):
            parts = self._extract_name_parts(node.value)
            return parts + [node.attr] if parts else None
        return None
