export function StatusBadge({status, label}: {status: string; label?: string}) {
  const normalized = ["online", "firing", "critical"].includes(status)
    ? status === "online" ? "online" : "critical"
    : ["offline"].includes(status)
      ? "offline"
      : ["pending", "warning"].includes(status)
        ? "warning"
        : "unknown";
  const labels: Record<string, string> = {
    online: "Online",
    offline: "Offline",
    critical: "Kritis",
    warning: "Peringatan",
    unknown: "Belum diketahui",
  };
  return <span className={`status status-${normalized}`}><span aria-hidden="true" />{label ?? labels[normalized]}</span>;
}

export function MetricBar({label, value}: {label: string; value: number | null}) {
  const safeValue = value == null ? 0 : Math.max(0, Math.min(100, value));
  const level = safeValue >= 90 ? "danger" : safeValue >= 75 ? "warning" : "normal";
  return (
    <div className="metric-row">
      <div className="metric-label"><span>{label}</span><strong>{value == null ? "—" : `${Math.round(value)}%`}</strong></div>
      <div className="metric-track" role="meter" aria-label={label} aria-valuemin={0} aria-valuemax={100} aria-valuenow={value ?? undefined}>
        <span className={`metric-fill metric-${level}`} style={{width: `${safeValue}%`}} />
      </div>
    </div>
  );
}

export function EmptyState({title, description}: {title: string; description: string}) {
  return <div className="empty-state"><span aria-hidden="true">i</span><div><strong>{title}</strong><p>{description}</p></div></div>;
}
