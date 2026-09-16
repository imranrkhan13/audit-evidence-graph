export default function StatusBadge({ status }: { status: string }) {
  const label = status.replace("_", " ");
  return <span className={`status-badge status-${status}`}>{label}</span>;
}
