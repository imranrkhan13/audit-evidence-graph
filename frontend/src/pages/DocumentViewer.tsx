import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";
import { DocumentOut, DocumentPage } from "../types";

export default function DocumentViewer() {
  const { id } = useParams();
  const [doc, setDoc] = useState<DocumentOut | null>(null);
  const [pages, setPages] = useState<DocumentPage[]>([]);
  const [pageIndex, setPageIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    Promise.all([api.getDocument(id), api.getDocumentPages(id)])
      .then(([d, p]) => {
        setDoc(d);
        setPages(p);
      })
      .catch((e) => setError(e.message));
  }, [id]);

  if (error) return <div className="p-6 text-sm text-fail">{error}</div>;
  if (!doc || pages.length === 0) return <div className="p-6 text-sm text-navy-700">Loading document…</div>;

  const page = pages[pageIndex];

  return (
    <div className="p-6 max-w-4xl space-y-4">
      <div className="panel p-4 flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-navy-900">{doc.title}</h2>
          <p className="text-xs text-navy-700/60 mt-1">
            {doc.doc_type} &nbsp;·&nbsp; Version {doc.version} {doc.is_current ? "(current)" : "(superseded)"}
          </p>
        </div>
        <div className="text-right text-xs text-navy-700/60">
          <div>Content hash</div>
          <div className="font-mono">{doc.content_hash.slice(0, 16)}…</div>
        </div>
      </div>

      <div className="panel p-4">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs text-navy-700/60">Page {page.page_number} of {pages.length}</span>
          <div className="flex gap-2">
            <button
              disabled={pageIndex === 0}
              onClick={() => setPageIndex((i) => Math.max(0, i - 1))}
              className="text-xs px-2 py-1 border border-navy-900/20 rounded disabled:opacity-40"
            >
              Previous
            </button>
            <button
              disabled={pageIndex === pages.length - 1}
              onClick={() => setPageIndex((i) => Math.min(pages.length - 1, i + 1))}
              className="text-xs px-2 py-1 border border-navy-900/20 rounded disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
        <pre className="whitespace-pre-wrap text-sm bg-stone-100 p-4 rounded border border-navy-900/10 font-mono leading-relaxed">
          {page.text_content}
        </pre>
        <p className="text-[11px] text-navy-700/50 mt-2 font-mono">Page content hash: {page.content_hash.slice(0, 16)}…</p>
      </div>
    </div>
  );
}
