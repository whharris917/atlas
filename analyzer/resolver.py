"""
Name Resolution Engine - Code Atlas

Contains the core NameResolver and its associated strategies for resolving
names and attribute chains within different contexts.
"""

import ast
from typing import Dict, List, Optional, Any

from .logger import get_logger, create_context, AnalysisPhase, log_debug, log_trace


class ResolutionStrategy:
    """Base class for name resolution strategies."""
    
    def can_resolve(self, base_name: str, context: Dict[str, Any]) -> bool:
        """Check if this strategy can resolve the given name."""
        raise NotImplementedError
    
    def resolve(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve the name using this strategy."""
        raise NotImplementedError


class LocalVariableStrategy(ResolutionStrategy):
    """Resolves names from local variable symbol tables."""
    
    def can_resolve(self, base_name: str, context: Dict[str, Any]) -> bool:
        symbol_manager = context.get('symbol_manager')
        can_resolve = symbol_manager and symbol_manager.get_variable_type(base_name) is not None
        
        log_context = create_context("resolver", AnalysisPhase.ANALYSIS, "LocalVariableStrategy")
        log_trace(f"can_resolve({base_name}): {can_resolve}", log_context)
        return can_resolve
    
    def resolve(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        symbol_manager = context['symbol_manager']
        result = symbol_manager.get_variable_type(base_name)
        
        log_context = create_context("resolver", AnalysisPhase.ANALYSIS, "LocalVariableStrategy")
        log_trace(f"resolve({base_name}): {result}", log_context)
        return result


class SelfStrategy(ResolutionStrategy):
    """Resolves 'self' references to current class."""
    
    def can_resolve(self, base_name: str, context: Dict[str, Any]) -> bool:
        can_resolve = base_name == "self" and context.get('current_class')
        
        log_context = create_context("resolver", AnalysisPhase.ANALYSIS, "SelfStrategy")
        log_trace(f"can_resolve({base_name}): {can_resolve}", log_context)
        return can_resolve
    
    def resolve(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        result = context['current_class']
        
        log_context = create_context("resolver", AnalysisPhase.ANALYSIS, "SelfStrategy")
        log_trace(f"resolve({base_name}): {result}", log_context)
        return result


class ImportStrategy(ResolutionStrategy):
    """Resolves names from import aliases and external libraries."""
    
    def __init__(self, recon_data: Dict[str, Any]):
        self.recon_data = recon_data
    
    def can_resolve(self, base_name: str, context: Dict[str, Any]) -> bool:
        import_map = context.get('import_map', {})
        can_resolve_import = base_name in import_map
        can_resolve_external = self._can_resolve_external(base_name)
        can_resolve = can_resolve_import or can_resolve_external
        
        log_context = create_context("resolver", AnalysisPhase.ANALYSIS, "ImportStrategy")
        log_trace(f"can_resolve({base_name}): {can_resolve} (import: {can_resolve_import}, external: {can_resolve_external})", log_context)
        return can_resolve
    
    def resolve(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        import_map = context.get('import_map', {})
        log_context = create_context("resolver", AnalysisPhase.ANALYSIS, "ImportStrategy")
        
        # First try direct import map
        if base_name in import_map:
            result = import_map[base_name]
            log_trace(f"resolve({base_name}): {result} (from import map)", log_context)
            return result
        
        # Then try external library resolution
        external_result = self._resolve_external(base_name)
        if external_result:
            log_trace(f"resolve({base_name}): {external_result} (external)", log_context)
            return external_result
        
        return None
    
    def _can_resolve_external(self, name: str) -> bool:
        """Check if name can be resolved from external libraries."""
        # Check if it's a direct external class or function alias
        for ext_class_fqn, ext_info in self.recon_data.get("external_classes", {}).items():
            if ext_info["local_alias"] == name:
                return True
        
        for ext_func_fqn, ext_info in self.recon_data.get("external_functions", {}).items():
            if ext_info["local_alias"] == name:
                return True
        
        return False
    
    def _resolve_external(self, name: str) -> Optional[str]:
        """Resolve name from external library imports."""
        # Check external classes
        for ext_class_fqn, ext_info in self.recon_data.get("external_classes", {}).items():
            if ext_info["local_alias"] == name:
                return ext_class_fqn
        
        # Check external functions
        for ext_func_fqn, ext_info in self.recon_data.get("external_functions", {}).items():
            if ext_info["local_alias"] == name:
                return ext_func_fqn
        
        return None


class ModuleStrategy(ResolutionStrategy):
    """Resolves names from current module (fallback)."""
    
    def can_resolve(self, base_name: str, context: Dict[str, Any]) -> bool:
        log_context = create_context("resolver", AnalysisPhase.ANALYSIS, "ModuleStrategy")
        log_trace(f"can_resolve({base_name}): True (fallback)", log_context)
        return True  # Always can try this as fallback
    
    def resolve(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        current_module = context.get('current_module', '')
        result = f"{current_module}.{base_name}"
        
        log_context = create_context("resolver", AnalysisPhase.ANALYSIS, "ModuleStrategy")
        log_trace(f"resolve({base_name}): {result}", log_context)
        return result


class NameResolver:
    """Core name resolution engine with inheritance-aware method resolution, attribute support, and external library support."""
    
    def __init__(self, recon_data: Dict[str, Any]):
        self.recon_data = recon_data
        self.strategies = [
            LocalVariableStrategy(),
            SelfStrategy(),
            ImportStrategy(recon_data),  # Pass recon_data to ImportStrategy
            ModuleStrategy()
        ]
    
    def resolve_name(self, name_parts: List[str], context: Dict[str, Any]) -> Optional[str]:
        """Resolve name using layered strategies with comprehensive logging."""
        if not name_parts:
            log_context = create_context("resolver", AnalysisPhase.ANALYSIS, "resolve_name")
            log_debug("FAILED No name parts provided", log_context)
            return None
        
        log_context = create_context("resolver", AnalysisPhase.ANALYSIS, "resolve_name")
        log_debug(f"Attempting to resolve: {name_parts}", log_context)
        
        # Layer 1: Simple resolution for single names
        if len(name_parts) == 1:
            result = self._resolve_simple(name_parts[0], context)
            if result:
                log_debug(f"RESOLVED to: {result}", log_context)
            else:
                log_debug(f"FAILED to resolve: {name_parts[0]}", log_context)
            return result
        
        # Layer 2: Complex chain resolution
        log_debug(f"Chain resolution needed for: {name_parts}", log_context)
        result = self._resolve_chain(name_parts, context)
        if result:
            log_debug(f"RESOLVED to: {result}", log_context)
        else:
            log_debug(f"FAILED to resolve chain: {'.'.join(name_parts)}", log_context)
        return result
    
    def _resolve_simple(self, name: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve simple single name using strategies."""
        log_context = create_context("resolver", AnalysisPhase.ANALYSIS, "_resolve_simple")
        log_trace(f"Resolving base: {name}", log_context)
        
        for i, strategy in enumerate(self.strategies):
            strategy_name = strategy.__class__.__name__
            log_trace(f"Trying strategy {i+1}: {strategy_name}", log_context.with_indent(1))
            
            if strategy.can_resolve(name, context):
                result = strategy.resolve(name, context)
                if result and self._validate_resolution(result):
                    log_trace(f"SUCCESS {strategy_name} succeeded: {name} -> {result}", log_context.with_indent(1))
                    log_trace(f"VALIDATION PASS Resolution validated", log_context.with_indent(1))
                    return result
                else:
                    log_trace(f"FAIL {strategy_name} failed validation", log_context.with_indent(1))
            else:
                log_trace(f"SKIP {strategy_name} cannot resolve", log_context.with_indent(1))
        
        log_trace(f"FAILED All strategies failed for: {name}", log_context)
        return None
    
    def _resolve_chain(self, name_parts: List[str], context: Dict[str, Any]) -> Optional[str]:
        """Resolve complex attribute chains with enhanced attribute support."""
        log_context = create_context("resolver", AnalysisPhase.ANALYSIS, "_resolve_chain")
        
        # Resolve base
        base_name = name_parts[0]
        log_trace(f"Resolving base: {base_name}", log_context)
        
        base_fqn = self._resolve_simple(base_name, context)
        if not base_fqn:
            log_trace(f"FAILED to resolve base: {base_name}", log_context)
            return None
        
        log_trace(f"Base resolved: {base_name} -> {base_fqn}", log_context)
        
        # Walk the chain
        current_fqn = base_fqn
        for i, attr in enumerate(name_parts[1:], 1):
            log_trace(f"Step {i}: Resolving {current_fqn}.{attr}", log_context.with_indent(1))
            current_fqn = self._resolve_attribute(current_fqn, attr, context)
            if not current_fqn:
                log_trace(f"FAILED at step {i}: .{attr}", log_context.with_indent(1))
                return None
            log_trace(f"Step {i} resolved: {current_fqn}", log_context.with_indent(1))
        
        return current_fqn
    
    def _resolve_attribute(self, context_fqn: str, attr: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve attribute in context of given FQN with inheritance, attribute support, and external library support."""
        candidate = f"{context_fqn}.{attr}"
        log_context = create_context("resolver", AnalysisPhase.ANALYSIS, "_resolve_attribute")
        log_trace(f"Resolving attribute: {context_fqn}.{attr}", log_context)
        
        # Check if context is a state variable - resolve through its type
        if context_fqn in self.recon_data["state"]:
            log_trace(f"Context is state variable, resolving through type", log_context.with_indent(1))
            state_type = self._get_state_type(context_fqn)
            if state_type:
                log_trace(f"State type resolved: {state_type}", log_context.with_indent(1))
                return self._resolve_attribute(state_type, attr, context)
            else:
                log_trace(f"Could not resolve state type", log_context.with_indent(1))
        
        # Check if context is an internal class - look for methods and attributes with inheritance
        if context_fqn in self.recon_data["classes"]:
            log_trace(f"Context is internal class, checking for method/attribute", log_context.with_indent(1))
            
            # First check direct method
            if candidate in self.recon_data["functions"]:
                log_trace(f"SUCCESS Found direct method: {candidate}", log_context.with_indent(1))
                return candidate
            
            # Check for class attribute
            class_info = self.recon_data["classes"][context_fqn]
            class_attributes = class_info.get("attributes", {})
            if attr in class_attributes:
                attr_type = class_attributes[attr].get("type")
                if attr_type and attr_type != "Unknown":
                    log_trace(f"SUCCESS Found class attribute: {attr} of type {attr_type}", log_context.with_indent(1))
                    # Resolve the attribute type to its FQN
                    resolved_type = self._resolve_attribute_type(attr_type, context)
                    if resolved_type:
                        log_trace(f"Attribute type resolved to: {resolved_type}", log_context.with_indent(1))
                        return resolved_type
                    else:
                        log_trace(f"Could not resolve attribute type: {attr_type}", log_context.with_indent(1))
            
            # Then check inheritance chain
            log_trace(f"Checking inheritance for method/attribute", log_context.with_indent(1))
            inherited_result = self._resolve_inherited_method_or_attribute(context_fqn, attr, context)
            if inherited_result:
                log_trace(f"SUCCESS Found in inheritance chain: {inherited_result}", log_context.with_indent(1))
                return inherited_result
            
            log_trace(f"Method/attribute not found in class or inheritance chain: {candidate}", log_context.with_indent(1))
        
        # Check if context is an external class
        elif context_fqn in self.recon_data.get("external_classes", {}):
            log_trace(f"Context is external class, checking for common methods", log_context.with_indent(1))
            
            # For external classes, we assume common methods exist
            external_method_fqn = f"{context_fqn}.{attr}"
            
            # Special handling for known external library patterns
            if self._is_known_external_method(context_fqn, attr):
                log_trace(f"SUCCESS Found known external method: {external_method_fqn}", log_context.with_indent(1))
                return external_method_fqn
            else:
                log_trace(f"Assuming external method exists: {external_method_fqn}", log_context.with_indent(1))
                return external_method_fqn
        
        # Check if context is a function - use return type
        if (context_fqn in self.recon_data["functions"] or 
            context_fqn in self.recon_data.get("external_functions", {})):
            log_trace(f"Context is function, using return type", log_context.with_indent(1))
            
            func_info = None
            if context_fqn in self.recon_data["functions"]:
                func_info = self.recon_data["functions"][context_fqn]
            elif context_fqn in self.recon_data.get("external_functions", {}):
                func_info = self.recon_data["external_functions"][context_fqn]
            
            if func_info:
                return_type = func_info.get("return_type")
                if return_type:
                    log_trace(f"Function return type: {return_type}", log_context.with_indent(1))
                    type_inference = context.get('type_inference')
                    if type_inference:
                        core_type = type_inference.extract_core_type(return_type)
                        if core_type:
                            log_trace(f"Core type extracted: {core_type}", log_context.with_indent(1))
                            resolved_type = self._resolve_type_name(core_type, context)
                            if resolved_type:
                                log_trace(f"Type name resolved: {resolved_type}", log_context.with_indent(1))
                                return self._resolve_attribute(resolved_type, attr, context)
                            else:
                                log_trace(f"Could not resolve type name", log_context.with_indent(1))
                        else:
                            log_trace(f"Could not extract core type", log_context.with_indent(1))
                    else:
                        log_trace(f"No type inference engine available", log_context.with_indent(1))
                else:
                    log_trace(f"Function has no return type", log_context.with_indent(1))
        
        # Direct resolution
        if self._validate_resolution(candidate):
            log_trace(f"SUCCESS Direct resolution successful: {candidate}", log_context.with_indent(1))
            return candidate
        
        log_trace(f"FAILED All resolution attempts failed", log_context.with_indent(1))
        return None
    
    def _is_known_external_method(self, class_fqn: str, method_name: str) -> bool:
        """Check if this is a known method of an external class."""
        # SocketIO specific methods
        if 'SocketIO' in class_fqn and method_name in ['emit', 'on', 'send', 'disconnect']:
            return True
        
        # Threading specific methods  
        if 'threading' in class_fqn and method_name in ['start', 'join', 'acquire', 'release']:
            return True
        
        # Common object methods
        if method_name in ['__init__', '__str__', '__repr__', '__call__']:
            return True
        
        return False
    
    def _resolve_inherited_method_or_attribute(self, class_fqn: str, attr_name: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve method or attribute through inheritance chain."""
        log_context = create_context("resolver", AnalysisPhase.ANALYSIS, "_resolve_inherited")
        log_trace(f"Checking inheritance chain for {class_fqn}.{attr_name}", log_context)
        
        if class_fqn not in self.recon_data["classes"]:
            log_trace(f"Class {class_fqn} not found in catalog", log_context.with_indent(1))
            return None
        
        class_info = self.recon_data["classes"][class_fqn]
        parents = class_info.get("parents", [])
        
        log_trace(f"Parents of {class_fqn}: {parents}", log_context.with_indent(1))
        
        for parent_fqn in parents:
            # Check for method in parent
            method_candidate = f"{parent_fqn}.{attr_name}"
            log_trace(f"Checking parent method: {method_candidate}", log_context.with_indent(1))
            
            if method_candidate in self.recon_data["functions"]:
                log_trace(f"SUCCESS Found inherited method: {method_candidate}", log_context.with_indent(1))
                return method_candidate
            
            # Check for attribute in parent
            if parent_fqn in self.recon_data["classes"]:
                parent_info = self.recon_data["classes"][parent_fqn]
                parent_attributes = parent_info.get("attributes", {})
                if attr_name in parent_attributes:
                    attr_type = parent_attributes[attr_name].get("type")
                    if attr_type and attr_type != "Unknown":
                        log_trace(f"SUCCESS Found inherited attribute: {attr_name} of type {attr_type}", log_context.with_indent(1))
                        resolved_type = self._resolve_attribute_type(attr_type, context)
                        if resolved_type:
                            return resolved_type
            
            # Recursive check up the inheritance chain
            inherited = self._resolve_inherited_method_or_attribute(parent_fqn, attr_name, context)
            if inherited:
                log_trace(f"SUCCESS Found in grandparent: {inherited}", log_context.with_indent(1))
                return inherited
        
        log_trace(f"Method/attribute {attr_name} not found in inheritance chain", log_context.with_indent(1))
        return None
    
    def _resolve_attribute_type(self, attr_type: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve attribute type string to FQN, including external classes."""
        # Handle simple class names
        if "." not in attr_type:
            current_module = context.get('current_module', '')
            candidate = f"{current_module}.{attr_type}"
            
            # Check internal classes first
            if candidate in self.recon_data["classes"]:
                return candidate
            
            # Check external classes
            for ext_class_fqn in self.recon_data.get("external_classes", {}):
                if ext_class_fqn.endswith(f".{attr_type}"):
                    return ext_class_fqn
            
            # Search all internal classes for matching name
            for class_fqn in self.recon_data["classes"]:
                if class_fqn.endswith(f".{attr_type}"):
                    return class_fqn
        
        # Handle already qualified names or complex expressions
        if attr_type in self.recon_data["classes"]:
            return attr_type
        
        if attr_type in self.recon_data.get("external_classes", {}):
            return attr_type
        
        # For complex expressions like "SAMPLE_RATES.get", return as-is
        # This will be handled by state variable resolution
        return attr_type
    
    def _get_state_type(self, state_fqn: str) -> Optional[str]:
        """Get type of state variable."""
        if state_fqn not in self.recon_data["state"]:
            return None
        
        state_info = self.recon_data["state"][state_fqn]
        type_value = state_info.get("type")
        
        if not type_value:
            return None
        
        # Handle inferred types
        if state_info.get("inferred_from_value"):
            module_name = state_fqn.rsplit(".", 1)[0]
            if "." not in type_value:
                candidate = f"{module_name}.{type_value}"
                if (candidate in self.recon_data["classes"] or 
                    candidate in self.recon_data.get("external_classes", {})):
                    return candidate
        
        return type_value
    
    def _resolve_type_name(self, type_name: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve type name to FQN."""
        current_module = context.get('current_module', '')
        
        # Try current module first
        candidate = f"{current_module}.{type_name}"
        if candidate in self.recon_data["classes"]:
            return candidate
        
        # Search all internal classes
        for class_fqn in self.recon_data["classes"]:
            if class_fqn.endswith(f".{type_name}"):
                return class_fqn
        
        # Search external classes
        for class_fqn in self.recon_data.get("external_classes", {}):
            if class_fqn.endswith(f".{type_name}"):
                return class_fqn
        
        return None
    
    def _validate_resolution(self, fqn: str) -> bool:
        """Validate that resolved FQN exists in reconnaissance data (including external libraries)."""
        exists = (fqn in self.recon_data["classes"] or 
                 fqn in self.recon_data["functions"] or 
                 fqn in self.recon_data["state"] or
                 fqn in self.recon_data.get("external_classes", {}) or
                 fqn in self.recon_data.get("external_functions", {}))
        
        log_context = create_context("resolver", AnalysisPhase.ANALYSIS, "_validate_resolution")
        log_trace(f"Checking {fqn}: {'EXISTS' if exists else 'NOT_FOUND'}", log_context)
        return exists
    
    def extract_name_parts(self, node: ast.AST) -> Optional[List[str]]:
        """Extract name parts from AST node."""
        if isinstance(node, ast.Name):
            return [node.id]
        elif isinstance(node, ast.Attribute):
            parts = self.extract_name_parts(node.value)
            return parts + [node.attr] if parts else None
        elif isinstance(node, ast.Call):
            return self.extract_name_parts(node.func)
        return None
