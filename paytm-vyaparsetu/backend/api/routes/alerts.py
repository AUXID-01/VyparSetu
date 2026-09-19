from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from api.deps import get_db, get_current_merchant
from db.models import Alert
from core.errors import success_envelope, AppException, ErrorCode

router = APIRouter()

@router.get("")
def get_alerts(db: Session = Depends(get_db), merchant_id: str = Depends(get_current_merchant)):
    alerts = db.query(Alert).filter(
        Alert.merchant_id == merchant_id
    ).order_by(Alert.created_at.desc()).all()
    
    result = []
    for a in alerts:
        result.append({
            "alert_id": a.alert_id,
            "alert_type": a.alert_type,
            "is_read": a.is_read,
            "details": a.details,
            "created_at": a.created_at.isoformat()
        })
    return success_envelope(result)

@router.patch("/{alert_id}/read")
def mark_alert_read(alert_id: str, db: Session = Depends(get_db), merchant_id: str = Depends(get_current_merchant)):
    alert = db.query(Alert).filter(
        Alert.alert_id == alert_id,
        Alert.merchant_id == merchant_id
    ).first()
    
    if not alert:
        raise AppException(ErrorCode.NOT_FOUND, "Alert not found", 404)
        
    alert.is_read = True
    db.commit()
    
    return success_envelope({"status": "SUCCESS"})
