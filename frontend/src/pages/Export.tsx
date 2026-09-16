import { useEffect, useState } from "react";
import { api } from "../api";
import { Engagement } from "../types";

export default function Export() {
  const [engagement, setEngagement] = useState<Engagement | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [prepared, setPrepared] = useState<{ url: string; filename: string } | null>(null);

  useEffect(() => () => {
    if (prepared) URL.revokeObjectURL(prepared.url);
  }, [prepared]);

  useEffect(() => {
    api.listEngagements()
      .then((engs: Engagement[]) => engs.length ? setEngagement(engs[0]) : setError("There is no sample audit project to export yet."))
      .catch(e => setError(e.message));
  }, []);

  async function download(format: "json" | "html") {
    if (!engagement) return;
    setBusy(true);
    setError("");
    setPrepared(null);
    try {
      // Fetch through the authenticated API; direct links cannot send the sign-in token.
      const report = await api.exportReport(engagement.id, format);
      const content = format === "json" ? JSON.stringify(report, null, 2) : report;
      const blob = new Blob([content], { type: format === "json" ? "application/json" : "text/html" });
      const url = URL.createObjectURL(blob);
      setPrepared({ url, filename: `sample-audit-report.${format}` });
    } catch (e) {
      setError(e instanceof Error ? e.message : "The report could not be downloaded. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return <div className="p-6 max-w-2xl space-y-4">
    <div className="panel p-5">
      <h2 className="text-base font-semibold text-navy-900 mb-2">Download reports</h2>
      <p className="text-sm text-navy-700/70 mb-4">Save the checked items, their supporting documents, and any reviewer decisions. All records are made-up examples.</p>
      {error && <p role="alert" className="text-sm text-fail mb-4">{error}</p>}
      {!engagement && !error && <p role="status">Loading your sample project…</p>}
      <div className="flex flex-wrap gap-3">
        <button onClick={() => download("json")} disabled={busy || !engagement} className="text-sm px-4 py-2 bg-navy-900 text-white rounded disabled:opacity-50">Prepare data file (JSON)</button>
        <button onClick={() => download("html")} disabled={busy || !engagement} className="text-sm px-4 py-2 border border-navy-900/30 text-navy-900 rounded disabled:opacity-50">Prepare printable report (HTML)</button>
      </div>
      {busy && <p role="status" className="text-sm mt-3">Preparing your download…</p>}
      {prepared && <div className="mt-4 p-4 border border-pass/30 bg-green-50 rounded">
        <p role="status" className="text-sm text-navy-900 mb-2">Your report is ready. Use the link below to save it.</p>
        <a href={prepared.url} download={prepared.filename} className="text-sm text-accent underline">Save {prepared.filename} ↓</a>
      </div>}
      <p className="text-xs text-navy-700/70 mt-4">For an easy-to-read report, choose HTML. Open the downloaded file in your browser and use Print. JSON is a data format for other software.</p>
    </div>
  </div>;
}
