"""
Name Resolution Engine - Code Atlas

Contains the core NameResolver and its associated strategies for resolving
names and attribute chains within different contexts.
"""

import ast
import inspect
from typing import Dict, List, Optional, Any

from .logger import get_logger, LogContext, AnalysisPhase, LogLevel
from .utils import get_source


class ResolutionStrategy:
    """Base class for name resolution strategies."""
    
    def can_resolve(self, base_name: str, context: Dict[str, Any]) -> bool:
        """Check if this strategy can resolve the given name."""
        raise NotImplementedError
    
    def resolve(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve the name using this strategy."""
        raise NotImplementedError

    def _log(
            self, 
            level: LogLevel, 
            message: str, 
            extra: Optional[Dict[str, Any]] = None
        ):
        """Enhanced logging with automatic source detection."""

        context = LogContext(
            phase=AnalysisPhase.ANALYSIS,
            source=get_source(),
            module=None,
            class_name=None,
            function=None
        )
        
        getattr(get_logger(__name__), level.name.lower())(message, context, extra)


class LocalVariableStrategy(ResolutionStrategy):
    """Resolves names from local variable symbol tables."""
    
    def can_resolve(self, base_name: str, context: Dict[str, Any]) -> bool:
        symbol_manager = context.get('symbol_manager')
        can_resolve = symbol_manager and symbol_manager.get_variable_type(base_name) is not None
        
        self._log(LogLevel.TRACE, f"LocalVariableStrategy.can_resolve({base_name}): {can_resolve}",
                  extra={'strategy': 'LocalVariable', 'variable': base_name})
        return can_resolve
    
    def resolve(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        symbol_manager = context['symbol_manager']
        result = symbol_manager.get_variable_type(base_name)
        
        self._log(LogLevel.TRACE, f"LocalVariableStrategy.resolve({base_name}): {result}",
                  extra={'strategy': 'LocalVariable', 'variable': base_name, 'result': result})
        return result


class SelfStrategy(ResolutionStrategy):
    """Resolves 'self' references to current class."""
    
    def can_resolve(self, base_name: str, context: Dict[str, Any]) -> bool:
        can_resolve = base_name == "self" and context.get('current_class')
        
        self._log(LogLevel.TRACE, f"SelfStrategy.can_resolve({base_name}): {can_resolve}",
                  extra={'strategy': 'Self', 'variable': base_name, 'current_class': context.get('current_class')})
        return can_resolve
    
    def resolve(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        result = context['current_class']
        
        self._log(LogLevel.TRACE, f"SelfStrategy.resolve({base_name}): {result}",
                  extra={'strategy': 'Self', 'variable': base_name, 'result': result})
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
        
        self._log(LogLevel.TRACE, f"ImportStrategy.can_resolve({base_name}): {can_resolve}",
                  extra={'strategy': 'Import', 'variable': base_name,
                         'import_available': can_resolve_import,
                         'external_available': can_resolve_external})
        return can_resolve
    
    def resolve(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        import_map = context.get('import_map', {})
        
        # First try direct import map
        if base_name in import_map:
            result = import_map[base_name]
            self._log(LogLevel.TRACE, f"ImportStrategy.resolve({base_name}): {result} (from import map)",
                      extra={'strategy': 'Import', 'variable': base_name, 'result': result, 'source_type': 'import_map'})
            return result
        
        # Then try external library resolution
        external_result = self._resolve_external(base_name)
        if external_result:
            self._log(LogLevel.TRACE, f"ImportStrategy.resolve({base_name}): {external_result} (external)",
                      extra={'strategy': 'Import', 'variable': base_name, 'result': external_result, 'source_type': 'external'})
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
        self._log(LogLevel.TRACE, f"ModuleStrategy.can_resolve({base_name}): True (fallback)",
                  extra={'strategy': 'Module', 'variable': base_name})
        return True  # Always can try this as fallback
    
    def resolve(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        current_module = context.get('current_module', '')
        result = f"{current_module}.{base_name}"
        
        self._log(LogLevel.TRACE, f"ModuleStrategy.resolve({base_name}): {result}",
                  extra={'strategy': 'Module', 'variable': base_name, 'result': result})
        return result


class NameResolver:
    """Core name resolution engine with inheritance-aware method resolution, attribute support, and external library support."""
    
    def __init__(self, recon_data: Dict[str, Any]):
        self.recon_data = recon_data
        self.strategies = [
            LocalVariableStrategy(),
            SelfStrategy(),
            ImportStrategy(recon_data),
            ModuleStrategy()
        ]
        
        self._log(LogLevel.DEBUG, f"Name resolver initialized with {len(self.strategies)} strategies",
                  extra={'strategy_count': len(self.strategies),
                         'recon_classes': len(recon_data.get("classes", {})),
                         'recon_functions': len(recon_data.get("functions", {})),
                         'external_classes': len(recon_data.get("external_classes", {})),
                         'external_functions': len(recon_data.get("external_functions", {}))})
    
    def _log(
            self, 
            level: LogLevel, 
            message: str, 
            extra: Optional[Dict[str, Any]] = None
        ):
        """Enhanced logging with automatic source detection."""
        
        context = LogContext(
            phase=AnalysisPhase.ANALYSIS,
            source=get_source(),
            module=None,
            class_name=None,
            function=None
        )
        
        getattr(get_logger(__name__), level.name.lower())(message, context, extra)
    
    def resolve_name(self, name_parts: List[str], context: Dict[str, Any]) -> Optional[str]:
        """Resolve name using layered strategies with comprehensive logging."""
        if not name_parts:
            self._log(LogLevel.DEBUG, "Resolution failed: No name parts provided")
            return None
        
        name_str = '.'.join(name_parts)
        self._log(LogLevel.DEBUG, f"Resolving name: {name_str}",
                  extra={'name_parts': name_parts, 'parts_count': len(name_parts)})
        
        # Layer 1: Simple resolution for single names
        if len(name_parts) == 1:
            result = self._resolve_simple(name_parts[0], context)
            if result:
                self._log(LogLevel.DEBUG, f"Simple resolution successful: {name_str} -> {result}",
                          extra={'resolution_type': 'simple', 'input': name_str, 'result': result})
            else:
                self._log(LogLevel.DEBUG, f"Simple resolution failed: {name_str}",
                          extra={'resolution_type': 'simple', 'input': name_str})
            return result
        
        # Layer 2: Complex chain resolution
        self._log(LogLevel.TRACE, f"Complex chain resolution needed: {name_str}",
                  extra={'resolution_type': 'chain', 'input': name_str})
        result = self._resolve_chain(name_parts, context)
        if result:
            self._log(LogLevel.DEBUG, f"Chain resolution successful: {name_str} -> {result}",
                      extra={'resolution_type': 'chain', 'input': name_str, 'result': result})
        else:
            self._log(LogLevel.DEBUG, f"Chain resolution failed: {name_str}",
                      extra={'resolution_type': 'chain', 'input': name_str})
        return result
    
    def _resolve_simple(self, name: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve simple single name using strategies."""
        self._log(LogLevel.TRACE, f"Resolving simple name: {name}",
                  extra={'resolution_method': 'simple', 'name': name})
        
        for i, strategy in enumerate(self.strategies):
            strategy_name = strategy.__class__.__name__
            self._log(LogLevel.TRACE, f"Trying strategy {i+1}: {strategy_name}",
                      extra={'strategy_index': i, 'strategy': strategy_name, 'name': name})
            
            if strategy.can_resolve(name, context):
                result = strategy.resolve(name, context)
                if result and self._validate_resolution(result):
                    self._log(LogLevel.TRACE, f"Strategy {strategy_name} succeeded: {name} -> {result}",
                              extra={'successful_strategy': strategy_name, 'name': name, 'result': result})
                    return result
                else:
                    self._log(LogLevel.TRACE, f"Strategy {strategy_name} failed validation",
                              extra={'failed_strategy': strategy_name, 'name': name, 'result': result})
            else:
                self._log(LogLevel.TRACE, f"Strategy {strategy_name} cannot resolve {name}",
                          extra={'skipped_strategy': strategy_name, 'name': name})
        
        self._log(LogLevel.TRACE, f"All strategies failed for: {name}",
                  extra={'resolution_result': 'failed', 'name': name})
        return None
    
    def _resolve_chain(self, name_parts: List[str], context: Dict[str, Any]) -> Optional[str]:
        """Resolve complex attribute chains with enhanced attribute support."""
        # Resolve base
        base_name = name_parts[0]
        self._log(LogLevel.TRACE, f"Resolving chain base: {base_name}",
                  extra={'chain_step': 'base', 'base_name': base_name, 'full_chain': name_parts})
        
        base_fqn = self._resolve_simple(base_name, context)
        if not base_fqn:
            self._log(LogLevel.TRACE, f"Chain resolution failed: could not resolve base {base_name}",
                      extra={'chain_failure': 'base_resolution', 'base_name': base_name})
            return None
        
        self._log(LogLevel.TRACE, f"Chain base resolved: {base_name} -> {base_fqn}",
                  extra={'base_name': base_name, 'base_fqn': base_fqn})
        
        # Walk the chain
        current_fqn = base_fqn
        for i, attr in enumerate(name_parts[1:], 1):
            self._log(LogLevel.TRACE, f"Chain step {i}: Resolving {current_fqn}.{attr}",
                      extra={'chain_step': i, 'current_fqn': current_fqn, 'attr': attr})
            current_fqn = self._resolve_attribute(current_fqn, attr, context)
            if not current_fqn:
                self._log(LogLevel.TRACE, f"Chain resolution failed at step {i}: .{attr}",
                          extra={'chain_failure': 'attribute_resolution', 'step': i, 'attr': attr})
                return None
            self._log(LogLevel.TRACE, f"Chain step {i} resolved: {current_fqn}",
                      extra={'chain_step': i, 'resolved_fqn': current_fqn})
        
        return current_fqn
    
    def _resolve_attribute(self, context_fqn: str, attr: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve attribute in context of given FQN with inheritance, attribute support, and external library support."""
        candidate = f"{context_fqn}.{attr}"
        self._log(LogLevel.TRACE, f"Resolving attribute: {context_fqn}.{attr}",
                  extra={'context_fqn': context_fqn, 'attr': attr, 'candidate': candidate})
        
        # Check if context is a state variable - resolve through its type
        if context_fqn in self.recon_data["state"]:
            self._log(LogLevel.TRACE, "Context is state variable, resolving through type",
                      extra={'context_fqn': context_fqn, 'resolution_method': 'state_type'})
            state_type = self._get_state_type(context_fqn)
            if state_type:
                self._log(LogLevel.TRACE, f"State type resolved: {state_type}",
                          extra={'state_fqn': context_fqn, 'state_type': state_type})
                return self._resolve_attribute(state_type, attr, context)
            else:
                self._log(LogLevel.TRACE, "Could not resolve state type",
                          extra={'state_fqn': context_fqn})
        
        # Check if context is an internal class - look for methods and attributes with inheritance
        if context_fqn in self.recon_data["classes"]:
            self._log(LogLevel.TRACE, "Context is internal class, checking for method/attribute",
                      extra={'class_fqn': context_fqn, 'resolution_method': 'class_member'})
            
            # First check direct method
            if candidate in self.recon_data["functions"]:
                self._log(LogLevel.TRACE, f"Found direct method: {candidate}",
                          extra={'method_fqn': candidate, 'resolution_type': 'direct_method'})
                return candidate
            
            # Check for class attribute
            class_info = self.recon_data["classes"][context_fqn]
            class_attributes = class_info.get("attributes", {})
            if attr in class_attributes:
                attr_type = class_attributes[attr].get("type")
                if attr_type and attr_type != "Unknown":
                    self._log(LogLevel.TRACE, f"Found class attribute: {attr} of type {attr_type}",
                              extra={'class_fqn': context_fqn, 'attr': attr, 'attr_type': attr_type})
                    # Resolve the attribute type to its FQN
                    resolved_type = self._resolve_attribute_type(attr_type, context)
                    if resolved_type:
                        self._log(LogLevel.TRACE, f"Attribute type resolved to: {resolved_type}",
                                  extra={'attr_type': attr_type, 'resolved_type': resolved_type})
                        return resolved_type
                    else:
                        self._log(LogLevel.TRACE, f"Could not resolve attribute type: {attr_type}",
                                  extra={'attr_type': attr_type})
            
            # Then check inheritance chain
            self._log(LogLevel.TRACE, "Checking inheritance for method/attribute",
                      extra={'class_fqn': context_fqn, 'attr': attr})
            inherited_result = self._resolve_inherited_method_or_attribute(context_fqn, attr, context)
            if inherited_result:
                self._log(LogLevel.TRACE, f"Found in inheritance chain: {inherited_result}",
                          extra={'class_fqn': context_fqn, 'attr': attr, 'inherited_result': inherited_result})
                return inherited_result
            
            self._log(LogLevel.TRACE, "Method/attribute not found in class or inheritance chain",
                      extra={'class_fqn': context_fqn, 'attr': attr, 'candidate': candidate})
        
        # Check if context is an external class
        elif context_fqn in self.recon_data.get("external_classes", {}):
            self._log(LogLevel.TRACE, "Context is external class, checking for common methods",
                      extra={'external_class_fqn': context_fqn, 'attr': attr})
            
            # For external classes, we assume common methods exist
            external_method_fqn = f"{context_fqn}.{attr}"
            
            # Special handling for known external library patterns
            if self._is_known_external_method(context_fqn, attr):
                self._log(LogLevel.TRACE, f"Found known external method: {external_method_fqn}",
                          extra={'external_method': external_method_fqn, 'known_method': True})
                return external_method_fqn
            else:
                self._log(LogLevel.TRACE, f"Assuming external method exists: {external_method_fqn}",
                          extra={'external_method': external_method_fqn, 'assumed': True})
                return external_method_fqn
        
        # Check if context is a function - use return type
        if (context_fqn in self.recon_data["functions"] or 
            context_fqn in self.recon_data.get("external_functions", {})):
            self._log(LogLevel.TRACE, "Context is function, using return type",
                      extra={'function_fqn': context_fqn, 'resolution_method': 'return_type'})
            
            func_info = None
            if context_fqn in self.recon_data["functions"]:
                func_info = self.recon_data["functions"][context_fqn]
            elif context_fqn in self.recon_data.get("external_functions", {}):
                func_info = self.recon_data["external_functions"][context_fqn]
            
            if func_info:
                return_type = func_info.get("return_type")
                if return_type:
                    self._log(LogLevel.TRACE, f"Function return type: {return_type}",
                              extra={'function_fqn': context_fqn, 'return_type': return_type})
                    type_inference = context.get('type_inference')
                    if type_inference:
                        core_type = type_inference.extract_core_type(return_type)
                        if core_type:
                            self._log(LogLevel.TRACE, f"Core type extracted: {core_type}",
                                      extra={'return_type': return_type, 'core_type': core_type})
                            resolved_type = self._resolve_type_name(core_type, context)
                            if resolved_type:
                                self._log(LogLevel.TRACE, f"Type name resolved: {resolved_type}",
                                          extra={'core_type': core_type, 'resolved_type': resolved_type})
                                return self._resolve_attribute(resolved_type, attr, context)
                            else:
                                self._log(LogLevel.TRACE, "Could not resolve type name",
                                          extra={'core_type': core_type})
                        else:
                            self._log(LogLevel.TRACE, "Could not extract core type",
                                      extra={'return_type': return_type})
                    else:
                        self._log(LogLevel.TRACE, "No type inference engine available",
                                  extra={'function_fqn': context_fqn})
                else:
                    self._log(LogLevel.TRACE, "Function has no return type",
                              extra={'function_fqn': context_fqn})
        
        # Direct resolution
        if self._validate_resolution(candidate):
            self._log(LogLevel.TRACE, f"Direct resolution successful: {candidate}",
                      extra={'candidate': candidate, 'resolution_type': 'direct'})
            return candidate
        
        self._log(LogLevel.TRACE, "All attribute resolution attempts failed",
                  extra={'context_fqn': context_fqn, 'attr': attr})
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
        self._log(LogLevel.TRACE, f"Checking inheritance chain for {class_fqn}.{attr_name}",
                  extra={'class_fqn': class_fqn, 'attr_name': attr_name})
        
        if class_fqn not in self.recon_data["classes"]:
            self._log(LogLevel.TRACE, f"Class {class_fqn} not found in catalog",
                      extra={'class_fqn': class_fqn})
            return None
        
        class_info = self.recon_data["classes"][class_fqn]
        parents = class_info.get("parents", [])
        
        self._log(LogLevel.TRACE, f"Parents of {class_fqn}: {parents}",
                  extra={'class_fqn': class_fqn, 'parents': parents})
        
        for parent_fqn in parents:
            # Check for method in parent
            method_candidate = f"{parent_fqn}.{attr_name}"
            self._log(LogLevel.TRACE, f"Checking parent method: {method_candidate}",
                      extra={'parent_fqn': parent_fqn, 'method_candidate': method_candidate})
            
            if method_candidate in self.recon_data["functions"]:
                self._log(LogLevel.TRACE, f"Found inherited method: {method_candidate}",
                          extra={'inherited_method': method_candidate})
                return method_candidate
            
            # Check for attribute in parent
            if parent_fqn in self.recon_data["classes"]:
                parent_info = self.recon_data["classes"][parent_fqn]
                parent_attributes = parent_info.get("attributes", {})
                if attr_name in parent_attributes:
                    attr_type = parent_attributes[attr_name].get("type")
                    if attr_type and attr_type != "Unknown":
                        self._log(LogLevel.TRACE, f"Found inherited attribute: {attr_name} of type {attr_type}",
                                  extra={'parent_fqn': parent_fqn, 'attr_name': attr_name, 'attr_type': attr_type})
                        resolved_type = self._resolve_attribute_type(attr_type, context)
                        if resolved_type:
                            return resolved_type
            
            # Recursive check up the inheritance chain
            inherited = self._resolve_inherited_method_or_attribute(parent_fqn, attr_name, context)
            if inherited:
                self._log(LogLevel.TRACE, f"Found in grandparent: {inherited}",
                          extra={'grandparent_result': inherited, 'parent_fqn': parent_fqn})
                return inherited
        
        self._log(LogLevel.TRACE, f"Method/attribute {attr_name} not found in inheritance chain",
                  extra={'class_fqn': class_fqn, 'attr_name': attr_name})
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
        
        self._log(LogLevel.TRACE, f"Validation check: {fqn} {'EXISTS' if exists else 'NOT_FOUND'}",
                  extra={'fqn': fqn, 'exists': exists})
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
