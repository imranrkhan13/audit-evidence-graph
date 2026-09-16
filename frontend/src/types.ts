export interface Engagement {
  id: string;
  name: string;
  client_name: string;
  period_start: string;
  period_end: string;
  status: string;
}

export interface Dashboard {
  engagement: Engagement;
  total_assertions: number;
  passed: number;
  needs_review: number;
  failed: number;
  pending: number;
  exception_value: number;
  missing_evidence_count: number;
  workflow_stages: { stage: string; status: string; detail: string }[];
}

export interface Assertion {
  id: string;
  label: string;
  assertion_type: string;
  subject_key: string;
  extracted_value: number | null;
  confidence: number;
  status: string;
  material: boolean;
  updated_at: string;
}

export interface TieOutResult {
  id: string;
  rule_name: string;
  passed: boolean;
  detail: string;
  computed_value: number | null;
  expected_value: number | null;
  difference: number | null;
  is_current: boolean;
  created_at: string;
}

export interface EvidenceLink {
  id: string;
  document_id: string | null;
  document_title: string | null;
  page_number: number | null;
  relation: string;
}

export interface AssertionDetail extends Assertion {
  quote: string | null;
  primary_document_id: string | null;
  primary_page_number: number | null;
  tie_out_results: TieOutResult[];
  tie_out_history: TieOutResult[];
  evidence_links: EvidenceLink[];
  ledger_rows: { id: string; entry_date: string; account: string; reference: string; description: string; amount: number; currency: string }[];
  review_task: { id: string; reason: string; status: string; financial_impact: number; risk_level: string; last_decision: string | null; last_note: string | null } | null;
}

export interface ReviewTask {
  id: string;
  assertion_id: string;
  assertion_label: string;
  reason: string;
  financial_impact: number;
  risk_level: string;
  status: string;
  confidence: number;
  created_at: string;
}

export interface DocumentOut {
  id: string;
  doc_type: string;
  title: string;
  version: number;
  is_current: boolean;
  content_hash: string;
}

export interface DocumentPage {
  page_number: number;
  text_content: string;
  content_hash: string;
}

export interface AuditEvent {
  id: string;
  event_type: string;
  entity_type: string | null;
  entity_id: string | null;
  actor: string;
  summary: string;
  created_at: string;
}

export interface RiskFlag {
  reference: string;
  vendor: string;
  amount: number;
  entry_date: string;
  risk_score: number;
  signals: { code: string; label: string; weight: number }[];
  assertion_id: string | null;
}

export interface EvidenceSearchResult {
  document_id: string;
  document_title: string;
  page_number: number;
  score: number;
  snippet: string;
}
