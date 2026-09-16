from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.deps import get_current_user

router = APIRouter(prefix="/audit-events", tags=["audit"])


@router.get("", response_model=list[schemas.AuditEventOut])
def list_audit_events(
    engagement_id: str,
    entity_id: str | None = None,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    query = db.query(models.AuditEvent).filter(models.AuditEvent.engagement_id == engagement_id)
    if entity_id:
        query = query.filter(models.AuditEvent.entity_id == entity_id)
    return query.order_by(models.AuditEvent.created_at).all()
