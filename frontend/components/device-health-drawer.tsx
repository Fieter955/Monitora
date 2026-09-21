"use client";

import {useEffect, useState} from "react";
import {api, formatBits} from "@/lib/api";
import type {Device, DeviceHealth, NetworkPort} from "@/lib/types";
import {Icon} from "./icons";
import {EmptyState, StatusBadge} from "./status";

const healthLabels = {
  healthy: "Sehat",
  warning: "Perlu perhatian",
  critical: "Bermasalah",
  unknown: "Belum diketahui",
};

export function DeviceHealthDrawer({
  device,
  onClose,
}: {
  device: Device | null;
  onClose: () => void;
}) {
  const [health, setHealth] = useState<DeviceHealth | null>(null);
  const [advanced, setAdvanced] = useState(false);

  useEffect(() => {
    const initial = window.setTimeout(() => {
      setHealth(null);
      setAdvanced(false);
      if (device) void api<DeviceHealth>(`/devices/${device.id}/health`).then(setHealth);
    }, 0);
    return () => window.clearTimeout(initial);
  }, [device]);

  if (!device) return null;
  const status = health?.status ?? "unknown";
  return (
    <>
      <button className="drawer-scrim" aria-label="Tutup detail perangkat" onClick={onClose}/>
      <aside className="drawer health-drawer" role="dialog" aria-modal="true" aria-labelledby="health-title">
        <header className="drawer-header">
          <div>
            <p className="eyebrow">Kondisi perangkat</p>
            <h2 id="health-title">{device.name}</h2>
            <p>{device.location || device.address}</p>
          </div>
          <button className="icon-button" aria-label="Tutup" onClick={onClose}><Icon name="close"/></button>
        </header>
        <div className="drawer-body">
          <div className="health-hero">
            <StatusBadge
              status={status === "healthy" ? "online" : status}
              label={healthLabels[status]}
            />
            <p>{health?.reason || summaryFor(status)}</p>
            <small>Terakhir diperiksa: {formatDate(health?.checked_at)}</small>
          </div>

          <section className="health-section" aria-labelledby="physical-title">
            <h3 id="physical-title">Lokasi fisik</h3>
            <dl className="definition-list technical-details">
              <div><dt>Label aset</dt><dd>{device.asset_tag || "Belum dicatat"}</dd></div>
              <div><dt>Rak/patokan</dt><dd>{device.physical_group || "Belum dicatat"}</dd></div>
              <div><dt>Posisi</dt><dd>{device.physical_position || "Belum dicatat"}</dd></div>
            </dl>
          </section>

          <section className="health-section" aria-labelledby="action-title">
            <h3 id="action-title">Yang perlu diperiksa</h3>
            {!health ? (
              <p className="muted">Memuat kondisi terbaru…</p>
            ) : health.issues.length === 0 ? (
              <EmptyState title="Tidak ada masalah aktif" description="Semua pemeriksaan yang tersedia dalam kondisi normal."/>
            ) : (
              <div className="issue-stack">
                {health.issues.map((issue, index) => (
                  <article className={`issue-card issue-${issue.severity}`} key={`${issue.code}-${issue.port_id}-${index}`}>
                    <span aria-hidden="true">!</span>
                    <div><strong>{issue.title}</strong><p>{issue.detail}</p></div>
                  </article>
                ))}
              </div>
            )}
          </section>

          {health && health.ports.length > 0 && (
            <section className="health-section" aria-labelledby="ports-title">
              <div className="section-heading"><div><h3 id="ports-title">Port dan koneksi</h3><p>{health.ports.length} interface ditemukan</p></div></div>
              <div className="compact-port-list">
                {health.ports.map((port) => <PortRow port={port} key={port.id}/>) }
              </div>
            </section>
          )}

          <section className="health-section advanced-section">
            <button className="advanced-toggle" onClick={() => setAdvanced((value) => !value)} aria-expanded={advanced}>
              <span>Detail lanjutan</span><span aria-hidden="true">{advanced ? "−" : "+"}</span>
            </button>
            {advanced && (
              <dl className="definition-list technical-details">
                <div><dt>Alamat</dt><dd>{device.address}</dd></div>
                <div><dt>Level monitoring</dt><dd>{device.monitoring_level}</dd></div>
                <div><dt>ID LibreNMS</dt><dd>{device.librenms_device_id ?? "—"}</dd></div>
                <div><dt>Kemampuan</dt><dd>{Object.keys(device.capabilities).join(", ") || "Belum diaudit"}</dd></div>
                <div><dt>Target Prometheus</dt><dd><code>{device.prometheus_target}</code></dd></div>
              </dl>
            )}
          </section>
        </div>
      </aside>
    </>
  );
}

function PortRow({port}: {port: NetworkPort}) {
  const conditionLabels: Record<string, string> = {
    healthy: "Aktif",
    normal_empty: "Kosong normal",
    disconnected: "Terputus",
    unexpected_active: "Asing aktif",
    unknown: "Belum diketahui",
  };
  return (
    <article className={`compact-port port-${port.condition}`}>
      <div><strong>{port.name}</strong><span>{port.expectation_label || port.alias || expectationLabel(port.expectation)}</span></div>
      <div className="port-traffic"><strong>{formatBits(Math.max(port.rx_bps ?? 0, port.tx_bps ?? 0))}</strong><span>{port.utilization_percent == null ? "—" : `${port.utilization_percent}% kapasitas`}</span></div>
      <StatusBadge status={port.condition === "healthy" ? "online" : port.condition === "disconnected" ? "critical" : port.condition === "unexpected_active" ? "warning" : "unknown"} label={conditionLabels[port.condition] ?? port.condition}/>
    </article>
  );
}

function expectationLabel(value: NetworkPort["expectation"]) {
  return value === "required" ? "Port wajib" : value === "spare" ? "Port cadangan" : "Diabaikan";
}

function summaryFor(status: DeviceHealth["status"]) {
  if (status === "healthy") return "Seluruh pemeriksaan yang tersedia berjalan normal.";
  if (status === "critical") return "Ada gangguan yang perlu segera ditindaklanjuti.";
  if (status === "warning") return "Ada perubahan yang perlu dikonfirmasi oleh tim IT.";
  return "Data monitoring perangkat belum tersedia.";
}

function formatDate(value: string | null | undefined) {
  return value ? new Intl.DateTimeFormat("id-ID", {dateStyle: "medium", timeStyle: "short"}).format(new Date(value)) : "belum tersedia";
}
