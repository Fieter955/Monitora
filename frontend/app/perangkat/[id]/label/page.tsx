"use client";

import Link from "next/link";
import Image from "next/image";
import {useParams} from "next/navigation";
import {useEffect, useState} from "react";
import QRCode from "qrcode";
import {AppShell, PageHeader} from "@/components/app-shell";
import {api} from "@/lib/api";
import type {Device, Location} from "@/lib/types";

export default function DeviceLabelPage(){
  const params=useParams<{id:string}>();
  const [device,setDevice]=useState<Device|null>(null);
  const [locations,setLocations]=useState<Location[]>([]);
  const [qr,setQr]=useState("");
  useEffect(()=>{const id=Number(params.id);if(!id)return;Promise.all([api<Device>(`/devices/${id}`),api<Location[]>("/locations")]).then(([item,locationData])=>{setDevice(item);setLocations(locationData);return QRCode.toDataURL(`${window.location.origin}/perangkat?device=${id}`,{width:320,margin:1,errorCorrectionLevel:"M"});}).then(setQr);},[params.id]);
  return <AppShell><div className="print-hidden"><PageHeader eyebrow="Inventaris fisik" title="Label perangkat" description="Cetak dan tempel label ini pada perangkat yang sesuai." actions={<><Link className="button" href="/perangkat">Kembali</Link><button className="button button-primary" onClick={()=>window.print()}>Cetak label</button></>}/></div>{device?<section className="asset-label" aria-label={`Label ${device.name}`}><div className="asset-label-copy"><p>MONITORA · ASET JARINGAN</p><h1>{device.asset_tag||device.name}</h1><h2>{device.name}</h2><dl><div><dt>Lokasi</dt><dd>{locationPath(device.room_id,locations)||device.location||"Belum dicatat"}</dd></div><div><dt>Rak/patokan</dt><dd>{device.physical_group||"—"}</dd></div><div><dt>Posisi</dt><dd>{device.physical_position||"—"}</dd></div><div><dt>Alamat</dt><dd>{device.address}</dd></div></dl></div>{qr&&<div className="asset-qr"><Image unoptimized width={210} height={210} src={qr} alt="QR menuju detail perangkat"/><small>Pindai untuk membuka kondisi perangkat</small></div>}</section>:<p className="empty-state">Memuat label…</p>}</AppShell>;
}

function locationPath(id:number|null,locations:Location[]){const names:string[]=[];let current=id;while(current!=null){const item=locations.find((entry)=>entry.id===current);if(!item)break;names.unshift(item.name);current=item.parent_id;}return names.join(" / ");}
