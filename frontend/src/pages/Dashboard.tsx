import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { AuditEvent, Dashboard as DashboardData, Engagement, ReviewTask } from "../types";
import Icon, { IconName } from "../components/Icon";

export default function Dashboard() {
  const [project, setProject] = useState<Engagement | null>(null);
  const [data, setData] = useState<DashboardData | null>(null);
  const [tasks, setTasks] = useState<ReviewTask[]>([]);
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [error, setError] = useState("");
  const [taskError, setTaskError] = useState(false);
  const [eventError, setEventError] = useState(false);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const projects: Engagement[] = await api.listEngagements();
        if (!projects.length) throw new Error("No sample audit project is available yet.");
        const selected = projects[0];
        const [summary, queue, activity] = await Promise.allSettled([
          api.dashboard(selected.id), api.reviewQueue(selected.id, "financial_impact", "open"), api.auditEvents(selected.id),
        ]);
        if (!active) return;
        if (summary.status === "rejected") throw summary.reason;
        setProject(selected);
        setData(summary.value);
        if (queue.status === "fulfilled") setTasks(queue.value); else setTaskError(true);
        if (activity.status === "fulfilled") setEvents(activity.value.slice(-4).reverse()); else setEventError(true);
      } catch (e) { if (active) setError(e instanceof Error ? e.message : "Could not load the dashboard."); }
      finally { if (active) setLoading(false); }
    })();
    return () => { active = false; };
  }, []);
  if (loading) return <div className="app-page app-loading" role="status">Loading your dashboard…</div>;
  if (error) return <div className="app-page"><p role="alert" className="app-error">{error}</p></div>;
  if (!data || !project) return null;
  const passedPercent = data.total_assertions ? Math.round(data.passed / data.total_assertions * 100) : 0;
  const metrics: { label: string; value: number; note: string; icon: IconName; tone: string; to: string }[] = [
    { label: "Total items", value: data.total_assertions, note: "Across this audit project", icon: "checks", tone: "blue", to: "/assertions" },
    { label: "Passed", value: data.passed, note: "Saved checks passed", icon: "checks", tone: "green", to: "/assertions" },
    { label: "Needs review", value: data.needs_review, note: "Waiting for a closer look", icon: "review", tone: "amber", to: "/review" },
    { label: "Problems found", value: data.failed, note: "An important check failed", icon: "risk", tone: "red", to: "/review" },
  ];
  return <div className="app-page dashboard-page">
    <div className="app-page-heading"><div><p className="app-eyebrow">AUDIT WORKSPACE</p><h1>Dashboard</h1><p>Your project, the checks so far, and what needs attention.</p></div><Link to="/review" className="app-button primary">Open review queue <Icon name="arrow" size={17}/></Link></div>
    <div className="project-banner"><span className="project-banner-icon"><Icon name="documents" size={22}/></span><div><strong>{project.client_name}</strong><p>Audit period · {project.period_start} — {project.period_end}</p></div><span className="project-status"><i/>{project.status.replace(/_/g, " ")}</span></div>
    <section className="dashboard-metrics" aria-label="Audit summary">{metrics.map(metric => <Link key={metric.label} to={metric.to} className={`metric-card ${metric.tone}`}><div className="metric-card-top"><span>{metric.label}</span><span className="metric-icon"><Icon name={metric.icon} size={18}/></span></div><strong>{metric.value.toString().padStart(2, "0")}</strong><small>{metric.note}</small></Link>)}</section>
    <div className="dashboard-columns">
      <section className="workspace-card review-card"><div className="card-heading"><div><h2>Needs your attention</h2><p>Open review tasks, ordered by recorded financial impact.</p></div><Link to="/review">View all <Icon name="arrow" size={15}/></Link></div>
        {taskError ? <p className="app-error">The review queue could not be loaded. <Link to="/review">Try opening it directly.</Link></p> : tasks.length ? <div className="dashboard-review-list">{tasks.slice(0, 4).map(task => <Link to={`/assertions/${task.assertion_id}`} className="dashboard-review-row" key={task.id}><span className={`review-indicator ${task.risk_level}`}><Icon name={task.reason === "missing_evidence" ? "documents" : "review"} size={18}/></span><div><strong>{task.assertion_label}</strong><small>{task.reason.replace(/_/g, " ")}</small></div><span className="risk-tag">{task.risk_level} priority</span><Icon name="arrow" size={16}/></Link>)}</div> : <p className="app-loading">No open review tasks. You’re up to date.</p>}
        <div className="card-footnote"><span className="small-dot amber"/>{data.missing_evidence_count} item{data.missing_evidence_count === 1 ? "" : "s"} flagged for missing documents <Link to="/documents">Browse documents →</Link></div>
      </section>
      <section className="workspace-card progress-card"><div className="card-heading"><div><h2>Check progress</h2><p>Current saved results</p></div></div><div className="progress-ring" style={{ background: `conic-gradient(#438a74 ${passedPercent}%, #e9edf0 0)` }} role="img" aria-label={`${passedPercent}% of items passed`}><div><strong>{passedPercent}%</strong><span>passed</span></div></div><div className="progress-legend">{[{label:"Passed",value:data.passed,color:"green"},{label:"Needs review",value:data.needs_review,color:"amber"},{label:"Problems found",value:data.failed,color:"red"},{label:"Pending",value:data.pending,color:"gray"}].map(item=><div key={item.label}><span><i className={`small-dot ${item.color}`}/>{item.label}</span><strong>{item.value}</strong></div>)}</div><p className="progress-note">Passing a check is a saved result, not a final audit opinion.</p></section>
    </div>
    <div className="dashboard-columns bottom-columns"><section className="workspace-card"><div className="card-heading"><div><h2>Recent activity</h2><p>The latest recorded steps in this project.</p></div><Link to="/audit-trail">Full history <Icon name="arrow" size={15}/></Link></div>{eventError ? <p className="app-error">Activity could not be loaded.</p> : events.length ? <ol className="dashboard-activity">{events.map(event=><li key={event.id}><span className="activity-node"/><div><strong>{event.summary}</strong><small>{event.event_type.replace(/_/g, " ")}</small></div><time dateTime={event.created_at}>{new Date(/Z$|[+-]\d{2}:\d{2}$/.test(event.created_at) ? event.created_at : `${event.created_at}Z`).toLocaleDateString(undefined,{month:"short",day:"numeric"})}</time></li>)}</ol> : <p className="app-loading">No activity recorded yet.</p>}</section>
      <section className="workspace-card quick-actions"><div className="card-heading"><div><h2>Continue working</h2><p>Go straight to the next step.</p></div></div>{[{to:"/change-impact",icon:"change" as const,title:"Preview a document change",text:"See which items may need another look."},{to:"/documents",icon:"documents" as const,title:"Find a source document",text:"Browse invoices and supporting records."},{to:"/export",icon:"download" as const,title:"Prepare a report",text:"Save the results for a closer review."}].map(action=><Link to={action.to} key={action.to}><span className="quick-icon"><Icon name={action.icon}/></span><div><strong>{action.title}</strong><small>{action.text}</small></div><Icon name="arrow" size={16}/></Link>)}</section></div>
  </div>;
}
