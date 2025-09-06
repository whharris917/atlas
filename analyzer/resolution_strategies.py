"""
Resolution strategies for name resolution.

Contains all strategy pattern implementations for different types of name resolution:
- LocalVariableStrategy: Resolves from symbol tables
- SelfStrategy: Resolves 'self' references
- ImportStrategy: Resolves imports and external libraries
- ModuleStrategy: Fallback module-level resolution
"""

from typing import Dict, Optional, Any
from .logger import LogLevel, get_logger
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
