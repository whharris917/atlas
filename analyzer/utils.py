"""
Utilities and Configuration - Code Atlas

Contains shared constants, helper functions for logging, file discovery,
report generation, and version validation.
"""

import json
import pathlib
import sys
import inspect
from typing import Dict, List, Any

from .logger import get_logger, LogContext, AnalysisPhase, LogLevel

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


def _log(level: LogLevel, message: str, phase: AnalysisPhase = AnalysisPhase.DISCOVERY, **extra):
    """Module-level consolidated logging for utils.py standalone functions."""
    try:
        source_frame = inspect.currentframe().f_back
        source_function = f"utils.{source_frame.f_code.co_name}"
    except Exception:
        source_function = "utils.unknown"
    
    context = LogContext(
        module="utils",
        phase=phase,
        source=source_function,
        extra=extra
    )
    
    getattr(get_logger(__name__), level.name.lower())(message, context=context)


# --- Helper Functions ---

def discover_python_files() -> List[pathlib.Path]:
    """Discover Python files in current directory."""
    current_dir = pathlib.Path.cwd()
    script_name = "atlas.py"

    _log(LogLevel.DEBUG, "Discovering Python files in current directory",
         directory=str(current_dir))

    python_files = []
    for py_file in current_dir.glob("*.py"):
        if py_file.name != script_name:
            python_files.append(py_file)
            _log(LogLevel.TRACE, f"Found Python file: {py_file.name}")
    
    # Also discover files in subdirectories if needed (optional)
    # for py_file in current_dir.rglob("*.py"):
    #     if py_file.name != script_name:
    #         python_files.append(py_file)

    _log(LogLevel.INFO, f"Discovered {len(python_files)} Python files for analysis",
         file_count=len(python_files), excluded_script=script_name)

    return python_files


def generate_json_report(recon_data: Dict[str, Any], atlas: Dict[str, Any]) -> None:
    """Generate final JSON report."""
    
    _log(LogLevel.DEBUG, "Starting JSON report generation",
         phase=AnalysisPhase.REPORTING)
    
    # Create comprehensive report structure
    report = {
        "metadata": {
            "version": "2.1",
            "generated_by": "Atlas Code Analysis Tool",
            "analysis_phases": ["reconnaissance", "analysis"],
            "features": [
                "External Library Support", 
                "SocketIO Detection", 
                "Inheritance Analysis",
                "Method Chain Tracking",
                "Type Inference"
            ]
        },
        "reconnaissance_data": recon_data,
        "analysis_data": atlas
    }

    try:
        output_file = "code_atlas_report.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        _log(LogLevel.INFO, f"Report generated successfully: {output_file}",
             phase=AnalysisPhase.REPORTING, 
             output_file=output_file,
             report_size_kb=round(len(json.dumps(report)) / 1024, 2))
        
    except Exception as e:
        _log(LogLevel.ERROR, f"Failed to generate report: {e}",
             phase=AnalysisPhase.REPORTING, error=str(e))
        raise


def validate_python_version() -> None:
    """Validate Python version compatibility."""
    
    _log(LogLevel.DEBUG, "Validating Python version compatibility")
    
    required_major = 3
    required_minor = 8
    
    current_major = sys.version_info.major
    current_minor = sys.version_info.minor
    
    current_version = f"{current_major}.{current_minor}"
    required_version = f"{required_major}.{required_minor}"
    
    if current_major < required_major or (current_major == required_major and current_minor < required_minor):
        error_msg = f"Python {required_version}+ required, but {current_version} found"
        _log(LogLevel.ERROR, error_msg,
             current_version=current_version,
             required_version=required_version)
        raise RuntimeError(error_msg)
    
    _log(LogLevel.TRACE, f"Python version validation passed: {current_version}",
         version_check="passed", python_version=current_version)
