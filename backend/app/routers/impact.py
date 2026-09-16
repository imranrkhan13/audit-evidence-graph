"""Read-only dependency analysis. A preview never changes an audit conclusion."""
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models as m
from app.database import get_db
from app.deps import get_current_user

router = APIRouter(prefix="/impact", tags=["evidence change impact"])


@router.get("/documents")
def documents(engagement_id: str, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    if not db.get(m.Engagement, engagement_id):
        raise HTTPException(404, "Engagement not found")
    return [dict(id=d.id, title=d.title, version=d.version, doc_type=d.doc_type.value)
            for d in db.query(m.Document).filter_by(engagement_id=engagement_id, is_current=True)
            .order_by(m.Document.doc_type, m.Document.title).all()]


@router.get("/{document_id}")
def preview(document_id: str, proposed_amount: float | None = Query(None, ge=0, le=1e12, allow_inf_nan=False),
            db: Session = Depends(get_db), _user=Depends(get_current_user)):
    doc = db.get(m.Document, document_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    if not doc.is_current:
        raise HTTPException(409, "Select the current document version to preview impact")
    if proposed_amount is not None and doc.doc_type != m.DocumentType.INVOICE:
        raise HTTPException(422, "Amount previews are supported for invoices only")

    # Walk actual version pointers, not filenames, and keep engagement boundaries.
    family = {doc.id}
    while True:
        ancestors = {d.id for d in db.query(m.Document).filter(
            m.Document.engagement_id == doc.engagement_id, m.Document.superseded_by_id.in_(family)).all()}
        if ancestors <= family:
            break
        family |= ancestors
    links = db.query(m.EvidenceLink).filter(m.EvidenceLink.document_id.in_(family)).all()
    linked_ids = {link.assertion_id for link in links}
    assertions = db.query(m.Assertion).filter_by(engagement_id=doc.engagement_id).order_by(m.Assertion.subject_key).all()
    affected = [a for a in assertions if a.primary_document_id in family or a.id in linked_ids]
    rows = []
    for a in affected:
        primary = a.primary_document_id in family
        tasks = db.query(m.ReviewTask).filter_by(assertion_id=a.id).all()
        task_ids = [t.id for t in tasks]
        approvals = db.query(m.Approval).filter(m.Approval.review_task_id.in_(task_ids),
                                              m.Approval.decision == "approve").all() if task_ids else []
        ledger = db.query(m.LedgerEntry).filter_by(engagement_id=doc.engagement_id, reference=a.subject_key).all()
        # Never choose an arbitrary ledger row when there are duplicates.
        comparison = None
        if proposed_amount is not None and primary and len(ledger) == 1 and ledger[0].currency == "USD":
            delta = Decimal(str(proposed_amount)) - Decimal(str(ledger[0].amount))
            comparison = dict(ledger_amount=ledger[0].amount, proposed_amount=proposed_amount,
                              difference=float(delta.quantize(Decimal("0.01"))),
                              matches=abs(delta) <= Decimal("0.01"), currency="USD")
        rows.append(dict(id=a.id, label=a.label, reference=a.subject_key, status=a.status,
                         relationship="primary source" if primary else "supporting evidence",
                         source_version_stale=a.primary_document_id in family - {doc.id}
                         or any(l.assertion_id == a.id and l.document_id != doc.id for l in links),
                         amount=a.extracted_value, confidence=a.confidence,
                         approvals_to_revisit=len(approvals),
                         open_reviews=sum(t.status in ("open", "evidence_requested") for t in tasks),
                         current_rules=db.query(m.TieOutResult).filter_by(assertion_id=a.id, is_current=True).count(),
                         comparison=comparison))
    return dict(report_type="SYNTHETIC_CHANGE_IMPACT_PREVIEW", read_only=True,
                note="Dependency preview only. Prior approvals may need reassessment; no approvals or conclusions have been changed. Amount comparison covers only invoice versus a single USD ledger row, not a full tie-out.",
                document=dict(id=doc.id, title=doc.title, version=doc.version, content_hash=doc.content_hash,
                              doc_type=doc.doc_type.value, prior_versions=len(family)-1),
                total_assertions=len(assertions), affected_count=len(rows),
                unaffected_count=len(assertions)-len(rows),
                approvals_to_revisit=sum(r["approvals_to_revisit"] for r in rows),
                rules_to_revisit=sum(r["current_rules"] for r in rows), assertions=rows)
