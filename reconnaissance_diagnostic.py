#!/usr/bin/env python3
"""
Quick Reconnaissance Phase Diagnostic

The issue is likely that the refactored reconnaissance with the fixes 
is not being used, or there's a configuration issue.

This diagnostic will determine:
1. Is refactored reconnaissance available?
2. Is it being used when --implementation refactored is specified?
3. Are the attribute extraction fixes active?
"""

import sys
import os
import json

def check_reconnaissance_implementation():
    """Check which reconnaissance implementation is actually being used."""
    
    print("🔍 RECONNAISSANCE IMPLEMENTATION DIAGNOSTIC")
    print("=" * 60)
    
    # Check if refactored reconnaissance is available
    try:
        from analyzer.recon_compat import get_recon_info
        recon_info = get_recon_info()
        
        print(f"📊 Reconnaissance Information:")
        print(f"  Refactored available: {recon_info.get('refactored_available', False)}")
        print(f"  Recommended: {recon_info.get('recommended', 'unknown')}")
        print(f"  Original available: {recon_info.get('original_available', True)}")
        
    except ImportError as e:
        print(f"❌ Could not import reconnaissance info: {e}")
        return False
    
    # Test which implementation is actually being used
    print(f"\n🧪 Testing Implementation Selection:")
    
    # Create a simple test file with enum
    test_content = '''
from enum import Enum

class TestEnum(Enum):
    VALUE1 = "test1"
    VALUE2 = "test2"
'''
    
    with open("diagnostic_test.py", "w") as f:
        f.write(test_content)
    
    try:
        # Test original implementation
        print(f"\n--- Testing Original Implementation ---")
        from analyzer.recon_compat import run_reconnaissance_pass_compat
        from pathlib import Path
        
        test_files = [Path("diagnostic_test.py")]
        original_data = run_reconnaissance_pass_compat(test_files, use_refactored=False)
        
        test_enum = original_data.get("classes", {}).get("diagnostic_test.TestEnum", {})
        original_attrs = test_enum.get("attributes", {})
        print(f"  Original enum attributes: {list(original_attrs.keys())}")
        
        # Test refactored implementation
        print(f"\n--- Testing Refactored Implementation ---")
        refactored_data = run_reconnaissance_pass_compat(test_files, use_refactored=True)
        
        test_enum_ref = refactored_data.get("classes", {}).get("diagnostic_test.TestEnum", {})
        refactored_attrs = test_enum_ref.get("attributes", {})
        print(f"  Refactored enum attributes: {list(refactored_attrs.keys())}")
        
        # Compare
        print(f"\n📊 Comparison:")
        print(f"  Original found {len(original_attrs)} attributes")
        print(f"  Refactored found {len(refactored_attrs)} attributes")
        
        if len(original_attrs) > 0 and len(refactored_attrs) == 0:
            print(f"  🚨 ISSUE: Refactored reconnaissance is losing attribute data!")
            return False
        elif len(original_attrs) == len(refactored_attrs):
            print(f"  ✅ Both implementations extract the same number of attributes")
            return True
        else:
            print(f"  ⚠️  Different attribute counts - may indicate partial fix")
            return False
            
    except Exception as e:
        print(f"❌ Error during implementation testing: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        if os.path.exists("diagnostic_test.py"):
            os.remove("diagnostic_test.py")

def check_atlas_configuration():
    """Check how atlas.py is configured to use reconnaissance."""
    
    print(f"\n🔧 ATLAS CONFIGURATION CHECK:")
    
    # Check what implementation atlas.py would use
    try:
        from analyzer.recon_compat import get_recon_info
        from analyzer.analysis_compat import get_atlas_info
        
        recon_info = get_recon_info()
        atlas_info = get_atlas_info()
        
        print(f"  Atlas analysis refactored: {atlas_info.get('refactored_available', False)}")
        print(f"  Atlas recon refactored: {recon_info.get('refactored_available', False)}")
        
        # Simulate what --implementation refactored would do
        if atlas_info.get('refactored_available') and recon_info.get('refactored_available'):
            print(f"  ✅ --implementation refactored should use refactored for both passes")
        else:
            print(f"  ⚠️  --implementation refactored may not use refactored for both passes")
            
        return True
        
    except Exception as e:
        print(f"❌ Configuration check failed: {e}")
        return False

def diagnose_attribute_extraction():
    """Test the specific attribute extraction logic."""
    
    print(f"\n🔬 ATTRIBUTE EXTRACTION DIAGNOSIS:")
    
    try:
        # Test if the fixed visitors are available and working
        from analyzer.visitors.specialized.class_recon_visitor import ClassReconVisitor
        from analyzer.visitors.specialized.state_recon_visitor import StateReconVisitor
        from analyzer.utils.logger import get_logger
        from analyzer.type_inference import TypeInferenceEngine
        
        logger = get_logger()
        class_visitor = ClassReconVisitor("diagnostic_test", logger)
        type_inference = TypeInferenceEngine({})
        state_visitor = StateReconVisitor("diagnostic_test", logger, type_inference)
        
        print(f"  ✅ Specialized visitors imported successfully")
        
        # Test enum processing
        import ast
        enum_code = '''
class TestEnum(Enum):
    VALUE1 = "test1"
    VALUE2 = "test2"
'''
        
        tree = ast.parse(enum_code)
        class_node = tree.body[0]
        
        # Process class
        class_info = class_visitor.process_class_def(class_node)
        class_fqn = class_info["fqn"]
        
        # Set context  
        class_visitor.enter_class_context(class_fqn)
        state_visitor.set_class_context(class_fqn)
        
        # Process assignments
        enum_attrs_found = 0
        for child in class_node.body:
            if isinstance(child, ast.Assign):
                def attr_callback(name, info):
                    class_visitor.add_class_attribute(name, info)
                    nonlocal enum_attrs_found
                    enum_attrs_found += 1
                    print(f"    Found enum value: {name} = {info}")
                
                state_visitor.process_assign(child, attr_callback)
        
        class_visitor.exit_class_context()
        
        # Check results
        final_classes = class_visitor.get_classes_data()
        test_class = next((c for c in final_classes if "TestEnum" in c["fqn"]), None)
        
        if test_class and len(test_class.get("attributes", {})) > 0:
            print(f"  ✅ Attribute extraction is working: {list(test_class['attributes'].keys())}")
            return True
        else:
            print(f"  ❌ Attribute extraction is not working - no attributes found")
            return False
            
    except Exception as e:
        print(f"  ❌ Attribute extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run complete diagnostic."""
    
    results = []
    
    # Test 1: Check reconnaissance implementation availability
    recon_ok = check_reconnaissance_implementation()
    results.append(("Reconnaissance Implementation", recon_ok))
    
    # Test 2: Check atlas configuration
    atlas_ok = check_atlas_configuration()
    results.append(("Atlas Configuration", atlas_ok))
    
    # Test 3: Test attribute extraction directly
    attr_ok = diagnose_attribute_extraction()
    results.append(("Attribute Extraction", attr_ok))
    
    # Summary
    print(f"\n" + "=" * 60)
    print(f"📊 DIAGNOSTIC RESULTS:")
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if not result:
            all_passed = False
    
    print(f"\n🎯 DIAGNOSIS:")
    if all_passed:
        print(f"  ✅ All reconnaissance components are working correctly")
        print(f"  ❓ The issue may be elsewhere in the pipeline")
    else:
        print(f"  ❌ Found issues in reconnaissance phase")
        print(f"  🔧 The Phase 2 fixes may not be properly applied or active")
    
    print(f"\n💡 NEXT STEPS:")
    if not recon_ok:
        print(f"  1. Check if refactored reconnaissance is being used")
        print(f"  2. Verify the Phase 2 emergency fixes are applied")
        print(f"  3. Test with --implementation original vs refactored")
    
    if not attr_ok:
        print(f"  1. Apply the Phase 2 emergency fixes to specialized visitors")
        print(f"  2. Ensure state_visitor.process_assign() calls class_attr_callback")
        print(f"  3. Verify class_visitor.add_class_attribute() is working")

if __name__ == "__main__":
    main()
