from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import ErrorCode


class AppError(Exception):
    """Base application error with code and HTTP status."""

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
    code: str
    message: str
    details: dict[str, Any] | None = None
    # Optional list of structured errors, using consumer-facing aliases.
    errors: list["ApiErrorItem"] | None = None


class ApiErrorItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    # Field aliases match requested shape:
    #   errorcode, errormessage, errorStatus, erorFiled (typo preserved as alias)
    code: str = Field(alias="errorcode")
    message: str = Field(alias="errormessage")
    status: int | None = Field(default=None, alias="errorStatus")
    field: str | None = Field(default=None, alias="errorField")
