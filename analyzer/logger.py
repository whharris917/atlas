# Complete enhanced logger.py implementation
# analyzer/logger.py

"""
Enhanced Logging System - Code Atlas

Centralized logging with highly verbose structured output, automatic source detection,
and comprehensive context tracking for detailed debugging visibility.
"""

import logging
import sys
import inspect
from enum import Enum, auto
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime


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
            module: str = None,  # FIXED: No default "atlas" value
            phase: Optional[AnalysisPhase] = None, 
            function: Optional[str] = None, 
            file_name: Optional[str] = None,
            class_name: Optional[str] = None,
            source: Optional[str] = None,
            extra: Optional[Dict[str, Any]] = None
        ):
        self.module = module
        self.phase = phase
        self.function = function
        self.file_name = file_name
        self.class_name = class_name
        self.source = source
        self.extra = extra or {}
        self.indent_level = 0
    
    def with_indent(self, level: int) -> 'LogContext':
        """Create new context with different indent level."""
        new_context = LogContext(
            self.module, 
            self.phase, 
            self.function, 
            self.file_name, 
            self.class_name,
            self.source,
            self.extra
        )
        new_context.indent_level = level
        return new_context
    
    def with_function(self, function: str) -> 'LogContext':
        """Create new context with different function."""
        new_context = LogContext(
            self.module, 
            self.phase, 
            function, 
            self.file_name, 
            self.class_name,
            self.source,
            self.extra
        )
        new_context.indent_level = self.indent_level
        return new_context
    
    def with_class(self, class_name: str) -> 'LogContext':
        """Create new context with different class."""
        new_context = LogContext(
            self.module, 
            self.phase, 
            self.function, 
            self.file_name, 
            class_name,
            self.source,
            self.extra
        )
        new_context.indent_level = self.indent_level
        return new_context
    
    def with_source(self, source: str) -> 'LogContext':
        """Create new context with different source function."""
        new_context = LogContext(
            self.module, 
            self.phase, 
            self.function, 
            self.file_name, 
            self.class_name,
            source,
            self.extra
        )
        new_context.indent_level = self.indent_level
        return new_context


class AtlasLogger:
    """Enhanced centralized logger with highly verbose context formatting."""
    
    def __init__(
            self, 
            level: LogLevel = LogLevel.INFO,
            output_file: Optional[Path] = None,
            show_timestamps: bool = False,
            show_context: bool = True,
            use_emojis: bool = True
        ):
        self.level = level
        self.output_file = output_file
        self.show_timestamps = show_timestamps
        self.show_context = show_context
        self.use_emojis = use_emojis
        self.statistics = {
            'total_messages': 0,
            'error_count': 0,
            'warning_count': 0,
            'info_count': 0,
            'debug_count': 0,
            'trace_count': 0
        }
        
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
    
    def _get_level_emoji(self, level: LogLevel) -> str:
        """Get emoji for log level."""
        if not self.use_emojis:
            return ""
        
        emojis = {
            LogLevel.ERROR: "❌ ",
            LogLevel.WARNING: "⚠️ ",
            LogLevel.INFO: "ℹ️ ",
            LogLevel.DEBUG: "🔍 ",
            LogLevel.TRACE: "🔬 "
        }
        return emojis.get(level, "")
    
    def _get_phase_emoji(self, phase: Optional[AnalysisPhase]) -> str:
        """Get emoji for analysis phase."""
        if not self.use_emojis or not phase:
            return ""
        
        emojis = {
            AnalysisPhase.DISCOVERY: "🔎 ",
            AnalysisPhase.RECONNAISSANCE: "🕵️ ",
            AnalysisPhase.ANALYSIS: "🧠 ",
            AnalysisPhase.VALIDATION: "✅ ",
            AnalysisPhase.REPORTING: "📊 "
        }
        return emojis.get(phase, "")
    
    def _format_message(
            self, 
            level: LogLevel, 
            message: str, 
            context: LogContext,
            extra_data: Optional[Dict[str, Any]] = None
        ) -> str:
        """Enhanced format with highly verbose context breakdown - all fields always shown."""
        parts = []
        
        # Timestamp
        if self.show_timestamps:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            parts.append(f"[{timestamp}]")
        
        # Level and phase emojis
        level_emoji = self._get_level_emoji(level)
        phase_emoji = self._get_phase_emoji(context.phase)
        if level_emoji or phase_emoji:
            parts.append(f"{phase_emoji}{level_emoji}")
        
        # Level text
        parts.append(f"[{level.name}]")
        
        # Enhanced context information - ALL FIELDS ALWAYS SHOWN
        if self.show_context:
            # Phase - show even if None
            phase_value = context.phase.name if context.phase else "None"
            parts.append(f"[phase:{phase_value}]")
            
            # Module - show even if None
            module_value = context.module if context.module else "None"
            parts.append(f"[module:{module_value}]")
            
            # Class - show even if None
            class_value = context.class_name if context.class_name else "None"
            parts.append(f"[class:{class_value}]")
            
            # Function - show even if None
            function_value = context.function if context.function else "None"
            parts.append(f"[function:{function_value}]")
            
            # Source - Atlas function generating this log, show even if None
            source_value = context.source if context.source else "None"
            parts.append(f"[source:{source_value}]")
        
        # Indentation
        indent = "  " * context.indent_level
        if indent:
            parts.append(indent)
        
        # Main message
        parts.append(message)
        
        # Extra data
        if extra_data:
            extra_str = " | ".join(f"{k}={v}" for k, v in extra_data.items())
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
            extra_data: Optional[Dict[str, Any]] = None
        ):
        """Internal logging method."""
        if not self._should_log(level):
            return
        
        # Update statistics
        self.statistics['total_messages'] += 1
        if level == LogLevel.ERROR:
            self.statistics['error_count'] += 1
        elif level == LogLevel.WARNING:
            self.statistics['warning_count'] += 1
        elif level == LogLevel.INFO:
            self.statistics['info_count'] += 1
        elif level == LogLevel.DEBUG:
            self.statistics['debug_count'] += 1
        elif level == LogLevel.TRACE:
            self.statistics['trace_count'] += 1
        
        # Merge context extra data with provided extra data
        merged_extra = dict(context.extra)
        if extra_data:
            merged_extra.update(extra_data)
        
        # Format and output
        formatted = self._format_message(level, message, context, merged_extra)
        self._output_message(formatted)
    
    def error(
            self, 
            message: str, 
            context: Optional[LogContext] = None,
            extra_data: Optional[Dict[str, Any]] = None
        ):
        """Log error message."""
        ctx = context or LogContext()
        self._log(LogLevel.ERROR, message, ctx, extra_data)
    
    def warning(
            self, 
            message: str, 
            context: Optional[LogContext] = None,
            extra_data: Optional[Dict[str, Any]] = None
        ):
        """Log warning message."""
        ctx = context or LogContext()
        self._log(LogLevel.WARNING, message, ctx, extra_data)
    
    def info(
            self, 
            message: str, 
            context: Optional[LogContext] = None,
            extra_data: Optional[Dict[str, Any]] = None
        ):
        """Log info message."""
        ctx = context or LogContext()
        self._log(LogLevel.INFO, message, ctx, extra_data)
    
    def debug(
            self, 
            message: str, 
            context: Optional[LogContext] = None,
            extra_data: Optional[Dict[str, Any]] = None
        ):
        """Log debug message."""
        ctx = context or LogContext()
        self._log(LogLevel.DEBUG, message, ctx, extra_data)
    
    def trace(
            self, 
            message: str, 
            context: Optional[LogContext] = None,
            extra_data: Optional[Dict[str, Any]] = None
        ):
        """Log trace message."""
        ctx = context or LogContext()
        self._log(LogLevel.TRACE, message, ctx, extra_data)
    
    def section_header(self, title: str, context: Optional[LogContext] = None):
        """Log section header with visual formatting."""
        ctx = context or LogContext()
        header = f"{'=' * 20} {title} {'=' * 20}"
        self._log(LogLevel.INFO, header, ctx)
    
    def section_footer(self, title: str, context: Optional[LogContext] = None):
        """Log section footer with visual formatting."""
        ctx = context or LogContext()
        footer = f"{'=' * (42 + len(title))}"
        self._log(LogLevel.INFO, footer, ctx)
    
    def progress(self, current: int, total: int, operation: str, context: Optional[LogContext] = None):
        """Log progress information."""
        ctx = context or LogContext()
        percentage = (current / total) * 100 if total > 0 else 0
        progress_msg = f"Progress: {current}/{total} ({percentage:.1f}%) - {operation}"
        self._log(LogLevel.INFO, progress_msg, ctx)


# Global logger instance
_logger: Optional[AtlasLogger] = None


def configure_logger(
        level: LogLevel = LogLevel.INFO,
        output_file: Optional[Path] = None,
        show_timestamps: bool = False,
        show_context: bool = True,
        use_emojis: bool = True
    ) -> AtlasLogger:
    """Configure and return the global logger instance."""
    global _logger
    _logger = AtlasLogger(level, output_file, show_timestamps, show_context, use_emojis)
    return _logger


def get_logger(module_name: str = __name__) -> AtlasLogger:
    """Get the global logger instance."""
    if _logger is None:
        configure_logger()
    return _logger


def create_context(
        module: str, 
        phase: Optional[AnalysisPhase] = None,
        function: Optional[str] = None, 
        file_name: Optional[str] = None,
        class_name: Optional[str] = None,
        source: Optional[str] = None
    ) -> LogContext:
    """Create a comprehensive logging context."""
    return LogContext(module, phase, function, file_name, class_name, source)


def _analysis_context(
        module_name: str, 
        function: str = None, 
        class_name: str = None,
        source: str = None,
        **extra
) -> LogContext:
    """Create standardized analysis context with enhanced details."""
    return LogContext(
        module=module_name,
        phase=AnalysisPhase.ANALYSIS,
        function=function,
        class_name=class_name,
        source=source,
        **extra
    )


# Convenience functions for common logging patterns
def log_error(message: str, context: Optional[LogContext] = None, extra_data: Optional[Dict[str, Any]] = None):
    """Log error message using global logger."""
    get_logger().error(message, context, extra_data)


def log_warning(message: str, context: Optional[LogContext] = None, extra_data: Optional[Dict[str, Any]] = None):
    """Log warning message using global logger."""
    get_logger().warning(message, context, extra_data)


def log_info(message: str, context: Optional[LogContext] = None, extra_data: Optional[Dict[str, Any]] = None):
    """Log info message using global logger."""
    get_logger().info(message, context, extra_data)


def log_debug(message: str, context: Optional[LogContext] = None, extra_data: Optional[Dict[str, Any]] = None):
    """Log debug message using global logger."""
    get_logger().debug(message, context, extra_data)


def log_trace(message: str, context: Optional[LogContext] = None, extra_data: Optional[Dict[str, Any]] = None):
    """Log trace message using global logger."""
    get_logger().trace(message, context, extra_data)


def log_section_start(title: str, context: Optional[LogContext] = None):
    """Log section start using global logger."""
    get_logger().section_header(title, context)


def log_section_end(title: str, context: Optional[LogContext] = None):
    """Log section end using global logger."""
    get_logger().section_footer(title, context)


def log_progress(current: int, total: int, operation: str, context: Optional[LogContext] = None):
    """Log progress using global logger."""
    get_logger().progress(current, total, operation, context)
