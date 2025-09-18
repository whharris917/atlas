"""
Modern name resolution strategies for ExpressionTraversal operations.

This module provides a clean strategy pattern implementation that uses only
the latest refactored components (ScopeManager, etc.) and avoids deprecated
code like SymbolManager. These strategies are designed for use within the
ExpressionTraversal operations system.

Key Design Principles:
- Uses ScopeManager instead of deprecated SymbolManager
- Accepts standardized operation context parameters
- Returns FQNs that match recon_data structure expectations
- Implements the same logical resolution order as the original NameResolver
"""

from typing import Dict, Optional, Any
from .logger import LogLevel, get_logger
from .utils import get_source
from .scope_manager import ScopeManager


class NameResolutionStrategy:
    """Base class for name resolution strategies used in ExpressionTraversal."""
    
    def resolve(self, name: str, context_fqn: str, recon_data: Dict[str, Any], scope_manager: ScopeManager) -> Optional[str]:
        """Resolve the name using this strategy, returning FQN or None."""
        raise NotImplementedError

    def _log(self, level: LogLevel, message: str, extra: Optional[Dict[str, Any]] = None):
        """Enhanced logging with automatic source detection."""
        getattr(get_logger(), level.name.lower())(message, get_source(), extra)


class LocalVariableStrategy(NameResolutionStrategy):
    """Resolves names from local variable scope using ScopeManager."""
    
    def resolve(self, name: str, context_fqn: str, recon_data: Dict[str, Any], scope_manager: ScopeManager) -> Optional[str]:
        result = scope_manager.get_variable_type(name)
        
        if result:
            self._log(LogLevel.TRACE, f"LocalVariableStrategy.resolve({name}): {result}",
                      extra={'strategy': 'LocalVariable', 'variable': name, 'result': result})
        
        return result


class SelfReferenceStrategy(NameResolutionStrategy):
    """Resolves 'self' references to current class FQN."""
    
    def resolve(self, name: str, context_fqn: str, recon_data: Dict[str, Any], scope_manager: ScopeManager) -> Optional[str]:
        if name != "self":
            return None
            
        current_class = scope_manager.get_current_class_fqn()
        if current_class:
            self._log(LogLevel.TRACE, f"SelfReferenceStrategy.resolve({name}): {current_class}",
                      extra={'strategy': 'SelfReference', 'variable': name, 'result': current_class})
        
        return current_class


class InternalClassStrategy(NameResolutionStrategy):
    """Resolves class names from internal classes in recon_data."""
    
    def resolve(self, name: str, context_fqn: str, recon_data: Dict[str, Any], scope_manager: ScopeManager) -> Optional[str]:
        # Extract current module from context_fqn
        current_module = context_fqn.split('.')[0] if context_fqn else ''
        
        # First try local module class
        class_candidate = f"{current_module}.{name}"
        if class_candidate in recon_data.get("classes", {}):
            self._log(LogLevel.TRACE, f"InternalClassStrategy.resolve({name}): {class_candidate} (local)",
                      extra={'strategy': 'InternalClass', 'class_name': name, 'result': class_candidate, 'match_type': 'local'})
            return class_candidate
        
        # Then search globally for classes ending with this name
        for class_fqn in recon_data.get("classes", {}):
            if class_fqn.endswith(f".{name}"):
                self._log(LogLevel.TRACE, f"InternalClassStrategy.resolve({name}): {class_fqn} (global)",
                          extra={'strategy': 'InternalClass', 'class_name': name, 'result': class_fqn, 'match_type': 'global'})
                return class_fqn
        
        return None


class ExternalLibraryStrategy(NameResolutionStrategy):
    """Resolves names from external library imports."""
    
    def resolve(self, name: str, context_fqn: str, recon_data: Dict[str, Any], scope_manager: ScopeManager) -> Optional[str]:
        # Check external classes first
        for ext_class_fqn, ext_info in recon_data.get("external_classes", {}).items():
            if ext_info.get("local_alias") == name:
                self._log(LogLevel.TRACE, f"ExternalLibraryStrategy.resolve({name}): {ext_class_fqn} (external class)",
                          extra={'strategy': 'ExternalLibrary', 'name': name, 'result': ext_class_fqn, 'type': 'class'})
                return ext_class_fqn
        
        # Then check external functions
        for ext_func_fqn, ext_info in recon_data.get("external_functions", {}).items():
            if ext_info.get("local_alias") == name:
                self._log(LogLevel.TRACE, f"ExternalLibraryStrategy.resolve({name}): {ext_func_fqn} (external function)",
                          extra={'strategy': 'ExternalLibrary', 'name': name, 'result': ext_func_fqn, 'type': 'function'})
                return ext_func_fqn
        
        return None


class ModuleFallbackStrategy(NameResolutionStrategy):
    """Fallback strategy that assumes name is module-level."""
    
    def resolve(self, name: str, context_fqn: str, recon_data: Dict[str, Any], scope_manager: ScopeManager) -> Optional[str]:
        current_module = context_fqn.split('.')[0] if context_fqn else ''
        
        if not current_module:
            return None
            
        result = f"{current_module}.{name}"
        
        self._log(LogLevel.TRACE, f"ModuleFallbackStrategy.resolve({name}): {result} (fallback)",
                  extra={'strategy': 'ModuleFallback', 'name': name, 'result': result, 'current_module': current_module})
        return result


class ModuleStateStrategy(NameResolutionStrategy):
    """Resolves names from module-level state variables."""
    
    def resolve(self, name: str, context_fqn: str, recon_data: Dict[str, Any], scope_manager: ScopeManager) -> Optional[str]:
        # Extract current module from context_fqn
        current_module = context_fqn.split('.')[0] if context_fqn else None
        if not current_module:
            self._log(LogLevel.TRACE, f"ModuleStateStrategy: no current_module from context_fqn: {context_fqn}",
                      extra={'strategy': 'ModuleState', 'variable': name, 'context_fqn': context_fqn})
            return None
        
        # Check if this name exists as a module state variable
        # Format: module.variable_name
        state_fqn = f"{current_module}.{name}"
        state_data = recon_data.get("state", {})
        
        self._log(LogLevel.TRACE, f"ModuleStateStrategy checking: {state_fqn}",
                  extra={'strategy': 'ModuleState', 'variable': name, 'state_fqn': state_fqn, 
                         'state_exists': state_fqn in state_data})
        
        if state_fqn in state_data:
            self._log(LogLevel.TRACE, f"ModuleStateStrategy.resolve({name}): {state_fqn}",
                      extra={'strategy': 'ModuleState', 'variable': name, 'result': state_fqn})
            return state_fqn
        
        self._log(LogLevel.TRACE, f"ModuleStateStrategy failed: {state_fqn} not found",
                  extra={'strategy': 'ModuleState', 'variable': name, 'state_fqn': state_fqn})
        return None
    

class NameResolutionEngine:
    """
    Unified name resolution engine using modern strategy pattern.
    
    This engine implements the same logical resolution order as the original
    NameResolver but uses only refactored components and provides a clean
    interface for ExpressionTraversal operations.
    """
    
    def __init__(self):
        self.strategies = [
            LocalVariableStrategy(),
            SelfReferenceStrategy(),
            InternalClassStrategy(),
            ModuleStateStrategy(),
            ExternalLibraryStrategy(),
            ModuleFallbackStrategy()
        ]
        self.logger = get_logger()
    
    def resolve_name(self, name: str, context_fqn: str, recon_data: Dict[str, Any], scope_manager: ScopeManager) -> Optional[str]:
        """
        Resolve a simple name using the strategy chain.
        
        Args:
            name: The name to resolve (e.g., 'DatabaseConnection')
            context_fqn: Current context FQN (e.g., 'sample.process_data')
            recon_data: Reconnaissance data structure
            scope_manager: Current scope manager instance
            
        Returns:
            Resolved FQN or None if resolution fails
        """
        self._log(LogLevel.DEBUG, f"Resolving name: {name}",
                  extra={'name': name, 'context': context_fqn, 'strategies_count': len(self.strategies)})
        
        for i, strategy in enumerate(self.strategies):
            strategy_name = strategy.__class__.__name__
            self._log(LogLevel.TRACE, f"Trying strategy {i+1}: {strategy_name}",
                      extra={'strategy_index': i, 'strategy': strategy_name, 'name': name})
            
            result = strategy.resolve(name, context_fqn, recon_data, scope_manager)
            if result:
                self._log(LogLevel.DEBUG, f"Strategy {strategy_name} resolved: {name} -> {result}",
                          extra={'successful_strategy': strategy_name, 'name': name, 'result': result})
                return result
            else:
                self._log(LogLevel.TRACE, f"Strategy {strategy_name} returned None",
                          extra={'failed_strategy': strategy_name, 'name': name})
        
        self._log(LogLevel.WARNING, f"All strategies failed for: {name}",
                  extra={'resolution_result': 'failed', 'name': name, 'context': context_fqn})
        return None
    
    def _log(self, level: LogLevel, message: str, extra: Optional[Dict[str, Any]] = None):
        """Enhanced logging with automatic source detection."""
        getattr(get_logger(), level.name.lower())(message, get_source(), extra)
