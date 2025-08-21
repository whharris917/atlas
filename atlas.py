#!/usr/bin/env python3
"""
Code Atlas Generation Script - Main Entry Point

This script orchestrates the two-pass analysis of a Python project to generate
a comprehensive JSON report about its structure and relationships.
"""

import sys
import argparse
from pathlib import Path

from analyzer.logger import configure_logger, LogLevel, create_context, AnalysisPhase, log_info, log_error, log_section_start, log_section_end
from analyzer.utils import (
    discover_python_files,
    validate_python_version,
    generate_json_report
)
from analyzer.recon import run_reconnaissance_pass
from analyzer.analysis import run_analysis_pass


def parse_arguments():
    """Parse command line arguments."""
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
        "--show-timestamps",
        action='store_true',
        help="Include timestamps in log output"
    )
    
    parser.add_argument(
        "--minimal-context",
        action='store_true',
        help="Reduce context information in log output"
    )
    
    parser.add_argument(
        "--no-emojis",
        action='store_true',
        help="Use text indicators instead of emoji icons for better compatibility"
    )
    
    return parser.parse_args()


def setup_logging(args):
    """Setup logging based on command line arguments."""
    level_map = {
        'silent': LogLevel.SILENT,
        'error': LogLevel.ERROR,
        'warning': LogLevel.WARNING,
        'info': LogLevel.INFO,
        'debug': LogLevel.DEBUG,
        'trace': LogLevel.TRACE
    }
    
    return configure_logger(
        level=level_map[args.log_level],
        output_file=args.log_file,
        show_timestamps=args.show_timestamps,
        show_context=not args.minimal_context,
        use_emojis=not args.no_emojis
    )


def main() -> None:
    """Main execution function with clean architecture and enhanced logging."""
    args = parse_arguments()
    logger = setup_logging(args)
    
    context = create_context("atlas", AnalysisPhase.DISCOVERY, "main")
    
    log_section_start("CODE ATLAS GENERATION", context)
    log_info("Enhanced Python Project Analysis Tool", context)
    log_info("Features: External Library Support, SocketIO Detection, Inheritance Analysis", context)

    try:
        validate_python_version()
        
        python_files = discover_python_files()

        if not python_files:
            log_error("No Python files found in current directory", context)
            sys.exit(1)

        log_info(f"Discovered {len(python_files)} Python files to analyze:", context)
        for py_file in python_files:
            log_info(f"- {py_file.name}", context.with_indent(1))

        # Two-pass architecture with comprehensive analysis
        recon_context = create_context("atlas", AnalysisPhase.RECONNAISSANCE, "main")
        analysis_context = create_context("atlas", AnalysisPhase.ANALYSIS, "main")
        reporting_context = create_context("atlas", AnalysisPhase.REPORTING, "main")
        
        log_section_start("RECONNAISSANCE PASS", recon_context)
        recon_data = run_reconnaissance_pass(python_files)
        log_section_end("RECONNAISSANCE PASS", recon_context)
        
        log_section_start("ANALYSIS PASS", analysis_context)
        atlas = run_analysis_pass(python_files, recon_data)
        log_section_end("ANALYSIS PASS", analysis_context)
        
        log_section_start("REPORT GENERATION", reporting_context)
        generate_json_report(recon_data, atlas)
        log_section_end("REPORT GENERATION", reporting_context)

        log_section_end("CODE ATLAS GENERATION", context)
        log_info("Analysis successful! Check 'code_atlas_report.json' for results.", context)
        
        # Print logging statistics if debug level or higher
        if logger.level.value >= LogLevel.DEBUG.value:
            logger.print_statistics()

    except KeyboardInterrupt:
        log_error("Operation cancelled by user", context)
        sys.exit(1)

    except Exception as e:
        log_error(f"FATAL ERROR: {e}", context)
        if logger.level.value >= LogLevel.DEBUG.value:
            import traceback
            log_error(f"Traceback: {traceback.format_exc()}", context)
        sys.exit(1)


if __name__ == "__main__":
    main()
