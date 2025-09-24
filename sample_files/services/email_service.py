"""
Email Service - Fully Typed Test

Complete type coverage for testing Atlas precision.
Should generate zero type hint violations.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class EmailPriority(Enum):
    """Email priority enumeration."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class EmailTemplate:
    """Email template with full type coverage."""
    
    def __init__(self, 
                 template_id: str, 
                 subject: str, 
                 body: str, 
                 variables: Optional[List[str]] = None) -> None:
        """Fully typed constructor."""
        self.template_id = template_id
        self.subject = subject
        self.body = body
        self.variables = variables or []
        self.created_at = datetime.now()
    
    def render(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Fully typed template rendering."""
        rendered_subject = self.subject
        rendered_body = self.body
        
        for variable in self.variables:
            if variable in context:
                placeholder = f"{{{variable}}}"
                value = str(context[variable])
                rendered_subject = rendered_subject.replace(placeholder, value)
                rendered_body = rendered_body.replace(placeholder, value)
        
        return {
            'subject': rendered_subject,
            'body': rendered_body
        }
    
    def get_required_variables(self) -> List[str]:
        """Fully typed getter."""
        return self.variables.copy()
    
    def validate_context(self, context: Dict[str, Any]) -> bool:
        """Fully typed validation."""
        return all(var in context for var in self.variables)


class EmailService:
    """Email service with complete type annotations."""
    
    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str) -> None:
        """Fully typed constructor."""
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.templates: Dict[str, EmailTemplate] = {}
        self.sent_emails: List[Dict[str, Any]] = []
    
    def add_template(self, template: EmailTemplate) -> None:
        """Fully typed template registration."""
        self.templates[template.template_id] = template
    
    def get_template(self, template_id: str) -> Optional[EmailTemplate]:
        """Fully typed template getter."""
        return self.templates.get(template_id)
    
    def send_email(self, 
                   to_addresses: List[str], 
                   subject: str, 
                   body: str,
                   priority: EmailPriority = EmailPriority.NORMAL,
                   attachments: Optional[List[str]] = None) -> bool:
        """Fully typed email sending."""
        email_record = {
            'to': to_addresses,
            'subject': subject,
            'body': body,
            'priority': priority.value,
            'attachments': attachments or [],
            'sent_at': datetime.now(),
            'status': 'sent'
        }
        
        self.sent_emails.append(email_record)
        return True
    
    def send_template_email(self, 
                           template_id: str, 
                           to_addresses: List[str],
                           context: Dict[str, Any],
                           priority: EmailPriority = EmailPriority.NORMAL) -> bool:
        """Fully typed template email sending."""
        template = self.get_template(template_id)
        if not template:
            return False
        
        if not template.validate_context(context):
            return False
        
        rendered = template.render(context)
        return self.send_email(
            to_addresses, 
            rendered['subject'], 
            rendered['body'], 
            priority
        )
    
    def get_sent_count(self) -> int:
        """Fully typed statistics."""
        return len(self.sent_emails)
    
    def get_sent_emails_by_priority(self, priority: EmailPriority) -> List[Dict[str, Any]]:
        """Fully typed filtering."""
        return [
            email for email in self.sent_emails 
            if email['priority'] == priority.value
        ]
