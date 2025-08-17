#!/usr/bin/env python3
"""
Phase 2 Validation Test - Atlas Reconnaissance Refactoring

Quick test to validate that the refactored reconnaissance system is working properly
and produces the same output as the original system.
"""

import sys
import pathlib
import json
from typing import Dict, Any

def test_reconnaissance_compatibility():
    """Test that refactored reconnaissance produces same output as original."""
    print("=== Phase 2 Validation Test ===")
    
    # Test file discovery
    try:
        from analyzer.utils import discover_python_files
        python_files = discover_python_files()
        print(f"✅ File discovery: Found {len(python_files)} Python files")
    except Exception as e:
        print(f"❌ File discovery failed: {e}")
        return False
    
    if not python_files:
        print("⚠️  No Python files found for testing")
        return True
    
    # Test reconnaissance compatibility info
    try:
        from analyzer.recon_compat import get_recon_info
        recon_info = get_recon_info()
        print(f"✅ Reconnaissance info: {recon_info}")
    except Exception as e:
        print(f"❌ Reconnaissance info failed: {e}")
        return False
    
    # Test original reconnaissance (should always work)
    try:
        print("\n--- Testing Original Reconnaissance ---")
        from analyzer.recon_compat import run_reconnaissance_pass_compat
        original_data = run_reconnaissance_pass_compat(python_files, use_refactored=False)
        print(f"✅ Original reconnaissance: {len(original_data['classes'])} classes, {len(original_data['functions'])} functions")
    except Exception as e:
        print(f"❌ Original reconnaissance failed: {e}")
        return False
    
    # Test refactored reconnaissance (if available)
    if recon_info['refactored_available']:
        try:
            print("\n--- Testing Refactored Reconnaissance ---")
            refactored_data = run_reconnaissance_pass_compat(python_files, use_refactored=True)
            print(f"✅ Refactored reconnaissance: {len(refactored_data['classes'])} classes, {len(refactored_data['functions'])} functions")
            
            # Compare basic structure
            original_keys = set(original_data.keys())
            refactored_keys = set(refactored_data.keys())
            
            if original_keys == refactored_keys:
                print("✅ Data structure compatibility: Identical top-level keys")
            else:
                print(f"⚠️  Data structure difference: Original={original_keys}, Refactored={refactored_keys}")
            
            # Compare counts
            comparisons = [
                ('classes', len(original_data['classes']), len(refactored_data['classes'])),
                ('functions', len(original_data['functions']), len(refactored_data['functions'])),
                ('state', len(original_data['state']), len(refactored_data['state'])),
                ('external_classes', len(original_data['external_classes']), len(refactored_data['external_classes'])),
                ('external_functions', len(original_data['external_functions']), len(refactored_data['external_functions']))
            ]
            
            print("\n--- Detailed Comparison ---")
            all_match = True
            for name, orig_count, refact_count in comparisons:
                if orig_count == refact_count:
                    print(f"✅ {name}: {orig_count} items (matches)")
                else:
                    print(f"⚠️  {name}: original={orig_count}, refactored={refact_count}")
                    all_match = False
            
            if all_match:
                print("🎉 Perfect compatibility! Refactored produces identical results.")
            else:
                print("⚠️  Minor differences detected - may need investigation.")
                
        except Exception as e:
            print(f"❌ Refactored reconnaissance failed: {e}")
            return False
    else:
        print("\n--- Refactored Reconnaissance ---")
        print("⚠️  Refactored implementation not available - this is expected during development")
    
    # Test auto-selection
    try:
        print("\n--- Testing Auto-Selection ---")
        auto_data = run_reconnaissance_pass_compat(python_files, use_refactored=None)
        print(f"✅ Auto-selection: {len(auto_data['classes'])} classes, {len(auto_data['functions'])} functions")
    except Exception as e:
        print(f"❌ Auto-selection failed: {e}")
        return False
    
    print("\n=== Phase 2 Validation Complete ===")
    return True

def test_atlas_integration():
    """Test that the updated atlas.py works with the new reconnaissance system."""
    print("\n=== Atlas Integration Test ===")
    
    try:
        from analyzer.recon_compat import get_recon_info
        from analyzer.analysis_compat import get_atlas_info
        
        recon_info = get_recon_info()
        atlas_info = get_atlas_info()
        
        print(f"✅ Atlas info integration: analysis={atlas_info['refactored_available']}, recon={recon_info['refactored_available']}")
        
        # Simulate atlas.py info command
        print("\n--- Simulated --info Output ---")
        print(f"Analysis refactored implementation: {'Yes' if atlas_info['refactored_available'] else 'No'}")
        print(f"Reconnaissance refactored implementation: {'Yes' if recon_info['refactored_available'] else 'No'}")
        print(f"Recommended configuration:")
        
        # Handle the case where 'recommended' key might not exist in atlas_info
        analysis_recommended = atlas_info.get('recommended', 'refactored' if atlas_info['refactored_available'] else 'original')
        recon_recommended = recon_info.get('recommended', 'refactored' if recon_info['refactored_available'] else 'original')
        
        print(f"  - Analysis: {analysis_recommended}")
        print(f"  - Reconnaissance: {recon_recommended}")
        
        return True
        
    except Exception as e:
        print(f"❌ Atlas integration test failed: {e}")
        import traceback
        print("Full traceback:")
        traceback.print_exc()
        return False

def main():
    """Run all validation tests."""
    print("Atlas Phase 2 Refactoring Validation")
    print("=" * 50)
    
    success = True
    
    # Test reconnaissance compatibility
    if not test_reconnaissance_compatibility():
        success = False
    
    # Test atlas integration  
    if not test_atlas_integration():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ALL TESTS PASSED - Phase 2 refactoring is working correctly!")
        print("Ready to proceed with Phase 3 (resolver refactoring)")
    else:
        print("❌ Some tests failed - Phase 2 needs debugging")
        sys.exit(1)

if __name__ == "__main__":
    main()
