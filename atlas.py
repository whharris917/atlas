#!/usr/bin/env python3
"""
Code Atlas Generation Script - Main Entry Point

This script orchestrates the two-pass analysis of a Python project to generate
a comprehensive JSON report about its structure and relationships.
"""

import sys
from analyzer.utils import (
    discover_python_files,
    validate_python_version,
    generate_json_report
)
from analyzer.recon import run_reconnaissance_pass
from analyzer.analysis import run_analysis_pass

def main() -> None:
    """Main execution function with clean architecture."""
    print("Code Atlas Generation Script - Enhanced with External Library Support and SocketIO Emit Detection")
    print("=" * 115)
    print()

    validate_python_version()

    python_files = discover_python_files()

    if not python_files:
        print("No Python files found in current directory.")
        sys.exit(1)

    print(f"Discovered {len(python_files)} Python files to analyze:")
    for py_file in python_files:
        print(f"  - {py_file.name}")
    print()

    try:
        # Two-pass architecture with inheritance-aware resolution, attribute cataloging, parameter type inference, and external library support
        recon_data = run_reconnaissance_pass(python_files)
        atlas = run_analysis_pass(python_files, recon_data)
        generate_json_report(recon_data, atlas)

        print("=== CODE ATLAS GENERATION COMPLETE ===")
        print("Analysis successful! Check 'code_atlas_report.json' for results.")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)

    except Exception as e:
        print(f"FATAL ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
