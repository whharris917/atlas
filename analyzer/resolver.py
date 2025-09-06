"""
Name Resolution Engine - Code Atlas

Contains the core NameResolver and its associated strategies for resolving
names and attribute chains within different contexts.
"""

import ast
import inspect
from typing import Dict, List, Optional, Any

from .logger import get_logger, AnalysisPhase, LogLevel
from .utils import get_source
from .validation import validate_resolution, is_known_external_method
from .attribute_resolution import resolve_attribute


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
        
        getattr(get_logger(), level.name.lower())(message, get_source(), extra)


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
        self.recon_data = recon_data  # Keep for strategy initialization and context creation
        self.strategies = [
            LocalVariableStrategy(),
            SelfStrategy(),
            ImportStrategy(recon_data),
            ModuleStrategy()
        ]
        self.context = None  # Will be set when resolution is called
        
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
        
        getattr(get_logger(), level.name.lower())(message, get_source(), extra)
    
    def resolve_name(self, name_parts: List[str], context: Dict[str, Any]) -> Optional[str]:
        """Resolve name using layered strategies with comprehensive logging."""
        if not name_parts:
            self._log(LogLevel.DEBUG, "Resolution failed: No name parts provided")
            return None
        
        # Create ResolutionContext for this resolution call
        self.context = ResolutionContext(
            symbol_manager=context.get('symbol_manager'),
            current_class=context.get('current_class'),
            current_module=context.get('current_module', ''),
            recon_data=self.recon_data,
            type_inference=context.get('type_inference')
        )

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
                if result and validate_resolution(result, self.recon_data):
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
            current_fqn = self._resolve_attribute(current_fqn, attr)
            if not current_fqn:
                self._log(LogLevel.TRACE, f"Chain resolution failed at step {i}: .{attr}",
                          extra={'chain_failure': 'attribute_resolution', 'step': i, 'attr': attr})
                return None
            self._log(LogLevel.TRACE, f"Chain step {i} resolved: {current_fqn}",
                      extra={'chain_step': i, 'resolved_fqn': current_fqn})
        
        return current_fqn
    
    def _resolve_attribute(self, context_fqn: str, attr: str) -> Optional[str]:
        """Resolve attribute using extracted attribute resolution functions."""
        return resolve_attribute(
            context_fqn, 
            attr, 
            self.context.recon_data, 
            self.context.current_module, 
            self.context.type_inference
        )

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


class ResolutionContext:
    """Encapsulates all context needed for name resolution."""
    
    def __init__(self, symbol_manager, current_class: Optional[str], 
                 current_module: str, recon_data: Dict[str, Any], 
                 type_inference=None):
        self.symbol_manager = symbol_manager
        self.current_class = current_class
        self.current_module = current_module
        self.recon_data = recon_data
        self.type_inference = type_inference
