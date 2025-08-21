# decorators.py
"""
Complex decorator patterns for stress testing decorator analysis.
Tests nested decorators, parameterized decorators, and class-based decorators.
"""
from typing import Callable, Any, Dict, Optional, Union, Type, List
from functools import wraps, partial
import time
import logging
from threading import Lock
from collections import defaultdict
import inspect
from database_manager import get_db_connection, TransactionManager
from admin_manager import AdminManager

# Global state for decorator tracking
PERFORMANCE_METRICS: Dict[str, List[float]] = defaultdict(list)
AUTH_CACHE: Dict[str, bool] = {}
RATE_LIMIT_CACHE: Dict[str, Dict[str, Any]] = defaultdict(dict)
TRACE_LOCK = Lock()

class DecoratorRegistry:
    """Registry for managing complex decorator patterns."""
    
    def __init__(self):
        self.registered_decorators: Dict[str, Callable] = {}
        self.decorator_chains: Dict[str, List[str]] = {}
        self.active_traces: List[str] = []
    
    def register_decorator(self, name: str, decorator: Callable) -> None:
        """Register a decorator for dynamic application."""
        self.registered_decorators[name] = decorator
    
    def get_decorator_chain(self, func_name: str) -> List[str]:
        """Get the decorator chain for a function."""
        return self.decorator_chains.get(func_name, [])

# Global registry instance
_decorator_registry = DecoratorRegistry()

def trace(func: Optional[Callable] = None, *, 
          level: str = 'INFO', 
          include_args: bool = True,
          include_result: bool = False) -> Callable:
    """
    Advanced tracing decorator with optional parameters.
    Tests parameterized decorator analysis.
    """
    
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            func_name = f"{f.__module__}.{f.__qualname__}"
            
            with TRACE_LOCK:
                _decorator_registry.active_traces.append(func_name)
            
            start_time = time.time()
            
            if include_args:
                logging.log(getattr(logging, level), 
                           f"TRACE ENTER: {func_name} args={args}, kwargs={kwargs}")
            else:
                logging.log(getattr(logging, level), f"TRACE ENTER: {func_name}")
            
            try:
                result = f(*args, **kwargs)
                
                if include_result:
                    logging.log(getattr(logging, level), 
                               f"TRACE EXIT: {func_name} result={result}")
                else:
                    logging.log(getattr(logging, level), f"TRACE EXIT: {func_name}")
                
                return result
            
            except Exception as e:
                logging.error(f"TRACE ERROR: {func_name} error={e}")
                raise
            
            finally:
                execution_time = time.time() - start_time
                PERFORMANCE_METRICS[func_name].append(execution_time)
                
                with TRACE_LOCK:
                    if func_name in _decorator_registry.active_traces:
                        _decorator_registry.active_traces.remove(func_name)
        
        # Register decorator application
        wrapper_name = f.__name__
        if wrapper_name not in _decorator_registry.decorator_chains:
            _decorator_registry.decorator_chains[wrapper_name] = []
        _decorator_registry.decorator_chains[wrapper_name].append('trace')
        
        return wrapper
    
    # Handle both @trace and @trace(...) patterns
    if func is None:
        return decorator
    else:
        return decorator(func)

def monitor_performance(func: Optional[Callable] = None, *,
                       threshold_ms: float = 1000.0,
                       alert_callback: Optional[Callable] = None) -> Callable:
    """
    Performance monitoring decorator with complex callback patterns.
    """
    
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = f(*args, **kwargs)
                return result
            
            finally:
                execution_time = (time.time() - start_time) * 1000
                func_name = f"{f.__module__}.{f.__qualname__}"
                
                PERFORMANCE_METRICS[func_name].append(execution_time)
                
                if execution_time > threshold_ms:
                    warning_msg = f"Performance alert: {func_name} took {execution_time:.2f}ms"
                    logging.warning(warning_msg)
                    
                    if alert_callback:
                        alert_callback(func_name, execution_time, args, kwargs)
        
        return wrapper
    
    if func is None:
        return decorator
    else:
        return decorator(func)

def validate_auth(required_role: Optional[str] = None,
                  check_session: bool = True) -> Callable:
    """
    Authentication validation decorator with complex role checking.
    """
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Complex authentication logic
            from session_manager import get_current_session, get_current_user
            
            if check_session:
                session = get_current_session()
                if not session or not session.is_valid():
                    raise PermissionError("Invalid session")
                
                user = get_current_user()
                if not user:
                    raise PermissionError("No authenticated user")
                
                # Check role if specified
                if required_role:
                    if not user.has_role(required_role):
                        raise PermissionError(f"Required role: {required_role}")
                
                # Cache auth result
                cache_key = f"{user.id}:{required_role or 'basic'}"
                AUTH_CACHE[cache_key] = True
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator

def rate_limit(calls: int = 10, period: int = 60, 
               per_user: bool = True,
               key_func: Optional[Callable] = None) -> Callable:
    """
    Rate limiting decorator with complex key generation and user tracking.
    """
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate rate limit key
            if key_func:
                rate_key = key_func(*args, **kwargs)
            elif per_user:
                from session_manager import get_current_user_id
                user_id = get_current_user_id()
                rate_key = f"{func.__name__}:{user_id}"
            else:
                rate_key = func.__name__
            
            current_time = time.time()
            
            # Check rate limit
            if rate_key not in RATE_LIMIT_CACHE:
                RATE_LIMIT_CACHE[rate_key] = {
                    'calls': [],
                    'blocked_until': 0
                }
            
            cache_entry = RATE_LIMIT_CACHE[rate_key]
            
            # Clean old calls
            cache_entry['calls'] = [
                call_time for call_time in cache_entry['calls']
                if current_time - call_time < period
            ]
            
            # Check if blocked
            if current_time < cache_entry['blocked_until']:
                raise RuntimeError(f"Rate limit exceeded. Try again later.")
            
            # Check call count
            if len(cache_entry['calls']) >= calls:
                cache_entry['blocked_until'] = current_time + period
                raise RuntimeError(f"Rate limit exceeded: {calls} calls per {period}s")
            
            # Record this call
            cache_entry['calls'].append(current_time)
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator

class ClassBasedDecorator:
    """
    Class-based decorator for testing complex decorator analysis.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.call_count = 0
        self.last_call_time = 0
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            self.call_count += 1
            self.last_call_time = time.time()
            
            # Pre-processing
            if self.config.get('log_calls', False):
                logging.info(f"Class decorator: calling {func.__name__} (#{self.call_count})")
            
            # Validation
            if self.config.get('validate_args', False):
                self._validate_arguments(func, args, kwargs)
            
            # Call function
            try:
                result = func(*args, **kwargs)
                
                # Post-processing
                if self.config.get('transform_result', False):
                    result = self._transform_result(result)
                
                return result
            
            except Exception as e:
                if self.config.get('log_errors', True):
                    logging.error(f"Class decorator: error in {func.__name__}: {e}")
                raise
        
        return wrapper
    
    def _validate_arguments(self, func: Callable, args: tuple, kwargs: dict) -> None:
        """Validate function arguments."""
        sig = inspect.signature(func)
        try:
            sig.bind(*args, **kwargs)
        except TypeError as e:
            raise ValueError(f"Argument validation failed: {e}")
    
    def _transform_result(self, result: Any) -> Any:
        """Transform function result."""
        transform_type = self.config.get('transform_type', 'none')
        
        if transform_type == 'wrap':
            return {'success': True, 'data': result, 'timestamp': time.time()}
        elif transform_type == 'log':
            logging.info(f"Function result: {result}")
            return result
        else:
            return result

# Factory function for creating parameterized decorators
def create_custom_decorator(name: str, 
                          pre_hook: Optional[Callable] = None,
                          post_hook: Optional[Callable] = None,
                          error_hook: Optional[Callable] = None) -> Callable:
    """
    Factory for creating custom decorators with hooks.
    Tests complex decorator factory patterns.
    """
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Pre-hook execution
            if pre_hook:
                pre_result = pre_hook(func, args, kwargs)
                if pre_result is False:
                    raise RuntimeError(f"Pre-hook failed for {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                
                # Post-hook execution
                if post_hook:
                    post_hook(func, args, kwargs, result)
                
                return result
            
            except Exception as e:
                # Error hook execution
                if error_hook:
                    error_hook(func, args, kwargs, e)
                raise
        
        # Register in global registry
        _decorator_registry.register_decorator(name, wrapper)
        
        return wrapper
    
    return decorator

# Advanced decorator combination patterns
def multi_decorator(*decorators: Callable) -> Callable:
    """
    Apply multiple decorators in sequence.
    Tests complex decorator chaining analysis.
    """
    
    def decorator(func: Callable) -> Callable:
        decorated_func = func
        
        # Apply decorators in reverse order (outermost first)
        for dec in reversed(decorators):
            decorated_func = dec(decorated_func)
        
        return decorated_func
    
    return decorator

# Conditional decorator
def conditional_decorator(condition: Union[bool, Callable], 
                         decorator: Callable) -> Callable:
    """
    Apply decorator only if condition is met.
    Tests conditional decorator application.
    """
    
    def decorator_wrapper(func: Callable) -> Callable:
        # Evaluate condition
        should_apply = condition
        if callable(condition):
            should_apply = condition(func)
        
        if should_apply:
            return decorator(func)
        else:
            return func
    
    return decorator_wrapper

# Decorator with complex parameter handling
def advanced_cache(ttl: int = 300,
                  key_func: Optional[Callable] = None,
                  serializer: Optional[Callable] = None,
                  validator: Optional[Callable] = None) -> Callable:
    """
    Advanced caching decorator with complex parameter patterns.
    """
    cache_storage: Dict[str, Dict[str, Any]] = {}
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            current_time = time.time()
            
            # Check cache
            if cache_key in cache_storage:
                entry = cache_storage[cache_key]
                if current_time - entry['timestamp'] < ttl:
                    # Validate cached result if validator provided
                    if validator and not validator(entry['result']):
                        del cache_storage[cache_key]
                    else:
                        return entry['result']
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Serialize result if serializer provided
            cached_result = result
            if serializer:
                cached_result = serializer(result)
            
            # Cache result
            cache_storage[cache_key] = {
                'result': cached_result,
                'timestamp': current_time
            }
            
            return result
        
        return wrapper
    
    return decorator

# Decorator with nested function creation
def create_monitoring_decorator(metrics_collector: Any) -> Callable:
    """
    Create a monitoring decorator that uses an external metrics collector.
    Tests decorator factories with external dependencies.
    """
    
    def monitor_decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Start monitoring
            monitor_id = metrics_collector.start_monitoring(func.__name__)
            
            try:
                result = func(*args, **kwargs)
                metrics_collector.record_success(monitor_id, len(str(result)))
                return result
            
            except Exception as e:
                metrics_collector.record_error(monitor_id, str(e))
                raise
            
            finally:
                metrics_collector.end_monitoring(monitor_id)
        
        return wrapper
    
    return monitor_decorator

# Complex nested decorator pattern
def transaction_decorator(isolation_level: str = 'READ_COMMITTED',
                         rollback_on: Optional[List[Type[Exception]]] = None) -> Callable:
    """
    Database transaction decorator with complex exception handling.
    """
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            
            db_conn = get_db_connection()
            tx_manager = TransactionManager(db_conn, isolation_level)
            
            try:
                tx_manager.begin_transaction()
                result = func(*args, **kwargs)
                tx_manager.commit_transaction()
                return result
            
            except Exception as e:
                should_rollback = True
                
                if rollback_on:
                    should_rollback = any(isinstance(e, exc_type) for exc_type in rollback_on)
                
                if should_rollback:
                    tx_manager.rollback_transaction()
                else:
                    tx_manager.commit_transaction()
                
                raise
            
            finally:
                tx_manager.close_connection()
        
        return wrapper
    
    return decorator

# Property decorator with complex getter/setter patterns
class PropertyDecorator:
    """
    Custom property decorator with validation and transformation.
    """
    
    def __init__(self, 
                 validator: Optional[Callable] = None,
                 transformer: Optional[Callable] = None,
                 cache: bool = False):
        self.validator = validator
        self.transformer = transformer
        self.cache = cache
        self._cache_storage: Dict[int, Any] = {}
    
    def __call__(self, func: Callable) -> property:
        
        def getter(instance):
            if self.cache:
                instance_id = id(instance)
                if instance_id in self._cache_storage:
                    return self._cache_storage[instance_id]
            
            value = func(instance)
            
            if self.transformer:
                value = self.transformer(value)
            
            if self.cache:
                self._cache_storage[id(instance)] = value
            
            return value
        
        def setter(instance, value):
            if self.validator and not self.validator(value):
                raise ValueError(f"Validation failed for {func.__name__}")
            
            # Store the value (this would typically set an instance attribute)
            instance_attr = f"_{func.__name__}"
            setattr(instance, instance_attr, value)
            
            # Clear cache if caching is enabled
            if self.cache:
                instance_id = id(instance)
                if instance_id in self._cache_storage:
                    del self._cache_storage[instance_id]
        
        return property(getter, setter)

# Module-level decorator applications for testing
@trace(level='DEBUG', include_args=True, include_result=True)
@monitor_performance(threshold_ms=500.0)
def complex_calculation(data: List[Dict[str, Any]], 
                       multiplier: float = 1.0) -> Dict[str, float]:
    """Function with multiple decorators for testing decorator chain analysis."""
    result = {}
    for item in data:
        if 'value' in item:
            result[item.get('key', 'unknown')] = item['value'] * multiplier
    return result

@validate_auth(required_role='admin')
@rate_limit(calls=5, period=300)
@ClassBasedDecorator({'log_calls': True, 'validate_args': True, 'transform_result': True})
def admin_operation(operation_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Admin operation with complex decorator stack."""
    
    admin_mgr = AdminManager()
    return admin_mgr.execute_operation(operation_type, parameters)

# Factory-created decorators
performance_monitor = create_custom_decorator(
    'performance_monitor',
    pre_hook=lambda f, a, k: logging.info(f"Starting {f.__name__}"),
    post_hook=lambda f, a, k, r: logging.info(f"Completed {f.__name__}"),
    error_hook=lambda f, a, k, e: logging.error(f"Error in {f.__name__}: {e}")
)

@performance_monitor
@advanced_cache(ttl=600, key_func=lambda x: f"cache_{hash(str(x))}")
def cached_expensive_operation(input_data: Any) -> Any:
    """Function using factory-created and parameterized decorators."""
    # Simulate expensive operation
    time.sleep(0.1)
    return f"processed_{input_data}"

# Conditional decorator usage
@conditional_decorator(
    condition=lambda func: func.__name__.startswith('debug_'),
    decorator=trace(level='DEBUG')
)
def debug_function() -> str:
    """Function with conditional decorator application."""
    return "debug output"

# Multi-decorator application
@multi_decorator(
    trace(),
    monitor_performance(),
    rate_limit(calls=10, period=60)
)
def multi_decorated_function(param: str) -> str:
    """Function with multiple decorators applied via multi_decorator."""
    return f"processed: {param}"
