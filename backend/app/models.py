import enum
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from itertools import count
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Enum, JSON
)
from sqlalchemy.orm import relationship

from app.database import Base


_seed_ids = ContextVar("seed_ids", default=None)


@contextmanager
def stable_demo_ids():
    """Keep fixture links and demo logins valid across serverless instances."""
    token = _seed_ids.set(count())
    try:
        yield
    finally:
        _seed_ids.reset(token)


def gen_id() -> str:
    sequence = _seed_ids.get()
    if sequence is not None:
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"audit-evidence-demo:v1:{next(sequence)}"))
    return str(uuid.uuid4())


class Role(str, enum.Enum):
    ADMIN = "admin"
    AUDITOR = "auditor"
    REVIEWER = "reviewer"


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=gen_id)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(Role), nullable=False)
    display_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Engagement(Base):
    __tablename__ = "engagements"
    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    client_name = Column(String, nullable=False)
    period_start = Column(String, nullable=False)
    period_end = Column(String, nullable=False)
    status = Column(String, default="in_progress")
    created_at = Column(DateTime, default=datetime.utcnow)

    documents = relationship("Document", back_populates="engagement")
    assertions = relationship("Assertion", back_populates="engagement")
    ledger_entries = relationship("LedgerEntry", back_populates="engagement")


class DocumentType(str, enum.Enum):
    INVOICE = "invoice"
    CONTRACT = "contract"
    BANK_STATEMENT = "bank_statement"
    APPROVAL = "approval"
    GENERAL_LEDGER = "general_ledger"


class Document(Base):
    __tablename__ = "documents"
    id = Column(String, primary_key=True, default=gen_id)
    engagement_id = Column(String, ForeignKey("engagements.id"), nullable=False)
    doc_type = Column(Enum(DocumentType), nullable=False)
    title = Column(String, nullable=False)
    version = Column(Integer, default=1)
    is_current = Column(Boolean, default=True)
    superseded_by_id = Column(String, ForeignKey("documents.id"), nullable=True)
    content_hash = Column(String, nullable=False)
    raw_fixture_key = Column(String, nullable=False)  # points to synthetic fixture source
    created_at = Column(DateTime, default=datetime.utcnow)

    engagement = relationship("Engagement", back_populates="documents")
    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")


class DocumentPage(Base):
    __tablename__ = "document_pages"
    id = Column(String, primary_key=True, default=gen_id)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    text_content = Column(Text, nullable=False)
    tables_json = Column(JSON, default=list)  # list of table dicts, synthetic
    content_hash = Column(String, nullable=False)

    document = relationship("Document", back_populates="pages")


class ExtractedEntity(Base):
    __tablename__ = "extracted_entities"
    id = Column(String, primary_key=True, default=gen_id)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    entity_type = Column(String, nullable=False)  # invoice_id, vendor, amount, date, currency, etc.
    raw_value = Column(String, nullable=False)
    normalized_value = Column(String, nullable=True)
    confidence = Column(Float, nullable=False)
    quote = Column(Text, nullable=False)  # exact extracted quote
    extraction_status = Column(String, default="ok")  # ok | failed
    provider = Column(String, default="fixture-v1")
    created_at = Column(DateTime, default=datetime.utcnow)


class Assertion(Base):
    __tablename__ = "assertions"
    id = Column(String, primary_key=True, default=gen_id)
    engagement_id = Column(String, ForeignKey("engagements.id"), nullable=False)
    label = Column(String, nullable=False)  # e.g. "Accounts receivable is $1.24M"
    assertion_type = Column(String, nullable=False)  # invoice_ledger_match, ar_balance, etc.
    subject_key = Column(String, nullable=False)  # e.g. invoice number this assertion is about
    extracted_value = Column(Float, nullable=True)
    confidence = Column(Float, nullable=False)
    status = Column(String, default="pending")  # pending|pass|fail|needs_review
    material = Column(Boolean, default=True)
    primary_document_id = Column(String, ForeignKey("documents.id"), nullable=True)
    primary_page_number = Column(Integer, nullable=True)
    quote = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    engagement = relationship("Engagement", back_populates="assertions")


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    id = Column(String, primary_key=True, default=gen_id)
    engagement_id = Column(String, ForeignKey("engagements.id"), nullable=False)
    entry_date = Column(String, nullable=False)
    account = Column(String, nullable=False)
    reference = Column(String, nullable=False)  # invoice number etc
    description = Column(String, nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")

    engagement = relationship("Engagement", back_populates="ledger_entries")


class EvidenceLink(Base):
    __tablename__ = "evidence_links"
    id = Column(String, primary_key=True, default=gen_id)
    assertion_id = Column(String, ForeignKey("assertions.id"), nullable=False)
    document_id = Column(String, ForeignKey("documents.id"), nullable=True)
    page_number = Column(Integer, nullable=True)
    ledger_entry_id = Column(String, ForeignKey("ledger_entries.id"), nullable=True)
    entity_id = Column(String, ForeignKey("extracted_entities.id"), nullable=True)
    relation = Column(String, nullable=False)  # source_document, supporting_ledger_entry, related_bank_txn, etc.
    created_at = Column(DateTime, default=datetime.utcnow)


class TieOutRun(Base):
    __tablename__ = "tie_out_runs"
    id = Column(String, primary_key=True, default=gen_id)
    engagement_id = Column(String, ForeignKey("engagements.id"), nullable=False)
    triggered_by = Column(String, nullable=False)  # user id or "system"
    reason = Column(String, default="initial")  # initial | rerun_on_document_change
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class TieOutResult(Base):
    __tablename__ = "tie_out_results"
    id = Column(String, primary_key=True, default=gen_id)
    tie_out_run_id = Column(String, ForeignKey("tie_out_runs.id"), nullable=False)
    assertion_id = Column(String, ForeignKey("assertions.id"), nullable=False)
    rule_name = Column(String, nullable=False)
    passed = Column(Boolean, nullable=False)
    detail = Column(Text, nullable=False)
    computed_value = Column(Float, nullable=True)
    expected_value = Column(Float, nullable=True)
    difference = Column(Float, nullable=True)
    is_current = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ReviewTask(Base):
    __tablename__ = "review_tasks"
    id = Column(String, primary_key=True, default=gen_id)
    assertion_id = Column(String, ForeignKey("assertions.id"), nullable=False)
    reason = Column(String, nullable=False)  # low_confidence | contradictory | missing_evidence | material_exception
    financial_impact = Column(Float, default=0.0)
    risk_level = Column(String, default="medium")  # low|medium|high
    status = Column(String, default="open")  # open|approved|rejected|evidence_requested
    assigned_role = Column(String, default="reviewer")
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class Approval(Base):
    __tablename__ = "approvals"
    id = Column(String, primary_key=True, default=gen_id)
    review_task_id = Column(String, ForeignKey("review_tasks.id"), nullable=False)
    reviewer_id = Column(String, ForeignKey("users.id"), nullable=False)
    decision = Column(String, nullable=False)  # approve|reject|request_evidence
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"
    id = Column(String, primary_key=True, default=gen_id)
    engagement_id = Column(String, ForeignKey("engagements.id"), nullable=False)
    stage = Column(String, nullable=False)  # ingestion|extraction|normalization|tie_out|export
    status = Column(String, default="completed")  # running|completed|failed
    detail = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(String, primary_key=True, default=gen_id)
    engagement_id = Column(String, ForeignKey("engagements.id"), nullable=False)
    event_type = Column(String, nullable=False)
    # ingestion|extraction|normalization|tie_out|rerun|review|approval|export
    entity_type = Column(String, nullable=True)  # e.g. "assertion", "document"
    entity_id = Column(String, nullable=True)
    actor = Column(String, nullable=False)  # user id or "system"
    summary = Column(Text, nullable=False)
    payload_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
