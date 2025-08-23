"""
Enhanced Logging System - Code Atlas

Centralized logging with structured output, configurable levels,
and context-aware formatting for better debugging and maintenance.
"""

import logging
import sys
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
    """Context information for structured logging."""
    
    def __init__(self, module: str = "atlas", phase: Optional[AnalysisPhase] = None, 
                 function: Optional[str] = None, file_name: Optional[str] = None,
                 extra: Optional[Dict[str, Any]] = None):
        self.module = module
        self.phase = phase
        self.function = function
        self.file_name = file_name
        self.extra = extra or {}
        self.indent_level = 0
    
    def with_indent(self, level: int) -> 'LogContext':
        """Create new context with different indent level."""
        new_context = LogContext(self.module, self.phase, self.function, self.file_name, self.extra)
        new_context.indent_level = level
        return new_context
    
    def with_function(self, function: str) -> 'LogContext':
        """Create new context with different function."""
        new_context = LogContext(self.module, self.phase, function, self.file_name, self.extra)
        new_context.indent_level = self.indent_level
        return new_context


class AtlasLogger:
    """Centralized logger for Code Atlas with structured output."""
    
    def __init__(self, level: LogLevel = LogLevel.INFO,
                 output_file: Optional[Path] = None,
                 show_timestamps: bool = False,
                 show_context: bool = True,
                 use_emojis: bool = True):
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
    
    def _format_message(self, level: LogLevel, message: str, context: LogContext,
                       extra_data: Optional[Dict[str, Any]] = None) -> str:
        """Format log message with context and styling."""
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
        
        # Context information
        if self.show_context:
            context_parts = []
            
            if context.module:
                context_parts.append(f"module:{context.module}")
            
            if context.phase:
                context_parts.append(f"phase:{context.phase.name}")
            
            if context.function:
                context_parts.append(f"func:{context.function}")
            
            if context.file_name:
                context_parts.append(f"file:{context.file_name}")
            
            if context_parts:
                parts.append(f"[{' '.join(context_parts)}]")
        
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
    
    def _log(self, level: LogLevel, message: str, context: LogContext,
             extra_data: Optional[Dict[str, Any]] = None):
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
    
    def error(self, message: str, context: Optional[LogContext] = None,
              extra_data: Optional[Dict[str, Any]] = None):
        """Log error message."""
        ctx = context or LogContext()
        self._log(LogLevel.ERROR, message, ctx, extra_data)
    
    def warning(self, message: str, context: Optional[LogContext] = None,
                extra_data: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        ctx = context or LogContext()
        self._log(LogLevel.WARNING, message, ctx, extra_data)
    
    def info(self, message: str, context: Optional[LogContext] = None,
             extra_data: Optional[Dict[str, Any]] = None):
        """Log info message."""
        ctx = context or LogContext()
        self._log(LogLevel.INFO, message, ctx, extra_data)
    
    def debug(self, message: str, context: Optional[LogContext] = None,
              extra_data: Optional[Dict[str, Any]] = None):
        """Log debug message."""
        ctx = context or LogContext()
        self._log(LogLevel.DEBUG, message, ctx, extra_data)
    
    def trace(self, message: str, context: Optional[LogContext] = None,
              extra_data: Optional[Dict[str, Any]] = None):
        """Log trace message."""
        ctx = context or LogContext()
        self._log(LogLevel.TRACE, message, ctx, extra_data)
    
    def section_header(self, title: str, context: Optional[LogContext] = None):
        """Log section header."""
        ctx = context or LogContext()
        
        if self.use_emojis:
            header = f"🚀 === {title.upper()} ==="
        else:
            header = f"=== {title.upper()} ==="
        
        self.info(header, ctx)
    
    def section_footer(self, title: str, context: Optional[LogContext] = None):
        """Log section footer."""
        ctx = context or LogContext()
        
        if self.use_emojis:
            footer = f"✅ === {title.upper()} COMPLETE ==="
        else:
            footer = f"=== {title.upper()} COMPLETE ==="
        
        self.info(footer, ctx)
    
    def progress(self, current: int, total: int, operation: str,
                context: Optional[LogContext] = None):
        """Log progress message."""
        ctx = context or LogContext()
        percentage = (current / total) * 100 if total > 0 else 0
        
        if self.use_emojis:
            progress_msg = f"⏳ Progress: {operation} ({current}/{total} - {percentage:.1f}%)"
        else:
            progress_msg = f"Progress: {operation} ({current}/{total} - {percentage:.1f}%)"
        
        self.info(progress_msg, ctx)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get logging statistics."""
        return self.statistics.copy()
    
    def close(self):
        """Close file handle if open."""
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None


# Global logger instance
_logger: Optional[AtlasLogger] = None


def get_logger(module_name: str = "atlas") -> AtlasLogger:
    """Get or create the global logger instance."""
    global _logger
    if _logger is None:
        _logger = AtlasLogger()
    return _logger


def configure_logger(level: LogLevel = LogLevel.INFO,
                    output_file: Optional[Path] = None,
                    show_timestamps: bool = False,
                    show_context: bool = True,
                    use_emojis: bool = True) -> AtlasLogger:
    """Configure the global logger."""
    global _logger
    _logger = AtlasLogger(level, output_file, show_timestamps, show_context, use_emojis)
    return _logger


def create_context(module: str, phase: Optional[AnalysisPhase] = None,
                  function: Optional[str] = None, file_name: Optional[str] = None) -> LogContext:
    """Create a logging context."""
    return LogContext(module, phase, function, file_name)


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
