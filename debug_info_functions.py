#!/usr/bin/env python3
"""
Debug script to check what get_atlas_info() and get_recon_info() return
"""

def debug_info_functions():
    print("=== Debugging Info Functions ===")
    
    # Test atlas info
    try:
        from analyzer.analysis_compat import get_atlas_info
        atlas_info = get_atlas_info()
        print("✅ get_atlas_info() works")
        print(f"   Keys: {list(atlas_info.keys())}")
        print(f"   Content: {atlas_info}")
    except Exception as e:
        print(f"❌ get_atlas_info() failed: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test recon info  
    try:
        from analyzer.recon_compat import get_recon_info
        recon_info = get_recon_info()
        print("✅ get_recon_info() works")
        print(f"   Keys: {list(recon_info.keys())}")
        print(f"   Content: {recon_info}")
    except Exception as e:
        print(f"❌ get_recon_info() failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_info_functions()
