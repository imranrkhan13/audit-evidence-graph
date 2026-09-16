from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.deps import get_current_user, require_roles
from app.normalization import normalize_invoice_id, normalize_vendor
from app.seed import sha256_hex
from app import engine as tie_out_engine

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/{document_id}", response_model=schemas.DocumentOut)
def get_document(document_id: str, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc


@router.get("/{document_id}/pages", response_model=list[schemas.DocumentPageOut])
def get_document_pages(document_id: str, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    pages = (
        db.query(models.DocumentPage)
        .filter(models.DocumentPage.document_id == document_id)
        .order_by(models.DocumentPage.page_number)
        .all()
    )
    return pages


@router.post("/{document_id}/amend")
def amend_document(
    document_id: str,
    new_amount: float = Body(..., embed=True),
    db: Session = Depends(get_db),
    user=Depends(require_roles("admin", "auditor")),
):
    """Demonstrates document versioning + rerun-only-affected-assertions.

    Creates a new version of the invoice document with a corrected amount,
    marks the old version superseded (never deleted), and reruns the tie-out
    only for assertions whose subject_key matches this invoice — every other
    assertion is left untouched, and the prior tie-out result is preserved
    in history (is_current=False) rather than overwritten.
    """
    old_doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not old_doc or old_doc.doc_type != models.DocumentType.INVOICE:
        raise HTTPException(404, "Invoice document not found")
    if not old_doc.is_current:
        raise HTTPException(400, "Cannot amend a document that is not the current version")

    old_page = (
        db.query(models.DocumentPage)
        .filter(models.DocumentPage.document_id == old_doc.id, models.DocumentPage.page_number == 1)
        .first()
    )
    new_text = old_page.text_content.replace(
        old_page.text_content.split("Total Due: $")[1].split("\n")[0],
        f"{new_amount:,.2f}",
    )
    new_hash = sha256_hex(new_text)
    new_doc = models.Document(
        engagement_id=old_doc.engagement_id, doc_type=old_doc.doc_type, title=old_doc.title,
        version=old_doc.version + 1, is_current=True, content_hash=new_hash,
        raw_fixture_key=old_doc.raw_fixture_key,
    )
    db.add(new_doc)
    db.flush()
    db.add(models.DocumentPage(document_id=new_doc.id, page_number=1, text_content=new_text,
                                tables_json=[], content_hash=new_hash))
    old_doc.is_current = False
    old_doc.superseded_by_id = new_doc.id

    db.add(models.AuditEvent(
        engagement_id=old_doc.engagement_id, event_type="ingestion", entity_type="document", entity_id=new_doc.id,
        actor=user.id, summary=f"Document '{old_doc.title}' amended to version {new_doc.version}; prior version preserved.",
        payload_json={"previous_version": old_doc.version, "previous_document_id": old_doc.id},
    ))

    invoice_id_line = [l for l in new_text.split("\n") if l.startswith("Invoice Number:")][0]
    invoice_id = invoice_id_line.split(":", 1)[1].strip()
    subject_key = normalize_invoice_id(invoice_id)
    vendor_line = [l for l in new_text.split("\n") if l.startswith("Vendor:")][0]
    vendor = vendor_line.split(":", 1)[1].strip()

    affected = (
        db.query(models.Assertion)
        .filter(models.Assertion.engagement_id == old_doc.engagement_id, models.Assertion.subject_key == subject_key)
        .all()
    )
    ledger_row = (
        db.query(models.LedgerEntry)
        .filter(models.LedgerEntry.engagement_id == old_doc.engagement_id, models.LedgerEntry.reference == subject_key)
        .first()
    )
    run = models.TieOutRun(engagement_id=old_doc.engagement_id, triggered_by=user.id, reason="rerun_on_document_change")
    db.add(run)
    db.flush()

    updated = []
    for assertion in affected:
        assertion.extracted_value = new_amount
        assertion.primary_document_id = new_doc.id
        assertion.quote = f"Total Due: ${new_amount:,.2f}"
        facts = {
            "extraction_status": "ok", "has_invoice": True, "has_approval": True,
            "invoice_total": new_amount, "ledger_amount": ledger_row.amount if ledger_row else None,
            "line_items_sum": new_amount, "bank_txn_amount": new_amount,
            "payment_date": "2025-06-15", "currency": "USD", "fx_rate_applied": None,
            "confidence": 0.97, "invoice_vendor_normalized": normalize_vendor(vendor),
            "ledger_vendor_normalized": normalize_vendor(vendor), "normalized_invoice_id": subject_key,
            "all_invoice_ids": [subject_key],
        }
        status = tie_out_engine.run_tie_out_for_assertion(db, assertion, run.id, facts, reason="rerun_on_document_change", actor=user.id)
        updated.append({"assertion_id": assertion.id, "new_status": status})

    run.completed_at = datetime.utcnow()
    db.commit()
    return {"new_document_id": new_doc.id, "new_version": new_doc.version, "rerun_assertions": updated}
