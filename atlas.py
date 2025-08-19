#!/usr/bin/env python3
"""
Atlas Code Analysis Tool - Progressive Implementation

This script orchestrates the two-pass analysis of a Python project to generate
a comprehensive JSON report about its structure and relationships.

Automatically uses the best available implementation (refactored when available,
original as fallback) while maintaining full backward compatibility.

Updated: Added --resolver flag for testing resolver implementations independently.
"""

import sys
import argparse
from analyzer.utils import (
    discover_python_files,
    validate_python_version,
    generate_json_report
)
# FIX: Import both compatibility layers
from analyzer.recon_compat import run_reconnaissance_pass_compat, get_recon_info
from analyzer.analysis_compat import run_analysis_pass_compat, get_atlas_info
from analyzer.resolver import get_resolver_info


def main() -> None:
    """Main execution with intelligent implementation selection."""
    parser = argparse.ArgumentParser(
        description='Atlas Code Analysis Tool - Enhanced with Modular Architecture',
        epilog='Examples:\n'
               '  atlas                                    # Auto-select best implementation\n'
               '  atlas --implementation original          # Force original implementation\n'
               '  atlas --resolver reorganized             # Test reorganized resolver\n'
               '  atlas --implementation original --resolver original  # Full original stack\n'
               '  atlas --verbose                          # Show detailed progress\n'
               '  atlas --quiet                            # Minimal output',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--implementation', choices=['original', 'refactored', 'auto'], 
                       default='auto', 
                       help='Implementation to use for analysis/reconnaissance (default: auto-select best)')
    parser.add_argument('--resolver', choices=['original', 'reorganized', 'refactored', 'auto'],
                       default='auto',
                       help='Resolver implementation to use (default: auto-select best)')
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
        resolver_info = get_resolver_info()
        
        print("=== Atlas Information ===")
        print(f"Version: {atlas_info['version']}")
        print(f"Analysis refactored implementation: {'Yes' if atlas_info['refactored_available'] else 'No'}")
        print(f"Reconnaissance refactored implementation: {'Yes' if recon_info['refactored_available'] else 'No'}")
        
        print(f"\nResolver implementations:")
        print(f"  - Original: {'Yes' if resolver_info['original_available'] else 'No'}")
        print(f"  - Refactored: {'Yes' if resolver_info['refactored_available'] else 'No'}")
        print(f"  - Reorganized: {'Yes' if resolver_info.get('reorganized_available', False) else 'No'}")
        
        if atlas_info['refactored_available']:
            print(f"Log level: {atlas_info.get('log_level', 'Unknown')}")
            print(f"Emit detection: {'Enabled' if atlas_info.get('emit_detection_enabled', True) else 'Disabled'}")
            print(f"External libraries: {atlas_info.get('external_libraries_count', 'Unknown')} configured")
        
        print(f"Recommended configuration:")
        print(f"  - Analysis: {atlas_info.get('recommended', 'refactored' if atlas_info['refactored_available'] else 'original')}")
        print(f"  - Reconnaissance: {recon_info.get('recommended', 'refactored' if recon_info['refactored_available'] else 'original')}")
        print(f"  - Resolver: {resolver_info.get('recommended', 'auto')}")
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
    atlas_info = get_atlas_info()
    recon_info = get_recon_info()
    resolver_info = get_resolver_info()
    
    if not args.quiet:
        print(f"Available implementations:")
        print(f"  - Analysis Original: Always available")
        print(f"  - Analysis Refactored: {'Yes' if atlas_info['refactored_available'] else 'No'}")
        print(f"  - Reconnaissance Original: Always available")
        print(f"  - Reconnaissance Refactored: {'Yes' if recon_info['refactored_available'] else 'No'}")
        print(f"  - Resolver Original: {'Yes' if resolver_info['original_available'] else 'No'}")
        print(f"  - Resolver Refactored: {'Yes' if resolver_info['refactored_available'] else 'No'}")
        print(f"  - Resolver Reorganized: {'Yes' if resolver_info.get('reorganized_available', False) else 'No'}")
    
    # Handle implementation selection for analysis/reconnaissance
    if args.implementation == 'auto':
        use_refactored_analysis = atlas_info['refactored_available']
        use_refactored_recon = recon_info['refactored_available']
        
        impl_name = []
        if use_refactored_recon:
            impl_name.append("recon:refactored")
        else:
            impl_name.append("recon:original")
            
        if use_refactored_analysis:
            impl_name.append("analysis:refactored")
        else:
            impl_name.append("analysis:original")
            
        impl_display = " + ".join(impl_name)
        
        if not args.quiet:
            print(f"Auto-selected: {impl_display}")
            
    elif args.implementation == 'refactored':
        if not atlas_info['refactored_available'] and not recon_info['refactored_available']:
            print("  ERROR: Refactored implementations requested but neither available!")
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
        else:
            impl_parts.append("analysis:original")
        impl_display = " + ".join(impl_parts)
        
        if not args.quiet:
            print(f"Using: {impl_display} (best available refactored)")
            
    else:  # original - FIX: Force BOTH to use original
        use_refactored_analysis = False
        use_refactored_recon = False
        impl_display = "recon:original + analysis:original"
        if not args.quiet:
            print(f"Using: {impl_display} (explicitly requested)")
    
    # Handle resolver selection
    resolver_choice = args.resolver
    if resolver_choice == 'auto':
        # Use the recommended resolver from get_resolver_info()
        resolver_choice = resolver_info.get('recommended', 'original')
    
    # Validate resolver choice is available
    if resolver_choice == 'reorganized' and not resolver_info.get('reorganized_available', False):
        print(f"  ERROR: Reorganized resolver requested but not available!")
        print("   Use --resolver auto, --resolver original, or ensure resolver_reorganized.py is present")
        sys.exit(1)
    elif resolver_choice == 'refactored' and not resolver_info.get('refactored_available', False):
        print(f"  ERROR: Refactored resolver requested but not available!")
        print("   Use --resolver auto, --resolver original, or ensure RefactoredNameResolver is implemented")
        sys.exit(1)
    
    if not args.quiet:
        print(f"Resolver: {resolver_choice}")
        print()

    # Set resolver implementation in environment for compatibility layer to use
    import os
    os.environ['ATLAS_RESOLVER_IMPLEMENTATION'] = resolver_choice

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
            recon_impl = "REFACTORED" if use_refactored_recon else "ORIGINAL"
            print(f"=== PHASE 1: RECONNAISSANCE ({recon_impl}) ===")
        elif not args.quiet:
            print("Running reconnaissance pass...")
        
        # FIX: Use reconnaissance compatibility layer with proper flag
        recon_data = run_reconnaissance_pass_compat(python_files, use_refactored=use_refactored_recon)
        
        if verbose:
            analysis_impl = "REFACTORED" if use_refactored_analysis else "ORIGINAL"
            print(f"=== PHASE 2: ANALYSIS ({analysis_impl}) ===")
        elif not args.quiet:
            analysis_impl_name = "refactored" if use_refactored_analysis else "original"
            print(f"Running analysis pass ({analysis_impl_name})...")
        
        atlas = run_analysis_pass_compat(python_files, recon_data, use_refactored=use_refactored_analysis)
        
        if verbose:
            print("=== GENERATING REPORT ===")
        elif not args.quiet:
            print("Generating report...")
        
        generate_json_report(recon_data, atlas)

        if not args.quiet:
            print("=== CODE ATLAS GENERATION COMPLETE ===")
            print(f"Analysis successful using {impl_display} + resolver:{resolver_choice}!")
            print("Check 'code_atlas_report.json' for results.")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
