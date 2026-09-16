import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { Assertion, Engagement } from "../types";
import StatusBadge from "../components/StatusBadge";

export default function AssertionsList() {
  const [assertions, setAssertions] = useState<Assertion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const engs: Engagement[] = await api.listEngagements();
        const list = await api.listAssertions(engs[0].id);
        setAssertions(list);
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <div className="p-6 text-sm text-navy-700">Loading items to check…</div>;
  if (error) return <div className="p-6 text-sm text-fail">{error}</div>;

  return (
    <div className="p-6">
      <p className="text-sm text-navy-700/80 mb-4">Each row is a statement to check, such as whether an invoice matches the accounting records. Open a row to see the documents and calculations. Reading confidence describes how certain the system is about the amount read from a document; it is not a measure of audit quality.</p>
      <div className="panel overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-panel text-navy-700 text-xs uppercase tracking-wide">
            <tr>
              <th className="text-left px-4 py-2">Reference</th>
              <th className="text-left px-4 py-2">What is being checked</th>
              <th className="text-right px-4 py-2">Amount read</th>
              <th className="text-right px-4 py-2">Reading confidence</th>
              <th className="text-left px-4 py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {assertions.map((a) => (
              <tr key={a.id} className="border-t border-navy-900/5 hover:bg-stone-100">
                <td className="px-4 py-2 font-mono text-xs">{a.subject_key}</td>
                <td className="px-4 py-2">
                  <Link to={`/assertions/${a.id}`} className="text-accent hover:underline">
                    {a.label}
                  </Link>
                </td>
                <td className="px-4 py-2 text-right">
                  {a.extracted_value != null ? `$${a.extracted_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : "—"}
                </td>
                <td className="px-4 py-2 text-right">{(a.confidence * 100).toFixed(0)}%</td>
                <td className="px-4 py-2"><StatusBadge status={a.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
