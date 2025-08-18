# inheritance_complex.py
"""
Complex inheritance patterns for stress testing inheritance-aware method resolution.
Tests multiple inheritance, mixin patterns, abstract base classes, and method resolution order.
"""
from typing import Any, Dict, List, Optional, Union, Protocol, TypeVar, Generic
from abc import ABC, abstractmethod
import asyncio
from dataclasses import dataclass, field
from enum import Enum, auto
from contextlib import contextmanager

from decorators import trace, monitor_performance, validate_auth
from proxy_handler import BaseProxy, DataProxy
from session_manager import SessionManager

T = TypeVar('T')
U = TypeVar('U')

class Priority(Enum):
    """Priority levels for task processing."""
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()

@dataclass
class ProcessingResult:
    """Result container for processing operations."""
    success: bool
    data: Any = None
    errors: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    timestamp: float = 0.0

# Abstract base classes for testing inheritance resolution
class AbstractProcessor(ABC):
    """Abstract base processor with required methods."""
    
    def __init__(self, processor_id: str):
        self.processor_id = processor_id
        self.processed_count = 0
        self.error_count = 0
    
    @abstractmethod
    def process_data(self, data: Any) -> ProcessingResult:
        """Abstract method that must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def validate_input(self, data: Any) -> bool:
        """Abstract validation method."""
        pass
    
    def get_statistics(self) -> Dict[str, int]:
        """Concrete method available to all subclasses."""
        return {
            'processed': self.processed_count,
            'errors': self.error_count,
            'success_rate': (self.processed_count - self.error_count) / max(self.processed_count, 1)
        }
    
    @trace
    def log_operation(self, operation: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Logging method with decorator."""
        print(f"[{self.processor_id}] {operation}: {details or {}}")

class AsyncProcessor(AbstractProcessor):
    """Async processing capabilities mixin."""
    
    def __init__(self, processor_id: str):
        super().__init__(processor_id)
        self.async_queue: List[Any] = []
        self.batch_size = 10
    
    async def async_process_data(self, data: Any) -> ProcessingResult:
        """Async version of process_data."""
        # Simulate async operation
        await asyncio.sleep(0.01)
        return self.process_data(data)
    
    async def batch_process(self, data_list: List[Any]) -> List[ProcessingResult]:
        """Batch processing with async operations."""
        results = []
        
        for i in range(0, len(data_list), self.batch_size):
            batch = data_list[i:i + self.batch_size]
            
            # Process batch concurrently
            tasks = [self.async_process_data(item) for item in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle results and exceptions
            for result in batch_results:
                if isinstance(result, Exception):
                    error_result = ProcessingResult(success=False, errors=[str(result)])
                    results.append(error_result)
                else:
                    results.append(result)
        
        return results
    
    def queue_for_async_processing(self, data: Any) -> None:
        """Queue data for async processing."""
        self.async_queue.append(data)
        self.log_operation("queued_async", {"queue_size": len(self.async_queue)})

class CacheableMixin:
    """Mixin providing caching capabilities."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache: Dict[str, Any] = {}
        self._cache_hits = 0
        self._cache_misses = 0
    
    def get_cache_key(self, data: Any) -> str:
        """Generate cache key for data."""
        return f"cache_{hash(str(data))}"
    
    @trace
    def get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Retrieve item from cache."""
        if cache_key in self._cache:
            self._cache_hits += 1
            self.log_operation("cache_hit", {"key": cache_key})
            return self._cache[cache_key]
        else:
            self._cache_misses += 1
            self.log_operation("cache_miss", {"key": cache_key})
            return None
    
    def store_in_cache(self, cache_key: str, data: Any) -> None:
        """Store item in cache."""
        self._cache[cache_key] = data
        self.log_operation("cache_store", {"key": cache_key, "size": len(self._cache)})
    
    def get_cache_statistics(self) -> Dict[str, Union[int, float]]:
        """Get cache performance statistics."""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / max(total_requests, 1)
        
        return {
            'hits': self._cache_hits,
            'misses': self._cache_misses,
            'hit_rate': hit_rate,
            'cache_size': len(self._cache)
        }

class ValidatedMixin:
    """Mixin providing advanced validation capabilities."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validation_rules: List[callable] = []
        self.validation_errors: List[str] = []
    
    def add_validation_rule(self, rule: callable, description: str = "") -> None:
        """Add a validation rule."""
        self.validation_rules.append((rule, description))
        self.log_operation("validation_rule_added", {"description": description})
    
    @trace
    def comprehensive_validate(self, data: Any) -> bool:
        """Run comprehensive validation using all rules."""
        self.validation_errors.clear()
        
        # Call parent validate_input if it exists
        if hasattr(super(), 'validate_input'):
            if not super().validate_input(data):
                self.validation_errors.append("Parent validation failed")
        
        # Apply custom validation rules
        for rule, description in self.validation_rules:
            try:
                if not rule(data):
                    self.validation_errors.append(f"Rule failed: {description}")
            except Exception as e:
                self.validation_errors.append(f"Rule error: {description} - {e}")
        
        is_valid = len(self.validation_errors) == 0
        
        self.log_operation("comprehensive_validation", {
            "valid": is_valid,
            "error_count": len(self.validation_errors)
        })
        
        return is_valid

class MetricsMixin:
    """Mixin providing metrics collection."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_metrics: Dict[str, List[float]] = {}
        self.metric_callbacks: Dict[str, List[callable]] = {}
    
    def record_metric(self, metric_name: str, value: float) -> None:
        """Record a custom metric."""
        if metric_name not in self.custom_metrics:
            self.custom_metrics[metric_name] = []
        
        self.custom_metrics[metric_name].append(value)
        
        # Call metric callbacks
        for callback in self.metric_callbacks.get(metric_name, []):
            try:
                callback(metric_name, value, self.custom_metrics[metric_name])
            except Exception as e:
                self.log_operation("metric_callback_error", {"error": str(e)})
    
    def add_metric_callback(self, metric_name: str, callback: callable) -> None:
        """Add callback for metric updates."""
        if metric_name not in self.metric_callbacks:
            self.metric_callbacks[metric_name] = []
        
        self.metric_callbacks[metric_name].append(callback)
    
    def get_metric_summary(self, metric_name: str) -> Optional[Dict[str, float]]:
        """Get summary statistics for a metric."""
        if metric_name not in self.custom_metrics:
            return None
        
        values = self.custom_metrics[metric_name]
        if not values:
            return None
        
        return {
            'count': len(values),
            'sum': sum(values),
            'mean': sum(values) / len(values),
            'min': min(values),
            'max': max(values)
        }

# Complex multiple inheritance classes
class BasicDataProcessor(AsyncProcessor, CacheableMixin, ValidatedMixin):
    """Basic data processor combining async, cache, and validation capabilities."""
    
    def __init__(self, processor_id: str, enable_cache: bool = True):
        # Multiple inheritance initialization
        super().__init__(processor_id)
        self.enable_cache = enable_cache
        
        # Set up basic validation rules
        self.add_validation_rule(
            lambda data: data is not None,
            "Data must not be None"
        )
        self.add_validation_rule(
            lambda data: isinstance(data, (dict, list, str, int, float)),
            "Data must be a basic type"
        )
    
    def validate_input(self, data: Any) -> bool:
        """Implementation of abstract method with enhanced validation."""
        # Call mixin validation
        return self.comprehensive_validate(data)
    
    @trace
    @monitor_performance
    def process_data(self, data: Any) -> ProcessingResult:
        """Implementation of abstract method with caching."""
        if not self.validate_input(data):
            self.error_count += 1
            return ProcessingResult(
                success=False,
                errors=self.validation_errors.copy()
            )
        
        # Check cache first
        if self.enable_cache:
            cache_key = self.get_cache_key(data)
            cached_result = self.get_from_cache(cache_key)
            
            if cached_result:
                return cached_result
        
        # Process data
        try:
            processed_data = self._internal_process(data)
            result = ProcessingResult(
                success=True,
                data=processed_data,
                timestamp=time.time()
            )
            
            # Store in cache
            if self.enable_cache:
                self.store_in_cache(cache_key, result)
            
            self.processed_count += 1
            return result
        
        except Exception as e:
            self.error_count += 1
            return ProcessingResult(
                success=False,
                errors=[str(e)]
            )
    
    def _internal_process(self, data: Any) -> Any:
        """Internal processing logic."""
        if isinstance(data, dict):
            return {k: v * 2 if isinstance(v, (int, float)) else v for k, v in data.items()}
        elif isinstance(data, list):
            return [item * 2 if isinstance(item, (int, float)) else item for item in data]
        elif isinstance(data, (int, float)):
            return data * 2
        else:
            return str(data).upper()

class AdvancedProcessor(BasicDataProcessor, MetricsMixin):
    """Advanced processor with metrics collection."""
    
    def __init__(self, processor_id: str, priority: Priority = Priority.MEDIUM):
        super().__init__(processor_id)
        self.priority = priority
        self.processing_strategy = "default"
        
        # Add metrics callbacks
        self.add_metric_callback("processing_time", self._processing_time_callback)
        self.add_metric_callback("data_size", self._data_size_callback)
    
    @trace
    def process_data(self, data: Any) -> ProcessingResult:
        """Enhanced processing with metrics collection."""
        import time
        start_time = time.time()
        
        # Record data size metric
        data_size = len(str(data))
        self.record_metric("data_size", data_size)
        
        # Call parent processing
        result = super().process_data(data)
        
        # Record processing time metric
        processing_time = time.time() - start_time
        self.record_metric("processing_time", processing_time)
        
        # Add metrics to result
        result.metrics = {
            'processing_time': processing_time,
            'data_size': data_size,
            'priority': self.priority.name
        }
        
        return result
    
    def _processing_time_callback(self, metric_name: str, value: float, history: List[float]) -> None:
        """Callback for processing time metrics."""
        if len(history) > 10:
            avg_time = sum(history[-10:]) / 10
            if avg_time > 1.0:  # Slow processing alert
                self.log_operation("slow_processing_alert", {"avg_time": avg_time})
    
    def _data_size_callback(self, metric_name: str, value: float, history: List[float]) -> None:
        """Callback for data size metrics."""
        if value > 10000:  # Large data alert
            self.log_operation("large_data_alert", {"size": value})
    
    @validate_auth(required_role='operator')
    def change_processing_strategy(self, new_strategy: str) -> bool:
        """Change processing strategy (requires authorization)."""
        old_strategy = self.processing_strategy
        self.processing_strategy = new_strategy
        
        self.log_operation("strategy_changed", {
            "old": old_strategy,
            "new": new_strategy
        })
        
        return True

class SpecializedProcessor(AdvancedProcessor):
    """Specialized processor with domain-specific logic."""
    
    def __init__(self, processor_id: str, specialization: str):
        super().__init__(processor_id, Priority.HIGH)
        self.specialization = specialization
        self.specialist_cache: Dict[str, Any] = {}
        
        # Add specialized validation rules
        self.add_validation_rule(
            self._validate_specialization,
            f"Data must be compatible with {specialization} specialization"
        )
    
    def _validate_specialization(self, data: Any) -> bool:
        """Specialized validation based on processor type."""
        if self.specialization == "numeric":
            return isinstance(data, (int, float, list, dict))
        elif self.specialization == "text":
            return isinstance(data, (str, list, dict))
        elif self.specialization == "structured":
            return isinstance(data, (dict, list))
        else:
            return True
    
    @trace
    def _internal_process(self, data: Any) -> Any:
        """Specialized processing logic."""
        if self.specialization == "numeric":
            return self._process_numeric(data)
        elif self.specialization == "text":
            return self._process_text(data)
        elif self.specialization == "structured":
            return self._process_structured(data)
        else:
            return super()._internal_process(data)
    
    def _process_numeric(self, data: Any) -> Any:
        """Numeric data processing."""
        if isinstance(data, (int, float)):
            return data ** 2
        elif isinstance(data, list):
            return [x ** 2 if isinstance(x, (int, float)) else x for x in data]
        elif isinstance(data, dict):
            return {k: v ** 2 if isinstance(v, (int, float)) else v for k, v in data.items()}
        return data
    
    def _process_text(self, data: Any) -> Any:
        """Text data processing."""
        if isinstance(data, str):
            return data.upper().replace(" ", "_")
        elif isinstance(data, list):
            return [item.upper().replace(" ", "_") if isinstance(item, str) else item for item in data]
        elif isinstance(data, dict):
            return {k: v.upper().replace(" ", "_") if isinstance(v, str) else v for k, v in data.items()}
        return data
    
    def _process_structured(self, data: Any) -> Any:
        """Structured data processing."""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if isinstance(value, dict):
                    result[f"nested_{key}"] = self._process_structured(value)
                elif isinstance(value, list):
                    result[f"list_{key}"] = [self._process_structured(item) if isinstance(item, dict) else item for item in value]
                else:
                    result[key] = value
            return result
        elif isinstance(data, list):
            return [self._process_structured(item) if isinstance(item, dict) else item for item in data]
        return data

# Protocol for testing protocol inheritance
class ProcessorProtocol(Protocol):
    """Protocol defining processor interface."""
    
    def process_data(self, data: Any) -> ProcessingResult:
        """Process data and return result."""
        ...
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processor statistics."""
        ...

# Generic class for testing generic inheritance
class GenericProcessor(Generic[T, U]):
    """Generic processor for testing generic type inheritance."""
    
    def __init__(self, input_type: type, output_type: type):
        self.input_type = input_type
        self.output_type = output_type
        self.type_conversion_cache: Dict[str, Any] = {}
    
    def process_typed_data(self, data: T) -> U:
        """Process data with type conversion."""
        if not isinstance(data, self.input_type):
            raise TypeError(f"Expected {self.input_type}, got {type(data)}")
        
        # Cache key for type conversion
        cache_key = f"{type(data).__name__}_to_{self.output_type.__name__}"
        
        if cache_key in self.type_conversion_cache:
            converter = self.type_conversion_cache[cache_key]
        else:
            converter = self._create_type_converter(type(data), self.output_type)
            self.type_conversion_cache[cache_key] = converter
        
        return converter(data)
    
    def _create_type_converter(self, from_type: type, to_type: type) -> callable:
        """Create type converter function."""
        if from_type == to_type:
            return lambda x: x
        elif to_type == str:
            return str
        elif to_type == int and from_type in (float, str):
            return int
        elif to_type == float and from_type in (int, str):
            return float
        else:
            return lambda x: to_type(x)

# Complex inheritance chain for testing deep inheritance resolution
class UltimateProcessor(SpecializedProcessor, GenericProcessor[Dict[str, Any], ProcessingResult]):
    """Ultimate processor combining all inheritance patterns."""
    
    def __init__(self, processor_id: str):
        # Complex multiple inheritance initialization
        SpecializedProcessor.__init__(self, processor_id, "ultimate")
        GenericProcessor.__init__(self, dict, ProcessingResult)
        
        self.ultimate_features_enabled = True
        self.cross_references: Dict[str, Any] = {}
    
    @trace
    @monitor_performance
    @validate_auth(required_role='admin')
    def ultimate_process(self, data: Dict[str, Any]) -> ProcessingResult:
        """Ultimate processing method combining all capabilities."""
        # Use generic processing
        typed_result = self.process_typed_data(data)
        
        if isinstance(typed_result, ProcessingResult):
            return typed_result
        
        # Fallback to specialized processing
        specialized_result = self.process_data(data)
        
        # Add ultimate enhancements
        if specialized_result.success and self.ultimate_features_enabled:
            specialized_result.data = self._apply_ultimate_enhancements(specialized_result.data)
            specialized_result.metrics.update({
                'ultimate_enhanced': True,
                'enhancement_level': 'maximum'
            })
        
        return specialized_result
    
    def _apply_ultimate_enhancements(self, data: Any) -> Any:
        """Apply ultimate-level enhancements."""
        if isinstance(data, dict):
            enhanced = {}
            for key, value in data.items():
                enhanced[f"ultimate_{key}"] = value
                
                # Create cross-references
                if isinstance(value, (str, int)):
                    ref_key = f"ref_{hash(str(value))}"
                    self.cross_references[ref_key] = value
                    enhanced[f"{key}_ref"] = ref_key
            
            return enhanced
        
        return data
    
    @contextmanager
    def ultimate_processing_context(self):
        """Context manager for ultimate processing."""
        original_features = self.ultimate_features_enabled
        self.ultimate_features_enabled = True
        
        self.log_operation("ultimate_context_entered")
        
        try:
            yield self
        finally:
            self.ultimate_features_enabled = original_features
            self.log_operation("ultimate_context_exited")

# Factory function for testing complex instantiation patterns
def create_processor_hierarchy(processor_configs: List[Dict[str, Any]]) -> Dict[str, AbstractProcessor]:
    """Factory function creating complex processor hierarchies."""
    processors = {}
    
    for config in processor_configs:
        processor_type = config.get('type', 'basic')
        processor_id = config['id']
        
        if processor_type == 'basic':
            processor = BasicDataProcessor(processor_id)
        elif processor_type == 'advanced':
            priority = Priority[config.get('priority', 'MEDIUM')]
            processor = AdvancedProcessor(processor_id, priority)
        elif processor_type == 'specialized':
            specialization = config.get('specialization', 'numeric')
            processor = SpecializedProcessor(processor_id, specialization)
        elif processor_type == 'ultimate':
            processor = UltimateProcessor(processor_id)
        else:
            processor = BasicDataProcessor(processor_id)
        
        # Configure processor
        if 'cache_enabled' in config:
            processor.enable_cache = config['cache_enabled']
        
        if 'validation_rules' in config:
            for rule_config in config['validation_rules']:
                rule_func = eval(rule_config['function'])  # In real code, use safer evaluation
                processor.add_validation_rule(rule_func, rule_config['description'])
        
        processors[processor_id] = processor
    
    return processors

# Module-level complex inheritance testing
import time

ultimate_processor = UltimateProcessor("master_processor")

# Test complex method resolution through inheritance
test_data = {"value": 42, "name": "test", "priority": "high"}

with ultimate_processor.ultimate_processing_context():
    result = ultimate_processor.ultimate_process(test_data)
    stats = ultimate_processor.get_statistics()
    cache_stats = ultimate_processor.get_cache_statistics()
    metric_summary = ultimate_processor.get_metric_summary("processing_time")
