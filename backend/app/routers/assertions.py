from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.deps import get_current_user

router = APIRouter(prefix="/assertions", tags=["assertions"])


@router.get("", response_model=list[schemas.AssertionOut])
def list_assertions(engagement_id: str, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    return (
        db.query(models.Assertion)
        .filter(models.Assertion.engagement_id == engagement_id)
        .order_by(models.Assertion.subject_key)
        .all()
    )


@router.get("/{assertion_id}", response_model=schemas.AssertionDetailOut)
def get_assertion(assertion_id: str, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    a = db.query(models.Assertion).filter(models.Assertion.id == assertion_id).first()
    if not a:
        raise HTTPException(404, "Assertion not found")

    current_results = (
        db.query(models.TieOutResult)
        .filter(models.TieOutResult.assertion_id == assertion_id, models.TieOutResult.is_current == True)  # noqa: E712
        .all()
    )
    history_results = (
        db.query(models.TieOutResult)
        .filter(models.TieOutResult.assertion_id == assertion_id, models.TieOutResult.is_current == False)  # noqa: E712
        .order_by(models.TieOutResult.created_at)
        .all()
    )

    links = db.query(models.EvidenceLink).filter(models.EvidenceLink.assertion_id == assertion_id).all()
    link_out = []
    for link in links:
        title = None
        if link.document_id:
            doc = db.query(models.Document).filter(models.Document.id == link.document_id).first()
            title = doc.title if doc else None
        link_out.append(schemas.EvidenceLinkOut(
            id=link.id, document_id=link.document_id, document_title=title,
            page_number=link.page_number, relation=link.relation,
        ))

    ledger_rows = (
        db.query(models.LedgerEntry)
        .filter(models.LedgerEntry.engagement_id == a.engagement_id, models.LedgerEntry.reference == a.subject_key)
        .all()
    )
    ledger_out = [
        {"id": r.id, "entry_date": r.entry_date, "account": r.account, "reference": r.reference,
         "description": r.description, "amount": r.amount, "currency": r.currency}
        for r in ledger_rows
    ]

    review_task = (
        db.query(models.ReviewTask)
        .filter(models.ReviewTask.assertion_id == assertion_id)
        .order_by(models.ReviewTask.created_at.desc())
        .first()
    )
    review_out = None
    if review_task:
        approval = (
            db.query(models.Approval)
            .filter(models.Approval.review_task_id == review_task.id)
            .order_by(models.Approval.created_at.desc())
            .first()
        )
        review_out = {
            "id": review_task.id, "reason": review_task.reason, "status": review_task.status,
            "financial_impact": review_task.financial_impact, "risk_level": review_task.risk_level,
            "last_decision": approval.decision if approval else None,
            "last_note": approval.note if approval else None,
        }

    return schemas.AssertionDetailOut(
        id=a.id, label=a.label, assertion_type=a.assertion_type, subject_key=a.subject_key,
        extracted_value=a.extracted_value, confidence=a.confidence, status=a.status, material=a.material,
        updated_at=a.updated_at, quote=a.quote, primary_document_id=a.primary_document_id,
        primary_page_number=a.primary_page_number,
        tie_out_results=current_results, tie_out_history=history_results,
        evidence_links=link_out, ledger_rows=ledger_out, review_task=review_out,
    )
