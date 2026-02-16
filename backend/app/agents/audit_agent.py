from datetime import datetime
from zoneinfo import ZoneInfo

from app.db import SessionLocal
from app.models import AuditLog


class AuditAgent:
    """
    Audit Agent provides immutable audit logging.
    Records all significant events for compliance and debugging.
    """

    def log_event(
        self,
        user_id: int,
        action: str,
        status: str,
        message: str,
    ) -> None:
        """
        Log an event to the audit log.
        
        Common actions:
        - PAYMENT_REQUESTED, PAYMENT_CONFIRMED, PAYMENT_CANCELLED
        - PAYMENT_EXECUTED, PAYMENT_FAILED
        - PAYMENT_BLOCKED_RISK, PAYMENT_BLOCKED_INSUFFICIENT_FUNDS
        - BALANCE_VIEWED, HISTORY_VIEWED, BILLS_VIEWED
        
        Common statuses:
        - SUCCESS, FAILED, BLOCKED, PENDING
        """
        db = SessionLocal()
        try:
            log = AuditLog(
                user_id=user_id,
                action=action,
                status=status,
                message=message,
                created_at=datetime.now(ZoneInfo("UTC")),
            )
            db.add(log)
            db.commit()
        except Exception as e:
            print(f"Audit logging error: {str(e)}")
            db.rollback()
        finally:
            db.close()

    def get_audit_logs(self, user_id: int, limit: int = 50) -> list:
        """Retrieve audit logs for a user"""
        db = SessionLocal()
        try:
            logs = db.query(AuditLog).filter(
                AuditLog.user_id == user_id
            ).order_by(AuditLog.created_at.desc()).limit(limit).all()
            return logs
        finally:
            db.close()


# Legacy function for backward compatibility
def log_event(
    user_id: int,
    action: str,
    status: str,
    message: str,
) -> None:
    """Legacy function - use AuditAgent.log_event instead"""
    agent = AuditAgent()
    agent.log_event(user_id, action, status, message)
