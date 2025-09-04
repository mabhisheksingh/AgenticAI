"""Global exception handlers for consistent error responses across the API.

This module implements FastAPI exception handlers that provide standardized
error responses for all types of exceptions, ensuring consistent error formats
for API consumers.
"""
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.status import (
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from app.core.enums import ErrorCode
from app.core.errors import ApiErrorItem, AppError


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers for the FastAPI application.
    
    Implements a "Controller Advice" pattern for centralized exception handling,
    ensuring all errors are formatted consistently across the entire API.
    
    Handlers registered:
    - AppError: Controlled application errors with structured responses
    - RequestValidationError: Pydantic validation errors from request data
    - Exception: Catch-all for unexpected errors (500 responses)
    
    Args:
        app (FastAPI): The FastAPI application instance to register handlers on
        
    Error Response Format:
        All handlers return a consistent JSON array format:
        [
            {
                "errorcode": "ERROR_CODE",
                "errormessage": "Human readable message",
                "errorStatus": 400,
                "errorField": "field_name"  # optional, for validation errors
            }
        ]
        
    Example Usage:
        app = FastAPI()
        register_exception_handlers(app)
        
    Note:
        The response format uses specific field names (errorcode, errormessage, etc.)
        to match client expectations. Field aliases in ApiErrorItem handle the mapping.
    """

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:  # type: ignore[unused-ignore]
        """Handle structured application errors.
        
        Processes AppError exceptions and converts them to standardized JSON responses.
        If the exception contains pre-structured errors, those are used; otherwise,
        a single error item is created from the exception properties.
        
        Args:
            request (Request): The HTTP request that caused the error
            exc (AppError): The application error exception
            
        Returns:
            JSONResponse: Structured error response with appropriate HTTP status
        """
        items: list[ApiErrorItem] = []
        if exc.errors:
            items = exc.errors
        else:
            payload: dict[str, Any] = {
                "errorcode": exc.code.value,
                "errormessage": exc.message,
                "errorStatus": exc.status_code,
                "erorFiled": None,
            }
            items = [ApiErrorItem.model_validate(payload)]
        return JSONResponse(
            status_code=exc.status_code,
            content=[item.model_dump(by_alias=True) for item in items],
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:  # type: ignore[unused-ignore]
        """Handle Pydantic validation errors from request data.
        
        Converts Pydantic validation errors into standardized error responses.
        Each validation error is transformed into an ApiErrorItem with field
        context for precise error reporting.
        
        Args:
            request (Request): The HTTP request that failed validation
            exc (RequestValidationError): The validation error from Pydantic
            
        Returns:
            JSONResponse: Structured validation error response (422 status)
            
        Error Structure:
            Each validation error includes:
            - Error code: "VALIDATION_ERROR"
            - Specific error message from Pydantic
            - HTTP status: 422 (Unprocessable Entity)
            - Field path that caused the error
        """
        items: list[ApiErrorItem] = []
        for err in exc.errors():
            # err is like {"loc": ("body", "field"), "msg": "...", "type": "value_error"}
            loc = err.get("loc", ())
            field = ".".join(str(p) for p in loc[1:]) if isinstance(loc, list | tuple) else None
            payload: dict[str, Any] = {
                "errorcode": ErrorCode.validation_error.value,
                "errormessage": str(err.get("msg", "Validation failed")),
                "errorStatus": HTTP_422_UNPROCESSABLE_ENTITY,
                "erorFiled": field,
            }
            items.append(ApiErrorItem.model_validate(payload))
        return JSONResponse(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            content=[item.model_dump(by_alias=True) for item in items],
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:  # type: ignore[unused-ignore]
        """Handle unexpected errors and exceptions.
        
        Catch-all handler for any exceptions not handled by more specific handlers.
        Returns a generic "Internal Server Error" response to avoid exposing
        sensitive error details to clients.
        
        Args:
            request (Request): The HTTP request that caused the error
            exc (Exception): The unexpected exception
            
        Returns:
            JSONResponse: Generic error response with 500 status
            
        Security Note:
            This handler intentionally provides minimal error details to prevent
            information leakage. Detailed error information should be logged
            server-side for debugging while returning safe messages to clients.
        """
        items: list[ApiErrorItem] = []
        payload: dict[str, Any] = {
            "errorcode": ErrorCode.internal_error.value,
            "errormessage": "Internal Server Error",
            "errorStatus": HTTP_500_INTERNAL_SERVER_ERROR,
            "erorFiled": None,
        }
        items.append(ApiErrorItem.model_validate(payload))
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content=[item.model_dump(by_alias=True) for item in items],
        )
