#!/usr/bin/env python3
"""
Quick debug to see why use_refactored=True isn't working
"""

import sys
from pathlib import Path

atlas_root = Path(__file__).parent
sys.path.insert(0, str(atlas_root))

def debug_resolver_selection():
    print("🔍 Resolver Selection Debug")
    print("=" * 40)
    
    # Test the compatibility layer directly
    try:
        from analyzer.resolver_compat import create_name_resolver, REFACTORED_AVAILABLE
        
        print(f"1. REFACTORED_AVAILABLE: {REFACTORED_AVAILABLE}")
        
        # Mock data
        mock_recon_data = {"classes": {}, "functions": {}, "external_classes": {}, "external_functions": {}}
        
        # Test explicit refactored request
        print(f"2. Testing use_refactored=True...")
        resolver = create_name_resolver(mock_recon_data, use_refactored=True)
        info = resolver.get_implementation_info()
        print(f"   Implementation: {info['implementation']}")
        print(f"   Refactored Available: {info['refactored_available']}")
        
        # Test auto selection
        print(f"3. Testing use_refactored=None (auto)...")
        resolver_auto = create_name_resolver(mock_recon_data, use_refactored=None)
        info_auto = resolver_auto.get_implementation_info()
        print(f"   Implementation: {info_auto['implementation']}")
        
        # Debug the resolver creation process
        print(f"4. Debugging resolver creation...")
        print(f"   REFACTORED_AVAILABLE: {REFACTORED_AVAILABLE}")
        
        if REFACTORED_AVAILABLE:
            try:
                from analyzer.visitors.resolver_refactored import RefactoredNameResolver
                print("   ✅ RefactoredNameResolver imports successfully")
                
                # Test creating it directly
                direct_resolver = RefactoredNameResolver(mock_recon_data)
                print("   ✅ RefactoredNameResolver creates successfully")
                
            except Exception as e:
                print(f"   ❌ RefactoredNameResolver error: {e}")
        else:
            print("   ❌ REFACTORED_AVAILABLE is False")
            
            # Try importing manually
            try:
                from analyzer.visitors.resolver_refactored import RefactoredNameResolver
                print("   🤔 But manual import works... check the import error handling")
            except Exception as e:
                print(f"   ❌ Manual import also fails: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_resolver_selection()
