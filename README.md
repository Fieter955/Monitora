# Pantau Infrastruktur

Portal internal untuk memantau server Linux, perangkat jaringan, website, alert, dan inventaris teknis. Portal memakai Next.js dan FastAPI sebagai antarmuka operasional; Prometheus dan Grafana tetap menjadi mesin monitoring agar pengumpulan time-series tidak dibuat ulang dari nol.

## Arsitektur

```text
Node Exporter ─┐
SNMP Exporter ─┼── Prometheus ── Grafana
Blackbox ──────┘       │
                       ├── Alertmanager
                       └── FastAPI ── PostgreSQL
                              │
                           Next.js
                              │
                   Nginx / reverse proxy HTTPS
```

- Next.js: login, ringkasan, inventaris, alert, dan laporan.
- FastAPI: autentikasi, role `admin`/`viewer`, CRUD perangkat, service discovery Prometheus, dan laporan CSV.
- PostgreSQL: akun dan inventaris. Sampel CPU/RAM tidak disalin ke database aplikasi.
- Prometheus: metrik dan aturan alert; retensi awal 30 hari.
- Grafana: dashboard historis yang diprovisikan dari repository.
- Node Exporter: CPU, memori, disk, network, dan uptime server Linux.
- Blackbox Exporter: HTTP, SSL, dan ketersediaan website.
- SNMP Exporter: router, switch, dan access point.

Inventaris portal menjadi sumber HTTP service discovery. Target yang ditambah melalui UI akan dibaca Prometheus paling lambat sekitar 30 detik kemudian.

## Menjalankan secara lokal

Prasyarat: Docker Engine dengan Compose v2.

1. Salin `.env.example` menjadi `.env`.
2. Ganti seluruh nilai yang diawali `replace-`. Untuk secret aplikasi gunakan nilai acak minimal 32 karakter.
3. Jalankan:

   ```bash
   docker compose up -d --build
   docker compose ps
   ```

4. Buka `http://localhost:8080` dan masuk memakai `ADMIN_USERNAME` serta `ADMIN_PASSWORD` dari `.env`.
5. Grafana tersedia melalui menu **Buka Grafana** atau `http://localhost:8080/grafana/`.

Nilai bawaan Compose hanya untuk pengembangan. Saat `APP_ENV=production`, backend menolak berjalan bila secret aplikasi atau password admin masih memakai nilai development.

## Alur penggunaan

1. Admin membuka menu **Perangkat** dan menambah target.
2. Untuk server Linux, isi target seperti `10.10.0.12:9100`.
3. Untuk website, isi URL lengkap seperti `https://layanan.example.go.id`.
4. Untuk router/switch/AP, isi IP yang dapat dijangkau server monitoring.
5. Prometheus mengambil target dari FastAPI, menyimpan metrik, dan mengevaluasi aturan setiap 15 detik.
6. Ringkasan tampil di portal; grafik rinci tersedia di Grafana; laporan terkini dapat diunduh sebagai CSV.

## Development tanpa Docker

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Perintah kualitas yang tersedia:

```powershell
cd backend
.\.venv\Scripts\ruff.exe check app alembic tests
.\.venv\Scripts\python.exe -m pytest --cov=app

cd ..\frontend
npm run lint
npm run typecheck
npm run build
npm run ui:smoke
```

`ui:smoke` menguji alur login, dashboard, dan navigasi mobile pada stack Docker yang sedang berjalan. Script memakai Chrome atau Edge yang terpasang di mesin pengembang.

## Keamanan dan UI

- Endpoint Prometheus, exporter, PostgreSQL, FastAPI, dan Grafana tidak dipublikasikan sebagai port host; akses pengguna melewati gateway.
- Dashboard sebaiknya hanya dapat dijangkau melalui LAN atau VPN. Dokumentasi Prometheus juga menyatakan endpoint monitoring tidak seharusnya dibuka langsung ke internet: [Prometheus security model](https://prometheus.io/docs/operating/security/).
- Status tidak dibedakan dengan warna saja, fokus keyboard terlihat, tabel memiliki header semantik, dan layout dapat reflow pada layar kecil, mengikuti [WCAG 2.2](https://www.w3.org/TR/WCAG22/) dan pola komponen layanan publik dari [GOV.UK Design System](https://design-system.service.gov.uk/components/).
- UI memakai bahasa operasional, radius kecil, warna terbatas, dan kepadatan informasi yang sesuai aplikasi internal—bukan gaya landing page atau dashboard template generik.

Panduan produksi, cPanel, firewall, HTTPS, SNMP, backup, dan notifikasi tersedia di [docs/deployment.md](docs/deployment.md).

## Visibilitas jaringan dan lokasi

- **LibreNMS** menangani discovery SNMP lintas vendor, port/interface, bandwidth, sensor, serta link LLDP/CDP.
- **Peta Lokasi** menyimpan hierarki site, gedung, lantai, ruang, denah, dan posisi perangkat.
- **Jalur Koneksi** menampilkan topologi logis dengan nama port dan utilisasi terakhir.
- **CCTV** diperiksa melalui keterjangkauan dan handshake RTSP tanpa mengambil atau menyimpan video.
- **Hub unmanaged** ditandai sebagai monitoring terbatas karena tidak dapat melaporkan kondisi port sendiri.
- Contoh pemasangan LAN kecil tersedia di [denah-jaringan-sederhana.md](docs/denah-jaringan-sederhana.md), termasuk gambar dan alamat IP simulasi.

Alur awal administrator:

1. Buat hierarki dan unggah denah melalui **Peta Lokasi**.
2. Ikuti wizard **Perangkat** untuk menguji akses dan menjalankan discovery.
3. Tandai port sebagai `wajib`, `cadangan`, atau `diabaikan`.
4. Tempatkan perangkat pada denah dan periksa LLDP/CDP melalui **Jalur Koneksi**.

Setelah deployment pertama, buat admin serta API token LibreNMS melalui `http://127.0.0.1:8001`. Masukkan token ke `LIBRENMS_API_TOKEN`, lalu restart service `backend` dan `network-worker`. Port LibreNMS hanya terikat ke loopback host.
"# Monitora" 
"# Monitora" 
