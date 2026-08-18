"use client";

import {useCallback, useEffect, useState} from "react";
import {AppShell, PageHeader} from "@/components/app-shell";
import {Icon} from "@/components/icons";
import {EmptyState, StatusBadge} from "@/components/status";
import {api} from "@/lib/api";
import type {AlertItem} from "@/lib/types";

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (quiet = false) => {
    if (quiet) setRefreshing(true);
    try {
      setAlerts(await api<AlertItem[]>("/monitoring/alerts"));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    const initial = window.setTimeout(() => void load(), 0);
    const timer = window.setInterval(() => void load(true), 30_000);
    return () => {
      window.clearTimeout(initial);
      window.clearInterval(timer);
    };
  }, [load]);

  const critical = alerts.filter((item) => item.severity === "critical").length;

  return (
    <AppShell>
      <PageHeader
        eyebrow="Tindak lanjut"
        title="Alert"
        description="Kondisi yang melewati ambang batas dan membutuhkan pemeriksaan petugas."
        actions={<button className="button" onClick={() => void load(true)} disabled={refreshing}><Icon name="refresh"/>{refreshing ? "Memperbarui…" : "Perbarui"}</button>}
      />

      {critical > 0 && <div className="notice notice-danger" role="alert"><span className="notice-mark" aria-hidden="true">!</span><div><strong>{critical} alert kritis aktif</strong><p>Dahulukan pemeriksaan layanan yang tidak tersedia dan kapasitas disk yang menipis.</p></div></div>}

      <section className="panel" aria-labelledby="alert-list-title">
        <div className="panel-header"><div><h2 id="alert-list-title">Daftar alert aktif</h2><p>Aturan dievaluasi Prometheus setiap 15 detik</p></div></div>
        {loading ? <div className="empty-state" aria-live="polite">Memuat alert…</div> : alerts.length === 0 ? (
          <EmptyState title="Tidak ada alert aktif" description="Semua target berada dalam kondisi yang ditetapkan." />
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead><tr><th scope="col">Alert</th><th scope="col">Target</th><th scope="col">Ringkasan</th><th scope="col">Prioritas</th><th scope="col">Aktif sejak</th></tr></thead>
              <tbody>{alerts.map((alert, index) => <tr key={`${alert.name}-${alert.instance}-${index}`}><td><span className="table-primary">{alert.name}</span><span className="table-secondary">{alert.state === "pending" ? "Menunggu durasi aturan" : "Sedang aktif"}</span></td><td><code>{alert.instance}</code></td><td>{alert.summary || "Tidak ada keterangan tambahan"}</td><td><StatusBadge status={alert.severity}/></td><td>{alert.active_since ? new Intl.DateTimeFormat("id-ID", {dateStyle: "medium", timeStyle: "short"}).format(new Date(alert.active_since)) : "—"}</td></tr>)}</tbody>
            </table>
          </div>
        )}
      </section>
    </AppShell>
  );
}
