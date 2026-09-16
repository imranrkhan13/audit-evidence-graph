import { useEffect, useRef, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";
import { pageTitle } from "../navigation";
import "../workspace.css";
import { hostedDemo } from "../demo";

export default function WorkspaceLayout() {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem("audit-sidebar-collapsed") === "true");
  const [mobile, setMobile] = useState(() => window.matchMedia("(max-width: 900px)").matches);
  const [open, setOpen] = useState(false);
  const sidebar = useRef<HTMLElement>(null);
  const content = useRef<HTMLDivElement>(null);
  const menuButton = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    const media = window.matchMedia("(max-width: 900px)");
    const update = () => { setMobile(media.matches); setOpen(false); };
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);
  useEffect(() => { setOpen(false); window.scrollTo(0, 0); }, [location.pathname]);
  useEffect(() => { localStorage.setItem("audit-sidebar-collapsed", String(collapsed)); }, [collapsed]);
  useEffect(() => {
    if (!mobile || !open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    content.current?.setAttribute("inert", "");
    const focusable = () => Array.from(sidebar.current?.querySelectorAll<HTMLElement>('a[href], button:not([disabled])') || []);
    focusable()[0]?.focus();
    const keydown = (event: KeyboardEvent) => {
      if (event.key === "Escape") { event.preventDefault(); setOpen(false); }
      if (event.key !== "Tab") return;
      const items = focusable();
      const first = items[0], last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    };
    document.addEventListener("keydown", keydown);
    return () => {
      document.body.style.overflow = previousOverflow;
      content.current?.removeAttribute("inert");
      document.removeEventListener("keydown", keydown);
      menuButton.current?.focus();
    };
  }, [mobile, open]);

  return <div className={`workspace-shell ${collapsed ? "sidebar-is-collapsed" : ""}`}>
    <a className="workspace-skip" href="#workspace-content">Skip to page content</a>
    {mobile && open && <button className="sidebar-backdrop" onClick={() => setOpen(false)} aria-label="Close navigation backdrop" tabIndex={-1}/>}
    <Sidebar ref={sidebar} collapsed={collapsed} mobile={mobile} open={open} onToggle={() => setCollapsed(value => !value)} onClose={() => setOpen(false)}/>
    <div ref={content} className="workspace-body">
      <TopBar title={pageTitle(location.pathname)} mobile={mobile} open={open} onOpen={() => setOpen(true)} buttonRef={menuButton}/>
      {hostedDemo && <div className="hosted-demo-note">Public sample workspace · Changes are temporary and may reset. Download a report to keep a copy.</div>}
      <main id="workspace-content" className="workspace-content" tabIndex={-1}><Outlet/></main>
      <footer className="workspace-footer">Independent demo · Made-up sample records · No live Modus connection</footer>
    </div>
  </div>;
}
