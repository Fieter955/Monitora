"use client";

import Link from "next/link";
import {useCallback, useEffect, useMemo, useState} from "react";
import {AppShell, PageHeader} from "@/components/app-shell";
import {Icon} from "@/components/icons";
import {EmptyState, MetricBar, StatusBadge} from "@/components/status";
import {api, formatBytes, formatUptime} from "@/lib/api";
import type {AlertItem, Device, MonitoringSummary, Topology} from "@/lib/types";

export default function DashboardPage() {
  const [summary, setSummary] = useState<MonitoringSummary | null>(null);
  const [devices, setDevices] = useState<Device[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [topology, setTopology] = useState<Topology | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = useCallback(async (quiet = false) => {
    if (quiet) setRefreshing(true);
    try {
      const [summaryData, deviceData, alertData, topologyData] = await Promise.all([
        api<MonitoringSummary>("/monitoring/summary"),
        api<Device[]>("/devices"),
        api<AlertItem[]>("/monitoring/alerts"),
        api<Topology>("/topology"),
      ]);
      setSummary(summaryData);
      setDevices(deviceData);
      setAlerts(alertData);
      setTopology(topologyData);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    const initial = window.setTimeout(() => void loadData(), 0);
    const timer = window.setInterval(() => void loadData(true), 30_000);
    return () => {
      window.clearTimeout(initial);
      window.clearInterval(timer);
    };
  }, [loadData]);

  const metrics = useMemo(() => new Map(summary?.devices.map((item) => [item.device_id, item])), [summary]);
  const activeDevices = devices.filter((device) => device.is_active);
  const problemNodes = topology?.nodes.filter((node) => node.status === "critical" || node.status === "warning") ?? [];

  return (
    <AppShell>
      <PageHeader
        eyebrow="Operasional hari ini"
        title="Ringkasan Infrastruktur"
        description="Kondisi terkini server, perangkat jaringan, dan layanan yang sedang dipantau."
        actions={
          <button className="button" onClick={() => void loadData(true)} disabled={refreshing}>
            <Icon name="refresh"/>{refreshing ? "Memperbarui…" : "Perbarui data"}
          </button>
        }
      />

      {summary && !summary.available && (
        <div className="notice notice-warning" role="status">
          <span className="notice-mark" aria-hidden="true">!</span>
          <div><strong>Data monitoring belum tersedia</strong><p>{summary.message}</p></div>
        </div>
      )}
      {summary && summary.offline_devices > 0 && (
        <div className="notice notice-danger" role="alert">
          <span className="notice-mark" aria-hidden="true">!</span>
          <div><strong>Ada perangkat yang tidak terjangkau</strong><p>Periksa koneksi atau exporter pada {summary.offline_devices} perangkat berstatus offline.</p></div>
        </div>
      )}

      <section className="summary-grid" aria-label="Statistik singkat">
        <SummaryCard label="Perangkat dipantau" value={loading ? "…" : String(summary?.total_devices ?? 0)} note="Target aktif di inventaris" tone="neutral" />
        <SummaryCard label="Online" value={loading ? "…" : String(summary?.online_devices ?? 0)} note="Metrik dapat diambil" tone="success" />
        <SummaryCard label="Offline" value={loading ? "…" : String(summary?.offline_devices ?? 0)} note="Perlu pemeriksaan" tone="danger" />
        <SummaryCard label="Alert aktif" value={loading ? "…" : String(summary?.firing_alerts ?? 0)} note="Kondisi yang perlu ditangani" tone="warning" />
      </section>

      <section className="operations-strip" aria-labelledby="priority-title">
        <div className="priority-copy"><p className="eyebrow">Prioritas tim</p><h2 id="priority-title">{problemNodes.length ? `${problemNodes.length} perangkat perlu diperiksa` : "Tidak ada gangguan jaringan aktif"}</h2><p>{problemNodes.length ? "Mulai dari lokasi dan perangkat berikut; detail teknis tersedia ketika dibutuhkan." : "Seluruh perangkat dengan data terbaru berada dalam kondisi normal."}</p></div>
        <div className="priority-devices">{problemNodes.slice(0,3).map((node)=><Link href="/peta" key={node.id}><StatusBadge status={node.status}/><span><strong>{node.name}</strong><small>{node.location||node.address}</small></span><span aria-hidden="true">→</span></Link>)}</div>
        <div className="priority-actions"><Link className="button" href="/peta"><Icon name="map"/>Buka Peta Lokasi</Link><Link className="button" href="/topologi"><Icon name="topology"/>Lihat Jalur Koneksi</Link></div>
      </section>

      <div className="content-grid">
        <section className="panel" aria-labelledby="server-health-title">
          <div className="panel-header">
            <div><h2 id="server-health-title">Kesehatan perangkat</h2><p>Diperbarui otomatis setiap 30 detik</p></div>
            <Link className="panel-link" href="/perangkat">Kelola perangkat</Link>
          </div>
          {activeDevices.length === 0 ? (
            <EmptyState title="Belum ada perangkat" description="Tambahkan perangkat pertama melalui menu Perangkat." />
          ) : (
            <div className="device-list">
              {activeDevices.slice(0, 8).map((device) => {
                const metric = metrics.get(device.id);
                return (
                  <article className="device-row" key={device.id}>
                    <div className="device-identity"><strong>{device.name}</strong><span>{device.location || device.address}</span></div>
                    <div className="device-metrics">
                      <MetricBar label="CPU" value={metric?.cpu_percent ?? null}/>
                      <MetricBar label="Memori" value={metric?.memory_percent ?? null}/>
                      <MetricBar label="Disk" value={metric?.disk_percent ?? null}/>
                    </div>
                    <StatusBadge status={metric?.status ?? "unknown"}/>
                  </article>
                );
              })}
            </div>
          )}
        </section>

        <div>
          <section className="panel" aria-labelledby="alerts-title">
            <div className="panel-header"><div><h2 id="alerts-title">Alert terbaru</h2><p>{alerts.length} kondisi tercatat</p></div><Link className="panel-link" href="/alert">Lihat semua</Link></div>
            {alerts.length === 0 ? (
              <EmptyState title="Tidak ada alert aktif" description="Belum ada kondisi yang memerlukan tindak lanjut." />
            ) : (
              <div className="alert-list">
                {alerts.slice(0, 5).map((alert, index) => <AlertRow key={`${alert.name}-${alert.instance}-${index}`} alert={alert}/>) }
              </div>
            )}
          </section>

          <section className="panel" aria-labelledby="detail-title">
            <div className="panel-header"><div><h2 id="detail-title">Analisis teknis</h2><p>Grafik historis enam jam terakhir</p></div></div>
            <div className="panel-body">
              <dl className="definition-list">
                <div><dt>Terakhir diperiksa</dt><dd>{summary ? new Intl.DateTimeFormat("id-ID", {dateStyle: "medium", timeStyle: "short"}).format(new Date(summary.checked_at)) : "—"}</dd></div>
                <div><dt>Data masuk</dt><dd>{formatBytes(summary?.devices.reduce((total, item) => total + (item.receive_bytes_per_second ?? 0), 0) ?? null)}</dd></div>
                <div><dt>Uptime pertama</dt><dd>{formatUptime(summary?.devices[0]?.uptime_seconds ?? null)}</dd></div>
              </dl>
              <a className="button" href="/grafana/" target="_blank" rel="noreferrer" style={{width: "100%", marginTop: 16}}><Icon name="external"/>Buka dashboard Grafana</a>
            </div>
          </section>
        </div>
      </div>
    </AppShell>
  );
}

function SummaryCard({label, value, note, tone}: {label: string; value: string; note: string; tone: string}) {
  return <article className={`summary-card ${tone}`}><div className="summary-card-label"><span>{label}</span><span className="summary-symbol" aria-hidden="true" /></div><strong className="summary-card-value">{value}</strong><span className="summary-card-note">{note}</span></article>;
}

function AlertRow({alert}: {alert: AlertItem}) {
  return (
    <article className="alert-row">
      <span className={`alert-indicator ${alert.severity === "critical" ? "critical" : ""}`} aria-hidden="true" />
      <div><strong>{alert.name}</strong><p>{alert.summary || alert.instance}</p><time>{alert.active_since ? new Intl.DateTimeFormat("id-ID", {dateStyle: "medium", timeStyle: "short"}).format(new Date(alert.active_since)) : "Waktu belum tersedia"}</time></div>
    </article>
  );
}
