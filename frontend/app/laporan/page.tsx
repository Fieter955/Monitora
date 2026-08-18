"use client";

import {AppShell, PageHeader} from "@/components/app-shell";
import {Icon} from "@/components/icons";

export default function ReportsPage() {
  const today = new Intl.DateTimeFormat("id-ID", {dateStyle: "long"}).format(new Date());
  return (
    <AppShell>
      <PageHeader eyebrow="Dokumentasi" title="Laporan" description="Unduh data operasional untuk dokumentasi, evaluasi, dan bahan presentasi." />

      <div className="notice" role="status"><span className="notice-mark" aria-hidden="true">i</span><div><strong>Laporan memakai kondisi terbaru</strong><p>Prometheus akan dihubungi saat berkas dibuat. Tanggal hari ini: {today}.</p></div></div>

      <section className="report-card" aria-labelledby="status-report-title">
        <span className="report-icon" aria-hidden="true"><Icon name="reports"/></span>
        <div><h2 id="status-report-title">Status Infrastruktur</h2><p>Inventaris, status target, CPU, memori, disk, lokasi, dan kondisi pemantauan dalam format CSV.</p></div>
        <a className="button button-primary" href="/api/v1/reports/status.csv"><Icon name="download"/>Unduh CSV</a>
      </section>

      <section className="panel" style={{marginTop: 20}} aria-labelledby="report-notes-title">
        <div className="panel-header"><div><h2 id="report-notes-title">Cara menggunakan laporan</h2><p>Catatan untuk dokumentasi berkala</p></div></div>
        <div className="panel-body">
          <dl className="definition-list">
            <div><dt>Format</dt><dd>CSV UTF-8, dapat dibuka di Excel atau LibreOffice</dd></div>
            <div><dt>Waktu data</dt><dd>Kondisi saat tombol unduh dipilih</dd></div>
            <div><dt>Data historis</dt><dd>Gunakan ekspor Grafana untuk rentang waktu dan grafik teknis</dd></div>
          </dl>
          <a className="button" href="/grafana/" target="_blank" rel="noreferrer" style={{marginTop: 16}}><Icon name="external"/>Buka Grafana</a>
        </div>
      </section>
    </AppShell>
  );
}
