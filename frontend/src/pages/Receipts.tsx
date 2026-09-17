import { useEffect, useRef, useState } from "react";
import { receiptApi } from "../api";
import Icon from "../components/Icon";
import { useReceipts } from "../components/ReceiptWorkspace";
import { receiptChecks, receiptCsv, receiptExport } from "../receipts";
import type { ReceiptData, ReceiptRecord, ReceiptResult } from "../receipts";
import "../receipts.css";

const MAX_BYTES = 3 * 1024 * 1024;
const allowed = ["image/jpeg", "image/png", "image/webp", "application/pdf"];
function DownloadLink({contents, filename, mime, primary, children}: {contents:string; filename:string; mime:string; primary?:boolean; children:React.ReactNode}) {
  const [url,setUrl] = useState("");
  useEffect(()=>{
    const next = URL.createObjectURL(new Blob([contents],{type:mime})); setUrl(next);
    return ()=>URL.revokeObjectURL(next);
  },[contents,mime]);
  return <a className={`app-button ${primary ? "primary" : ""}`} href={url || undefined} download={filename}>{children}</a>;
}

export default function Receipts() {
  const {records,setRecords} = useReceipts();
  const [selected,setSelected] = useState(records[0]?.id || "");
  const [file,setFile] = useState<File|null>(null);
  const [consent,setConsent] = useState(false);
  const [enabled,setEnabled] = useState<boolean|null>(null);
  const [statusError,setStatusError] = useState("");
  const [error,setError] = useState("");
  const [busy,setBusy] = useState(false);
  const [elapsed,setElapsed] = useState(0);
  const [preview,setPreview] = useState("");
  const [dropActive,setDropActive] = useState(false);
  const [confirmDelete,setConfirmDelete] = useState(false);
  const upload = useRef<HTMLInputElement>(null);
  const controller = useRef<AbortController|null>(null);
  const record = records.find(r => r.id === selected) || records[0];
  const previewFile = file || record?.file;
  const loadStatus = () => { setStatusError(""); setEnabled(null); receiptApi.status().then(data=>setEnabled(data.enabled)).catch(()=>setStatusError("Could not connect to the receipt reader. Please try again.")); };
  useEffect(() => { loadStatus(); return () => controller.current?.abort(); }, []);
  useEffect(() => {
    if (!previewFile) { setPreview(""); return; }
    const url = URL.createObjectURL(previewFile); setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [previewFile]);
  useEffect(() => {
    if (!busy) {setElapsed(0); return;}
    const timer = setInterval(()=>setElapsed(v=>v+1),1000);
    return ()=>clearInterval(timer);
  }, [busy]);
  const choose = (candidate?: File) => {
    if (!candidate || busy) return;
    setError(""); setConfirmDelete(false); setConsent(false);
    if (!allowed.includes(candidate.type)) {setError("Choose a JPG, PNG, WebP or PDF file."); return;}
    if (!candidate.size || candidate.size > MAX_BYTES) {setError("Choose a file between 1 byte and 3 MB."); return;}
    setFile(candidate);
  };
  async function extract() {
    if (!file || !consent || !enabled || busy) return;
    if (records.length >= 10) {setError("You have 10 receipts in this tab. Download and remove one before adding another."); return;}
    setError(""); setBusy(true);
    const abort = new AbortController(); controller.current = abort;
    const timeout = setTimeout(()=>abort.abort(),65000);
    try {
      const fingerprint = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", await file.arrayBuffer()))).map(byte=>byte.toString(16).padStart(2,"0")).join("");
      if (records.some(r=>r.fingerprint === fingerprint)) {setError("This receipt is already in your list. Open it below to review it."); return;}
      const result: ReceiptResult = await receiptApi.extract(file,abort.signal);
      if (!result.receipt.receipt_detected) {setError("This does not look like a readable receipt or invoice. Try a clear photo of one receipt."); return;}
      if (records.some(r=>r.fingerprint === result.file_sha256)) {setError("This receipt is already in your list. Open it below to review it."); return;}
      const id = crypto.randomUUID();
      const newRecord: ReceiptRecord = {id,filename:file.name,file,extractedAt:new Date().toISOString(),original:structuredClone(result.receipt),edited:structuredClone(result.receipt),fingerprint:result.file_sha256,reviewed:false,expected:""};
      setRecords(current=>[newRecord,...current]); setSelected(id); setFile(null); setConsent(false);
    } catch (e) {setError(e instanceof Error && e.name === "AbortError" ? "Reading was stopped. You can try again; no result was saved." : e instanceof Error ? e.message : "Could not read this receipt. Please try again.");}
    finally {clearTimeout(timeout); setBusy(false); controller.current=null;}
  }
  const change = (update: Partial<ReceiptRecord>) => record && setRecords(current=>current.map(r=>r.id === record.id ? {...r,...update} : r));
  const field = (name: keyof ReceiptData, value: string) => record && change({edited:{...record.edited,[name]:value.trim() ? value : null},reviewed:false});
  const fields: {key: keyof ReceiptData; label:string; numeric?:boolean}[] = [
    {key:"merchant",label:"Store or vendor"},{key:"date",label:"Receipt date"},{key:"receipt_number",label:"Receipt number"},{key:"currency",label:"Currency (for example, USD)"},
    {key:"subtotal",label:"Subtotal",numeric:true},{key:"tax",label:"Tax added",numeric:true},{key:"tip",label:"Tip",numeric:true},{key:"discount",label:"Discount",numeric:true},{key:"total",label:"Total",numeric:true},
  ];
  const checks = record ? receiptChecks(record.edited,record.expected) : [];
  return <div className="app-page receipts-page">
    <div className="app-page-heading"><div><p className="app-eyebrow">YOUR OWN DOCUMENTS</p><h1>Read a receipt</h1><p>Turn a receipt into details you can check, correct and download.</p></div><span className="receipt-provider"><i/> Powered by Interfaze</span></div>
    <div className="receipt-privacy"><Icon name="documents" size={20}/><p><strong>Your receipts stay out of the shared demo.</strong> Files go through this server to Interfaze for reading, with its zero-retention option requested. This app does not save your file or result on the server. Results remain in this tab until you refresh, close it, sign out or remove them. Download a copy to keep them.</p></div>
    <div className="receipt-layout">
      <section className="workspace-card receipt-upload">
        <div className="card-heading"><div><h2>1. Choose a receipt</h2><p>One receipt or invoice per file.</p></div><Icon name="documents"/></div>
        <div className={`receipt-drop ${dropActive ? "drag-active" : ""}`} onDragOver={e=>{e.preventDefault();setDropActive(true);}} onDragLeave={()=>setDropActive(false)} onDrop={e=>{e.preventDefault();setDropActive(false);choose(e.dataTransfer.files[0]);}}>
          <span className="receipt-upload-symbol"><Icon name="documents" size={28}/></span>
          <strong>{file ? file.name : "Drop a receipt here"}</strong><p>{file ? `${(file.size/1024).toFixed(0)} KB · Ready to read` : "A clear photo works best. Keep every edge in view."}</p>
          <button type="button" className="app-button" disabled={busy} onClick={()=>upload.current?.click()}>{file ? "Choose another file" : "Choose a file"}</button>
          <input ref={upload} type="file" aria-label="Upload receipt" accept="image/jpeg,image/png,image/webp,application/pdf" hidden onChange={e=>{choose(e.target.files?.[0]);e.target.value="";}}/>
          <small>JPG, PNG, WebP or PDF · Up to 3 MB · PDFs up to 3 pages</small>
        </div>
        <div className="receipt-upload-controls">
          {statusError && <p className="receipt-error" role="alert">{statusError} <button onClick={loadStatus}>Retry connection</button></p>}
          {enabled === false && <p className="receipt-error" role="status">Receipt reading is currently unavailable. Please try again later.</p>}
          <label className="receipt-consent"><input type="checkbox" checked={consent} disabled={busy || !file} onChange={e=>setConsent(e.target.checked)}/><span>I can share this receipt with Interfaze to read it. <a href="https://interfaze.ai/docs/security" target="_blank" rel="noreferrer">How it handles data ↗</a></span></label>
          <button className="app-button primary receipt-read" disabled={!file || !consent || !enabled || busy} onClick={extract}>{busy ? `Reading your receipt… ${elapsed}s` : enabled === null && !statusError ? "Connecting to reader…" : "Extract receipt details"}<Icon name="arrow" size={17}/></button>
          {busy && <p role="status" className="receipt-hint">This usually takes a few seconds. Stay on this page. <button onClick={()=>controller.current?.abort()}>Cancel</button></p>}
          {error && <p role="alert" className="receipt-error">{error}</p>}
          <p className="receipt-hint">AI can misread a faded number or a date. Always compare the result with the original.</p>
        </div>
        {preview && <div className="receipt-preview"><div><strong>{file ? "Selected file" : "Original receipt"}</strong><a href={preview} target="_blank" rel="noreferrer">Open original ↗</a></div>{previewFile?.type.startsWith("image/") ? <img src={preview} alt="Receipt selected for review"/> : <p>PDF selected. Use “Open original” to view it in your browser.</p>}</div>}
      </section>
      <section className="workspace-card receipt-result">
        <div className="card-heading"><div><h2>2. Review the details</h2><p>{record ? "Edit anything that does not match your receipt." : "The fields will appear after extraction."}</p></div>{record && <span className={`receipt-status ${record.reviewed ? "reviewed" : ""}`}>{record.reviewed ? "Reviewed by you" : "Needs your review"}</span>}</div>
        {!record ? <div className="receipt-empty"><Icon name="checks" size={46}/><h3>From a photo to useful numbers</h3><p>Store name, date, taxes, total and line items—ready for you to check.</p><ol><li>Choose a receipt and allow extraction.</li><li>Compare the fields with the original.</li><li>Download a JSON report or a CSV for spreadsheets.</li></ol></div> : <div className="receipt-result-body">
          <p className="receipt-filename">{record.filename}</p>
          {file && <p className="receipt-hint">You selected a new file on the left. These fields still belong to {record.filename}.</p>}
          <div className="receipt-fields">{fields.map(f=><label key={f.key} className={f.key === "total" ? "receipt-total" : ""}><span>{f.label}</span><input type={f.numeric ? "number" : "text"} step={f.numeric ? "any" : undefined} value={String(record.edited[f.key] ?? "")} placeholder="Not found — check original" maxLength={f.numeric ? undefined : 240} onChange={e=>field(f.key,e.target.value)}/></label>)}</div>
          {record.original.warnings.length > 0 && <div className="receipt-warnings"><strong>The reader wants you to check</strong><ul>{record.original.warnings.map((warning,i)=><li key={i}>{warning}</li>)}</ul></div>}
          <div className="receipt-section-title"><h3>Line items</h3><span>{record.edited.items.length} found</span></div>
          {record.edited.items.length ? <div className="receipt-table-wrap"><table className="receipt-items"><thead><tr><th>Description</th><th>Qty</th><th>Unit price</th><th>Amount</th></tr></thead><tbody>{record.edited.items.map((item,i)=><tr key={i}>{(["description","quantity","unit_price","amount"] as const).map(key=><td key={key}><input aria-label={`Item ${i+1} ${key.replace("_"," ")}`} type={key === "description" ? "text" : "number"} step="any" value={item[key] ?? ""} onChange={e=>change({edited:{...record.edited,items:record.edited.items.map((line,index)=>index===i ? {...line,[key]:e.target.value || (key === "description" ? "" : null)} : line)},reviewed:false})}/></td>)}</tr>)}</tbody></table></div> : <p className="receipt-hint">No line items could be read. Check the original receipt.</p>}
          <div className="receipt-section-title"><h3>3. Check the numbers</h3><span>Simple arithmetic</span></div>
          <label className="receipt-expected"><span>Expected total, if you know it ({record.edited.currency || "same currency as receipt"})</span><input type="number" step="any" placeholder="Optional: amount in your records" value={record.expected} onChange={e=>change({expected:e.target.value,reviewed:false})}/></label>
          <div className="receipt-checks">{checks.map(check=><div className={`receipt-check ${check.status}`} key={check.label}><span>{check.status === "pass" ? "✓" : check.status === "review" ? "!" : "—"}</span><div><strong>{check.label}</strong><p>{check.detail}</p></div></div>)}</div>
          <p className="receipt-hint">Blank tax, tip and discount count as zero. Comparisons use a 0.01 tolerance and do not prove the receipt is valid. No bank or accounting system is connected.</p>
          <label className="receipt-consent receipt-reviewed"><input type="checkbox" checked={record.reviewed} onChange={e=>change({reviewed:e.target.checked})}/><span>I compared these details with the original receipt.</span></label>
          <div className="receipt-actions"><DownloadLink contents={JSON.stringify(receiptExport(record),null,2)} filename="receipt-report.json" mime="application/json" primary>Download JSON <Icon name="download" size={16}/></DownloadLink><DownloadLink contents={receiptCsv([record])} filename="receipt.csv" mime="text/csv;charset=utf-8">Download CSV <Icon name="download" size={16}/></DownloadLink></div>
          <details className="receipt-transcript"><summary>Text read from the receipt</summary><pre>{record.original.source_text || "No readable text returned."}</pre></details>
        </div>}
      </section>
    </div>
    {records.length > 0 && <section className="workspace-card receipt-history"><div className="card-heading"><div><h2>Receipts in this tab</h2><p>{records.length} of 10 · Removed when you refresh, close the tab or sign out.</p></div><DownloadLink contents={receiptCsv(records)} filename="receipts.csv" mime="text/csv;charset=utf-8">Export all CSV</DownloadLink></div><div className="receipt-records">{records.map(r=><button key={r.id} disabled={busy} aria-pressed={record?.id===r.id} onClick={()=>{setSelected(r.id);setFile(null);setConfirmDelete(false);setError("");}}><Icon name="documents"/><span><strong>{r.edited.merchant || r.filename}</strong><small>{r.filename} · {r.edited.date || "Date unknown"}</small></span><b>{r.edited.total ?? "—"} {r.edited.currency}</b><span className={`receipt-status ${r.reviewed ? "reviewed" : ""}`}>{r.reviewed ? "Reviewed" : "Check details"}</span></button>)}</div><div className="receipt-remove">{confirmDelete ? <><span>Remove this receipt and its edits from this tab?</span><button onClick={()=>{setRecords(current=>current.filter(r=>r.id!==record?.id));setSelected("");setFile(null);setConfirmDelete(false);}}>Yes, remove it</button><button onClick={()=>setConfirmDelete(false)}>Keep it</button></> : <button disabled={busy} onClick={()=>setConfirmDelete(true)}>Remove selected receipt</button>}</div></section>}
  </div>;
}
