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

## Monitoring router tanpa SNMP

Istilah **managed** pada router berarti perangkat dapat dikonfigurasi melalui web UI, aplikasi, atau cloud. Ini tidak otomatis berarti perangkat menyediakan SNMP, API publik, NetFlow, atau metrik internal yang dapat dibaca sistem monitoring.

| Perangkat | Management | SNMP | Monitoring yang stabil |
| --- | --- | --- | --- |
| TP-Link TL-WR840N | Web UI dan Tether (bergantung versi firmware) | Tidak tersedia | ICMP, TCP/HTTP web UI, serta pemeriksaan koneksi internet dari LAN |
| Ruijie Reyee RG-EW1200G Pro | EWEB dan Ruijie Cloud | Tidak tersedia pada seri EW | ICMP, TCP/HTTP EWEB, dan Ruijie Cloud/API bila akses akun tersedia |

Ruijie menyatakan bahwa tidak ada perangkat seri EW yang mendukung SNMP; dukungan tersebut tersedia pada model tertentu seri EG. Lihat [jawaban Ruijie](https://community.ruijie.com/forum.php?mod=viewthread&tid=8958). Untuk TL-WR840N, web UI menyediakan status/uptime, daftar klien DHCP dan Wi-Fi, log, serta statistik trafik; ketersediaan menu dapat berbeda menurut versi perangkat keras dan firmware. Lihat [manual TP-Link](https://www.tp-link.com/us/user-guides/TL-WR840N_V6.2/chapter-4-configure-the-router-in-standard-wireless-router-mode).

### Pilihan implementasi

1. **Baseline yang direkomendasikan:** tambahkan alamat LAN router sebagai perangkat `router`. Job ICMP memantau online/offline, latency, dan packet loss. Tambahkan probe TCP atau HTTP ke web UI untuk membedakan router yang hidup dari layanan administrasi yang bermasalah.
2. **Pemeriksaan kualitas koneksi:** jalankan probe berantai dari server monitoring: router LAN, IP internet, DNS, lalu HTTPS. Hasilnya membantu membedakan gangguan LAN/router, WAN/ISP, DNS, dan layanan tujuan. Blackbox Exporter mendukung probe ICMP, TCP, HTTP/HTTPS, DNS, gRPC, dan WebSocket. Lihat [dokumentasi Blackbox Exporter](https://github.com/prometheus/blackbox_exporter).
3. **TP-Link UPnP IGD (opsional):** TL-WR840N mendukung UPnP. Bila implementasi firmware mengekspos layanan `WANCommonInterfaceConfig`, exporter khusus dapat membaca total byte/paket WAN lalu menghitung laju trafik. Fitur ini harus diuji pada perangkat aktual; jangan membuka UPnP/SSDP ke internet. Standar IGD mendefinisikan counter `GetTotalBytesSent` dan `GetTotalBytesReceived` [di sini](https://upnp.org/specs/gw/UPnP-gw-WANCommonInterfaceConfig-v1-Service.pdf).
4. **Ruijie Cloud API (opsional):** gunakan API Cloud sebagai sumber status perangkat, klien, trafik, dan event bila akun/region perangkat memperoleh akses API. Poller atau exporter khusus kemudian menerbitkan metrik ke Prometheus. Dokumentasi API tersedia melalui [Ruijie Cloud Help Centre](https://cloud.ruijienetworks.com/help/#/ArticleList?id=7e875942927f4e3fb3e5736c8502c03c). Metode ini bergantung pada koneksi internet, cloud, token, dan kompatibilitas endpoint model/perangkat.
5. **Scraping EWEB/web UI (eksperimental):** request HTTP internal dapat diubah menjadi exporter, tetapi endpoint, token sesi, dan format respons dapat berubah saat firmware diperbarui. Gunakan hanya sebagai adapter tambahan, simpan kredensial sebagai secret, dan jangan jadikan sumber alert utama.
6. **Pengamatan di luar router:** bila perlu trafik per-port atau per-klien tanpa API router, gunakan managed switch dengan port mirroring, network TAP, atau bridge inline. Metode ini dapat melihat trafik pada titik tersebut, tetapi tidak dapat menyediakan CPU, suhu, tabel port, atau topologi LLDP dari router consumer.

Tanpa SNMP/API resmi, CPU/RAM/suhu, counter interface per-port, dan discovery LLDP/CDP tidak dapat diperoleh secara andal dari kedua router. Untuk kebutuhan tersebut, gunakan router/switch kelas SMB/enterprise yang mendukung SNMP atau API resmi.

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

Untuk menguji LibreNMS dengan perangkat fisik melalui Ethernet laptop Windows sebelum deployment ke ESXi, ikuti [panduan uji LibreNMS di laptop](docs/uji-librenms-laptop.md). Panduan tersebut mencakup topologi kabel, subnet lab terisolasi, preflight dari container, discovery SNMP/LLDP, dan simulasi gangguan.

## Visibilitas jaringan dan lokasi

- **LibreNMS** menangani discovery SNMP lintas vendor, port/interface, bandwidth, sensor, serta link LLDP/CDP.
- **Pencari Gangguan** menghubungkan gangguan aktif ke hierarki site, gedung, lantai, ruang, rak/patokan, label aset, dan posisi denah.
- **Jalur Koneksi** menampilkan topologi logis dengan nama port dan utilisasi terakhir.
- **CCTV** diperiksa melalui keterjangkauan dan handshake RTSP tanpa mengambil atau menyimpan video.
- **Hub unmanaged** ditandai sebagai monitoring terbatas karena tidak dapat melaporkan kondisi port sendiri.
- Contoh pemasangan LAN kecil tersedia di [denah-jaringan-sederhana.md](docs/denah-jaringan-sederhana.md), termasuk gambar dan alamat IP simulasi.

Alur awal administrator:

1. Buat hierarki dan unggah denah melalui **Pencari Gangguan**.
2. Ikuti wizard **Perangkat** untuk menguji akses dan menjalankan discovery.
3. Tandai port sebagai `wajib`, `cadangan`, atau `diabaikan`.
4. Tambahkan label aset, tempatkan perangkat pada denah, lalu periksa jalur LLDP/CDP bila gangguan memerlukan penelusuran teknis.

Setelah deployment pertama, buat admin serta API token LibreNMS melalui `http://127.0.0.1:8001`. Masukkan token ke `LIBRENMS_API_TOKEN`, lalu restart service `backend` dan `network-worker`. Port LibreNMS hanya terikat ke loopback host.
## Detail perangkat uji

### Perangkat pertama
laptop windows 11 yang menjalankan docker dibawah linux virtual machine


### Perangkat kedua
Merek: Ruijie | Reyee

Jenis Perangkat: Dual Band Wireless Router

Model: RG-EW1200

Input: 12.0V ⎓ 1.0A

Version: V2.40

SSID: @Ruijie-s02FD

Default Management Address: 192.168.110.1

Password: admin

S/N: G1VQ4HT019285

MAC: 4C4968C902FD

Teks Lain & Logo: UK CA, NOM, Scan to Add (dengan QR Code), MCMC CIDF16000114, R-NZ, CE, EAC

Keterangan: Use only power supplies listed in the user instructions

Technical Support(International): https://reyee.ruijie.com/en-global/support

Perusahaan: Ruijie Networks Co., Ltd.

Asal Pembuatan: Made in China/ Сделано в Китае /Fabriqué en Chine/Fabricado en China

### Perangkat ketiga
Merek: Ruijie | Reyee

Jenis Perangkat: Switch

Model: RG-ES05

Version: V1.20

Power: 5V ⎓ 600mA

S/N: G1RP8ZK025067

Teks Lain & Logo: (QR Code), CE, 10, RoHS, QC PASSED

Technical Support(International): https://www.ruijienetworks.com/support

Perusahaan: Ruijie Networks Co., Ltd.

Asal Pembuatan: MADE IN CHINA

## Cara perangkat saat ini terhubung
laptop akan dianggap sebagai VM pada server fisik yang os nya adalah esxi, dimana saat ini laptop windows 11 terhubung ke jaringan internet lalu memiliki menghubungkan usb ke rj45 menggunakna conventer lalu mencolokannya ke RG-ES05 di port 1 nya, kemudian pada port 2 RG-ES05 dicolok ke port 1 RG-EW1200. saya mau RG-EW1200 itu hanya bertugas memancarkan jaringan wirelessnya yang ada internet yang dibawa dari laptop

## Uji perangkat fisik saat ini

Topologi yang telah diuji menggunakan subnet `192.168.110.0/24`:

```text
Laptop Windows 11 / Monitora
Ethernet 192.168.110.10
        |
        | RG-ES05 port 1
     RG-ES05 (unmanaged, tanpa IP)
        | RG-ES05 port 2
        |
     RG-EW1200
LAN 192.168.110.1
        |
        | Wi-Fi
        |
Laptop Ubuntu 192.168.110.114
```

Alamat Ubuntu di atas berasal dari DHCP dan dapat berubah. Gunakan DHCP reservation pada RG-EW1200 atau alamat statis agar target monitoring tetap konsisten.

### Hasil preflight yang telah dicapai

Jalankan dari PowerShell pada laptop Windows, di root repository:

```powershell
.\scripts\test-librenms-lab.ps1 -Target 192.168.110.114 -LabNetwork 192.168.110.0
```

Pengujian dinyatakan lulus apabila menghasilkan:

- satu rute lab melalui adapter Ethernet;
- Docker Compose dan container LibreNMS berjalan;
- target dapat diping dari Windows;
- target dapat diping dari container LibreNMS; dan
- validator LibreNMS selesai tanpa exit error.

Hasil tersebut membuktikan bahwa Monitora di dalam Docker dapat mencapai perangkat fisik melalui Windows, converter USB-RJ45, RG-ES05, dan Wi-Fi RG-EW1200. Ping yang berhasil belum membuktikan dukungan SNMP.

Untuk memastikan ping tidak salah melewati Wi-Fi internet, tentukan alamat sumber Ethernet secara eksplisit:

```powershell
ping -S 192.168.110.10 192.168.110.1
ping -S 192.168.110.10 192.168.110.114
```

### Mendaftarkan perangkat ke Monitora

Daftarkan perangkat aktual melalui `http://localhost:8080/perangkat` menggunakan nilai berikut.

| Perangkat | Jenis | Peran | Alamat dan target | Job | Kredensial |
| --- | --- | --- | --- | --- | --- |
| RG-EW1200 | Router | Akses/cabang | `192.168.110.1` | `icmp` | Pilih **ICMP saja (tanpa SNMP)** |
| RG-ES05 | Hub | Distribusi pusat | `Tidak ada IP (unmanaged)` / `not-monitored` | `none` | Tidak ada |
| Laptop Ubuntu | Komputer/client | Perangkat akhir | `192.168.110.114` | `icmp` | Tidak ada |

RG-ES05 dicatat sebagai `Hub` karena kategori tersebut dipakai Monitora untuk perangkat penghubung unmanaged yang tidak mempunyai IP. Catat model sebenarnya, posisi, serta nomor port pada kolom nama dan catatan.

Untuk RG-EW1200, pilihan ICMP menyembunyikan seluruh kolom SNMP dan mengaktifkan monitoring tanpa menjalankan LibreNMS atau discovery port.

Gunakan **Gateway ISP** hanya untuk perangkat yang benar-benar menjadi pintu keluar utama menuju internet. Apabila RG-EW1200 kelak tetap bekerja sebagai router dan default gateway seluruh jaringan lab, perannya dapat diubah menjadi **Gateway ISP**. Jika hanya memancarkan Wi-Fi dalam mode AP/bridge, gunakan **Akses/cabang**.

Tombol **Uji koneksi** untuk jenis Komputer/client saat ini memeriksa TCP port 80. Pesan berikut tidak berarti jaringan gagal:

```text
Koneksi gagal: [Errno 111] Connection refused
```

Pesan tersebut berarti perangkat dapat dijangkau, tetapi tidak menjalankan web server pada port 80. Untuk perangkat yang hanya dipantau melalui ping, lanjutkan penyimpanan dengan job `icmp` dan nilai hasilnya dari dashboard setelah sekitar satu menit.

### Arti status perangkat

| Status | Arti operasional |
| --- | --- |
| Hijau | Target merespons pemeriksaan terakhir. |
| Oranye | Monitoring hanya parsial, datanya terlambat, atau ada kondisi yang memerlukan perhatian. |
| Merah | Target gagal dijangkau atau pemeriksaan layanan gagal. |
| Abu-abu/netral | Status tidak dapat diperiksa langsung; normal untuk RG-ES05 yang tidak mempunyai IP. |

Status hanya menunjukkan hasil pemeriksaan, bukan diagnosis kerusakan perangkat. Perangkat offline dapat disebabkan daya mati, kabel terlepas, IP berubah, firewall, Wi-Fi, atau perangkat sedang restart.

### ICMP dan SNMP

- **ICMP** menggunakan ping untuk mengetahui apakah alamat perangkat dapat dijangkau. ICMP tidak membutuhkan community string atau akun perangkat.
- **SNMP** mengambil informasi internal seperti status port, bandwidth, error/discard, uptime, sensor, dan identitas interface. SNMP harus tersedia pada firmware perangkat dan memerlukan kredensial read-only.
- RG-EW1200 tidak menyediakan SNMP, sehingga dipantau melalui ICMP. Ruijie menyatakan seri EW tidak mendukung SNMP: [Does Ruijie RG-EW Series Support SNMP?](https://community.ruijienetworks.com/forum.php?mod=viewthread&tid=8958).
- RG-ES05 adalah switch unmanaged, plug-and-play, dan zero-configuration tanpa IP manajemen: [spesifikasi resmi RG-ES05](https://reyee.ruijie.com/en-global/products/reyee-switch/unmanaged-switch/rg-es05/).

## Uji gangguan nyata

Tunggu sekitar 1-3 menit setelah setiap tindakan agar polling dan tampilan aplikasi diperbarui.

| Skenario | Tindakan | Hasil yang diharapkan | Batas diagnosis tanpa SNMP |
| --- | --- | --- | --- |
| Kondisi normal | Semua perangkat dan kabel terpasang | RG-EW1200 dan Ubuntu hijau; RG-ES05 netral | RG-ES05 hanya tercatat sebagai inventaris. |
| Ubuntu mati | Matikan Ubuntu | Hanya Ubuntu menjadi merah | Penyebab pastinya dapat berupa daya, Wi-Fi, IP, atau firewall. |
| Wi-Fi Ubuntu putus | Putuskan Ubuntu dari SSID | Router tetap hijau dan Ubuntu merah | Monitora mengetahui target hilang, bukan kualitas radio penyebabnya. |
| Kabel router putus | Cabut kabel RG-ES05 ke RG-EW1200 | Router dan Ubuntu terdampak | Monitora tidak dapat menyebut nomor port yang down. |
| Kabel berpindah port | Pindahkan kabel router dari port 2 ke port lain | Target kembali hijau | Perpindahan port tidak terdeteksi dan topologi manual harus diperbarui. |
| RG-ES05 mati | Cabut adaptor RG-ES05 | Router dan Ubuntu offline; link Ethernet Windows turun | Monitora melihat dampak bersama, bukan status internal switch. |
| Internet atau DNS gagal | Putuskan jalur internet, tetapi pertahankan LAN | Perangkat lokal tetap hijau dan target website eksternal merah | Gangguan mengarah ke gateway, ISP, atau DNS. |
| Layanan aplikasi mati | Hentikan layanan web pada perangkat yang masih hidup | Ping tetap berhasil, tetapi probe HTTP/TCP gagal | Perangkat hidup tidak menjamin aplikasinya sehat. |

Jika beberapa perangkat di belakang jalur yang sama menjadi merah pada waktu hampir bersamaan, periksa titik bersama terdekat: daya, switch, uplink, router, dan kabel. Ini merupakan korelasi gejala, bukan pembacaan port secara langsung.

## Rencana peningkatan ke managed switch

Label **managed** atau **cloud-managed** tidak otomatis menjamin dukungan SNMP. Sebelum membeli, spesifikasi atau konfirmasi vendor harus menyebutkan:

- SNMPv2c atau, lebih baik, SNMPv3;
- LLDP;
- status dan counter trafik/error per interface;
- IP manajemen dan akses MIB;
- port mirroring bila diperlukan untuk analisis paket.

Managed switch yang memenuhi syarat memungkinkan Monitora menampilkan port yang down, kecepatan link, trafik, error/discard, dan tetangga LLDP. Periksa dukungan per model; beberapa switch yang dapat dikelola melalui web/cloud tetap tidak menyediakan SNMP.

RG-EW1200 belum harus diganti. Dengan managed switch, Monitora dapat memantau port dan total trafik yang menuju router walaupun statistik internal router tetap tidak tersedia. Ganti router hanya jika instansi membutuhkan SNMPv3, kondisi WAN, CPU/RAM, statistik radio, daftar klien, VLAN/multi-SSID, atau trafik internal per interface.

Urutan peningkatan yang disarankan:

1. stabilkan IP target menggunakan alamat statis atau DHCP reservation;
2. lengkapi label perangkat, kabel, port, lokasi, dan topologi manual;
3. gunakan ICMP serta probe layanan untuk perangkat yang tidak mendukung SNMP;
4. pasang managed switch ber-SNMP pada titik distribusi yang paling kritis; dan
5. evaluasi penggantian router hanya jika data dari managed switch belum mencukupi.
