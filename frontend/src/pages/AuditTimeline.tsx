import { useEffect, useState } from "react";
import { api } from "../api";
import { AuditEvent, Engagement } from "../types";

const EVENT_COLORS: Record<string, string> = {
  ingestion: "bg-slate-panel",
  extraction: "bg-blue-50",
  normalization: "bg-blue-50",
  tie_out: "bg-amber-50",
  review: "bg-amber-50",
  approval: "bg-green-50",
  export: "bg-slate-panel",
};

export default function AuditTimeline() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const engs: Engagement[] = await api.listEngagements();
        const ev = await api.auditEvents(engs[0].id);
        setEvents(ev);
      } catch (e: any) {
        setError(e.message);
      }
    })();
  }, []);

  if (error) return <div className="p-6 text-sm text-fail">{error}</div>;

  return (
    <div className="p-6 max-w-3xl">
      <div className="panel p-5">
        <h2 className="text-sm font-semibold text-navy-900 mb-1">Append-Only Audit Timeline</h2>
        <p className="text-xs text-navy-700/60 mb-4">
          Every extraction, normalization, tie-out, rerun, review, approval, and export event is recorded here
          and never overwritten.
        </p>
        <ol className="space-y-3">
          {events.map((e) => (
            <li key={e.id} className={`border-l-2 border-navy-900/10 pl-3 py-1 ${EVENT_COLORS[e.event_type] || ""}`}>
              <div className="flex items-center justify-between text-xs text-navy-700/60">
                <span className="uppercase tracking-wide font-medium">{e.event_type.replace(/_/g, " ")}</span>
                <span>{new Date(e.created_at).toLocaleString()}</span>
              </div>
              <div className="text-sm text-navy-900 mt-0.5">{e.summary}</div>
              <div className="text-[11px] text-navy-700/50">actor: {e.actor}</div>
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}
