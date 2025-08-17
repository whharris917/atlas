#!/usr/bin/env python3
"""
Import Test Script - Atlas Refactoring

Test that all refactored components can be imported correctly.
Place this in the same directory as atlas.py and run it first.
"""

import sys
import traceback

def test_imports():
    """Test all refactored component imports."""
    print("=== Atlas Import Test ===")
    
    test_results = {
        "original_components": [],
        "refactored_components": [],
        "errors": []
    }
    
    # Test original components
    print("\n1. Testing Original Components...")
    original_imports = [
        ("analyzer.analysis", "AnalysisVisitor"),
        ("analyzer.recon", "run_reconnaissance_pass"),
        ("analyzer.resolver", "NameResolver"),
        ("analyzer.type_inference", "TypeInferenceEngine"),
        ("analyzer.symbol_table", "SymbolTableManager"),
        ("analyzer.code_checker", "CodeStandardChecker"),
        ("analyzer.utils", "LOG_LEVEL")
    ]
    
    for module_name, component in original_imports:
        try:
            module = __import__(module_name, fromlist=[component])
            getattr(module, component)
            print(f"  ✓ {module_name}.{component}")
            test_results["original_components"].append(f"{module_name}.{component}")
        except Exception as e:
            print(f"  ✗ {module_name}.{component}: {e}")
            test_results["errors"].append(f"{module_name}.{component}: {e}")
    
    # Test refactored components
    print("\n2. Testing Refactored Components...")
    refactored_imports = [
        ("analyzer.core.configuration", "AnalysisConfig"),
        ("analyzer.utils.logger", "AnalysisLogger"),
        ("analyzer.utils.naming", "generate_fqn"),
        ("analyzer.visitors.base", "BaseVisitor"),
        ("analyzer.visitors.specialized.emit_visitor", "EmitVisitor"),
        ("analyzer.visitors.specialized.call_visitor", "CallVisitor"),
        ("analyzer.visitors.specialized.assignment_visitor", "AssignmentVisitor"),
        ("analyzer.visitors.analysis_refactored", "RefactoredAnalysisVisitor")
    ]
    
    for module_name, component in refactored_imports:
        try:
            module = __import__(module_name, fromlist=[component])
            getattr(module, component)
            print(f"  ✓ {module_name}.{component}")
            test_results["refactored_components"].append(f"{module_name}.{component}")
        except Exception as e:
            print(f"  ✗ {module_name}.{component}: {e}")
            test_results["errors"].append(f"{module_name}.{component}: {e}")
    
    # Test compatibility layer
    print("\n3. Testing Compatibility Layer...")
    try:
        from analyzer.analysis_compat import (
            CompatibilityAnalysisVisitor, 
            run_analysis_pass_compat,
            test_compatibility,
            get_atlas_info
        )
        print("  ✓ analyzer.analysis_compat imported successfully")
        
        # Test compatibility info
        info = get_atlas_info()
        print(f"  ✓ Atlas version: {info['version']}")
        print(f"  ✓ Refactored available: {info['refactored_available']}")
        
    except Exception as e:
        print(f"  ✗ Compatibility layer: {e}")
        test_results["errors"].append(f"Compatibility layer: {e}")
        traceback.print_exc()
    
    # Summary
    print(f"\n=== Test Summary ===")
    print(f"Original components working: {len(test_results['original_components'])}/{len(original_imports)}")
    print(f"Refactored components working: {len(test_results['refactored_components'])}/{len(refactored_imports)}")
    print(f"Total errors: {len(test_results['errors'])}")
    
    if test_results['errors']:
        print(f"\nErrors found:")
        for error in test_results['errors']:
            print(f"  - {error}")
        return False
    else:
        print(f"\n🎉 All imports successful! Ready for functionality testing.")
        return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
