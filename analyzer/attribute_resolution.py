"""
Attribute resolution functions for name resolution.

These functions handle resolving attributes in different contexts including
inheritance, state variables, external classes, and type resolution.
"""

from typing import Dict, Any, Optional
from .logger import LogLevel, get_logger
from .utils import get_source
from .validation import validate_resolution, is_known_external_method


def resolve_attribute(context_fqn: str, attr: str, recon_data: Dict[str, Any], 
                     current_module: str, type_inference=None) -> Optional[str]:
    """
    Resolve attribute in context of given FQN with inheritance, attribute support, and external library support.
    
    Args:
        context_fqn: Fully qualified name of the context (class, function, state var)
        attr: Attribute name to resolve
        recon_data: Reconnaissance data
        current_module: Current module context
        type_inference: Type inference engine (optional)
        
    Returns:
        Resolved FQN of the attribute, or None if not found
    """
    candidate = f"{context_fqn}.{attr}"
    _log_trace(f"Resolving attribute: {context_fqn}.{attr}",
               {'context_fqn': context_fqn, 'attr': attr, 'candidate': candidate})
    
    # Check if context is a state variable - resolve through its type
    if context_fqn in recon_data["state"]:
        _log_trace("Context is state variable, resolving through type",
                   {'context_fqn': context_fqn, 'resolution_method': 'state_type'})
        state_type = get_state_type(context_fqn, recon_data)
        if state_type:
            _log_trace(f"State type resolved: {state_type}",
                       {'state_fqn': context_fqn, 'state_type': state_type})
            return resolve_attribute(state_type, attr, recon_data, current_module, type_inference)
        else:
            _log_trace("Could not resolve state type", {'state_fqn': context_fqn})
    
    # Check if context is an internal class - look for methods and attributes with inheritance
    if context_fqn in recon_data["classes"]:
        _log_trace("Context is internal class, checking for method/attribute",
                   {'class_fqn': context_fqn, 'resolution_method': 'class_member'})
        
        # First check direct method
        if candidate in recon_data["functions"]:
            _log_trace(f"Found direct method: {candidate}",
                       {'method_fqn': candidate, 'resolution_type': 'direct_method'})
            return candidate
        
        # Check for class attribute
        class_info = recon_data["classes"][context_fqn]
        class_attributes = class_info.get("attributes", {})
        if attr in class_attributes:
            attr_type = class_attributes[attr].get("type")
            if attr_type and attr_type != "Unknown":
                _log_trace(f"Found class attribute: {attr} of type {attr_type}",
                           {'class_fqn': context_fqn, 'attr': attr, 'attr_type': attr_type})
                # Resolve the attribute type to its FQN
                resolved_type = resolve_attribute_type(attr_type, recon_data, current_module)
                if resolved_type:
                    _log_trace(f"Attribute type resolved to: {resolved_type}",
                               {'attr_type': attr_type, 'resolved_type': resolved_type})
                    return resolved_type
                else:
                    _log_trace(f"Could not resolve attribute type: {attr_type}",
                               {'attr_type': attr_type})
        
        # Then check inheritance chain
        _log_trace("Checking inheritance for method/attribute",
                   {'class_fqn': context_fqn, 'attr': attr})
        inherited_result = resolve_inherited_method_or_attribute(context_fqn, attr, recon_data, current_module)
        if inherited_result:
            _log_trace(f"Found in inheritance chain: {inherited_result}",
                       {'class_fqn': context_fqn, 'attr': attr, 'inherited_result': inherited_result})
            return inherited_result
        
        _log_trace("Method/attribute not found in class or inheritance chain",
                   {'class_fqn': context_fqn, 'attr': attr, 'candidate': candidate})
    
    # Check if context is an external class
    elif context_fqn in recon_data.get("external_classes", {}):
        _log_trace("Context is external class, checking for common methods",
                   {'external_class_fqn': context_fqn, 'attr': attr})
        
        # For external classes, we assume common methods exist
        external_method_fqn = f"{context_fqn}.{attr}"
        
        # Special handling for known external library patterns
        if is_known_external_method(context_fqn, attr):
            _log_trace(f"Found known external method: {external_method_fqn}",
                       {'external_method': external_method_fqn, 'known_method': True})
            return external_method_fqn
        else:
            _log_trace(f"Assuming external method exists: {external_method_fqn}",
                       {'external_method': external_method_fqn, 'assumed': True})
            return external_method_fqn
    
    # Check if context is a function - use return type
    if (context_fqn in recon_data["functions"] or 
        context_fqn in recon_data.get("external_functions", {})):
        _log_trace("Context is function, using return type",
                   {'function_fqn': context_fqn, 'resolution_method': 'return_type'})
        
        func_info = None
        if context_fqn in recon_data["functions"]:
            func_info = recon_data["functions"][context_fqn]
        elif context_fqn in recon_data.get("external_functions", {}):
            func_info = recon_data["external_functions"][context_fqn]
        
        if func_info:
            return_type = func_info.get("return_type")
            if return_type:
                _log_trace(f"Function return type: {return_type}",
                           {'function_fqn': context_fqn, 'return_type': return_type})
                
                if type_inference:
                    core_type = type_inference.extract_core_type(return_type)
                    if core_type:
                        _log_trace(f"Core type extracted: {core_type}",
                                   {'return_type': return_type, 'core_type': core_type})
                        resolved_type = resolve_type_name(core_type, recon_data, current_module)
                        if resolved_type:
                            _log_trace(f"Type name resolved: {resolved_type}",
                                       {'core_type': core_type, 'resolved_type': resolved_type})
                            return resolve_attribute(resolved_type, attr, recon_data, current_module, type_inference)
                        else:
                            _log_trace("Could not resolve type name", {'core_type': core_type})
                    else:
                        _log_trace("Could not extract core type", {'return_type': return_type})
                else:
                    _log_trace("No type inference engine available", {'function_fqn': context_fqn})
            else:
                _log_trace("Function has no return type", {'function_fqn': context_fqn})
    
    # Direct resolution
    if validate_resolution(candidate, recon_data):
        _log_trace(f"Direct resolution successful: {candidate}",
                   {'candidate': candidate, 'resolution_type': 'direct'})
        return candidate
    
    _log_trace("All attribute resolution attempts failed",
               {'context_fqn': context_fqn, 'attr': attr})
    return None


def resolve_inherited_method_or_attribute(class_fqn: str, attr_name: str, 
                                         recon_data: Dict[str, Any], current_module: str) -> Optional[str]:
    """
    Resolve method or attribute through inheritance chain.
    
    Args:
        class_fqn: Fully qualified name of the class
        attr_name: Name of attribute/method to find
        recon_data: Reconnaissance data
        current_module: Current module context
        
    Returns:
        FQN of inherited method/attribute, or None if not found
    """
    _log_trace(f"Checking inheritance chain for {class_fqn}.{attr_name}",
               {'class_fqn': class_fqn, 'attr_name': attr_name})
    
    if class_fqn not in recon_data["classes"]:
        _log_trace(f"Class {class_fqn} not found in catalog", {'class_fqn': class_fqn})
        return None
    
    class_info = recon_data["classes"][class_fqn]
    parents = class_info.get("parents", [])
    
    _log_trace(f"Parents of {class_fqn}: {parents}",
               {'class_fqn': class_fqn, 'parents': parents})
    
    for parent_fqn in parents:
        # Check for method in parent
        method_candidate = f"{parent_fqn}.{attr_name}"
        _log_trace(f"Checking parent method: {method_candidate}",
                   {'parent_fqn': parent_fqn, 'method_candidate': method_candidate})
        
        if method_candidate in recon_data["functions"]:
            _log_trace(f"Found inherited method: {method_candidate}",
                       {'inherited_method': method_candidate})
            return method_candidate
        
        # Check for attribute in parent
        if parent_fqn in recon_data["classes"]:
            parent_info = recon_data["classes"][parent_fqn]
            parent_attributes = parent_info.get("attributes", {})
            if attr_name in parent_attributes:
                attr_type = parent_attributes[attr_name].get("type")
                if attr_type and attr_type != "Unknown":
                    _log_trace(f"Found inherited attribute: {attr_name} of type {attr_type}",
                               {'parent_fqn': parent_fqn, 'attr_name': attr_name, 'attr_type': attr_type})
                    resolved_type = resolve_attribute_type(attr_type, recon_data, current_module)
                    if resolved_type:
                        return resolved_type
        
        # Recursive check up the inheritance chain
        inherited = resolve_inherited_method_or_attribute(parent_fqn, attr_name, recon_data, current_module)
        if inherited:
            _log_trace(f"Found in grandparent: {inherited}",
                       {'grandparent_result': inherited, 'parent_fqn': parent_fqn})
            return inherited
    
    _log_trace(f"Method/attribute {attr_name} not found in inheritance chain",
               {'class_fqn': class_fqn, 'attr_name': attr_name})
    return None


def resolve_attribute_type(attr_type: str, recon_data: Dict[str, Any], current_module: str) -> Optional[str]:
    """
    Resolve attribute type string to FQN, including external classes.
    
    Args:
        attr_type: Type string to resolve
        recon_data: Reconnaissance data
        current_module: Current module context
        
    Returns:
        Resolved FQN of the type, or the original type if already resolved
    """
    # Handle simple class names
    if "." not in attr_type:
        candidate = f"{current_module}.{attr_type}"
        
        # Check internal classes first
        if candidate in recon_data["classes"]:
            return candidate
        
        # Check external classes
        for ext_class_fqn in recon_data.get("external_classes", {}):
            if ext_class_fqn.endswith(f".{attr_type}"):
                return ext_class_fqn
        
        # Search all internal classes for matching name
        for class_fqn in recon_data["classes"]:
            if class_fqn.endswith(f".{attr_type}"):
                return class_fqn
    
    # Handle already qualified names or complex expressions
    if attr_type in recon_data["classes"]:
        return attr_type
    
    if attr_type in recon_data.get("external_classes", {}):
        return attr_type
    
    # For complex expressions like "SAMPLE_RATES.get", return as-is
    # This will be handled by state variable resolution
    return attr_type


def get_state_type(state_fqn: str, recon_data: Dict[str, Any]) -> Optional[str]:
    """
    Get type of state variable.
    
    Args:
        state_fqn: Fully qualified name of state variable
        recon_data: Reconnaissance data
        
    Returns:
        Type FQN of the state variable, or None if not found
    """
    if state_fqn not in recon_data["state"]:
        return None
    
    state_info = recon_data["state"][state_fqn]
    type_value = state_info.get("type")
    
    if not type_value:
        return None
    
    # Handle inferred types
    if state_info.get("inferred_from_value"):
        module_name = state_fqn.rsplit(".", 1)[0]
        if "." not in type_value:
            candidate = f"{module_name}.{type_value}"
            if (candidate in recon_data["classes"] or 
                candidate in recon_data.get("external_classes", {})):
                return candidate
    
    return type_value


def resolve_type_name(type_name: str, recon_data: Dict[str, Any], current_module: str) -> Optional[str]:
    """
    Resolve type name to FQN.
    
    Args:
        type_name: Type name to resolve
        recon_data: Reconnaissance data
        current_module: Current module context
        
    Returns:
        Resolved FQN of the type, or None if not found
    """
    # Try current module first
    candidate = f"{current_module}.{type_name}"
    if candidate in recon_data["classes"]:
        return candidate
    
    # Search all internal classes
    for class_fqn in recon_data["classes"]:
        if class_fqn.endswith(f".{type_name}"):
            return class_fqn
    
    # Search external classes
    for class_fqn in recon_data.get("external_classes", {}):
        if class_fqn.endswith(f".{type_name}"):
            return class_fqn
    
    return None


def _log_trace(message: str, extra: Dict[str, Any] = None):
    """Helper function for trace logging."""
    getattr(get_logger(), LogLevel.TRACE.name.lower())(message, get_source(), extra or {})
