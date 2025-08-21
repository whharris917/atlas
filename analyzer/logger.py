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
                 function: Optional[str] = None, file_name: Optional[str] = None):
        self.module = module
        self.phase = phase
        self.function = function
        self.file_name = file_name
        self.indent_level = 0
    
    def with_indent(self, level: int) -> 'LogContext':
        """Create new context with different indent level."""
        new_context = LogContext(self.module, self.phase, self.function, self.file_name)
        new_context.indent_level = level
        return new_context
    
    def with_function(self, function: str) -> 'LogContext':
        """Create new context with different function."""
        new_context = LogContext(self.module, self.phase, function, self.file_name)
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
        
        # Statistics tracking
        self.stats = {
            'total_messages': 0,
            'by_level': {level: 0 for level in LogLevel},
            'by_phase': {phase: 0 for phase in AnalysisPhase},
            'by_module': {}
        }
        
        # Setup file logging if requested
        if output_file:
            self._setup_file_logging()
    
    def _setup_file_logging(self):
        """Setup file logging handler."""
        logging.basicConfig(
            filename=self.output_file,
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filemode='w'
        )
    
    def _should_log(self, level: LogLevel) -> bool:
        """Check if message should be logged based on current level."""
        return level.value <= self.level.value
    
    def _format_message(self, message: str, context: LogContext, 
                       level: LogLevel, extra_data: Optional[Dict[str, Any]] = None) -> str:
        """Format log message with context and styling."""
        parts = []
        
        # Timestamp
        if self.show_timestamps:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            parts.append(f"[{timestamp}]")
        
        # Context information
        if self.show_context:
            context_parts = []
            
            if context.phase:
                context_parts.append(context.phase.name)
            
            if context.module != "atlas":
                context_parts.append(context.module.upper())
            
            if context.function:
                context_parts.append(context.function)
            
            if context.file_name:
                context_parts.append(f"({context.file_name})")
            
            if context_parts:
                parts.append(f"[{':'.join(context_parts)}]")
        
        # Level indicator
        if self.use_emojis:
            level_indicators = {
                LogLevel.ERROR: "❌",
                LogLevel.WARNING: "⚠️ ",
                LogLevel.INFO: "ℹ️ ",
                LogLevel.DEBUG: "🔍",
                LogLevel.TRACE: "🔬"
            }
        else:
            level_indicators = {
                LogLevel.ERROR: "[ERROR]",
                LogLevel.WARNING: "[WARN] ",
                LogLevel.INFO: "[INFO] ",
                LogLevel.DEBUG: "[DEBUG]",
                LogLevel.TRACE: "[TRACE]"
            }
        
        if level in level_indicators:
            parts.append(level_indicators[level])
        
        # Indentation
        indent = "  " * context.indent_level
        
        # Main message
        formatted_parts = " ".join(parts) if parts else ""
        formatted_message = f"{indent}{formatted_parts} {message}".strip()
        
        # Extra data
        if extra_data:
            formatted_message += f" {extra_data}"
        
        return formatted_message
    
    def _log(self, level: LogLevel, message: str, context: LogContext,
             extra_data: Optional[Dict[str, Any]] = None):
        """Internal logging method."""
        if not self._should_log(level):
            return
        
        formatted_message = self._format_message(message, context, level, extra_data)
        
        # Console output
        if level == LogLevel.ERROR:
            print(formatted_message, file=sys.stderr)
        else:
            print(formatted_message)
        
        # File output
        if self.output_file:
            log_level_map = {
                LogLevel.ERROR: logging.ERROR,
                LogLevel.WARNING: logging.WARNING,
                LogLevel.INFO: logging.INFO,
                LogLevel.DEBUG: logging.DEBUG,
                LogLevel.TRACE: logging.DEBUG
            }
            logging.log(log_level_map.get(level, logging.INFO), formatted_message)
        
        # Update statistics
        self._update_stats(level, context)
    
    def _update_stats(self, level: LogLevel, context: LogContext):
        """Update logging statistics."""
        self.stats['total_messages'] += 1
        self.stats['by_level'][level] += 1
        
        if context.phase:
            self.stats['by_phase'][context.phase] += 1
        
        if context.module not in self.stats['by_module']:
            self.stats['by_module'][context.module] = 0
        self.stats['by_module'][context.module] += 1
    
    def error(self, message: str, context: LogContext, extra_data: Optional[Dict[str, Any]] = None):
        """Log error message."""
        self._log(LogLevel.ERROR, message, context, extra_data)
    
    def warning(self, message: str, context: LogContext, extra_data: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        self._log(LogLevel.WARNING, message, context, extra_data)
    
    def info(self, message: str, context: LogContext, extra_data: Optional[Dict[str, Any]] = None):
        """Log info message."""
        self._log(LogLevel.INFO, message, context, extra_data)
    
    def debug(self, message: str, context: LogContext, extra_data: Optional[Dict[str, Any]] = None):
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, context, extra_data)
    
    def trace(self, message: str, context: LogContext, extra_data: Optional[Dict[str, Any]] = None):
        """Log trace message."""
        self._log(LogLevel.TRACE, message, context, extra_data)
    
    def section_header(self, title: str, context: LogContext, level: LogLevel = LogLevel.INFO):
        """Log a section header with decorative formatting."""
        if not self._should_log(level):
            return
        
        separator = "=" * min(60, len(title) + 10)
        self._log(level, separator, context)
        self._log(level, f"  {title}  ", context)
        self._log(level, separator, context)
    
    def section_footer(self, title: str, context: LogContext, level: LogLevel = LogLevel.INFO):
        """Log a section footer."""
        if not self._should_log(level):
            return
        
        separator = "=" * min(60, len(title) + 20)
        self._log(level, f"{title} COMPLETE", context)
        self._log(level, separator, context)
    
    def progress(self, current: int, total: int, operation: str, context: LogContext):
        """Log progress information."""
        if not self._should_log(LogLevel.INFO):
            return
        
        percentage = (current / max(total, 1)) * 100
        progress_bar = "█" * int(percentage // 5) + "░" * (20 - int(percentage // 5))
        message = f"{operation}: [{progress_bar}] {current}/{total} ({percentage:.1f}%)"
        self._log(LogLevel.INFO, message, context)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get logging statistics."""
        return self.stats.copy()
    
    def print_statistics(self):
        """Print logging statistics summary."""
        stats = self.get_statistics()
        context = LogContext("logger", AnalysisPhase.REPORTING)
        
        self.section_header("LOGGING STATISTICS", context)
        self.info(f"Total messages logged: {stats['total_messages']}", context)
        
        # By level
        self.info("Messages by level:", context.with_indent(1))
        for level, count in stats['by_level'].items():
            if count > 0:
                self.info(f"{level.name}: {count}", context.with_indent(2))
        
        # By phase
        self.info("Messages by phase:", context.with_indent(1))
        for phase, count in stats['by_phase'].items():
            if count > 0:
                self.info(f"{phase.name}: {count}", context.with_indent(2))
        
        # By module
        if stats['by_module']:
            self.info("Messages by module:", context.with_indent(1))
            for module, count in sorted(stats['by_module'].items()):
                self.info(f"{module}: {count}", context.with_indent(2))


# Global logger instance
_logger: Optional[AtlasLogger] = None


def get_logger() -> AtlasLogger:
    """Get the global logger instance."""
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
def log_error(message: str, context: LogContext, extra_data: Optional[Dict[str, Any]] = None):
    """Log error message using global logger."""
    get_logger().error(message, context, extra_data)


def log_warning(message: str, context: LogContext, extra_data: Optional[Dict[str, Any]] = None):
    """Log warning message using global logger."""
    get_logger().warning(message, context, extra_data)


def log_info(message: str, context: LogContext, extra_data: Optional[Dict[str, Any]] = None):
    """Log info message using global logger."""
    get_logger().info(message, context, extra_data)


def log_debug(message: str, context: LogContext, extra_data: Optional[Dict[str, Any]] = None):
    """Log debug message using global logger."""
    get_logger().debug(message, context, extra_data)


def log_trace(message: str, context: LogContext, extra_data: Optional[Dict[str, Any]] = None):
    """Log trace message using global logger."""
    get_logger().trace(message, context, extra_data)


def log_section_start(title: str, context: LogContext):
    """Log section start using global logger."""
    get_logger().section_header(title, context)


def log_section_end(title: str, context: LogContext):
    """Log section end using global logger."""
    get_logger().section_footer(title, context)


def log_progress(current: int, total: int, operation: str, context: LogContext):
    """Log progress using global logger."""
    get_logger().progress(current, total, operation, context)
