"""Core error classes and exception handling for the AgenticAI application.

This module provides standardized error handling with structured error responses,
HTTP status codes, and detailed error information for API consumers.
"""
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import ErrorCode


class AppError(Exception):
    """Base application error with structured error information.
    
    Provides a standardized way to handle application errors with
    error codes, HTTP status codes, and optional detailed error data.
    
    Args:
        message (str): Human-readable error message
        code (ErrorCode, optional): Application error code. Defaults to internal_error.
        status_code (int, optional): HTTP status code. Defaults to 500.
        extra (dict, optional): Additional error context data
        errors (list[ApiErrorItem], optional): List of detailed error items
        
    Example:
        >>> raise AppError(
        ...     "User not found",
        ...     code=ErrorCode.not_found,
        ...     status_code=404
        ... )
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.internal_error,
        status_code: int = 500,
        extra: dict[str, Any] | None = None,
        errors: list["ApiErrorItem"] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.extra = extra or {}
        self.errors = errors


class NotFoundError(AppError):
    """Specialized error for resource not found scenarios.
    
    Convenience class that automatically sets the error code to NOT_FOUND
    and HTTP status to 404.
    
    Args:
        message (str, optional): Error message. Defaults to "Resource not found".
        extra (dict, optional): Additional error context data
        errors (list[ApiErrorItem], optional): List of detailed error items
        
    Example:
        >>> raise NotFoundError("Thread with ID 123 not found")
    """
    def __init__(
        self,
        message: str = "Resource not found",
        extra: dict[str, Any] | None = None,
        errors: list["ApiErrorItem"] | None = None,
    ) -> None:
        super().__init__(
            message,
            code=ErrorCode.not_found,
            status_code=404,
            extra=extra,
            errors=errors,
        )


class ApiErrorBody(BaseModel):
    """Standardized API error response body structure.
    
    Provides a consistent format for all API error responses,
    ensuring clients can reliably parse error information.
    
    Attributes:
        code (str): Error code identifier
        message (str): Human-readable error message
        details (dict, optional): Additional error context
        errors (list[ApiErrorItem], optional): Detailed error list
    """
    code: str
    message: str
    details: dict[str, Any] | None = None
    # Optional list of structured errors, using consumer-facing aliases.
    errors: list["ApiErrorItem"] | None = None


class ApiErrorItem(BaseModel):
    """Individual error item with detailed field-level information.
    
    Represents a single error with specific field context, typically used
    for validation errors or detailed error reporting.
    
    The model uses field aliases to match the expected API response format
    while maintaining clean internal field names.
    
    Attributes:
        code (str): Error code (aliased as 'errorcode')
        message (str): Error message (aliased as 'errormessage')
        status (int, optional): HTTP status code (aliased as 'errorStatus')
        field (str, optional): Field that caused the error (aliased as 'errorField')
        
    Example:
        >>> error_item = ApiErrorItem(
        ...     errorcode="VALIDATION_ERROR",
        ...     errormessage="Field is required",
        ...     errorStatus=422,
        ...     errorField="username"
        ... )
    """
    model_config = ConfigDict(populate_by_name=True)
    # Field aliases match requested shape:
    #   errorcode, errormessage, errorStatus, erorFiled (typo preserved as alias)
    code: str = Field(alias="errorcode")
    message: str = Field(alias="errormessage")
    status: int | None = Field(default=None, alias="errorStatus")
    field: str | None = Field(default=None, alias="errorField")
