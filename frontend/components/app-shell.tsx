"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { SystemCapabilities, User } from "@/lib/types";
import { Icon } from "./icons";

const navigation = [
  { href: "/", label: "Ringkasan", icon: "dashboard" as const },
  { href: "/peta", label: "Pencari Gangguan", icon: "map" as const },
  { href: "/topologi", label: "Jalur Koneksi", icon: "topology" as const, advanced: true },
  { href: "/perangkat", label: "Perangkat", icon: "devices" as const },
  { href: "/alert", label: "Alert", icon: "alerts" as const },
  { href: "/laporan", label: "Laporan", icon: "reports" as const },
];

const grafanaDashboardUrl = "/grafana/d/infrastructure-overview/ringkasan-infrastruktur?kiosk&_dash.hideTimePicker=true&_dash.hideVariables=true";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [menuOpen, setMenuOpen] = useState(false);
  const [capabilities, setCapabilities] = useState<SystemCapabilities | null>(null);

  useEffect(() => {
    Promise.all([api<User>("/auth/me"), api<SystemCapabilities>("/system/capabilities")])
      .then(([currentUser, currentCapabilities]) => {
        setUser(currentUser);
        setCapabilities(currentCapabilities);
      })
      .catch(() => router.replace("/login"))
      .finally(() => setLoading(false));
  }, [router]);

  async function logout() {
    await api("/auth/logout", { method: "POST" });
    router.replace("/login");
    router.refresh();
  }

  if (loading) {
    return (
      <main className="loading-screen" aria-live="polite">
        <span className="loading-mark" aria-hidden="true" />
        <p>Menyiapkan ruang kerja…</p>
      </main>
    );
  }

  if (!user) return null;

  return (
    <div className="app-layout">
      <a className="skip-link" href="#main-content">Lewati ke konten utama</a>
      <aside className={`sidebar ${menuOpen ? "sidebar-open" : ""}`} aria-label="Navigasi utama">
        <div className="brand">
          <Image className="brand-logo" src="/logo.jpg" alt="" width={38} height={38} priority />
          <div><strong>Monitora</strong><small>Infrastruktur TI</small></div>
        </div>
        <nav className="main-nav">
          {navigation.filter((item) => !("advanced" in item) || capabilities?.advanced_topology).map((item) => {
            const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={active ? "active" : ""}
                aria-current={active ? "page" : undefined}
                onClick={() => setMenuOpen(false)}
              >
                <Icon name={item.icon} /><span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="sidebar-footer">
          <a href={grafanaDashboardUrl} target="_blank" rel="noreferrer">
            <Icon name="external" /><span>Buka Grafana</span>
          </a>
          <p>Data teknis dan grafik historis</p>
        </div>
      </aside>

      {menuOpen && <button className="sidebar-scrim" aria-label="Tutup navigasi" onClick={() => setMenuOpen(false)} />}

      <div className="workspace">
        <header className="topbar">
          <button className="icon-button mobile-menu" aria-label="Buka navigasi" onClick={() => setMenuOpen(true)}>
            <Icon name="menu" />
          </button>
          <div className="topbar-context"><span>Sistem internal</span><strong>Monitoring Infrastruktur</strong></div>
          <div className="user-area">
            <span className="avatar" aria-hidden="true">{user.full_name.slice(0, 1).toUpperCase()}</span>
            <div><strong>{user.full_name}</strong><small>{user.role === "admin" ? "Administrator" : "Pengamat"}</small></div>
            <button className="icon-button" aria-label="Keluar dari aplikasi" title="Keluar" onClick={logout}><Icon name="logout" /></button>
          </div>
        </header>
        <main id="main-content" className="main-content" tabIndex={-1}>
          {children}
        </main>
      </div>
    </div>
  );
}

export function PageHeader({ eyebrow, title, description, actions }: { eyebrow: string; title: string; description: string; actions?: React.ReactNode }) {
  return (
    <header className="page-header">
      <div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p className="page-description">{description}</p></div>
      {actions && <div className="page-actions">{actions}</div>}
    </header>
  );
}
