"""
Simple Resolution Visitor - Code Atlas

Handles basic single-name resolution using layered strategy pattern.
This visitor focuses on resolving single names through various contexts.
"""

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from ...utils import LOG_LEVEL


class ResolutionStrategy(ABC):
    """Base class for name resolution strategies."""
    
    @abstractmethod
    def can_resolve(self, name: str, context: Dict[str, Any]) -> bool:
        """Check if this strategy can resolve the given name."""
        pass
    
    @abstractmethod
    def resolve(self, name: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve the name using this strategy."""
        pass


class LocalVariableStrategy(ResolutionStrategy):
    """Resolves names from local variable symbol tables."""
    
    def can_resolve(self, name: str, context: Dict[str, Any]) -> bool:
        symbol_manager = context.get('symbol_manager')
        can_resolve = symbol_manager and symbol_manager.get_variable_type(name) is not None
        if LOG_LEVEL >= 3:
            print(f"      [STRATEGY] LocalVariableStrategy.can_resolve({name}): {can_resolve}")
        return can_resolve
    
    def resolve(self, name: str, context: Dict[str, Any]) -> Optional[str]:
        symbol_manager = context['symbol_manager']
        result = symbol_manager.get_variable_type(name)
        if LOG_LEVEL >= 3:
            print(f"      [STRATEGY] LocalVariableStrategy.resolve({name}): {result}")
        return result


class SelfStrategy(ResolutionStrategy):
    """Resolves 'self' references to current class."""
    
    def can_resolve(self, name: str, context: Dict[str, Any]) -> bool:
        can_resolve = name == "self" and context.get('current_class')
        if LOG_LEVEL >= 3:
            print(f"      [STRATEGY] SelfStrategy.can_resolve({name}): {can_resolve}")
        return can_resolve
    
    def resolve(self, name: str, context: Dict[str, Any]) -> Optional[str]:
        result = context['current_class']
        if LOG_LEVEL >= 3:
            print(f"      [STRATEGY] SelfStrategy.resolve({name}): {result}")
        return result


class ImportStrategy(ResolutionStrategy):
    """Resolves names from import aliases and external libraries."""
    
    def __init__(self, recon_data: Dict[str, Any]):
        self.recon_data = recon_data
    
    def can_resolve(self, name: str, context: Dict[str, Any]) -> bool:
        import_map = context.get('import_map', {})
        can_resolve_import = name in import_map
        can_resolve_external = self._can_resolve_external(name)
        can_resolve = can_resolve_import or can_resolve_external
        
        if LOG_LEVEL >= 3:
            print(f"      [STRATEGY] ImportStrategy.can_resolve({name}): {can_resolve} (import: {can_resolve_import}, external: {can_resolve_external})")
        return can_resolve
    
    def resolve(self, name: str, context: Dict[str, Any]) -> Optional[str]:
        import_map = context.get('import_map', {})
        
        # First try direct import map
        if name in import_map:
            result = import_map[name]
            if LOG_LEVEL >= 3:
                print(f"      [STRATEGY] ImportStrategy.resolve({name}): {result} (from import map)")
            return result
        
        # Then try external library resolution
        external_result = self._resolve_external(name)
        if external_result:
            if LOG_LEVEL >= 3:
                print(f"      [STRATEGY] ImportStrategy.resolve({name}): {external_result} (external)")
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
    
    def can_resolve(self, name: str, context: Dict[str, Any]) -> bool:
        if LOG_LEVEL >= 3:
            print(f"      [STRATEGY] ModuleStrategy.can_resolve({name}): True (fallback)")
        return True  # Always can try this as fallback
    
    def resolve(self, name: str, context: Dict[str, Any]) -> Optional[str]:
        current_module = context.get('current_module', '')
        result = f"{current_module}.{name}"
        if LOG_LEVEL >= 3:
            print(f"      [STRATEGY] ModuleStrategy.resolve({name}): {result}")
        return result


class SimpleResolutionVisitor:
    """
    Handles simple single-name resolution using layered strategy pattern.
    
    This visitor focuses on resolving single names through various contexts:
    - Local variables
    - Self references
    - Import aliases
    - Module fallback
    """
    
    def __init__(self, recon_data: Dict[str, Any]):
        self.recon_data = recon_data
        
        # Initialize resolution strategies in order of precedence
        self.strategies = [
            LocalVariableStrategy(),
            SelfStrategy(),
            ImportStrategy(recon_data),
            ModuleStrategy()
        ]
    
    def resolve(self, name: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Resolve a single name using the strategy pattern.
        
        Args:
            name: Single name to resolve
            context: Resolution context
            
        Returns:
            Fully qualified name if resolved, None otherwise
        """
        if LOG_LEVEL >= 2:
            print(f"      [SIMPLE] Resolving single name: {name}")
        
        # Try each strategy in order
        for i, strategy in enumerate(self.strategies):
            strategy_name = strategy.__class__.__name__
            if LOG_LEVEL >= 3:
                print(f"      [STRATEGY] Trying strategy {i+1}: {strategy_name}")
            
            if strategy.can_resolve(name, context):
                result = strategy.resolve(name, context)
                if result and self._validate_resolution(result):
                    if LOG_LEVEL >= 2:
                        print(f"      [STRATEGY] SUCCESS {strategy_name}: {name} -> {result}")
                    return result
                else:
                    if LOG_LEVEL >= 3:
                        print(f"      [STRATEGY] FAIL {strategy_name} failed validation")
            else:
                if LOG_LEVEL >= 3:
                    print(f"      [STRATEGY] SKIP {strategy_name} cannot resolve")
        
        if LOG_LEVEL >= 2:
            print(f"      [SIMPLE] FAILED All strategies failed for: {name}")
        return None
    
    def _validate_resolution(self, fqn: str) -> bool:
        """
        Validate that a resolved FQN exists in reconnaissance data.
        
        Args:
            fqn: Fully qualified name to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not fqn:
            return False
        
        # Check if FQN exists in any reconnaissance data structure
        if fqn in self.recon_data.get("functions", {}):
            return True
        
        if fqn in self.recon_data.get("classes", {}):
            return True
        
        if fqn in self.recon_data.get("state", {}):
            return True
        
        if fqn in self.recon_data.get("external_classes", {}):
            return True
        
        if fqn in self.recon_data.get("external_functions", {}):
            return True
        
        # Allow module-level names (fallback validation)
        if "." in fqn:
            module_part = fqn.rsplit(".", 1)[0]
            return module_part in self.recon_data.get("imports", {}).values()
        
        return False
