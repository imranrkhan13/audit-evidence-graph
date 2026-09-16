import { forwardRef } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { currentDisplayName, currentRole, logout } from "../api";
import { navigation } from "../navigation";
import Icon from "./Icon";

interface Props {
  collapsed: boolean;
  mobile: boolean;
  open: boolean;
  onToggle: () => void;
  onClose: () => void;
}

const Sidebar = forwardRef<HTMLElement, Props>(function Sidebar({ collapsed, mobile, open, onToggle, onClose }, ref) {
  const navigate = useNavigate();
  const name = currentDisplayName() || "Demo user";
  const initials = name.split(" ").map(part => part[0]).slice(0, 2).join("");
  return (
    <aside ref={ref} id="workspace-sidebar" className={`workspace-sidebar ${collapsed && !mobile ? "is-collapsed" : ""} ${open ? "is-open" : ""}`}
      role={mobile && open ? "dialog" : undefined} aria-modal={mobile && open ? true : undefined} aria-label="Workspace navigation">
      <div className="sidebar-brand-row">
        <Link to="/dashboard" onClick={onClose} className="workspace-brand" aria-label="Evidence workspace dashboard">
          <span className="workspace-symbol"><Icon name="checks" size={22}/></span>
          <span className="sidebar-copy"><strong>Evidence</strong><small>Audit workspace</small></span>
        </Link>
        {mobile && <button className="sidebar-icon-button" onClick={onClose} aria-label="Close navigation"><Icon name="close"/></button>}
      </div>
      <div className="sidebar-project"><span className="project-avatar">D</span><span className="sidebar-copy"><strong>Demo workspace</strong><small><i/> Sample data</small></span></div>
      <nav aria-label="App pages" className="sidebar-navigation">
        {navigation.map(group => <div className="sidebar-group" key={group.label}>
          <div className="sidebar-group-label">{group.label}</div>
          {group.items.map(item => <NavLink key={item.to} to={item.to} onClick={onClose} title={collapsed && !mobile ? item.label : undefined}
            aria-label={item.label} className={({ isActive }) => `sidebar-link ${isActive ? "is-active" : ""}`}>
            <Icon name={item.icon}/><span className="sidebar-copy">{item.label}</span><span className="active-dot"/>
          </NavLink>)}
        </div>)}
      </nav>
      <div className="sidebar-bottom">
        {!mobile && <button className="sidebar-collapse" onClick={onToggle} aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"} aria-expanded={!collapsed} aria-controls="workspace-sidebar" title={collapsed ? "Expand sidebar" : undefined}>
          <Icon name={collapsed ? "expand" : "collapse"}/><span className="sidebar-copy">Collapse sidebar</span>
        </button>}
        <div className="sidebar-profile"><span className="profile-avatar" title={name}>{initials}</span><div className="sidebar-copy"><strong>{name}</strong><small>{currentRole() || "Demo account"}</small></div>
          <button className="sidebar-icon-button" aria-label="Sign out" title="Sign out" onClick={() => { logout(); navigate("/login"); }}><Icon name="logout" size={18}/></button>
        </div>
      </div>
    </aside>
  );
});
export default Sidebar;
