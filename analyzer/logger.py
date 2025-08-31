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


class AtlasLogger:
    """Enhanced centralized logger with highly verbose context formatting."""
    
    def __init__(
            self, 
            level: LogLevel = LogLevel.INFO,
            output_file: Optional[Path] = None
        ):
        self.level = level
        self.output_file = output_file

        self.phase = None
        self.module = None
        self.class_name = None
        self.function = None
        self.indent_level = 0
        
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
            source: str,
            extra: Optional[Dict[str, Any]] = None
        ) -> str:
        """Enhanced format with highly verbose context breakdown - all fields always shown."""

        parts = []
        
        # Level text
        parts.append(f"[{level.name}]")
        
        # Phase - should never be None
        parts.append(f"[phase:{self.phase}]")

        # Source - Atlas function generating this log - should never be None
        parts.append(f"[source:{source}]")
        
        # Module being analyzed - can be None
        parts.append(f"[module:{self.module}]")
        
        # Class being analyzed - can be None
        parts.append(f"[class:{self.class_name}]")
        
        # Function being analyzed - can be None
        parts.append(f"[function:{self.function}]")
        
        # Indentation
        indent = "   " * self.indent_level
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
            source: str,
            extra: Optional[Dict[str, Any]] = None
        ):
        """Internal logging method."""
        if not self._should_log(level):
            return
        
        # Format and output
        formatted = self._format_message(level, message, source, extra)
        self._output_message(formatted)
    
    def error(
            self, 
            message: str, 
            source: str,
            extra: Optional[Dict[str, Any]] = None
        ):
        """Log error message."""
        self._log(LogLevel.ERROR, message, source, extra)
    
    def warning(
            self, 
            message: str, 
            source: str,
            extra: Optional[Dict[str, Any]] = None
        ):
        """Log warning message."""
        self._log(LogLevel.WARNING, message, source, extra)
    
    def info(
            self, 
            message: str, 
            source: str,
            extra: Optional[Dict[str, Any]] = None
        ):
        """Log info message."""
        self._log(LogLevel.INFO, message, source, extra)
    
    def debug(
            self, 
            message: str, 
            source: str,
            extra: Optional[Dict[str, Any]] = None
        ):
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, source, extra)
    
    def trace(
            self, 
            message: str, 
            source: str,
            extra: Optional[Dict[str, Any]] = None
        ):
        """Log trace message."""
        self._log(LogLevel.TRACE, message, source, extra)
    
    def section_header(
            self, 
            title: str, 
            source: str
        ):
        """Log section header with visual formatting."""
        header = f"{'=' * 20} {title} {'=' * 20}"
        self._log(LogLevel.INFO, header, source)
    
    def section_footer(
            self,
            title: str,
            source: str,
        ):
        """Log section footer with visual formatting."""
        footer = f"{'=' * (42 + len(title))}"
        self._log(LogLevel.INFO, footer, source)


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


def get_logger() -> AtlasLogger:
    """Get the global logger instance."""
    if _logger is None:
        configure_logger()
    return _logger
