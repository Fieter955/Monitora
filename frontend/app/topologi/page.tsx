"use client";

import Link from "next/link";
import {FormEvent, useCallback, useEffect, useMemo, useRef, useState} from "react";
import {AppShell, PageHeader} from "@/components/app-shell";
import {DeviceHealthDrawer} from "@/components/device-health-drawer";
import {Icon} from "@/components/icons";
import {EmptyState, StatusBadge} from "@/components/status";
import {api, formatPercent} from "@/lib/api";
import type {Device, NetworkPort, Topology, TopologyNode, User} from "@/lib/types";

type Point = {x: number; y: number};

export default function TopologyPage() {
  const [topology, setTopology] = useState<Topology | null>(null);
  const [devices, setDevices] = useState<Device[]>([]);
  const [user, setUser] = useState<User | null>(null);
  const [positions, setPositions] = useState<Record<number, Point>>({});
  const [zoom, setZoom] = useState(1);
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [manualOpen, setManualOpen] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState("");
  const [isFullscreen, setIsFullscreen] = useState(false);
  const viewportRef = useRef<HTMLDivElement>(null);
  const previousZoomRef = useRef(1);

  const load = useCallback(async () => {
    const query = new URLSearchParams(window.location.search);
    const requested = Number(query.get("device"));
    const requestedScope = query.get("scope") === "neighbors" ? "neighbors" : "path";
    const [topologyData, deviceData, me] = await Promise.all([
      api<Topology>(requested ? `/topology?focus_device_id=${requested}&scope=${requestedScope}` : "/topology"), api<Device[]>("/devices"), api<User>("/auth/me"),
    ]);
    setTopology(topologyData); setDevices(deviceData); setUser(me);
    setPositions((current) => Object.keys(current).length ? current : layoutNodes(topologyData.nodes));
  }, []);
  useEffect(() => { const initial = window.setTimeout(() => void load(), 0); const timer = window.setInterval(() => void load(), 60_000); return () => { window.clearTimeout(initial); window.clearInterval(timer); }; }, [load]);

  const deviceById = useMemo(() => new Map(devices.map((device) => [device.id, device])), [devices]);

  const fitToScreen = useCallback(() => {
    const viewport = viewportRef.current;
    if (!viewport) return;
    const rect = viewport.getBoundingClientRect();
    const fitted = Math.min((rect.width - 24) / 1000, (rect.height - 24) / 620);
    setZoom(Math.max(.65, Math.min(1.6, fitted)));
    viewport.scrollTo({left: 0, top: 0, behavior: "smooth"});
  }, []);

  const exitFullscreen = useCallback(() => {
    setIsFullscreen(false);
    setZoom(previousZoomRef.current);
  }, []);

  function enterFullscreen() {
    previousZoomRef.current = zoom;
    setIsFullscreen(true);
  }

  useEffect(() => {
    if (!isFullscreen) return;
    document.body.classList.add("topology-fullscreen-open");
    const fitTimer = window.setTimeout(fitToScreen, 0);
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") exitFullscreen();
    };
    const onResize = () => fitToScreen();
    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("resize", onResize);
    return () => {
      window.clearTimeout(fitTimer);
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("resize", onResize);
      document.body.classList.remove("topology-fullscreen-open");
    };
  }, [exitFullscreen, fitToScreen, isFullscreen]);

  async function sync() {
    setSyncing(true); setMessage("");
    try { await api<Topology>("/network/sync", {method: "POST"}); await load(); setMessage("Discovery port dan jalur koneksi selesai diperbarui."); }
    catch { setMessage("LibreNMS belum siap atau sebagian perangkat tidak dapat dijangkau."); }
    finally { setSyncing(false); }
  }

  function moveNode(id: number, x: number, y: number) {
    setPositions((current) => ({...current, [id]: {x: Math.max(20, Math.min(850, x)), y: Math.max(20, Math.min(520, y))}}));
  }

  return (
    <AppShell>
      <PageHeader eyebrow="Pandangan logis" title="Jalur Koneksi" description="Lihat perangkat terhubung ke mana, melalui port apa, dan seberapa besar jalur tersebut sedang digunakan."
        actions={<><button className="button" onClick={() => { setPositions(layoutNodes(topology?.nodes ?? [])); setZoom(1); }}><Icon name="refresh"/>Rapikan</button>{user?.role === "admin" && <button className="button button-primary" disabled={syncing} onClick={() => void sync()}><Icon name="topology"/>{syncing ? "Menyinkronkan…" : "Temukan koneksi"}</button>}</>}/>
      {message && <div className={`notice ${message.includes("belum") ? "notice-warning" : ""}`} role="status"><span className="notice-mark">i</span><div><strong>Status sinkronisasi</strong><p>{message}</p></div></div>}
      {topology?.focus_device_id && <div className={`notice ${topology.path_complete===false?"notice-warning":""}`} role="status"><span className="notice-mark">i</span><div><strong>{topology.path_complete?"Jalur dari gateway":"Jalur belum lengkap"}</strong><p>{topology.path_complete?"Hanya jalur menuju perangkat terpilih yang ditampilkan.":"Gateway atau koneksi belum tercatat lengkap; tetangga yang diketahui ditampilkan tanpa menebak penyebab."}</p></div><Link className="button button-small" href="/topologi">Tampilkan semua</Link></div>}
      <div className="topology-layout">
        <section className={`panel topology-panel ${isFullscreen ? "topology-panel-fullscreen" : ""}`} aria-label="Topologi aktif">
          <div className="panel-header"><div><h2>Topologi aktif</h2><p>{topology?.nodes.length ?? 0} perangkat · {topology?.edges.length ?? 0} koneksi</p></div><div className="topology-header-actions"><div className="zoom-controls" aria-label="Kontrol zoom"><button onClick={() => setZoom((value) => Math.max(.65, value - .15))} aria-label="Perkecil" title="Perkecil">−</button><span aria-live="polite">{Math.round(zoom * 100)}%</span><button onClick={() => setZoom((value) => Math.min(1.6, value + .15))} aria-label="Perbesar" title="Perbesar">+</button></div><button className="button button-small" onClick={fitToScreen} title="Sesuaikan seluruh topologi ke area tampilan"><Icon name="fit"/>Pas ke layar</button>{isFullscreen ? <button className="button button-small button-primary" onClick={exitFullscreen} aria-pressed="true" title="Keluar dari layar penuh (Esc)"><Icon name="minimize"/>Keluar layar penuh</button> : <button className="button button-small" onClick={enterFullscreen} aria-pressed="false" title="Buka topologi memenuhi layar"><Icon name="maximize"/>Layar penuh</button>}</div></div>
          {!topology || topology.nodes.length === 0 ? <EmptyState title="Topologi belum tersedia" description="Daftarkan managed switch/router/AP lalu jalankan Temukan koneksi."/> : (
            <div className="topology-viewport" ref={viewportRef}>
              <div className="topology-stage" style={{transform: `scale(${zoom})`}}>
                <svg viewBox="0 0 1000 620" aria-hidden="true">
                  <defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z"/></marker></defs>
                  {topology.edges.map((edge) => {
                    const source = positions[edge.source_device_id]; const target = edge.target_device_id ? positions[edge.target_device_id] : null;
                    if (!source || !target) return null;
                    return <g key={edge.id}><line className={`topology-edge ${edge.active ? "active" : "inactive"}`} x1={source.x + 65} y1={source.y + 37} x2={target.x + 65} y2={target.y + 37} markerEnd="url(#arrow)"/><text x={(source.x + target.x) / 2 + 65} y={(source.y + target.y) / 2 + 27}>{edge.source_port}{edge.target_port ? ` → ${edge.target_port}` : ""}</text></g>;
                  })}
                </svg>
                {topology.nodes.map((node) => {
                  const position = positions[node.id] ?? {x: 30, y: 30};
                  return <button key={node.id} draggable className={`topology-node node-${node.status} ${topology.focus_device_id===node.id?"topology-node-focus":""}`} style={{left: position.x, top: position.y}} onDragEnd={(event) => { const rect = event.currentTarget.parentElement!.getBoundingClientRect(); moveNode(node.id, (event.clientX - rect.left) / zoom - 65, (event.clientY - rect.top) / zoom - 37); }} onKeyDown={(event) => { const step = event.shiftKey ? 25 : 8; if (["ArrowLeft","ArrowRight","ArrowUp","ArrowDown"].includes(event.key)) event.preventDefault(); if (event.key === "ArrowLeft") moveNode(node.id, position.x-step, position.y); if (event.key === "ArrowRight") moveNode(node.id, position.x+step, position.y); if (event.key === "ArrowUp") moveNode(node.id, position.x, position.y-step); if (event.key === "ArrowDown") moveNode(node.id, position.x, position.y+step); }} onClick={() => setSelectedDevice(deviceById.get(node.id) ?? null)}>
                    <span className="node-icon" aria-hidden="true">{nodeAbbreviation(node)}</span><span className="node-copy"><strong>{node.name}</strong><small>{node.location || node.address}</small></span><span className={`node-state state-${node.status}`} aria-hidden="true"/>
                  </button>;
                })}
              </div>
            </div>
          )}
          <div className="map-legend"><span><i className="legend-line discovered"/>LLDP/CDP</span><span><i className="legend-line manual"/>Manual</span><span>Seret node atau gunakan tombol panah</span></div>
        </section>
        <aside className="panel connection-panel">
          <div className="panel-header"><div><h2>Koneksi</h2><p>Port dan pemakaian terkini</p></div>{user?.role === "admin" && <button className="button button-small" onClick={() => setManualOpen(true)}><Icon name="plus"/>Manual</button>}</div>
          {!topology?.edges.length ? <EmptyState title="Belum ada koneksi" description="Aktifkan LLDP/CDP atau tambahkan jalur manual."/> : <div className="connection-list">{topology.edges.map((edge) => <button key={edge.id} onClick={() => setSelectedDevice(deviceById.get(edge.source_device_id) ?? null)}><span className="connection-origin">{edge.origin.toUpperCase()}</span><strong>{deviceById.get(edge.source_device_id)?.name ?? "Perangkat"} → {edge.target_device_id ? deviceById.get(edge.target_device_id)?.name : edge.target_name || "Perangkat luar"}</strong><small>{edge.source_port || "Port tidak diketahui"}{edge.target_port ? ` ke ${edge.target_port}` : ""}</small><span className="connection-util">{formatPercent(edge.utilization_percent)}</span></button>)}</div>}
        </aside>
      </div>
      <DeviceHealthDrawer device={selectedDevice} onClose={() => setSelectedDevice(null)}/>
      {manualOpen && <ManualLinkDrawer devices={devices} onClose={() => setManualOpen(false)} onSaved={async () => { setManualOpen(false); setMessage("Koneksi manual berhasil ditambahkan."); await load(); }}/>}
    </AppShell>
  );
}

function ManualLinkDrawer({devices, onClose, onSaved}: {devices: Device[]; onClose: () => void; onSaved: () => Promise<void>}) {
  const [local, setLocal] = useState(""); const [remote, setRemote] = useState(""); const [ports, setPorts] = useState<Record<number, NetworkPort[]>>({}); const [localPort, setLocalPort] = useState(""); const [remotePort, setRemotePort] = useState(""); const [error, setError] = useState("");
  async function selectDevice(value: string, side: "local" | "remote") { if (side === "local") setLocal(value); else setRemote(value); const id = Number(value); if (id && !ports[id]) { const result = await api<{ports: NetworkPort[]}>(`/devices/${id}/discovery`); setPorts((current) => ({...current, [id]: result.ports})); } }
  async function submit(event: FormEvent) { event.preventDefault(); setError(""); try { await api<Topology>("/topology/links/manual", {method: "POST", body: JSON.stringify({local_device_id: Number(local), local_port_id: localPort ? Number(localPort) : null, remote_device_id: Number(remote), remote_port_id: remotePort ? Number(remotePort) : null})}); await onSaved(); } catch { setError("Koneksi manual tidak dapat disimpan. Pastikan dua perangkat berbeda."); } }
  return <><button className="drawer-scrim" aria-label="Tutup" onClick={onClose}/><section className="drawer" role="dialog" aria-modal="true" aria-labelledby="manual-link-title"><header className="drawer-header"><div><h2 id="manual-link-title">Tambah koneksi manual</h2><p>Gunakan untuk perangkat yang tidak mendukung LLDP/CDP.</p></div><button className="icon-button" onClick={onClose} aria-label="Tutup"><Icon name="close"/></button></header><div className="drawer-body"><form onSubmit={submit}>{error && <div className="form-error">{error}</div>}<div className="form-grid"><DeviceSelect label="Perangkat asal" value={local} devices={devices} onChange={(value) => void selectDevice(value,"local")}/><PortSelect label="Port asal" value={localPort} ports={ports[Number(local)] ?? []} onChange={setLocalPort}/><DeviceSelect label="Perangkat tujuan" value={remote} devices={devices} onChange={(value) => void selectDevice(value,"remote")}/><PortSelect label="Port tujuan" value={remotePort} ports={ports[Number(remote)] ?? []} onChange={setRemotePort}/></div><div className="form-actions"><button type="button" className="button" onClick={onClose}>Batal</button><button className="button button-primary" type="submit" disabled={!local || !remote}>Simpan koneksi</button></div></form></div></section></>;
}

function DeviceSelect({label,value,devices,onChange}: {label:string;value:string;devices:Device[];onChange:(value:string)=>void}) { return <div className="field field-full"><label>{label}</label><select required value={value} onChange={(event)=>onChange(event.target.value)}><option value="">Pilih perangkat</option>{devices.map((device)=><option value={device.id} key={device.id}>{device.name}</option>)}</select></div>; }
function PortSelect({label,value,ports,onChange}: {label:string;value:string;ports:NetworkPort[];onChange:(value:string)=>void}) { return <div className="field field-full"><label>{label}</label><select value={value} onChange={(event)=>onChange(event.target.value)}><option value="">Tanpa port khusus</option>{ports.map((port)=><option value={port.id} key={port.id}>{port.name} · {port.oper_status}</option>)}</select></div>; }

function layoutNodes(nodes: TopologyNode[]) { const groups = [nodes.filter((n)=>n.network_role==="gateway"),nodes.filter((n)=>n.network_role==="distribution"),nodes.filter((n)=>n.network_role==="access"),nodes.filter((n)=>n.network_role==="endpoint")].filter((group)=>group.length); const positions: Record<number,Point>={}; groups.forEach((group,row)=>group.forEach((node,index)=>{positions[node.id]={x:70+index*(780/Math.max(1,group.length-1)),y:45+row*(500/Math.max(1,groups.length-1))};})); return positions; }
function nodeAbbreviation(node: TopologyNode) { return node.kind === "access_point" ? "AP" : node.kind === "switch" ? "SW" : node.kind === "router" ? "RT" : node.kind === "cctv" ? "CAM" : node.kind === "hub" ? "HB" : node.kind === "linux_server" ? "SRV" : "PC"; }
