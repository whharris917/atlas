#!/usr/bin/env python3
"""
Code Atlas Generation Script - Main Entry Point

This script orchestrates the two-pass analysis of a Python project to generate
a comprehensive JSON report about its structure and relationships.
"""

import sys
import argparse
import inspect
from pathlib import Path
from typing import Dict, Any, Optional

from analyzer.logger import configure_logger, LogLevel, AnalysisPhase, get_logger
from analyzer.utils import (
    discover_python_files,
    validate_python_version,
    generate_json_report,
    get_source
)
from analyzer.recon import run_reconnaissance_pass
from analyzer.analysis import run_analysis_pass


class AtlasMain:
    """Main application controller with automatic phase propagation to logger."""
    
    def __init__(self):
        self.logger = None
        
        # Initialize private phase attribute
        self._phase = AnalysisPhase.DISCOVERY

    @property
    def phase(self):
        return self._phase
    
    @phase.setter
    def phase(self, value):
        self._phase = value
        self._update_logger_phase()
    
    def _update_logger_phase(self):
        """Update logger phase whenever phase attribute changes."""
        if hasattr(self, 'logger') and self.logger is not None:
            self.logger.phase = self._phase

    def _log(
            self, 
            level: LogLevel, 
            message: str, 
            extra: Optional[Dict[str, Any]] = None
        ):
        """Consolidated logging for main application functions."""
        
        logger_method = {
            LogLevel.ERROR: get_logger().error,
            LogLevel.WARNING: get_logger().warning,
            LogLevel.INFO: get_logger().info,
            LogLevel.DEBUG: get_logger().debug,
            LogLevel.TRACE: get_logger().trace
        }[level]
        
        logger_method(message, get_source(), extra)
    
    def parse_arguments(self):
        """Parse command line arguments."""
        #self._log(LogLevel.TRACE, "Parsing command line arguments", phase=AnalysisPhase.DISCOVERY)
        
        parser = argparse.ArgumentParser(
            description="Generate comprehensive analysis of Python project structure"
        )
        
        parser.add_argument(
            "--log-level", 
            choices=['silent', 'error', 'warning', 'info', 'debug', 'trace'],
            default='info',
            help="Set logging verbosity level (default: info)"
        )
        
        parser.add_argument(
            "--log-file",
            type=Path,
            help="Output log messages to file in addition to console"
        )
        
        parser.add_argument(
            "--minimal-context",
            action='store_true',
            help="Reduce context information in log output"
        )
        
        args = parser.parse_args()
        """
        self._log(LogLevel.DEBUG, "Command line arguments parsed successfully", phase=AnalysisPhase.DISCOVERY,
            extra={
            "log_level": args.log_level, 
            "log_file": str(args.log_file) if args.log_file else None,
            "minimal_context": args.minimal_context
            }
        )
        """
        return args
    
    def setup_logging(self, args):
        """Setup logging based on command line arguments."""
        #self._log(LogLevel.TRACE, "Setting up logging system", phase=AnalysisPhase.DISCOVERY)
        
        level_map = {
            'silent': LogLevel.SILENT,
            'error': LogLevel.ERROR,
            'warning': LogLevel.WARNING,
            'info': LogLevel.INFO,
            'debug': LogLevel.DEBUG,
            'trace': LogLevel.TRACE
        }
        
        self.logger = configure_logger(
            level=level_map[args.log_level],
            output_file=args.log_file
        )
        
        # Set initial phase after logger is configured
        self._update_logger_phase()
        
        self._log(LogLevel.DEBUG, "Logging system configured successfully",
            extra={
                "configured_level": args.log_level, 
                "file_output": args.log_file is not None
            }
        )
        return self.logger
    
    def run_analysis(self):
        """Main execution function with clean architecture and enhanced logging."""
        
        self.phase = AnalysisPhase.DISCOVERY  # This triggers logger phase update

        self._log(LogLevel.INFO, "CODE ATLAS GENERATION")
        self._log(LogLevel.INFO, "Enhanced Python Project Analysis Tool")
        self._log(LogLevel.INFO, "Features: External Library Support, SocketIO Detection, Inheritance Analysis")

        try:
            validate_python_version()
            
            python_files = discover_python_files()

            if not python_files:
                self._log(LogLevel.ERROR, "No Python files found in current directory")
                sys.exit(1)

            self._log(LogLevel.INFO, f"Discovered {len(python_files)} Python files to analyze:", extra={"file_count": len(python_files)})
            
            for py_file in python_files:
                self._log(LogLevel.INFO, f"- {py_file.name}")

            self.phase = AnalysisPhase.RECONNAISSANCE  # This triggers logger phase update

            # Two-pass architecture with comprehensive analysis
            self._log(LogLevel.INFO, "RECONNAISSANCE PASS")
            recon_data = run_reconnaissance_pass(python_files)
            self._log(LogLevel.INFO, "RECONNAISSANCE PASS COMPLETE")
            
            self.phase = AnalysisPhase.ANALYSIS  # This triggers logger phase update

            self._log(LogLevel.INFO, "ANALYSIS PASS")
            atlas = run_analysis_pass(python_files, recon_data)
            self._log(LogLevel.INFO, "ANALYSIS PASS COMPLETE")
            
            self.phase = AnalysisPhase.REPORTING  # This triggers logger phase update

            self._log(LogLevel.INFO, "REPORT GENERATION")
            generate_json_report(recon_data, atlas)
            self._log(LogLevel.INFO, "REPORT GENERATION COMPLETE")

            self._log(LogLevel.INFO, "CODE ATLAS GENERATION COMPLETE")
            self._log(LogLevel.INFO, "Analysis successful! Check 'code_atlas_report.json' for results.")
            
            # Print logging statistics if debug level or higher
            if self.logger and self.logger.level.value >= LogLevel.DEBUG.value:
                self._log(LogLevel.DEBUG, "Session statistics available", extra={"statistics": "available"})

        except KeyboardInterrupt:
            self._log(LogLevel.ERROR, "Operation cancelled by user")
            sys.exit(1)

        except Exception as e:
            self._log(LogLevel.ERROR, f"FATAL ERROR: {e}", extra={"error": str(e)})
            if self.logger and self.logger.level.value >= LogLevel.DEBUG.value:
                import traceback
                self._log(LogLevel.ERROR, f"Traceback: {traceback.format_exc()}")
            sys.exit(1)


def main() -> None:
    """Main entry point function."""
    atlas_app = AtlasMain()
    args = atlas_app.parse_arguments()
    atlas_app.setup_logging(args)
    atlas_app.run_analysis()


if __name__ == "__main__":
    main()
