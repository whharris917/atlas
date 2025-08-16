"""
Name Resolution Engine - Code Atlas

Contains the core NameResolver and its associated strategies for resolving
names and attribute chains within different contexts.
"""

import ast
from typing import Dict, List, Optional, Any
from .utils import LOG_LEVEL


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
        if LOG_LEVEL >= 3:
            print(f"      [STRATEGY] LocalVariableStrategy.can_resolve({base_name}): {can_resolve}")
        return can_resolve
    
    def resolve(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        symbol_manager = context['symbol_manager']
        result = symbol_manager.get_variable_type(base_name)
        if LOG_LEVEL >= 3:
            print(f"      [STRATEGY] LocalVariableStrategy.resolve({base_name}): {result}")
        return result


class SelfStrategy(ResolutionStrategy):
    """Resolves 'self' references to current class."""
    
    def can_resolve(self, base_name: str, context: Dict[str, Any]) -> bool:
        can_resolve = base_name == "self" and context.get('current_class')
        if LOG_LEVEL >= 3:
            print(f"      [STRATEGY] SelfStrategy.can_resolve({base_name}): {can_resolve}")
        return can_resolve
    
    def resolve(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        result = context['current_class']
        if LOG_LEVEL >= 3:
            print(f"      [STRATEGY] SelfStrategy.resolve({base_name}): {result}")
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
        
        if LOG_LEVEL >= 3:
            print(f"      [STRATEGY] ImportStrategy.can_resolve({base_name}): {can_resolve} (import: {can_resolve_import}, external: {can_resolve_external})")
        return can_resolve
    
    def resolve(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        import_map = context.get('import_map', {})
        
        # First try direct import map
        if base_name in import_map:
            result = import_map[base_name]
            if LOG_LEVEL >= 3:
                print(f"      [STRATEGY] ImportStrategy.resolve({base_name}): {result} (from import map)")
            return result
        
        # Then try external library resolution
        external_result = self._resolve_external(base_name)
        if external_result:
            if LOG_LEVEL >= 3:
                print(f"      [STRATEGY] ImportStrategy.resolve({base_name}): {external_result} (external)")
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
        if LOG_LEVEL >= 3:
            print(f"      [STRATEGY] ModuleStrategy.can_resolve({base_name}): True (fallback)")
        return True  # Always can try this as fallback
    
    def resolve(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        current_module = context.get('current_module', '')
        result = f"{current_module}.{base_name}"
        if LOG_LEVEL >= 3:
            print(f"      [STRATEGY] ModuleStrategy.resolve({base_name}): {result}")
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
            print("    [RESOLVE] FAILED No name parts provided")
            return None
        
        if LOG_LEVEL >= 2:
            print(f"    [RESOLVE] Attempting to resolve: {name_parts}")
        
        # Layer 1: Simple resolution for single names
        if len(name_parts) == 1:
            result = self._resolve_simple(name_parts[0], context)
            if result:
                if LOG_LEVEL >= 1:
                    print(f"    [RESOLVE] RESOLVED to: {result}")
            else:
                if LOG_LEVEL >= 1:
                    print(f"    [RESOLVE] FAILED to resolve: {name_parts[0]}")
            return result
        
        # Layer 2: Complex chain resolution
        if LOG_LEVEL >= 2:
            print(f"    [RESOLVE] Chain resolution needed for: {name_parts}")
        result = self._resolve_chain(name_parts, context)
        if result:
            if LOG_LEVEL >= 1:
                print(f"    [RESOLVE] RESOLVED to: {result}")
        else:
            print(f"    [RESOLVE] FAILED to resolve chain: {'.'.join(name_parts)}")
        return result
    
    def _resolve_simple(self, name: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve simple single name using strategies."""
        print(f"      [RESOLVE_SIMPLE] Resolving base: {name}")
        
        for i, strategy in enumerate(self.strategies):
            strategy_name = strategy.__class__.__name__
            print(f"      [STRATEGY] Trying strategy {i+1}: {strategy_name}")
            
            if strategy.can_resolve(name, context):
                result = strategy.resolve(name, context)
                if result and self._validate_resolution(result):
                    print(f"      [STRATEGY] SUCCESS {strategy_name} succeeded: {name} -> {result}")
                    print(f"      [VALIDATION] PASS Resolution validated")
                    return result
                else:
                    print(f"      [STRATEGY] FAIL {strategy_name} failed validation")
            else:
                print(f"      [STRATEGY] SKIP {strategy_name} cannot resolve")
        
        print(f"      [RESOLVE_SIMPLE] FAILED All strategies failed for: {name}")
        return None
    
    def _resolve_chain(self, name_parts: List[str], context: Dict[str, Any]) -> Optional[str]:
        """Resolve complex attribute chains with enhanced attribute support."""
        # Resolve base
        base_name = name_parts[0]
        print(f"      [CHAIN] Resolving base: {base_name}")
        
        base_fqn = self._resolve_simple(base_name, context)
        if not base_fqn:
            print(f"      [CHAIN] FAILED to resolve base: {base_name}")
            return None
        
        print(f"      [CHAIN] Base resolved: {base_name} -> {base_fqn}")
        
        # Walk the chain
        current_fqn = base_fqn
        for i, attr in enumerate(name_parts[1:], 1):
            print(f"      [CHAIN] Step {i}: Resolving {current_fqn}.{attr}")
            current_fqn = self._resolve_attribute(current_fqn, attr, context)
            if not current_fqn:
                print(f"      [CHAIN] FAILED at step {i}: .{attr}")
                return None
            print(f"      [CHAIN] Step {i} resolved: {current_fqn}")
        
        return current_fqn
    
    def _resolve_attribute(self, context_fqn: str, attr: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve attribute in context of given FQN with inheritance, attribute support, and external library support."""
        candidate = f"{context_fqn}.{attr}"
        print(f"        [ATTRIBUTE] Resolving attribute: {context_fqn}.{attr}")
        
        # Check if context is a state variable - resolve through its type
        if context_fqn in self.recon_data["state"]:
            print(f"        [ATTRIBUTE] Context is state variable, resolving through type")
            state_type = self._get_state_type(context_fqn)
            if state_type:
                print(f"        [ATTRIBUTE] State type resolved: {state_type}")
                return self._resolve_attribute(state_type, attr, context)
            else:
                print(f"        [ATTRIBUTE] Could not resolve state type")
        
        # Check if context is an internal class - look for methods and attributes with inheritance
        if context_fqn in self.recon_data["classes"]:
            print(f"        [ATTRIBUTE] Context is internal class, checking for method/attribute")
            
            # First check direct method
            if candidate in self.recon_data["functions"]:
                print(f"        [ATTRIBUTE] SUCCESS Found direct method: {candidate}")
                return candidate
            
            # Check for class attribute
            class_info = self.recon_data["classes"][context_fqn]
            class_attributes = class_info.get("attributes", {})
            if attr in class_attributes:
                attr_type = class_attributes[attr].get("type")
                if attr_type and attr_type != "Unknown":
                    print(f"        [ATTRIBUTE] SUCCESS Found class attribute: {attr} of type {attr_type}")
                    # Resolve the attribute type to its FQN
                    resolved_type = self._resolve_attribute_type(attr_type, context)
                    if resolved_type:
                        print(f"        [ATTRIBUTE] Attribute type resolved to: {resolved_type}")
                        return resolved_type
                    else:
                        print(f"        [ATTRIBUTE] Could not resolve attribute type: {attr_type}")
            
            # Then check inheritance chain
            print(f"        [ATTRIBUTE] Checking inheritance for method/attribute")
            inherited_result = self._resolve_inherited_method_or_attribute(context_fqn, attr, context)
            if inherited_result:
                print(f"        [ATTRIBUTE] SUCCESS Found in inheritance chain: {inherited_result}")
                return inherited_result
            
            print(f"        [ATTRIBUTE] Method/attribute not found in class or inheritance chain: {candidate}")
        
        # Check if context is an external class
        elif context_fqn in self.recon_data.get("external_classes", {}):
            print(f"        [ATTRIBUTE] Context is external class, checking for common methods")
            
            # For external classes, we assume common methods exist
            external_method_fqn = f"{context_fqn}.{attr}"
            
            # Special handling for known external library patterns
            if self._is_known_external_method(context_fqn, attr):
                print(f"        [ATTRIBUTE] SUCCESS Found known external method: {external_method_fqn}")
                return external_method_fqn
            else:
                print(f"        [ATTRIBUTE] Assuming external method exists: {external_method_fqn}")
                return external_method_fqn
        
        # Check if context is a function - use return type
        if (context_fqn in self.recon_data["functions"] or 
            context_fqn in self.recon_data.get("external_functions", {})):
            print(f"        [ATTRIBUTE] Context is function, using return type")
            
            func_info = None
            if context_fqn in self.recon_data["functions"]:
                func_info = self.recon_data["functions"][context_fqn]
            elif context_fqn in self.recon_data.get("external_functions", {}):
                func_info = self.recon_data["external_functions"][context_fqn]
            
            if func_info:
                return_type = func_info.get("return_type")
                if return_type:
                    print(f"        [ATTRIBUTE] Function return type: {return_type}")
                    type_inference = context.get('type_inference')
                    if type_inference:
                        core_type = type_inference.extract_core_type(return_type)
                        if core_type:
                            print(f"        [ATTRIBUTE] Core type extracted: {core_type}")
                            resolved_type = self._resolve_type_name(core_type, context)
                            if resolved_type:
                                print(f"        [ATTRIBUTE] Type name resolved: {resolved_type}")
                                return self._resolve_attribute(resolved_type, attr, context)
                            else:
                                print(f"        [ATTRIBUTE] Could not resolve type name")
                        else:
                            print(f"        [ATTRIBUTE] Could not extract core type")
                    else:
                        print(f"        [ATTRIBUTE] No type inference engine available")
                else:
                    print(f"        [ATTRIBUTE] Function has no return type")
        
        # Direct resolution
        if self._validate_resolution(candidate):
            print(f"        [ATTRIBUTE] SUCCESS Direct resolution successful: {candidate}")
            return candidate
        
        print(f"        [ATTRIBUTE] FAILED All resolution attempts failed")
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
        print(f"        [INHERITANCE] Checking inheritance chain for {class_fqn}.{attr_name}")
        
        if class_fqn not in self.recon_data["classes"]:
            print(f"        [INHERITANCE] Class {class_fqn} not found in catalog")
            return None
        
        class_info = self.recon_data["classes"][class_fqn]
        parents = class_info.get("parents", [])
        
        print(f"        [INHERITANCE] Parents of {class_fqn}: {parents}")
        
        for parent_fqn in parents:
            # Check for method in parent
            method_candidate = f"{parent_fqn}.{attr_name}"
            print(f"        [INHERITANCE] Checking parent method: {method_candidate}")
            
            if method_candidate in self.recon_data["functions"]:
                print(f"        [INHERITANCE] SUCCESS Found inherited method: {method_candidate}")
                return method_candidate
            
            # Check for attribute in parent
            if parent_fqn in self.recon_data["classes"]:
                parent_info = self.recon_data["classes"][parent_fqn]
                parent_attributes = parent_info.get("attributes", {})
                if attr_name in parent_attributes:
                    attr_type = parent_attributes[attr_name].get("type")
                    if attr_type and attr_type != "Unknown":
                        print(f"        [INHERITANCE] SUCCESS Found inherited attribute: {attr_name} of type {attr_type}")
                        resolved_type = self._resolve_attribute_type(attr_type, context)
                        if resolved_type:
                            return resolved_type
            
            # Recursive check up the inheritance chain
            inherited = self._resolve_inherited_method_or_attribute(parent_fqn, attr_name, context)
            if inherited:
                print(f"        [INHERITANCE] SUCCESS Found in grandparent: {inherited}")
                return inherited
        
        print(f"        [INHERITANCE] Method/attribute {attr_name} not found in inheritance chain")
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
        print(f"        [VALIDATION] Checking {fqn}: {'EXISTS' if exists else 'NOT_FOUND'}")
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
