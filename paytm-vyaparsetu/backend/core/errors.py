from enum import Enum
from typing import Any, Optional, Dict
from fastapi.responses import JSONResponse

class StrEnum(str, Enum):
    def __str__(self) -> str:
        return str(self.value)

class ErrorCode(StrEnum):
    CUSTOMER_NOT_FOUND = "CUSTOMER_NOT_FOUND"
    MERCHANT_NOT_FOUND = "MERCHANT_NOT_FOUND"
    INVOICE_NOT_FOUND = "INVOICE_NOT_FOUND"
    LOW_CONFIDENCE_EXTRACTION = "LOW_CONFIDENCE_EXTRACTION"
    DUPLICATE_MERCHANT_PHONE = "DUPLICATE_MERCHANT_PHONE"
    INTERNAL_TOKEN_INVALID = "INTERNAL_TOKEN_INVALID"
    SARVAM_API_ERROR = "SARVAM_API_ERROR"

class AppException(Exception):
    def __init__(self, code: ErrorCode, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)

def success_envelope(data: Any = None) -> Dict[str, Any]:
    """
    Standard success response envelope:
    {
        "success": true,
        "data": { ... },
        "error": null
    }
    """
    return {
        "success": True,
        "data": data,
        "error": None
    }

def error_envelope(code: ErrorCode | str, message: str) -> Dict[str, Any]:
    """
    Standard error response envelope:
    {
        "success": false,
        "data": null,
        "error": { "code": "CUSTOMER_NOT_FOUND", "message": "..." }
    }
    """
    code_str = code.value if isinstance(code, ErrorCode) else str(code)
    return {
        "success": False,
        "data": None,
        "error": {
            "code": code_str,
            "message": message
        }
    }

def app_exception_handler(request: Any, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_envelope(exc.code, exc.message)
    )
