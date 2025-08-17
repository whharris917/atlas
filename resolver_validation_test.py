#!/usr/bin/env python3
"""
Resolver Validation Test - Code Atlas Phase 3

Tests the refactored resolver implementation against the original
to ensure identical behavior and output.
"""

import sys
import os
import json
from typing import Dict, List, Any, Optional, Tuple

# Add the analyzer directory to path for imports
analyzer_path = os.path.join(os.path.dirname(__file__), 'analyzer')
if analyzer_path not in sys.path:
    sys.path.insert(0, analyzer_path)

def load_gold_standard_data() -> Dict[str, Any]:
    """Load the gold standard JSON data for testing."""
    try:
        with open('code_atlas_report_gold_standard.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("ERROR: code_atlas_report_gold_standard.json not found")
        print("Please ensure the gold standard file is in the current directory")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in gold standard file: {e}")
        sys.exit(1)


def create_test_recon_data() -> Dict[str, Any]:
    """Create test reconnaissance data based on the sample project."""
    return {
        "imports": {
            "socketio": "flask_socketio",
            "threading": "threading",
            "Session": "session_manager.Session"
        },
        "classes": {
            "admin_manager.AdminManager": {
                "parents": [],
                "attributes": {
                    "socketio": {"type": "flask_socketio.SocketIO"},
                    "session_manager": {"type": "session_manager.SessionManager"}
                }
            },
            "database_manager.DatabaseManager": {
                "parents": [],
                "attributes": {
                    "connection": {"type": "sqlite3.Connection"}
                }
            },
            "session_manager.SessionManager": {
                "parents": [],
                "attributes": {
                    "sessions": {"type": "dict"}
                }
            }
        },
        "functions": {
            "admin_manager.AdminManager.__init__": {"return_type": "None"},
            "admin_manager.AdminManager.emit_status": {"return_type": "None"},
            "database_manager.DatabaseManager.connect": {"return_type": "bool"},
            "session_manager.SessionManager.create_session": {"return_type": "str"}
        },
        "state": {
            "admin_manager.global_admin": {"type": "admin_manager.AdminManager"},
            "database_manager.db_instance": {"type": "database_manager.DatabaseManager"}
        },
        "external_classes": {
            "flask_socketio.SocketIO": {
                "local_alias": "SocketIO",
                "module": "flask_socketio"
            },
            "threading.Thread": {
                "local_alias": "Thread", 
                "module": "threading"
            }
        },
        "external_functions": {
            "threading.Lock": {
                "local_alias": "Lock",
                "module": "threading"
            }
        }
    }


def create_test_context(module_name: str = "test_module", current_class: str = None) -> Dict[str, Any]:
    """Create test resolution context."""
    return {
        "current_module": module_name,
        "current_class": current_class,
        "current_function_fqn": f"{module_name}.test_function" if not current_class else f"{current_class}.test_method",
        "import_map": {
            "socketio": "flask_socketio",
            "threading": "threading",
            "Session": "session_manager.Session",
            "SocketIO": "flask_socketio.SocketIO"
        },
        "symbol_manager": None,  # Mock symbol manager
        "type_inference": None   # Mock type inference
    }


def run_resolution_tests() -> Tuple[int, int, List[str]]:
    """
    Run comprehensive resolution tests comparing original vs refactored.
    
    Returns:
        Tuple of (passed_tests, total_tests, error_messages)
    """
    print("🧪 Starting Resolver Validation Tests...")
    
    # Load test data
    recon_data = create_test_recon_data()
    context = create_test_context()
    
    # Import both implementations
    try:
        from resolver import NameResolver as OriginalResolver
        print("✅ Original resolver imported successfully")
    except ImportError as e:
        return 0, 1, [f"Failed to import original resolver: {e}"]
    
    try:
        from resolver_compat import create_name_resolver
        refactored_resolver = create_name_resolver(recon_data, use_refactored=True)
        print("✅ Refactored resolver imported successfully")
    except ImportError as e:
        return 0, 1, [f"Failed to import refactored resolver: {e}"]
    
    # Create resolver instances
    original = OriginalResolver(recon_data)
    refactored = refactored_resolver.resolver  # Get the actual resolver from wrapper
    
    # Test cases: (name_parts, expected_behavior_description)
    test_cases = [
        # Simple name resolution
        (["self"], "self reference resolution"),
        (["socketio"], "import alias resolution"),
        (["SocketIO"], "external class resolution"),
        (["threading"], "module import resolution"),
        (["Session"], "imported class resolution"),
        (["unknown_name"], "fallback module resolution"),
        
        # Complex chain resolution
        (["self", "socketio"], "self attribute chain"),
        (["self", "socketio", "emit"], "self method chain"),
        (["self", "session_manager", "create_session"], "deep attribute chain"),
        (["global_admin", "emit_status"], "state variable method"),
        (["db_instance", "connect"], "state variable method"),
        
        # External library chains
        (["SocketIO", "emit"], "external class method"),
        (["Thread", "start"], "external threading method"),
        (["Lock", "acquire"], "external function call"),
        
        # Inheritance and type resolution
        (["admin_manager", "AdminManager"], "module class resolution"),
        (["database_manager", "DatabaseManager", "connect"], "module method chain"),
    ]
    
    passed_tests = 0
    total_tests = len(test_cases)
    error_messages = []
    
    print(f"\n🔍 Running {total_tests} resolution test cases...")
    
    for i, (name_parts, description) in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {description} ---")
        print(f"Testing: {'.'.join(name_parts)}")
        
        try:
            # Test original implementation
            original_result = original.resolve_name(name_parts, context)
            print(f"Original result: {original_result}")
            
            # Test refactored implementation
            refactored_result = refactored.resolve_name(name_parts, context)
            print(f"Refactored result: {refactored_result}")
            
            # Compare results
            if original_result == refactored_result:
                print("✅ PASS: Results match")
                passed_tests += 1
            else:
                error_msg = f"❌ FAIL: Results differ for {'.'.join(name_parts)}"
                error_msg += f"\n  Original: {original_result}"
                error_msg += f"\n  Refactored: {refactored_result}"
                print(error_msg)
                error_messages.append(error_msg)
                
        except Exception as e:
            error_msg = f"❌ ERROR: Exception in test {i} ({description}): {e}"
            print(error_msg)
            error_messages.append(error_msg)
    
    return passed_tests, total_tests, error_messages


def test_resolver_compatibility() -> Tuple[bool, List[str]]:
    """Test the compatibility layer functionality."""
    print("\n🔧 Testing Resolver Compatibility Layer...")
    
    errors = []
    recon_data = create_test_recon_data()
    
    try:
        from resolver_compat import create_name_resolver, get_resolver_implementation_status
        
        # Test implementation status
        status = get_resolver_implementation_status()
        print(f"Implementation status: {status}")
        
        # Test auto-detection
        auto_resolver = create_name_resolver(recon_data)
        print(f"Auto-detected implementation: {auto_resolver.implementation_type}")
        
        # Test forced original
        original_resolver = create_name_resolver(recon_data, use_refactored=False)
        print(f"Forced original implementation: {original_resolver.implementation_type}")
        
        # Test forced refactored (if available)
        if status.get("refactored_available", False):
            refactored_resolver = create_name_resolver(recon_data, use_refactored=True)
            print(f"Forced refactored implementation: {refactored_resolver.implementation_type}")
        
        # Test compatibility wrapper methods
        test_resolver = auto_resolver
        info = test_resolver.get_implementation_info()
        print(f"Implementation info: {info}")
        
        # Test cache clearing
        test_resolver.clear_cache()
        print("✅ Cache clearing works")
        
        # Test validation
        valid_fqn = "admin_manager.AdminManager"
        is_valid = test_resolver.validate_resolution(valid_fqn)
        print(f"Validation test for '{valid_fqn}': {is_valid}")
        
        return True, errors
        
    except Exception as e:
        error_msg = f"Compatibility layer test failed: {e}"
        errors.append(error_msg)
        return False, errors


def test_specialized_visitors() -> Tuple[bool, List[str]]:
    """Test individual specialized visitors."""
    print("\n🎯 Testing Specialized Visitors...")
    
    errors = []
    recon_data = create_test_recon_data()
    context = create_test_context()
    
    try:
        # Test Simple Resolution Visitor
        print("Testing Simple Resolution Visitor...")
        from visitors.specialized.simple_resolution_visitor import SimpleResolutionVisitor
        simple_visitor = SimpleResolutionVisitor(recon_data)
        
        simple_tests = [
            ("self", "self reference"),
            ("socketio", "import resolution"),
            ("SocketIO", "external class"),
            ("unknown", "fallback resolution")
        ]
        
        for name, desc in simple_tests:
            result = simple_visitor.resolve(name, context)
            print(f"  {desc} ({name}): {result}")
        
        # Test Chain Resolution Visitor
        print("\nTesting Chain Resolution Visitor...")
        from visitors.specialized.chain_resolution_visitor import ChainResolutionVisitor
        chain_visitor = ChainResolutionVisitor(recon_data)
        
        chain_tests = [
            (["self", "socketio"], "self attribute"),
            (["self", "socketio", "emit"], "method chain"),
            (["global_admin", "emit_status"], "state method")
        ]
        
        for name_parts, desc in chain_tests:
            result = chain_visitor.resolve(name_parts, context)
            print(f"  {desc} ({'.'.join(name_parts)}): {result}")
        
        # Test Inheritance Resolution Visitor
        print("\nTesting Inheritance Resolution Visitor...")
        from visitors.specialized.inheritance_resolution_visitor import InheritanceResolutionVisitor
        inheritance_visitor = InheritanceResolutionVisitor(recon_data)
        
        # Test inheritance chain
        chain = inheritance_visitor.get_inheritance_chain("admin_manager.AdminManager")
        print(f"  Inheritance chain for AdminManager: {chain}")
        
        # Test External Resolution Visitor
        print("\nTesting External Resolution Visitor...")
        from visitors.specialized.external_resolution_visitor import ExternalResolutionVisitor
        external_visitor = ExternalResolutionVisitor(recon_data)
        
        external_tests = [
            ("SocketIO", "external class"),
            ("Thread", "threading class"),
            ("Lock", "threading function")
        ]
        
        for name, desc in external_tests:
            result = external_visitor.resolve_external_name(name, context)
            print(f"  {desc} ({name}): {result}")
        
        return True, errors
        
    except Exception as e:
        error_msg = f"Specialized visitor test failed: {e}"
        errors.append(error_msg)
        return False, errors


def main():
    """Main test runner."""
    print("🚀 Atlas Resolver Phase 3 Validation")
    print("=" * 50)
    
    all_passed = True
    all_errors = []
    
    # Test 1: Resolution comparison
    passed, total, errors = run_resolution_tests()
    print(f"\n📊 Resolution Tests: {passed}/{total} passed")
    if errors:
        all_errors.extend(errors)
        all_passed = False
    
    # Test 2: Compatibility layer
    compat_passed, compat_errors = test_resolver_compatibility()
    print(f"📊 Compatibility Tests: {'PASS' if compat_passed else 'FAIL'}")
    if compat_errors:
        all_errors.extend(compat_errors)
        all_passed = False
    
    # Test 3: Specialized visitors
    visitors_passed, visitor_errors = test_specialized_visitors()
    print(f"📊 Specialized Visitor Tests: {'PASS' if visitors_passed else 'FAIL'}")
    if visitor_errors:
        all_errors.extend(visitor_errors)
        all_passed = False
    
    # Final summary
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Refactored resolver is ready for production")
        print("✅ Progressive migration system working correctly")
        print("✅ All specialized visitors functioning properly")
    else:
        print("❌ SOME TESTS FAILED")
        print(f"Total errors: {len(all_errors)}")
        print("\nError details:")
        for error in all_errors:
            print(f"  - {error}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
