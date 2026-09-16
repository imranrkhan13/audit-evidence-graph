from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.deps import get_current_user

router = APIRouter(prefix="/engagements", tags=["engagements"])


@router.get("", response_model=list[schemas.EngagementOut])
def list_engagements(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    return db.query(models.Engagement).all()


@router.get("/{engagement_id}/dashboard", response_model=schemas.DashboardOut)
def get_dashboard(engagement_id: str, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    eng = db.query(models.Engagement).filter(models.Engagement.id == engagement_id).first()
    if not eng:
        raise HTTPException(404, "Engagement not found")

    assertions = db.query(models.Assertion).filter(models.Assertion.engagement_id == engagement_id).all()
    passed = sum(1 for a in assertions if a.status == "pass")
    needs_review = sum(1 for a in assertions if a.status == "needs_review")
    failed = sum(1 for a in assertions if a.status == "fail")
    pending = sum(1 for a in assertions if a.status == "pending")

    open_reviews = (
        db.query(models.ReviewTask)
        .join(models.Assertion, models.Assertion.id == models.ReviewTask.assertion_id)
        .filter(models.Assertion.engagement_id == engagement_id, models.ReviewTask.status == "open")
        .all()
    )
    exception_value = round(sum(t.financial_impact for t in open_reviews), 2)
    missing_evidence_count = sum(1 for t in open_reviews if t.reason == "missing_evidence")

    stages = (
        db.query(models.WorkflowRun)
        .filter(models.WorkflowRun.engagement_id == engagement_id)
        .order_by(models.WorkflowRun.started_at)
        .all()
    )
    workflow_stages = [{"stage": s.stage, "status": s.status, "detail": s.detail} for s in stages]

    return schemas.DashboardOut(
        engagement=eng,
        total_assertions=len(assertions),
        passed=passed,
        needs_review=needs_review,
        failed=failed,
        pending=pending,
        exception_value=exception_value,
        missing_evidence_count=missing_evidence_count,
        workflow_stages=workflow_stages,
    )
