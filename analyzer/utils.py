"""
Utilities and Configuration - Code Atlas

Contains shared constants, helper functions for logging, file discovery,
report generation, and version validation.
"""

import json
import pathlib
import sys
from typing import Dict, List, Any

from .logger import get_logger, LogContext, AnalysisPhase

logger = get_logger(__name__)

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


# --- Helper Functions ---

def discover_python_files() -> List[pathlib.Path]:
    """Discover Python files in current directory."""
    current_dir = pathlib.Path.cwd()
    script_name = "atlas.py"

    logger.debug("Discovering Python files in current directory",
                context=LogContext(phase=AnalysisPhase.DISCOVERY,
                                 extra={'directory': str(current_dir)}))

    python_files = []
    for py_file in current_dir.glob("*.py"):
        if py_file.name != script_name:
            python_files.append(py_file)
            logger.trace(f"Found Python file: {py_file.name}",
                        context=LogContext(phase=AnalysisPhase.DISCOVERY))
    
    # Also discover files in subdirectories if needed (optional)
    # for py_file in current_dir.rglob("*.py"):
    #     if py_file.name != script_name:
    #         python_files.append(py_file)

    logger.info(f"Discovered {len(python_files)} Python files for analysis",
               context=LogContext(phase=AnalysisPhase.DISCOVERY,
                                extra={'file_count': len(python_files),
                                       'excluded_script': script_name}))

    return python_files


def generate_json_report(recon_data: Dict[str, Any], atlas: Dict[str, Any]) -> None:
    """Generate final JSON report."""
    logger.info("Generating JSON report",
               context=LogContext(phase=AnalysisPhase.REPORTING))

    final_report = {
        "recon_data": recon_data,
        "atlas": atlas
    }

    output_file = pathlib.Path("code_atlas_report.json")
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)

        file_size = output_file.stat().st_size
        logger.info(f"Report successfully written: {output_file} ({file_size} bytes)",
                   context=LogContext(phase=AnalysisPhase.REPORTING,
                                    extra={'output_file': str(output_file),
                                           'file_size_bytes': file_size}))

    except Exception as e:
        logger.error(f"Failed to write JSON report: {e}",
                    context=LogContext(phase=AnalysisPhase.REPORTING,
                                     extra={'output_file': str(output_file)}))
        sys.exit(1)


def validate_python_version() -> None:
    """Validate Python version requirements."""
    required_version = (3, 9)
    current_version = sys.version_info[:2]
    
    logger.debug(f"Validating Python version: {current_version} >= {required_version}",
                context=LogContext(phase=AnalysisPhase.VALIDATION,
                                 extra={'current_version': current_version,
                                        'required_version': required_version}))
    
    if current_version < required_version:
        logger.error(f"Python version {current_version} is too old. Required: {required_version} or newer",
                    context=LogContext(phase=AnalysisPhase.VALIDATION,
                                     extra={'current_version_str': sys.version}))
        logger.info("Please upgrade Python and try again",
                   context=LogContext(phase=AnalysisPhase.VALIDATION))
        sys.exit(1)
    
    logger.info(f"Python version validation passed: {current_version}",
               context=LogContext(phase=AnalysisPhase.VALIDATION,
                                extra={'version_info': sys.version}))
