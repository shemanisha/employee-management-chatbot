from fastapi import FastAPI, Request

from api.routes.auth import router as auth_router
from api.routes.employees import router as employee_router

from fastapi.responses import JSONResponse

from core.config import settings
from core.exceptions import (
    AppError,
    EmployeeNotFoundError,
    InsufficientLeaveBalanceError,
    InvalidCredentialsError,
)




app = FastAPI(
    title=settings.app_name,
)

app.include_router(auth_router)
app.include_router(employee_router)


@app.exception_handler(EmployeeNotFoundError)
async def employee_not_found_handler(
    request: Request,
    exc: EmployeeNotFoundError,
):
    return JSONResponse(
        status_code=404,
        content={
            "error": "EMPLOYEE_NOT_FOUND",
            "message": str(exc),
        },
    )


@app.exception_handler(InsufficientLeaveBalanceError)
async def leave_balance_handler(
    request: Request,
    exc: InsufficientLeaveBalanceError,
):
    return JSONResponse(
        status_code=400,
        content={
            "error": "INSUFFICIENT_LEAVE_BALANCE",
            "message": str(exc),
        },
    )


@app.exception_handler(InvalidCredentialsError)
async def credentials_handler(
    request: Request,
    exc: InvalidCredentialsError,
):
    return JSONResponse(
        status_code=401,
        content={
            "error": "INVALID_CREDENTIALS",
            "message": "Invalid email or password",
        },
    )


@app.exception_handler(AppError)
async def application_error_handler(
    request: Request,
    exc: AppError,
):
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.__class__.__name__,
            "message": str(exc),
        },
    )


@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }