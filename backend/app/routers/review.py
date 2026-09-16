from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.deps import require_roles

router = APIRouter(prefix="/review", tags=["review"])

VALID_DECISIONS = {"approve", "reject", "request_evidence"}


@router.get("/queue", response_model=list[schemas.ReviewTaskOut])
def get_review_queue(
    engagement_id: str,
    sort_by: str = "financial_impact",
    status_filter: str = "open",
    db: Session = Depends(get_db),
    _user=Depends(require_roles("admin", "auditor", "reviewer")),
):
    query = (
        db.query(models.ReviewTask, models.Assertion)
        .join(models.Assertion, models.Assertion.id == models.ReviewTask.assertion_id)
        .filter(models.Assertion.engagement_id == engagement_id)
    )
    if status_filter != "all":
        query = query.filter(models.ReviewTask.status == status_filter)
    rows = query.all()

    out = [
        schemas.ReviewTaskOut(
            id=t.id, assertion_id=a.id, assertion_label=a.label, reason=t.reason,
            financial_impact=t.financial_impact, risk_level=t.risk_level, status=t.status,
            confidence=a.confidence, created_at=t.created_at,
        )
        for t, a in rows
    ]

    risk_order = {"high": 0, "medium": 1, "low": 2}
    if sort_by == "financial_impact":
        out.sort(key=lambda r: r.financial_impact, reverse=True)
    elif sort_by == "confidence":
        out.sort(key=lambda r: r.confidence)
    elif sort_by == "risk":
        out.sort(key=lambda r: risk_order.get(r.risk_level, 3))
    elif sort_by == "status":
        out.sort(key=lambda r: r.status)
    return out


@router.post("/tasks/{task_id}/action")
def act_on_review_task(
    task_id: str,
    action: schemas.ReviewActionIn,
    db: Session = Depends(get_db),
    user=Depends(require_roles("admin", "reviewer")),
):
    """Atomic: the approval row, the review task status change, and the audit
    event are written in a single DB transaction — either all persist or
    none do."""
    if action.decision not in VALID_DECISIONS:
        raise HTTPException(400, f"decision must be one of {sorted(VALID_DECISIONS)}")

    task = db.query(models.ReviewTask).filter(models.ReviewTask.id == task_id).first()
    if not task:
        raise HTTPException(404, "Review task not found")
    if task.status != "open":
        raise HTTPException(400, f"Review task is already '{task.status}'")

    assertion = db.query(models.Assertion).filter(models.Assertion.id == task.assertion_id).first()

    try:
        approval = models.Approval(review_task_id=task.id, reviewer_id=user.id, decision=action.decision, note=action.note)
        db.add(approval)

        if action.decision == "approve":
            task.status = "approved"
            assertion.status = "pass"
        elif action.decision == "reject":
            task.status = "rejected"
            assertion.status = "fail"
        else:
            task.status = "evidence_requested"

        from datetime import datetime
        task.resolved_at = datetime.utcnow() if action.decision != "request_evidence" else None

        db.add(models.AuditEvent(
            engagement_id=assertion.engagement_id, event_type="approval", entity_type="assertion",
            entity_id=assertion.id, actor=user.id,
            summary=f"Reviewer decision '{action.decision}' on review task {task.id}"
                    + (f": {action.note}" if action.note else "") + f". Assertion status now '{assertion.status}'.",
            payload_json={"decision": action.decision, "note": action.note, "review_task_id": task.id},
        ))
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"task_id": task.id, "new_status": task.status, "assertion_status": assertion.status}
