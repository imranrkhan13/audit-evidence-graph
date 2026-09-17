import { Link } from "react-router-dom";
import Icon from "./Icon";

export default function TopBar({ title, mobile, open, onOpen, buttonRef }: {
  title: string; mobile: boolean; open: boolean; onOpen: () => void; buttonRef: React.RefObject<HTMLButtonElement>;
}) {
  return <header className="workspace-topbar">
    <div className="topbar-location">
      {mobile && <button ref={buttonRef} className="workspace-icon-button" onClick={onOpen} aria-label="Open navigation" aria-expanded={open} aria-controls="workspace-sidebar"><Icon name="menu"/></button>}
      <span className="topbar-workspace">Workspace</span><span className="breadcrumb-divider">/</span><span className="topbar-page">{title}</span>
    </div>
    <div className="topbar-actions"><span className="demo-pill"><i/> {title === "Read a receipt" ? "Your uploads" : "Demo data"}</span><Link to="/guide" className="workspace-icon-button" aria-label="Help and simple guide" title="Help and simple guide"><Icon name="help" size={19}/></Link></div>
  </header>;
}
