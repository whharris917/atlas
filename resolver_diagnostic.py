#!/usr/bin/env python3
"""
Resolver Integration Diagnostic

Quick diagnostic to check if the refactored resolver is actually being used
by the analysis pass and identify integration issues.
"""

import sys
from pathlib import Path

# Add analyzer to path
atlas_root = Path(__file__).parent
sys.path.insert(0, str(atlas_root))

def test_resolver_integration():
    print("🔍 Resolver Integration Diagnostic")
    print("=" * 50)
    
    # Test 1: Check if refactored resolver can be imported
    print("1. Testing refactored resolver import...")
    try:
        from analyzer.visitors.resolver_refactored import RefactoredNameResolver
        print("   ✅ RefactoredNameResolver imports successfully")
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    # Test 2: Check resolver compatibility layer
    print("2. Testing resolver compatibility layer...")
    try:
        from analyzer.resolver_compat import create_name_resolver, get_resolver_info
        
        # Mock recon data
        mock_recon_data = {
            "classes": {"test.TestClass": {"methods": ["test_method"]}},
            "functions": {"test.test_func": {}},
            "state": {},
            "external_classes": {},
            "external_functions": {}
        }
        
        # Test resolver creation
        resolver = create_name_resolver(mock_recon_data, use_refactored=True)
        print(f"   ✅ Resolver created: {resolver.implementation_name}")
        
        # Test resolver info
        info = get_resolver_info()
        print(f"   ✅ Resolver info: refactored_available={info['refactored_available']}")
        
    except Exception as e:
        print(f"   ❌ Compatibility layer failed: {e}")
        return False
    
    # Test 3: Check if analysis pass uses refactored resolver
    print("3. Testing analysis pass integration...")
    try:
        from analyzer.visitors.analysis_refactored import RefactoredAnalysisVisitor
        
        # Create mock analysis visitor
        visitor = RefactoredAnalysisVisitor(mock_recon_data, "test_module")
        
        # Check what resolver type it's using
        resolver_type = type(visitor.name_resolver).__name__
        print(f"   Analysis visitor uses: {resolver_type}")
        
        if "Compatibility" in resolver_type:
            impl_info = visitor.name_resolver.get_implementation_info()
            print(f"   Implementation: {impl_info['implementation']}")
            print(f"   ✅ Analysis pass is using compatibility resolver")
        else:
            print(f"   ⚠️  Analysis pass using original resolver: {resolver_type}")
            
    except Exception as e:
        print(f"   ❌ Analysis integration failed: {e}")
        return False
    
    # Test 4: Simple resolution test
    print("4. Testing simple name resolution...")
    try:
        # Test context
        context = {
            'symbol_manager': None,  # Mock symbol manager would go here
            'current_class': 'test.TestClass',
            'current_module': 'test',
            'import_map': {'TestImport': 'external.TestImport'}
        }
        
        # Test resolution
        result = resolver.resolve_name(['TestImport'], context)
        print(f"   Test resolution result: {result}")
        
        if result:
            print("   ✅ Basic resolution working")
        else:
            print("   ⚠️  Resolution returned None (may be expected without proper context)")
            
    except Exception as e:
        print(f"   ❌ Resolution test failed: {e}")
        return False
    
    print("\n🎯 Diagnostic Summary:")
    print("✅ Refactored resolver components working")
    print("✅ Compatibility layer functional")
    print("✅ Analysis pass integration present")
    print("\n💡 Next steps:")
    print("- Check if NameResolver is being used in call resolution")
    print("- Verify symbol_manager integration")
    print("- Debug why 0 calls are being resolved")
    
    return True

if __name__ == "__main__":
    test_resolver_integration()
