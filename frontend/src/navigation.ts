import type { IconName } from "./components/Icon";

export const navigation: { label: string; items: { to: string; label: string; icon: IconName }[] }[] = [
  { label: "Workspace", items: [
    { to: "/dashboard", label: "Dashboard", icon: "dashboard" },
    { to: "/receipts", label: "Read a receipt", icon: "documents" },
    { to: "/documents", label: "Documents", icon: "documents" },
    { to: "/assertions", label: "Items to check", icon: "checks" },
  ] },
  { label: "Review & investigate", items: [
    { to: "/change-impact", label: "Document changes", icon: "change" },
    { to: "/risk-radar", label: "Unusual transactions", icon: "risk" },
    { to: "/review", label: "Needs review", icon: "review" },
  ] },
  { label: "Records", items: [
    { to: "/audit-trail", label: "Activity history", icon: "history" },
    { to: "/export", label: "Download reports", icon: "download" },
    { to: "/guide", label: "Simple guide", icon: "help" },
  ] },
];

export function pageTitle(path: string) {
  if (path.startsWith("/documents/")) return "Document details";
  if (path.startsWith("/assertions/")) return "Item details";
  return navigation.flatMap(group => group.items).find(item => item.to === path)?.label || "Dashboard";
}
