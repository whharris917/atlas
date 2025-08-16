"""
Utilities and Configuration - Code Atlas

Contains shared constants, helper functions for logging, file discovery,
report generation, and version validation.
"""

import json
import pathlib
import sys
from typing import Dict, List, Any

# --- Configuration Constants ---

EXTERNAL_LIBRARY_ALLOWLIST = {
    'flask_socketio',
    'flask',
    'socketio',
    'threading',
    'multiprocessing',
    'uuid'
}

LOG_LEVEL = 3  # 0=minimal, 1=normal, 2=verbose, 3=debug


# --- Helper Classes and Functions ---

class ViolationType:
    """Code standard violation types for enhanced logging."""
    MISSING_PARAM_TYPE = "MISSING_PARAM_TYPE"
    MISSING_RETURN_TYPE = "MISSING_RETURN_TYPE"
    UNRESOLVABLE_TYPE = "UNRESOLVABLE_TYPE"
    MISSING_CLASS_ANNOTATION = "MISSING_CLASS_ANNOTATION"


def log_violation(violation_type: str, details: str, impact: str, indent: int = 3):
    """Log code standard violations with impact assessment."""
    if LOG_LEVEL >= 1:
        print("  " * indent + f"[CODE_STANDARD_VIOLATION] {violation_type}: {details}")
        print("  " * indent + f"[IMPACT] {impact}")
        print("  " * indent + f"[ACTION_REQUIRED] Add appropriate type annotation")


def set_log_level(level: int) -> None:
    """Set logging level: 0=minimal, 1=normal, 2=verbose, 3=debug"""
    global LOG_LEVEL
    LOG_LEVEL = level
    print(f"Log level set to {level}")


def discover_python_files() -> List[pathlib.Path]:
    """Discover Python files in current directory."""
    current_dir = pathlib.Path.cwd()
    script_name = "atlas.py"

    python_files = []
    for py_file in current_dir.glob("*.py"):
        if py_file.name != script_name:
            python_files.append(py_file)
    
    # Also discover files in subdirectories if needed (optional)
    # for py_file in current_dir.rglob("*.py"):
    #     if py_file.name != script_name:
    #         python_files.append(py_file)

    return python_files


def generate_json_report(recon_data: Dict[str, Any], atlas: Dict[str, Any]) -> None:
    """Generate final JSON report."""
    print("=== GENERATING JSON REPORT ===")

    final_report = {
        "recon_data": recon_data,
        "atlas": atlas
    }

    output_file = pathlib.Path("code_atlas_report.json")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)

        print(f"Report successfully written to: {output_file}")
        print(f"Report size: {output_file.stat().st_size} bytes")

    except Exception as e:
        print(f"ERROR: Failed to write JSON report: {e}")
        sys.exit(1)


def validate_python_version() -> None:
    """Validate Python version requirements."""
    if sys.version_info < (3, 9):
        print("ERROR: This script requires Python 3.9 or newer")
        print(f"Current version: {sys.version}")
        print("Please upgrade Python and try again.")
        sys.exit(1)
