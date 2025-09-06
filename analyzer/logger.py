"""
Enhanced logging system for Atlas - Code Atlas

Provides hierarchical, context-aware logging with automatic indentation,
configurable output levels, and structured formatting for debugging.
"""

from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any


class LogLevel(Enum):
    """Logging levels in order of verbosity (lower values = more important)."""
    SILENT = 0
    ERROR = 1
    WARNING = 2
    INFO = 3
    DEBUG = 4
    TRACE = 5


class AnalysisPhase(Enum):
    """Analysis phases for context tracking."""
    DISCOVERY = "DISCOVERY"
    RECONNAISSANCE = "RECONNAISSANCE"
    ANALYSIS = "ANALYSIS"
    VALIDATION = "VALIDATION"
    REPORTING = "REPORTING"


class AtlasLogger:
    """
    Hierarchical logger with automatic context-aware indentation.
    
    Provides structured logging with phase, module, class, function, and source
    context tracking. Automatically displays hierarchical headers when context
    changes and properly indents messages based on their context depth.
    """
    
    def __init__(self, level: LogLevel = LogLevel.INFO, output_file: Optional[Path] = None):
        """Initialize logger with level and optional file output."""
        self.level = level
        self.file_handle = None
        
        # Context state
        self.phase: Optional[AnalysisPhase] = None
        self.source: Optional[str] = None
        self.module: Optional[str] = None
        self.class_name: Optional[str] = None
        self.function: Optional[str] = None
        
        # Previous context for change detection
        self.prev_phase: Optional[AnalysisPhase] = None
        self.prev_source: Optional[str] = None
        self.prev_module: Optional[str] = None
        self.prev_class_name: Optional[str] = None
        self.prev_function: Optional[str] = None
        
        # Configure file output if specified
        if output_file:
            try:
                self.file_handle = open(output_file, 'w', encoding='utf-8')
            except Exception as e:
                print(f"Warning: Could not open log file {output_file}: {e}")

    def _detect_context_changes(self) -> Dict[str, bool]:
        """Detect which context fields have changed since last message."""
        return {
            'phase': self.phase != self.prev_phase,
            'source': self.source != self.prev_source,
            'module': self.module != self.prev_module,
            'class': self.class_name != self.prev_class_name,
            'function': self.function != self.prev_function
        }

    def _invalidate_lower_rank_context(self, changes: Dict[str, bool]):
        """Invalidate lower-rank prev_* values when higher-rank context changes."""
        # Hierarchy: phase, module, class, function, source (highest to lowest)
        hierarchy = ['phase', 'module', 'class', 'function', 'source']
        
        # Find the highest-rank change
        highest_changed_index = None
        for i, level in enumerate(hierarchy):
            if changes[level]:
                highest_changed_index = i
                break
        
        # If any level changed, invalidate all lower-rank prev_* values
        if highest_changed_index is not None:
            for i in range(highest_changed_index + 1, len(hierarchy)):
                level = hierarchy[i]
                if level == 'module':
                    self.prev_module = None
                elif level == 'class':
                    self.prev_class_name = None
                elif level == 'function':
                    self.prev_function = None
                elif level == 'source':
                    self.prev_source = None

    def _update_previous_context(self):
        """Update previous context tracking for next comparison."""
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
        """Format message with hierarchical context headers and proper invalidation."""
        
        # 1. Update current context
        self.source = source
        
        # 2. Detect what changed
        changes = self._detect_context_changes()
        
        # 3. Invalidate lower-rank prev_* values based on changes
        self._invalidate_lower_rank_context(changes)
        
        # 4. Re-detect changes (now includes invalidated contexts)
        changes = self._detect_context_changes()
        
        parts = []
        current_depth = 0
        
        # 5. Show context headers when they change (includes invalidated contexts)
        if changes['phase'] and self.phase is not None:
            indent = "    " * current_depth
            parts.append(f"{indent}[phase:{self.phase}]")
            current_depth += 1
        elif self.phase is not None:
            # Phase exists and unchanged, count for depth
            current_depth += 1
        
        if changes['module'] and self.module is not None:
            indent = "    " * current_depth
            parts.append(f"{indent}[module:{self.module}]")
            current_depth += 1
        elif self.module is not None:
            # Module exists and unchanged, count for depth
            current_depth += 1
        
        if changes['class'] and self.class_name is not None:
            indent = "    " * current_depth
            parts.append(f"{indent}[class:{self.class_name}]")
            current_depth += 1
        elif self.class_name is not None:
            # Class exists and unchanged, count for depth
            current_depth += 1
        
        if changes['function'] and self.function is not None:
            indent = "    " * current_depth
            parts.append(f"{indent}[function:{self.function}]")
            current_depth += 1
        elif self.function is not None:
            # Function exists and unchanged, count for depth
            current_depth += 1
        
        if changes['source'] and self.source is not None:
            indent = "    " * current_depth
            parts.append(f"{indent}[source:{self.source}]")
            current_depth += 1
        elif self.source is not None:
            # Source exists and unchanged, count for depth
            current_depth += 1
        
        # 6. Add the actual message at the current context depth
        message_indent = "    " * current_depth
        message_part = f"{message_indent}[{level.name}] {message}"
        
        # Add extra data if present
        if extra:
            extra_str = " | ".join(f"{k}={v}" for k, v in extra.items())
            message_part += f"  ({extra_str})"
        
        parts.append(message_part)
        
        # 7. Update previous context for next comparison
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
