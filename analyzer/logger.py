#!/usr/bin/env python3
"""
Enhanced Logging System - Code Atlas

Centralized logging with hierarchical tree-structured display, automatic context 
change detection, and consistent indentation for detailed debugging visibility.
"""


from enum import Enum, auto
from typing import Optional, Dict, Any
from pathlib import Path


class LogLevel(Enum):
    """Log level enumeration for type safety."""
    SILENT = 0
    ERROR = 1
    WARNING = 2
    INFO = 3
    DEBUG = 4
    TRACE = 5


class AnalysisPhase(Enum):
    """Analysis phase enumeration for context."""
    DISCOVERY = auto()
    RECONNAISSANCE = auto()
    ANALYSIS = auto()
    VALIDATION = auto()
    REPORTING = auto()


class AtlasLogger:
    """Enhanced centralized logger with hierarchical tree-structured output."""
    
    def __init__(
            self, 
            level: LogLevel = LogLevel.INFO,
            output_file: Optional[Path] = None
        ):
        self.level = level
        self.output_file = output_file

        # Current context
        self.phase = None
        self.source = None
        self.module = None
        self.class_name = None
        self.function = None

        # Context change detection for hierarchical display
        self.prev_phase = None
        self.prev_source = None  
        self.prev_module = None
        self.prev_class_name = None
        self.prev_function = None
        
        # Initialize file output if specified
        self.file_handle = None
        if output_file:
            try:
                self.file_handle = open(output_file, 'w', encoding='utf-8')
            except Exception as e:
                print(f"Warning: Could not open log file {output_file}: {e}")
    
    def _detect_context_changes(self) -> Dict[str, bool]:
        """Detect which context fields changed since last message."""
        changes = {
            'phase': self.phase != self.prev_phase,
            'source': self.source != self.prev_source,
            'module': self.module != self.prev_module,
            'class': self.class_name != self.prev_class_name,
            'function': self.function != self.prev_function
        }
        return changes

    def _update_previous_context(self):
        """Update previous context for next message comparison."""
        self.prev_phase = self.phase
        self.prev_source = self.source
        self.prev_module = self.module
        self.prev_class_name = self.class_name
        self.prev_function = self.function

    def reset_context(self):
        """Reset all context to None - used between module analysis."""
        
        # Explicitly reset all context to None
        self.source = None
        self.module = None
        self.class_name = None
        self.function = None
        # Don't reset phase - that's managed by AtlasMain
        
        # Reset previous context tracking
        self.prev_source = None
        self.prev_module = None
        self.prev_class_name = None
        self.prev_function = None
    
    def _should_log(self, level: LogLevel) -> bool:
        """Check if message should be logged based on current level."""
        return level.value <= self.level.value and self.level != LogLevel.SILENT
    
    def _format_message(
            self, 
            level: LogLevel, 
            message: str, 
            source: str,
            extra: Optional[Dict[str, Any]] = None
        ) -> str:
        """Format message with hierarchical context headers and consistent indentation."""
        
        # Update source context before detecting changes
        self.source = source
        
        changes = self._detect_context_changes()
        parts = []
        current_depth = 0
        
        # Show context headers only when they change, building depth progressively
        # All context fields are now treated consistently for indentation
        if changes['phase'] and self.phase is not None:
            indent = "    " * current_depth
            parts.append(f"{indent}[phase:{self.phase}]")
            current_depth += 1
        elif self.phase is not None:
            # Phase exists but unchanged - only count if it was previously shown
            if self.prev_phase is not None:
                current_depth += 1
        
        if changes['source'] and self.source is not None:
            indent = "    " * current_depth
            parts.append(f"{indent}[source:{self.source}]")
            current_depth += 1
        elif self.source is not None:
            # Source exists but unchanged - only count if it was previously shown
            if self.prev_source is not None:
                current_depth += 1
        
        if changes['module'] and self.module is not None:
            indent = "    " * current_depth
            parts.append(f"{indent}[module:{self.module}]")
            current_depth += 1
        elif self.module is not None:
            # Module exists but unchanged - only count if it was previously shown
            if self.prev_module is not None:
                current_depth += 1
        
        if changes['class'] and self.class_name is not None:
            indent = "    " * current_depth
            parts.append(f"{indent}[class:{self.class_name}]")
            current_depth += 1
        elif self.class_name is not None:
            # Class exists but unchanged - only count if it was previously shown
            if self.prev_class_name is not None:
                current_depth += 1
        
        if changes['function'] and self.function is not None:
            indent = "    " * current_depth
            parts.append(f"{indent}[function:{self.function}]")
            current_depth += 1
        elif self.function is not None:
            # Function exists but unchanged - only count if it was previously shown
            if self.prev_function is not None:
                current_depth += 1
        
        # Add the actual message at the current context depth
        message_indent = "    " * current_depth
        message_part = f"{message_indent}[{level.name}] {message}"
        
        # Add extra data if present
        if extra:
            extra_str = " | ".join(f"{k}={v}" for k, v in extra.items())
            message_part += f"  ({extra_str})"
        
        parts.append(message_part)
        
        # Update previous context for next comparison
        self._update_previous_context()
        
        return "\n".join(parts)

    def _output(self, message: str):
        """Output message to console and file if configured."""
        print(message)
        
        if self.file_handle:
            try:
                self.file_handle.write(message + '\n')
                self.file_handle.flush()
            except Exception as e:
                print(f"Warning: Could not write to log file: {e}")

    def close(self):
        """Close file handle if open."""
        if self.file_handle:
            try:
                self.file_handle.close()
                self.file_handle = None
            except Exception as e:
                print(f"Warning: Error closing log file: {e}")

    # Context management properties
    @property
    def current_module(self) -> Optional[str]:
        """Get current module context."""
        return self.module

    @current_module.setter  
    def current_module(self, value: Optional[str]):
        """Set current module context."""
        self.module = value

    @property
    def current_class(self) -> Optional[str]:
        """Get current class context."""
        return self.class_name

    @current_class.setter
    def current_class(self, value: Optional[str]):
        """Set current class context."""
        self.class_name = value

    @property
    def current_function(self) -> Optional[str]:
        """Get current function context.""" 
        return self.function

    @current_function.setter
    def current_function(self, value: Optional[str]):
        """Set current function context."""
        self.function = value

    @property
    def current_phase(self) -> Optional[AnalysisPhase]:
        """Get current analysis phase."""
        return self.phase

    @current_phase.setter
    def current_phase(self, value: Optional[AnalysisPhase]):
        """Set current analysis phase."""
        self.phase = value

    # Logging methods - keep original interface with source parameter
    def error(self, message: str, source: str = "Unknown", extra: Optional[Dict[str, Any]] = None):
        """Log error message."""
        if self._should_log(LogLevel.ERROR):
            formatted = self._format_message(LogLevel.ERROR, message, source, extra)
            self._output(formatted)

    def warning(self, message: str, source: str = "Unknown", extra: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        if self._should_log(LogLevel.WARNING):
            formatted = self._format_message(LogLevel.WARNING, message, source, extra)
            self._output(formatted)

    def info(self, message: str, source: str = "Unknown", extra: Optional[Dict[str, Any]] = None):
        """Log info message."""
        if self._should_log(LogLevel.INFO):
            formatted = self._format_message(LogLevel.INFO, message, source, extra)
            self._output(formatted)

    def debug(self, message: str, source: str = "Unknown", extra: Optional[Dict[str, Any]] = None):
        """Log debug message."""
        if self._should_log(LogLevel.DEBUG):
            formatted = self._format_message(LogLevel.DEBUG, message, source, extra)
            self._output(formatted)

    def trace(self, message: str, source: str = "Unknown", extra: Optional[Dict[str, Any]] = None):
        """Log trace message."""
        if self._should_log(LogLevel.TRACE):
            formatted = self._format_message(LogLevel.TRACE, message, source, extra)
            self._output(formatted)


# Global logger instance management
_logger: Optional[AtlasLogger] = None


def configure_logger(
        level: LogLevel = LogLevel.INFO,
        output_file: Optional[Path] = None
    ) -> AtlasLogger:
    """Configure and return the global logger instance."""
    global _logger
    _logger = AtlasLogger(level, output_file)
    return _logger


def get_logger() -> AtlasLogger:
    """Get the global logger instance."""
    if _logger is None:
        configure_logger()
    return _logger
