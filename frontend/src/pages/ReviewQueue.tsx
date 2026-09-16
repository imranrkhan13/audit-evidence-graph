import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, currentRole } from "../api";
import { Engagement, ReviewTask } from "../types";

const SORT_OPTIONS = [
  { value: "financial_impact", label: "Financial Impact" },
  { value: "confidence", label: "Confidence" },
  { value: "risk", label: "Risk" },
  { value: "status", label: "Status" },
];

export default function ReviewQueue() {
  const [engagementId, setEngagementId] = useState<string | null>(null);
  const [tasks, setTasks] = useState<ReviewTask[]>([]);
  const [sortBy, setSortBy] = useState("financial_impact");
  const [statusFilter, setStatusFilter] = useState("open");
  const [error, setError] = useState<string | null>(null);
  const [noteDrafts, setNoteDrafts] = useState<Record<string, string>>({});
  const [busyTaskId, setBusyTaskId] = useState<string | null>(null);
  const role = currentRole();
  const canAct = role === "admin" || role === "reviewer";

  async function load() {
    try {
      const engs: Engagement[] = await api.listEngagements();
      const engId = engs[0].id;
      setEngagementId(engId);
      const q = await api.reviewQueue(engId, sortBy, statusFilter);
      setTasks(q);
    } catch (e: any) {
      setError(e.message);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sortBy, statusFilter]);

  async function act(taskId: string, decision: string) {
    setBusyTaskId(taskId);
    try {
      await api.actOnReview(taskId, decision, noteDrafts[taskId]);
      await load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusyTaskId(null);
    }
  }

  if (error) return <div className="p-6 text-sm text-fail">{error}</div>;
  if (!engagementId) return <div className="p-6 text-sm text-navy-700">Loading review queue…</div>;

  return (
    <div className="p-6 space-y-4">
      <p className="text-sm text-navy-700/80">These items need a person to review a difference, an uncertain value, or a missing document. Open an item to see the details. {canAct ? "Add a note and choose a decision below." : "You are signed in as an auditor. Use the reviewer demo account to approve, reject, or request more documents."}</p>
      <div className="flex items-center gap-4">
        <div>
          <label className="text-xs text-navy-700/60 mr-2">Sort by</label>
          <select
            className="border border-navy-900/20 rounded text-sm px-2 py-1"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            {SORT_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs text-navy-700/60 mr-2">Status</label>
          <select
            className="border border-navy-900/20 rounded text-sm px-2 py-1"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="open">Open</option>
            <option value="all">All</option>
          </select>
        </div>
      </div>

      {tasks.length === 0 && <div className="panel p-5 text-sm text-navy-700/70">No review tasks match this filter.</div>}

      <div className="space-y-3">
        {tasks.map((t) => (
          <div key={t.id} className="panel p-4">
            <div className="flex items-start justify-between">
              <div>
                <Link to={`/assertions/${t.assertion_id}`} className="text-accent hover:underline font-medium text-sm">
                  {t.assertion_label}
                </Link>
                <div className="text-xs text-navy-700/60 mt-1">
                  Reason: {t.reason.replace(/_/g, " ")} &nbsp;·&nbsp; Risk: <span className="uppercase">{t.risk_level}</span>
                  &nbsp;·&nbsp; Confidence: {(t.confidence * 100).toFixed(0)}% &nbsp;·&nbsp; Status: {t.status}
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm font-semibold text-fail">
                  ${t.financial_impact.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </div>
                <div className="text-[11px] text-navy-700/50">financial impact</div>
              </div>
            </div>
            {canAct && t.status === "open" && (
              <div className="mt-3 flex items-center gap-2">
                <input
                  className="flex-1 border border-navy-900/20 rounded text-sm px-2 py-1"
                  placeholder="Add a note (optional)"
                  value={noteDrafts[t.id] || ""}
                  onChange={(e) => setNoteDrafts({ ...noteDrafts, [t.id]: e.target.value })}
                />
                <button
                  disabled={busyTaskId === t.id}
                  onClick={() => act(t.id, "approve")}
                  className="text-xs px-3 py-1 rounded bg-pass text-white disabled:opacity-50"
                >
                  Approve
                </button>
                <button
                  disabled={busyTaskId === t.id}
                  onClick={() => act(t.id, "reject")}
                  className="text-xs px-3 py-1 rounded bg-fail text-white disabled:opacity-50"
                >
                  Reject
                </button>
                <button
                  disabled={busyTaskId === t.id}
                  onClick={() => act(t.id, "request_evidence")}
                  className="text-xs px-3 py-1 rounded bg-review text-white disabled:opacity-50"
                >
                  Request Evidence
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
