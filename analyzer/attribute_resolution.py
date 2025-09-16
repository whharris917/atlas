"""
Attribute resolution functions for name resolution.

These functions handle resolving attributes in different contexts including
inheritance, state variables, external classes, and type resolution.

**REWRITTEN FOR CLARITY AND MODULARITY**
"""

from typing import Dict, Any, Optional
from .logger import LogLevel, get_logger
from .utils import get_source
from .validation import validate_resolution, is_known_external_method


def resolve_attribute(
    context_fqn: str, 
    attr: str, 
    recon_data: Dict[str, Any], 
    current_module: str, 
    type_inference=None
) -> Optional[str]:
    """
    Resolve an attribute based on the FQN of its context.

    This function acts as a dispatcher, determining the type of the context
    (e.g., class, function, state variable) and delegating to the
    appropriate specialized resolution helper.
    """
    _log_trace(f"Resolving attribute: {context_fqn}.{attr}",
               {'context_fqn': context_fqn, 'attr': attr})

    # Scenario 1: The context is an internal class.
    if context_fqn in recon_data.get("classes", {}):
        return _resolve_from_class(context_fqn, attr, recon_data, current_module)

    # Scenario 2: The context is an external class.
    if context_fqn in recon_data.get("external_classes", {}):
        return _resolve_from_external_class(context_fqn, attr)

    # Scenario 3: The context is a function (internal or external).
    if (context_fqn in recon_data.get("functions", {}) or 
        context_fqn in recon_data.get("external_functions", {})):
        return _resolve_from_function(context_fqn, attr, recon_data, current_module, type_inference)

    # Scenario 4: The context is a module-level state variable.
    if context_fqn in recon_data.get("state", {}):
        return _resolve_from_state(context_fqn, attr, recon_data, current_module, type_inference)

    # Fallback: Attempt a direct resolution (e.g., for sub-modules).
    candidate = f"{context_fqn}.{attr}"
    if validate_resolution(candidate, recon_data):
        _log_trace(f"Direct resolution successful: {candidate}",
                   {'candidate': candidate, 'resolution_type': 'direct'})
        return candidate

    _log_trace("All attribute resolution attempts failed",
               {'context_fqn': context_fqn, 'attr': attr})
    return None

# --- Specialized Helper Functions ---

def _resolve_from_class(
    class_fqn: str, 
    attr: str, 
    recon_data: Dict[str, Any], 
    current_module: str
) -> Optional[str]:
    """Handle attribute resolution when the context is an internal class."""
    _log_trace("Context is internal class, checking for method/attribute", {'class_fqn': class_fqn})
    
    # Check for a direct method on the class.
    method_candidate = f"{class_fqn}.{attr}"
    if method_candidate in recon_data.get("functions", {}):
        _log_trace(f"Found direct method: {method_candidate}", {'method_fqn': method_candidate})
        return method_candidate

    # Check for a direct attribute on the class.
    class_info = recon_data["classes"][class_fqn]
    if attr in class_info.get("attributes", {}):
        attr_type = class_info["attributes"][attr].get("type", "Unknown")
        _log_trace(f"Found class attribute '{attr}' with type '{attr_type}'", {'attr_type': attr_type})
        # Return the FQN of the attribute's type.
        return _resolve_type_name(attr_type, recon_data, current_module)
        
    # If not found directly, search the inheritance hierarchy.
    _log_trace("Method/attribute not found directly, checking inheritance chain", {'class_fqn': class_fqn})
    return _resolve_inherited_attribute(class_fqn, attr, recon_data, current_module)

def _resolve_from_external_class(class_fqn: str, attr: str) -> Optional[str]:
    """Handle attribute resolution when the context is an external class."""
    _log_trace("Context is external class, assuming method exists", {'external_class_fqn': class_fqn})
    
    # For external classes, we optimistically assume the method exists.
    # We can add special validation for known library patterns.
    external_method_fqn = f"{class_fqn}.{attr}"
    if is_known_external_method(class_fqn, attr):
        _log_trace(f"Found known external method: {external_method_fqn}", {'known_method': True})
    else:
        _log_trace(f"Assuming external method exists: {external_method_fqn}", {'assumed': True})
        
    return external_method_fqn

def _resolve_from_function(
    func_fqn: str, 
    attr: str, 
    recon_data: Dict[str, Any], 
    current_module: str, 
    type_inference
) -> Optional[str]:
    """Handle attribute resolution when the context is a function call."""
    _log_trace("Context is a function, resolving through its return type", {'function_fqn': func_fqn})
    
    # Get the function's metadata from the appropriate catalog.
    func_info = (recon_data.get("functions", {}).get(func_fqn) or 
                 recon_data.get("external_functions", {}).get(func_fqn))

    if not func_info or not func_info.get("return_type"):
        _log_trace("Function has no return type information", {'function_fqn': func_fqn})
        return None

    return_type_str = func_info["return_type"]
    _log_trace(f"Function return type: {return_type_str}", {'return_type': return_type_str})
    
    # Use the type inference engine to clean the type string (e.g., 'Optional[Client]' -> 'Client').
    core_type = type_inference.extract_core_type(return_type_str) if type_inference else return_type_str
    if not core_type:
        return None
        
    # Resolve the return type string (e.g., 'Client') to its FQN (e.g., 'services.Client').
    resolved_type_fqn = _resolve_type_name(core_type, recon_data, current_module)
    if not resolved_type_fqn:
        _log_trace("Could not resolve the function's return type to an FQN", {'core_type': core_type})
        return None
        
    # CRITICAL: Recursively call the main resolver with the *return type* as the new context.
    _log_trace("Pivoting resolution to the function's return type", {'new_context': resolved_type_fqn})
    return resolve_attribute(resolved_type_fqn, attr, recon_data, current_module, type_inference)

def _resolve_from_state(
    state_fqn: str, 
    attr: str, 
    recon_data: Dict[str, Any], 
    current_module: str, 
    type_inference
) -> Optional[str]:
    """Handle attribute resolution when the context is a module-level state variable."""
    _log_trace("Context is a state variable, resolving through its type", {'state_fqn': state_fqn})
    
    state_info = recon_data.get("state", {}).get(state_fqn)
    if not state_info or not state_info.get("type"):
        _log_trace("State variable has no type information", {'state_fqn': state_fqn})
        return None

    # Resolve the state variable's type string to its FQN.
    type_name = state_info["type"]
    resolved_type_fqn = _resolve_type_name(type_name, recon_data, current_module)
    if not resolved_type_fqn:
        _log_trace("Could not resolve the state variable's type to an FQN", {'type_name': type_name})
        return None
        
    # CRITICAL: Recursively call the main resolver with the *variable's type* as the new context.
    _log_trace("Pivoting resolution to the state variable's type", {'new_context': resolved_type_fqn})
    return resolve_attribute(resolved_type_fqn, attr, recon_data, current_module, type_inference)

# --- Inheritance and Type Resolution Helpers ---

def _resolve_inherited_attribute(
    class_fqn: str, 
    attr: str, 
    recon_data: Dict[str, Any], 
    current_module: str
) -> Optional[str]:
    """Recursively search the inheritance chain for a method or attribute."""
    class_info = recon_data.get("classes", {}).get(class_fqn, {})
    
    # Iterate through parent classes in the order they are defined (respecting MRO).
    for parent_fqn in class_info.get("parents", []):
        _log_trace(f"Searching for '{attr}' in parent: {parent_fqn}", {'parent_fqn': parent_fqn})
        
        # Check if the attribute is defined on the parent itself.
        found_on_parent = _resolve_from_class(parent_fqn, attr, recon_data, current_module)
        if found_on_parent:
            _log_trace(f"Found '{attr}' in parent class {parent_fqn}", {'found_fqn': found_on_parent})
            return found_on_parent
            
    _log_trace(f"Attribute '{attr}' not found in inheritance chain for {class_fqn}", {'class_fqn': class_fqn})
    return None

def _resolve_type_name(
    type_name: str, 
    recon_data: Dict[str, Any], 
    current_module: str
) -> Optional[str]:
    """Resolve a simple type name (e.g., 'Client') to its full FQN."""
    if not type_name or type_name == "Unknown":
        return None

    # If the name is already an FQN, just validate it.
    if "." in type_name:
        if (type_name in recon_data.get("classes", {}) or 
            type_name in recon_data.get("external_classes", {})):
            return type_name

    # Check for a class with this name in the current module.
    candidate = f"{current_module}.{type_name}"
    if candidate in recon_data.get("classes", {}):
        return candidate
    
    # Search all internal and external classes for a matching name.
    for catalog_name in ["classes", "external_classes"]:
        for fqn in recon_data.get(catalog_name, {}):
            if fqn.endswith(f".{type_name}"):
                return fqn
    
    # Return the original name as a last resort if it might be a state variable itself.
    if f"{current_module}.{type_name}" in recon_data.get("state", {}):
        return f"{current_module}.{type_name}"

    return None

def _log_trace(message: str, extra: Optional[Dict[str, Any]] = None):
    """Helper function for trace logging."""
    get_logger().trace(message, get_source(), extra or {})