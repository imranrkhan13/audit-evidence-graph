import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, impactApi } from "../api";
import Icon from "../components/Icon";

type Source = { id: string; title: string; doc_type: string; version: number };

export default function Documents() {
  const [documents, setDocuments] = useState<Source[]>([]);
  const [query, setQuery] = useState("");
  const [type, setType] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const projects = await api.listEngagements();
        const docs = projects.length ? await impactApi.documents(projects[0].id) : [];
        if (active) setDocuments(docs);
      } catch (e) { if (active) setError(e instanceof Error ? e.message : "Could not load documents."); }
      finally { if (active) setLoading(false); }
    })();
    return () => { active = false; };
  }, []);
  const visible = documents.filter(doc => doc.title.toLowerCase().includes(query.toLowerCase()) && (type === "all" || doc.doc_type === type));
  return <div className="app-page">
    <div className="app-page-heading"><div><p className="app-eyebrow">YOUR SOURCE RECORDS</p><h1>Documents</h1><p>Browse the current version of every document in the sample project.</p></div><span className="subtle-label">{documents.length} documents</span></div>
    <div className="document-filters"><label className="search-field"><Icon name="search" size={18}/><input aria-label="Search documents" placeholder="Search by title or invoice number…" value={query} onChange={event => setQuery(event.target.value)}/></label><select aria-label="Document type" value={type} onChange={event => setType(event.target.value)}><option value="all">All document types</option>{[...new Set(documents.map(doc => doc.doc_type))].map(value => <option key={value} value={value}>{value.replace(/_/g, " ")}</option>)}</select></div>
    {error && <p role="alert" className="app-error">{error}</p>}
    {loading ? <p role="status" className="app-loading">Loading documents…</p> : <div className="document-list">{visible.map(doc => <Link key={doc.id} to={`/documents/${doc.id}`} className="document-list-row"><span className="document-list-icon"><Icon name="documents"/></span><div><strong>{doc.title}</strong><small>{doc.doc_type.replace(/_/g, " ")} · Version {doc.version}</small></div><Icon name="arrow" size={18}/></Link>)}{!visible.length && !error && <p className="app-loading">{documents.length ? "No documents match your search." : "No sample documents are available yet."}</p>}</div>}
  </div>;
}
