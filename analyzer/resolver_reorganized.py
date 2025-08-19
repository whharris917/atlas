"""
Reorganized Name Resolver - Code Atlas (Session 3 Fixes)

This is a proof-of-concept reorganization of the original resolver that addresses
the key problems while maintaining identical API and behavior.

Session 3 fixes based on Test 3 diff analysis:
1. Fix spurious threading.RLock and uuid.uuid4 calls
2. Fix FQN prefix mismatches in SocketIO calls  
3. Ensure exact behavior matching with original resolver
4. Address context data handling issues
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


# DISABLED: Caching is temporarily disabled to match original behavior exactly
class ResolutionCache:
    """Simple caching for resolution results - DISABLED FOR EXACT BEHAVIOR MATCHING."""
    
    def __init__(self):
        self._cache: Dict[str, ResolutionResult] = {}
        self._hits = 0
        self._misses = 0
    
    def get_key(self, name_parts: List[str], context: Dict[str, Any]) -> str:
        """Generate cache key from name parts and relevant context."""
        module = context.get('current_module', '')
        class_name = context.get('current_class', '')  # Fixed: use 'current_class' not 'current_class_name'
        func_name = context.get('current_function_name', '')
        return f"{module}:{class_name}:{func_name}:{'.'.join(name_parts)}"
    
    def get(self, name_parts: List[str], context: Dict[str, Any]) -> Optional[ResolutionResult]:
        """Get cached result if available - DISABLED."""
        return None  # Always return None to disable caching
    
    def put(self, name_parts: List[str], context: Dict[str, Any], result: ResolutionResult):
        """Cache a resolution result - DISABLED."""
        pass  # Do nothing to disable caching
    
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
        # Use symbol_manager like original implementation
        symbol_manager = context.get('symbol_manager')
        if symbol_manager:
            var_type = symbol_manager.get_variable_type(base_name)
            return var_type is not None
        
        # Fallback to local_variables set if symbol_manager not available
        local_vars = context.get('local_variables', set())
        return base_name in local_vars
    
    def resolve(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        # Use symbol_manager like original implementation  
        symbol_manager = context.get('symbol_manager')
        if symbol_manager:
            var_type = symbol_manager.get_variable_type(base_name)
            if var_type:
                return var_type
        
        # Fallback behavior - local variables resolve to their contextual FQN
        current_module = context.get('current_module', '')
        current_class = context.get('current_class', '')  # Fixed: use 'current_class' not 'current_class_name'
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
                context.get('current_class') is not None)  # Fixed: use 'current_class' not 'current_class_name'
    
    def resolve(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        current_module = context.get('current_module', '')
        current_class = context.get('current_class', '')  # Fixed: use 'current_class' not 'current_class_name'
        return f"{current_module}.{current_class}"


class ImportStrategy(BaseStrategy):
    """Resolves imported names and external library references."""
    
    def __init__(self, recon_data: Dict[str, Any]):
        super().__init__("Import")
        self.recon_data = recon_data
    
    def can_resolve(self, base_name: str, context: Dict[str, Any]) -> bool:
        import_map = context.get('import_map', {})
        
        # First check direct import map
        if base_name in import_map:
            return True
            
        # Don't automatically resolve external references - be more conservative
        # Only resolve if we have explicit evidence
        return self._has_explicit_external_reference(base_name)
    
    def resolve(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        import_map = context.get('import_map', {})
        
        # Try direct import map first
        if base_name in import_map:
            return import_map[base_name]
        
        # Only try external resolution if explicitly available
        return self._resolve_external(base_name)
    
    def _has_explicit_external_reference(self, name: str) -> bool:
        """Check if name has explicit external library reference."""
        external_classes = self.recon_data.get("external_classes", {})
        external_functions = self.recon_data.get("external_functions", {})
        
        # Only resolve if we have an exact alias match
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
        # Be more conservative - only resolve if we have clear module context
        current_module = context.get('current_module', '')
        return bool(current_module)
    
    def resolve(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        current_module = context.get('current_module', '')
        if current_module:
            return f"{current_module}.{base_name}"
        return None


class AttributeResolver:
    """Handles complex attribute chain resolution."""
    
    def __init__(self, recon_data: Dict[str, Any]):
        self.recon_data = recon_data
    
    def resolve_attribute_chain(self, name_parts: List[str], context: Dict[str, Any]) -> Optional[str]:
        """Resolve multi-part attribute access chains."""
        if len(name_parts) < 2:
            return None
        
        base_name = name_parts[0]
        remaining_parts = name_parts[1:]
        
        # Try to resolve the base name first using standard strategies
        base_fqn = self._resolve_base_name(base_name, context)
        if not base_fqn:
            return None
        
        # Build the full attribute chain - be more conservative about chain building
        return f"{base_fqn}.{'.'.join(remaining_parts)}"
    
    def _resolve_base_name(self, base_name: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve the base name using available strategies."""
        # Create strategies in same order as original
        strategies = [
            LocalVariableStrategy(),
            SelfStrategy(),
            ImportStrategy(self.recon_data),
            ModuleStrategy()
        ]
        
        for strategy in strategies:
            result = strategy.attempt_resolve(base_name, context)
            if result.success:
                return result.fqn
        
        return None


class NameResolver:
    """
    Reorganized name resolver maintaining identical API to original.
    
    This proof-of-concept demonstrates architectural improvements while
    preserving exact behavioral compatibility.
    """
    
    def __init__(self, recon_data: Dict[str, Any]):
        """Initialize resolver with reconnaissance data."""
        self.recon_data = recon_data
        self.cache = ResolutionCache()
        self.attribute_resolver = AttributeResolver(recon_data)
        
        # Initialize strategies in same order as original
        self.strategies = [
            LocalVariableStrategy(),
            SelfStrategy(), 
            ImportStrategy(recon_data),
            ModuleStrategy()
        ]
    
    def resolve_name(self, name_parts: List[str], context: Dict[str, Any]) -> Optional[str]:
        """
        Resolve name parts to fully qualified name.
        
        Maintains identical behavior to original resolver while using
        cleaner internal architecture.
        """
        if not name_parts:
            return None
        
        ResolutionLogger.log_attempt(name_parts)
        
        # Handle single names and attribute chains differently
        if len(name_parts) == 1:
            result = self._resolve_single_name(name_parts[0], context)
        else:
            # For attribute chains, use the specialized resolver
            result = self.attribute_resolver.resolve_attribute_chain(name_parts, context)
        
        if result:
            ResolutionLogger.log_success(ResolutionResult(result, "Chain", "high"))
            return result
        else:
            ResolutionLogger.log_failure(name_parts)
            return None
    
    def _resolve_single_name(self, name: str, context: Dict[str, Any]) -> Optional[str]:
        """Resolve a single name using strategy pattern."""
        # Check cache first (currently disabled)
        cached = self.cache.get([name], context)
        if cached and cached.success:
            return cached.fqn
        
        # Try each strategy in order
        for strategy in self.strategies:
            result = strategy.attempt_resolve(name, context)
            if result.success:
                # Cache the result (currently disabled)
                self.cache.put([name], context, result)
                return result.fqn
        
        return None
    
    def extract_name_parts(self, node) -> List[str]:
        """
        Extract name parts from AST node.
        
        Maintains identical behavior to original implementation.
        """
        if node is None:
            return []
        
        try:
            if isinstance(node, ast.Name):
                return [node.id]
            elif isinstance(node, ast.Attribute):
                # Recursively build attribute chain
                base_parts = self.extract_name_parts(node.value)
                return base_parts + [node.attr] if base_parts else []
            elif isinstance(node, ast.Call):
                # For function calls, extract the function name
                return self.extract_name_parts(node.func)
            elif isinstance(node, ast.Subscript):
                # For subscripts, extract the base name
                return self.extract_name_parts(node.value)
            else:
                # For any other node type, return empty list
                return []
        except Exception:
            # On any error, return empty list to match original behavior
            return []


# Maintain exact API compatibility
__all__ = ['NameResolver']
