from app import tie_out


def test_invoice_equals_ledger_pass_within_tolerance():
    r = tie_out.check_invoice_equals_ledger(100.00, 100.005)
    assert r.passed


def test_invoice_equals_ledger_fails_outside_tolerance():
    r = tie_out.check_invoice_equals_ledger(100.00, 250.00)
    assert not r.passed
    assert r.difference == -150.00


def test_line_items_equal_total():
    assert tie_out.check_line_items_equal_total(99.99, 100.00).passed
    assert not tie_out.check_line_items_equal_total(80.00, 100.00).passed


def test_bank_txn_supports_payment_missing_txn_fails():
    r = tie_out.check_bank_txn_supports_payment(None, 100.00)
    assert not r.passed


def test_payment_date_in_period():
    assert tie_out.check_payment_date_in_period("2025-06-15", "2025-01-01", "2025-12-31").passed
    assert not tie_out.check_payment_date_in_period("2026-01-15", "2025-01-01", "2025-12-31").passed


def test_identities_match():
    assert tie_out.check_identities_match("ACME ROBOTICS", "acme robotics").passed
    assert not tie_out.check_identities_match("ACME ROBOTICS", "SUMMIT CONSULTING").passed


def test_duplicate_invoice_detected():
    ids = ["INV1001", "INV1002", "INV1001"]
    r = tie_out.check_duplicate_invoice("INV1001", ids)
    assert not r.passed
    r2 = tie_out.check_duplicate_invoice("INV1002", ids)
    assert r2.passed


def test_missing_evidence_flags_missing_invoice_and_approval():
    r = tie_out.check_missing_evidence(has_invoice=False, has_approval=False)
    assert not r.passed
    assert "invoice" in r.detail and "approval" in r.detail


def test_currency_conversion_requires_explicit_rate():
    r_missing = tie_out.check_currency_conversion_explicit("EUR", "USD", None)
    assert not r_missing.passed
    r_present = tie_out.check_currency_conversion_explicit("EUR", "USD", 1.08)
    assert r_present.passed
    r_same = tie_out.check_currency_conversion_explicit("USD", "USD", None)
    assert r_same.passed


def test_failed_extraction_never_passes():
    r = tie_out.check_extraction_not_failed("failed")
    assert not r.passed
    r_ok = tie_out.check_extraction_not_failed("ok")
    assert r_ok.passed
