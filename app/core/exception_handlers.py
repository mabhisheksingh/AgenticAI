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
    """Register global exception handlers (Controller Advice).

    - AppError: controlled application errors with code and status
    - RequestValidationError: pydantic/validation errors
    - Exception: unexpected errors (500)
    """

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:  # type: ignore[unused-ignore]
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
