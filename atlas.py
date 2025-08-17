#!/usr/bin/env python3
"""
Atlas Code Analysis Tool - Progressive Implementation

This script orchestrates the two-pass analysis of a Python project to generate
a comprehensive JSON report about its structure and relationships.

Automatically uses the best available implementation (refactored when available,
original as fallback) while maintaining full backward compatibility.
"""

import sys
import argparse
from analyzer.utils import (
    discover_python_files,
    validate_python_version,
    generate_json_report
)
from analyzer.recon import run_reconnaissance_pass
from analyzer.analysis_compat import run_analysis_pass_compat, get_atlas_info

def main() -> None:
    """Main execution with intelligent implementation selection."""
    parser = argparse.ArgumentParser(
        description='Atlas Code Analysis Tool - Enhanced with Modular Architecture',
        epilog='Examples:\n'
               '  atlas                           # Auto-select best implementation\n'
               '  atlas --implementation original # Force original implementation\n'
               '  atlas --verbose                 # Show detailed progress\n'
               '  atlas --quiet                   # Minimal output',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--implementation', choices=['original', 'refactored', 'auto'], 
                       default='auto', 
                       help='Implementation to use (default: auto-select best)')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Show detailed analysis progress')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Minimal output (overrides --verbose)')
    parser.add_argument('--info', action='store_true',
                       help='Show Atlas version info and exit')
    
    args = parser.parse_args()
    
    # Handle --info flag
    if args.info:
        info = get_atlas_info()
        print("=== Atlas Information ===")
        print(f"Version: {info['version']}")
        print(f"Refactored implementation available: {'Yes' if info['refactored_available'] else 'No'}")
        if info['refactored_available']:
            print(f"Log level: {info.get('log_level', 'Unknown')}")
            print(f"Emit detection: {'Enabled' if info.get('emit_detection_enabled', True) else 'Disabled'}")
            print(f"External libraries: {info.get('external_libraries_count', 'Unknown')} configured")
        return
    
    # Determine verbosity
    if args.quiet:
        verbose = False
        show_header = False
    else:
        verbose = args.verbose
        show_header = True
    
    if show_header:
        print("Code Atlas Generation Script - Enhanced with External Library Support and SocketIO Emit Detection")
        print("=" * 115)
    
    # Show implementation info (unless quiet)
    info = get_atlas_info()
    if not args.quiet:
        print(f"Available implementations:")
        print(f"  - Original: Always available")
        print(f"  - Refactored: {'Yes' if info['refactored_available'] else 'No'} {'' if info['refactored_available'] else 'Not available'}")
    
    # Determine which implementation to use
    if args.implementation == 'auto':
        use_refactored = info['refactored_available']
        impl_name = "refactored" if use_refactored else "original"
        if not args.quiet:
            print(f"Auto-selected: {impl_name} implementation")
    elif args.implementation == 'refactored':
        if not info['refactored_available']:
            print("  ERROR: Refactored implementation requested but not available!")
            print("   Use --implementation auto or --implementation original")
            sys.exit(1)
        use_refactored = True
        impl_name = "refactored"
        if not args.quiet:
            print(f"Using: {impl_name} implementation (explicitly requested)")
    else:  # original
        use_refactored = False
        impl_name = "original"
        if not args.quiet:
            print(f"Using: {impl_name} implementation (explicitly requested)")
    
    if not args.quiet:
        print()

    validate_python_version()
    python_files = discover_python_files()

    if not python_files:
        print("No Python files found in current directory.")
        sys.exit(1)

    if not args.quiet:
        print(f"Discovered {len(python_files)} Python files to analyze:")
        for py_file in python_files:
            print(f"  - {py_file.name}")
        print()

    try:
        # Two-pass architecture with intelligent implementation selection
        if verbose:
            print("=== PHASE 1: RECONNAISSANCE ===")
        elif not args.quiet:
            print("Running reconnaissance pass...")
        
        recon_data = run_reconnaissance_pass(python_files)
        
        if verbose:
            print(f"=== PHASE 2: ANALYSIS ({'REFACTORED' if use_refactored else 'ORIGINAL'}) ===")
        elif not args.quiet:
            print(f"Running analysis pass ({impl_name})...")
        
        atlas = run_analysis_pass_compat(python_files, recon_data, use_refactored=use_refactored)
        
        if verbose:
            print("=== GENERATING REPORT ===")
        elif not args.quiet:
            print("Generating report...")
        
        generate_json_report(recon_data, atlas)

        if not args.quiet:
            print("=== CODE ATLAS GENERATION COMPLETE ===")
            print(f"Analysis successful using {impl_name} implementation!")
            print("Check 'code_atlas_report.json' for results.")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)

    except Exception as e:
        print(f"FATAL ERROR: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
