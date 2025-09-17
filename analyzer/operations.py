"""
Operations for ExpressionTraversal engine.

This module provides the concrete operation classes that implement the 
Expression Traversal workflow. Each operation represents a single step
in analyzing a complex expression, with proper Type Propagation support.

UPDATED: Now uses modern name resolution strategies instead of simple
scope lookups to handle all name types (variables, classes, etc.).
"""

import ast
from typing import Dict, Any, Optional
from dataclasses import dataclass

from .logger import get_logger, LogLevel
from .utils import get_source
from .name_resolution_strategies import NameResolutionEngine


@dataclass
class Operation:
    """Base class for all Expression Traversal operations."""
    
    def execute(self, context_fqn: str, recon_data: Dict[str, Any], scope_manager) -> Optional[str]:
        """
        Execute this operation and return the resulting FQN.
        
        Args:
            context_fqn: The FQN of the current context
            recon_data: Reconnaissance data structure
            scope_manager: Current scope manager instance
            
        Returns:
            FQN of the result, or None if operation fails
        """
        raise NotImplementedError
    
    def _log(self, level: LogLevel, message: str, extra: Optional[Dict[str, Any]] = None):
        """Enhanced logging with automatic source detection."""
        getattr(get_logger(), level.name.lower())(message, get_source(), extra)


@dataclass
class GetName(Operation):
    """
    Operation to resolve a simple name (variable, class, function, etc.).
    
    This operation handles all types of name resolution using the modern
    strategy pattern, not just local variables.
    """
    name: str
    
    def execute(self, context_fqn: str, recon_data: Dict[str, Any], scope_manager) -> Optional[str]:
        """
        Resolve the name using comprehensive name resolution strategies.
        
        This replaces the old scope-only lookup with a complete resolution
        strategy chain that handles variables, classes, external imports, etc.
        """
        self._log(LogLevel.TRACE, f"GetName.execute({self.name})",
                  extra={'operation': 'GetName', 'name': self.name, 'context': context_fqn})
        
        # Use the modern name resolution engine
        resolver = NameResolutionEngine()
        result = resolver.resolve_name(self.name, context_fqn, recon_data, scope_manager)
        
        if result:
            self._log(LogLevel.DEBUG, f"GetName resolved: {self.name} -> {result}",
                      extra={'operation': 'GetName', 'name': self.name, 'result': result})
        else:
            self._log(LogLevel.WARNING, f"GetName failed to resolve: {self.name}",
                      extra={'operation': 'GetName', 'name': self.name, 'context': context_fqn})
        
        return result
    
    def __str__(self):
        return f"GetName('{self.name}')"


@dataclass
class GetAttribute(Operation):
    """
    Operation to resolve an attribute access (e.g., obj.attr).
    
    This operation takes a context FQN (from the previous operation) and
    resolves the specified attribute within that context.
    """
    attr_name: str
    
    def execute(self, context_fqn: str, recon_data: Dict[str, Any], scope_manager) -> Optional[str]:
        """
        Resolve attribute access within the given context.
        
        Args:
            context_fqn: FQN of the object/class containing the attribute
            recon_data: Reconnaissance data structure
            scope_manager: Current scope manager instance
            
        Returns:
            FQN of the attribute, or None if not found
        """
        self._log(LogLevel.TRACE, f"GetAttribute.execute({self.attr_name}) on context: {context_fqn}",
                  extra={'operation': 'GetAttribute', 'attr_name': self.attr_name, 'context': context_fqn})
        
        if not context_fqn:
            self._log(LogLevel.WARNING, f"GetAttribute failed: no context for attribute '{self.attr_name}'",
                      extra={'operation': 'GetAttribute', 'attr_name': self.attr_name})
            return None
        
        result = self._resolve_attribute(context_fqn, self.attr_name, recon_data, scope_manager)
        
        if result:
            self._log(LogLevel.DEBUG, f"GetAttribute resolved: {context_fqn}.{self.attr_name} -> {result}",
                      extra={'operation': 'GetAttribute', 'context': context_fqn, 'attr_name': self.attr_name, 'result': result})
        else:
            self._log(LogLevel.WARNING, f"GetAttribute failed: {context_fqn}.{self.attr_name}",
                      extra={'operation': 'GetAttribute', 'context': context_fqn, 'attr_name': self.attr_name})
        
        return result
    
    def _resolve_attribute(self, context_fqn: str, attr_name: str, recon_data: Dict[str, Any], scope_manager) -> Optional[str]:
        """
        Resolve attribute using the same logic as the original attribute resolution.
        
        This implements the core attribute resolution logic from attribute_resolution.py
        but adapted for the operations context.
        """
        # Scenario 1: Context is an internal class
        if context_fqn in recon_data.get("classes", {}):
            return self._resolve_from_class(context_fqn, attr_name, recon_data)
        
        # Scenario 2: Context is an external class
        if context_fqn in recon_data.get("external_classes", {}):
            return self._resolve_from_external_class(context_fqn, attr_name)
        
        # Scenario 3: Context is a function (return its return type's attribute)
        if (context_fqn in recon_data.get("functions", {}) or 
            context_fqn in recon_data.get("external_functions", {})):
            return self._resolve_from_function(context_fqn, attr_name, recon_data)
        
        # Scenario 4: Context is a state variable
        if context_fqn in recon_data.get("state", {}):
            return self._resolve_from_state(context_fqn, attr_name, recon_data)
        
        # Fallback: Direct resolution
        candidate = f"{context_fqn}.{attr_name}"
        if self._validate_fqn(candidate, recon_data):
            return candidate
        
        return None
    
    def _resolve_from_class(self, class_fqn: str, attr_name: str, recon_data: Dict[str, Any]) -> Optional[str]:
        """Resolve attribute from an internal class."""
        # Check for direct method
        method_candidate = f"{class_fqn}.{attr_name}"
        if method_candidate in recon_data.get("functions", {}):
            return method_candidate
        
        # Check for class attribute
        class_info = recon_data["classes"][class_fqn]
        if attr_name in class_info.get("attributes", {}):
            attr_type = class_info["attributes"][attr_name].get("type", "Unknown")
            return self._resolve_type_name(attr_type, recon_data, class_fqn)
        
        # Check inheritance hierarchy
        for parent_fqn in class_info.get("parents", []):
            result = self._resolve_from_class(parent_fqn, attr_name, recon_data)
            if result:
                return result
        
        return None
    
    def _resolve_from_external_class(self, class_fqn: str, attr_name: str) -> Optional[str]:
        """Resolve attribute from an external class (optimistic)."""
        return f"{class_fqn}.{attr_name}"
    
    def _resolve_from_function(self, func_fqn: str, attr_name: str, recon_data: Dict[str, Any]) -> Optional[str]:
        """Resolve attribute by looking at function's return type."""
        func_info = (recon_data.get("functions", {}).get(func_fqn) or 
                     recon_data.get("external_functions", {}).get(func_fqn))
        
        if not func_info or not func_info.get("return_type"):
            return None
        
        return_type = func_info["return_type"]
        cleaned_type = self._clean_type_annotation(return_type)
        
        if cleaned_type:
            resolved_type = self._resolve_type_name(cleaned_type, recon_data, func_fqn)
            if resolved_type:
                # Recursively resolve attribute on the return type
                return self._resolve_attribute(resolved_type, attr_name, recon_data, None)
        
        return None
    
    def _resolve_from_state(self, state_fqn: str, attr_name: str, recon_data: Dict[str, Any]) -> Optional[str]:
        """Resolve attribute from a state variable."""
        state_info = recon_data["state"][state_fqn]
        state_type = state_info.get("type")
        
        if state_type:
            resolved_type = self._resolve_type_name(state_type, recon_data, state_fqn)
            if resolved_type:
                # Recursively resolve attribute on the state variable's type
                return self._resolve_attribute(resolved_type, attr_name, recon_data, None)
        
        return None
    
    def _resolve_type_name(self, type_name: str, recon_data: Dict[str, Any], context_fqn: str) -> Optional[str]:
        """Resolve a type name to its FQN."""
        if not type_name or type_name == "Unknown":
            return None
        
        # Already FQN
        if "." in type_name:
            if (type_name in recon_data.get("classes", {}) or 
                type_name in recon_data.get("external_classes", {})):
                return type_name
        
        # Try current module
        current_module = context_fqn.split('.')[0] if context_fqn else ''
        candidate = f"{current_module}.{type_name}"
        if candidate in recon_data.get("classes", {}):
            return candidate
        
        # Search all classes
        for catalog_name in ["classes", "external_classes"]:
            for fqn in recon_data.get(catalog_name, {}):
                if fqn.endswith(f".{type_name}"):
                    return fqn
        
        return None
    
    def _clean_type_annotation(self, type_str: str) -> Optional[str]:
        """Clean type annotations like 'Optional[Client]' -> 'Client'."""
        if not type_str:
            return None
        
        # Simple cleanup for common patterns
        type_str = type_str.strip()
        
        # Handle Optional[Type] -> Type
        if type_str.startswith("Optional[") and type_str.endswith("]"):
            return type_str[9:-1].strip()
        
        # Handle List[Type] -> Type (for now, simplified)
        if type_str.startswith("List[") and type_str.endswith("]"):
            return type_str[5:-1].strip()
        
        # Handle Dict[Key, Value] -> Dict (for now, simplified)
        if type_str.startswith("Dict["):
            return "dict"
        
        return type_str
    
    def _validate_fqn(self, fqn: str, recon_data: Dict[str, Any]) -> bool:
        """Check if FQN exists in recon_data."""
        return (fqn in recon_data.get("classes", {}) or
                fqn in recon_data.get("functions", {}) or
                fqn in recon_data.get("state", {}) or
                fqn in recon_data.get("external_classes", {}) or
                fqn in recon_data.get("external_functions", {}))
    
    def __str__(self):
        return f"GetAttribute(\"{self.attr_name}\")"


@dataclass
class CallFunction(Operation):
    """
    Operation to handle function/method calls.
    
    This operation takes a function/method FQN and returns the FQN
    of its return type for proper Type Propagation.
    """
    
    def execute(self, context_fqn: str, recon_data: Dict[str, Any], scope_manager) -> Optional[str]:
        """
        Execute function call and return the return type FQN.
        
        Args:
            context_fqn: FQN of the function/method being called
            recon_data: Reconnaissance data structure
            scope_manager: Current scope manager instance
            
        Returns:
            FQN of the function's return type, or None if not found
        """
        self._log(LogLevel.TRACE, f"CallFunction.execute() on context: {context_fqn}",
                  extra={'operation': 'CallFunction', 'context': context_fqn})
        
        if not context_fqn:
            self._log(LogLevel.WARNING, f"CallFunction failed: no context function",
                      extra={'operation': 'CallFunction'})
            return None
        
        result = self._get_return_type(context_fqn, recon_data)
        
        if result:
            self._log(LogLevel.DEBUG, f"CallFunction resolved: {context_fqn}() -> {result}",
                      extra={'operation': 'CallFunction', 'function': context_fqn, 'return_type': result})
        else:
            self._log(LogLevel.WARNING, f"CallFunction failed to get return type for: {context_fqn}",
                      extra={'operation': 'CallFunction', 'function': context_fqn})
        
        return result
    
    def _get_return_type(self, func_fqn: str, recon_data: Dict[str, Any]) -> Optional[str]:
        """Get the return type FQN for a function."""
        # Check internal functions
        func_info = recon_data.get("functions", {}).get(func_fqn)
        if func_info and func_info.get("return_type"):
            return_type = func_info["return_type"]
            return self._resolve_return_type(return_type, recon_data, func_fqn)
        
        # Check external functions
        ext_func_info = recon_data.get("external_functions", {}).get(func_fqn)
        if ext_func_info and ext_func_info.get("return_type"):
            return_type = ext_func_info["return_type"]
            return self._resolve_return_type(return_type, recon_data, func_fqn)
        
        # Handle special case: constructor calls (ClassName() -> ClassName)
        # If the function FQN looks like a class name, it might be a constructor
        if func_fqn in recon_data.get("classes", {}):
            return func_fqn
        
        # Check if it's an external class constructor
        if func_fqn in recon_data.get("external_classes", {}):
            return func_fqn
        
        return None
    
    def _resolve_return_type(self, return_type: str, recon_data: Dict[str, Any], func_fqn: str) -> Optional[str]:
        """Resolve return type string to FQN."""
        if not return_type:
            return None
        
        # Clean the type annotation
        cleaned_type = self._clean_type_annotation(return_type)
        if not cleaned_type:
            return None
        
        # If already FQN, validate and return
        if "." in cleaned_type:
            if (cleaned_type in recon_data.get("classes", {}) or 
                cleaned_type in recon_data.get("external_classes", {})):
                return cleaned_type
        
        # Try to resolve relative to current module
        current_module = func_fqn.split('.')[0] if func_fqn else ''
        candidate = f"{current_module}.{cleaned_type}"
        if candidate in recon_data.get("classes", {}):
            return candidate
        
        # Search all classes for matching name
        for catalog_name in ["classes", "external_classes"]:
            for class_fqn in recon_data.get(catalog_name, {}):
                if class_fqn.endswith(f".{cleaned_type}"):
                    return class_fqn
        
        return None
    
    def _clean_type_annotation(self, type_str: str) -> Optional[str]:
        """Clean type annotations like 'Optional[Client]' -> 'Client'."""
        if not type_str:
            return None
        
        type_str = type_str.strip()
        
        # Handle Optional[Type] -> Type
        if type_str.startswith("Optional[") and type_str.endswith("]"):
            return type_str[9:-1].strip()
        
        # Handle List[Type] -> Type
        if type_str.startswith("List[") and type_str.endswith("]"):
            return type_str[5:-1].strip()
        
        # Handle Dict[Key, Value] -> dict
        if type_str.startswith("Dict["):
            return "dict"
        
        # Handle Union types (take first type for simplicity)
        if type_str.startswith("Union["):
            inner = type_str[6:-1].strip()
            first_type = inner.split(',')[0].strip()
            return first_type
        
        return type_str
    
    def __str__(self):
        return "CallFunction()"
