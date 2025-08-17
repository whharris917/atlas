# test_pure_original.py
import sys
import pathlib

# Import ONLY original components
from analyzer.utils import discover_python_files, validate_python_version, generate_json_report
from analyzer.recon import run_reconnaissance_pass  # Original recon
from analyzer.analysis import run_analysis_pass    # Original analysis

def run_pure_original():
    """Run Atlas using exclusively original code."""
    print("=== PURE ORIGINAL ATLAS ===")
    
    validate_python_version()
    python_files = discover_python_files()
    
    if not python_files:
        print("No Python files found.")
        return
    
    print(f"Found {len(python_files)} files to analyze")
    
    # Pure original reconnaissance
    print("Running ORIGINAL reconnaissance...")
    recon_data = run_reconnaissance_pass(python_files)
    
    # Pure original analysis  
    print("Running ORIGINAL analysis...")
    atlas = run_analysis_pass(python_files, recon_data)
    
    # Generate report
    generate_json_report(recon_data, atlas)
    print("Pure original analysis complete!")

if __name__ == "__main__":
    run_pure_original()
