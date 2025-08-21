"""
Utilities and Configuration - Code Atlas

Contains shared constants, helper functions for file discovery,
report generation, and version validation. Logging moved to dedicated logger module.
"""

import json
import pathlib
import sys
from typing import Dict, List, Any

from .logger import get_logger, create_context, AnalysisPhase

# --- Configuration Constants ---

EXTERNAL_LIBRARY_ALLOWLIST = {
    'flask_socketio',
    'flask',
    'socketio',
    'threading',
    'multiprocessing',
    'uuid'
}

# --- Helper Classes ---

class ViolationType:
    """Code standard violation types for enhanced logging."""
    MISSING_PARAM_TYPE = "MISSING_PARAM_TYPE"
    MISSING_RETURN_TYPE = "MISSING_RETURN_TYPE"
    UNRESOLVABLE_TYPE = "UNRESOLVABLE_TYPE"
    MISSING_CLASS_ANNOTATION = "MISSING_CLASS_ANNOTATION"


def log_violation(violation_type: str, details: str, impact: str, context_module: str = "code_checker"):
    """Log code standard violations with impact assessment using centralized logger."""
    logger = get_logger()
    context = create_context(context_module, AnalysisPhase.ANALYSIS, "violation_check")
    
    logger.warning(f"CODE VIOLATION [{violation_type}]: {details}", context)
    logger.info(f"Impact: {impact}", context.with_indent(1))
    logger.info("Action Required: Add appropriate type annotation", context.with_indent(1))


def discover_python_files() -> List[pathlib.Path]:
    """Discover Python files in current directory."""
    logger = get_logger()
    context = create_context("utils", AnalysisPhase.DISCOVERY, "discover_files")
    
    current_dir = pathlib.Path.cwd()
    script_name = "atlas.py"

    python_files = []
    for py_file in current_dir.glob("*.py"):
        if py_file.name != script_name:
            python_files.append(py_file)
    
    logger.debug(f"Discovered {len(python_files)} Python files in {current_dir}", context)
    for py_file in python_files:
        logger.trace(f"Found: {py_file.name}", context.with_indent(1))

    return python_files


def generate_json_report(recon_data: Dict[str, Any], atlas: Dict[str, Any]) -> None:
    """Generate final JSON report."""
    logger = get_logger()
    context = create_context("utils", AnalysisPhase.REPORTING, "generate_report")
    
    logger.info("Generating JSON report", context)

    final_report = {
        "recon_data": recon_data,
        "atlas": atlas
    }

    output_file = pathlib.Path("code_atlas_report.json")
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)

        file_size = output_file.stat().st_size
        logger.info(f"Report successfully written to: {output_file}", context)
        logger.debug(f"Report size: {file_size} bytes", context)

    except Exception as e:
        logger.error(f"Failed to write JSON report: {e}", context)
        sys.exit(1)


def validate_python_version() -> None:
    """Validate Python version requirements."""
    logger = get_logger()
    context = create_context("utils", AnalysisPhase.VALIDATION, "version_check")
    
    if sys.version_info < (3, 9):
        logger.error(f"This script requires Python 3.9 or newer", context)
        logger.error(f"Current version: {sys.version}", context)
        logger.error("Please upgrade Python and try again.", context)
        sys.exit(1)
    else:
        logger.debug(f"Python version check passed: {sys.version}", context)
