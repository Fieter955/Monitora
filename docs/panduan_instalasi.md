# Panduan Instalasi & Penambahan Perangkat Monitora

Berikut panduan instalasi dan penambahan target ke aplikasi **Monitora** secara langsung, jelas, dan tanpa bertele-tele.

---

### Skenario Alamat IP (Contoh)
* **Server Monitoring Utama (Linux):** `192.168.1.10`
* **Target Linux Client:** `192.168.1.20`
* **Target Windows Client:** `192.168.1.30`

*(Silakan sesuaikan IP di bawah dengan IP jaringan Anda yang sebenarnya)*.

---

## BAGIAN 1: Instalasi Server Utama (Linux Monitoring)

Server ini adalah pusat aplikasi yang menjalankan Monitora, Prometheus, dan Grafana via Docker.

### Langkah-langkah:
1. **Buka Terminal** di server Linux utama Anda.
2. **Pastikan Docker & Git sudah terpasang:**
   ```bash
   sudo apt update
   sudo apt install -y docker.io docker-compose-v2 git
   ```
3. **Masuk ke folder project Monitora** (atau clone jika belum):
   ```bash
   cd /opt/Monitora
   ```
4. **Siapkan konfigurasi `.env`:**
   ```bash
   cp .env.example .env
   ```
   *(Buka file `.env` dengan `nano .env` jika ingin mengganti password admin atau domain).*
5. **Jalankan aplikasi:**
   ```bash
   docker compose up -d --build
   ```
6. **Pastikan semua container berjalan:**
   ```bash
   docker compose ps
   ```
   *Aplikasi utama kini aktif dan dapat diakses melalui browser di `http://192.168.1.10:8080`.*

---

## BAGIAN 2: Pasang Agen di Linux Client (Target Linux)

Mesin Linux yang ingin dipantau hanya butuh agen kecil bernama **Node Exporter** (port default `9100`).

### Langkah-langkah:
1. **Login ke Terminal mesin Linux Client** (`192.168.1.20`).
2. **Download dan pasang Node Exporter:**
   ```bash
   # 1. Download binary resmi
   wget https://github.com/prometheus/node_exporter/releases/download/v1.9.0/node_exporter-1.9.0.linux-amd64.tar.gz

   # 2. Ekstrak
   tar -xvf node_exporter-1.9.0.linux-amd64.tar.gz

   # 3. Pindahkan binary ke system path
   sudo mv node_exporter-1.9.0.linux-amd64/node_exporter /usr/local/bin/

   # 4. Buat user sistem khusus
   sudo useradd -rs /bin/false node_exporter
   ```

3. **Buat Systemd Service agar jalan otomatis di background:**
   ```bash
   sudo tee /etc/systemd/system/node_exporter.service <<EOF
   [Unit]
   Description=Node Exporter
   After=network.target

   [Service]
   User=node_exporter
   Group=node_exporter
   Type=simple
   ExecStart=/usr/local/bin/node_exporter

   [Install]
   WantedBy=multi-user.target
   EOF
   ```

4. **Aktifkan dan jalankan service:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now node_exporter
   ```

5. **Buka Firewall port 9100 (Khusus IP Server Utama):**
   ```bash
   # Izinkan hanya IP server monitoring
   sudo ufw allow proto tcp from 192.168.1.10 to any port 9100
   ```

6. **Tes Verifikasi:**
   Jalankan perintah ini:
   ```bash
   curl http://localhost:9100/metrics
   ```
   *Jika keluar teks metrik panjang, agen Linux sudah aktif.*

---

## BAGIAN 3: Pasang Agen di Windows Client (Target Windows)

Mesin Windows yang ingin dipantau menggunakan agen **Windows Exporter** (port default `9182`).

### Langkah-langkah:
1. **Login ke Windows Client** (`192.168.1.30`).
2. Buka menu Start, cari **PowerShell**, klik kanan lalu pilih **"Run as Administrator"**.
3. Jalankan script instalasi otomatis di bawah ini (masukkan IP server monitoring pada parameter `-MonitoringServer`):

   ```powershell
   # Jalankan perintah ini di PowerShell Administrator:
   $MonitoringServer = "192.168.1.10"
   $Version = "0.31.8"
   $Url = "https://github.com/prometheus-community/windows_exporter/releases/download/v$Version/windows_exporter-$Version-amd64.msi"
   $OutFile = "$env:TEMP\windows_exporter.msi"

   Write-Host "Mengunduh windows_exporter..."
   Invoke-WebRequest -Uri $Url -OutFile $OutFile

   Write-Host "Memasang service windows_exporter..."
   Start-Process msiexec.exe -ArgumentList "/i", $OutFile, "/qn", "/norestart", "ENABLED_COLLECTORS=cpu,logical_disk,memory,net,os,service,system", "LISTEN_PORT=9182" -Wait

   Write-Host "Membuka port firewall 9182 untuk Server Monitoring..."
   Get-NetFirewallRule -DisplayName "Monitora windows_exporter" -ErrorAction SilentlyContinue | Remove-NetFirewallRule
   New-NetFirewallRule -DisplayName "Monitora windows_exporter" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 9182 -RemoteAddress $MonitoringServer | Out-Null

   Write-Host "SELESAI! Agen Windows aktif pada port 9182."
   ```

4. **Tes Verifikasi:**
   Buka browser di Windows tersebut atau ketik di PowerShell:
   ```powershell
   Invoke-WebRequest -Uri http://localhost:9182/metrics
   ```
   *Jika statusnya `200 OK`, agen Windows sudah aktif.*

---

## BAGIAN 4: Menambahkan Perangkat ke Aplikasi Monitora (UI Walkthrough)

Setelah agen di target terpasang, sekarang daftarkan perangkat ke web Monitora:

### Step 1: Buka & Login ke Aplikasi
1. Buka browser Anda (Chrome/Firefox/Edge).
2. Ketik alamat: `http://192.168.1.10:8080`
3. Masuk dengan akun Anda (Default: `admin` / `admin12345`).

### Step 2: Menuju Menu Perangkat
1. Lihat menu di bilah navigasi sebelah kiri (sidebar).
2. Klik menu **Perangkat** (ikon perangkat/server).
3. Anda akan melihat halaman tabel *Daftar perangkat*.
4. Di pojok kanan atas, klik tombol biru **`+ Tambah perangkat`**.
5. Jendela formulir (drawer) akan muncul di sisi kanan layar.

---

### Step 3A: Menambahkan Target LINUX
1. **Langkah 1: Identitas**
   * **Nama perangkat:** Ketik nama server (Contoh: `Server Database Linux`).
   * **Jenis:** Klik dropdown, pilih **`Server Linux`**.
   * **Peran jaringan:** Pilih **`Perangkat akhir`**.
   * **IP atau hostname:** Masukkan IP client (Contoh: `192.168.1.20`).
   * Klik tombol biru di kanan bawah: **`Lanjut ke akses`**.

2. **Langkah 2: Akses**
   * **Target monitoring:** Pastikan tertulis format `IP:PORT`, yaitu `192.168.1.20:9100`. *(Penting: jangan lupa `:9100`)*.
   * **Job:** Otomatis bernilai `node`.
   * Klik tombol **`Uji koneksi`** untuk mengecek apakah server bisa menjangkau target.
   * Pastikan kotak **Aktifkan monitoring** tercentang.
   * Klik tombol biru: **`Simpan & temukan port`** (atau Simpan).

---

### Step 3B: Menambahkan Target WINDOWS
1. **Langkah 1: Identitas**
   * **Nama perangkat:** Ketik nama server (Contoh: `Server Aplikasi Windows`).
   * **Jenis:** Klik dropdown, pilih **`Server Windows`**.
   * **Peran jaringan:** Pilih **`Perangkat akhir`**.
   * **IP atau hostname:** Masukkan IP client (Contoh: `192.168.1.30`).
   * Klik tombol biru di kanan bawah: **`Lanjut ke akses`**.

2. **Langkah 2: Akses**
   * **Target monitoring:** Ganti/isi dengan format `IP:PORT`, yaitu `192.168.1.30:9182`. *(Penting: port Windows adalah `:9182`)*.
   * **Job:** Otomatis bernilai `windows`.
   * Klik tombol **`Uji koneksi`**.
   * Pastikan kotak **Aktifkan monitoring** tercentang.
   * Klik tombol biru: **`Simpan & temukan port`** (atau Simpan).

---

## BAGIAN 5: Melihat Grafik & Hasil Monitoring
1. Kembali ke tabel **Perangkat**, perangkat yang baru ditambahkan akan muncul dalam daftar dengan badge hijau **Aktif**.
2. **Prometheus** membutuhkan waktu sekitar **30 detik** untuk mulai menarik data metrik pertama kali.
3. Untuk melihat grafik CPU, RAM, Disk, dan Trafik:
   * Lihat sidebar kiri bagian paling bawah, klik tombol **`Buka Grafana`**.
   * Tab baru akan terbuka menampilkan dashboard metrik.
   * Pilih menu dashboard **Server Linux** untuk target Linux, atau **Server Windows** untuk target Windows.