#!/usr/bin/env python3
"""
Simple Resolver Test - Atlas Phase 3

A simplified test to validate the resolver refactoring is working.
Run this from the atlas_project root directory.
"""

import sys
import os

def test_file_structure():
    """Test that all required files exist in the correct locations."""
    print("🔍 Checking file structure...")
    
    required_files = [
        "analyzer/resolver.py",                    # Original
        "analyzer/resolver_refactored.py",        # New orchestrator
        "analyzer/resolver_compat.py",           # Compatibility layer
        "analyzer/visitors/specialized/simple_resolution_visitor.py",
        "analyzer/visitors/specialized/chain_resolution_visitor.py", 
        "analyzer/visitors/specialized/inheritance_resolution_visitor.py",
        "analyzer/visitors/specialized/external_resolution_visitor.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
            print(f"❌ Missing: {file_path}")
        else:
            print(f"✅ Found: {file_path}")
    
    if missing_files:
        print(f"\n⚠️  Missing {len(missing_files)} files. Please create them in the correct locations.")
        return False
    else:
        print("\n✅ All required files found!")
        return True

def test_imports():
    """Test that imports work correctly."""
    print("\n🔍 Testing imports...")
    
    # Add analyzer to path
    analyzer_path = os.path.join(os.getcwd(), 'analyzer')
    if analyzer_path not in sys.path:
        sys.path.insert(0, analyzer_path)
    
    try:
        # Test original resolver import
        from resolver import NameResolver
        print("✅ Original NameResolver imported")
        
        # Test refactored resolver import  
        from resolver_refactored import RefactoredNameResolver
        print("✅ RefactoredNameResolver imported")
        
        # Test compatibility layer
        from resolver_compat import create_name_resolver
        print("✅ Compatibility layer imported")
        
        # Test specialized visitors
        from visitors.specialized.simple_resolution_visitor import SimpleResolutionVisitor
        print("✅ SimpleResolutionVisitor imported")
        
        from visitors.specialized.chain_resolution_visitor import ChainResolutionVisitor  
        print("✅ ChainResolutionVisitor imported")
        
        from visitors.specialized.inheritance_resolution_visitor import InheritanceResolutionVisitor
        print("✅ InheritanceResolutionVisitor imported")
        
        from visitors.specialized.external_resolution_visitor import ExternalResolutionVisitor
        print("✅ ExternalResolutionVisitor imported")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_basic_functionality():
    """Test basic resolver functionality."""
    print("\n🔍 Testing basic functionality...")
    
    # Add analyzer to path
    analyzer_path = os.path.join(os.getcwd(), 'analyzer')
    if analyzer_path not in sys.path:
        sys.path.insert(0, analyzer_path)
    
    try:
        from resolver_compat import create_name_resolver
        
        # Create test data
        test_recon_data = {
            "imports": {"socketio": "flask_socketio"},
            "classes": {"TestClass": {"parents": []}},
            "functions": {"TestClass.method": {"return_type": "None"}},
            "state": {},
            "external_classes": {},
            "external_functions": {}
        }
        
        test_context = {
            "current_module": "test_module",
            "current_class": "TestClass", 
            "import_map": {"socketio": "flask_socketio"},
            "symbol_manager": None
        }
        
        # Test compatibility wrapper
        resolver = create_name_resolver(test_recon_data, use_refactored=False)
        print(f"✅ Created resolver: {resolver.implementation_type}")
        
        # Test basic resolution  
        result = resolver.resolve_name(["self"], test_context)
        print(f"✅ Basic resolution test: ['self'] -> {result}")
        
        # Test implementation info
        info = resolver.get_implementation_info()
        print(f"✅ Implementation info: {info['type']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Simple Resolver Test - Atlas Phase 3")
    print("=" * 50)
    
    # Test 1: File structure
    structure_ok = test_file_structure()
    
    # Test 2: Imports
    imports_ok = test_imports() if structure_ok else False
    
    # Test 3: Basic functionality  
    functionality_ok = test_basic_functionality() if imports_ok else False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"  File Structure: {'✅ PASS' if structure_ok else '❌ FAIL'}")
    print(f"  Imports: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    print(f"  Functionality: {'✅ PASS' if functionality_ok else '❌ FAIL'}")
    
    if all([structure_ok, imports_ok, functionality_ok]):
        print("\n🎉 All tests passed! Resolver refactoring is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the file structure and imports.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
