"""
Test module for constructor resolution validation.

Place this file in sample_files/ to test constructor type inference.
"""

# Import a sample class from the project
from sample_files.models.user import User

# Test 1: Custom class constructor
user_instance = User()

# Test 2: Builtin constructors
empty_list = list()
empty_dict = dict()
empty_set = set()
new_string = str()
zero = int()

# Test 3: Constructor with immediate method call (chaining)
# user_name = User().get_name()  # If User has get_name() method

# Test 4: Constructor with attribute access
# user_email = User().email  # If User has email attribute

# Test 5: More complex builtin usage
numbers = list([1, 2, 3])
mapping = dict({"key": "value"})

# Test 6: Class stored in variable (advanced case)
UserClass = User
user_from_var = UserClass()

print("Constructor test module loaded successfully")
print("Run Atlas analysis to validate type inference:")
print("  project = build_complete_atlas('sample_files')")
print("  project.analyze()")
print("  # Then inspect the inferred types for variables in this module")