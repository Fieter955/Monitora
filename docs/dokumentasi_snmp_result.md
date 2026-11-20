# Hasil Integrasi Monitoring SNMP MikroTik — Monitora

Ringkasan arsitektur jaringan, kendala teknis, dan solusi implementasi monitoring bandwidth MikroTik menggunakan **Monitora** (SNMP Exporter, Prometheus, Grafana, dan LibreNMS).

---

## 1. Arsitektur Jaringan Instansi

```text
[Server Monitora] (192.168.0.231)
        │  Segmen Server (192.168.0.0/24)
        ▼
[MikroTik Astinet Bigdata] (192.168.0.1 / 12.12.12.1)
        │  NAT + Link Point-to-Point (12.12.12.0/24)
        │  (paket dari 192.168.0.231 terbaca sebagai 12.12.12.1)
        ▼
[MikroTik Staff — RB1100AHx4] (ether5: 12.12.12.2)
  ├── ether1-ISP    (192.168.1.3/24)  ──► Jaringan ISP / WAN (Aktif)
  ├── ether3-Staff  (192.168.30.1/24) ──► LAN & Wi-Fi Staff (Aktif)
  ├── ether2-Laptop (192.168.20.1/24) ──► Port Laptop (Fleksibel)
  └── ether4, ether6–ether13          ──► Port Cadangan (Kosong)
```

### Interface `MikroTik Staff` (RouterOS `6.49.13`)
| Interface | Alamat IP | Fungsi & Aturan Port di Monitora |
| :--- | :--- | :--- |
| `ether1-ISP` | `192.168.1.3/24` | Jalur WAN / penerima ISP — **Wajib terisi** |
| `ether2-Laptop` | `192.168.20.1/24` | Port uji/laptop — **Diabaikan** |
| `ether3-Staff` | `192.168.30.1/24` | Distribusi jaringan Staff — **Wajib terisi** |
| `ether5-Miktotik astinet Bigdata` | `12.12.12.2/24` | Link ke MikroTik Bigdata & target SNMP — **Wajib terisi** |
| `ether4`, `ether6`–`ether13` | — | Port kosong — **Cadangan** |

### Alur Data Monitoring
- **Bandwidth, Status Link & Resource:** `MikroTik Staff (12.12.12.2)` ← SNMP v2c (UDP `161`, modul `if_mib`, `hrDevice`, `hrStorage`, `system`) via `snmp-exporter` → `Prometheus` → `Grafana` (dashboard **Perangkat Jaringan**) & Ringkasan Portal **Monitora**.
- **Inventaris 13 Port & Kesehatan:** `MikroTik Staff` ← `LibreNMS` ← `backend` & `network-worker` → `PostgreSQL` → Portal **Monitora**.

---

## 2. Masalah yang Dihadapi & Solusinya

| # | Masalah | Penyebab | Solusi |
| :--- | :--- | :--- | :--- |
| 1 | **SNMP timeout (`request timeout`)** | Trafik dari server `192.168.0.231` di-NAT oleh `MikroTik Astinet Bigdata`, sehingga tiba di `MikroTik Staff` sebagai `src-address` `12.12.12.1` dan ditolak filter `/32`. | Mengizinkan `192.168.0.231/32,12.12.12.1/32` pada community SNMP read-only di MikroTik serta menonaktifkan community bawaan `public` (`::/0`). |
| 2 | **`snmp-exporter` gagal auth (`office_v2` HTTP 500)** | Flag `--config.expand-environment-variables` milik `snmp_exporter` tidak mengekspansi `${SNMP_COMMUNITY}` pada field `community` SNMPv2c. | Mengubah `compose.yaml` pada service `snmp-exporter` agar merender `/tmp/auth.yml` dari env `SNMP_COMMUNITY` (`.env`) saat startup container, tanpa menyimpan rahasia di `infra/snmp/auth.yml`. |
| 3 | **LibreNMS `get_ports` ditolak (`HTTP 400`)** | LibreNMS `26.6.1` menolak kolom `ifHighSpeed`, `ifInDiscards_delta`, dan `ifOutDiscards_delta`. | Menghapus ketiga kolom tersebut di `backend/services/librenms.py` dan menampilkan pesan JSON error asli dari LibreNMS pada `LibreNMSUnavailable`. |
| 4 | **LibreNMS `add_device` error duplikat (`HTTP 500`)** | Error `HTTP 400` sebelumnya memicu `db.rollback()` sehingga `librenms_device_id` di DB Monitora kembali `NULL`, lalu percobaan ulang mengirim `POST /api/v0/devices` duplikat. | Menambahkan `find_device_by_hostname` di `backend/services/librenms.py` agar `add_device` memakai ulang `device_id` yang sudah terdaftar di LibreNMS. |
| 5 | **Peringatan `Data monitoring terlambat` (`network-worker`)** | Proses standalone `network-worker` gagal dengan `NoReferencedTableError` karena tabel `locations` belum terdaftar di metadata SQLAlchemy. | Mengimpor `CredentialProfile` dan `Location` di `backend/models/device.py` serta menambahkan unit test isolasi `network_worker`. |
| 6 | **Warning `VSPHERE_PASSWORD` di Docker Compose** | Variabel opsional profil `vmware` belum memiliki nilai default kosong. | Mengubah `${VSPHERE_PASSWORD}` menjadi `${VSPHERE_PASSWORD:-}` di `compose.yaml`. |

---

## 3. Catatan Tampilan & Hasil Akhir

- **Panel ICMP `No data` di Grafana Perangkat Jaringan:** bukan error. Job `icmp` hanya berisi perangkat *ICMP-only* (MikroTik masuk ke **Perangkat SNMP** dan **Status Gateway**).
- **CPU, Memori, Disk & Uptime MikroTik via SNMP:** diambil bersama modul `if_mib` menggunakan modul bawaan `snmp_exporter` (`hrDevice`, `hrStorage`, `system`) dan ditampilkan pada Ringkasan **Kesehatan perangkat**, alert CPU/Memori Prometheus, serta panel resource di Grafana **Perangkat Jaringan**.
- **Hasil akhir:**
  - Seluruh **13 port** `MikroTik Staff` terdeteksi di Monitora dan aturan port WAN (`ether1-ISP`) aktif.
  - Grafik bandwidth, CPU, Memori, dan Disk realtime & historis aktif di Grafana (**Perangkat Jaringan**).
  - Sinkronisasi `network-worker` berjalan normal dan metrik CPU/Memori/Disk perangkat SNMP terintegrasi ke Ringkasan Monitora.
