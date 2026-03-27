from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.database import get_db
from app.models.user import User
from app.models.alert_log import AlertLog
from datetime import datetime, timezone

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("/acknowledge/{alert_id}")
def acknowledge_alert(
    alert_id: int, 
    user_id: UUID,
    db: Session = Depends(get_db)
):
    alert = db.query(AlertLog).filter(AlertLog.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูลการแจ้งเตือน")
    if alert.is_acknowledged:
        previous_user = db.query(User).filter(User.user_id == alert.acknowledged_by).first()
        name = previous_user.first_name if previous_user else "บุคคลอื่น"
        return {"message": f"เหตุการณ์นี้ได้รับการยืนยันไปแล้วโดยคุณ {name}"}

    user = db.query(User).filter(User.user_id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=403, detail="สิทธิ์การยืนยันไม่ถูกต้อง")

    alert.is_acknowledged = True
    alert.acknowledged_by = user.user_id 
    alert.acknowledged_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": f"รับทราบเหตุการณ์เรียบร้อยแล้ว โดยคุณ {user.first_name}"}