"""
Service Tests - Partial Type Coverage

Test functions with mixed type annotation patterns.
"""

from datetime import datetime
from ..services.auth_service import AuthService, TokenManager
from ..services.email_service import EmailService, EmailTemplate
from ..models.user import User


class TestAuthService:
    """Authentication service tests with mixed typing."""
    
    def setup_method(self) -> None:
        """Fully typed setup."""
        self.token_manager = TokenManager("secret_key", 24)
        self.auth_service = AuthService(self.token_manager)
    
    def test_token_generation(self):
        """Missing return type."""
        token = self.token_manager.generate_token("user123")
        assert token is not None
        assert token.startswith("token_user123")
    
    def test_token_validation(self, token):
        """Missing parameter and return types."""
        # Create a fresh token for testing
        test_token = self.token_manager.generate_token("test_user")
        
        # Valid token should pass
        is_valid = self.token_manager.validate_token(test_token)
        assert is_valid
        
        # Invalid token should fail
        invalid_result = self.token_manager.validate_token("invalid_token")
        assert not invalid_result
    
    def test_authentication(self, username: str, password):
        """Partially typed - missing password type."""
        # Test successful authentication
        user = self.auth_service.authenticate("admin", "secret")
        assert user is not None
        assert user.username == "admin"
        
        # Test failed authentication
        failed_user = self.auth_service.authenticate("admin", "wrong_password")
        assert failed_user is None
    
    def test_login_process(self):
        """No type hints."""
        try:
            result = self.auth_service.login("admin", "secret")
            assert 'user' in result
            assert 'token' in result
            assert 'expires_at' in result
        except Exception as e:
            assert False, f"Login should succeed: {e}"
    
    def test_failed_login_attempts(self, username):
        """Missing parameter and return types."""
        # Record multiple failed attempts
        self.auth_service.record_failed_attempt(username)
        self.auth_service.record_failed_attempt(username)
        self.auth_service.record_failed_attempt(username)
        
        # Account should be locked
        locked = self.auth_service.is_account_locked(username)
        assert locked


class TestEmailService:
    """Email service tests with partial type coverage."""
    
    def setup_method(self):
        """Missing return type."""
        self.email_service = EmailService("smtp.test.com", 587, "test@example.com", "password")
        self.template = EmailTemplate(
            "welcome",
            "Welcome {name}!",
            "Hello {name}, welcome to our platform!",
            ["name"]
        )
        self.email_service.add_template(self.template)
    
    def test_template_rendering(self, context):
        """Missing parameter and return types."""
        test_context = {"name": "John Doe"}
        rendered = self.template.render(test_context)
        
        assert rendered['subject'] == "Welcome John Doe!"
        assert "Hello John Doe" in rendered['body']
    
    def test_email_sending(self):
        """No type hints."""
        recipients = ["test1@example.com", "test2@example.com"]
        success = self.email_service.send_email(
            recipients,
            "Test Subject",
            "Test Body"
        )
        assert success
        assert self.email_service.get_sent_count() == 1


def create_test_token_manager(secret: str, hours):
    """Missing parameter and return types."""
    return TokenManager(secret, hours)


def setup_auth_test_data():
    """No type hints."""
    return {
        'username': 'test_user',
        'password': 'test_password',
        'email': 'test@example.com'
    }
