from app.anomaly import compute_risk_flags, APPROVAL_THRESHOLD


def _row(ref, vendor, amount, date="2025-06-16"):
    return {"reference": ref, "description": vendor, "amount": amount, "entry_date": date}


def test_outlier_amount_flagged_relative_to_vendor():
    rows = [
        _row("INV1", "Acme", 1000), _row("INV2", "Acme", 1050),
        _row("INV3", "Acme", 980), _row("INV4", "Acme", 50000),  # wildly out of line
    ]
    flags = compute_risk_flags(rows)
    outlier = next(f for f in flags if f.reference == "INV4")
    assert any(s.code == "amount_outlier" for s in outlier.signals)
    assert outlier.risk_score > 0


def test_near_approval_threshold_flagged():
    rows = [_row("INV5", "Vendor X", APPROVAL_THRESHOLD * 0.95)]
    flags = compute_risk_flags(rows)
    assert len(flags) == 1
    assert any(s.code == "near_approval_threshold" for s in flags[0].signals)


def test_round_number_flagged():
    rows = [_row("INV6", "Vendor Y", 8000.00)]
    flags = compute_risk_flags(rows)
    assert any(s.code == "round_number" for s in flags[0].signals)


def test_weekend_posting_flagged():
    rows = [_row("INV7", "Vendor Z", 1234.56, date="2025-06-14")]  # a Saturday
    flags = compute_risk_flags(rows)
    assert any(s.code == "weekend_posting" for s in flags[0].signals)


def test_first_time_vendor_flagged_only_when_alone():
    rows = [_row("INV8", "Lonely Vendor", 4999.00)]
    flags = compute_risk_flags(rows)
    assert any(s.code == "first_time_vendor" for s in flags[0].signals)


def test_clean_transaction_gets_no_flags():
    rows = [
        _row("INV9", "Vendor Q", 2000), _row("INV10", "Vendor Q", 2100),
        _row("INV11", "Vendor Q", 1950),
    ]
    flags = compute_risk_flags(rows)
    # amounts are close together, not round, not weekend, vendor repeats -> no flags for any
    assert flags == []


def test_results_sorted_highest_risk_first():
    rows = [
        _row("A", "V1", 100), _row("B", "V1", 110), _row("C", "V1", 9999999),
        _row("D", "V2", APPROVAL_THRESHOLD * 0.92),
    ]
    flags = compute_risk_flags(rows)
    scores = [f.risk_score for f in flags]
    assert scores == sorted(scores, reverse=True)
