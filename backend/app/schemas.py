from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    display_name: str


class EngagementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    client_name: str
    period_start: str
    period_end: str
    status: str


class DashboardOut(BaseModel):
    engagement: EngagementOut
    total_assertions: int
    passed: int
    needs_review: int
    failed: int
    pending: int
    exception_value: float
    missing_evidence_count: int
    workflow_stages: List[dict]


class TieOutResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    rule_name: str
    passed: bool
    detail: str
    computed_value: Optional[float] = None
    expected_value: Optional[float] = None
    difference: Optional[float] = None
    is_current: bool
    created_at: datetime


class EvidenceLinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    document_id: Optional[str] = None
    document_title: Optional[str] = None
    page_number: Optional[int] = None
    relation: str


class AssertionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    label: str
    assertion_type: str
    subject_key: str
    extracted_value: Optional[float] = None
    confidence: float
    status: str
    material: bool
    updated_at: datetime


class AssertionDetailOut(AssertionOut):
    quote: Optional[str] = None
    primary_document_id: Optional[str] = None
    primary_page_number: Optional[int] = None
    tie_out_results: List[TieOutResultOut] = []
    tie_out_history: List[TieOutResultOut] = []
    evidence_links: List[EvidenceLinkOut] = []
    ledger_rows: List[dict] = []
    review_task: Optional[dict] = None


class ReviewTaskOut(BaseModel):
    id: str
    assertion_id: str
    assertion_label: str
    reason: str
    financial_impact: float
    risk_level: str
    status: str
    confidence: float
    created_at: datetime


class ReviewActionIn(BaseModel):
    decision: str  # approve | reject | request_evidence
    note: Optional[str] = None


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    doc_type: str
    title: str
    version: int
    is_current: bool
    content_hash: str


class DocumentPageOut(BaseModel):
    page_number: int
    text_content: str
    content_hash: str


class AuditEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    event_type: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    actor: str
    summary: str
    created_at: datetime
