"use client";

import Link from "next/link";
import {FormEvent, useCallback, useEffect, useMemo, useState} from "react";
import {AppShell, PageHeader} from "@/components/app-shell";
import {DeviceHealthDrawer} from "@/components/device-health-drawer";
import {Icon} from "@/components/icons";
import {EmptyState, StatusBadge} from "@/components/status";
import {api, apiForm, ApiError} from "@/lib/api";
import type {Device, Floorplan, Location, LocationKind, ProblemLocator, Topology, User} from "@/lib/types";

const locationLabels: Record<LocationKind, string> = {site:"Site",building:"Gedung",floor:"Lantai",room:"Ruang"};
const severityWeight = {critical: 2, warning: 1, healthy: 0, unknown: -1};

type Marker = {key:string;x:number;y:number;devices:Device[];status:"healthy"|"warning"|"critical"|"unknown"};

export default function ProblemLocatorPage() {
  const [locations,setLocations]=useState<Location[]>([]);
  const [floorplans,setFloorplans]=useState<Floorplan[]>([]);
  const [devices,setDevices]=useState<Device[]>([]);
  const [topology,setTopology]=useState<Topology|null>(null);
  const [problems,setProblems]=useState<ProblemLocator[]>([]);
  const [user,setUser]=useState<User|null>(null);
  const [selectedLocation,setSelectedLocation]=useState<number|null>(null);
  const [selectedDevice,setSelectedDevice]=useState<Device|null>(null);
  const [drawerDevice,setDrawerDevice]=useState<Device|null>(null);
  const [selectedMarker,setSelectedMarker]=useState<string|null>(null);
  const [placingIds,setPlacingIds]=useState<number[]>([]);
  const [placementGroup,setPlacementGroup]=useState("");
  const [managing,setManaging]=useState(false);
  const [showSiteMap,setShowSiteMap]=useState(false);
  const [search,setSearch]=useState("");
  const [message,setMessage]=useState("");

  const load=useCallback(async()=>{
    const [locationData,floorplanData,deviceData,topologyData,problemData,me]=await Promise.all([
      api<Location[]>("/locations"),api<Floorplan[]>("/locations/floorplans"),api<Device[]>("/devices"),
      api<Topology>("/topology"),api<ProblemLocator[]>("/operations/problems"),api<User>("/auth/me"),
    ]);
    setLocations(locationData);setFloorplans(floorplanData);setDevices(deviceData);setTopology(topologyData);setProblems(problemData);setUser(me);
    const requested=Number(new URLSearchParams(window.location.search).get("device"));
    const requestedDevice=deviceData.find((item)=>item.id===requested);
    if(requestedDevice){
      setSelectedDevice(requestedDevice);
      setSelectedLocation(findFloorplanLocation(requestedDevice.room_id,locationData,floorplanData)??requestedDevice.room_id);
    } else {
      setSelectedLocation((current)=>current??floorplanData[0]?.location_id??locationData.find((item)=>item.kind==="floor"||item.kind==="room")?.id??locationData[0]?.id??null);
    }
  },[]);
  useEffect(()=>{const initial=window.setTimeout(()=>void load(),0);const timer=window.setInterval(()=>void load(),30_000);return()=>{window.clearTimeout(initial);window.clearInterval(timer);};},[load]);

  const orderedLocations=useMemo(()=>orderLocations(locations),[locations]);
  const visibleIds=useMemo(()=>descendantsOf(selectedLocation,locations),[selectedLocation,locations]);
  const visibleDevices=devices.filter((device)=>device.room_id!=null&&visibleIds.has(device.room_id));
  const floorplan=floorplans.find((item)=>item.location_id===selectedLocation);
  const statusById=new Map(topology?.nodes.map((node)=>[node.id,node.status]));
  const placedDevices=visibleDevices.filter((device)=>device.floorplan_x!=null&&device.floorplan_y!=null);
  const unplacedDevices=visibleDevices.filter((device)=>device.floorplan_x==null||device.floorplan_y==null);
  const markers=buildMarkers(placedDevices,statusById);
  const activeMarker=markers.find((marker)=>marker.key===selectedMarker);
  const selectedProblem=selectedDevice?problems.find((problem)=>problem.device_id===selectedDevice.id):undefined;
  const selectedLocationRecord=locations.find((item)=>item.id===selectedLocation);
  const filteredProblems=problems.filter((problem)=>`${problem.name} ${problem.address} ${problem.asset_tag??""} ${problem.location_path.join(" ")} ${problem.physical_group}`.toLocaleLowerCase("id").includes(search.toLocaleLowerCase("id")));

  function focusDevice(device:Device){
    setSelectedDevice(device);setSelectedMarker(null);
    const locationId=findFloorplanLocation(device.room_id,locations,floorplans)??device.room_id;
    if(locationId)setSelectedLocation(locationId);
    const url=new URL(window.location.href);url.searchParams.set("device",String(device.id));window.history.replaceState({},"",url);
  }
  function togglePlacement(device:Device){
    setPlacingIds((current)=>{
      if(current.includes(device.id))return current.filter((id)=>id!==device.id);
      const first=devices.find((item)=>item.id===current[0]);
      if(first&&first.room_id!==device.room_id){setMessage("Pilih perangkat dari ruang yang sama untuk penempatan massal.");return current;}
      return [...current,device.id];
    });
  }
  async function place(x:number,y:number){
    if(user?.role!=="admin"||placingIds.length===0)return;
    const selected=devices.filter((device)=>placingIds.includes(device.id));
    if(selected.length===1){
      await api<Device>(`/devices/${selected[0].id}`,{method:"PATCH",body:JSON.stringify({floorplan_x:x,floorplan_y:y,physical_group:placementGroup})});
    }else{
      await api<Device[]>("/devices/bulk-placement",{method:"PATCH",body:JSON.stringify({device_ids:placingIds,room_id:selected[0].room_id,floorplan_x:x,floorplan_y:y,physical_group:placementGroup})});
    }
    setMessage(`${selected.length} perangkat ditempatkan pada denah.`);setPlacingIds([]);setPlacementGroup("");await load();
  }
  async function moveDevice(deviceId:number,x:number,y:number){await api<Device>(`/devices/${deviceId}`,{method:"PATCH",body:JSON.stringify({floorplan_x:x,floorplan_y:y})});setMessage("Posisi perangkat diperbarui.");await load();}
  function canvasPosition(event:React.MouseEvent<HTMLDivElement>|React.DragEvent<HTMLDivElement>){const rect=event.currentTarget.getBoundingClientRect();return{x:Math.max(0,Math.min(100,((event.clientX-rect.left)/rect.width)*100)),y:Math.max(0,Math.min(100,((event.clientY-rect.top)/rect.height)*100))};}

  return <AppShell>
    <PageHeader eyebrow="Operasional lapangan" title="Pencari Gangguan" description="Mulai dari perangkat bermasalah, temukan ruang dan label fisiknya, lalu buka jalur jaringan hanya bila diperlukan." actions={user?.role==="admin"?<button className="button" onClick={()=>setManaging(true)}><Icon name="edit"/>Atur lokasi & denah</button>:undefined}/>
    {message&&<div className="notice" role="status"><span className="notice-mark">i</span><div><strong>Peta diperbarui</strong><p>{message}</p></div></div>}
    <div className="locator-toolbar panel"><label htmlFor="problem-search">Cari perangkat, IP, label, atau ruang</label><input id="problem-search" type="search" value={search} onChange={(event)=>setSearch(event.target.value)} placeholder="Contoh: SW-RS-01 atau Ruang Server"/><span>{problems.length} gangguan aktif</span></div>
    <div className="locator-layout">
      <aside className="problem-browser panel" aria-label="Gangguan aktif">
        <div className="panel-header"><div><h2>Perlu diperiksa</h2><p>Kritis ditampilkan lebih dahulu</p></div></div>
        {filteredProblems.length===0?<EmptyState title="Tidak ada gangguan yang cocok" description={problems.length?"Ubah kata pencarian untuk melihat perangkat lain.":"Seluruh pemeriksaan yang tersedia dalam kondisi normal."}/>:<div className="problem-list">{filteredProblems.map((problem)=><button key={problem.device_id} className={selectedDevice?.id===problem.device_id?"active":""} onClick={()=>{const device=devices.find((item)=>item.id===problem.device_id);if(device)focusDevice(device);}}><StatusBadge status={problem.status}/><span><strong>{problem.name}</strong><small>{problem.location_path.join(" / ")||"Lokasi belum dicatat"}</small><small>{problem.asset_tag||problem.physical_group||problem.address}</small></span><span className="problem-count">{problem.issues.length||1}</span></button>)}</div>}
        <div className="location-section"><h3>Jelajah lokasi</h3><div className="location-tree">{orderedLocations.map((location)=><button key={location.id} className={selectedLocation===location.id?"active":""} style={{paddingLeft:`${10+locationDepth(location,locations)*15}px`}} onClick={()=>{setSelectedLocation(location.id);setSelectedDevice(null);setSelectedMarker(null);setShowSiteMap(false);}}><span className={`location-kind kind-${location.kind}`}/><span><strong>{location.name}</strong><small>{locationLabels[location.kind]}</small></span></button>)}</div></div>
      </aside>
      <section className="floorplan-panel panel" aria-labelledby="floorplan-title">
        <div className="panel-header"><div><h2 id="floorplan-title">{selectedLocationRecord?.name??"Denah lokasi"}</h2><p>{placedDevices.length} ditempatkan · {unplacedDevices.length} belum ditempatkan</p></div>{placingIds.length>0&&<span className="placing-hint">Klik posisi untuk {placingIds.length} perangkat</span>}</div>
        {floorplan?<div className={`floorplan-canvas ${placingIds.length?"placing":""}`} style={{backgroundImage:`url(${floorplan.image_url})`}} onClick={(event)=>{if(placingIds.length){const position=canvasPosition(event);void place(position.x,position.y);}}} onDragOver={(event)=>event.preventDefault()} onDrop={(event)=>{event.preventDefault();const id=Number(event.dataTransfer.getData("text/device-id"));if(id){const position=canvasPosition(event);void moveDevice(id,position.x,position.y);}}}>{markers.map((marker)=>{const selected=marker.devices.some((device)=>device.id===selectedDevice?.id);return <button key={marker.key} draggable={user?.role==="admin"&&marker.devices.length===1} className={`map-device map-device-${marker.status} ${selected?"map-device-selected":""}`} style={{left:`${marker.x}%`,top:`${marker.y}%`}} onDragStart={(event)=>event.dataTransfer.setData("text/device-id",String(marker.devices[0].id))} onClick={(event)=>{event.stopPropagation();if(marker.devices.length===1)focusDevice(marker.devices[0]);else{setSelectedDevice(null);setSelectedMarker(marker.key);}}} aria-label={`${markerLabel(marker)}, ${healthLabel(marker.status)}`}><DeviceGlyph kind={marker.devices[0].kind}/><span>{markerLabel(marker)}</span>{marker.devices.length>1&&<b>{marker.devices.length}</b>}</button>;})}</div>:selectedLocationRecord?.kind==="site"?<SiteDetail site={selectedLocationRecord} showMap={showSiteMap} onShowMap={()=>setShowSiteMap(true)}/>:<EmptyState title="Denah belum tersedia" description="Lokasi tetap dapat ditemukan melalui hierarki dan label fisik. Admin dapat mengunggah gambar denah bila diperlukan."/>}
        {floorplan&&<div className="map-legend"><span><i className="legend-dot healthy"/>Sehat</span><span><i className="legend-dot warning"/>Perlu perhatian</span><span><i className="legend-dot critical"/>Bermasalah</span><span>Lingkaran bernomor = beberapa perangkat</span></div>}
      </section>
      <aside className="locator-detail panel">
        <div className="panel-header"><div><h2>Lokasi & tindakan</h2><p>Informasi untuk petugas lapangan</p></div></div>
        {selectedDevice?<div className="locator-device-detail"><StatusBadge status={selectedProblem?.status??statusById.get(selectedDevice.id)??"unknown"}/><h3>{selectedDevice.name}</h3><p className="location-breadcrumb">{locationPathForId(selectedDevice.room_id,locations).join(" → ")||"Lokasi belum dicatat"}</p><dl className="definition-list"><div><dt>Label aset</dt><dd>{selectedDevice.asset_tag||"Belum ada"}</dd></div><div><dt>Rak/patokan</dt><dd>{selectedDevice.physical_group||"Belum ada"}</dd></div><div><dt>Posisi</dt><dd>{selectedDevice.physical_position||"Belum ada"}</dd></div><div><dt>Alamat</dt><dd>{selectedDevice.address}</dd></div></dl>{selectedProblem?.issues.length?<div className="locator-actions"><h3>Yang perlu diperiksa</h3>{selectedProblem.issues.map((issue,index)=><article className={`issue-card issue-${issue.severity}`} key={`${issue.code}-${index}`}><span>!</span><div><strong>{issue.title}</strong><p>{issue.detail}</p></div></article>)}</div>:<p className="muted">Tidak ada masalah aktif pada pemeriksaan terbaru.</p>}<div className="detail-buttons"><button className="button button-primary" onClick={()=>setDrawerDevice(selectedDevice)}>Buka detail kondisi</button><Link className="button" href={`/topologi?device=${selectedDevice.id}&scope=path`}><Icon name="topology"/>Lihat jalur</Link></div></div>:activeMarker?<div className="group-detail"><h3>{activeMarker.devices[0].physical_group||"Perangkat berdekatan"}</h3><p>Pilih perangkat untuk melihat label dan tindakan.</p>{activeMarker.devices.map((device)=><button key={device.id} onClick={()=>focusDevice(device)}><DeviceGlyph kind={device.kind}/><span><strong>{device.name}</strong><small>{device.asset_tag||device.address}</small></span><StatusBadge status={statusById.get(device.id)??"unknown"} label=""/></button>)}</div>:<PlacementPanel devices={unplacedDevices} selectedIds={placingIds} group={placementGroup} isAdmin={user?.role==="admin"} onGroup={setPlacementGroup} onToggle={togglePlacement}/>}
      </aside>
    </div>
    <DeviceHealthDrawer device={drawerDevice} onClose={()=>setDrawerDevice(null)}/>
    {managing&&<LocationManager locations={locations} selectedLocation={selectedLocation} onClose={()=>setManaging(false)} onSaved={async(text)=>{setMessage(text);await load();}}/>}
  </AppShell>;
}

function PlacementPanel({devices,selectedIds,group,isAdmin,onGroup,onToggle}:{devices:Device[];selectedIds:number[];group:string;isAdmin:boolean;onGroup:(value:string)=>void;onToggle:(device:Device)=>void}){return <div className="placement-panel"><h3>Belum ditempatkan</h3><p>{isAdmin?"Pilih satu atau beberapa perangkat dari ruang yang sama, lalu klik denah.":"Admin dapat menempatkan perangkat pada denah."}</p>{isAdmin&&devices.length>0&&<div className="field"><label htmlFor="placement-group">Rak atau patokan bersama</label><input id="placement-group" value={group} onChange={(event)=>onGroup(event.target.value)} placeholder="Contoh: Rack 01"/></div>}{devices.length===0?<EmptyState title="Semua sudah dipetakan" description="Tidak ada perangkat yang menunggu penempatan."/>:<div className="unplaced-list">{devices.map((device)=><button key={device.id} className={selectedIds.includes(device.id)?"active":""} onClick={()=>onToggle(device)} disabled={!isAdmin}><DeviceGlyph kind={device.kind}/><span><strong>{device.name}</strong><small>{device.asset_tag||device.address}</small></span><span>{selectedIds.includes(device.id)?"✓":"+"}</span></button>)}</div>}</div>;}

function SiteDetail({site,showMap,onShowMap}:{site:Location;showMap:boolean;onShowMap:()=>void}){const query=site.latitude!=null&&site.longitude!=null?`${site.latitude},${site.longitude}`:site.address||site.name;return <div className="site-detail"><Icon name="map"/><h3>{site.name}</h3><p>{site.address||"Alamat site belum diisi."}</p>{showMap?<iframe src={`https://maps.google.com/maps?q=${encodeURIComponent(query)}&z=15&output=embed`} title={`Peta ${site.name}`} loading="lazy" referrerPolicy="no-referrer-when-downgrade"/>:<button className="button" onClick={onShowMap}>Tampilkan peta geografis</button>}</div>;}

function LocationManager({locations,selectedLocation,onClose,onSaved}:{locations:Location[];selectedLocation:number|null;onClose:()=>void;onSaved:(text:string)=>Promise<void>}){const [name,setName]=useState("");const [kind,setKind]=useState<LocationKind>(locations.length?"building":"site");const [parentId,setParentId]=useState<number|null>(selectedLocation);const [address,setAddress]=useState("");const [latitude,setLatitude]=useState("");const [longitude,setLongitude]=useState("");const [file,setFile]=useState<File|null>(null);const [error,setError]=useState("");const expected:Partial<Record<LocationKind,LocationKind>>={building:"site",floor:"building",room:"floor"};const parents=locations.filter((item)=>item.kind===expected[kind]);const selectedSite=findAncestorSite(selectedLocation,locations);
  async function add(event:FormEvent){event.preventDefault();setError("");try{await api<Location>("/locations",{method:"POST",body:JSON.stringify({name,kind,parent_id:kind==="site"?null:parentId,address:kind==="site"?address:"",latitude:kind==="site"&&latitude?Number(latitude):null,longitude:kind==="site"&&longitude?Number(longitude):null})});setName("");await onSaved(`${name} berhasil ditambahkan.`);}catch(reason){setError(reason instanceof ApiError?reason.message:"Lokasi tidak dapat disimpan");}}
  async function upload(event:FormEvent){event.preventDefault();if(!selectedLocation||!file)return;const form=new FormData();form.append("file",file);try{await apiForm<Floorplan>(`/locations/${selectedLocation}/floorplan`,form);await onSaved("Denah berhasil diperbarui.");}catch(reason){setError(reason instanceof ApiError?reason.message:"Denah tidak dapat diunggah");}}
  async function rename(location:Location){const next=window.prompt("Nama lokasi baru",location.name)?.trim();if(!next||next===location.name)return;try{await api<Location>(`/locations/${location.id}`,{method:"PATCH",body:JSON.stringify({name:next})});await onSaved(`${location.name} diubah menjadi ${next}.`);}catch(reason){setError(reason instanceof ApiError?reason.message:"Lokasi tidak dapat diubah");}}
  async function remove(location:Location){if(!window.confirm(`Hapus ${location.name}?`))return;try{await api(`/locations/${location.id}`,{method:"DELETE"});await onSaved(`${location.name} berhasil dihapus.`);}catch(reason){setError(reason instanceof ApiError?reason.message:"Lokasi tidak dapat dihapus");}}
  return <><button className="drawer-scrim" aria-label="Tutup pengaturan" onClick={onClose}/><section className="drawer" role="dialog" aria-modal="true" aria-labelledby="manager-title"><header className="drawer-header"><div><h2 id="manager-title">Atur lokasi & denah</h2><p>Susun site, gedung, lantai, dan ruang.</p></div><button className="icon-button" onClick={onClose} aria-label="Tutup"><Icon name="close"/></button></header><div className="drawer-body">{error&&<div className="form-error" role="alert">{error}</div>}<form onSubmit={add} className="stacked-form"><h3>Tambah lokasi</h3><div className="field"><label htmlFor="location-kind">Jenis</label><select id="location-kind" value={kind} onChange={(event)=>{setKind(event.target.value as LocationKind);setParentId(null);}}><option value="site">Site</option><option value="building">Gedung</option><option value="floor">Lantai</option><option value="room">Ruang</option></select></div>{kind!=="site"&&<div className="field"><label htmlFor="location-parent">Induk</label><select id="location-parent" required value={parentId??""} onChange={(event)=>setParentId(Number(event.target.value))}><option value="">Pilih induk</option>{parents.map((item)=><option value={item.id} key={item.id}>{item.name}</option>)}</select></div>}<div className="field"><label htmlFor="location-name">Nama</label><input id="location-name" required value={name} onChange={(event)=>setName(event.target.value)}/></div>{kind==="site"&&<><div className="field"><label htmlFor="site-address">Alamat</label><input id="site-address" value={address} onChange={(event)=>setAddress(event.target.value)}/></div><div className="form-grid"><div className="field"><label htmlFor="site-latitude">Latitude</label><input id="site-latitude" type="number" step="any" value={latitude} onChange={(event)=>setLatitude(event.target.value)}/></div><div className="field"><label htmlFor="site-longitude">Longitude</label><input id="site-longitude" type="number" step="any" value={longitude} onChange={(event)=>setLongitude(event.target.value)}/></div></div></>}<button className="button button-primary">Tambah lokasi</button></form>{selectedSite&&<SiteEditor site={selectedSite} onSaved={onSaved}/>}<form onSubmit={upload} className="stacked-form upload-form"><h3>Unggah denah lokasi terpilih</h3><p className="muted">PNG, JPG, atau WebP, maksimal 10 MB.</p><div className="field"><label htmlFor="floorplan-file">Berkas denah</label><input id="floorplan-file" type="file" accept="image/png,image/jpeg,image/webp" onChange={(event)=>setFile(event.target.files?.[0]??null)}/></div><button className="button" disabled={!selectedLocation||!file}>Unggah denah</button></form><section className="managed-locations"><h3>Lokasi terdaftar</h3>{orderLocations(locations).map((location)=><div key={location.id} style={{paddingLeft:`${locationDepth(location,locations)*14}px`}}><span><strong>{location.name}</strong><small>{locationLabels[location.kind]}</small></span><button type="button" className="icon-button" aria-label={`Ubah ${location.name}`} onClick={()=>void rename(location)}><Icon name="edit"/></button><button type="button" className="icon-button" aria-label={`Hapus ${location.name}`} onClick={()=>void remove(location)}><Icon name="trash"/></button></div>)}</section></div></section></>;
}

function SiteEditor({site,onSaved}:{site:Location;onSaved:(text:string)=>Promise<void>}){const [address,setAddress]=useState(site.address);const [latitude,setLatitude]=useState(site.latitude?.toString()??"");const [longitude,setLongitude]=useState(site.longitude?.toString()??"");return <form className="stacked-form" onSubmit={async(event)=>{event.preventDefault();await api<Location>(`/locations/${site.id}`,{method:"PATCH",body:JSON.stringify({address,latitude:latitude?Number(latitude):null,longitude:longitude?Number(longitude):null})});await onSaved(`Detail ${site.name} diperbarui.`);}}><h3>Detail geografis {site.name}</h3><div className="field"><label htmlFor="edit-site-address">Alamat</label><input id="edit-site-address" value={address} onChange={(event)=>setAddress(event.target.value)}/></div><div className="form-grid"><div className="field"><label htmlFor="edit-latitude">Latitude</label><input id="edit-latitude" type="number" step="any" value={latitude} onChange={(event)=>setLatitude(event.target.value)}/></div><div className="field"><label htmlFor="edit-longitude">Longitude</label><input id="edit-longitude" type="number" step="any" value={longitude} onChange={(event)=>setLongitude(event.target.value)}/></div></div><button className="button">Simpan detail site</button></form>;}

function buildMarkers(devices:Device[],statuses:Map<number,string>):Marker[]{const groups=new Map<string,Device[]>();for(const device of devices){const key=device.physical_group.trim()?`${device.room_id}:${device.physical_group.trim().toLocaleLowerCase("id")}`:`device:${device.id}`;groups.set(key,[...(groups.get(key)??[]),device]);}return [...groups].map(([key,members])=>{const first=members[0];const status=members.map((device)=>statuses.get(device.id)??"unknown").sort((a,b)=>(severityWeight[b as keyof typeof severityWeight]??-1)-(severityWeight[a as keyof typeof severityWeight]??-1))[0] as Marker["status"];return{key,x:first.floorplan_x!,y:first.floorplan_y!,devices:members,status};});}
function markerLabel(marker:Marker){return marker.devices.length>1?(marker.devices[0].physical_group||"Kelompok perangkat"):marker.devices[0].name;}
function descendantsOf(selected:number|null,locations:Location[]){if(selected==null)return new Set<number>();const result=new Set<number>([selected]);let changed=true;while(changed){changed=false;for(const item of locations)if(item.parent_id!=null&&result.has(item.parent_id)&&!result.has(item.id)){result.add(item.id);changed=true;}}return result;}
function findFloorplanLocation(roomId:number|null,locations:Location[],floorplans:Floorplan[]){let current=roomId;while(current!=null){if(floorplans.some((item)=>item.location_id===current))return current;current=locations.find((item)=>item.id===current)?.parent_id??null;}return null;}
function findAncestorSite(id:number|null,locations:Location[]){let current=id;while(current!=null){const item=locations.find((entry)=>entry.id===current);if(!item)return undefined;if(item.kind==="site")return item;current=item.parent_id;}return locations.find((item)=>item.kind==="site");}
function locationPathForId(id:number|null,locations:Location[]){const names:string[]=[];let current=id;while(current!=null){const item=locations.find((entry)=>entry.id===current);if(!item)break;names.unshift(item.name);current=item.parent_id;}return names;}
function locationDepth(location:Location,locations:Location[]){return Math.max(0,locationPathForId(location.id,locations).length-1);}
function orderLocations(locations:Location[]){const result:Location[]=[];const visit=(parent:number|null)=>locations.filter((item)=>item.parent_id===parent).sort((a,b)=>a.sort_order-b.sort_order||a.name.localeCompare(b.name,"id")).forEach((item)=>{result.push(item);visit(item.id);});visit(null);return result;}
function healthLabel(status:string){return status==="healthy"?"sehat":status==="critical"?"bermasalah":status==="warning"?"perlu perhatian":"belum diketahui";}
function DeviceGlyph({kind}:{kind:Device["kind"]}){return <span className="device-glyph" aria-hidden="true">{kind==="cctv"?"CAM":kind==="access_point"?"AP":kind==="switch"?"SW":kind==="router"?"RT":kind==="hub"?"HB":kind==="linux_server"?"SRV":"DEV"}</span>;}
