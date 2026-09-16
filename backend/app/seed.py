"""Synthetic data seeding.

Every document, page, invoice, ledger row, and extraction result generated
here is FIXTURE DATA — clearly labeled as synthetic and used only to
demonstrate the pipeline. Nothing here represents a real client, a real
accounting firm, or a real Modus integration.
"""
import hashlib
from datetime import datetime

from sqlalchemy.orm import Session

from app import models
from app.database import engine, Base, SessionLocal
from app.security import hash_password
from app.normalization import normalize_invoice_id, normalize_vendor
from app.extraction.fixture_provider import register_fixture
from app import engine as tie_out_engine

AUDIT_PERIOD_START = "2025-01-01"
AUDIT_PERIOD_END = "2025-12-31"


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


VENDORS = [
    "Northwind Logistics Inc.", "Acme Robotics Inc.", "Blue Harbor Supplies LLC",
    "Summit Consulting Group", "Cascade Office Solutions", "Ferrostone Manufacturing Corp.",
]

# (invoice_no_suffix, vendor_idx, amount, category)
# categories: "pass" x14, "review" x3, "mismatch" x2, "missing" x1  => 20 total
INVOICE_PLAN = [
    (1001, 0, 13600.00, "pass"), (1002, 1, 8420.50, "pass"), (1003, 2, 2210.00, "pass"),
    (1004, 3, 45000.00, "pass"), (1005, 4, 990.75, "pass"), (1006, 5, 17650.00, "pass"),
    (1007, 0, 3300.00, "pass"), (1008, 1, 6120.20, "pass"), (1009, 2, 780.00, "pass"),
    (1010, 3, 22400.00, "pass"), (1011, 4, 5600.00, "pass"), (1012, 5, 11200.00, "pass"),
    (1013, 0, 940.00, "pass"), (1014, 1, 3050.00, "pass"),
    (1015, 2, 15800.00, "review"), (1016, 3, 2675.00, "review"), (1017, 4, 8890.00, "review"),
    (1018, 5, 12500.00, "mismatch"), (1019, 0, 4300.00, "mismatch"),
    (1020, 1, 9600.00, "missing"),
]

CONFIDENCE = {
    "pass": [0.94, 0.97, 0.91, 0.99, 0.93, 0.96, 0.98, 0.92, 0.95, 0.90, 0.99, 0.93, 0.96, 0.97],
    "review": [0.58, 0.72, 0.80],
    "mismatch": [0.95, 0.96],
    "missing": [],
}

MISMATCH_DELTA = {1018: 250.00, 1019: -75.50}


def build_invoice_id(n: int) -> str:
    return f"INV-2025-{n}"


def _payment_dates() -> list:
    from datetime import date, timedelta
    d = date(2025, 3, 3)  # a Monday
    dates = []
    for _ in range(20):
        dates.append(d.isoformat())
        d += timedelta(days=4)  # spread across ~10 weeks; naturally lands on some weekends
    return dates


PAYMENT_DATES = _payment_dates()


def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def seed_users(db: Session):
    users = [
        ("admin", "admin123", models.Role.ADMIN, "Priya Admin"),
        ("auditor", "auditor123", models.Role.AUDITOR, "Dana Auditor"),
        ("reviewer", "reviewer123", models.Role.REVIEWER, "Sam Reviewer"),
    ]
    for username, pw, role, display in users:
        db.add(models.User(username=username, hashed_password=hash_password(pw), role=role, display_name=display))
    db.commit()


def seed_engagement(db: Session) -> models.Engagement:
    eng = models.Engagement(
        name="FY2025 Statutory Audit — Northwind Trading Co. [SYNTHETIC DEMO DATA]",
        client_name="Northwind Trading Co. (synthetic)",
        period_start=AUDIT_PERIOD_START,
        period_end=AUDIT_PERIOD_END,
        status="in_progress",
    )
    db.add(eng)
    db.commit()
    db.refresh(eng)
    return eng


def _make_document(db, engagement_id, doc_type, title, fixture_key, page_text, version=1) -> models.Document:
    content_hash = sha256_hex(page_text)
    doc = models.Document(
        engagement_id=engagement_id, doc_type=doc_type, title=title, version=version,
        is_current=True, content_hash=content_hash, raw_fixture_key=fixture_key,
    )
    db.add(doc)
    db.flush()
    page = models.DocumentPage(
        document_id=doc.id, page_number=1, text_content=page_text,
        tables_json=[], content_hash=sha256_hex(page_text),
    )
    db.add(page)
    db.flush()
    return doc


def seed_documents_and_entities(db: Session, engagement: models.Engagement):
    all_invoice_ids_normalized = [normalize_invoice_id(build_invoice_id(n)) for n, *_ in INVOICE_PLAN]
    ledger_lines = ["account,reference,date,amount,currency,description"]
    assertions_out = []
    conf_counters = {"pass": 0, "review": 0, "mismatch": 0, "missing": 0}
    actor = "system"

    for i, (n, vendor_idx, amount, category) in enumerate(INVOICE_PLAN):
        invoice_id = build_invoice_id(n)
        vendor = VENDORS[vendor_idx]
        payment_date = PAYMENT_DATES[i]
        idx = conf_counters[category]
        confidence = CONFIDENCE[category][idx] if CONFIDENCE[category] else 0.0
        conf_counters[category] += 1

        has_invoice = category != "missing"
        has_approval = category != "missing"
        invoice_doc = None

        if has_invoice:
            fixture_key = f"invoice-{invoice_id}"
            page_text = (
                f"[SYNTHETIC FIXTURE DOCUMENT]\nINVOICE\nInvoice Number: {invoice_id}\n"
                f"Vendor: {vendor}\nInvoice Date: {payment_date}\nCurrency: USD\n"
                f"Line Items:\n  Services rendered ...... ${amount:,.2f}\n"
                f"Total Due: ${amount:,.2f}\n"
            )
            invoice_doc = _make_document(db, engagement.id, models.DocumentType.INVOICE,
                                          f"Invoice {invoice_id}", fixture_key, page_text)
            register_fixture(fixture_key, [
                {"entity_type": "invoice_id", "raw_value": invoice_id, "confidence": 0.99,
                 "quote": f"Invoice Number: {invoice_id}", "page_number": 1, "extraction_status": "ok"},
                {"entity_type": "vendor", "raw_value": vendor, "confidence": 0.97,
                 "quote": f"Vendor: {vendor}", "page_number": 1, "extraction_status": "ok"},
                {"entity_type": "amount", "raw_value": f"${amount:,.2f}", "confidence": confidence,
                 "quote": f"Total Due: ${amount:,.2f}", "page_number": 1, "extraction_status": "ok"},
                {"entity_type": "date", "raw_value": payment_date, "confidence": 0.95,
                 "quote": f"Invoice Date: {payment_date}", "page_number": 1, "extraction_status": "ok"},
                {"entity_type": "currency", "raw_value": "USD", "confidence": 0.99,
                 "quote": "Currency: USD", "page_number": 1, "extraction_status": "ok"},
            ])
            for f in [
                {"entity_type": "invoice_id", "raw_value": invoice_id, "normalized_value": normalize_invoice_id(invoice_id), "confidence": 0.99, "quote": f"Invoice Number: {invoice_id}", "page_number": 1},
                {"entity_type": "vendor", "raw_value": vendor, "normalized_value": normalize_vendor(vendor), "confidence": 0.97, "quote": f"Vendor: {vendor}", "page_number": 1},
                {"entity_type": "amount", "raw_value": f"${amount:,.2f}", "normalized_value": str(amount), "confidence": confidence, "quote": f"Total Due: ${amount:,.2f}", "page_number": 1},
                {"entity_type": "date", "raw_value": payment_date, "normalized_value": payment_date, "confidence": 0.95, "quote": f"Invoice Date: {payment_date}", "page_number": 1},
                {"entity_type": "currency", "raw_value": "USD", "normalized_value": "USD", "confidence": 0.99, "quote": "Currency: USD", "page_number": 1},
            ]:
                db.add(models.ExtractedEntity(document_id=invoice_doc.id, page_number=1, entity_type=f["entity_type"],
                                               raw_value=f["raw_value"], normalized_value=f["normalized_value"],
                                               confidence=f["confidence"], quote=f["quote"],
                                               extraction_status="ok"))

        if has_approval:
            approval_text = (
                f"[SYNTHETIC FIXTURE DOCUMENT]\nAPPROVAL MEMO\nApproves payment of {invoice_id} to {vendor} "
                f"for ${amount:,.2f}.\nApproved by: J. Alvarez, Controller.\nDate: {payment_date}\n"
            )
            _make_document(db, engagement.id, models.DocumentType.APPROVAL,
                            f"Approval for {invoice_id}", f"approval-{invoice_id}", approval_text)

        ledger_amount = amount + MISMATCH_DELTA.get(n, 0.0)
        ledger_lines.append(f"Accounts Payable,{normalize_invoice_id(invoice_id)},{payment_date},{ledger_amount:.2f},USD,{vendor}")
        db.add(models.LedgerEntry(
            engagement_id=engagement.id, entry_date=payment_date, account="Accounts Payable",
            reference=normalize_invoice_id(invoice_id), description=vendor, amount=round(ledger_amount, 2), currency="USD",
        ))

        assertions_out.append({
            "invoice_id": invoice_id, "vendor": vendor, "amount": amount, "ledger_amount": ledger_amount,
            "category": category, "confidence": confidence, "payment_date": payment_date,
            "has_invoice": has_invoice, "has_approval": has_approval, "invoice_doc": invoice_doc,
        })

    gl_text = "\n".join(ledger_lines)
    gl_doc = _make_document(db, engagement.id, models.DocumentType.GENERAL_LEDGER,
                             "General Ledger Export — FY2025 (synthetic)", "gl-export-fy2025", gl_text)

    bank_lines = ["[SYNTHETIC FIXTURE DOCUMENT] BANK STATEMENT — FY2025"]
    for a in assertions_out:
        if a["has_invoice"]:
            bank_lines.append(f"  {a['payment_date']}  DEBIT  ${a['amount']:,.2f}  ref:{normalize_invoice_id(a['invoice_id'])}")
    bank_text = "\n".join(bank_lines)
    bank_doc = _make_document(db, engagement.id, models.DocumentType.BANK_STATEMENT,
                               "Bank Statement — Operating Account (synthetic)", "bank-stmt-fy2025", bank_text)

    db.flush()
    return assertions_out, gl_doc, bank_doc, all_invoice_ids_normalized


def seed_assertions_and_tie_out(db: Session, engagement: models.Engagement, assertion_inputs, gl_doc, bank_doc, all_invoice_ids):
    run = models.TieOutRun(engagement_id=engagement.id, triggered_by="system", reason="initial")
    db.add(run)
    db.flush()
    db.add(models.WorkflowRun(engagement_id=engagement.id, stage="ingestion", status="completed",
                               detail="Seeded synthetic documents (invoices, approvals, bank statement, general ledger)."))
    db.add(models.WorkflowRun(engagement_id=engagement.id, stage="extraction", status="completed",
                               detail="Fixture extraction provider ran over all ingested documents."))
    db.add(models.WorkflowRun(engagement_id=engagement.id, stage="normalization", status="completed",
                               detail="Normalized invoice ids, vendors, currencies, dates, and amounts."))

    for a in assertion_inputs:
        assertion = models.Assertion(
            engagement_id=engagement.id,
            label=f"Invoice {a['invoice_id']} ({a['vendor']}) ties out to the general ledger and bank records.",
            assertion_type="invoice_ledger_match",
            subject_key=normalize_invoice_id(a["invoice_id"]),
            extracted_value=a["amount"] if a["has_invoice"] else None,
            confidence=a["confidence"],
            status="pending",
            material=True,
            primary_document_id=a["invoice_doc"].id if a["invoice_doc"] else None,
            primary_page_number=1 if a["invoice_doc"] else None,
            quote=f"Total Due: ${a['amount']:,.2f}" if a["has_invoice"] else None,
        )
        db.add(assertion)
        db.flush()

        db.add(models.AuditEvent(
            engagement_id=engagement.id, event_type="extraction", entity_type="assertion", entity_id=assertion.id,
            actor="system", summary=f"Extracted candidate value for {a['invoice_id']} with confidence {a['confidence']:.2f}.",
        ))
        db.add(models.AuditEvent(
            engagement_id=engagement.id, event_type="normalization", entity_type="assertion", entity_id=assertion.id,
            actor="system", summary=f"Normalized invoice id, vendor, currency, and amount for {a['invoice_id']}.",
        ))

        if a["invoice_doc"]:
            db.add(models.EvidenceLink(assertion_id=assertion.id, document_id=a["invoice_doc"].id, page_number=1,
                                        relation="source_document"))
        db.add(models.EvidenceLink(assertion_id=assertion.id, document_id=gl_doc.id, page_number=1,
                                    relation="supporting_ledger_entry"))
        if a["has_invoice"]:
            db.add(models.EvidenceLink(assertion_id=assertion.id, document_id=bank_doc.id, page_number=1,
                                        relation="supporting_bank_transaction"))
        db.flush()

        facts = {
            "extraction_status": "ok" if a["has_invoice"] else "failed",
            "has_invoice": a["has_invoice"],
            "has_approval": a["has_approval"],
            "invoice_total": a["amount"] if a["has_invoice"] else None,
            "ledger_amount": a["ledger_amount"],
            "line_items_sum": a["amount"] if a["has_invoice"] else None,
            "bank_txn_amount": a["amount"] if a["has_invoice"] else None,
            "payment_date": a["payment_date"],
            "currency": "USD",
            "fx_rate_applied": None,
            "confidence": a["confidence"],
            "invoice_vendor_normalized": normalize_vendor(a["vendor"]) if a["has_invoice"] else None,
            "ledger_vendor_normalized": normalize_vendor(a["vendor"]),
            "normalized_invoice_id": normalize_invoice_id(a["invoice_id"]),
            "all_invoice_ids": all_invoice_ids,
        }
        tie_out_engine.run_tie_out_for_assertion(db, assertion, run.id, facts, reason="initial", actor="system")

    run.completed_at = datetime.utcnow()
    db.add(models.WorkflowRun(engagement_id=engagement.id, stage="tie_out", status="completed",
                               detail="Deterministic tie-out engine evaluated all 20 seeded assertions."))
    db.commit()


def run_seed():
    reset_db()
    db = SessionLocal()
    try:
        seed_users(db)
        engagement = seed_engagement(db)
        assertion_inputs, gl_doc, bank_doc, all_invoice_ids = seed_documents_and_entities(db, engagement)
        db.commit()
        seed_assertions_and_tie_out(db, engagement, assertion_inputs, gl_doc, bank_doc, all_invoice_ids)
        print("Seed complete.")
        print("Users: admin/admin123 (admin), auditor/auditor123 (auditor), reviewer/reviewer123 (reviewer)")
        print(f"Engagement id: {engagement.id}")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
