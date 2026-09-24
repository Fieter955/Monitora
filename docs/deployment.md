# Deployment Linux dan cPanel

## Rekomendasi penempatan

Dengan LibreNMS, MariaDB, Redis, dan RRDCached, gunakan 4 vCPU, RAM 8–12 GB, serta SSD minimal 60 GB sebagai titik awal untuk kurang dari 100 perangkat. Ukur kembali berdasarkan jumlah interface dan retensi histori.

Gunakan satu VPS/VM Linux terpisah dengan akses SSH administrator. Kapasitas akhir tetap harus dievaluasi dari jumlah interface, frekuensi polling, dan retensi data setelah masa uji coba.

Satu instalasi pusat dapat memantau banyak VM. Untuk sembilan VM Windows pada satu ESXi, pasang
Monitora hanya pada satu VM monitoring, lalu pasang `windows_exporter` pada setiap guest. Monitoring
MikroTik/ISP juga cukup dijalankan oleh VM pusat.

Shared hosting dengan akun cPanel saja bukan tempat yang cocok untuk stack ini. cPanel Application Manager dapat menjalankan Node.js/Python bila provider mengaktifkannya, tetapi portal juga membutuhkan Prometheus, Grafana, exporter, volume persisten, serta jaringan internal. Dokumentasi resmi cPanel menjelaskan deployment Node/Python melalui Passenger dan container EA4 berbasis Podman, yang tetap membutuhkan dukungan administrator:

- [cPanel Application Manager](https://docs.cpanel.net/cpanel/software/application-manager/)
- [cPanel EasyApache containers](https://docs.cpanel.net/ea4/containers/easyapache-4-containers/)

Jika website instansi tetap berada di cPanel:

1. Buat VPS/VM monitoring terpisah.
2. Tambahkan subdomain, misalnya `monitor.example.go.id`, melalui Zone Editor cPanel.
3. Arahkan record A subdomain ke IP VPS monitoring.
4. Jangan memindahkan website utama dan jangan membuka port Prometheus/exporter ke internet.

## Persiapan server

1. Pasang Linux LTS yang didukung organisasi dan Docker Engine dari repository resminya: [Docker Engine installation](https://docs.docker.com/engine/install/).
2. Buat user deployment non-root dan batasi akses SSH menggunakan key.
3. Clone repository ke direktori tetap, misalnya `/opt/pantau-infrastruktur`.
4. Salin `.env.example` menjadi `.env`, lalu isi secret dan domain produksi.
5. Set sekurang-kurangnya:

   ```dotenv
   APP_ENV=production
   COOKIE_SECURE=true
   ALLOWED_HOSTS=monitor.example.go.id,backend,gateway
   PUBLIC_BASE_URL=https://monitor.example.go.id
   BIND_ADDRESS=127.0.0.1
   HTTP_PORT=8080
   NODE_EXPORTER_ROOTFS_MODE=ro,rslave
   ```

6. Jalankan `docker compose up -d --build`.

Gunakan secret berbeda untuk `APP_SECRET_KEY` dan `CREDENTIAL_ENCRYPTION_KEY`. Ganti juga `LIBRENMS_DB_PASSWORD`, `LIBRENMS_DB_ROOT_PASSWORD`, serta `LIBRENMS_REDIS_PASSWORD` sebelum menjalankan production.

## Aktivasi LibreNMS

1. Buka `http://127.0.0.1:8001` dari host monitoring. Untuk server remote gunakan SSH tunnel; jangan membuka port ini ke internet.
2. Selesaikan pembuatan admin LibreNMS lalu buat API token khusus integrasi pada menu API Access.
3. Isi `LIBRENMS_API_TOKEN` di `.env`, kemudian jalankan `docker compose up -d backend network-worker`.
4. Aktifkan SNMP read-only dan LLDP/CDP pada perangkat serta batasi UDP 161 hanya dari IP server monitoring.
5. Jalankan discovery dari wizard Perangkat, konfirmasi fungsi port, lalu uji dengan mencabut satu koneksi wajib.

Fast ping digunakan untuk target status sekitar satu menit. Polling seluruh interface satu menit hanya boleh diaktifkan setelah halaman poller LibreNMS membuktikan semua pekerjaan selesai di bawah 60 detik. Jika tidak, gunakan polling port lima menit dan pertahankan fast ping satu menit.

## Monitoring Windows, MikroTik, dan ISP

- Daftarkan guest Windows sebagai `Server Windows` dengan target `IP:9182`.
- Batasi firewall TCP 9182 agar hanya menerima koneksi dari server monitoring.
- Aktifkan SNMP read-only pada MikroTik dan batasi UDP 161 dari server monitoring saja.
- Tandai MikroTik sebagai `Gateway ISP`, jalankan discovery, lalu pilih interface yang menerima ISP.
- Diagnosis internet menggabungkan status gateway, link WAN, dua target IP publik, DNS, dan HTTPS.
  Traffic WAN nol tidak dianggap sebagai bukti tunggal gangguan.
- Alert gangguan ISP menghambat alert website eksternal turunannya, tetapi monitoring LAN dan VM
  internal tetap berjalan.

## Integrasi ESXi opsional

Profil `vmware` memakai Telegraf dan membutuhkan vSphere 7 atau lebih baru. Buat akun khusus pada
ESXi/vCenter dengan role `Read-only`; jangan gunakan akun root. Isi `VSPHERE_URL`,
`VSPHERE_USERNAME`, dan `VSPHERE_PASSWORD`, kemudian aktifkan target dan profil:

Set `ENABLE_VMWARE=true`, lalu jalankan preflight dan aktivasi berikut:

```powershell
.\scripts\enable-vmware.ps1
```

Skrip baru mengaktifkan target Prometheus setelah koneksi dan pengambilan metrik uji berhasil.

Jika versi ESXi belum diketahui atau preflight Telegraf gagal, biarkan profil ini nonaktif. Data
CPU/RAM/disk dari sembilan guest Windows tetap tersedia melalui `windows_exporter`.

`BIND_ADDRESS=127.0.0.1` membuat gateway Compose hanya dapat dijangkau reverse proxy pada host. Next.js juga merekomendasikan reverse proxy di depan server ketika self-hosting: [Next.js self-hosting](https://nextjs.org/docs/app/guides/self-hosting).

## HTTPS dan firewall

Pilihan yang paling mudah dirawat adalah Nginx/Apache host atau reverse proxy organisasi menangani sertifikat TLS, lalu meneruskan trafik ke `127.0.0.1:8080`. Contoh konfigurasi TLS container juga tersedia di `infra/nginx/https.example.conf` jika sertifikat memang dikelola di dalam stack.

Aturan firewall minimum:

- TCP 22 hanya dari IP admin atau VPN.
- TCP 80/443 untuk pengguna yang diizinkan.
- TCP 9100 pada server target hanya dari IP server monitoring.
- UDP 161 pada perangkat SNMP hanya dari IP server monitoring.
- TCP 8001 hanya pada loopback host untuk administrasi LibreNMS.
- Jangan membuka 3000, 5432, 9090, 9093, 9115, atau 9116 ke internet.

## Node Exporter pada server lain

Node Exporter ditempatkan di setiap mesin Linux yang dipantau, idealnya sebagai service systemd dengan user khusus. Unduh binary dari release resmi, verifikasi checksum, lalu batasi port 9100 melalui firewall. Referensi instalasi dan metrik: [Prometheus Node Exporter guide](https://prometheus.io/docs/guides/node-exporter/).

Setelah exporter aktif, tambahkan perangkat melalui portal dengan target `IP_SERVER:9100`. Hindari memberi container monitoring akses SSH ke server target; Prometheus cukup melakukan scrape HTTP ke exporter.

## SNMP router, switch, dan access point

Konfigurasi bawaan MVP memakai `public_v2` read-only agar dapat diuji pada LAN tertutup. SNMP v1/v2c tidak mengenkripsi community string. Untuk produksi:

1. Aktifkan SNMPv3 read-only pada perangkat jika tersedia.
2. Gunakan generator resmi SNMP Exporter untuk menghasilkan `snmp.yml` dengan module perangkat.
3. Simpan username/password/privacy key sebagai secret, bukan di Git.
4. Mount konfigurasi hasil generator ke container dan ubah parameter `auth` pada `infra/prometheus/prometheus.yml`.

Dokumentasi exporter merekomendasikan SNMPv3 untuk akses aman: [Prometheus SNMP Exporter](https://github.com/prometheus/snmp_exporter).

## Alert Telegram

Alert tetap terlihat di portal tanpa konfigurasi eksternal. Untuk mengaktifkan Telegram:

1. Salin `infra/alertmanager/telegram.example.yml` menjadi `infra/alertmanager/telegram.yml`.
2. Ganti `chat_id` pada file tersebut.
3. Tulis bot token saja ke `secrets/telegram_bot_token`; jangan tambahkan file ini ke Git.
4. Salin `compose.telegram.example.yaml` menjadi `compose.telegram.yaml`.
5. Jalankan:

   ```bash
   docker compose -f compose.yaml -f compose.telegram.yaml up -d alertmanager
   ```

6. Uji receiver dengan alert non-produksi sebelum mengandalkannya untuk insiden nyata. Alertmanager mendukung Telegram, email, Slack, Webex, dan webhook: [notification integrations](https://prometheus.io/docs/alerting/latest/integrations/).

## Backup dan pemulihan

Jalankan `scripts/backup.sh` melalui cron setelah membuat file executable. Script menyimpan dump PostgreSQL, data Prometheus, data Grafana, serta salinan environment ke folder `backups/`. Folder tersebut harus dipindahkan ke penyimpanan terenkripsi di luar server dan memiliki kebijakan retensi.

Prometheus menyarankan snapshot untuk backup konsisten; local storage tidak direplikasi otomatis: [Prometheus storage](https://prometheus.io/docs/prometheus/latest/storage/). Lakukan uji restore pada server staging secara berkala. Jangan menunggu insiden pertama untuk mengetahui bahwa backup tidak dapat dipulihkan.

## Checklist sebelum go-live

- Secret development dan password default sudah diganti.
- HTTPS aktif dan `COOKIE_SECURE=true`.
- Portal hanya dapat diakses dari LAN/VPN atau daftar IP yang disetujui.
- Semua port internal tertutup dari internet.
- Target server, website, dan SNMP sudah menampilkan data.
- Alert offline, CPU, memori, disk, website, dan SSL sudah diuji.
- Backup berhasil dipulihkan pada lingkungan uji.
- Admin organisasi menerima dokumentasi akun, domain, update, backup, dan prosedur rollback.
