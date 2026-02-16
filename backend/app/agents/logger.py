from app.db import SessionLocal
from app.models import AuditLog

def log_event(user_id, action, status, message):
    db = SessionLocal()
    db.add(AuditLog(
        user_id=user_id,
        action=action,
        status=status,
        message=message,
    ))
    db.commit()
    db.close()
