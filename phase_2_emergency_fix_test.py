#!/usr/bin/env python3
"""
Phase 2 Emergency Fix Test - Code Atlas

Test script to validate that the reconnaissance data extraction fixes work correctly.
This script tests the specific enum extraction and class attribute cases that were broken.
"""

import ast
import sys
import pathlib
from typing import Dict, Any

# Add the current directory to the path so we can import the Atlas modules
sys.path.insert(0, str(pathlib.Path(__file__).parent))

def test_enum_extraction():
    """Test enum value extraction specifically."""
    print("=== Testing Enum Extraction ===")
    
    # Sample enum code similar to admin_manager.py
    enum_code = '''
from enum import Enum, auto

class OperationType(Enum):
    """Types of administrative operations."""
    USER_MANAGEMENT = auto()
    SYSTEM_CONFIGURATION = auto()
    DATA_MIGRATION = auto()
    SECURITY_AUDIT = auto()
    PERFORMANCE_TUNING = auto()
    BACKUP_RESTORE = auto()
    MONITORING_SETUP = auto()
'''
    
    # Parse and test with fixed visitors
    tree = ast.parse(enum_code)
    
    # Import the fixed visitors
    try:
        from analyzer.visitors.specialized.class_recon_visitor import ClassReconVisitor
        from analyzer.visitors.specialized.state_recon_visitor import StateReconVisitor
        from analyzer.utils.logger import get_logger
        from analyzer.type_inference import TypeInferenceEngine
        
        logger = get_logger()
        class_visitor = ClassReconVisitor("test_module", logger)
        type_inference = TypeInferenceEngine({})
        state_visitor = StateReconVisitor("test_module", logger, type_inference)
        
        print("✅ Successfully imported fixed visitors")
        
        # Find the class definition
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "OperationType":
                print(f"Found class: {node.name}")
                
                # Process class structure
                class_info = class_visitor.process_class_def(node)
                print(f"Class info: {class_info}")
                
                # Set context
                class_fqn = class_info["fqn"]
                state_visitor.set_class_context(class_fqn)
                class_visitor.enter_class_context(class_fqn)
                
                # Process class body elements
                enum_values_found = 0
                for child in node.body:
                    if isinstance(child, ast.Assign):
                        print(f"Processing assignment: {ast.unparse(child)}")
                        
                        def class_attr_callback(name: str, info: Dict[str, Any]):
                            class_visitor.add_class_attribute(name, info)
                            nonlocal enum_values_found
                            enum_values_found += 1
                            print(f"  Added attribute: {name} = {info}")
                        
                        state_visitor.process_assign(child, class_attr_callback)
                
                # Exit context
                class_visitor.exit_class_context()
                
                # Check results
                final_classes = class_visitor.get_classes_data()
                enum_class = next((c for c in final_classes if "OperationType" in c["fqn"]), None)
                
                if enum_class:
                    print(f"Final enum class: {enum_class}")
                    attributes = enum_class.get("attributes", {})
                    print(f"Found {len(attributes)} attributes: {list(attributes.keys())}")
                    
                    expected_values = ['USER_MANAGEMENT', 'SYSTEM_CONFIGURATION', 'DATA_MIGRATION', 
                                     'SECURITY_AUDIT', 'PERFORMANCE_TUNING', 'BACKUP_RESTORE', 'MONITORING_SETUP']
                    
                    missing = [v for v in expected_values if v not in attributes]
                    if missing:
                        print(f"❌ MISSING ENUM VALUES: {missing}")
                        return False
                    else:
                        print("✅ All enum values found!")
                        return True
                else:
                    print("❌ Enum class not found in results")
                    return False
                
        print("❌ OperationType class not found in AST")
        return False
        
    except Exception as e:
        print(f"❌ Error during enum test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_module_state_extraction():
    """Test module-level state variable extraction."""
    print("\n=== Testing Module State Extraction ===")
    
    # Sample module state code
    state_code = '''
from typing import Dict, Any
import threading

# Module-level state variables
operations_history: Dict[str, Any] = {}
active_operations = set()
operation_lock = threading.RLock()
system_config = {"debug": True}
'''
    
    tree = ast.parse(state_code)
    
    try:
        from analyzer.visitors.specialized.state_recon_visitor import StateReconVisitor
        from analyzer.utils.logger import get_logger
        from analyzer.type_inference import TypeInferenceEngine
        
        logger = get_logger()
        type_inference = TypeInferenceEngine({})
        state_visitor = StateReconVisitor("test_module", logger, type_inference)
        
        # No class context for module-level state
        state_visitor.set_class_context(None)
        
        variables_found = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                print(f"Processing assignment: {ast.unparse(node)}")
                result = state_visitor.process_assign(node)
                variables_found += len(result)
                print(f"  Result: {result}")
            elif isinstance(node, ast.AnnAssign):
                print(f"Processing annotated assignment: {ast.unparse(node)}")
                result = state_visitor.process_ann_assign(node)
                variables_found += len(result)
                print(f"  Result: {result}")
        
        # Check final state
        final_state = state_visitor.get_state_data()
        print(f"Final state data: {final_state}")
        print(f"Found {len(final_state)} state variables")
        
        expected_vars = ['operations_history', 'active_operations', 'operation_lock', 'system_config']
        missing = [v for v in expected_vars if not any(v in key for key in final_state.keys())]
        
        if missing:
            print(f"❌ MISSING STATE VARIABLES: {missing}")
            return False
        else:
            print("✅ All state variables found!")
            return True
            
    except Exception as e:
        print(f"❌ Error during state test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_init_attribute_extraction():
    """Test __init__ method attribute extraction."""
    print("\n=== Testing __init__ Attribute Extraction ===")
    
    # Sample class with __init__ method
    init_code = '''
from typing import Dict, Set
import threading

class AdminManager:
    def __init__(self):
        self.operations_history: Dict[str, Any] = {}
        self.active_operations: Set[str] = set()
        self.operation_lock = threading.RLock()
        self.admin_permissions = {}
        self.system_config = {}
        self.audit_log = []
'''
    
    tree = ast.parse(init_code)
    
    try:
        from analyzer.visitors.specialized.function_recon_visitor import FunctionReconVisitor
        from analyzer.utils.logger import get_logger
        from analyzer.type_inference import TypeInferenceEngine
        
        logger = get_logger()
        type_inference = TypeInferenceEngine({})
        function_visitor = FunctionReconVisitor("test_module", logger)
        
        # Find the class and __init__ method
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "AdminManager":
                print(f"Found class: {node.name}")
                
                # Set class context
                class_fqn = f"test_module.{node.name}"
                function_visitor.set_class_context(class_fqn)
                
                # Find __init__ method
                for child in node.body:
                    if isinstance(child, ast.FunctionDef) and child.name == "__init__":
                        print(f"Found __init__ method")
                        
                        # Extract attributes
                        attributes = function_visitor.extract_init_attributes(child, type_inference)
                        print(f"Extracted attributes: {attributes}")
                        
                        expected_attrs = ['operations_history', 'active_operations', 'operation_lock', 
                                        'admin_permissions', 'system_config', 'audit_log']
                        
                        missing = [a for a in expected_attrs if a not in attributes]
                        if missing:
                            print(f"❌ MISSING INIT ATTRIBUTES: {missing}")
                            return False
                        else:
                            print("✅ All __init__ attributes found!")
                            return True
                
        print("❌ __init__ method not found")
        return False
        
    except Exception as e:
        print(f"❌ Error during __init__ test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all emergency fix tests."""
    print("🚨 Phase 2 Emergency Fix Tests 🚨")
    print("=" * 50)
    
    tests = [
        ("Enum Extraction", test_enum_extraction),
        ("Module State Extraction", test_module_state_extraction),
        ("__init__ Attribute Extraction", test_init_attribute_extraction)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running test: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\nTests passed: {passed}/{len(results)}")
    
    if passed == len(results):
        print("🎉 ALL TESTS PASSED! Emergency fixes successful!")
        return True
    else:
        print("🚨 SOME TESTS FAILED! Need further debugging.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
