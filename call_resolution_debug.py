#!/usr/bin/env python3
"""
Call Resolution Debug Script

Debug why the refactored implementation isn't resolving calls properly.
"""

import sys
import ast
from pathlib import Path

# Add analyzer to path
atlas_root = Path(__file__).parent
sys.path.insert(0, str(atlas_root))

def debug_call_resolution():
    print("🔍 Call Resolution Debug")
    print("=" * 50)
    
    # Step 1: Test the original resolver directly
    print("1. Testing original resolver...")
    try:
        from analyzer.resolver import NameResolver as OriginalNameResolver
        
        # Mock recon data
        mock_recon_data = {
            "classes": {"session_manager.SessionManager": {"methods": ["get_session"]}},
            "functions": {"session_manager.create_session": {}},
            "state": {"session_manager.session_store": {}},
            "external_classes": {"flask_socketio.SocketIO": {"local_alias": "SocketIO"}},
            "external_functions": {"flask_socketio.emit": {"local_alias": "emit"}}
        }
        
        original_resolver = OriginalNameResolver(mock_recon_data)
        
        # Test context
        context = {
            'symbol_manager': None,
            'current_class': None,
            'current_module': 'session_manager',
            'import_map': {'SocketIO': 'flask_socketio.SocketIO', 'emit': 'flask_socketio.emit'}
        }
        
        # Test resolution
        result1 = original_resolver.resolve_name(['SocketIO'], context)
        result2 = original_resolver.resolve_name(['emit'], context)
        print(f"   Original resolver: SocketIO -> {result1}")
        print(f"   Original resolver: emit -> {result2}")
        
    except Exception as e:
        print(f"   ❌ Original resolver error: {e}")
    
    # Step 2: Test the refactored resolver
    print("\n2. Testing refactored resolver...")
    try:
        from analyzer.resolver_compat import create_name_resolver
        
        refactored_resolver = create_name_resolver(mock_recon_data, use_refactored=True)
        
        # Same test
        result1 = refactored_resolver.resolve_name(['SocketIO'], context)
        result2 = refactored_resolver.resolve_name(['emit'], context)
        print(f"   Refactored resolver: SocketIO -> {result1}")
        print(f"   Refactored resolver: emit -> {result2}")
        
    except Exception as e:
        print(f"   ❌ Refactored resolver error: {e}")
    
    # Step 3: Test with actual sample file
    print("\n3. Testing with actual sample file...")
    sample_file = atlas_root / "sample_files" / "session_manager.py"
    
    if sample_file.exists():
        print(f"   Analyzing: {sample_file.name}")
        
        try:
            # Read and parse the file
            source_code = sample_file.read_text(encoding='utf-8')
            tree = ast.parse(source_code)
            
            # Find a function call in the AST
            class CallFinder(ast.NodeVisitor):
                def __init__(self):
                    self.calls_found = []
                
                def visit_Call(self, node):
                    try:
                        # Try to extract name parts like the analysis does
                        if isinstance(node.func, ast.Name):
                            self.calls_found.append([node.func.id])
                        elif isinstance(node.func, ast.Attribute):
                            # Simple attribute access
                            if isinstance(node.func.value, ast.Name):
                                self.calls_found.append([node.func.value.id, node.func.attr])
                    except:
                        pass
                    self.generic_visit(node)
            
            finder = CallFinder()
            finder.visit(tree)
            
            print(f"   Found {len(finder.calls_found)} calls in AST:")
            for i, call in enumerate(finder.calls_found[:5]):  # Show first 5
                print(f"     {i+1}. {'.'.join(call)}")
            
            if finder.calls_found:
                # Test resolving the first call
                test_call = finder.calls_found[0]
                print(f"\n   Testing resolution of: {'.'.join(test_call)}")
                
                # Test with both resolvers
                orig_result = original_resolver.resolve_name(test_call, context)
                refact_result = refactored_resolver.resolve_name(test_call, context)
                
                print(f"   Original: {orig_result}")
                print(f"   Refactored: {refact_result}")
                print(f"   Match: {orig_result == refact_result}")
        
        except Exception as e:
            print(f"   ❌ File analysis error: {e}")
    
    # Step 4: Check if the analysis visitor is actually calling the resolver
    print("\n4. Testing analysis visitor integration...")
    try:
        from analyzer.visitors.analysis_refactored import RefactoredAnalysisVisitor
        
        # Create a minimal test
        simple_code = '''
def test_function():
    result = some_call()
    return result
'''
        
        tree = ast.parse(simple_code)
        visitor = RefactoredAnalysisVisitor(mock_recon_data, "test_module")
        
        print(f"   Visitor resolver type: {type(visitor.name_resolver).__name__}")
        print(f"   Visitor resolver implementation: {visitor.name_resolver.implementation_name}")
        
        # Visit the tree
        visitor.visit(tree)
        
        # Check what we found
        if visitor.module_report["functions"]:
            func_report = visitor.module_report["functions"][0]
            print(f"   Function found: {func_report['name']}")
            print(f"   Calls found: {len(func_report['calls'])}")
            print(f"   Instantiations: {len(func_report['instantiations'])}")
            print(f"   Accessed state: {len(func_report['accessed_state'])}")
        else:
            print("   No functions found in report")
        
    except Exception as e:
        print(f"   ❌ Analysis visitor error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_call_resolution()
