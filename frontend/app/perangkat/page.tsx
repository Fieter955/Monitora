"use client";

import {FormEvent, useCallback, useEffect, useState} from "react";
import {AppShell, PageHeader} from "@/components/app-shell";
import {DeviceHealthDrawer} from "@/components/device-health-drawer";
import {Icon} from "@/components/icons";
import {EmptyState, StatusBadge} from "@/components/status";
import {api, ApiError} from "@/lib/api";
import type {
  CredentialSecret, Device, DeviceInput, DeviceKind, DiscoveryResult,
  Location, NetworkPort, PortExpectation, SystemCapabilities, User,
} from "@/lib/types";

const kindLabels: Record<DeviceKind, string> = {
  linux_server: "Server Linux", windows_server: "Server Windows", router: "Router", switch: "Switch",
  access_point: "Access point", cctv: "CCTV", hub: "Hub",
  website: "Website", other: "Komputer / client",
};

const initialInput: DeviceInput = {
  name: "", kind: "switch", address: "", location: "", prometheus_job: "snmp",
  prometheus_target: "", notes: "", is_active: true, room_id: null,
  credential_profile_id: null, stream_url: "", floorplan_x: null, floorplan_y: null,
  asset_tag: null, physical_group: "", physical_position: "", network_role: "endpoint",
  isp_name: "", wan_if_name: "", wan_if_index: null,
};

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
    {editing !== undefined && <DeviceWizard device={editing} locations={locations} onClose={() => setEditing(undefined)} onSaved={async (text) => { setEditing(undefined); setMessage(text); await load(); }}/>} 
  </AppShell>;
}

function DeviceWizard({device, locations, onClose, onSaved}: {device: Device | null; locations: Location[]; onClose: () => void; onSaved: (message: string) => Promise<void>}) {
  const [form, setForm] = useState<DeviceInput>(device ? {
    name: device.name, kind: device.kind, address: device.address, location: device.location,
    prometheus_job: device.prometheus_job, prometheus_target: device.prometheus_target,
    notes: device.notes, is_active: device.is_active, room_id: device.room_id,
    credential_profile_id: device.credential_profile_id, stream_url: device.stream_url,
    floorplan_x: device.floorplan_x, floorplan_y: device.floorplan_y,
    asset_tag: device.asset_tag, physical_group: device.physical_group,
    physical_position: device.physical_position, network_role: device.network_role,
    isp_name: device.isp_name, wan_if_name: device.wan_if_name, wan_if_index: device.wan_if_index,
  } : initialInput);
  const [credential, setCredential] = useState<CredentialSecret>({name: device ? `Akses ${device.name}` : "", kind: "snmp_v2c", community: ""});
  const [step, setStep] = useState(1);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [testResult, setTestResult] = useState("");
  const [savedDevice, setSavedDevice] = useState<Device | null>(device);
  const [discovery, setDiscovery] = useState<DiscoveryResult | null>(null);
  const [portModes, setPortModes] = useState<Record<number, PortExpectation>>({});

  function setField<K extends keyof DeviceInput>(key: K, value: DeviceInput[K]) { setForm((current) => ({...current, [key]: value})); }
  function changeKind(kind: DeviceKind) {
    const prometheus_job = kind === "linux_server" ? "node" : kind === "windows_server" ? "windows" : kind === "website" ? "blackbox" : kind === "switch" ? "snmp" : ["router", "access_point", "other"].includes(kind) ? "icmp" : kind === "cctv" ? "cctv" : "none";
    setForm((current) => ({...current, kind, prometheus_job, credential_profile_id: prometheus_job === "icmp" ? null : current.credential_profile_id, prometheus_target: current.prometheus_target || current.address}));
    setCredential((current) => ({...current, kind: kind === "cctv" ? "onvif_rtsp" : "snmp_v2c"}));
  }
  function secret(): CredentialSecret | undefined {
    if (form.kind === "cctv") return credential.username || credential.password ? {...credential, name: credential.name || `Akses ${form.name}`} : undefined;
    if (!["router", "switch", "access_point"].includes(form.kind) || form.prometheus_job !== "snmp") return undefined;
    if (credential.kind === "snmp_v2c" && !credential.community) return undefined;
    return {...credential, name: credential.name || `Akses ${form.name}`};
  }
  async function testConnection() {
    setError(""); setTestResult("Menguji koneksi…");
    try { const result = await api<{message:string}>("/devices/test-connection", {method:"POST", body:JSON.stringify({address:form.address, kind:form.kind, prometheus_job:form.prometheus_job, stream_url:form.stream_url, credential:secret()})}); setTestResult(result.message); }
    catch (reason) { setTestResult(""); setError(reason instanceof ApiError ? reason.message : "Koneksi tidak dapat diuji"); }
  }
  async function saveAndDiscover(event: FormEvent) {
    event.preventDefault(); setError(""); setSaving(true);
    try {
      const payload = {...form, credential_profile_id: form.prometheus_job === "icmp" ? null : form.credential_profile_id, prometheus_target: form.prometheus_target || form.address, credential: secret()};
      const stored = device ? await api<Device>(`/devices/${device.id}`, {method:"PATCH", body:JSON.stringify(payload)}) : await api<Device>("/devices", {method:"POST", body:JSON.stringify(payload)});
      setSavedDevice(stored);
      const result = await api<DiscoveryResult>(`/devices/${stored.id}/discover`, {method:"POST"});
      if (form.prometheus_job === "icmp") {
        await onSaved(`${stored.name} tersimpan dan monitoring ICMP telah diaktifkan.`);
        return;
      }
      setDiscovery(result); setPortModes(Object.fromEntries(result.ports.map((port) => [port.id, port.expectation]))); setStep(3);
    } catch (reason) { setError(reason instanceof ApiError ? reason.message : "Perangkat tidak dapat disimpan"); }
    finally { setSaving(false); }
  }
  async function finish() {
    if (!savedDevice) return; setSaving(true); setError("");
    try {
      if (form.network_role === "gateway" && form.prometheus_job === "snmp") {
        await api(`/devices/${savedDevice.id}`, {method:"PATCH", body:JSON.stringify({isp_name:form.isp_name,wan_if_name:form.wan_if_name,wan_if_index:form.wan_if_index})});
      }
      if (discovery?.ports.length) await api(`/devices/${savedDevice.id}/port-expectations`, {method:"PUT", body:JSON.stringify({ports:discovery.ports.map((port) => ({port_id:port.id, mode:portModes[port.id] ?? "spare", expected_device_id:null, label:port.alias || port.name}))})});
      await onSaved(`${savedDevice.name} tersimpan. Selanjutnya tempatkan melalui Peta Lokasi.`);
    } catch (reason) { setError(reason instanceof ApiError ? reason.message : "Aturan port tidak dapat disimpan"); }
    finally { setSaving(false); }
  }

  return <><button className="drawer-scrim" aria-label="Tutup formulir" onClick={onClose}/><section className="drawer drawer-wide" role="dialog" aria-modal="true" aria-labelledby="device-form-title">
    <header className="drawer-header"><div><h2 id="device-form-title">{device ? "Edit perangkat" : "Tambah perangkat"}</h2><p>{step === 1 ? "Identitas dan lokasi" : step === 2 ? "Akses monitoring" : "Konfirmasi fungsi port"}</p></div><button className="icon-button" aria-label="Tutup" onClick={onClose}><Icon name="close"/></button></header>
    <div className="drawer-body"><ol className="wizard-steps"><li className={step >= 1 ? "active":""}><span>1</span>Identitas</li><li className={step >= 2 ? "active":""}><span>2</span>Akses</li><li className={step >= 3 ? "active":""}><span>3</span>Port</li></ol>
      <form onSubmit={saveAndDiscover}>{error && <div className="form-error" role="alert">{error}</div>}
        {step === 1 && <IdentityStep form={form} locations={locations} setField={setField} changeKind={changeKind}/>} 
        {step === 2 && <AccessStep form={form} credential={credential} setField={setField} setCredential={setCredential} testResult={testResult}/>} 
        {step === 3 && <PortConfirmation discovery={discovery} portModes={portModes} setPortModes={setPortModes} gateway={form.network_role === "gateway"} ispName={form.isp_name} wanIfIndex={form.wan_if_index} setIspName={(value)=>setField("isp_name",value)} setWan={(port)=>{setField("wan_if_index",port.if_index);setField("wan_if_name",port.name);}}/>}
        <div className="form-actions"><button className="button" type="button" onClick={step === 1 ? onClose : () => setStep(step-1)}>{step === 1 ? "Batal":"Kembali"}</button>{step === 1 ? <button className="button button-primary" type="button" onClick={() => form.name && form.address ? setStep(2) : setError("Nama dan alamat perangkat wajib diisi.")}>Lanjut ke akses</button> : step === 2 ? <><button className="button" type="button" onClick={() => void testConnection()}>Uji koneksi</button><button className="button button-primary" disabled={saving}>{saving ? "Menyimpan…" : form.prometheus_job === "icmp" ? "Simpan & aktifkan ICMP" : "Simpan & temukan port"}</button></> : <button className="button button-primary" type="button" onClick={() => void finish()} disabled={saving}>{saving ? "Menyimpan…":"Simpan aturan port"}</button>}</div>
      </form>
    </div>
  </section></>;
}

function IdentityStep({form, locations, setField, changeKind}: {form:DeviceInput;locations:Location[];setField:<K extends keyof DeviceInput>(key:K,value:DeviceInput[K])=>void;changeKind:(kind:DeviceKind)=>void}) {
  return <div className="form-grid"><div className="field field-full"><label htmlFor="name">Nama perangkat</label><input id="name" required value={form.name} onChange={(e)=>setField("name",e.target.value)}/></div><div className="field"><label htmlFor="kind">Jenis</label><select id="kind" value={form.kind} onChange={(e)=>changeKind(e.target.value as DeviceKind)}>{Object.entries(kindLabels).map(([value,label])=><option value={value} key={value}>{label}</option>)}</select></div><div className="field"><label htmlFor="network-role">Peran jaringan</label><select id="network-role" value={form.network_role} onChange={(e)=>setField("network_role",e.target.value as DeviceInput["network_role"])}><option value="gateway">Gateway ISP</option><option value="distribution">Distribusi pusat</option><option value="access">Akses/cabang</option><option value="endpoint">Perangkat akhir</option></select></div><div className="field"><label htmlFor="room">Ruang</label><select id="room" value={form.room_id ?? ""} onChange={(e)=>setField("room_id",e.target.value?Number(e.target.value):null)}><option value="">Belum dipetakan</option>{locations.filter((item)=>item.kind==="room").map((item)=><option value={item.id} key={item.id}>{locationPath(item,locations)}</option>)}</select></div><div className="field"><label htmlFor="asset-tag">Label aset</label><input id="asset-tag" value={form.asset_tag ?? ""} onChange={(e)=>setField("asset_tag",e.target.value || null)} placeholder="SW-RS-01"/></div><div className="field field-full"><label htmlFor="address">IP atau hostname</label><input id="address" required value={form.address} onChange={(e)=>{setField("address",e.target.value);if(!form.prometheus_target)setField("prometheus_target",e.target.value);}}/></div><div className="field"><label htmlFor="physical-group">Rak atau patokan</label><input id="physical-group" value={form.physical_group} onChange={(e)=>setField("physical_group",e.target.value)} placeholder="Rack 01 / Koridor timur"/></div><div className="field"><label htmlFor="physical-position">Posisi fisik</label><input id="physical-position" value={form.physical_position} onChange={(e)=>setField("physical_position",e.target.value)} placeholder="U12 / plafon dekat pintu"/></div><div className="field field-full"><label htmlFor="location-label">Keterangan posisi lama</label><input id="location-label" value={form.location} onChange={(e)=>setField("location",e.target.value)} placeholder="Opsional untuk kompatibilitas data lama"/></div><div className="field field-full"><label htmlFor="notes">Catatan</label><textarea id="notes" value={form.notes} onChange={(e)=>setField("notes",e.target.value)}/></div></div>;
}

function AccessStep({form, credential, setField, setCredential, testResult}: {form:DeviceInput;credential:CredentialSecret;setField:<K extends keyof DeviceInput>(key:K,value:DeviceInput[K])=>void;setCredential:React.Dispatch<React.SetStateAction<CredentialSecret>>;testResult:string}) {
  const network = ["router","switch","access_point"].includes(form.kind);
  return <div className="form-grid"><div className="field field-full"><label htmlFor="target">Target monitoring</label><input id="target" required value={form.prometheus_target} onChange={(e)=>setField("prometheus_target",e.target.value)}/><small>{form.kind === "linux_server" ? "Contoh: 10.0.0.1:9100" : "Biasanya sama dengan IP perangkat."}</small></div>{network ? <div className="field"><label htmlFor="job">Metode monitoring</label><select id="job" value={form.prometheus_job} onChange={(e)=>{const job=e.target.value;setField("prometheus_job",job);if(job==="icmp")setField("credential_profile_id",null);}}><option value="icmp">ICMP saja (tanpa SNMP)</option><option value="snmp">SNMP dan discovery port</option></select></div> : <div className="field"><label htmlFor="job">Job</label><input id="job" required value={form.prometheus_job} onChange={(e)=>setField("prometheus_job",e.target.value)}/></div>}{form.kind === "cctv" && <><div className="field field-full"><label htmlFor="stream">URL stream RTSP</label><input id="stream" required value={form.stream_url} onChange={(e)=>setField("stream_url",e.target.value)} placeholder="rtsp://alamat:554/path"/></div><SecretField id="camera-user" label="Username kamera" value={credential.username} onChange={(value)=>setCredential((current)=>({...current,username:value}))}/><SecretField id="camera-password" label="Password kamera" password value={credential.password} onChange={(value)=>setCredential((current)=>({...current,password:value}))}/></>}{network && form.prometheus_job === "icmp" && <div className="notice field-full"><span className="notice-mark">i</span><div><strong>Monitoring tanpa SNMP</strong><p>Monitora akan memeriksa online/offline dan latensi melalui ICMP. Port, klien Wi-Fi, dan metrik internal tidak tersedia.</p></div></div>}{network && form.prometheus_job === "snmp" && <><div className="field"><label htmlFor="snmp-kind">Versi SNMP</label><select id="snmp-kind" value={credential.kind} onChange={(e)=>setCredential((current)=>({...current,kind:e.target.value as CredentialSecret["kind"]}))}><option value="snmp_v2c">SNMP v2c</option><option value="snmp_v3">SNMP v3</option></select></div>{credential.kind === "snmp_v2c" ? <SecretField id="community" label="Community read-only" password value={credential.community} onChange={(value)=>setCredential((current)=>({...current,community:value}))}/> : <><SecretField id="snmp-user" label="Username SNMPv3" value={credential.username} onChange={(value)=>setCredential((current)=>({...current,username:value}))}/><SecretField id="snmp-pass" label="Auth password" password value={credential.password} onChange={(value)=>setCredential((current)=>({...current,password:value}))}/><SecretField id="privacy-pass" label="Privacy password" password value={credential.privacy_password} onChange={(value)=>setCredential((current)=>({...current,privacy_password:value}))}/></>}</>}<div className="field-full checkbox-field"><input id="active" type="checkbox" checked={form.is_active} onChange={(e)=>setField("is_active",e.target.checked)}/><label htmlFor="active">Aktifkan monitoring</label></div>{testResult && <div className="notice field-full"><span className="notice-mark">i</span><div><strong>Hasil pemeriksaan</strong><p>{testResult}</p></div></div>}</div>;
}

function SecretField({id,label,value,onChange,password=false}:{id:string;label:string;value?:string;onChange:(value:string)=>void;password?:boolean}) { return <div className="field"><label htmlFor={id}>{label}</label><input id={id} type={password?"password":"text"} value={value??""} onChange={(e)=>onChange(e.target.value)}/></div>; }
function PortConfirmation({discovery,portModes,setPortModes,gateway,ispName,wanIfIndex,setIspName,setWan}:{discovery:DiscoveryResult|null;portModes:Record<number,PortExpectation>;setPortModes:React.Dispatch<React.SetStateAction<Record<number,PortExpectation>>>;gateway:boolean;ispName:string;wanIfIndex:number|null;setIspName:(value:string)=>void;setWan:(port:NetworkPort)=>void}) { if(!discovery)return <EmptyState title="Menunggu discovery" description="Sistem sedang memeriksa kemampuan perangkat."/>; return <div><div className={`notice ${discovery.state==="unavailable"?"notice-warning":""}`}><span className="notice-mark">i</span><div><strong>{discovery.state==="ready"?"Discovery selesai":"Discovery sebagian"}</strong><p>{discovery.message}</p></div></div>{gateway&&<div className="form-grid"><div className="field"><label htmlFor="isp-name">Nama ISP</label><input id="isp-name" value={ispName} onChange={(event)=>setIspName(event.target.value)} placeholder="Contoh: Telkom"/></div><div className="field"><label htmlFor="wan-interface">Interface penerima ISP</label><select id="wan-interface" value={wanIfIndex??""} onChange={(event)=>{const port=discovery.ports.find((item)=>item.if_index===Number(event.target.value));if(port)setWan(port);}}><option value="">Pilih interface WAN</option>{discovery.ports.filter((port)=>port.if_index!=null).map((port)=><option value={port.if_index??""} key={port.id}>{port.name}{port.alias?` — ${port.alias}`:""}</option>)}</select><small>Pilih port MikroTik yang menerima koneksi ISP, misalnya ether1 atau pppoe-out1.</small></div></div>}{discovery.ports.length===0?<EmptyState title="Tidak ada port untuk dikonfirmasi" description="Simpan perangkat dan audit kembali setelah mesin monitoring tersedia."/>:<div className="port-config-list">{discovery.ports.map((port)=><PortConfig key={port.id} port={port} mode={portModes[port.id]??"spare"} onChange={(mode)=>setPortModes((current)=>({...current,[port.id]:mode}))}/>)}</div>}</div>; }
function PortConfig({port,mode,onChange}:{port:NetworkPort;mode:PortExpectation;onChange:(mode:PortExpectation)=>void}) { return <div className="port-config"><div><strong>{port.name}</strong><span>{port.alias||port.description||"Tanpa deskripsi"}</span></div><StatusBadge status={port.oper_status==="up"?"online":"unknown"} label={port.oper_status==="up"?"Sedang aktif":"Kosong/down"}/><select aria-label={`Fungsi ${port.name}`} value={mode} onChange={(e)=>onChange(e.target.value as PortExpectation)}><option value="required">Wajib terisi</option><option value="spare">Cadangan</option><option value="ignored">Diabaikan</option></select></div>; }

function locationPath(location:Location,locations:Location[]){const names=[location.name];let parent=location.parent_id;while(parent){const item=locations.find((entry)=>entry.id===parent);if(!item)break;names.unshift(item.name);parent=item.parent_id;}return names.join(" / ");}
function locationName(id:number|null,locations:Location[]){return id?locations.find((item)=>item.id===id)?.name:"";}
function monitoringLabel(level:string){return level==="full"?"Jaringan lengkap":level==="stream"?"Online + stream":level==="limited"?"Terbatas":"Dasar";}
