"""Extraction provider interface.

A future LLM-backed provider (e.g. a Claude/GPT extraction service) can be
dropped in by implementing this same interface. The rest of the system only
depends on this contract, never on a specific provider's SDK.
"""
from abc import ABC, abstractmethod
from typing import List, TypedDict


class ExtractedField(TypedDict):
    entity_type: str
    raw_value: str
    confidence: float
    quote: str
    page_number: int
    extraction_status: str  # "ok" | "failed"


class ExtractionProvider(ABC):
    @abstractmethod
    def extract(self, document_fixture_key: str, pages: List[dict]) -> List[ExtractedField]:
        """Return a list of extracted fields for the given document's pages."""
        raise NotImplementedError
