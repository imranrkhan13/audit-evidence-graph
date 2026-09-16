"""Deterministic tie-out rule engine.

Every rule here is plain Python with no model calls. Vector/semantic search
(when present) is only ever used upstream to *locate* candidate evidence —
it never decides pass/fail. All monetary comparisons use a fixed tolerance
and are fully explainable via the returned detail string.
"""
from dataclasses import dataclass
from typing import Optional

from app.config import settings


@dataclass
class RuleResult:
    rule_name: str
    passed: bool
    detail: str
    computed_value: Optional[float] = None
    expected_value: Optional[float] = None
    difference: Optional[float] = None


TOLERANCE = settings.MATERIALITY_TOLERANCE


def check_invoice_equals_ledger(invoice_total: Optional[float], ledger_amount: Optional[float]) -> RuleResult:
    if invoice_total is None or ledger_amount is None:
        return RuleResult("invoice_equals_ledger", False, "Missing invoice total or ledger amount for comparison.")
    diff = round(invoice_total - ledger_amount, 2)
    passed = abs(diff) <= TOLERANCE
    detail = (
        f"Invoice total {invoice_total:.2f} vs ledger amount {ledger_amount:.2f}; "
        f"difference {diff:.2f} ({'within' if passed else 'exceeds'} tolerance {TOLERANCE:.2f})."
    )
    return RuleResult("invoice_equals_ledger", passed, detail, invoice_total, ledger_amount, diff)


def check_line_items_equal_total(line_items_sum: Optional[float], invoice_total: Optional[float]) -> RuleResult:
    if line_items_sum is None or invoice_total is None:
        return RuleResult("line_items_equal_total", False, "Missing line items sum or invoice total.")
    diff = round(line_items_sum - invoice_total, 2)
    passed = abs(diff) <= TOLERANCE
    detail = f"Sum of line items {line_items_sum:.2f} vs invoice total {invoice_total:.2f}; difference {diff:.2f}."
    return RuleResult("line_items_equal_total", passed, detail, line_items_sum, invoice_total, diff)


def check_bank_txn_supports_payment(txn_amount: Optional[float], invoice_total: Optional[float]) -> RuleResult:
    if txn_amount is None or invoice_total is None:
        return RuleResult("bank_txn_supports_payment", False, "No matching bank transaction found for this invoice.")
    diff = round(txn_amount - invoice_total, 2)
    passed = abs(diff) <= TOLERANCE
    detail = f"Bank transaction {txn_amount:.2f} vs invoice total {invoice_total:.2f}; difference {diff:.2f}."
    return RuleResult("bank_txn_supports_payment", passed, detail, txn_amount, invoice_total, diff)


def check_payment_date_in_period(payment_date: Optional[str], period_start: str, period_end: str) -> RuleResult:
    if payment_date is None:
        return RuleResult("payment_date_in_period", False, "Payment date could not be determined.")
    passed = period_start <= payment_date <= period_end
    detail = f"Payment date {payment_date} vs audit period {period_start} to {period_end}."
    return RuleResult("payment_date_in_period", passed, detail)


def check_identities_match(vendor_a: Optional[str], vendor_b: Optional[str]) -> RuleResult:
    if not vendor_a or not vendor_b:
        return RuleResult("identities_match", False, "One or both vendor identities missing.")
    passed = vendor_a.strip().upper() == vendor_b.strip().upper()
    detail = f"Vendor on invoice: '{vendor_a}' vs vendor on ledger/contract: '{vendor_b}'."
    return RuleResult("identities_match", passed, detail)


def check_duplicate_invoice(invoice_id: str, all_invoice_ids: list) -> RuleResult:
    count = all_invoice_ids.count(invoice_id)
    passed = count <= 1
    detail = f"Normalized invoice id '{invoice_id}' appears {count} time(s) in the document set."
    return RuleResult("duplicate_invoice_check", passed, detail)


def check_missing_evidence(has_invoice: bool, has_approval: bool) -> RuleResult:
    missing = []
    if not has_invoice:
        missing.append("invoice")
    if not has_approval:
        missing.append("approval")
    passed = len(missing) == 0
    detail = "All required documents present." if passed else f"Missing required document(s): {', '.join(missing)}."
    return RuleResult("missing_evidence_check", passed, detail)


def check_currency_conversion_explicit(from_currency: str, to_currency: str, rate_applied: Optional[float]) -> RuleResult:
    if from_currency == to_currency:
        return RuleResult("currency_conversion_explicit", True, f"No conversion needed; both amounts in {to_currency}.")
    passed = rate_applied is not None
    detail = (
        f"Converted {from_currency}->{to_currency} using explicit fixed rate {rate_applied}."
        if passed else f"Currency conversion {from_currency}->{to_currency} required but no rate was recorded."
    )
    return RuleResult("currency_conversion_explicit", passed, detail)


def check_extraction_not_failed(extraction_status: str) -> RuleResult:
    passed = extraction_status == "ok"
    detail = (
        "Extraction succeeded." if passed
        else "Extraction failed for one or more required fields; this assertion cannot be finalized as passed."
    )
    return RuleResult("extraction_not_failed", passed, detail)
