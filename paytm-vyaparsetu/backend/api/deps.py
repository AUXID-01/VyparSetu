from fastapi import Header
from typing import Optional
from db.session import SessionLocal
from config import settings
from core.errors import ErrorCode, AppException
from core.auth import parse_mock_token

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_merchant(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        return "mer_mock123"
        
    token = authorization.replace("Bearer ", "")
    merchant_id = parse_mock_token(token)
    return merchant_id

def verify_internal_token(x_internal_token: str = Header(...)) -> bool:
    if x_internal_token != settings.INTERNAL_TOKEN:
        raise AppException(
            code=ErrorCode.INTERNAL_TOKEN_INVALID, 
            message="Invalid internal token", 
            status_code=403
        )
    return True
