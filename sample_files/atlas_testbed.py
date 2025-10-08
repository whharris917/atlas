"""
Analysis Phase Test Bed - Module-Level Assignments

This module serves as the primary test bed for the Analysis Phase, focusing
on module-level variable assignments that use classes and functions from the
sample_files project. This is the file we'll use to develop and debug the
ModuleAnalysisVisitor.

The goal is to exemplify all the kinds of assignments and patterns we want
the Analysis Phase to detect and create TypeNotes for.
"""

import sys
from decimal import Decimal
from typing import List, Dict, Optional

# Import entities from sample_files to use in assignments
from models.user import User, UserProfile
from models.product import Product, ProductCategory
from models.order import Order, OrderItem
from services.auth_service import AuthService, TokenManager
from services.email_service import EmailService
from services.payment_service import PaymentService
from core.exceptions import ValidationError
from core.utils import format_timestamp, calculate_hash

# =============================================================================
# SECTION 1: SIMPLE ANNOTATED ASSIGNMENTS - Should use annotation
# =============================================================================

VERSION: str = "1.0.0"
MAX_CONNECTIONS: int = 100
DEBUG_ENABLED: bool = False
TIMEOUT_SECONDS: float = 30.5

# =============================================================================
# SECTION 2: SIMPLE NON-ANNOTATED ASSIGNMENTS - Should infer from literal
# =============================================================================

author = "Atlas Analysis Phase"
default_port = 8080
is_production = True
retry_delay = 1.5

# =============================================================================
# SECTION 3: COLLECTION LITERALS - Should infer collection types
# =============================================================================

error_codes = [400, 401, 403, 404, 500]
default_headers = {"Content-Type": "application/json", "Accept": "*/*"}
allowed_methods = {"GET", "POST", "PUT", "DELETE"}
coordinate = (10.5, 20.3)

# =============================================================================
# SECTION 4: SIMPLE CLASS INSTANTIATIONS - Core instances for later use
# =============================================================================

# Service instantiations with literals
token_manager = TokenManager("secret_key_123", 24)
email_service = EmailService("smtp.example.com", 587, "admin@test.com", "password")
payment_service = PaymentService(None)

# User instantiations with literals
admin_user = User("admin_001", "admin@example.com", "admin", "password123")
premium_user = User("user_002", "user@example.com", "testuser", "securepass")

# Product instantiation with Decimal
product = Product("prod_001", "Laptop", Decimal("1299.99"), "Electronics")

# =============================================================================
# SECTION 5: MULTI-TARGET ASSIGNMENTS - Tests StateContainerNode
# =============================================================================

x = y = z = 42
first_name = last_name = "Unknown"

# =============================================================================
# SECTION 6: CONDITIONAL ASSIGNMENTS - Variables defined in branches
# =============================================================================

if sys.platform == "win32":
    path_sep = "\\"
    line_ending = "\r\n"
else:
    path_sep = "/"
    line_ending = "\n"

# Annotated conditional
if DEBUG_ENABLED:
    log_level: str = "DEBUG"
    log_file: str = "debug.log"
else:
    log_level: str = "INFO"
    log_file: str = "app.log"

# =============================================================================
# SECTION 7: NESTED CONDITIONALS - Multiple levels
# =============================================================================

if is_production:
    cache_enabled = True
    if MAX_CONNECTIONS > 50:
        use_connection_pool = True
        pool_size = MAX_CONNECTIONS
    else:
        use_connection_pool = False
        pool_size = 10
else:
    cache_enabled = False

# =============================================================================
# SECTION 8: TRY-EXCEPT ASSIGNMENTS - Error handling patterns
# =============================================================================

try:
    import json
    json_available = True
    json_encoder = json.JSONEncoder
except ImportError:
    json_available = False
    json_encoder = None

# =============================================================================
# SECTION 9: ANNOTATED WITH COMPLEX TYPES - Should use annotation
# =============================================================================

user_cache: Dict[str, User] = {}
pending_orders: List[Order] = []
optional_service: Optional[EmailService] = None

# =============================================================================
# SECTION 10: COMPLEX EXPRESSIONS - Attribute access on objects
# =============================================================================

# Simple attribute access
user_email = admin_user.email
user_username = admin_user.username
product_name = product.name
product_price = product.price

# Attribute access on modules
platform_name = sys.platform
version_info = sys.version_info

# =============================================================================
# SECTION 11: COMPLEX EXPRESSIONS - Method calls (simple)
# =============================================================================

# String methods
upper_author = author.upper()
stripped_version = VERSION.strip()
lower_email = user_email.lower()

# Collection methods
error_list_copy = error_codes.copy()
header_keys = list(default_headers.keys())

# =============================================================================
# SECTION 12: COMPLEX EXPRESSIONS - Chained method calls
# =============================================================================

normalized_email = admin_user.email.lower().strip()
formatted_name = author.replace("Atlas", "ATLAS").upper()
processed_version = VERSION.strip().lower().replace(".", "_")

# =============================================================================
# SECTION 13: COMPLEX EXPRESSIONS - Method calls returning objects
# =============================================================================

# Dictionary methods
default_value = default_headers.get("Accept")
content_type = default_headers.get("Content-Type", "text/plain")

# String methods with indexing
email_domain = admin_user.email.split("@")[1]

# User methods (from User class)
user_validation = admin_user.validate()  # Returns bool
profile_data = admin_user.get_profile()  # Returns dict

# =============================================================================
# SECTION 14: COMPLEX EXPRESSIONS - Service method calls
# =============================================================================

# TokenManager methods
authenticated_user = token_manager.generate_token("user_001")
decoded_token = token_manager.verify_token(authenticated_user)

# EmailService methods
email_result = email_service.send_email("test@test.com", "Subject", "Body", None)

# PaymentService methods
validation_result = payment_service.validate_payment_method({"type": "credit_card"})

# =============================================================================
# SECTION 15: COMPLEX EXPRESSIONS - Chained object method calls
# =============================================================================

payment_status = payment_service.get_processor().get_provider_name()
user_profile_name = admin_user.get_profile().get("name", "Unknown")

# =============================================================================
# SECTION 16: COMPLEX EXPRESSIONS - Imported function calls
# =============================================================================

formatted_time = format_timestamp(None)
data_hash = calculate_hash("some data")

# =============================================================================
# SECTION 17: COMPLEX EXPRESSIONS - Built-in function calls
# =============================================================================

computed_max = max(100, 200)
string_length = len(author)
rounded_value = round(3.14159, 2)
max_of_errors = max(error_codes) if error_codes else 0
sum_of_coords = sum(coordinate)

# =============================================================================
# SECTION 18: COMPLEX EXPRESSIONS - Ternary expressions
# =============================================================================

status_message = admin_user.validate() if admin_user else "No user"
safe_email = admin_user.email.lower() if admin_user and admin_user.email else "no-email"
optional_port = default_port if is_production else 3000

# =============================================================================
# SECTION 19: COMPLEX EXPRESSIONS - Collection access
# =============================================================================

first_error = error_codes[0] if error_codes else None
last_error = error_codes[-1] if error_codes else None
content_type_header = default_headers["Content-Type"]
optional_header = default_headers.get("Authorization", "Bearer none")
path_element = sys.path[0]

# =============================================================================
# SECTION 20: CLASS INSTANTIATIONS WITH COMPLEX ARGUMENTS
# =============================================================================

# Instantiation with string concatenation
backup_user = User("backup_001", admin_user.email.replace("admin", "backup"), 
                   "backup", "password")

# Instantiation with attribute access
cloned_product = Product("prod_002", product.name + " Clone", 
                        product.price, product.category)

# Instantiation with method call result
order_with_item = Order("order_001", admin_user.id, "2024-01-01")

# Chained instantiation and method call
configured_service = AuthService(TokenManager("key", 48)).authenticate("user", "pass")

# =============================================================================
# SECTION 21: COMPLEX EXPRESSIONS - Comprehensions
# =============================================================================

# List comprehension
user_emails = [user.email for user in [admin_user, premium_user, backup_user] if user]
squared_numbers = [x * x for x in range(5)]

# Dict comprehension
error_map = {code: str(code) for code in error_codes}
user_map = {user.id: user.username for user in [admin_user, premium_user]}

# =============================================================================
# SECTION 22: TYPE EVOLUTION - Same variable assigned different types
# =============================================================================

counter = 0
# Later reassigned to different type
counter = "reset"

# =============================================================================
# SECTION 23: AUGMENTED ASSIGNMENTS - Should be treated as assignment
# =============================================================================

total = 0
total += 100
total += 50

# =============================================================================
# SECTION 24: WALRUS OPERATOR - Python 3.8+
# =============================================================================

if (threshold := 100) > 50:
    max_threshold = threshold

# =============================================================================
# EXPECTED OUTCOMES FOR TESTING
# =============================================================================
# 
# PHASE 1 - Simple inference (Steps 6-9):
# ========================================
# The ModuleAnalysisVisitor should create TypeNotes for:
# 1. All simple annotated assignments (use annotation directly)
#    - VERSION, MAX_CONNECTIONS, DEBUG_ENABLED, TIMEOUT_SECONDS
# 2. All simple literal assignments (infer int/str/bool/float)
#    - author, default_port, is_production, retry_delay
# 3. Collection literals (infer list/dict/set/tuple)
#    - error_codes, default_headers, allowed_methods, coordinate
# 4. Multi-target assignments (all targets get same type)
#    - x, y, z all get int from 42
# 5. Conditional branches (track variables in each branch)
#    - path_sep, line_ending, log_level, log_file
#
# PHASE 2 - Class instantiation inference (Later):
# =================================================
# 6. Simple class instantiations with literal args
#    - token_manager → TokenManager
#    - admin_user → User
#    - product → Product
#
# PHASE 3 - Complex expression inference (Much later):
# =====================================================
# 7. Simple attribute access
#    - user_email = admin_user.email → str
#    - product_name = product.name → str
# 8. Simple method calls
#    - upper_author = author.upper() → str
#    - user_validation = admin_user.validate() → bool
# 9. Chained method calls
#    - normalized_email = admin_user.email.lower().strip() → str
# 10. Function calls with known return types
#     - computed_max = max(100, 200) → int
# 11. Chained object method calls
#     - payment_status = payment_service.get_processor().get_provider_name() → str
# 12. Complex instantiations with expression arguments
#     - backup_user = User(..., admin_user.email.replace(...), ...) → User
#
# This gives us a clear progression from simple to complex patterns.