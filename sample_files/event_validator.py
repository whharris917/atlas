# event_validator.py
"""
Advanced validation patterns with complex rule engines and chaining.
Tests complex validation logic with method chaining and factory patterns.
"""
from typing import Any, Dict, List, Optional, Callable, Union, Protocol, TypeVar
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
import re
import time
from functools import wraps

from decorators import trace, monitor_performance, validate_auth

T = TypeVar('T')

class ValidationLevel(Enum):
    """Validation severity levels."""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()

class ValidationResult(Enum):
    """Validation result types."""
    VALID = auto()
    INVALID = auto()
    REQUIRES_REVIEW = auto()
    CONDITIONALLY_VALID = auto()

@dataclass
class ValidationError:
    """Validation error details."""
    field: str
    message: str
    level: ValidationLevel
    code: str
    context: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)

@dataclass 
class ValidationReport:
    """Comprehensive validation report."""
    result: ValidationResult
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    validation_time: float = 0.0
    rules_applied: List[str] = field(default_factory=list)
    
    def is_valid(self) -> bool:
        """Check if validation passed."""
        return self.result in [ValidationResult.VALID, ValidationResult.CONDITIONALLY_VALID]
    
    def has_errors(self) -> bool:
        """Check if there are validation errors."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if there are validation warnings."""
        return len(self.warnings) > 0
    
    def get_error_codes(self) -> List[str]:
        """Get list of error codes."""
        return [error.code for error in self.errors]
    
    def add_error(self, field: str, message: str, code: str, 
                  level: ValidationLevel = ValidationLevel.ERROR,
                  context: Dict[str, Any] = None,
                  suggestions: List[str] = None) -> None:
        """Add validation error."""
        error = ValidationError(
            field=field,
            message=message,
            level=level,
            code=code,
            context=context or {},
            suggestions=suggestions or []
        )
        
        if level == ValidationLevel.WARNING:
            self.warnings.append(error)
        else:
            self.errors.append(error)

class ValidationRule(Protocol):
    """Protocol for validation rules."""
    
    def validate(self, data: Any, context: Dict[str, Any]) -> ValidationReport:
        """Validate data and return report."""
        ...
    
    def get_rule_name(self) -> str:
        """Get rule name."""
        ...

class BaseValidationRule(ABC):
    """Abstract base class for validation rules."""
    
    def __init__(self, rule_name: str, description: str = ""):
        self.rule_name = rule_name
        self.description = description
        self.enabled = True
        self.priority = 0
        self.dependencies: List[str] = []
    
    @abstractmethod
    def _validate_implementation(self, data: Any, context: Dict[str, Any]) -> ValidationReport:
        """Implementation-specific validation logic."""
        pass
    
    @trace
    def validate(self, data: Any, context: Dict[str, Any] = None) -> ValidationReport:
        """Main validation method with error handling."""
        context = context or {}
        start_time = time.time()
        
        try:
            report = self._validate_implementation(data, context)
            report.validation_time = time.time() - start_time
            report.rules_applied.append(self.rule_name)
            return report
        
        except Exception as e:
            # Create error report for validation failure
            report = ValidationReport(result=ValidationResult.INVALID)
            report.add_error(
                field="validation_system",
                message=f"Validation rule '{self.rule_name}' failed: {str(e)}",
                code="VALIDATION_RULE_ERROR",
                level=ValidationLevel.CRITICAL
            )
            report.validation_time = time.time() - start_time
            return report
    
    def get_rule_name(self) -> str:
        """Get rule name."""
        return self.rule_name

class RequiredFieldRule(BaseValidationRule):
    """Rule for validating required fields."""
    
    def __init__(self, required_fields: List[str]):
        super().__init__("required_fields", "Validates presence of required fields")
        self.required_fields = required_fields
    
    def _validate_implementation(self, data: Any, context: Dict[str, Any]) -> ValidationReport:
        """Validate required fields."""
        report = ValidationReport(result=ValidationResult.VALID)
        
        if not isinstance(data, dict):
            report.result = ValidationResult.INVALID
            report.add_error(
                field="data_type",
                message="Data must be a dictionary for field validation",
                code="INVALID_DATA_TYPE"
            )
            return report
        
        for field in self.required_fields:
            if field not in data:
                report.result = ValidationResult.INVALID
                report.add_error(
                    field=field,
                    message=f"Required field '{field}' is missing",
                    code="MISSING_REQUIRED_FIELD",
                    suggestions=[f"Add '{field}' field to the data"]
                )
            elif data[field] is None:
                report.result = ValidationResult.INVALID
                report.add_error(
                    field=field,
                    message=f"Required field '{field}' cannot be null",
                    code="NULL_REQUIRED_FIELD"
                )
        
        return report

class DataTypeRule(BaseValidationRule):
    """Rule for validating data types."""
    
    def __init__(self, field_types: Dict[str, Union[type, List[type]]]):
        super().__init__("data_types", "Validates field data types")
        self.field_types = field_types
    
    def _validate_implementation(self, data: Any, context: Dict[str, Any]) -> ValidationReport:
        """Validate data types."""
        report = ValidationReport(result=ValidationResult.VALID)
        
        if not isinstance(data, dict):
            report.result = ValidationResult.INVALID
            report.add_error(
                field="data_type",
                message="Data must be a dictionary for type validation",
                code="INVALID_DATA_TYPE"
            )
            return report
        
        for field, expected_type in self.field_types.items():
            if field in data:
                value = data[field]
                
                # Handle multiple allowed types
                if isinstance(expected_type, list):
                    if not any(isinstance(value, t) for t in expected_type):
                        type_names = [t.__name__ for t in expected_type]
                        report.add_error(
                            field=field,
                            message=f"Field '{field}' must be one of types: {type_names}, got {type(value).__name__}",
                            code="INVALID_FIELD_TYPE",
                            level=ValidationLevel.ERROR,
                            context={"expected_types": type_names, "actual_type": type(value).__name__}
                        )
                        report.result = ValidationResult.INVALID
                else:
                    if not isinstance(value, expected_type):
                        report.add_error(
                            field=field,
                            message=f"Field '{field}' must be {expected_type.__name__}, got {type(value).__name__}",
                            code="INVALID_FIELD_TYPE",
                            level=ValidationLevel.ERROR,
                            context={"expected_type": expected_type.__name__, "actual_type": type(value).__name__}
                        )
                        report.result = ValidationResult.INVALID
        
        return report

class RegexValidationRule(BaseValidationRule):
    """Rule for regex pattern validation."""
    
    def __init__(self, field_patterns: Dict[str, str]):
        super().__init__("regex_validation", "Validates fields against regex patterns")
        self.field_patterns = field_patterns
        self.compiled_patterns = {field: re.compile(pattern) for field, pattern in field_patterns.items()}
    
    def _validate_implementation(self, data: Any, context: Dict[str, Any]) -> ValidationReport:
        """Validate regex patterns."""
        report = ValidationReport(result=ValidationResult.VALID)
        
        if not isinstance(data, dict):
            return report
        
        for field, pattern in self.compiled_patterns.items():
            if field in data:
                value = data[field]
                
                if not isinstance(value, str):
                    report.add_error(
                        field=field,
                        message=f"Field '{field}' must be string for regex validation",
                        code="NON_STRING_REGEX_FIELD"
                    )
                    report.result = ValidationResult.INVALID
                    continue
                
                if not pattern.match(value):
                    report.add_error(
                        field=field,
                        message=f"Field '{field}' does not match required pattern",
                        code="REGEX_PATTERN_MISMATCH",
                        context={"pattern": self.field_patterns[field], "value": value}
                    )
                    report.result = ValidationResult.INVALID
        
        return report

class ValidationEngine:
    """Comprehensive validation engine with rule management."""
    
    def __init__(self):
        self.rules: List[BaseValidationRule] = []
        self.global_context: Dict[str, Any] = {}
        self.validation_cache: Dict[str, ValidationReport] = {}
        self.cache_enabled = True
        
    @trace
    def add_rule(self, rule: BaseValidationRule) -> 'ValidationEngine':
        """Add validation rule to engine."""
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        return self
    
    def add_rules(self, rules: List[BaseValidationRule]) -> 'ValidationEngine':
        """Add multiple validation rules."""
        for rule in rules:
            self.add_rule(rule)
        return self
    
    def set_global_context(self, context: Dict[str, Any]) -> 'ValidationEngine':
        """Set global context for all validations."""
        self.global_context.update(context)
        return self
    
    @trace
    @monitor_performance
    def validate(self, data: Any, context: Dict[str, Any] = None) -> ValidationReport:
        """Comprehensive validation using all rules."""
        full_context = {**self.global_context, **(context or {})}
        
        # Check cache
        if self.cache_enabled:
            cache_key = self._generate_cache_key(data, full_context)
            if cache_key in self.validation_cache:
                cached_report = self.validation_cache[cache_key]
                cached_report.metadata['from_cache'] = True
                return cached_report
        
        # Initialize comprehensive report
        comprehensive_report = ValidationReport(result=ValidationResult.VALID)
        start_time = time.time()
        
        # Apply rules in priority order
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            rule_report = rule.validate(data, full_context)
            self._merge_reports(comprehensive_report, rule_report)
        
        # Finalize report
        comprehensive_report.validation_time = time.time() - start_time
        comprehensive_report.metadata.update({
            'rules_count': len(self.rules),
            'enabled_rules': sum(1 for r in self.rules if r.enabled),
            'total_validation_time': comprehensive_report.validation_time
        })
        
        # Cache result
        if self.cache_enabled:
            self.validation_cache[cache_key] = comprehensive_report
        
        return comprehensive_report
    
    def _generate_cache_key(self, data: Any, context: Dict[str, Any]) -> str:
        """Generate cache key for validation."""
        data_hash = hash(str(data))
        context_hash = hash(str(sorted(context.items())))
        rules_hash = hash(tuple(r.rule_name for r in self.rules if r.enabled))
        return f"{data_hash}_{context_hash}_{rules_hash}"
    
    def _merge_reports(self, main_report: ValidationReport, rule_report: ValidationReport) -> None:
        """Merge rule report into main report."""
        main_report.errors.extend(rule_report.errors)
        main_report.warnings.extend(rule_report.warnings)
        main_report.rules_applied.extend(rule_report.rules_applied)
        
        # Update result based on most restrictive
        if rule_report.result == ValidationResult.INVALID:
            main_report.result = ValidationResult.INVALID
        elif (rule_report.result == ValidationResult.REQUIRES_REVIEW and 
              main_report.result == ValidationResult.VALID):
            main_report.result = ValidationResult.REQUIRES_REVIEW
    
    def create_rule_builder(self) -> 'ValidationRuleBuilder':
        """Create a rule builder for fluent rule creation."""
        return ValidationRuleBuilder(self)

class ValidationRuleBuilder:
    """Fluent builder for creating validation rules."""
    
    def __init__(self, engine: ValidationEngine):
        self.engine = engine
        self.current_rules: List[BaseValidationRule] = []
    
    def require_fields(self, *fields: str) -> 'ValidationRuleBuilder':
        """Add required field validation."""
        rule = RequiredFieldRule(list(fields))
        self.current_rules.append(rule)
        return self
    
    def field_types(self, **field_types) -> 'ValidationRuleBuilder':
        """Add field type validation."""
        rule = DataTypeRule(field_types)
        self.current_rules.append(rule)
        return self
    
    def field_patterns(self, **field_patterns) -> 'ValidationRuleBuilder':
        """Add regex pattern validation."""
        rule = RegexValidationRule(field_patterns)
        self.current_rules.append(rule)
        return self
    
    def build(self) -> ValidationEngine:
        """Build and add rules to engine."""
        for rule in self.current_rules:
            self.engine.add_rule(rule)
        self.current_rules.clear()
        return self.engine

class EventValidator:
    """Specialized validator for event data with complex patterns."""
    
    def __init__(self):
        self.validation_engine = ValidationEngine()
        self.event_schemas: Dict[str, ValidationEngine] = {}
        self._setup_default_validations()
    
    def _setup_default_validations(self) -> None:
        """Setup default event validation rules."""
        # Base event validation
        self.validation_engine.create_rule_builder().require_fields('event_type', 'timestamp').field_types(event_type=str, timestamp=[int, float], data=dict).build()
        
        # Message event validation - FIXED REGEX PATTERN
        message_engine = ValidationEngine()
        message_engine.create_rule_builder().require_fields('message', 'sender_id').field_types(message=str, sender_id=str, room=str).field_patterns(sender_id=r'^[a-zA-Z0-9_-]+$').build()
        
        self.event_schemas['message'] = message_engine
        
        # Room event validation
        room_engine = ValidationEngine()
        room_engine.create_rule_builder().require_fields('room_name', 'action').field_types(room_name=str, action=str, user_id=str).field_patterns(room_name=r'^[a-zA-Z0-9_-]+$', action=r'^(join|leave|create|delete)$').build()
        
        self.event_schemas['room'] = room_engine
    
    @trace
    def validate_event(self, event_data: Dict[str, Any]) -> ValidationReport:
        """Validate event data with type-specific rules."""
        # First validate base event structure
        base_report = self.validation_engine.validate(event_data)
        
        if not base_report.is_valid():
            return base_report
        
        # Get event type
        event_type = event_data.get('event_type', 'unknown')
        
        # Apply type-specific validation
        if event_type in self.event_schemas:
            type_engine = self.event_schemas[event_type]
            type_report = type_engine.validate(event_data.get('data', {}))
            
            # Merge reports
            self.validation_engine._merge_reports(base_report, type_report)
        
        return base_report
    
    def validate_result(self, result: Any) -> bool:
        """Simple result validation."""
        return result is not None and result != False
    
    def get_validation_details(self) -> Dict[str, Any]:
        """Get validation details."""
        return {
            'rules_count': len(self.validation_engine.rules),
            'schemas_count': len(self.event_schemas),
            'cache_size': len(self.validation_engine.validation_cache)
        }

class MessageValidator:
    """Specialized validator for message content with advanced filtering."""
    
    def __init__(self):
        self.content_filters: List[Callable[[str], bool]] = []
        self.banned_patterns: List[re.Pattern] = []
        self.validation_cache: Dict[str, bool] = {}
        
        self._setup_default_filters()
    
    def _setup_default_filters(self) -> None:
        """Setup default message content filters."""
        # Length filter
        self.content_filters.append(lambda msg: 1 <= len(msg.strip()) <= 1000)
        
        # Basic profanity filter (simplified)
        banned_words = ['spam', 'abuse', 'inappropriate']
        for word in banned_words:
            pattern = re.compile(rf'\b{re.escape(word)}\b', re.IGNORECASE)
            self.banned_patterns.append(pattern)
    
    @trace
    def validate_message(self, message: str) -> bool:
        """Validate message content with comprehensive filtering."""
        # Check cache
        message_hash = hash(message)
        if message_hash in self.validation_cache:
            return self.validation_cache[message_hash]
        
        # Apply content filters
        for filter_func in self.content_filters:
            if not filter_func(message):
                self.validation_cache[message_hash] = False
                return False
        
        # Check banned patterns
        for pattern in self.banned_patterns:
            if pattern.search(message):
                self.validation_cache[message_hash] = False
                return False
        
        # Cache positive result
        self.validation_cache[message_hash] = True
        return True
    
    def get_validation_details(self) -> Dict[str, Any]:
        """Get detailed validation information."""
        return {
            'filters_count': len(self.content_filters),
            'banned_patterns_count': len(self.banned_patterns),
            'cache_size': len(self.validation_cache)
        }

# Module-level validator instances for testing
event_validator = EventValidator()
message_validator = MessageValidator()

# Test complex validation chains
test_event_data = {
    'event_type': 'message',
    'timestamp': time.time(),
    'data': {
        'message': 'Hello, this is a test message!',
        'sender_id': 'user_123',
        'room': 'general'
    }
}

# Execute complex validation chains
event_validation_result = event_validator.validate_event(test_event_data)
message_validation_result = message_validator.validate_message("This is a clean test message")

def validate_complete_action(event_data: Dict[str, Any], message_content: str) -> Dict[str, Any]:
    """Complete validation chain for actions."""
    results = {}
    
    # Validate event
    results['event'] = event_validator.validate_event(event_data)
    
    # Validate message content
    message_valid = message_validator.validate_message(message_content)
    results['message_valid'] = message_valid
    
    return results

# Test the complete validation chain
complete_validation = validate_complete_action(test_event_data, "Test message for validation")
