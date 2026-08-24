"use client";

import {FormEvent, useCallback, useEffect, useMemo, useState} from "react";
import {AppShell, PageHeader} from "@/components/app-shell";
import {DeviceHealthDrawer} from "@/components/device-health-drawer";
import {Icon} from "@/components/icons";
import {EmptyState, StatusBadge} from "@/components/status";
import {api, apiForm, ApiError} from "@/lib/api";
import type {Device, Floorplan, Location, LocationKind, Topology, User} from "@/lib/types";

const locationLabels: Record<LocationKind, string> = {
  site: "Site",
  building: "Gedung",
  floor: "Lantai",
  room: "Ruang",
};

export default function FloorplanPage() {
  const [locations, setLocations] = useState<Location[]>([]);
  const [floorplans, setFloorplans] = useState<Floorplan[]>([]);
  const [devices, setDevices] = useState<Device[]>([]);
  const [topology, setTopology] = useState<Topology | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [selectedLocation, setSelectedLocation] = useState<number | null>(null);
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [placing, setPlacing] = useState<number | null>(null);
  const [managing, setManaging] = useState(false);
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    const [locationData, floorplanData, deviceData, topologyData, me] = await Promise.all([
      api<Location[]>("/locations"),
      api<Floorplan[]>("/locations/floorplans"),
      api<Device[]>("/devices"),
      api<Topology>("/topology"),
      api<User>("/auth/me"),
    ]);
    let loadedLocations = locationData;
    let loadedFloorplans = floorplanData;

    // Inject mock data if the database is completely empty
    if (loadedLocations.length === 0) {
      loadedLocations = [
        { id: 9990, name: "Kampus BBWS Serayu Opak", kind: "site", parent_id: null, sort_order: 1, created_at: "", updated_at: "" },
        { id: 9991, name: "Balai Teknik Pantai", kind: "building", parent_id: 9990, sort_order: 1, created_at: "", updated_at: "" },
        { id: 9992, name: "Lantai 1", kind: "floor", parent_id: 9991, sort_order: 1, created_at: "", updated_at: "" },
        { id: 9993, name: "Ruang Server", kind: "room", parent_id: 9992, sort_order: 1, created_at: "", updated_at: "" },
        { id: 9994, name: "Ruang Admin", kind: "room", parent_id: 9992, sort_order: 2, created_at: "", updated_at: "" }
      ];
      loadedFloorplans = [
        { id: 9991, location_id: 9992, filename: "denah-ruangan.jpg", content_type: "image/jpeg", image_url: "/denah-ruangan.jpg", updated_at: "" }
      ];
    }

    setLocations(loadedLocations);
    setFloorplans(loadedFloorplans);
    setDevices(deviceData);
    setTopology(topologyData);
    setUser(me);
    setSelectedLocation((current) => current ?? loadedFloorplans[0]?.location_id ?? loadedLocations.find((item) => item.kind === "floor" || item.kind === "room")?.id ?? null);
  }, []);

  useEffect(() => { const initial = window.setTimeout(() => void load(), 0); return () => window.clearTimeout(initial); }, [load]);

  const visibleLocationIds = useMemo(() => descendantsOf(selectedLocation, locations), [selectedLocation, locations]);
  const orderedLocations = useMemo(() => orderLocations(locations), [locations]);
  const visibleDevices = devices.filter((device) => device.room_id != null && visibleLocationIds.has(device.room_id));
  const placedDevices = visibleDevices.filter((device) => device.floorplan_x != null && device.floorplan_y != null);
  const unplacedDevices = visibleDevices.filter((device) => device.floorplan_x == null || device.floorplan_y == null);
  const floorplan = floorplans.find((item) => item.location_id === selectedLocation);
  const statusById = new Map(topology?.nodes.map((node) => [node.id, node.status]));

  async function place(deviceId: number, x: number, y: number) {
    if (user?.role !== "admin") return;
    const updated = await api<Device>(`/devices/${deviceId}`, {
      method: "PATCH",
      body: JSON.stringify({floorplan_x: x, floorplan_y: y}),
    });
    setDevices((current) => current.map((device) => device.id === deviceId ? updated : device));
    setPlacing(null);
    setMessage(`${updated.name} ditempatkan pada denah.`);
  }

  function canvasPosition(event: React.MouseEvent<HTMLDivElement> | React.DragEvent<HTMLDivElement>) {
    const rect = event.currentTarget.getBoundingClientRect();
    return {
      x: Math.max(0, Math.min(100, ((event.clientX - rect.left) / rect.width) * 100)),
      y: Math.max(0, Math.min(100, ((event.clientY - rect.top) / rect.height) * 100)),
    };
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow="Pandangan fisik"
        title="Peta Lokasi"
        description="Temukan perangkat bermasalah berdasarkan gedung, lantai, dan ruang tanpa membaca detail jaringan terlebih dahulu."
        actions={user?.role === "admin" ? <button className="button" onClick={() => setManaging(true)}><Icon name="edit"/>Atur lokasi & denah</button> : undefined}
      />

      {message && <div className="notice" role="status"><span className="notice-mark">i</span><div><strong>Peta diperbarui</strong><p>{message}</p></div></div>}

      <div className="panel" style={{ margin: "20px 32px" }}>
        <div className="panel-header">
          <div><h2>Lokasi: Balai Teknik Pantai</h2><p>Peta area dan denah 1 lantai 2 ruangan (Placeholder)</p></div>
        </div>
        <div style={{ display: "flex", gap: "20px", padding: "20px" }}>
          <div style={{ flex: 1 }}>
            <h3 style={{ marginBottom: "10px", fontSize: "14px", color: "var(--muted)" }}>Peta Geografis</h3>
            <iframe 
              src="https://maps.google.com/maps?q=Balai%20Teknik%20Pantai&t=&z=15&ie=UTF8&iwloc=&output=embed" 
              width="100%" 
              height="100%" 
              style={{ aspectRatio: "4/3", border: 0, borderRadius: "8px" }} 
              allowFullScreen={true} 
              loading="lazy" 
              referrerPolicy="no-referrer-when-downgrade"
              title="Peta Lokasi Balai Teknik Pantai"
            ></iframe>
          </div>
          <div style={{ flex: 1 }}>
            <h3 style={{ marginBottom: "10px", fontSize: "14px", color: "var(--muted)" }}>Denah 1 Lantai 2 Ruangan</h3>
            <img src="/denah-ruangan.jpg" alt="Denah Ruangan" style={{ width: "100%", aspectRatio: "4/3", objectFit: "cover", borderRadius: "8px", border: "1px solid var(--border)" }} />
          </div>
        </div>
      </div>

      <div className="map-layout">
        <aside className="location-browser panel" aria-label="Daftar lokasi">
          <div className="panel-header"><div><h2>Lokasi</h2><p>Pilih lantai atau ruang</p></div></div>
          <div className="location-tree">
            {locations.length === 0 ? <EmptyState title="Belum ada lokasi" description="Admin dapat membuat hierarki lokasi dan mengunggah denah."/> : orderedLocations.map((location) => (
              <button
                key={location.id}
                className={selectedLocation === location.id ? "active" : ""}
                style={{paddingLeft: `${14 + locationDepth(location, locations) * 17}px`}}
                onClick={() => setSelectedLocation(location.id)}
              >
                <span className={`location-kind kind-${location.kind}`} aria-hidden="true"/>
                <span><strong>{location.name}</strong><small>{locationLabels[location.kind]}</small></span>
              </button>
            ))}
          </div>
        </aside>

        <section className="floorplan-panel panel" aria-labelledby="floorplan-title">
          <div className="panel-header">
            <div><h2 id="floorplan-title">{locations.find((item) => item.id === selectedLocation)?.name ?? "Denah"}</h2><p>{placedDevices.length} perangkat ditempatkan · {unplacedDevices.length} belum ditempatkan</p></div>
            {placing && <span className="placing-hint">Klik posisi perangkat pada denah</span>}
          </div>
          {floorplan ? (
            <div
              className={`floorplan-canvas ${placing ? "placing" : ""}`}
              style={{backgroundImage: `url(${floorplan.image_url})`}}
              onClick={(event) => { if (placing) { const position = canvasPosition(event); void place(placing, position.x, position.y); } }}
              onDragOver={(event) => event.preventDefault()}
              onDrop={(event) => { event.preventDefault(); const id = Number(event.dataTransfer.getData("text/device-id")); if (id) { const position = canvasPosition(event); void place(id, position.x, position.y); } }}
            >
              {placedDevices.map((device) => {
                const status = statusById.get(device.id) ?? "unknown";
                return (
                  <button
                    key={device.id}
                    draggable={user?.role === "admin"}
                    className={`map-device map-device-${status}`}
                    style={{left: `${device.floorplan_x}%`, top: `${device.floorplan_y}%`}}
                    onDragStart={(event) => event.dataTransfer.setData("text/device-id", String(device.id))}
                    onClick={(event) => { event.stopPropagation(); setSelectedDevice(device); }}
                    aria-label={`${device.name}, ${healthLabel(status)}`}
                  >
                    <DeviceGlyph kind={device.kind}/><span>{device.name}</span>
                  </button>
                );
              })}
            </div>
          ) : (
            <EmptyState title="Denah belum tersedia" description="Unggah denah PNG, JPG, atau WebP untuk lokasi ini melalui Atur lokasi & denah."/>
          )}
          {visibleDevices.length > 0 && (
            <div className="map-legend">
              <span><i className="legend-dot healthy"/>Sehat</span><span><i className="legend-dot warning"/>Perlu perhatian</span><span><i className="legend-dot critical"/>Bermasalah</span><span><i className="legend-dot unknown"/>Belum diketahui</span>
            </div>
          )}
        </section>

        <aside className="unplaced-panel panel">
          <div className="panel-header"><div><h2>Belum ditempatkan</h2><p>Pilih lalu klik pada denah</p></div></div>
          {unplacedDevices.length === 0 ? <EmptyState title="Semua sudah dipetakan" description="Tidak ada perangkat yang menunggu penempatan."/> : <div className="unplaced-list">{unplacedDevices.map((device) => (
            <button key={device.id} className={placing === device.id ? "active" : ""} onClick={() => setPlacing(device.id)} disabled={user?.role !== "admin"}>
              <DeviceGlyph kind={device.kind}/><span><strong>{device.name}</strong><small>{device.location || device.address}</small></span><StatusBadge status={statusById.get(device.id) === "healthy" ? "online" : statusById.get(device.id) ?? "unknown"} label=""/>
            </button>
          ))}</div>}
        </aside>
      </div>

      <DeviceHealthDrawer device={selectedDevice} onClose={() => setSelectedDevice(null)}/>
      {managing && <LocationManager locations={locations} selectedLocation={selectedLocation} onClose={() => setManaging(false)} onSaved={async (text) => { setMessage(text); await load(); }}/>} 
    </AppShell>
  );
}

function LocationManager({locations, selectedLocation, onClose, onSaved}: {locations: Location[]; selectedLocation: number | null; onClose: () => void; onSaved: (text: string) => Promise<void>}) {
  const [name, setName] = useState("");
  const [kind, setKind] = useState<LocationKind>(locations.length ? "building" : "site");
  const [parentId, setParentId] = useState<number | null>(selectedLocation);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const expectedParentKind: Partial<Record<LocationKind, LocationKind>> = {building: "site", floor: "building", room: "floor"};
  const parents = locations.filter((item) => item.kind === expectedParentKind[kind]);

  async function addLocation(event: FormEvent) {
    event.preventDefault(); setError("");
    try {
      await api<Location>("/locations", {method: "POST", body: JSON.stringify({name, kind, parent_id: kind === "site" ? null : parentId})});
      setName(""); await onSaved(`${name} berhasil ditambahkan.`);
    } catch (reason) { setError(reason instanceof ApiError ? reason.message : "Lokasi tidak dapat disimpan"); }
  }

  async function upload(event: FormEvent) {
    event.preventDefault(); setError("");
    if (!selectedLocation || !file) return;
    const form = new FormData(); form.append("file", file);
    try { await apiForm<Floorplan>(`/locations/${selectedLocation}/floorplan`, form); await onSaved("Denah berhasil diperbarui."); }
    catch (reason) { setError(reason instanceof ApiError ? reason.message : "Denah tidak dapat diunggah"); }
  }

  async function rename(location: Location) {
    const nextName = window.prompt("Nama lokasi baru", location.name)?.trim();
    if (!nextName || nextName === location.name) return;
    try { await api<Location>(`/locations/${location.id}`, {method:"PATCH",body:JSON.stringify({name:nextName})}); await onSaved(`${location.name} diubah menjadi ${nextName}.`); }
    catch (reason) { setError(reason instanceof ApiError ? reason.message : "Lokasi tidak dapat diubah"); }
  }
  async function remove(location: Location) {
    if (!window.confirm(`Hapus ${location.name}? Lokasi harus kosong dan tidak memiliki turunan.`)) return;
    try { await api(`/locations/${location.id}`, {method:"DELETE"}); await onSaved(`${location.name} berhasil dihapus.`); }
    catch (reason) { setError(reason instanceof ApiError ? reason.message : "Lokasi tidak dapat dihapus"); }
  }

  return <><button className="drawer-scrim" aria-label="Tutup pengaturan" onClick={onClose}/><section className="drawer" role="dialog" aria-modal="true" aria-labelledby="location-manager-title">
    <header className="drawer-header"><div><h2 id="location-manager-title">Atur lokasi & denah</h2><p>Susun site, gedung, lantai, dan ruang secara berurutan.</p></div><button className="icon-button" onClick={onClose} aria-label="Tutup"><Icon name="close"/></button></header>
    <div className="drawer-body">
      {error && <div className="form-error" role="alert">{error}</div>}
      <form onSubmit={addLocation} className="stacked-form">
        <h3>Tambah lokasi</h3>
        <div className="field"><label htmlFor="location-kind">Jenis</label><select id="location-kind" value={kind} onChange={(event) => { const value = event.target.value as LocationKind; setKind(value); setParentId(null); }}><option value="site">Site</option><option value="building">Gedung</option><option value="floor">Lantai</option><option value="room">Ruang</option></select></div>
        {kind !== "site" && <div className="field"><label htmlFor="location-parent">Induk</label><select id="location-parent" required value={parentId ?? ""} onChange={(event) => setParentId(Number(event.target.value))}><option value="">Pilih {locationLabels[expectedParentKind[kind]!]}</option>{parents.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></div>}
        <div className="field"><label htmlFor="location-name">Nama</label><input id="location-name" required value={name} onChange={(event) => setName(event.target.value)} placeholder="Contoh: Lantai 2"/></div>
        <button className="button button-primary" type="submit">Tambah lokasi</button>
      </form>
      <form onSubmit={upload} className="stacked-form upload-form">
        <h3>Unggah denah lokasi terpilih</h3><p className="muted">PNG, JPG, atau WebP, maksimal 10 MB.</p>
        <div className="field"><label htmlFor="floorplan-file">Berkas denah</label><input id="floorplan-file" type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => setFile(event.target.files?.[0] ?? null)}/></div>
        <button className="button" type="submit" disabled={!selectedLocation || !file}>Unggah denah</button>
      </form>
      <section className="managed-locations">
        <h3>Lokasi terdaftar</h3>
        {orderLocations(locations).map((location) => <div key={location.id} style={{paddingLeft: `${locationDepth(location,locations)*14}px`}}><span><strong>{location.name}</strong><small>{locationLabels[location.kind]}</small></span><button type="button" className="icon-button" aria-label={`Ubah ${location.name}`} onClick={() => void rename(location)}><Icon name="edit"/></button><button type="button" className="icon-button" aria-label={`Hapus ${location.name}`} onClick={() => void remove(location)}><Icon name="trash"/></button></div>)}
      </section>
    </div>
  </section></>;
}

function descendantsOf(selected: number | null, locations: Location[]) {
  if (selected == null) return new Set<number>();
  const result = new Set<number>([selected]);
  let changed = true;
  while (changed) { changed = false; for (const item of locations) if (item.parent_id != null && result.has(item.parent_id) && !result.has(item.id)) { result.add(item.id); changed = true; } }
  return result;
}

function locationDepth(location: Location, locations: Location[]) { let depth = 0; let parent = location.parent_id; while (parent != null && depth < 4) { depth += 1; parent = locations.find((item) => item.id === parent)?.parent_id ?? null; } return depth; }
function orderLocations(locations: Location[]) { const result: Location[]=[]; const visit=(parent:number|null)=>locations.filter((item)=>item.parent_id===parent).sort((a,b)=>a.sort_order-b.sort_order||a.name.localeCompare(b.name,"id")).forEach((item)=>{result.push(item);visit(item.id);}); visit(null); return result; }
function healthLabel(status: string) { return status === "healthy" ? "sehat" : status === "critical" ? "bermasalah" : status === "warning" ? "perlu perhatian" : "belum diketahui"; }
function DeviceGlyph({kind}: {kind: Device["kind"]}) { return <span className="device-glyph" aria-hidden="true">{kind === "cctv" ? "CAM" : kind === "access_point" ? "AP" : kind === "switch" ? "SW" : kind === "router" ? "RT" : kind === "hub" ? "HB" : kind === "linux_server" ? "SRV" : "DEV"}</span>; }
