"""Assertion-level tie-out orchestration.

Wraps the pure rule functions in app/tie_out.py, persists TieOutResult rows,
updates the Assertion's status, opens ReviewTask rows when needed, and writes
AuditEvent rows for every step. This is the single code path used both by
the initial seed run and by reruns triggered by document changes — so
"seed" and "rerun" behave identically.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app import models
from app.config import settings
from app import tie_out


def _log_event(db: Session, engagement_id: str, event_type: str, entity_type: str,
                entity_id: str, actor: str, summary: str, payload: Optional[dict] = None):
    db.add(models.AuditEvent(
        engagement_id=engagement_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        actor=actor,
        summary=summary,
        payload_json=payload or {},
    ))


def run_tie_out_for_assertion(
    db: Session,
    assertion: models.Assertion,
    run_id: str,
    facts: dict,
    reason: str = "initial",
    actor: str = "system",
) -> str:
    """Evaluate all applicable deterministic rules for one assertion, persist
    results, set the assertion's final status, and open a review task if
    warranted. Returns the final status string.

    `facts` carries the pre-resolved, already-normalized inputs the rules
    need (invoice_total, ledger_amount, bank_txn_amount, payment_date,
    has_invoice, has_approval, extraction_status, confidence, currency info).
    Resolving those facts is the caller's job (see seed.py) so this function
    stays purely about rule evaluation + bookkeeping.
    """
    # supersede any previous "current" results for this assertion
    old_results = db.query(models.TieOutResult).filter(
        models.TieOutResult.assertion_id == assertion.id,
        models.TieOutResult.is_current == True,  # noqa: E712
    ).all()
    for r in old_results:
        r.is_current = False

    results = []
    results.append(tie_out.check_extraction_not_failed(facts["extraction_status"]))
    results.append(tie_out.check_missing_evidence(facts["has_invoice"], facts["has_approval"]))

    if facts["has_invoice"]:
        results.append(tie_out.check_invoice_equals_ledger(facts.get("invoice_total"), facts.get("ledger_amount")))
        results.append(tie_out.check_line_items_equal_total(facts.get("line_items_sum"), facts.get("invoice_total")))
        results.append(tie_out.check_bank_txn_supports_payment(facts.get("bank_txn_amount"), facts.get("invoice_total")))
        results.append(tie_out.check_payment_date_in_period(
            facts.get("payment_date"), settings.AUDIT_PERIOD_START, settings.AUDIT_PERIOD_END))
        results.append(tie_out.check_currency_conversion_explicit(
            facts.get("currency", "USD"), "USD", facts.get("fx_rate_applied")))
        results.append(tie_out.check_identities_match(
            facts.get("invoice_vendor_normalized"), facts.get("ledger_vendor_normalized")))
        results.append(tie_out.check_duplicate_invoice(
            facts.get("normalized_invoice_id"), facts.get("all_invoice_ids", [])))

    for r in results:
        db.add(models.TieOutResult(
            tie_out_run_id=run_id,
            assertion_id=assertion.id,
            rule_name=r.rule_name,
            passed=r.passed,
            detail=r.detail,
            computed_value=r.computed_value,
            expected_value=r.expected_value,
            difference=r.difference,
            is_current=True,
        ))

    hard_failures = [r for r in results if not r.passed]
    low_confidence = facts["confidence"] < settings.CONFIDENCE_REVIEW_THRESHOLD

    if hard_failures and not facts["extraction_status"] == "ok":
        status = "fail"
        review_reason = "missing_evidence" if not facts["has_invoice"] else "failed_extraction"
    elif any(r.rule_name == "missing_evidence_check" and not r.passed for r in results):
        status = "fail"
        review_reason = "missing_evidence"
    elif any(r.rule_name in ("invoice_equals_ledger", "bank_txn_supports_payment") and not r.passed for r in results):
        status = "fail"
        review_reason = "material_exception"
    elif low_confidence:
        status = "needs_review"
        review_reason = "low_confidence"
    elif hard_failures:
        status = "needs_review"
        review_reason = "contradictory"
    else:
        status = "pass"
        review_reason = None

    assertion.status = status
    assertion.updated_at = datetime.utcnow()

    if review_reason:
        financial_impact = abs(facts.get("invoice_total") or 0 - (facts.get("ledger_amount") or facts.get("invoice_total") or 0))
        risk = "high" if financial_impact > 1000 or review_reason == "missing_evidence" else (
            "medium" if review_reason in ("material_exception", "contradictory") else "low"
        )
        db.add(models.ReviewTask(
            assertion_id=assertion.id,
            reason=review_reason,
            financial_impact=round(financial_impact, 2),
            risk_level=risk,
            status="open",
        ))
        _log_event(db, assertion.engagement_id, "review", "assertion", assertion.id, actor,
                   f"Routed to review: {review_reason} (status={status}).")

    _log_event(db, assertion.engagement_id, "tie_out", "assertion", assertion.id, actor,
               f"Tie-out evaluated ({reason}); {sum(1 for r in results if r.passed)}/{len(results)} rules passed; "
               f"final status = {status}.",
               payload={"rule_results": [r.rule_name for r in results]})

    return status
