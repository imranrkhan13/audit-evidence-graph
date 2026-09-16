import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api";
import { AssertionDetail as DetailType } from "../types";
import StatusBadge from "../components/StatusBadge";

export default function AssertionDetail() {
  const { id } = useParams();
  const [detail, setDetail] = useState<DetailType | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    api.getAssertion(id).then(setDetail).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="p-6 text-sm text-navy-700">Loading assertion…</div>;
  if (error) return <div className="p-6 text-sm text-fail">{error}</div>;
  if (!detail) return null;

  return (
    <div className="p-6 space-y-5 max-w-5xl">
      <div className="panel p-5">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-base font-semibold text-navy-900">{detail.label}</h2>
            <p className="text-xs text-navy-700/60 mt-1 font-mono">{detail.subject_key}</p>
          </div>
          <StatusBadge status={detail.status} />
        </div>
        <div className="grid grid-cols-3 gap-4 mt-4 text-sm">
          <div>
            <div className="text-xs text-navy-700/60">Extracted Value</div>
            <div className="font-semibold text-navy-900">
              {detail.extracted_value != null ? `$${detail.extracted_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : "—"}
            </div>
          </div>
          <div>
            <div className="text-xs text-navy-700/60">Confidence</div>
            <div className="font-semibold text-navy-900">{(detail.confidence * 100).toFixed(0)}%</div>
          </div>
          <div>
            <div className="text-xs text-navy-700/60">Source</div>
            {detail.primary_document_id ? (
              <Link to={`/documents/${detail.primary_document_id}`} className="text-accent hover:underline">
                Page {detail.primary_page_number}
              </Link>
            ) : (
              <span className="text-fail">No source document</span>
            )}
          </div>
        </div>
        {detail.quote && (
          <div className="mt-4 bg-amber-50 border border-review/30 rounded p-3 text-sm italic text-navy-900">
            "{detail.quote}"
          </div>
        )}
      </div>

      <div className="panel p-5">
        <h3 className="text-sm font-semibold text-navy-900 mb-3">Supporting documents and where they came from</h3>
        <ul className="space-y-2 text-sm">
          {detail.evidence_links.map((l) => (
            <li key={l.id} className="flex items-center justify-between border-b border-navy-900/5 pb-2 last:border-0">
              <span className="text-navy-700">{l.relation.replace(/_/g, " ")}</span>
              {l.document_id ? (
                <Link to={`/documents/${l.document_id}`} className="text-accent hover:underline">
                  {l.document_title} {l.page_number ? `(p.${l.page_number})` : ""}
                </Link>
              ) : (
                <span className="text-navy-700/50">—</span>
              )}
            </li>
          ))}
        </ul>
      </div>

      {detail.ledger_rows.length > 0 && (
        <div className="panel p-5">
          <h3 className="text-sm font-semibold text-navy-900 mb-3">Related accounting entries</h3>
          <table className="w-full text-sm">
            <thead className="text-xs uppercase text-navy-700/60">
              <tr>
                <th className="text-left py-1">Date</th>
                <th className="text-left py-1">Account</th>
                <th className="text-left py-1">Description</th>
                <th className="text-right py-1">Amount</th>
              </tr>
            </thead>
            <tbody>
              {detail.ledger_rows.map((r) => (
                <tr key={r.id} className="border-t border-navy-900/5">
                  <td className="py-1">{r.entry_date}</td>
                  <td className="py-1">{r.account}</td>
                  <td className="py-1">{r.description}</td>
                  <td className="py-1 text-right">${r.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="panel p-5">
        <h3 className="text-sm font-semibold text-navy-900 mb-3">What was checked and what happened</h3>
        <ul className="space-y-2 text-sm">
          {detail.tie_out_results.map((r) => (
            <li key={r.id} className="flex items-start gap-2">
              <span className={r.passed ? "text-pass" : "text-fail"}>{r.passed ? "✓" : "✗"}</span>
              <div>
                <div className="font-medium text-navy-900">{r.rule_name.replace(/_/g, " ")}</div>
                <div className="text-navy-700/70 text-xs">{r.detail}</div>
              </div>
            </li>
          ))}
        </ul>
        {detail.tie_out_history.length > 0 && (
          <details className="mt-4">
            <summary className="text-xs text-accent cursor-pointer">
              View {detail.tie_out_history.length} prior tie-out result(s) (history)
            </summary>
            <ul className="mt-2 space-y-2 text-sm">
              {detail.tie_out_history.map((r) => (
                <li key={r.id} className="text-navy-700/60 text-xs">
                  {r.created_at}: {r.rule_name.replace(/_/g, " ")} — {r.passed ? "passed" : "failed"} — {r.detail}
                </li>
              ))}
            </ul>
          </details>
        )}
      </div>

      <div className="panel p-5">
        <h3 className="text-sm font-semibold text-navy-900 mb-2">Reviewer Decision</h3>
        {detail.review_task ? (
          <div className="text-sm text-navy-700 space-y-1">
            <div>Reason: <span className="font-medium">{detail.review_task.reason.replace(/_/g, " ")}</span></div>
            <div>Risk: <span className="font-medium">{detail.review_task.risk_level}</span></div>
            <div>Financial impact: ${detail.review_task.financial_impact.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
            <div>Status: <span className="font-medium">{detail.review_task.status}</span></div>
            {detail.review_task.last_decision && (
              <div>Last decision: {detail.review_task.last_decision} {detail.review_task.last_note && `— "${detail.review_task.last_note}"`}</div>
            )}
          </div>
        ) : (
          <p className="text-sm text-navy-700/60">No review task was required for this assertion.</p>
        )}
      </div>
    </div>
  );
}
