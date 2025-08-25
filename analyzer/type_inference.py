"""
Type Inference Engine - Code Atlas

Handles the logic for inferring variable and expression types from
various AST patterns like function calls and assignments.
"""

import ast
import inspect
from typing import Dict, List, Optional, Any

from .logger import get_logger, LogContext, AnalysisPhase, LogLevel
from .utils import get_source


class TypeInferenceEngine:
    """Handles type inference from various AST patterns."""
    
    def __init__(self, recon_data: Dict[str, Any]):
        self.recon_data = recon_data
    
    def _log(
            self, 
            level: LogLevel, 
            message: str, 
            extra: Optional[Dict[str, Any]] = None
        ):
        """Consolidated logging with automatic source detection and context."""
        
        context = LogContext(
            phase=AnalysisPhase.ANALYSIS,
            source=get_source(),
            module=None,
            class_name=None,
            function=None            
        )
        
        getattr(get_logger(__name__), level.name.lower())(message, context, extra)
    
    def extract_core_type(self, type_string: str) -> Optional[str]:
        """Extract core type from generic annotations."""
        if not type_string:
            return None
        
        type_string = type_string.strip()
        
        # Handle common patterns
        if type_string.startswith("Optional[") and type_string.endswith("]"):
            core_type = type_string[9:-1].strip()
            self._log(LogLevel.TRACE, f"Extracted core type from Optional: {core_type}", extra={'original_type': type_string})
            return core_type
        if type_string.startswith("List[") and type_string.endswith("]"):
            core_type = type_string[5:-1].strip()
            self._log(LogLevel.TRACE, f"Extracted core type from List: {core_type}", extra={'original_type': type_string})
            return core_type
        if type_string.startswith("'") and type_string.endswith("'"):
            core_type = type_string[1:-1].strip()
            self._log(LogLevel.TRACE, f"Extracted core type from quoted string: {core_type}", extra={'original_type': type_string})
            return core_type
        if type_string.startswith('"') and type_string.endswith('"'):
            core_type = type_string[1:-1].strip()
            self._log(LogLevel.TRACE, f"Extracted core type from double-quoted string: {core_type}", extra={'original_type': type_string})
            return core_type
        
        self._log(LogLevel.TRACE, f"No core type extraction needed: {type_string}")
        return type_string
    
    def infer_from_call(self, call_node: ast.Call, name_resolver, context: Dict[str, Any]) -> Optional[str]:
        """Infer type from function call."""
        name_parts = self._extract_name_parts(call_node.func)
        if not name_parts:
            self._log(LogLevel.TRACE, "No name parts extracted from call node")
            return None
        
        call_name = '.'.join(name_parts)
        
        resolved_fqn = name_resolver.resolve_name(name_parts, context)
        if not resolved_fqn:
            self._log(LogLevel.DEBUG, f"Could not resolve call FQN for type inference: {call_name}")
            return None
        
        self._log(LogLevel.DEBUG, f"Call resolved to: {resolved_fqn}", extra={'original_call': call_name})
        
        # Class instantiation
        if (resolved_fqn in self.recon_data["classes"] or 
            resolved_fqn in self.recon_data.get("external_classes", {})):
            self._log(LogLevel.DEBUG, f"Inferred type from class instantiation: {resolved_fqn}", extra={'inference_type': 'class_instantiation'})
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
                    self._log(LogLevel.TRACE, f"Function has return type: {return_type}", extra={'function': resolved_fqn})
                    core_type = self.extract_core_type(return_type)
                    if core_type:
                        # **ENHANCED: Resolve the return type to its full FQN**
                        resolved_return_type = self._resolve_return_type_to_fqn(core_type, context)
                        if resolved_return_type:
                            self._log(LogLevel.DEBUG, f"Resolved return type to FQN: {resolved_return_type}", 
                                    extra={'function': resolved_fqn, 'original_return_type': return_type, 'inference_type': 'resolved_return_type'})
                            return resolved_return_type
                        else:
                            self._log(LogLevel.WARNING, f"Could not resolve return type '{core_type}' to FQN", 
                                    extra={'function': resolved_fqn, 'return_type': core_type})
                            # Fallback to the original core_type
                            self._log(LogLevel.DEBUG, f"Using unresolved return type: {core_type}", 
                                    extra={'function': resolved_fqn, 'inference_type': 'unresolved_return_type'})
                            return core_type
                    else:
                        self._log(LogLevel.WARNING, f"Could not extract core type from '{return_type}'", extra={'function': resolved_fqn})
                else:
                    self._log(LogLevel.TRACE, f"Function has no return type annotation: {resolved_fqn}")
        
        self._log(LogLevel.DEBUG, f"Could not infer type for call: {call_name}", extra={'resolved_fqn': resolved_fqn})
        return None

    def _resolve_return_type_to_fqn(self, return_type: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve return type string to its full FQN."""
        self._log(LogLevel.TRACE, f"Resolving return type to FQN: {return_type}")
        
        # If already fully qualified, check if it exists
        if "." in return_type:
            if (return_type in self.recon_data["classes"] or 
                return_type in self.recon_data.get("external_classes", {})):
                self._log(LogLevel.TRACE, f"Return type already FQN and exists: {return_type}")
                return return_type
        
        # Try to resolve simple class name to FQN
        if "." not in return_type:
            # First try current module
            current_module = context.get('current_module', '')
            candidate = f"{current_module}.{return_type}"
            
            if candidate in self.recon_data["classes"]:
                self._log(LogLevel.TRACE, f"Found return type in current module: {candidate}", extra={'original_type': return_type})
                return candidate
            
            # Search all modules for this class name
            for class_fqn in self.recon_data["classes"]:
                if class_fqn.endswith(f".{return_type}"):
                    self._log(LogLevel.TRACE, f"Found return type in other module: {class_fqn}", extra={'original_type': return_type})
                    return class_fqn
            
            # Search external classes
            for class_fqn in self.recon_data.get("external_classes", {}):
                if class_fqn.endswith(f".{return_type}"):
                    self._log(LogLevel.TRACE, f"Found return type in external classes: {class_fqn}", extra={'original_type': return_type})
                    return class_fqn
            
            self._log(LogLevel.DEBUG, f"Class '{return_type}' not found in any module")
        
        # Handle quoted strings like "'NetworkClient'"
        if return_type.startswith("'") and return_type.endswith("'"):
            unquoted = return_type[1:-1]
            self._log(LogLevel.TRACE, f"Recursively resolving quoted return type: {unquoted}", extra={'quoted_type': return_type})
            return self._resolve_return_type_to_fqn(unquoted, context)
        
        self._log(LogLevel.DEBUG, f"Could not resolve return type to FQN: {return_type}")
        return None
    
    def infer_from_assignment_value(self, value_node: ast.AST) -> Optional[str]:
        """Infer type from assignment value during reconnaissance."""
        if isinstance(value_node, ast.Call):
            if isinstance(value_node.func, ast.Name):
                inferred_type = value_node.func.id
                self._log(LogLevel.TRACE, f"Inferred type from direct call: {inferred_type}")
                return inferred_type
            elif isinstance(value_node.func, ast.Attribute):
                parts = self._extract_name_parts(value_node.func)
                if parts:
                    inferred_type = ".".join(parts)
                    self._log(LogLevel.TRACE, f"Inferred type from attribute call: {inferred_type}")
                    return inferred_type
        
        elif isinstance(value_node, ast.Constant):
            # For constants, return basic Python type names
            value = value_node.value
            if isinstance(value, str):
                return "str"
            elif isinstance(value, int):
                return "int"
            elif isinstance(value, float):
                return "float"
            elif isinstance(value, bool):
                return "bool"
        
        elif isinstance(value_node, ast.List):
            return "list"
        elif isinstance(value_node, ast.Dict):
            return "dict"
        elif isinstance(value_node, ast.Set):
            return "set"
        elif isinstance(value_node, ast.Tuple):
            return "tuple"
        elif isinstance(value_node, ast.Name):
            inferred_type = value_node.id
            self._log(LogLevel.TRACE, f"Inferred type from name: {inferred_type}")
            return inferred_type
        elif isinstance(value_node, ast.Attribute):
            parts = self._extract_name_parts(value_node)
            if parts:
                inferred_type = ".".join(parts)
                self._log(LogLevel.TRACE, f"Inferred type from attribute: {inferred_type}")
                return inferred_type
        
        self._log(LogLevel.TRACE, "Could not infer type from assignment value", extra={'node_type': type(value_node).__name__})
        return None
    
    def _extract_name_parts(self, node: ast.AST) -> Optional[List[str]]:
        """Extract name parts from AST node."""
        if isinstance(node, ast.Name):
            return [node.id]
        elif isinstance(node, ast.Attribute):
            parts = self._extract_name_parts(node.value)
            return parts + [node.attr] if parts else None
        
        self._log(LogLevel.TRACE, "Could not extract name parts from node", extra={'node_type': type(node).__name__})
        return None
