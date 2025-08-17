"""
Configuration Management - Code Atlas

Centralized configuration for all analysis settings and constants.
"""

import json
from dataclasses import dataclass, field
from typing import Set, Dict, Any, Optional
from pathlib import Path


@dataclass
class AnalysisConfig:
    """Comprehensive configuration for Atlas analysis."""
    
    # Logging configuration
    log_level: int = 3  # 0=minimal, 1=normal, 2=verbose, 3=debug
    
    # Analysis toggles
    emit_detection_enabled: bool = True
    decorator_analysis_enabled: bool = True
    inheritance_analysis_enabled: bool = True
    external_library_support_enabled: bool = True
    
    # External libraries allowlist
    external_libraries: Set[str] = field(default_factory=lambda: {
        'flask_socketio',
        'flask',
        'socketio', 
        'threading',
        'multiprocessing',
        'uuid'
    })
    
    # Performance and limits
    inheritance_depth_limit: int = 10
    resolution_cache_size: int = 1000
    max_function_analysis_depth: int = 50
    
    # Output configuration
    include_emit_contexts: bool = True
    include_decorators: bool = True
    include_module_state: bool = True
    include_inheritance_info: bool = True
    
    # File discovery
    exclude_patterns: Set[str] = field(default_factory=lambda: {
        '__pycache__',
        '.git',
        '.pytest_cache',
        'venv',
        'env',
        '.venv'
    })
    
    # Built-in functions to ignore during analysis
    builtin_functions: Set[str] = field(default_factory=lambda: {
        'print', 'len', 'str', 'int', 'float', 'bool', 'list', 'dict',
        'set', 'tuple', 'range', 'enumerate', 'zip', 'all', 'any',
        'max', 'min', 'sum', 'abs', 'round', 'sorted', 'reversed',
        'map', 'filter', 'isinstance', 'hasattr', 'getattr', 'setattr'
    })
    
    # Validation settings
    strict_type_checking: bool = False
    report_missing_type_hints: bool = True
    report_unresolvable_types: bool = True
    
    @classmethod
    def from_file(cls, config_path: str) -> 'AnalysisConfig':
        """Load configuration from JSON file."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Convert sets from lists in JSON
            if 'external_libraries' in config_data:
                config_data['external_libraries'] = set(config_data['external_libraries'])
            if 'exclude_patterns' in config_data:
                config_data['exclude_patterns'] = set(config_data['exclude_patterns'])
            if 'builtin_functions' in config_data:
                config_data['builtin_functions'] = set(config_data['builtin_functions'])
            
            return cls(**config_data)
        
        except Exception as e:
            raise ValueError(f"Failed to load configuration from {config_path}: {e}")
    
    def to_file(self, config_path: str) -> None:
        """Save configuration to JSON file."""
        # Convert sets to lists for JSON serialization
        config_dict = {}
        for key, value in self.__dict__.items():
            if isinstance(value, set):
                config_dict[key] = list(value)
            else:
                config_dict[key] = value
        
        path = Path(config_path)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise ValueError(f"Failed to save configuration to {config_path}: {e}")
    
    def update(self, **kwargs) -> None:
        """Update configuration values."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Unknown configuration key: {key}")
    
    def get_external_library_allowlist(self) -> Set[str]:
        """Get the external library allowlist (for backward compatibility)."""
        return self.external_libraries.copy()
    
    def is_builtin_function(self, func_name: str) -> bool:
        """Check if function name is a built-in that should be ignored."""
        return func_name in self.builtin_functions
    
    def should_analyze_decorators(self) -> bool:
        """Check if decorator analysis is enabled."""
        return self.decorator_analysis_enabled
    
    def should_detect_emits(self) -> bool:
        """Check if emit detection is enabled."""
        return self.emit_detection_enabled
    
    def should_track_inheritance(self) -> bool:
        """Check if inheritance analysis is enabled."""
        return self.inheritance_analysis_enabled
    
    def get_log_level(self) -> int:
        """Get current logging level."""
        return self.log_level
    
    def validate(self) -> None:
        """Validate configuration values."""
        if self.log_level < 0 or self.log_level > 3:
            raise ValueError("log_level must be between 0 and 3")
        
        if self.inheritance_depth_limit < 1:
            raise ValueError("inheritance_depth_limit must be positive")
        
        if self.resolution_cache_size < 0:
            raise ValueError("resolution_cache_size must be non-negative")
        
        if not self.external_libraries:
            raise ValueError("external_libraries cannot be empty")


# Global configuration instance
_global_config: Optional[AnalysisConfig] = None


def get_config() -> AnalysisConfig:
    """Get the global configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = AnalysisConfig()
    return _global_config


def set_config(config: AnalysisConfig) -> None:
    """Set the global configuration instance."""
    global _global_config
    config.validate()
    _global_config = config


def load_config_from_file(config_path: str) -> AnalysisConfig:
    """Load and set global configuration from file."""
    config = AnalysisConfig.from_file(config_path)
    set_config(config)
    return config


def reset_config() -> None:
    """Reset configuration to defaults."""
    global _global_config
    _global_config = AnalysisConfig()


# Backward compatibility functions
def get_log_level() -> int:
    """Get current log level (backward compatibility)."""
    return get_config().log_level


def get_external_library_allowlist() -> Set[str]:
    """Get external library allowlist (backward compatibility)."""
    return get_config().external_libraries
