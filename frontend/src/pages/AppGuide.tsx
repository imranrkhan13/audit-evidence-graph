import { Link } from "react-router-dom";
import { Brand } from "./Landing";
import "../landing.css";

const pages = [
  { to: "/dashboard", title: "Dashboard", text: "See how many items passed the checks, need a person's review, or have a problem." },
  { to: "/documents", title: "Documents", text: "Browse and search the invoices, bank statements, and other records in this project." },
  { to: "/assertions", title: "Items to check", text: "Open a statement such as ‘this invoice matches the accounting records.’ See the documents and calculations behind it." },
  { to: "/change-impact", title: "When a document changes", text: "Choose a document to see which items use it. For an invoice, try a new total and compare it with the amount in the accounting records." },
  { to: "/risk-radar", title: "Unusual transactions", text: "Find transactions worth a closer look and search the sample documents. A flag is a clue to investigate, not proof of an error." },
  { to: "/review", title: "Needs a person’s review", text: "See items with missing documents, different amounts, or uncertain readings. A reviewer can approve, reject, or ask for more documents." },
  { to: "/audit-trail", title: "Activity history", text: "See what happened, when it happened, and who did it. Earlier results remain available when a document is updated." },
  { to: "/export", title: "Download reports", text: "Save results with links back to the documents. Choose a data file (JSON) or an HTML file you can open in a browser and print." },
];

export default function AppGuide({ publicView = false }: { publicView?: boolean }) {
  return (
    <div className={publicView ? "modus-site" : "workspace-feature"}>
      {publicView && <header className="site-nav"><Link to="/"><Brand /></Link><Link className="button button-blue" to="/change-impact">Try the demo ↗</Link></header>}
      <div className="impact-main guide-main">
        <p className="eyebrow">A SIMPLE GUIDE</p>
        <h1>Simple guide</h1>
        <p className="guide-intro">It helps an auditor check whether a company’s documents and accounting records agree. When a document changes, it shows which earlier checks may need another look.</p>
        <section className="impact-notice guide-example">
          <h2>A small example</h2>
          <p>Imagine an invoice and the accounting records both say <strong>$1,000</strong>. Later, someone corrects the invoice to <strong>$1,250</strong>.</p>
          <p>The app can show the <strong>$250 difference</strong> and the items that use that invoice. A person then decides what to investigate. Trying a new amount in the preview does not save the change or approve anything.</p>
        </section>
        <section className="guide-section">
          <h2>Try it in three steps</h2>
          <ol className="guide-steps">
            <li><strong>Start on the Dashboard.</strong> See which items passed and which need a closer look.</li>
            <li><strong>Choose a document.</strong> On “Document changes,” pick an invoice. Enter a new total and select “See what needs checking.”</li>
            <li><strong>Read the result.</strong> Look at the difference, open a related item, or download the report. Try a shared bank statement or ledger to see why one document can affect several items.</li>
          </ol>
        </section>
        <section className="guide-section">
          <h2>What you can explore</h2>
          <div className="guide-cards">{pages.map(page => <Link key={page.to} to={page.to}><h3>{page.title} ↗</h3><p>{page.text}</p></Link>)}</div>
        </section>
        <section className="guide-section">
          <h2>A few words you may see</h2>
          <dl className="guide-glossary">
            <div><dt>Audit</dt><dd>A review of financial records and the documents that support them.</dd></div>
            <div><dt>Evidence</dt><dd>The supporting documents, such as invoices, bank statements, and approval notes.</dd></div>
            <div><dt>Assertion</dt><dd>A statement to check, such as “this invoice matches the amount recorded.” The app calls these “items to check.”</dd></div>
            <div><dt>Ledger</dt><dd>The company’s list of recorded financial transactions.</dd></div>
            <div><dt>Tie-out</dt><dd>A comparison to see whether amounts in different records match.</dd></div>
            <div><dt>Confidence</dt><dd>How certain the system is about a value read from a document. It does not tell you how likely the company’s accounts are to be correct.</dd></div>
            <div><dt>Engagement</dt><dd>One audit project for one company and time period.</dd></div>
          </dl>
        </section>
        <section className="guide-section">
          <h2>What this demo can and cannot tell you</h2>
          <p>The invoices, businesses, and transactions are made-up examples. Values read from documents are prepared in advance; this demo does not run AI or scan your files.</p>
          <p>The checks use fixed rules. The change preview only compares an invoice amount with one matching US-dollar accounting entry. It does not run every check again or change earlier approvals.</p>
          <p>The app helps a person find and review problems. It does not issue an audit opinion or replace an accountant. It is an independent project inspired by Modus, with no connection to Modus’s live systems.</p>
        </section>
        <Link className="button button-blue" to="/change-impact">Start exploring ↗</Link>
      </div>
    </div>
  );
}
