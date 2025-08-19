"""
Name Resolution Engine - Reorganized Implementation - Code Atlas

Clean, modular implementation of the name resolver that preserves all the
sophisticated resolution logic from the original while eliminating architectural
anti-patterns and improving maintainability.

Key improvements:
- Centralized logging with configurable levels
- Single responsibility principle for all components  
- Consistent strategy interfaces
- Testable, isolated components
- Clear separation of concerns
- Comprehensive error handling
- Instance attribute type resolution
- Validation logic preservation
"""

import ast
from typing import Dict, List, Optional, Any, Protocol
from enum import Enum
from dataclasses import dataclass


# Configuration and Constants
class LogLevel(Enum):
    """Centralized log level definitions."""
    NONE = 0
    ERROR = 1
    SUCCESS = 1
    INFO = 2
    DEBUG = 3
    TRACE = 4


class ContextKeys:
    """Centralized context key definitions to avoid magic strings."""
    CURRENT_MODULE = 'current_module'
    CURRENT_CLASS = 'current_class'
    CURRENT_FUNCTION = 'current_function_name'
    SYMBOL_MANAGER = 'symbol_manager'
    IMPORT_MAP = 'import_map'


class ReconDataKeys:
    """Centralized reconnaissance data key definitions."""
    CLASSES = "classes"
    FUNCTIONS = "functions"
    STATE = "state"
    EXTERNAL_CLASSES = "external_classes"
    EXTERNAL_FUNCTIONS = "external_functions"


@dataclass
class ResolutionResult:
    """Structured container for resolution results with metadata."""
    fqn: Optional[str]
    strategy_used: str
    confidence: str
    metadata: Dict[str, Any] = None
    
    @property
    def success(self) -> bool:
        """Check if resolution was successful."""
        return self.fqn is not None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ResolutionLogger:
    """Centralized logging system with configurable verbosity."""
    
    def __init__(self, log_level: LogLevel = LogLevel.INFO):
        self.log_level = log_level
        self._resolution_stats = {
            'attempts': 0,
            'successes': 0,
            'failures': 0,
            'strategy_usage': {}
        }
    
    def log(self, message: str, level: LogLevel, prefix: str = "RESOLVE"):
        """Central logging method with consistent formatting."""
        if level.value <= self.log_level.value:
            indent = "  " * (level.value - 1)
            print(f"{indent}[{prefix}] {message}")
    
    def log_attempt(self, name_parts: List[str]):
        """Log resolution attempt."""
        self._resolution_stats['attempts'] += 1
        self.log(f"Attempting to resolve: {'.'.join(name_parts)}", LogLevel.INFO)
    
    def log_success(self, result: ResolutionResult):
        """Log successful resolution."""
        self._resolution_stats['successes'] += 1
        self._track_strategy_usage(result.strategy_used)
        self.log(f"RESOLVED to: {result.fqn} (via {result.strategy_used})", LogLevel.SUCCESS)
    
    def log_failure(self, name_parts: List[str]):
        """Log resolution failure."""
        self._resolution_stats['failures'] += 1
        self.log(f"FAILED to resolve: {'.'.join(name_parts)}", LogLevel.ERROR)
    
    def log_strategy_attempt(self, strategy_name: str, name: str, can_resolve: bool):
        """Log strategy attempt."""
        status = "CAN" if can_resolve else "SKIP"
        self.log(f"{strategy_name}: {status} resolve '{name}'", LogLevel.DEBUG, "STRATEGY")
    
    def log_chain_step(self, step: int, current_fqn: str, attr: str):
        """Log attribute chain resolution step."""
        self.log(f"Step {step}: {current_fqn}.{attr}", LogLevel.TRACE, "CHAIN")
    
    def log_validation(self, fqn: str, valid: bool):
        """Log validation result."""
        status = "PASS" if valid else "FAIL"
        self.log(f"Validation {status}: {fqn}", LogLevel.TRACE, "VALIDATE")
    
    def _track_strategy_usage(self, strategy_name: str):
        """Track which strategies are being used."""
        self._resolution_stats['strategy_usage'][strategy_name] = \
            self._resolution_stats['strategy_usage'].get(strategy_name, 0) + 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get resolution statistics for debugging."""
        total = self._resolution_stats['attempts']
        success_rate = self._resolution_stats['successes'] / max(total, 1)
        return {
            **self._resolution_stats,
            'success_rate': success_rate
        }


class ResolutionValidator:
    """Handles validation of resolved names."""
    
    def __init__(self, recon_data: Dict[str, Any], logger: ResolutionLogger):
        self.recon_data = recon_data
        self.logger = logger
    
    def validate_resolution(self, fqn: str) -> bool:
        """
        Validate that a resolved FQN exists in reconnaissance data.
        
        This matches the original resolver's _validate_resolution logic.
        """
        if not fqn:
            return False
        
        # Check if it's a known function/method
        if fqn in self.recon_data.get(ReconDataKeys.FUNCTIONS, {}):
            self.logger.log_validation(fqn, True)
            return True
        
        # Check if it's a known class
        if fqn in self.recon_data.get(ReconDataKeys.CLASSES, {}):
            self.logger.log_validation(fqn, True)
            return True
        
        # Check if it's a known state variable
        if fqn in self.recon_data.get(ReconDataKeys.STATE, {}):
            self.logger.log_validation(fqn, True)
            return True
        
        # Check external classes and functions
        if fqn in self.recon_data.get(ReconDataKeys.EXTERNAL_CLASSES, {}):
            self.logger.log_validation(fqn, True)
            return True
        
        if fqn in self.recon_data.get(ReconDataKeys.EXTERNAL_FUNCTIONS, {}):
            self.logger.log_validation(fqn, True)
            return True
        
        # For method calls on external classes, be more permissive
        # Example: threading.RLock.__enter__ might not be in recon_data but should be valid
        parts = fqn.split('.')
        if len(parts) >= 2:
            potential_class = '.'.join(parts[:-1])
            if potential_class in self.recon_data.get(ReconDataKeys.EXTERNAL_CLASSES, {}):
                self.logger.log_validation(fqn, True)
                return True
        
        self.logger.log_validation(fqn, False)
        return False


class ResolutionStrategy(Protocol):
    """Protocol defining the interface all resolution strategies must implement."""
    
    def can_resolve(self, name: str, context: Dict[str, Any]) -> bool:
        """Check if this strategy can resolve the given name."""
        ...
    
    def resolve(self, name: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve the name using this strategy."""
        ...


class BaseStrategy:
    """Base class providing common functionality for all resolution strategies."""
    
    def __init__(self, name: str, logger: ResolutionLogger, validator: ResolutionValidator):
        self.name = name
        self.logger = logger
        self.validator = validator
        self._resolution_count = 0
        self._success_count = 0
    
    def attempt_resolve(self, name: str, context: Dict[str, Any]) -> ResolutionResult:
        """Attempt resolution with logging, validation, and result wrapping."""
        self._resolution_count += 1
        
        try:
            can_resolve = self.can_resolve(name, context)
            self.logger.log_strategy_attempt(self.name, name, can_resolve)
            
            if not can_resolve:
                return ResolutionResult(None, self.name, "none")
            
            fqn = self.resolve(name, context)
            if fqn and self.validator.validate_resolution(fqn):
                self._success_count += 1
                confidence = "high"
            elif fqn:
                # Resolution succeeded but validation failed
                confidence = "low"
                self.logger.log(f"{self.name} resolved to unvalidated FQN: {fqn}", LogLevel.DEBUG, "STRATEGY")
            else:
                confidence = "low"
            
            return ResolutionResult(fqn, self.name, confidence)
            
        except Exception as e:
            self.logger.log(f"{self.name} error: {e}", LogLevel.ERROR, "STRATEGY")
            return ResolutionResult(None, self.name, "error", {"error": str(e)})
    
    def get_statistics(self) -> Dict[str, int]:
        """Get strategy-specific statistics."""
        return {
            'attempts': self._resolution_count,
            'successes': self._success_count,
            'success_rate': self._success_count / max(self._resolution_count, 1)
        }


class LocalVariableStrategy(BaseStrategy):
    """Resolves names from local variable symbol tables."""
    
    def __init__(self, logger: ResolutionLogger, validator: ResolutionValidator):
        super().__init__("LocalVariable", logger, validator)
    
    def can_resolve(self, name: str, context: Dict[str, Any]) -> bool:
        """Check if name exists in symbol manager."""
        symbol_manager = context.get(ContextKeys.SYMBOL_MANAGER)
        return symbol_manager and symbol_manager.get_variable_type(name) is not None
    
    def resolve(self, name: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve name through symbol manager."""
        symbol_manager = context.get(ContextKeys.SYMBOL_MANAGER)
        if symbol_manager:
            return symbol_manager.get_variable_type(name)
        return None


class SelfStrategy(BaseStrategy):
    """Resolves 'self' references to current class."""
    
    def __init__(self, logger: ResolutionLogger, validator: ResolutionValidator):
        super().__init__("Self", logger, validator)
    
    def can_resolve(self, name: str, context: Dict[str, Any]) -> bool:
        """Check if this is a 'self' reference in a class context."""
        return name == "self" and context.get(ContextKeys.CURRENT_CLASS) is not None
    
    def resolve(self, name: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve 'self' to current class FQN."""
        return context.get(ContextKeys.CURRENT_CLASS)


class ImportStrategy(BaseStrategy):
    """Resolves names from import aliases and external libraries."""
    
    def __init__(self, recon_data: Dict[str, Any], logger: ResolutionLogger, validator: ResolutionValidator):
        super().__init__("Import", logger, validator)
        self.recon_data = recon_data
    
    def can_resolve(self, name: str, context: Dict[str, Any]) -> bool:
        """Check if name exists in import map or external libraries."""
        import_map = context.get(ContextKeys.IMPORT_MAP, {})
        if name in import_map:
            return True
        
        # Check external classes and functions
        external_classes = self.recon_data.get(ReconDataKeys.EXTERNAL_CLASSES, {})
        external_functions = self.recon_data.get(ReconDataKeys.EXTERNAL_FUNCTIONS, {})
        
        for ext_info in external_classes.values():
            if ext_info.get("local_alias") == name:
                return True
        
        for ext_info in external_functions.values():
            if ext_info.get("local_alias") == name:
                return True
        
        return False
    
    def resolve(self, name: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve name through import map or external libraries."""
        # First check import map (primary mechanism)
        import_map = context.get(ContextKeys.IMPORT_MAP, {})
        if name in import_map:
            return import_map[name]
        
        # Check external classes
        external_classes = self.recon_data.get(ReconDataKeys.EXTERNAL_CLASSES, {})
        for ext_fqn, ext_info in external_classes.items():
            if ext_info.get("local_alias") == name:
                return ext_fqn
        
        # Check external functions
        external_functions = self.recon_data.get(ReconDataKeys.EXTERNAL_FUNCTIONS, {})
        for ext_fqn, ext_info in external_functions.items():
            if ext_info.get("local_alias") == name:
                return ext_fqn
        
        return None


class ModuleStrategy(BaseStrategy):
    """Fallback strategy that resolves to current module."""
    
    def __init__(self, logger: ResolutionLogger, validator: ResolutionValidator):
        super().__init__("Module", logger, validator)
    
    def can_resolve(self, name: str, context: Dict[str, Any]) -> bool:
        """Can attempt resolution if we have a current module."""
        return bool(context.get(ContextKeys.CURRENT_MODULE))
    
    def resolve(self, name: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve name to current module namespace."""
        current_module = context.get(ContextKeys.CURRENT_MODULE)
        if current_module:
            return f"{current_module}.{name}"
        return None


class AttributeResolver:
    """Handles complex attribute chain resolution with inheritance and type traversal."""
    
    def __init__(self, recon_data: Dict[str, Any], logger: ResolutionLogger, validator: ResolutionValidator):
        self.recon_data = recon_data
        self.logger = logger
        self.validator = validator
    
    def resolve_attribute_chain(self, name_parts: List[str], context: Dict[str, Any]) -> Optional[str]:
        """Resolve multi-part attribute access chains step by step."""
        if len(name_parts) < 2:
            return None
        
        base_name = name_parts[0]
        
        # Resolve base name first using inline strategy resolution
        base_fqn = self._resolve_base_name(base_name, context)
        if not base_fqn:
            self.logger.log(f"Failed to resolve base: {base_name}", LogLevel.DEBUG, "CHAIN")
            return None
        
        self.logger.log(f"Base resolved: {base_name} -> {base_fqn}", LogLevel.DEBUG, "CHAIN")
        
        # Walk the attribute chain step by step
        current_fqn = base_fqn
        for i, attr in enumerate(name_parts[1:], 1):
            self.logger.log_chain_step(i, current_fqn, attr)
            current_fqn = self._resolve_attribute(current_fqn, attr, context)
            if not current_fqn:
                self.logger.log(f"Failed at step {i}: .{attr}", LogLevel.DEBUG, "CHAIN")
                return None
            self.logger.log(f"Step {i} resolved: {current_fqn}", LogLevel.TRACE, "CHAIN")
        
        return current_fqn
    
    def _resolve_base_name(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve the base name using inline strategy logic to avoid circular imports."""
        # Inline LocalVariableStrategy logic
        symbol_manager = context.get(ContextKeys.SYMBOL_MANAGER)
        if symbol_manager and symbol_manager.get_variable_type(base_name) is not None:
            result = symbol_manager.get_variable_type(base_name)
            self.logger.log(f"LocalVariable resolved: {base_name} -> {result}", LogLevel.TRACE, "BASE")
            return result
        
        # Inline SelfStrategy logic
        if base_name == "self" and context.get(ContextKeys.CURRENT_CLASS) is not None:
            result = context.get(ContextKeys.CURRENT_CLASS)
            self.logger.log(f"Self resolved: {base_name} -> {result}", LogLevel.TRACE, "BASE")
            return result
        
        # Inline ImportStrategy logic
        import_map = context.get(ContextKeys.IMPORT_MAP, {})
        if base_name in import_map:
            result = import_map[base_name]
            self.logger.log(f"Import resolved: {base_name} -> {result}", LogLevel.TRACE, "BASE")
            return result
        
        # Check external classes and functions
        external_classes = self.recon_data.get(ReconDataKeys.EXTERNAL_CLASSES, {})
        for ext_fqn, ext_info in external_classes.items():
            if ext_info.get("local_alias") == base_name:
                self.logger.log(f"External class resolved: {base_name} -> {ext_fqn}", LogLevel.TRACE, "BASE")
                return ext_fqn
        
        external_functions = self.recon_data.get(ReconDataKeys.EXTERNAL_FUNCTIONS, {})
        for ext_fqn, ext_info in external_functions.items():
            if ext_info.get("local_alias") == base_name:
                self.logger.log(f"External function resolved: {base_name} -> {ext_fqn}", LogLevel.TRACE, "BASE")
                return ext_fqn
        
        # Inline ModuleStrategy logic (fallback)
        current_module = context.get(ContextKeys.CURRENT_MODULE)
        if current_module:
            result = f"{current_module}.{base_name}"
            self.logger.log(f"Module resolved: {base_name} -> {result}", LogLevel.TRACE, "BASE")
            return result
        
        return None
    
    def _resolve_attribute(self, context_fqn: str, attr: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Resolve attribute in context of given FQN.
        
        This is the core logic that handles:
        - State variable type resolution
        - Internal class method lookup with inheritance
        - External class method resolution
        - Class attribute resolution
        - Instance attribute type resolution
        - Function return type method chaining
        """
        candidate = f"{context_fqn}.{attr}"
        self.logger.log(f"Resolving attribute: {context_fqn}.{attr}", LogLevel.TRACE, "ATTR")
        
        # Strategy 1: State variable type resolution
        if context_fqn in self.recon_data.get(ReconDataKeys.STATE, {}):
            self.logger.log("Context is state variable, resolving through type", LogLevel.TRACE, "ATTR")
            state_type = self._get_state_type(context_fqn)
            if state_type:
                self.logger.log(f"State type resolved: {state_type}", LogLevel.TRACE, "ATTR")
                # Recursive resolution through the type
                return self._resolve_attribute(state_type, attr, context)
            else:
                self.logger.log("Could not resolve state type", LogLevel.TRACE, "ATTR")
        
        # Strategy 2: Check if context_fqn is a function that returns a type (METHOD CHAINING FIX)
        elif context_fqn in self.recon_data.get(ReconDataKeys.FUNCTIONS, {}):
            func_info = self.recon_data[ReconDataKeys.FUNCTIONS][context_fqn]
            return_type = func_info.get("return_type")
            if return_type and return_type != "None" and return_type != "Unknown":
                self.logger.log(f"Function returns type: {return_type}, resolving attribute on that", LogLevel.TRACE, "ATTR")
                
                # Handle quoted return types like "'ValidationRuleBuilder'"
                if return_type.startswith("'") and return_type.endswith("'"):
                    return_type = return_type[1:-1]
                
                resolved_return_type = self._resolve_attribute_type(return_type, context)
                if resolved_return_type:
                    self.logger.log(f"Return type resolved to: {resolved_return_type}, continuing chain", LogLevel.TRACE, "ATTR")
                    return self._resolve_attribute(resolved_return_type, attr, context)
                else:
                    self.logger.log(f"Could not resolve return type: {return_type}", LogLevel.TRACE, "ATTR")
        
        # Strategy 3: Internal class method/attribute lookup
        elif context_fqn in self.recon_data.get(ReconDataKeys.CLASSES, {}):
            self.logger.log("Context is internal class, checking methods/attributes", LogLevel.TRACE, "ATTR")
            
            # Direct method check
            if candidate in self.recon_data.get(ReconDataKeys.FUNCTIONS, {}):
                self.logger.log(f"Found direct method: {candidate}", LogLevel.TRACE, "ATTR")
                return candidate
            
            # **CRITICAL FIX: Instance attribute type resolution**
            class_info = self.recon_data[ReconDataKeys.CLASSES][context_fqn]
            class_attributes = class_info.get("attributes", {})
            if attr in class_attributes:
                attr_info = class_attributes[attr]
                attr_type = attr_info.get("type")
                
                if attr_type and attr_type != "Unknown":
                    self.logger.log(f"Found class attribute: {attr} of type {attr_type}", LogLevel.TRACE, "ATTR")
                    
                    # Resolve the attribute type to its FQN
                    resolved_type = self._resolve_attribute_type(attr_type, context)
                    if resolved_type:
                        self.logger.log(f"Attribute type resolved to: {resolved_type}", LogLevel.TRACE, "ATTR")
                        return resolved_type
                    else:
                        self.logger.log(f"Could not resolve attribute type: {attr_type}", LogLevel.TRACE, "ATTR")
                        # Even if we can't resolve the type, the attribute access itself might be valid
                        # Return the simple concatenation as fallback
                        return candidate
            
            # Inheritance chain check
            inherited_result = self._resolve_inherited_method_or_attribute(context_fqn, attr, context)
            if inherited_result:
                self.logger.log(f"Found in inheritance chain: {inherited_result}", LogLevel.TRACE, "ATTR")
                return inherited_result
        
        # Strategy 4: External class method resolution
        elif context_fqn in self.recon_data.get(ReconDataKeys.EXTERNAL_CLASSES, {}):
            self.logger.log("Context is external class, assuming method exists", LogLevel.TRACE, "ATTR")
            # For external classes, assume methods exist
            return candidate
        
        self.logger.log(f"No resolution path found for: {candidate}", LogLevel.TRACE, "ATTR")
        return None
    
    def _get_state_type(self, state_fqn: str) -> Optional[str]:
        """Get the type of a state variable."""
        state_info = self.recon_data.get(ReconDataKeys.STATE, {}).get(state_fqn)
        if state_info and isinstance(state_info, dict):
            return state_info.get("type")
        return None
    
    def _resolve_inherited_method_or_attribute(self, class_fqn: str, attr: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve method or attribute through inheritance chain."""
        class_info = self.recon_data.get(ReconDataKeys.CLASSES, {}).get(class_fqn, {})
        parents = class_info.get("parents", [])
        
        for parent_fqn in parents:
            candidate = f"{parent_fqn}.{attr}"
            
            # Check if method exists in parent
            if candidate in self.recon_data.get(ReconDataKeys.FUNCTIONS, {}):
                self.logger.log(f"Found inherited method: {candidate}", LogLevel.TRACE, "INHERIT")
                return candidate
            
            # Check parent's attributes
            if parent_fqn in self.recon_data.get(ReconDataKeys.CLASSES, {}):
                parent_info = self.recon_data[ReconDataKeys.CLASSES][parent_fqn]
                parent_attributes = parent_info.get("attributes", {})
                if attr in parent_attributes:
                    attr_type = parent_attributes[attr].get("type")
                    if attr_type and attr_type != "Unknown":
                        resolved_type = self._resolve_attribute_type(attr_type, context)
                        if resolved_type:
                            return resolved_type
            
            # Recurse up the inheritance chain
            inherited_result = self._resolve_inherited_method_or_attribute(parent_fqn, attr, context)
            if inherited_result:
                return inherited_result
        
        return None
    
    def _resolve_attribute_type(self, attr_type: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Resolve an attribute type to its FQN.
        
        This handles cases like:
        - connection: DatabaseConnection -> database_manager.DatabaseConnection
        - manager: AdminManager -> admin_manager.AdminManager
        - 'ValidationRuleBuilder' -> event_validator.ValidationRuleBuilder
        """
        # Handle quoted types like "'ValidationRuleBuilder'"
        if attr_type.startswith("'") and attr_type.endswith("'"):
            attr_type = attr_type[1:-1]
        
        # If it already looks like an FQN, return as-is
        if "." in attr_type:
            return attr_type
        
        # Try to resolve the type name using the same logic as base name resolution
        resolved = self._resolve_base_name(attr_type, context)
        if resolved:
            return resolved
        
        # Fallback: check if it's a class in the current module
        current_module = context.get(ContextKeys.CURRENT_MODULE)
        if current_module:
            candidate = f"{current_module}.{attr_type}"
            if candidate in self.recon_data.get(ReconDataKeys.CLASSES, {}):
                return candidate
        
        # Check all modules for this class name
        for class_fqn in self.recon_data.get(ReconDataKeys.CLASSES, {}):
            if class_fqn.endswith(f".{attr_type}"):
                self.logger.log(f"Found type in module: {class_fqn}", LogLevel.TRACE, "TYPE")
                return class_fqn
        
        # Check external classes
        for ext_class_fqn in self.recon_data.get(ReconDataKeys.EXTERNAL_CLASSES, {}):
            if ext_class_fqn.endswith(f".{attr_type}"):
                self.logger.log(f"Found external type: {ext_class_fqn}", LogLevel.TRACE, "TYPE")
                return ext_class_fqn
        
        # Final fallback: return the type as-is
        self.logger.log(f"Using type as-is: {attr_type}", LogLevel.TRACE, "TYPE")
        return attr_type


class NameResolver:
    """
    Clean, modular name resolver maintaining identical API to original.
    
    Key improvements:
    - Centralized logging with configurable levels
    - Single responsibility principle for all components
    - Consistent strategy interfaces  
    - Testable, isolated components
    - Clear separation of concerns
    - Comprehensive error handling
    - Instance attribute type resolution
    - Validation logic preservation
    """
    
    def __init__(self, recon_data: Dict[str, Any], log_level: LogLevel = LogLevel.INFO):
        """Initialize resolver with reconnaissance data and optional log level."""
        self.recon_data = recon_data
        self.logger = ResolutionLogger(log_level)
        self.validator = ResolutionValidator(recon_data, self.logger)
        self.attribute_resolver = AttributeResolver(recon_data, self.logger, self.validator)
        
        # Initialize strategies in same order as original for compatibility
        self.strategies = [
            LocalVariableStrategy(self.logger, self.validator),
            SelfStrategy(self.logger, self.validator),
            ImportStrategy(recon_data, self.logger, self.validator),
            ModuleStrategy(self.logger, self.validator)
        ]
    
    def resolve_name(self, name_parts: List[str], context: Dict[str, Any]) -> Optional[str]:
        """
        Resolve name parts to fully qualified name.
        
        Maintains identical behavior to original resolver while using
        clean, modular architecture.
        """
        if not name_parts:
            self.logger.log("No name parts provided", LogLevel.ERROR)
            return None
        
        self.logger.log_attempt(name_parts)
        
        try:
            # Handle single names and attribute chains differently
            if len(name_parts) == 1:
                result = self._resolve_single_name(name_parts[0], context)
            else:
                # For attribute chains, use the specialized resolver
                result = self.attribute_resolver.resolve_attribute_chain(name_parts, context)
            
            if result:
                success_result = ResolutionResult(result, "Chain", "high")
                self.logger.log_success(success_result)
                return result
            else:
                self.logger.log_failure(name_parts)
                return None
                
        except Exception as e:
            self.logger.log(f"Unexpected error: {e}", LogLevel.ERROR)
            self.logger.log_failure(name_parts)
            return None
    
    def _resolve_single_name(self, name: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve a single name using strategy pattern."""
        # Try each strategy in order
        for strategy in self.strategies:
            result = strategy.attempt_resolve(name, context)
            if result.success and result.confidence == "high":
                return result.fqn
        
        return None
    
    def extract_name_parts(self, node) -> List[str]:
        """
        Extract name parts from AST node.
        
        Maintains identical behavior to original implementation.
        """
        if isinstance(node, ast.Name):
            return [node.id]
        elif isinstance(node, ast.Attribute):
            parts = []
            current = node
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
                return list(reversed(parts))
        elif isinstance(node, ast.Call) and hasattr(node, 'func'):
            return self.extract_name_parts(node.func)
        
        return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive resolver statistics for debugging."""
        strategy_stats = {
            strategy.name: strategy.get_statistics() 
            for strategy in self.strategies
        }
        
        return {
            "resolver_stats": self.logger.get_statistics(),
            "strategy_stats": strategy_stats
        }
    
    def set_log_level(self, log_level: LogLevel):
        """Update logging level at runtime."""
        self.logger.log_level = log_level
