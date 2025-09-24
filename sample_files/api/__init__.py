"""
API Package - REST Endpoints

Web API layer with mixed type annotation patterns.
"""

from .middleware import AuthMiddleware, LoggingMiddleware
from .endpoints import UserEndpoints, ProductEndpoints
