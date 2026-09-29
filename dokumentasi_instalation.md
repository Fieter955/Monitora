# Dokumentasi Instalasi & Troubleshooting Monitora

## Catatan Penting & Panduan Debugging

### 1. Sisi Server (Linux/Ubuntu & Docker)

**Potensi Masalah Umum:**
- Server gagal menghubungi perangkat target (Timeout / No Route to Host).
- Data masuk ke Prometheus tapi tidak muncul di Dashboard / Backend.

**Langkah Debugging (Server-side):**
- **Cek Konektivitas Dasar:** Pastikan server Linux bisa menghubungi target. Gunakan perintah `curl -m 5 http://<IP_TARGET>:9182/metrics` di terminal Ubuntu. Jika respon lambat atau gagal, masalah kemungkinan besar ada di jaringan, firewall target, atau agen yang tidak berjalan.
- **Cek Akses Jaringan Kontainer:** Secara default, konfigurasi Docker Compose tertentu mengisolasi jaringan. Pastikan service `prometheus` memiliki akses `egress` atau berada di network yang diizinkan untuk merutekan trafik keluar ke jaringan LAN. Anda bisa mencoba mengeksekusi `curl` langsung dari dalam kontainer: `docker compose exec prometheus curl ...`
- **Cek Target Prometheus:** Akses antarmuka web Prometheus di `http://<IP_SERVER>:9090/targets`. Periksa status target perangkat Windows. Jika statusnya `DOWN`, lihat pesan error yang muncul di baris tersebut untuk petunjuk lebih lanjut.
- **Cek Log Service Utama:** Pantau log kontainer backend dan prometheus jika mendapati keanehan saat mendaftarkan perangkat atau metrik tidak tersimpan: `docker compose logs -f backend prometheus`.
- **Cek Kompatibilitas Query (PromQL):** Jika dashboard Grafana terlihat kosong padahal target `UP`, pastikan query tidak kedaluwarsa. Versi exporter baru sering kali mengubah format atau nama metrik (misalnya `windows_cs_physical_memory_bytes` yang kini berubah menjadi `windows_memory_physical_total_bytes`).

### 2. Sisi Target (Windows Server)

**Potensi Masalah Umum:**
- Service `windows_exporter` gagal berjalan (berstatus *Stopped* sesaat setelah dicoba untuk di-*Start*).
- Firewall Windows secara otomatis memblokir akses koneksi masuk (inbound) dari server Linux ke port exporter.

**Langkah Debugging (Target-side):**
- **Verifikasi Status Service:** Buka PowerShell sebagai Administrator dan jalankan `Get-Service windows_exporter`. Jika statusnya terus-menerus *Stopped*, ini menandakan service mengalami *crash* saat inisialisasi.
- **Cek Konfigurasi Eksekusi (Registry):** Jika service sering crash, kemungkinan besar ada parameter kolektor yang sudah tidak didukung oleh versi exporter terbaru (seperti kolektor `cs`). Buka *Registry Editor* (`regedit`), navigasi ke `HKLM\SYSTEM\CurrentControlSet\Services\windows_exporter`, dan periksa data parameter di `ImagePath`. Hapus argumen kolektor yang bermasalah, lalu restart service.
- **Uji Endpoint Secara Lokal:** Buka browser atau gunakan PowerShell `Invoke-WebRequest` di Windows target dan akses `http://localhost:9182/metrics`. Jika halaman tersebut menampilkan teks yang panjang berisi data-data metrik, berarti agen sudah terpasang dan berjalan dengan benar.
- **Konfigurasi Firewall:** Pastikan port untuk exporter (default `9182` TCP) diizinkan pada Inbound Rules di Windows Defender Firewall. Jika server Linux dapat melakukan `ping` ke Windows namun tidak bisa melakukan `curl` ke port 9182, ini adalah indikasi kuat adanya pemblokiran di tingkat firewall lokal Windows.
