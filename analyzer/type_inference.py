"""
Type Inference Engine - Code Atlas

Handles the logic for inferring variable and expression types from
various AST patterns like function calls and assignments.
"""

import ast
from typing import Dict, List, Optional, Any

from .logger import get_logger, LogContext, AnalysisPhase


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
            core_type = type_string[9:-1].strip()
            get_logger(__name__).trace(f"Extracted core type from Optional: {core_type}",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS, 
                                         extra={'original_type': type_string}))
            return core_type
        if type_string.startswith("List[") and type_string.endswith("]"):
            core_type = type_string[5:-1].strip()
            get_logger(__name__).trace(f"Extracted core type from List: {core_type}",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                         extra={'original_type': type_string}))
            return core_type
        if type_string.startswith("'") and type_string.endswith("'"):
            core_type = type_string[1:-1].strip()
            get_logger(__name__).trace(f"Extracted core type from quoted string: {core_type}",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                         extra={'original_type': type_string}))
            return core_type
        if type_string.startswith('"') and type_string.endswith('"'):
            core_type = type_string[1:-1].strip()
            get_logger(__name__).trace(f"Extracted core type from double-quoted string: {core_type}",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                         extra={'original_type': type_string}))
            return core_type
        
        get_logger(__name__).trace(f"No core type extraction needed: {type_string}",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS))
        return type_string
    
    def infer_from_call(self, call_node: ast.Call, name_resolver, context: Dict[str, Any]) -> Optional[str]:
        """Infer type from function call."""
        name_parts = self._extract_name_parts(call_node.func)
        if not name_parts:
            get_logger(__name__).trace("No name parts extracted from call node",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS))
            return None
        
        call_name = '.'.join(name_parts)
        get_logger(__name__).debug(f"Inferring type from call: {call_name}",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                     extra={'call_parts': name_parts}))
        
        resolved_fqn = name_resolver.resolve_name(name_parts, context)
        if not resolved_fqn:
            get_logger(__name__).debug(f"Could not resolve call FQN for type inference: {call_name}",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS))
            return None
        
        get_logger(__name__).debug(f"Call resolved to: {resolved_fqn}",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                     extra={'original_call': call_name}))
        
        # Class instantiation
        if (resolved_fqn in self.recon_data["classes"] or 
            resolved_fqn in self.recon_data.get("external_classes", {})):
            get_logger(__name__).debug(f"Inferred type from class instantiation: {resolved_fqn}",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                         extra={'inference_type': 'class_instantiation'}))
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
                    get_logger(__name__).trace(f"Function has return type: {return_type}",
                               context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                                extra={'function': resolved_fqn}))
                    core_type = self.extract_core_type(return_type)
                    if core_type:
                        # **ENHANCED: Resolve the return type to its full FQN**
                        resolved_return_type = self._resolve_return_type_to_fqn(core_type, context)
                        if resolved_return_type:
                            get_logger(__name__).debug(f"Resolved return type to FQN: {resolved_return_type}",
                                       context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                                        extra={'function': resolved_fqn,
                                                               'original_return_type': return_type,
                                                               'inference_type': 'resolved_return_type'}))
                            return resolved_return_type
                        else:
                            get_logger(__name__).warning(f"Could not resolve return type '{core_type}' to FQN",
                                         context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                                          extra={'function': resolved_fqn,
                                                                 'return_type': core_type}))
                            # Fallback to the original core_type
                            get_logger(__name__).debug(f"Using unresolved return type: {core_type}",
                                       context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                                        extra={'function': resolved_fqn,
                                                               'inference_type': 'unresolved_return_type'}))
                            return core_type
                    else:
                        get_logger(__name__).warning(f"Could not extract core type from '{return_type}'",
                                     context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                                      extra={'function': resolved_fqn}))
                else:
                    get_logger(__name__).trace(f"Function has no return type annotation: {resolved_fqn}",
                               context=LogContext(phase=AnalysisPhase.ANALYSIS))
        
        get_logger(__name__).debug(f"Could not infer type for call: {call_name}",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                     extra={'resolved_fqn': resolved_fqn}))
        return None

    def _resolve_return_type_to_fqn(self, return_type: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve return type string to its full FQN."""
        get_logger(__name__).trace(f"Resolving return type to FQN: {return_type}",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS))
        
        # If already fully qualified, check if it exists
        if "." in return_type:
            if (return_type in self.recon_data["classes"] or 
                return_type in self.recon_data.get("external_classes", {})):
                get_logger(__name__).trace(f"Return type already FQN and exists: {return_type}",
                           context=LogContext(phase=AnalysisPhase.ANALYSIS))
                return return_type
        
        # Try to resolve simple class name to FQN
        if "." not in return_type:
            # First try current module
            current_module = context.get('current_module', '')
            candidate = f"{current_module}.{return_type}"
            
            if candidate in self.recon_data["classes"]:
                get_logger(__name__).trace(f"Found return type in current module: {candidate}",
                           context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                            extra={'original_type': return_type}))
                return candidate
            
            # Search all modules for this class name
            for class_fqn in self.recon_data["classes"]:
                if class_fqn.endswith(f".{return_type}"):
                    get_logger(__name__).trace(f"Found return type in other module: {class_fqn}",
                               context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                                extra={'original_type': return_type}))
                    return class_fqn
            
            # Search external classes
            for class_fqn in self.recon_data.get("external_classes", {}):
                if class_fqn.endswith(f".{return_type}"):
                    get_logger(__name__).trace(f"Found return type in external classes: {class_fqn}",
                               context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                                extra={'original_type': return_type}))
                    return class_fqn
            
            get_logger(__name__).debug(f"Class '{return_type}' not found in any module",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS))
        
        # Handle quoted strings like "'NetworkClient'"
        if return_type.startswith("'") and return_type.endswith("'"):
            unquoted = return_type[1:-1]
            get_logger(__name__).trace(f"Recursively resolving quoted return type: {unquoted}",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                         extra={'quoted_type': return_type}))
            return self._resolve_return_type_to_fqn(unquoted, context)
        
        get_logger(__name__).debug(f"Could not resolve return type to FQN: {return_type}",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS))
        return None
    
    def infer_from_assignment_value(self, value_node: ast.AST) -> Optional[str]:
        """Infer type from assignment value during reconnaissance."""
        if isinstance(value_node, ast.Call):
            if isinstance(value_node.func, ast.Name):
                inferred_type = value_node.func.id
                get_logger(__name__).trace(f"Inferred type from direct call: {inferred_type}",
                           context=LogContext(phase=AnalysisPhase.RECONNAISSANCE))
                return inferred_type
            elif isinstance(value_node.func, ast.Attribute):
                parts = self._extract_name_parts(value_node.func)
                if parts:
                    inferred_type = ".".join(parts)
                    get_logger(__name__).trace(f"Inferred type from attribute call: {inferred_type}",
                               context=LogContext(phase=AnalysisPhase.RECONNAISSANCE))
                    return inferred_type
        elif isinstance(value_node, ast.Name):
            inferred_type = value_node.id
            get_logger(__name__).trace(f"Inferred type from name: {inferred_type}",
                        context=LogContext(phase=AnalysisPhase.RECONNAISSANCE))
            return inferred_type
        elif isinstance(value_node, ast.Attribute):
            parts = self._extract_name_parts(value_node)
            if parts:
                inferred_type = ".".join(parts)
                get_logger(__name__).trace(f"Inferred type from attribute: {inferred_type}",
                           context=LogContext(phase=AnalysisPhase.RECONNAISSANCE))
                return inferred_type
        
        get_logger(__name__).trace("Could not infer type from assignment value",
                    context=LogContext(phase=AnalysisPhase.RECONNAISSANCE,
                                     extra={'node_type': type(value_node).__name__}))
        return None
    
    def _extract_name_parts(self, node: ast.AST) -> Optional[List[str]]:
        """Extract name parts from AST node."""
        if isinstance(node, ast.Name):
            return [node.id]
        elif isinstance(node, ast.Attribute):
            parts = self._extract_name_parts(node.value)
            return parts + [node.attr] if parts else None
        
        get_logger(__name__).trace("Could not extract name parts from node",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                     extra={'node_type': type(node).__name__}))
        return None
