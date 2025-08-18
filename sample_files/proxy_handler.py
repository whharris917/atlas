# proxy_handler.py
"""
Complex proxy handler patterns for testing advanced method resolution and chaining.
Tests proxy patterns, delegation, and complex object relationships.
"""
from typing import Any, Dict, List, Optional, Callable, Union, TypeVar, Generic, Set
from abc import ABC, abstractmethod
from functools import wraps
import threading
import time
from dataclasses import dataclass
from contextlib import contextmanager

from decorators import trace, monitor_performance, validate_auth, rate_limit

T = TypeVar('T')

@dataclass
class ProxyConfig:
    """Configuration for proxy behavior."""
    cache_enabled: bool = True
    logging_enabled: bool = True
    metrics_enabled: bool = True
    timeout_seconds: float = 30.0
    retry_attempts: int = 3
    circuit_breaker_enabled: bool = False

class ProxyMetrics:
    """Metrics collection for proxy operations."""
    
    def __init__(self):
        self.call_count = 0
        self.success_count = 0
        self.error_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_execution_time = 0.0
        self.average_execution_time = 0.0
        self.last_error_time: Optional[float] = None
        self.last_success_time: Optional[float] = None
    
    def record_call(self, execution_time: float, success: bool, cache_hit: bool = False) -> None:
        """Record proxy method call metrics."""
        self.call_count += 1
        self.total_execution_time += execution_time
        self.average_execution_time = self.total_execution_time / self.call_count
        
        if success:
            self.success_count += 1
            self.last_success_time = time.time()
        else:
            self.error_count += 1
            self.last_error_time = time.time()
        
        if cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
    
    def get_success_rate(self) -> float:
        """Calculate success rate."""
        return self.success_count / max(self.call_count, 1)
    
    def get_cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total_cacheable = self.cache_hits + self.cache_misses
        return self.cache_hits / max(total_cacheable, 1)

class BaseProxy(ABC):
    """Abstract base proxy with core functionality."""
    
    def __init__(self, target: Any, config: ProxyConfig = None):
        self.target = target
        self.config = config or ProxyConfig()
        self.metrics = ProxyMetrics()
        self.cache: Dict[str, Any] = {}
        self.lock = threading.RLock()
        self.circuit_breaker_open = False
        self.circuit_breaker_failures = 0
        self.circuit_breaker_last_failure = 0.0
    
    @abstractmethod
    def _proxy_method_call(self, method_name: str, *args, **kwargs) -> Any:
        """Abstract method for proxying method calls."""
        pass
    
    @trace
    def __getattr__(self, name: str) -> Any:
        """Dynamic attribute access with proxy behavior."""
        # Check if target has the attribute
        if hasattr(self.target, name):
            attr = getattr(self.target, name)
            
            # If it's callable, wrap it
            if callable(attr):
                return self._create_proxy_method(name, attr)
            else:
                return attr
        
        raise AttributeError(f"'{type(self.target).__name__}' object has no attribute '{name}'")
    
    def _create_proxy_method(self, method_name: str, original_method: Callable) -> Callable:
        """Create a proxy wrapper for a method."""
        
        @wraps(original_method)
        def proxy_wrapper(*args, **kwargs):
            return self._proxy_method_call(method_name, *args, **kwargs)
        
        return proxy_wrapper
    
    @trace
    @monitor_performance
    def _execute_with_circuit_breaker(self, method_name: str, method: Callable, *args, **kwargs) -> Any:
        """Execute method with circuit breaker pattern."""
        if self.circuit_breaker_open:
            # Check if we should try to close the circuit breaker
            if time.time() - self.circuit_breaker_last_failure > 60:  # 1 minute timeout
                self.circuit_breaker_open = False
                self.circuit_breaker_failures = 0
            else:
                raise RuntimeError(f"Circuit breaker open for {method_name}")
        
        try:
            result = method(*args, **kwargs)
            # Reset failure count on success
            self.circuit_breaker_failures = 0
            return result
        
        except Exception as e:
            self.circuit_breaker_failures += 1
            self.circuit_breaker_last_failure = time.time()
            
            # Open circuit breaker after 3 failures
            if self.circuit_breaker_failures >= 3:
                self.circuit_breaker_open = True
            
            raise e
    
    def _get_cache_key(self, method_name: str, *args, **kwargs) -> str:
        """Generate cache key for method call."""
        return f"{method_name}:{hash(str(args) + str(sorted(kwargs.items())))}"
    
    @contextmanager
    def _metrics_context(self, method_name: str):
        """Context manager for metrics collection."""
        start_time = time.time()
        success = False
        cache_hit = False
        
        try:
            yield lambda: setattr(self, '_cache_hit', True)  # Callback to mark cache hit
            success = True
        except Exception:
            success = False
            raise
        finally:
            execution_time = time.time() - start_time
            cache_hit = getattr(self, '_cache_hit', False)
            setattr(self, '_cache_hit', False)  # Reset for next call
            
            self.metrics.record_call(execution_time, success, cache_hit)

class DataProxy(BaseProxy):
    """Proxy for data access with caching and validation."""
    
    def __init__(self, data_source: Any, config: ProxyConfig = None):
        super().__init__(data_source, config)
        self.data_validators: Dict[str, List[Callable]] = {}
        self.data_transformers: Dict[str, List[Callable]] = {}
    
    @trace
    def _proxy_method_call(self, method_name: str, *args, **kwargs) -> Any:
        """Proxy data access method calls with caching and validation."""
        with self._metrics_context(method_name) as mark_cache_hit:
            
            # Check cache first
            if self.config.cache_enabled:
                cache_key = self._get_cache_key(method_name, *args, **kwargs)
                
                with self.lock:
                    if cache_key in self.cache:
                        mark_cache_hit()

class HavenProxy(BaseProxy):
    """Haven-specific proxy for testing complex interactions."""
    
    def __init__(self, target: Any, config: ProxyConfig = None):
        super().__init__(target, config)
        self.user_cache: Dict[str, Any] = {}
        self.room_permissions: Dict[str, Set[str]] = {}
    
    def validate_user_credentials(self, auth_data: Dict[str, Any]) -> bool:
        """Validate user credentials."""
        return auth_data.get('user_id') is not None
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences."""
        return self.user_cache.get(user_id, {})
    
    def validate_room_access(self, user_id: str, room_name: str) -> bool:
        """Validate room access permissions."""
        return room_name in self.room_permissions.get(user_id, set())
    
    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get user information."""
        return {"user_id": user_id, "active": True}
    
    def validate_admin_role(self, user_id: str) -> bool:
        """Check if user has admin role."""
        return user_id.startswith('admin_')
    
    def validate_moderator_role(self, user_id: str) -> bool:
        """Check if user has moderator role."""
        return user_id.startswith('mod_') or self.validate_admin_role(user_id)
    
    def get_runner_capabilities(self) -> Dict[str, Any]:
        """Get runner capabilities."""
        return {"version": "1.0", "features": ["test", "validate"]}
    
    def get_guest_limitations(self) -> Dict[str, Any]:
        """Get guest limitations."""
        return {"max_messages": 10, "timeout": 300}
    
    def validate_message_content(self, message: str, user_id: str) -> bool:
        """Validate message content."""
        return len(message.strip()) > 0 and len(message) <= 1000
    
    def log_room_message(self, room: str, user_id: str, message: str) -> None:
        """Log room message."""
        pass
    
    def validate_direct_message_permission(self, sender_id: str, recipient_id: str) -> bool:
        """Validate direct message permissions."""
        return True
    
    def validate_broadcast_permission(self, user_id: str) -> bool:
        """Validate broadcast permissions."""
        return self.validate_admin_role(user_id)
    
    def get_room_statistics(self, room_name: str) -> Dict[str, Any]:
        """Get room statistics."""
        return {"member_count": 0, "message_count": 0}
    
    def validate_event_data(self, event_name: str, data: Dict[str, Any], user_id: str) -> bool:
        """Validate event data."""
        return True
    
    def process_event(self, event_name: str, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Process event."""
        return {"success": True}
    
    def user_exists(self, user_id: str) -> bool:
        """Check if user exists."""
        return user_id is not None
    
    def _proxy_method_call(self, method_name: str, *args, **kwargs) -> Any:
        """Implementation of abstract proxy method."""
        return getattr(self.target, method_name)(*args, **kwargs)


class UserProxy(BaseProxy):
    """User-specific proxy for testing user interactions."""
    
    def __init__(self, user_data: Dict[str, Any], config: ProxyConfig = None):
        super().__init__(user_data, config)
        self.user_data = user_data
    
    def has_role(self, role: str) -> bool:
        """Check if user has specified role."""
        user_roles = self.user_data.get('roles', [])
        return role in user_roles
    
    @property
    def id(self) -> str:
        """Get user ID."""
        return self.user_data.get('id', 'unknown')
    
    def _proxy_method_call(self, method_name: str, *args, **kwargs) -> Any:
        """Implementation of abstract proxy method."""
        if hasattr(self.user_data, method_name):
            return getattr(self.user_data, method_name)(*args, **kwargs)
        return None
