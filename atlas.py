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

from analyzer.logger import configure_logger, LogLevel, LogContext, AnalysisPhase, get_logger
from analyzer.utils import (
    discover_python_files,
    validate_python_version,
    generate_json_report,
    get_source
)
from analyzer.recon import run_reconnaissance_pass
from analyzer.analysis import run_analysis_pass


class AtlasMain:
    """Main application controller with consolidated logging."""
    
    def __init__(self):
        self.logger = None
    
    def _log(
            self, 
            level: LogLevel, 
            message: str, 
            phase: AnalysisPhase, 
            extra: Optional[Dict[str, Any]] = None
        ):
        """Consolidated logging for main application functions."""
        
        context = LogContext(
            phase=phase,
            source=get_source(),
            module=None,
            class_name=None,
            function=None
        )
        
        logger_method = {
            LogLevel.ERROR: get_logger(__name__).error,
            LogLevel.WARNING: get_logger(__name__).warning,
            LogLevel.INFO: get_logger(__name__).info,
            LogLevel.DEBUG: get_logger(__name__).debug,
            LogLevel.TRACE: get_logger(__name__).trace
        }[level]
        
        logger_method(message, context, extra)
    
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
        
        self._log(LogLevel.DEBUG, "Logging system configured successfully", phase=AnalysisPhase.DISCOVERY,
            extra={
                "configured_level": args.log_level, 
                "file_output": args.log_file is not None
            }
        )
        return self.logger
    
    def run_analysis(self):
        """Main execution function with clean architecture and enhanced logging."""
        
        self._log(LogLevel.INFO, "CODE ATLAS GENERATION", phase=AnalysisPhase.DISCOVERY)
        self._log(LogLevel.INFO, "Enhanced Python Project Analysis Tool", phase=AnalysisPhase.DISCOVERY)
        self._log(LogLevel.INFO, "Features: External Library Support, SocketIO Detection, Inheritance Analysis", phase=AnalysisPhase.DISCOVERY)

        try:
            validate_python_version()
            
            python_files = discover_python_files()

            if not python_files:
                self._log(LogLevel.ERROR, "No Python files found in current directory", phase=AnalysisPhase.DISCOVERY)
                sys.exit(1)

            self._log(LogLevel.INFO, f"Discovered {len(python_files)} Python files to analyze:", phase=AnalysisPhase.DISCOVERY, extra={"file_count": len(python_files)})
            
            for py_file in python_files:
                self._log(LogLevel.INFO, f"- {py_file.name}", phase=AnalysisPhase.DISCOVERY)

            # Two-pass architecture with comprehensive analysis
            self._log(LogLevel.INFO, "RECONNAISSANCE PASS", phase=AnalysisPhase.RECONNAISSANCE)
            recon_data = run_reconnaissance_pass(python_files)
            self._log(LogLevel.INFO, "RECONNAISSANCE PASS COMPLETE", phase=AnalysisPhase.RECONNAISSANCE)
            
            self._log(LogLevel.INFO, "ANALYSIS PASS", phase=AnalysisPhase.ANALYSIS)
            atlas = run_analysis_pass(python_files, recon_data)
            self._log(LogLevel.INFO, "ANALYSIS PASS COMPLETE", phase=AnalysisPhase.ANALYSIS)
            
            self._log(LogLevel.INFO, "REPORT GENERATION", phase=AnalysisPhase.REPORTING)
            generate_json_report(recon_data, atlas)
            self._log(LogLevel.INFO, "REPORT GENERATION COMPLETE", phase=AnalysisPhase.REPORTING)

            self._log(LogLevel.INFO, "CODE ATLAS GENERATION COMPLETE", phase=AnalysisPhase.REPORTING)
            self._log(LogLevel.INFO, "Analysis successful! Check 'code_atlas_report.json' for results.", phase=AnalysisPhase.REPORTING)
            
            # Print logging statistics if debug level or higher
            if self.logger and self.logger.level.value >= LogLevel.DEBUG.value:
                self._log(LogLevel.DEBUG, "Session statistics available", phase=AnalysisPhase.REPORTING, extra={"statistics": "available"})

        except KeyboardInterrupt:
            self._log(LogLevel.ERROR, "Operation cancelled by user", phase=AnalysisPhase.REPORTING)
            sys.exit(1)

        except Exception as e:
            self._log(LogLevel.ERROR, f"FATAL ERROR: {e}", phase=AnalysisPhase.REPORTING, extra={"error": str(e)})
            if self.logger and self.logger.level.value >= LogLevel.DEBUG.value:
                import traceback
                self._log(LogLevel.ERROR, f"Traceback: {traceback.format_exc()}", phase=AnalysisPhase.REPORTING)
            sys.exit(1)


def main() -> None:
    """Main entry point function."""
    atlas_app = AtlasMain()
    args = atlas_app.parse_arguments()
    atlas_app.setup_logging(args)
    atlas_app.run_analysis()


if __name__ == "__main__":
    main()
