"""Fixture extraction provider.

Returns pre-baked, deterministic "extraction" results for our synthetic
documents so the demo is fully reproducible offline with no model calls.
The FixtureExtractionProvider implements the same ExtractionProvider
interface a future LLM provider would use.
"""
from typing import List

from app.extraction.provider import ExtractionProvider, ExtractedField

# Keyed by the document's raw_fixture_key. Each entry is the list of fields
# our synthetic extraction "found" for that document, including a couple of
# intentionally low-confidence / failed fields to drive review routing.
FIXTURE_EXTRACTIONS: dict = {}


class FixtureExtractionProvider(ExtractionProvider):
    provider_name = "fixture-v1"

    def extract(self, document_fixture_key: str, pages: List[dict]) -> List[ExtractedField]:
        return FIXTURE_EXTRACTIONS.get(document_fixture_key, [])


def register_fixture(fixture_key: str, fields: List[ExtractedField]) -> None:
    FIXTURE_EXTRACTIONS[fixture_key] = fields
