#!/usr/bin/env python3
"""
Atlas Code Analysis Tool - Progressive Implementation

This script orchestrates the two-pass analysis of a Python project to generate
a comprehensive JSON report about its structure and relationships.

Automatically uses the best available implementation (refactored when available,
original as fallback) while maintaining full backward compatibility.

CRITICAL FIX: Now properly coordinates refactored resolver with refactored analysis.
"""

import sys
import argparse
from analyzer.utils import (
    discover_python_files,
    validate_python_version,
    generate_json_report
)
# Import both compatibility layers
from analyzer.recon_compat import run_reconnaissance_pass_compat, get_recon_info
from analyzer.analysis_compat import run_analysis_pass_compat, get_atlas_info

def main() -> None:
    """Main execution with intelligent implementation selection and resolver integration."""
    parser = argparse.ArgumentParser(
        description='Atlas Code Analysis Tool - Enhanced with Modular Architecture',
        epilog='Examples:\n'
               '  atlas                           # Auto-select best implementation\n'
               '  atlas --implementation original # Force original implementation\n'
               '  atlas --implementation refactored # Force refactored implementation\n'
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
        atlas_info = get_atlas_info()
        recon_info = get_recon_info()
        
        print("=== Atlas Information ===")
        print(f"Version: {atlas_info['version']}")
        print(f"Analysis refactored implementation: {'Yes' if atlas_info['refactored_available'] else 'No'}")
        print(f"Reconnaissance refactored implementation: {'Yes' if recon_info['refactored_available'] else 'No'}")
        print(f"Recommended configuration:")
        print(f"  - Analysis: {atlas_info['recommended']}")
        print(f"  - Reconnaissance: {recon_info['recommended']}")
        
        # Show resolver status
        try:
            from analyzer.resolver_compat import get_resolver_implementation_status
            resolver_status = get_resolver_implementation_status()
            print(f"Resolver refactored implementation: {'Yes' if resolver_status['refactored_available'] else 'No'}")
            print(f"  - Recommended resolver: {resolver_status['recommended']}")
        except ImportError:
            print("Resolver refactored implementation: No (not available)")
        
        sys.exit(0)
    
    # Set verbosity
    verbose = args.verbose and not args.quiet
    
    # Get implementation information
    atlas_info = get_atlas_info()
    recon_info = get_recon_info()
    
    # Determine implementation strategy with resolver coordination
    if args.implementation == 'refactored':
        if not atlas_info['refactored_available']:
            print("Error: Refactored analysis implementation not available.")
            print("   Use --implementation auto or --implementation original")
            sys.exit(1)
        if not recon_info['refactored_available']:
            print("Error: Refactored reconnaissance implementation not available.")
            print("   Use --implementation auto or --implementation original")
            sys.exit(1)
        
        use_refactored_analysis = True
        use_refactored_recon = True
        impl_display = "recon:refactored + analysis:refactored + resolver:refactored"
        if not args.quiet:
            print(f"Using: {impl_display} (explicitly requested)")
            
    elif args.implementation == 'auto':
        if not atlas_info['refactored_available'] and not recon_info['refactored_available']:
            print("Error: No refactored implementations available.")
            print("   Use --implementation auto or --implementation original")
            sys.exit(1)
        
        use_refactored_analysis = atlas_info['refactored_available']
        use_refactored_recon = recon_info['refactored_available']
        
        # Show what we're actually using
        impl_parts = []
        if use_refactored_recon:
            impl_parts.append("recon:refactored")
        else:
            impl_parts.append("recon:original")
        if use_refactored_analysis:
            impl_parts.append("analysis:refactored")
            impl_parts.append("resolver:refactored")  # When analysis is refactored, resolver should be too
        else:
            impl_parts.append("analysis:original")
        impl_display = " + ".join(impl_parts)
        
        if not args.quiet:
            print(f"Using: {impl_display} (best available)")
            
    else:  # original - Force BOTH to use original
        use_refactored_analysis = False
        use_refactored_recon = False
        impl_display = "recon:original + analysis:original + resolver:original"
        if not args.quiet:
            print(f"Using: {impl_display} (explicitly requested)")
    
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
        # Two-pass architecture with coordinated implementation selection
        if verbose:
            recon_impl = "REFACTORED" if use_refactored_recon else "ORIGINAL"
            print(f"=== PHASE 1: RECONNAISSANCE ({recon_impl}) ===")
        elif not args.quiet:
            print("Running reconnaissance pass...")
        
        # Phase 1: Reconnaissance with selected implementation
        recon_data = run_reconnaissance_pass_compat(python_files, use_refactored=use_refactored_recon)
        
        if verbose:
            analysis_impl = "REFACTORED" if use_refactored_analysis else "ORIGINAL"
            resolver_impl = "REFACTORED" if use_refactored_analysis else "ORIGINAL"
            print(f"=== PHASE 2: ANALYSIS ({analysis_impl}) + RESOLVER ({resolver_impl}) ===")
        elif not args.quiet:
            analysis_impl_name = "refactored" if use_refactored_analysis else "original"
            print(f"Running analysis pass ({analysis_impl_name})...")
        
        # Phase 2: Analysis with coordinated resolver implementation
        # CRITICAL: The analysis_compat now handles resolver integration internally
        atlas = run_analysis_pass_compat(python_files, recon_data, use_refactored=use_refactored_analysis)
        
        if verbose:
            print("=== GENERATING REPORT ===")
        elif not args.quiet:
            print("Generating report...")
        
        # Phase 3: Report generation
        generate_json_report(recon_data, atlas)

        if not args.quiet:
            print("=== CODE ATLAS GENERATION COMPLETE ===")
            print(f"Analysis successful using {impl_display}!")
            print("Check 'code_atlas_report.json' for results.")
            
            # Show a brief summary
            class_count = len(recon_data.get("classes", {}))
            function_count = len(recon_data.get("functions", {}))
            state_count = len(recon_data.get("state", {}))
            
            print(f"\nSummary: {class_count} classes, {function_count} functions, {state_count} state variables")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error during analysis: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
