#!/usr/bin/env python3
"""
Quick test to check if the refactored visitor works now.
"""

import ast
import tempfile
import pathlib

def test_refactored_visitor():
    print("=== Quick Refactored Visitor Test ===")
    
    # Simple test code
    test_code = '''
def test_function():
    print("Hello")
    return 42

x = 10
'''
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        test_file = pathlib.Path(f.name)
    
    try:
        # Test reconnaissance first
        print("1. Testing reconnaissance...")
        from analyzer.recon import run_reconnaissance_pass
        recon_data = run_reconnaissance_pass([test_file])
        print(f"   ✓ Recon found {len(recon_data['functions'])} functions")
        
        # Test refactored analysis
        print("2. Testing refactored analysis...")
        from analyzer.visitors.analysis_refactored import RefactoredAnalysisVisitor
        
        source_code = test_file.read_text(encoding='utf-8')
        tree = ast.parse(source_code)
        module_name = test_file.stem
        
        visitor = RefactoredAnalysisVisitor(recon_data, module_name)
        visitor.visit(tree)
        
        # Check results
        report = visitor.module_report
        print(f"   ✓ Analysis completed")
        print(f"   ✓ Found {len(report['functions'])} functions")
        print(f"   ✓ Found {len(report['module_state'])} state variables")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        try:
            test_file.unlink()
        except:
            pass

if __name__ == "__main__":
    success = test_refactored_visitor()
    print(f"\nResult: {'✅ SUCCESS' if success else '❌ FAILED'}")
