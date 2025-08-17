#!/usr/bin/env python3
"""
Quick import test to verify the fixes work.
"""

def test_basic_imports():
    print("=== Quick Import Test ===")
    
    try:
        # Test the problematic imports
        print("1. Testing original utils imports...")
        from analyzer.utils import LOG_LEVEL, EXTERNAL_LIBRARY_ALLOWLIST, ViolationType
        print(f"   ✓ LOG_LEVEL = {LOG_LEVEL}")
        print(f"   ✓ EXTERNAL_LIBRARY_ALLOWLIST has {len(EXTERNAL_LIBRARY_ALLOWLIST)} items")
        print(f"   ✓ ViolationType.MISSING_PARAM_TYPE = {ViolationType.MISSING_PARAM_TYPE}")
        
        print("\n2. Testing original components...")
        from analyzer.analysis import AnalysisVisitor
        print("   ✓ AnalysisVisitor imported")
        
        from analyzer.resolver import NameResolver
        print("   ✓ NameResolver imported")
        
        from analyzer.symbol_table import SymbolTableManager
        print("   ✓ SymbolTableManager imported")
        
        print("\n3. Testing refactored components...")
        from analyzer.visitors.analysis_refactored import RefactoredAnalysisVisitor
        print("   ✓ RefactoredAnalysisVisitor imported")
        
        print("\n4. Testing compatibility layer...")
        from analyzer.analysis_compat import get_atlas_info
        info = get_atlas_info()
        print(f"   ✓ Atlas version: {info['version']}")
        print(f"   ✓ Refactored available: {info['refactored_available']}")
        
        print("\n🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_imports()
    if success:
        print("\n✅ Ready to run full tests!")
    else:
        print("\n❌ Need to fix more import issues.")
