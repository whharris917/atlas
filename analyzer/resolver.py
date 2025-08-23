"""
Name Resolution Engine - Code Atlas

Contains the core NameResolver and its associated strategies for resolving
names and attribute chains within different contexts.
"""

import ast
from typing import Dict, List, Optional, Any

from .logger import get_logger, LogContext, AnalysisPhase

logger = get_logger(__name__)


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
        
        logger.trace(f"LocalVariableStrategy.can_resolve({base_name}): {can_resolve}",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                     extra={'strategy': 'LocalVariable', 'variable': base_name}))
        return can_resolve
    
    def resolve(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        symbol_manager = context['symbol_manager']
        result = symbol_manager.get_variable_type(base_name)
        
        logger.trace(f"LocalVariableStrategy.resolve({base_name}): {result}",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                     extra={'strategy': 'LocalVariable', 'variable': base_name, 'result': result}))
        return result


class SelfStrategy(ResolutionStrategy):
    """Resolves 'self' references to current class."""
    
    def can_resolve(self, base_name: str, context: Dict[str, Any]) -> bool:
        can_resolve = base_name == "self" and context.get('current_class')
        
        logger.trace(f"SelfStrategy.can_resolve({base_name}): {can_resolve}",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                     extra={'strategy': 'Self', 'variable': base_name,
                                            'current_class': context.get('current_class')}))
        return can_resolve
    
    def resolve(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        result = context['current_class']
        
        logger.trace(f"SelfStrategy.resolve({base_name}): {result}",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                     extra={'strategy': 'Self', 'variable': base_name, 'result': result}))
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
        
        logger.trace(f"ImportStrategy.can_resolve({base_name}): {can_resolve}",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                     extra={'strategy': 'Import', 'variable': base_name,
                                            'import_available': can_resolve_import,
                                            'external_available': can_resolve_external}))
        return can_resolve
    
    def resolve(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        import_map = context.get('import_map', {})
        
        # First try direct import map
        if base_name in import_map:
            result = import_map[base_name]
            logger.trace(f"ImportStrategy.resolve({base_name}): {result} (from import map)",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                         extra={'strategy': 'Import', 'variable': base_name, 'result': result, 'source': 'import_map'}))
            return result
        
        # Then try external library resolution
        external_result = self._resolve_external(base_name)
        if external_result:
            logger.trace(f"ImportStrategy.resolve({base_name}): {external_result} (external)",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                         extra={'strategy': 'Import', 'variable': base_name, 'result': external_result, 'source': 'external'}))
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
        logger.trace(f"ModuleStrategy.can_resolve({base_name}): True (fallback)",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                     extra={'strategy': 'Module', 'variable': base_name}))
        return True  # Always can try this as fallback
    
    def resolve(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        current_module = context.get('current_module', '')
        result = f"{current_module}.{base_name}"
        
        logger.trace(f"ModuleStrategy.resolve({base_name}): {result}",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                     extra={'strategy': 'Module', 'variable': base_name, 'result': result}))
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
        
        logger.debug(f"Name resolver initialized with {len(self.strategies)} strategies",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                     extra={'strategy_count': len(self.strategies),
                                            'recon_classes': len(recon_data.get("classes", {})),
                                            'recon_functions': len(recon_data.get("functions", {})),
                                            'external_classes': len(recon_data.get("external_classes", {})),
                                            'external_functions': len(recon_data.get("external_functions", {}))}))
    
    def resolve_name(self, name_parts: List[str], context: Dict[str, Any]) -> Optional[str]:
        """Resolve name using layered strategies with comprehensive logging."""
        if not name_parts:
            logger.debug("Resolution failed: No name parts provided",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS))
            return None
        
        name_str = '.'.join(name_parts)
        logger.debug(f"Resolving name: {name_str}",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                     extra={'name_parts': name_parts, 'parts_count': len(name_parts)}))
        
        # Layer 1: Simple resolution for single names
        if len(name_parts) == 1:
            result = self._resolve_simple(name_parts[0], context)
            if result:
                logger.debug(f"Simple resolution successful: {name_str} -> {result}",
                           context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                            extra={'resolution_type': 'simple', 'input': name_str, 'result': result}))
            else:
                logger.debug(f"Simple resolution failed: {name_str}",
                           context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                            extra={'resolution_type': 'simple', 'input': name_str}))
            return result
        
        # Layer 2: Complex chain resolution
        logger.trace(f"Complex chain resolution needed: {name_str}",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                     extra={'resolution_type': 'chain', 'input': name_str}))
        result = self._resolve_chain(name_parts, context)
        if result:
            logger.debug(f"Chain resolution successful: {name_str} -> {result}",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                         extra={'resolution_type': 'chain', 'input': name_str, 'result': result}))
        else:
            logger.debug(f"Chain resolution failed: {name_str}",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                         extra={'resolution_type': 'chain', 'input': name_str}))
        return result
    
    def _resolve_simple(self, name: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve simple single name using strategies."""
        logger.trace(f"Resolving simple name: {name}",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                     extra={'resolution_method': 'simple', 'name': name}))
        
        for i, strategy in enumerate(self.strategies):
            strategy_name = strategy.__class__.__name__
            logger.trace(f"Trying strategy {i+1}: {strategy_name}",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                         extra={'strategy_index': i, 'strategy': strategy_name, 'name': name}))
            
            if strategy.can_resolve(name, context):
                result = strategy.resolve(name, context)
                if result and self._validate_resolution(result):
                    logger.trace(f"Strategy {strategy_name} succeeded: {name} -> {result}",
                                context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                                 extra={'successful_strategy': strategy_name, 'name': name, 'result': result}))
                    return result
                else:
                    logger.trace(f"Strategy {strategy_name} failed validation",
                                context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                                 extra={'failed_strategy': strategy_name, 'name': name, 'result': result}))
            else:
                logger.trace(f"Strategy {strategy_name} cannot resolve {name}",
                            context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                             extra={'skipped_strategy': strategy_name, 'name': name}))
        
        logger.trace(f"All strategies failed for: {name}",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                     extra={'resolution_result': 'failed', 'name': name}))
        return None
    
    def _resolve_chain(self, name_parts: List[str], context: Dict[str, Any]) -> Optional[str]:
        """Resolve complex attribute chains with enhanced attribute support."""
        # Resolve base
        base_name = name_parts[0]
        logger.trace(f"Resolving chain base: {base_name}",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                     extra={'chain_step': 'base', 'base_name': base_name, 'full_chain': name_parts}))
        
        base_fqn = self._resolve_simple(base_name, context)
        if not base_fqn:
            logger.trace(f"Chain resolution failed: could not resolve base {base_name}",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                         extra={'chain_failure': 'base_resolution', 'base_name': base_name}))
            return None
        
        logger.trace(f"Chain base resolved: {base_name} -> {base_fqn}",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                     extra={'base_name': base_name, 'base_fqn': base_fqn}))
        
        # Walk the chain
        current_fqn = base_fqn
        for i, attr in enumerate(name_parts[1:], 1):
            logger.trace(f"Chain step {i}: Resolving {current_fqn}.{attr}",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                         extra={'chain_step': i, 'current_fqn': current_fqn, 'attr': attr}))
            current_fqn = self._resolve_attribute(current_fqn, attr, context)
            if not current_fqn:
                logger.trace(f"Chain resolution failed at step {i}: .{attr}",
                           context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                            extra={'chain_failure': 'attribute_resolution', 'step': i, 'attr': attr}))
                return None
            logger.trace(f"Chain step {i} resolved: {current_fqn}",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                         extra={'chain_step': i, 'resolved_fqn': current_fqn}))
        
        return current_fqn
    
    def _resolve_attribute(self, context_fqn: str, attr: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve attribute in context of given FQN with inheritance, attribute support, and external library support."""
        candidate = f"{context_fqn}.{attr}"
        logger.trace(f"Resolving attribute: {context_fqn}.{attr}",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                     extra={'context_fqn': context_fqn, 'attr': attr, 'candidate': candidate}))
        
        # Check if context is a state variable - resolve through its type
        if context_fqn in self.recon_data["state"]:
            logger.trace("Context is state variable, resolving through type",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                         extra={'context_fqn': context_fqn, 'resolution_method': 'state_type'}))
            state_type = self._get_state_type(context_fqn)
            if state_type:
                logger.trace(f"State type resolved: {state_type}",
                           context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                            extra={'state_fqn': context_fqn, 'state_type': state_type}))
                return self._resolve_attribute(state_type, attr, context)
            else:
                logger.trace("Could not resolve state type",
                           context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                            extra={'state_fqn': context_fqn}))
        
        # Check if context is an internal class - look for methods and attributes with inheritance
        if context_fqn in self.recon_data["classes"]:
            logger.trace("Context is internal class, checking for method/attribute",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                         extra={'class_fqn': context_fqn, 'resolution_method': 'class_member'}))
            
            # First check direct method
            if candidate in self.recon_data["functions"]:
                logger.trace(f"Found direct method: {candidate}",
                           context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                            extra={'method_fqn': candidate, 'resolution_type': 'direct_method'}))
                return candidate
            
            # Check for class attribute
            class_info = self.recon_data["classes"][context_fqn]
            class_attributes = class_info.get("attributes", {})
            if attr in class_attributes:
                attr_type = class_attributes[attr].get("type")
                if attr_type and attr_type != "Unknown":
                    logger.trace(f"Found class attribute: {attr} of type {attr_type}",
                               context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                                extra={'class_fqn': context_fqn, 'attr': attr, 'attr_type': attr_type}))
                    # Resolve the attribute type to its FQN
                    resolved_type = self._resolve_attribute_type(attr_type, context)
                    if resolved_type:
                        logger.trace(f"Attribute type resolved to: {resolved_type}",
                                   context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                                    extra={'attr_type': attr_type, 'resolved_type': resolved_type}))
                        return resolved_type
                    else:
                        logger.trace(f"Could not resolve attribute type: {attr_type}",
                                   context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                                    extra={'attr_type': attr_type}))
            
            # Then check inheritance chain
            logger.trace("Checking inheritance for method/attribute",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                         extra={'class_fqn': context_fqn, 'attr': attr}))
            inherited_result = self._resolve_inherited_method_or_attribute(context_fqn, attr, context)
            if inherited_result:
                logger.trace(f"Found in inheritance chain: {inherited_result}",
                           context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                            extra={'class_fqn': context_fqn, 'attr': attr, 'inherited_result': inherited_result}))
                return inherited_result
            
            logger.trace("Method/attribute not found in class or inheritance chain",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                         extra={'class_fqn': context_fqn, 'attr': attr, 'candidate': candidate}))
        
        # Check if context is an external class
        elif context_fqn in self.recon_data.get("external_classes", {}):
            logger.trace("Context is external class, checking for common methods",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                         extra={'external_class_fqn': context_fqn, 'attr': attr}))
            
            # For external classes, we assume common methods exist
            external_method_fqn = f"{context_fqn}.{attr}"
            
            # Special handling for known external library patterns
            if self._is_known_external_method(context_fqn, attr):
                logger.trace(f"Found known external method: {external_method_fqn}",
                           context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                            extra={'external_method': external_method_fqn, 'known_method': True}))
                return external_method_fqn
            else:
                logger.trace(f"Assuming external method exists: {external_method_fqn}",
                           context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                            extra={'external_method': external_method_fqn, 'assumed': True}))
                return external_method_fqn
        
        # Check if context is a function - use return type
        if (context_fqn in self.recon_data["functions"] or 
            context_fqn in self.recon_data.get("external_functions", {})):
            logger.trace("Context is function, using return type",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                         extra={'function_fqn': context_fqn, 'resolution_method': 'return_type'}))
            
            func_info = None
            if context_fqn in self.recon_data["functions"]:
                func_info = self.recon_data["functions"][context_fqn]
            elif context_fqn in self.recon_data.get("external_functions", {}):
                func_info = self.recon_data["external_functions"][context_fqn]
            
            if func_info:
                return_type = func_info.get("return_type")
                if return_type:
                    logger.trace(f"Function return type: {return_type}",
                               context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                                extra={'function_fqn': context_fqn, 'return_type': return_type}))
                    type_inference = context.get('type_inference')
                    if type_inference:
                        core_type = type_inference.extract_core_type(return_type)
                        if core_type:
                            logger.trace(f"Core type extracted: {core_type}",
                                       context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                                        extra={'return_type': return_type, 'core_type': core_type}))
                            resolved_type = self._resolve_type_name(core_type, context)
                            if resolved_type:
                                logger.trace(f"Type name resolved: {resolved_type}",
                                           context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                                            extra={'core_type': core_type, 'resolved_type': resolved_type}))
                                return self._resolve_attribute(resolved_type, attr, context)
                            else:
                                logger.trace("Could not resolve type name",
                                           context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                                            extra={'core_type': core_type}))
                        else:
                            logger.trace("Could not extract core type",
                                       context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                                        extra={'return_type': return_type}))
                    else:
                        logger.trace("No type inference engine available",
                                   context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                                    extra={'function_fqn': context_fqn}))
                else:
                    logger.trace("Function has no return type",
                               context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                                extra={'function_fqn': context_fqn}))
        
        # Direct resolution
        if self._validate_resolution(candidate):
            logger.trace(f"Direct resolution successful: {candidate}",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                         extra={'candidate': candidate, 'resolution_type': 'direct'}))
            return candidate
        
        logger.trace("All attribute resolution attempts failed",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                     extra={'context_fqn': context_fqn, 'attr': attr}))
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
        logger.trace(f"Checking inheritance chain for {class_fqn}.{attr_name}",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                     extra={'class_fqn': class_fqn, 'attr_name': attr_name}))
        
        if class_fqn not in self.recon_data["classes"]:
            logger.trace(f"Class {class_fqn} not found in catalog",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                         extra={'class_fqn': class_fqn}))
            return None
        
        class_info = self.recon_data["classes"][class_fqn]
        parents = class_info.get("parents", [])
        
        logger.trace(f"Parents of {class_fqn}: {parents}",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                     extra={'class_fqn': class_fqn, 'parents': parents}))
        
        for parent_fqn in parents:
            # Check for method in parent
            method_candidate = f"{parent_fqn}.{attr_name}"
            logger.trace(f"Checking parent method: {method_candidate}",
                        context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                         extra={'parent_fqn': parent_fqn, 'method_candidate': method_candidate}))
            
            if method_candidate in self.recon_data["functions"]:
                logger.trace(f"Found inherited method: {method_candidate}",
                           context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                            extra={'inherited_method': method_candidate}))
                return method_candidate
            
            # Check for attribute in parent
            if parent_fqn in self.recon_data["classes"]:
                parent_info = self.recon_data["classes"][parent_fqn]
                parent_attributes = parent_info.get("attributes", {})
                if attr_name in parent_attributes:
                    attr_type = parent_attributes[attr_name].get("type")
                    if attr_type and attr_type != "Unknown":
                        logger.trace(f"Found inherited attribute: {attr_name} of type {attr_type}",
                                   context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                                    extra={'parent_fqn': parent_fqn, 'attr_name': attr_name, 'attr_type': attr_type}))
                        resolved_type = self._resolve_attribute_type(attr_type, context)
                        if resolved_type:
                            return resolved_type
            
            # Recursive check up the inheritance chain
            inherited = self._resolve_inherited_method_or_attribute(parent_fqn, attr_name, context)
            if inherited:
                logger.trace(f"Found in grandparent: {inherited}",
                           context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                            extra={'grandparent_result': inherited, 'parent_fqn': parent_fqn}))
                return inherited
        
        logger.trace(f"Method/attribute {attr_name} not found in inheritance chain",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                     extra={'class_fqn': class_fqn, 'attr_name': attr_name}))
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
        
        logger.trace(f"Validation check: {fqn} {'EXISTS' if exists else 'NOT_FOUND'}",
                    context=LogContext(phase=AnalysisPhase.ANALYSIS,
                                     extra={'fqn': fqn, 'exists': exists}))
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
