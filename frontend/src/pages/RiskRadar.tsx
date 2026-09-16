import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, riskApi } from "../api";
import { Engagement, RiskFlag, EvidenceSearchResult } from "../types";

const RISK_COLOR = (score: number) => (score >= 40 ? "text-fail" : score >= 20 ? "text-review" : "text-navy-700");

export default function RiskRadar() {
  const [engagementId, setEngagementId] = useState<string | null>(null);
  const [flags, setFlags] = useState<RiskFlag[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<EvidenceSearchResult[] | null>(null);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const engs: Engagement[] = await api.listEngagements();
        const engId = engs[0].id;
        setEngagementId(engId);
        const radar = await riskApi.radar(engId);
        setFlags(radar);
      } catch (e: any) {
        setError(e.message);
      }
    })();
  }, []);

  async function runSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!engagementId || !query.trim()) return;
    setSearching(true);
    try {
      const results = await riskApi.searchEvidence(engagementId, query);
      setSearchResults(results);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSearching(false);
    }
  }

  if (error) return <div className="p-6 text-sm text-fail">{error}</div>;
  if (!engagementId) return <div className="p-6 text-sm text-navy-700">Loading risk radar…</div>;

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      <div className="panel p-5">
        <h2 className="text-sm font-semibold text-navy-900 mb-1">Transactions worth a closer look</h2>
        <p className="text-xs text-navy-700/60 mb-4">
          The app checks every sample accounting entry for unusual patterns, such as an unusually large
          amount or a new vendor. Higher scores appear first. A flag suggests where to look closer;
          it does not prove there is an error or change any saved result.
        </p>
        {flags.length === 0 ? (
          <p className="text-sm text-navy-700/70">No ledger entries triggered a risk signal.</p>
        ) : (
          <div className="space-y-2">
            {flags.map((f) => (
              <div key={f.reference} className="border border-navy-900/10 rounded p-3 flex items-start justify-between">
                <div>
                  <div className="text-sm font-medium text-navy-900">
                    {f.assertion_id ? (
                      <Link to={`/assertions/${f.assertion_id}`} className="text-accent hover:underline">
                        {f.reference}
                      </Link>
                    ) : (
                      f.reference
                    )}
                    <span className="text-navy-700/60 font-normal"> — {f.vendor}</span>
                  </div>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {f.signals.map((s) => (
                      <span key={s.code} className="text-[11px] bg-slate-panel px-2 py-0.5 rounded text-navy-700">
                        {s.label}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="text-right shrink-0 ml-4">
                  <div className={`text-lg font-semibold ${RISK_COLOR(f.risk_score)}`}>{f.risk_score}</div>
                  <div className="text-[11px] text-navy-700/50">risk score</div>
                  <div className="text-xs text-navy-700/70 mt-1">
                    ${f.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="panel p-5">
        <h2 className="text-sm font-semibold text-navy-900 mb-1">Find a document</h2>
        <p className="text-xs text-navy-700/60 mb-3">
          Type a vendor name, invoice reference, or a few words to find matching sample documents.
          Search helps you find things to read; it does not decide whether the numbers are correct.
        </p>
        <form onSubmit={runSearch} className="flex gap-2 mb-4">
          <input
            className="flex-1 border border-navy-900/20 rounded text-sm px-3 py-2"
            placeholder="e.g. Ferrostone Manufacturing invoice total"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button
            type="submit"
            disabled={searching}
            className="text-sm px-4 py-2 bg-navy-900 text-white rounded disabled:opacity-50"
          >
            {searching ? "Searching…" : "Search"}
          </button>
        </form>
        {searchResults && (
          <div className="space-y-2">
            {searchResults.length === 0 && <p className="text-sm text-navy-700/60">No matching evidence found.</p>}
            {searchResults.map((r, i) => (
              <div key={i} className="border-b border-navy-900/5 pb-2 last:border-0">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-navy-900">{r.document_title} (p.{r.page_number})</span>
                  <span className="text-xs text-navy-700/50">score {r.score.toFixed(3)}</span>
                </div>
                <p className="text-xs text-navy-700/70 mt-0.5 font-mono">{r.snippet}…</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
