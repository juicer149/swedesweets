#! src/swedesweets/domain/errors.py
"""
Domain errors.

This module defines the base exception hierarchy for the domain.

Design:
- All domain-specific errors inherit from DomainError
- Keeps domain failures separate from infrastructure/framework errors
- Lets the application layer handle domain failures uniformly
"""


class DomainError(Exception):
    """Base class for all domain-related errors."""


class ValidationError(DomainError):
    """Raised when input data violates structural or type constraints."""


class BusinessRuleError(DomainError):
    """Raised when valid data violates a business rule."""
