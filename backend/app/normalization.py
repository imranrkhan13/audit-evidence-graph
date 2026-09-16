"""Deterministic normalization helpers.

These are pure functions with no ML/LLM involvement — every financial
tie-out decision in this system rests on deterministic Python logic,
never on model output.
"""
import re
from datetime import datetime
from typing import Optional


def normalize_invoice_id(raw: str) -> str:
    """Upper-case, strip whitespace, drop separators so INV-0001 == inv 0001."""
    cleaned = re.sub(r"[\s\-_]", "", raw.strip().upper())
    return cleaned


def normalize_vendor(raw: str) -> str:
    """Collapse whitespace, strip common corporate suffixes, upper-case for matching."""
    v = re.sub(r"\s+", " ", raw.strip())
    v = re.sub(r"\b(inc\.?|llc\.?|ltd\.?|corp\.?)\b", "", v, flags=re.IGNORECASE)
    v = v.strip(" .,").strip()
    return v.upper()


def normalize_currency(raw: str) -> str:
    mapping = {"$": "USD", "usd": "USD", "us dollar": "USD", "€": "EUR", "eur": "EUR", "£": "GBP", "gbp": "GBP"}
    key = raw.strip().lower()
    return mapping.get(key, raw.strip().upper())


def normalize_amount(raw: str) -> float:
    """Strip currency symbols/commas and parse to float. Raises ValueError on bad input."""
    cleaned = re.sub(r"[,$€£\s]", "", raw.strip())
    return round(float(cleaned), 2)


def normalize_date(raw: str) -> Optional[str]:
    """Try a handful of common formats and return ISO 8601 (YYYY-MM-DD), or None if unparseable."""
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%b %d, %Y", "%B %d, %Y", "%d-%b-%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(raw.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def convert_currency(amount: float, from_currency: str, to_currency: str) -> float:
    """Explicit, fixed synthetic conversion table for the demo (no live FX call).

    All conversions are logged with their rate so the calculation is auditable.
    """
    if from_currency == to_currency:
        return round(amount, 2)
    rates_to_usd = {"USD": 1.0, "EUR": 1.08, "GBP": 1.27}
    if from_currency not in rates_to_usd or to_currency not in rates_to_usd:
        raise ValueError(f"No fixed synthetic rate available for {from_currency}->{to_currency}")
    usd_amount = amount * rates_to_usd[from_currency]
    return round(usd_amount / rates_to_usd[to_currency], 2)
