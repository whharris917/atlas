"""
Utilities and Configuration - Code Atlas

Contains shared constants, helper functions for logging, file discovery,
report generation, and version validation.
"""

import json
import pathlib
import sys
import inspect, os
from typing import Dict, List, Any, Optional

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


def _log(level: LogLevel, message: str, phase: AnalysisPhase, extra: Optional[Dict[str, Any]] = None):
    """Module-level consolidated logging for utils.py standalone functions."""
    try:
        source_frame = inspect.currentframe().f_back
        source_method_name = source_frame.f_code.co_name
        source_function = f"utils.{source_method_name}"
    except Exception as e:
        source_function = f"utils.unknown_error_{str(e)}"
    
    context = LogContext(
        phase=phase,
        source=source_function,
        module=None,
        class_name=None,
        function=None
    )
        
    getattr(get_logger(__name__), level.name.lower())(message, context=context, extra=extra)

# --- Helper Functions ---

def discover_python_files() -> List[pathlib.Path]:
    """Discover Python files in current directory."""
    current_dir = pathlib.Path.cwd()
    script_name = "atlas.py"

    _log(LogLevel.DEBUG, "Discovering Python files in current directory", phase=AnalysisPhase.DISCOVERY, extra={"directory": str(current_dir)})

    python_files = []
    for py_file in current_dir.glob("*.py"):
        if py_file.name != script_name:
            python_files.append(py_file)
            _log(LogLevel.TRACE, f"Found Python file: {py_file.name}", phase=AnalysisPhase.DISCOVERY)
    
    # Also discover files in subdirectories if needed (optional)
    # for py_file in current_dir.rglob("*.py"):
    #     if py_file.name != script_name:
    #         python_files.append(py_file)

    _log(LogLevel.INFO, f"Discovered {len(python_files)} Python files for analysis", phase=AnalysisPhase.DISCOVERY, 
        extra={"file_count": len(python_files), "excluded_script": script_name})

    return python_files


def generate_json_report(recon_data: Dict[str, Any], atlas: Dict[str, Any]) -> None:
    """Generate final JSON report."""
    
    _log(LogLevel.DEBUG, "Starting JSON report generation", phase=AnalysisPhase.REPORTING)
    
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
        
        _log(LogLevel.INFO, f"Report generated successfully: {output_file}", phase=AnalysisPhase.REPORTING, 
            extra={
                "output_file": output_file,
                "report_size_kb": round(len(json.dumps(report)) / 1024, 2)
            }
        )

    except Exception as e:
        _log(LogLevel.ERROR, f"Failed to generate report: {e}", phase=AnalysisPhase.REPORTING, extra={"error": str(e)})
        raise


def validate_python_version() -> None:
    """Validate Python version compatibility."""
    
    _log(LogLevel.DEBUG, "Validating Python version compatibility", phase=AnalysisPhase.DISCOVERY)
    
    required_major = 3
    required_minor = 8
    
    current_major = sys.version_info.major
    current_minor = sys.version_info.minor
    
    current_version = f"{current_major}.{current_minor}"
    required_version = f"{required_major}.{required_minor}"
    
    if current_major < required_major or (current_major == required_major and current_minor < required_minor):
        error_msg = f"Python {required_version}+ required, but {current_version} found"
        _log(LogLevel.ERROR, error_msg, phase=AnalysisPhase.DISCOVERY,
            extra={
                "current_version": current_version,
                "required_version": required_version
            }
        )
        raise RuntimeError(error_msg)
    
    _log(LogLevel.TRACE, f"Python version validation passed: {current_version}", phase=AnalysisPhase.DISCOVERY,
        extra={
            "version_check": "passed", 
            "python_version": current_version
        }
    )


def get_source(source_to_show_if_error: Optional[str] = None):
    """
    Inspects the call stack to find the module, class, and function name
    of the code that called the function that called this one.
    """
    source_function = "Unknown"
    source_frame = None 
    
    try:
        frame_stack = inspect.currentframe()
        if frame_stack and frame_stack.f_back and frame_stack.f_back.f_back:
            source_frame = frame_stack.f_back.f_back
        else:
            return "Stack too shallow to determine source"

        # --- 1. Get module name (Modified Logic) ---
        module_globals = source_frame.f_globals
        module_name = module_globals.get('__name__')

        if module_name == '__main__':
            # If the script is run directly, derive name from the file path
            file_path = module_globals.get('__file__')
            if file_path:
                # Get the base filename (e.g., 'main.py')
                base_name = os.path.basename(file_path)
                # Get the name without the .py extension
                module_name = os.path.splitext(base_name)[0]
            else:
                module_name = 'main' # Fallback if __file__ is not available
        
        # --- 2. Get class name ---
        class_name = None
        if 'self' in source_frame.f_locals:
            class_name = source_frame.f_locals['self'].__class__.__name__
        elif 'cls' in source_frame.f_locals:
            class_name = source_frame.f_locals['cls'].__name__

        # --- 3. Get function/method name ---
        method_name = source_frame.f_code.co_name

        # --- 4. Assemble the final source string ---
        if class_name:
            source_function = f"{module_name}.{class_name}.{method_name}"
        else:
            source_function = f"{module_name}.{method_name}"
        
        return source_function
    
    except Exception as e:
        if source_to_show_if_error:
            source_function = f"{source_to_show_if_error}.unknown_error_{str(e)}"
        else:
            source_function = f"unknown_error_{str(e)}"
        return source_function
    
    finally:
        del source_frame
        if 'frame_stack' in locals():
            del frame_stack
