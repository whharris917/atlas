"""
Services Package - Business Logic Layer

Mix of service classes with different type annotation patterns.
"""

from .auth_service import AuthService, TokenManager
from .email_service import EmailService, EmailTemplate
from .payment_service import PaymentService, PaymentProcessor
