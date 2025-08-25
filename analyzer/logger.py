#!/usr/bin/env python3
"""
Enhanced Logging System - Code Atlas

Centralized logging with highly verbose structured output, automatic source detection,
and comprehensive context tracking for detailed debugging visibility.
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


class LogContext:
    """Enhanced context information for highly verbose structured logging."""
    
    def __init__(
            self, 
            phase: AnalysisPhase,
            source: str,
            module: Optional[str] = None,
            class_name: Optional[str] = None,
            function: Optional[str] = None
        ):
        self.phase = phase
        self.source = source
        self.module = module
        self.class_name = class_name
        self.function = function
        self.indent_level = 0
    
    def with_source(self, source: str) -> 'LogContext':
        """Create new context with different source function."""
        new_context = LogContext(
            self.phase, 
            source,
            self.module, 
            self.class_name,
            self.function
        )
        new_context.indent_level = self.indent_level
        return new_context

    def with_class(self, class_name: str) -> 'LogContext':
        """Create new context with different class."""
        new_context = LogContext(
            self.phase, 
            self.source,
            self.module, 
            class_name,
            self.function 
        )
        new_context.indent_level = self.indent_level
        return new_context
    
    def with_function(self, function: str) -> 'LogContext':
        """Create new context with different function."""
        new_context = LogContext(
            self.phase,
            self.source,
            self.module, 
            self.class_name,
            function
        )
        new_context.indent_level = self.indent_level
        return new_context

    def with_indent(self, level: int) -> 'LogContext':
        """Create new context with different indent level."""
        new_context = LogContext(
            self.phase, 
            self.source,
            self.module, 
            self.class_name,
            self.function
        )
        new_context.indent_level = level
        return new_context


class AtlasLogger:
    """Enhanced centralized logger with highly verbose context formatting."""
    
    def __init__(
            self, 
            level: LogLevel = LogLevel.INFO,
            output_file: Optional[Path] = None
        ):
        self.level = level
        self.output_file = output_file
        
        # Initialize file output if specified
        self.file_handle = None
        if output_file:
            try:
                self.file_handle = open(output_file, 'w', encoding='utf-8')
            except Exception as e:
                print(f"Warning: Could not open log file {output_file}: {e}")
    
    def _should_log(self, level: LogLevel) -> bool:
        """Check if message should be logged based on current level."""
        return level.value <= self.level.value and self.level != LogLevel.SILENT
    
    def _format_message(
            self, 
            level: LogLevel, 
            message: str, 
            context: LogContext,
            extra: Optional[Dict[str, Any]] = None
        ) -> str:
        """Enhanced format with highly verbose context breakdown - all fields always shown."""

        parts = []
        
        # Level text
        parts.append(f"[{level.name}]")
        
        # Phase - should never be None
        phase_value = context.phase.name
        parts.append(f"[phase:{phase_value}]")

        # Source - Atlas function generating this log - should never be None
        source_value = context.source
        parts.append(f"[source:{source_value}]")
        
        # Module being analyzed - can be None
        module_value = context.module if context.module else "None"
        parts.append(f"[module:{module_value}]")
        
        # Class being analyzed - can be None
        class_value = context.class_name if context.class_name else "None"
        parts.append(f"[class:{class_value}]")
        
        # Function being analyzed - can be None
        function_value = context.function if context.function else "None"
        parts.append(f"[function:{function_value}]")
        
        # Indentation
        indent = "   " * context.indent_level
        if indent:
            parts.append(indent)
        
        # Main message
        parts.append(message)
        
        # Extra data
        if extra:
            extra_str = " | ".join(f"{k}={v}" for k, v in extra.items())
            parts.append(f" ({extra_str})")
        
        return " ".join(parts)
    
    def _output_message(self, formatted_message: str):
        """Output message to console and/or file."""
        # Console output
        print(formatted_message)
        
        # File output
        if self.file_handle:
            try:
                self.file_handle.write(formatted_message + "\n")
                self.file_handle.flush()
            except Exception as e:
                print(f"Warning: Could not write to log file: {e}")
    
    def _log(
            self, 
            level: LogLevel, 
            message: str, 
            context: LogContext,
            extra: Optional[Dict[str, Any]] = None
        ):
        """Internal logging method."""
        if not self._should_log(level):
            return
        
        # Format and output
        formatted = self._format_message(level, message, context, extra)
        self._output_message(formatted)
    
    def error(
            self, 
            message: str, 
            context: LogContext,
            extra: Optional[Dict[str, Any]] = None
        ):
        """Log error message."""
        self._log(LogLevel.ERROR, message, context, extra)
    
    def warning(
            self, 
            message: str, 
            context: LogContext,
            extra: Optional[Dict[str, Any]] = None
        ):
        """Log warning message."""
        self._log(LogLevel.WARNING, message, context, extra)
    
    def info(
            self, 
            message: str, 
            context: LogContext,
            extra: Optional[Dict[str, Any]] = None
        ):
        """Log info message."""
        self._log(LogLevel.INFO, message, context, extra)
    
    def debug(
            self, 
            message: str, 
            context: LogContext,
            extra: Optional[Dict[str, Any]] = None
        ):
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, context, extra)
    
    def trace(
            self, 
            message: str, 
            context: LogContext,
            extra: Optional[Dict[str, Any]] = None
        ):
        """Log trace message."""
        self._log(LogLevel.TRACE, message, context, extra)
    
    def section_header(
            self, 
            title: str, 
            context: LogContext
        ):
        """Log section header with visual formatting."""
        header = f"{'=' * 20} {title} {'=' * 20}"
        self._log(LogLevel.INFO, header, context)
    
    def section_footer(
            self,
            title: str,
            context: LogContext
        ):
        """Log section footer with visual formatting."""
        footer = f"{'=' * (42 + len(title))}"
        self._log(LogLevel.INFO, footer, context)


# Global logger instance
_logger: Optional[AtlasLogger] = None


def configure_logger(
        level: LogLevel = LogLevel.INFO,
        output_file: Optional[Path] = None
    ) -> AtlasLogger:
    """Configure and return the global logger instance."""
    global _logger
    _logger = AtlasLogger(level, output_file)
    return _logger


def get_logger(module_name: str) -> AtlasLogger:
    """Get the global logger instance."""
    if _logger is None:
        configure_logger()
    return _logger


if False:

    # Convenience functions for common logging patterns

    def log_error(message: str, context: Optional[LogContext] = None, extra: Optional[Dict[str, Any]] = None):
        """Log error message using global logger."""
        get_logger().error(message, context, extra)


    def log_warning(message: str, context: Optional[LogContext] = None, extra: Optional[Dict[str, Any]] = None):
        """Log warning message using global logger."""
        get_logger().warning(message, context, extra)


    def log_info(message: str, context: Optional[LogContext] = None, extra: Optional[Dict[str, Any]] = None):
        """Log info message using global logger."""
        get_logger().info(message, context, extra)


    def log_debug(message: str, context: Optional[LogContext] = None, extra: Optional[Dict[str, Any]] = None):
        """Log debug message using global logger."""
        get_logger().debug(message, context, extra)


    def log_trace(message: str, context: Optional[LogContext] = None, extra: Optional[Dict[str, Any]] = None):
        """Log trace message using global logger."""
        get_logger().trace(message, context, extra)


    def log_section_start(title: str, context: Optional[LogContext] = None):
        """Log section start using global logger."""
        get_logger().section_header(title, context)


    def log_section_end(title: str, context: Optional[LogContext] = None):
        """Log section end using global logger."""
        get_logger().section_footer(title, context)
