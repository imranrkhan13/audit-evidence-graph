from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.deps import get_current_user
from app.anomaly import compute_risk_flags
from app.search import search_pages

router = APIRouter(tags=["risk"])


@router.get("/risk/radar")
def get_risk_radar(engagement_id: str, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    """Continuous risk monitoring: every ledger entry in the engagement is
    scored right now (not sampled) against a small set of deterministic
    statistical signals, and returned highest-risk first."""
    rows = db.query(models.LedgerEntry).filter(models.LedgerEntry.engagement_id == engagement_id).all()
    ledger_dicts = [
        {"reference": r.reference, "description": r.description, "amount": r.amount, "entry_date": r.entry_date}
        for r in rows
    ]
    flags = compute_risk_flags(ledger_dicts)

    # attach the assertion id for each flagged reference, if one exists, so the
    # frontend can deep-link straight from a risk flag to the assertion detail
    assertions = db.query(models.Assertion).filter(models.Assertion.engagement_id == engagement_id).all()
    by_subject = {a.subject_key: a.id for a in assertions}

    return [
        {
            "reference": f.reference,
            "vendor": f.vendor,
            "amount": f.amount,
            "entry_date": f.entry_date,
            "risk_score": f.risk_score,
            "signals": [{"code": s.code, "label": s.label, "weight": s.weight} for s in f.signals],
            "assertion_id": by_subject.get(f.reference),
        }
        for f in flags
    ]


@router.get("/evidence/search")
def evidence_search(engagement_id: str, query: str, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    """Deterministic TF-IDF vector search over every page in this engagement.
    Locates candidate evidence only — see app/search.py's module docstring
    for why this can never influence a tie-out decision."""
    docs = db.query(models.Document).filter(models.Document.engagement_id == engagement_id).all()
    doc_titles = {d.id: d.title for d in docs}
    doc_ids = list(doc_titles.keys())

    pages = db.query(models.DocumentPage).filter(models.DocumentPage.document_id.in_(doc_ids)).all()
    page_dicts = [
        {"document_id": p.document_id, "document_title": doc_titles.get(p.document_id, "Unknown"),
         "page_number": p.page_number, "text_content": p.text_content}
        for p in pages
    ]

    results = search_pages(page_dicts, query)
    return [
        {"document_id": r.document_id, "document_title": r.document_title,
         "page_number": r.page_number, "score": r.score, "snippet": r.snippet}
        for r in results
    ]
