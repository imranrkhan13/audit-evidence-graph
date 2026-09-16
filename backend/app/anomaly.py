"""Deterministic, statistical risk-signal detection over ledger entries.

This is the "continuous monitoring" layer Modus describes publicly: instead
of a periodic, sample-based review, every ledger entry is scored on a small
set of transparent, explainable statistical rules every time this runs, and
the highest-risk items are surfaced first. Every signal below is a plain
Python computation over the numbers already in the database — nothing here
is a model prediction, and nothing here decides a tie-out. It only decides
*where a human's attention should go first*.
"""
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from typing import List

APPROVAL_THRESHOLD = 10000.00  # synthetic, fixture threshold used for the "near-threshold" signal


@dataclass
class RiskSignal:
    code: str
    label: str
    weight: int


@dataclass
class RiskFlag:
    reference: str
    vendor: str
    amount: float
    entry_date: str
    risk_score: int
    signals: List[RiskSignal] = field(default_factory=list)


def _is_weekend(date_str: str) -> bool:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").weekday() >= 5
    except ValueError:
        return False


def compute_risk_flags(ledger_rows: list) -> List[RiskFlag]:
    """ledger_rows: list of objects/dicts with .reference/.description(vendor)/.amount/.entry_date

    Groups by vendor to compute a per-vendor z-score, then applies four
    additional flat rules. Returns every entry with risk_score > 0, sorted
    highest risk first — this ordering is what "allocate judgment to the
    areas that carry the most risk" means in code.
    """
    by_vendor: dict = {}
    for idx, r in enumerate(ledger_rows):
        by_vendor.setdefault(r["description"], []).append(idx)

    results = []
    for idx, r in enumerate(ledger_rows):
        signals = []
        vendor = r["description"]
        amount = r["amount"]

        # Leave-one-out z-score: compare this amount to the OTHER entries for
        # the same vendor, so one outlier can't inflate its own baseline.
        other_indices = [i for i in by_vendor.get(vendor, []) if i != idx]
        if len(other_indices) >= 3:  # require a reasonable baseline before scoring an outlier
            other_amounts = [ledger_rows[i]["amount"] for i in other_indices]
            mean = statistics.mean(other_amounts)
            stdev = statistics.pstdev(other_amounts) or 1e-9
            z = (amount - mean) / stdev
            if abs(z) >= 2.0:
                signals.append(RiskSignal(
                    "amount_outlier", f"Amount is a statistical outlier for this vendor (z={z:.2f})", 40))

        if amount >= 5000 and amount % 1000 == 0:
            signals.append(RiskSignal("round_number", "Suspiciously round amount", 15))

        if 0.90 * APPROVAL_THRESHOLD <= amount < APPROVAL_THRESHOLD:
            signals.append(RiskSignal(
                "near_approval_threshold",
                f"Just under the ${APPROVAL_THRESHOLD:,.0f} approval threshold", 25))

        if _is_weekend(r["entry_date"]):
            signals.append(RiskSignal("weekend_posting", "Posted on a weekend", 10))

        if len(by_vendor.get(vendor, [])) == 1:
            signals.append(RiskSignal("first_time_vendor", "First transaction from this vendor in the period", 10))

        score = min(100, sum(s.weight for s in signals))
        if score > 0:
            results.append(RiskFlag(
                reference=r["reference"], vendor=vendor, amount=amount,
                entry_date=r["entry_date"], risk_score=score, signals=signals,
            ))

    results.sort(key=lambda f: f.risk_score, reverse=True)
    return results
