"""
Reorganized Name Resolver - Code Atlas

This is a proof-of-concept reorganization of the original resolver that addresses
the key problems while maintaining identical API and behavior.

Key improvements:
1. Clean separation of concerns
2. Optional logging that doesn't impact performance
3. Streamlined strategy pattern
4. Better error handling and validation
5. Result caching for performance
6. Enhanced readability and maintainability

This single-file implementation proves the refactoring concept before we
break it into separate modules.
"""

from typing import Dict, List, Any, Optional, Set
import ast

# Global logging level (0=none, 1=errors, 2=info, 3=debug)
LOG_LEVEL = 0


class ResolutionResult:
    """Container for resolution results with metadata."""
    
    def __init__(self, fqn: Optional[str], strategy: str = "", confidence: str = "low"):
        self.fqn = fqn
        self.strategy = strategy
        self.confidence = confidence
        self.success = fqn is not None
    
    def __str__(self) -> str:
        return self.fqn if self.fqn else "None"


class ResolutionLogger:
    """Centralized logging for resolution operations."""
    
    @staticmethod
    def log_attempt(name_parts: List[str], level: int = 2):
        if LOG_LEVEL >= level:
            print(f"    [RESOLVE] Attempting: {'.'.join(name_parts)}")
    
    @staticmethod
    def log_success(result: ResolutionResult, level: int = 1):
        if LOG_LEVEL >= level:
            print(f"    [RESOLVE] SUCCESS: {result.fqn} (via {result.strategy})")
    
    @staticmethod
    def log_failure(name_parts: List[str], level: int = 1):
        if LOG_LEVEL >= level:
            print(f"    [RESOLVE] FAILED: {'.'.join(name_parts)}")
    
    @staticmethod
    def log_strategy(strategy_name: str, name: str, can_resolve: bool, level: int = 3):
        if LOG_LEVEL >= level:
            status = "CAN" if can_resolve else "SKIP"
            print(f"      [STRATEGY] {status} {strategy_name}: {name}")


class ResolutionCache:
    """Simple caching for resolution results."""
    
    def __init__(self):
        self._cache: Dict[str, ResolutionResult] = {}
        self._hits = 0
        self._misses = 0
    
    def get_key(self, name_parts: List[str], context: Dict[str, Any]) -> str:
        """Generate cache key from name parts and relevant context."""
        module = context.get('current_module', '')
        class_name = context.get('current_class_name', '')
        func_name = context.get('current_function_name', '')
        return f"{module}:{class_name}:{func_name}:{'.'.join(name_parts)}"
    
    def get(self, name_parts: List[str], context: Dict[str, Any]) -> Optional[ResolutionResult]:
        """Get cached result if available."""
        key = self.get_key(name_parts, context)
        result = self._cache.get(key)
        if result:
            self._hits += 1
        else:
            self._misses += 1
        return result
    
    def put(self, name_parts: List[str], context: Dict[str, Any], result: ResolutionResult):
        """Cache a resolution result."""
        key = self.get_key(name_parts, context)
        self._cache[key] = result
    
    def stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {"hits": self._hits, "misses": self._misses, "size": len(self._cache)}


class BaseStrategy:
    """Base class for resolution strategies with common functionality."""
    
    def __init__(self, name: str):
        self.name = name
    
    def can_resolve(self, base_name: str, context: Dict[str, Any]) -> bool:
        """Check if this strategy can resolve the given name."""
        raise NotImplementedError(f"{self.name} must implement can_resolve")
    
    def resolve(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve the name using this strategy."""
        raise NotImplementedError(f"{self.name} must implement resolve")
    
    def attempt_resolve(self, base_name: str, context: Dict[str, Any]) -> ResolutionResult:
        """Attempt resolution with logging and result wrapping."""
        can_resolve = self.can_resolve(base_name, context)
        ResolutionLogger.log_strategy(self.name, base_name, can_resolve)
        
        if not can_resolve:
            return ResolutionResult(None, self.name, "none")
        
        fqn = self.resolve(base_name, context)
        confidence = "high" if fqn else "low"
        return ResolutionResult(fqn, self.name, confidence)


class LocalVariableStrategy(BaseStrategy):
    """Resolves local variables and parameters."""
    
    def __init__(self):
        super().__init__("LocalVariable")
    
    def can_resolve(self, base_name: str, context: Dict[str, Any]) -> bool:
        local_vars = context.get('local_variables', set())
        return base_name in local_vars
    
    def resolve(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        # Local variables resolve to their contextual FQN
        current_module = context.get('current_module', '')
        current_class = context.get('current_class_name', '')
        current_function = context.get('current_function_name', '')
        
        if current_function:
            if current_class:
                return f"{current_module}.{current_class}.{current_function}.{base_name}"
            else:
                return f"{current_module}.{current_function}.{base_name}"
        
        return f"{current_module}.{base_name}"


class SelfStrategy(BaseStrategy):
    """Resolves 'self' references in class methods."""
    
    def __init__(self):
        super().__init__("Self")
    
    def can_resolve(self, base_name: str, context: Dict[str, Any]) -> bool:
        return (base_name == 'self' and 
                context.get('current_class_name') is not None)
    
    def resolve(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        current_module = context.get('current_module', '')
        current_class = context.get('current_class_name', '')
        return f"{current_module}.{current_class}"


class ImportStrategy(BaseStrategy):
    """Resolves imported names and external library references."""
    
    def __init__(self, recon_data: Dict[str, Any]):
        super().__init__("Import")
        self.recon_data = recon_data
    
    def can_resolve(self, base_name: str, context: Dict[str, Any]) -> bool:
        import_map = context.get('import_map', {})
        return (base_name in import_map or 
                self._is_external_reference(base_name))
    
    def resolve(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        import_map = context.get('import_map', {})
        
        # Try direct import map first
        if base_name in import_map:
            return import_map[base_name]
        
        # Try external library resolution
        return self._resolve_external(base_name)
    
    def _is_external_reference(self, name: str) -> bool:
        """Check if name refers to external library component."""
        external_classes = self.recon_data.get("external_classes", {})
        external_functions = self.recon_data.get("external_functions", {})
        
        for ext_info in external_classes.values():
            if ext_info.get("local_alias") == name:
                return True
        
        for ext_info in external_functions.values():
            if ext_info.get("local_alias") == name:
                return True
        
        return False
    
    def _resolve_external(self, name: str) -> Optional[str]:
        """Resolve external library reference."""
        external_classes = self.recon_data.get("external_classes", {})
        external_functions = self.recon_data.get("external_functions", {})
        
        # Check external classes
        for ext_fqn, ext_info in external_classes.items():
            if ext_info.get("local_alias") == name:
                return ext_fqn
        
        # Check external functions
        for ext_fqn, ext_info in external_functions.items():
            if ext_info.get("local_alias") == name:
                return ext_fqn
        
        return None


class ModuleStrategy(BaseStrategy):
    """Fallback strategy that resolves to current module."""
    
    def __init__(self):
        super().__init__("Module")
    
    def can_resolve(self, base_name: str, context: Dict[str, Any]) -> bool:
        return True  # Always can try as fallback
    
    def resolve(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        current_module = context.get('current_module', '')
        return f"{current_module}.{base_name}"


class AttributeResolver:
    """Handles complex attribute chain resolution."""
    
    def __init__(self, recon_data: Dict[str, Any]):
        self.recon_data = recon_data
    
    def resolve_chain(self, base_fqn: str, attributes: List[str], context: Dict[str, Any]) -> Optional[str]:
        """Resolve attribute chain starting from base FQN."""
        current_fqn = base_fqn
        
        for attr in attributes:
            current_fqn = self._resolve_single_attribute(current_fqn, attr, context)
            if not current_fqn:
                return None
        
        return current_fqn
    
    def _resolve_single_attribute(self, context_fqn: str, attr: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve a single attribute in the context of the given FQN."""
        candidate = f"{context_fqn}.{attr}"
        
        # Try various resolution strategies
        resolvers = [
            self._resolve_direct_attribute,
            self._resolve_inherited_method,
            self._resolve_class_attribute,
            self._resolve_external_attribute
        ]
        
        for resolver in resolvers:
            result = resolver(context_fqn, attr, candidate, context)
            if result:
                return result
        
        return None
    
    def _resolve_direct_attribute(self, context_fqn: str, attr: str, candidate: str, context: Dict[str, Any]) -> Optional[str]:
        """Check if the attribute exists directly."""
        classes = self.recon_data.get("classes", {})
        functions = self.recon_data.get("functions", {})
        
        # Check if candidate exists as a known function or class
        if candidate in functions or candidate in classes:
            return candidate
        
        return None
    
    def _resolve_inherited_method(self, context_fqn: str, attr: str, candidate: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve method through inheritance hierarchy."""
        classes = self.recon_data.get("classes", {})
        
        if context_fqn in classes:
            class_info = classes[context_fqn]
            inheritance_chain = class_info.get("inheritance_chain", [])
            
            for base_class_fqn in inheritance_chain:
                inherited_candidate = f"{base_class_fqn}.{attr}"
                if inherited_candidate in self.recon_data.get("functions", {}):
                    return inherited_candidate
        
        return None
    
    def _resolve_class_attribute(self, context_fqn: str, attr: str, candidate: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve class-level attributes."""
        # This is a simplified implementation
        # In a full implementation, we'd check for actual class attributes
        return candidate if self._is_valid_identifier(attr) else None
    
    def _resolve_external_attribute(self, context_fqn: str, attr: str, candidate: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve attributes on external library objects."""
        external_classes = self.recon_data.get("external_classes", {})
        
        if context_fqn in external_classes:
            # For external classes, assume attribute exists (we can't introspect)
            return candidate
        
        return None
    
    def _is_valid_identifier(self, name: str) -> bool:
        """Check if name is a valid Python identifier."""
        return name.isidentifier() and not name.startswith('__')


class NameResolver:
    """
    Reorganized name resolver with clean architecture and improved performance.
    
    Maintains exact same API as original while providing:
    - Better separation of concerns
    - Optional performance-oriented logging
    - Result caching
    - Cleaner error handling
    - Enhanced maintainability
    """
    
    def __init__(self, recon_data: Dict[str, Any]):
        self.recon_data = recon_data
        
        # Initialize components
        self.cache = ResolutionCache()
        self.attribute_resolver = AttributeResolver(recon_data)
        
        # Initialize strategies in priority order
        self.strategies = [
            LocalVariableStrategy(),
            SelfStrategy(),
            ImportStrategy(recon_data),
            ModuleStrategy()  # Always last as fallback
        ]
    
    def resolve_name(self, name_parts: List[str], context: Dict[str, Any]) -> Optional[str]:
        """
        Resolve name using reorganized strategy system.
        
        Maintains identical behavior to original while providing better
        performance and maintainability.
        """
        if not name_parts:
            return None
        
        ResolutionLogger.log_attempt(name_parts)
        
        # Check cache first
        cached_result = self.cache.get(name_parts, context)
        if cached_result:
            ResolutionLogger.log_success(cached_result)
            return cached_result.fqn
        
        # Resolve based on complexity
        if len(name_parts) == 1:
            result = self._resolve_simple_name(name_parts[0], context)
        else:
            result = self._resolve_complex_name(name_parts, context)
        
        # Cache and log result
        resolution_result = ResolutionResult(
            result, 
            "cached" if cached_result else "computed",
            "high" if result else "none"
        )
        
        self.cache.put(name_parts, context, resolution_result)
        
        if result:
            ResolutionLogger.log_success(resolution_result)
        else:
            ResolutionLogger.log_failure(name_parts)
        
        return result
    
    def _resolve_simple_name(self, name: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve single name using strategy pattern."""
        for strategy in self.strategies:
            result = strategy.attempt_resolve(name, context)
            if result.success and self._validate_resolution(result.fqn):
                return result.fqn
        
        return None
    
    def _resolve_complex_name(self, name_parts: List[str], context: Dict[str, Any]) -> Optional[str]:
        """Resolve attribute chain (e.g., obj.method.attr)."""
        base_name = name_parts[0]
        attributes = name_parts[1:]
        
        # Resolve base name
        base_fqn = self._resolve_simple_name(base_name, context)
        if not base_fqn:
            return None
        
        # Resolve attribute chain
        return self.attribute_resolver.resolve_chain(base_fqn, attributes, context)
    
    def _validate_resolution(self, fqn: Optional[str]) -> bool:
        """Validate that resolution result is reasonable."""
        if not fqn:
            return False
        
        # Basic validation - ensure it's a reasonable identifier chain
        parts = fqn.split('.')
        return all(part and (part.isidentifier() or part in ['<module>', '<class>']) for part in parts)
    
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
        elif isinstance(node, ast.Call):
            return self.extract_name_parts(node.func)
        
        return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get resolver performance statistics."""
        return {
            "cache_stats": self.cache.stats(),
            "strategy_count": len(self.strategies),
            "strategies": [s.name for s in self.strategies]
        }


# Maintain original logging level behavior for compatibility
LOG_LEVEL = 0
