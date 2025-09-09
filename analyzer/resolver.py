"""
Name resolution engine with inheritance-aware method resolution, attribute support, and external library support.
"""

import ast
from typing import Dict, List, Optional, Any

from .logger import LogLevel, get_logger
from .utils import get_source
from .validation import validate_resolution
from .attribute_resolution import resolve_attribute
from .chain_resolution import resolve_chain
from .resolution_strategies import (
    LocalVariableStrategy, 
    SelfStrategy, 
    ImportStrategy, 
    ModuleStrategy
)


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
        
        self._log(LogLevel.DEBUG, f"Name resolver initialized with {len(self.strategies)} strategies")
    
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
        """Resolve complex attribute chains using extracted chain resolution function."""
        # Create a closure that captures the context for _resolve_simple
        def resolve_simple_for_chain(name: str) -> Optional[str]:
            return self._resolve_simple(name, context)
        
        return resolve_chain(
            name_parts,
            resolve_simple_for_chain,
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
