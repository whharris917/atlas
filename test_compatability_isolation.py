#!/usr/bin/env python3
"""
Isolation test to find what's causing differences between original and refactored output.
"""

import json
import tempfile
import pathlib
from typing import Dict, Any

def create_simple_test_file() -> pathlib.Path:
    """Create a very simple test file to isolate differences."""
    test_code = '''
"""Simple test module."""

def simple_function():
    """A simple function."""
    print("Hello")
    return 42

x = 10
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        return pathlib.Path(f.name)

def run_analysis_comparison(test_file: pathlib.Path):
    """Run both original and current analysis on the same file."""
    print("=== Isolation Test for Atlas Compatibility ===\n")
    
    # Test reconnaissance (should be identical)
    print("1. Testing reconnaissance pass...")
    from analyzer.recon import run_reconnaissance_pass
    recon_data = run_reconnaissance_pass([test_file])
    print(f"   Recon found: {len(recon_data['functions'])} functions, {len(recon_data['state'])} state vars")
    
    # Test original analysis
    print("\n2. Testing ORIGINAL analysis...")
    try:
        from analyzer.analysis import run_analysis_pass as original_analysis
        atlas_original = original_analysis([test_file], recon_data)
        print("   ✓ Original analysis completed")
    except Exception as e:
        print(f"   ❌ Original analysis failed: {e}")
        return
    
    # Test current analysis with --implementation original
    print("\n3. Testing CURRENT analysis with original flag...")
    try:
        from analyzer.analysis_compat import run_analysis_pass_compat
        atlas_current = run_analysis_pass_compat([test_file], recon_data, use_refactored=False)
        print("   ✓ Current analysis completed")
    except Exception as e:
        print(f"   ❌ Current analysis failed: {e}")
        return
    
    # Compare results
    print("\n4. Comparing results...")
    filename = test_file.name
    
    if filename not in atlas_original or filename not in atlas_current:
        print(f"   ❌ File {filename} missing from one analysis")
        return
    
    orig_data = atlas_original[filename]
    curr_data = atlas_current[filename]
    
    # Compare structure
    differences = []
    
    for key in ['classes', 'functions', 'imports', 'module_state']:
        orig_count = len(orig_data.get(key, []))
        curr_count = len(curr_data.get(key, []))
        
        if orig_count != curr_count:
            differences.append(f"{key}: {orig_count} vs {curr_count}")
        else:
            print(f"   ✓ {key}: {orig_count} items match")
    
    if differences:
        print(f"   ❌ Differences found: {differences}")
        
        # Show detailed differences
        print("\n5. Detailed differences:")
        
        # Compare functions in detail
        if len(orig_data.get('functions', [])) != len(curr_data.get('functions', [])):
            print(f"   Function count differs!")
            print(f"   Original functions: {[f['name'] for f in orig_data.get('functions', [])]}")
            print(f"   Current functions:  {[f['name'] for f in curr_data.get('functions', [])]}")
        
        # Compare specific function content
        for orig_func in orig_data.get('functions', []):
            func_name = orig_func['name']
            curr_func = next((f for f in curr_data.get('functions', []) if f['name'] == func_name), None)
            
            if curr_func:
                if orig_func.get('calls', []) != curr_func.get('calls', []):
                    print(f"   Function '{func_name}' calls differ:")
                    print(f"     Original: {orig_func.get('calls', [])}")
                    print(f"     Current:  {curr_func.get('calls', [])}")
        
        return False
    else:
        print("   🎉 All results match perfectly!")
        return True

def main():
    """Main isolation test."""
    test_file = create_simple_test_file()
    
    try:
        success = run_analysis_comparison(test_file)
        
        if not success:
            print("\n=== DEBUGGING INFO ===")
            print("The issue appears to be in our backward compatibility layer.")
            print("Please share the output above to help debug the differences.")
        
    finally:
        # Cleanup
        try:
            test_file.unlink()
        except:
            pass

if __name__ == "__main__":
    main()
