export type IconName = "dashboard" | "documents" | "checks" | "change" | "risk" | "review" | "history" | "download" | "help" | "collapse" | "expand" | "menu" | "close" | "logout" | "arrow" | "search";
const paths: Record<IconName, JSX.Element> = {
  dashboard: <><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></>,
  documents: <><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6M8 13h8M8 17h5"/></>,
  checks: <><rect x="4" y="3" width="16" height="18" rx="2"/><path d="m8 9 2 2 4-4M8 16h8"/></>,
  change: <><path d="M4 7h14l-3-3m5 13H6l3 3M18 7l-3 3M6 17l3-3"/></>,
  risk: <><path d="m12 3 10 18H2zM12 9v5"/><path d="M12 17h.01"/></>,
  review: <><path d="M21 11.5a8.5 8.5 0 0 1-8.5 8.5H4l-2 2v-9.5A8.5 8.5 0 0 1 10.5 4"/><path d="m14 6 2 2 5-5M7 12h8M7 16h5"/></>,
  history: <><path d="M3 11a9 9 0 1 1 2.6 7.4M3 4v7h7M12 7v5l3 2"/></>,
  download: <><path d="M12 3v12m-5-5 5 5 5-5M4 15v5h16v-5"/></>,
  help: <><circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 4 2c-1 .7-1.5 1-1.5 3M12 17h.01"/></>,
  collapse: <><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16m7-11-3 3 3 3"/></>,
  expand: <><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16m4-11 3 3-3 3"/></>,
  menu: <path d="M4 6h16M4 12h16M4 18h16"/>,
  close: <path d="m6 6 12 12M6 18 18 6"/>,
  logout: <><path d="M10 4H4v16h6m4-12 4 4-4 4m-5-4h12"/></>,
  arrow: <path d="M4 12h15m-6-6 6 6-6 6"/>,
  search: <><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/></>,
};
export default function Icon({ name, size = 20 }: { name: IconName; size?: number }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.65" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>;
}
