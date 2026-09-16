from app.normalization import (
    normalize_invoice_id, normalize_vendor, normalize_currency,
    normalize_amount, normalize_date, convert_currency,
)


def test_normalize_invoice_id_ignores_separators_and_case():
    assert normalize_invoice_id("inv-2025-1001") == normalize_invoice_id("INV 2025 1001")
    assert normalize_invoice_id("INV-2025-1001") == "INV20251001"


def test_normalize_vendor_strips_suffix_and_case():
    assert normalize_vendor("Acme Robotics Inc.") == normalize_vendor("acme robotics")


def test_normalize_currency_symbols():
    assert normalize_currency("$") == "USD"
    assert normalize_currency("eur") == "EUR"


def test_normalize_amount_strips_symbols_and_commas():
    assert normalize_amount("$13,600.00") == 13600.00


def test_normalize_date_multiple_formats():
    assert normalize_date("2025-06-15") == "2025-06-15"
    assert normalize_date("06/15/2025") == "2025-06-15"
    assert normalize_date("not a date") is None


def test_convert_currency_explicit_rate():
    usd = convert_currency(100, "EUR", "USD")
    assert usd == 108.0


def test_convert_currency_same_currency_noop():
    assert convert_currency(50, "USD", "USD") == 50.0
