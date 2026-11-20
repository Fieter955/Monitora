"use client";

import {useCallback, useEffect, useState} from "react";
import {AppShell, PageHeader} from "@/components/app-shell";
import {DeviceHealthDrawer} from "@/components/device-health-drawer";
import {DeviceWizardDrawer, kindLabels} from "@/components/device-wizard-drawer";
import {Icon} from "@/components/icons";
import {EmptyState, StatusBadge} from "@/components/status";
import {api} from "@/lib/api";
import type {Device, Location, SystemCapabilities, User} from "@/lib/types";

export default function DevicesPage() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<Device | null | undefined>(undefined);
  const [message, setMessage] = useState("");
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [capabilities, setCapabilities] = useState<SystemCapabilities | null>(null);

  const load = useCallback(async () => {
    const [deviceData, me, locationData, capabilityData] = await Promise.all([
      api<Device[]>("/devices"), api<User>("/auth/me"), api<Location[]>("/locations"),
      api<SystemCapabilities>("/system/capabilities"),
    ]);
    setDevices(deviceData); setUser(me); setLocations(locationData); setCapabilities(capabilityData); setLoading(false);
    const requested = Number(new URLSearchParams(window.location.search).get("device"));
    if (requested) setSelectedDevice(deviceData.find((item) => item.id === requested) ?? null);
  }, []);
  useEffect(() => { const initial = window.setTimeout(() => void load(), 0); return () => window.clearTimeout(initial); }, [load]);

  async function remove(device: Device) {
    if (!window.confirm(`Arsipkan ${device.name}? Perangkat hilang dari operasi tetapi histori tetap disimpan.`)) return;
    await api(`/devices/${device.id}`, {method: "DELETE"});
    setMessage(`${device.name} telah diarsipkan.`); await load();
  }

  const isAdmin = user?.role === "admin";
  return <AppShell>
    <PageHeader eyebrow="Inventaris" title="Perangkat" description="Daftarkan seluruh perangkat, uji aksesnya, lalu tentukan port mana yang seharusnya terhubung."
      actions={isAdmin ? <button className="button button-primary" onClick={() => setEditing(null)}><Icon name="plus"/>Tambah perangkat</button> : undefined}/>
    {message && <div className="notice" role="status"><span className="notice-mark">i</span><div><strong>Inventaris diperbarui</strong><p>{message}</p></div></div>}
    {capabilities?.deployment_profile === "windows_native" && <div className="notice"><span className="notice-mark">i</span><div><strong>Mode Windows native</strong><p>Monitoring host, website, ICMP, SNMP, ISP, dan Grafana aktif. Discovery topologi LibreNMS tidak tersedia pada profil ini.</p></div></div>}
    <section className="panel" aria-labelledby="device-table-title">
      <div className="panel-header"><div><h2 id="device-table-title">Daftar perangkat</h2><p>{devices.length} perangkat aktif dalam inventaris</p></div></div>
      {loading ? <div className="empty-state">Memuat inventaris…</div> : devices.length === 0 ? <EmptyState title="Inventaris masih kosong" description="Tambahkan switch, router, AP, CCTV, server, atau perangkat pertama."/> : <div className="table-wrap"><table className="data-table"><thead><tr><th>Perangkat</th><th>Jenis</th><th>Monitoring</th><th>Lokasi</th><th>Status</th>{isAdmin && <th><span className="visually-hidden">Tindakan</span></th>}</tr></thead><tbody>{devices.map((device) => <tr key={device.id}>
        <td><button className="table-device-link" onClick={() => setSelectedDevice(device)}><span className="table-primary">{device.name}</span><span className="table-secondary">{device.asset_tag || device.address}</span></button></td>
        <td>{kindLabels[device.kind]}</td><td><span className="table-primary">{monitoringLabel(device.monitoring_level)}</span><span className="table-secondary">{Object.keys(device.capabilities).join(", ") || device.prometheus_job}</span></td><td>{device.location || locationName(device.room_id, locations) || "—"}</td><td><StatusBadge status={device.is_active ? "online" : "unknown"} label={device.is_active ? "Aktif" : "Dinonaktifkan"}/></td>
        {isAdmin && <td><div className="table-actions"><a className="icon-button" aria-label={`Cetak label ${device.name}`} href={`/perangkat/${device.id}/label`}><Icon name="external"/></a><button className="icon-button" aria-label={`Edit ${device.name}`} onClick={() => setEditing(device)}><Icon name="edit"/></button><button className="icon-button" aria-label={`Arsipkan ${device.name}`} onClick={() => void remove(device)}><Icon name="trash"/></button></div></td>}
      </tr>)}</tbody></table></div>}
    </section>
    <DeviceHealthDrawer device={selectedDevice} onClose={() => setSelectedDevice(null)}/>
    {editing !== undefined && <DeviceWizardDrawer device={editing} locations={locations} onClose={() => setEditing(undefined)} onSaved={async (text) => { setEditing(undefined); setMessage(text); await load(); }}/>}
  </AppShell>;
}

function locationName(id:number|null,locations:Location[]){return id?locations.find((item)=>item.id===id)?.name:"";}
function monitoringLabel(level:string){return level==="full"?"Jaringan lengkap":level==="stream"?"Online + stream":level==="limited"?"Terbatas":"Dasar";}
