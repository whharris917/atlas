#!/usr/bin/env python3
"""
Test script to understand Python import resolution between
analyzer/utils.py and analyzer/utils/ directory.
"""

def test_import_resolution():
    print("=== Python Import Resolution Test ===")
    print("Testing how Python chooses between utils.py and utils/ directory\n")
    
    # Test 1: What does "from analyzer import utils" give us?
    print("1. Testing: from analyzer import utils")
    try:
        from analyzer import utils
        print(f"   Type: {type(utils)}")
        print(f"   File: {getattr(utils, '__file__', 'No __file__ attribute')}")
        print(f"   Is package: {hasattr(utils, '__path__')}")
        
        # Check what attributes it has
        attrs = [attr for attr in dir(utils) if not attr.startswith('_')]
        print(f"   Key attributes: {attrs[:10]}...")  # Show first 10
        
        # Test specific attributes we care about
        test_attrs = ['LOG_LEVEL', 'EXTERNAL_LIBRARY_ALLOWLIST', 'ViolationType', 'AnalysisLogger']
        for attr in test_attrs:
            has_attr = hasattr(utils, attr)
            print(f"   Has {attr}: {'✓' if has_attr else '✗'}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 2: What does direct import give us?
    print("2. Testing: from analyzer.utils import LOG_LEVEL")
    try:
        from analyzer.utils import LOG_LEVEL
        print(f"   LOG_LEVEL = {LOG_LEVEL}")
        print("   ✓ Direct import works")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 3: Can we still access original utils.py directly?
    print("3. Testing direct file access:")
    import os
    utils_py_path = "analyzer/utils.py"
    utils_dir_path = "analyzer/utils/"
    
    print(f"   utils.py exists: {os.path.exists(utils_py_path)}")
    print(f"   utils/ dir exists: {os.path.exists(utils_dir_path)}")
    
    print()
    
    # Test 4: Import order explanation
    print("4. Python Import Resolution Order:")
    print("   When Python sees 'from analyzer import utils', it looks for:")
    print("   1. analyzer/utils/__init__.py  ← FOUND (this is what gets imported)")
    print("   2. analyzer/utils.py           ← Ignored (directory takes precedence)")
    print()
    print("   📚 Python Rule: Package directories take precedence over modules")
    print("   📚 Since analyzer/utils/ exists with __init__.py, utils.py is ignored")
    
    print()
    
    # Test 5: How to access the original file if needed
    print("5. How to access original utils.py (if needed):")
    print("   You would need to rename it and import directly:")
    print("   - Rename utils.py -> utils_original.py") 
    print("   - Then: from analyzer.utils_original import LOG_LEVEL")
    print("   But this is NOT needed since our __init__.py provides everything!")

if __name__ == "__main__":
    test_import_resolution()
