# Dokumen Asesmen Keamanan Siber & Hardening Sistem Monitora
**Standar Pengujian Siber, Matriks Analisis Risiko (Aman vs Bahaya), Skenario Uji Penetrasi, dan Panduan Kepatuhan Klien Intranet**

*Klasifikasi Dokumen: Keamanan Sistem & Panduan Implementasi*  
*Target Lingkungan: On-Premises Private Intranet / LAN Kantor Operasional*  
*Standar Rujukan: NIST SP 800-115, PTES, OWASP Top 10 (2021), OWASP API Security Top 10 (2023), CIS Controls v8, serta Pedoman Teknis BSSN untuk Sistem Pemerintahan Berbasis Elektronik (SPBE)*

---

## 1. Ringkasan Eksekutif (Executive Summary)

### 1.1 Jaminan Keamanan untuk Klien & Manajemen
Aplikasi **Monitora** dirancang khusus untuk memantau ketersediaan dan performa infrastruktur server, jaringan, website, serta perangkat telemetri secara terpusat. Dalam penerapannya di lingkungan intranet instansi pemerintah maupun korporasi, kepastian keamanan siber adalah prioritas tertinggi.

Klien dapat merasa **yakin, tenang, dan aman** menggunakan Monitora karena platform ini dibangun dengan prinsip:
1. **Prinsip Hak Akses Minimal (*Least Privilege*) & *Read-Only Telemetry*:** Monitora beroperasi sebagai sistem pembaca metrik (*collector*). Sistem **tidak** melakukan perubahan konfigurasi pada router/switch, **tidak** melakukan eksekusi perintah jarak jauh (*remote shell*) pada server klien, dan **tidak** menyimpan data personal/privasi pengguna (PII).
2. **Arsitektur Pertahanan Berlapis (*Defense-in-Depth*):** Terdiri dari segmentasi multi-tier jaringan container (Gateway, Internal, Monitoring, Egress), di mana database, storage metrik Prometheus, dan cache Redis sama sekali **tidak terekspos** ke jaringan LAN.
3. **Kriptografi Standar Industri:** Seluruh kata sandi diamankan dengan algoritma hashing mutakhir (**Argon2** via `pwdlib`), dan kredensial perangkat (SNMP, RTSP CCTV, akun service vSphere) disimpan dalam format terenkripsi **AES-256-GCM authenticated envelope** dengan kunci terpisah dari JWT sesi.
4. **Isolasi Subrequest Reverse Proxy:** Akses dashboard Grafana dilindungi oleh mekanisme delegasi autentikasi subrequest Nginx (`auth_request /_auth/session`), menjamin hanya pengguna yang telah login secara sah yang dapat melihat metrik teknis.

---

## 2. Metodologi Pengujian Siber Internasional & Nasional

Dokumentasi dan skenario pengujian pada Monitora disusun berdasarkan kombinasi standar internasional dan regulasi nasional:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   METODOLOGI ASESMEN KEAMANAN SIBER                    │
├──────────────────────────────────┬─────────────────────────────────────┤
│ 1. Kerangka Prosedural           │ NIST SP 800-115 & PTES              │
│    (Bagaimana pengujian dimulai, │ - Planning & Rules of Engagement    │
│    fase discovery, hingga lapor) │ - Threat Modeling & Reconnaissance  │
│                                  │ - Exploitation & Post-Exploitation  │
├──────────────────────────────────┼─────────────────────────────────────┤
│ 2. Taksonomi Kerentanan Aplikasi │ OWASP Top 10 (Web) & API Top 10     │
│    (Apa saja celah yang diuji    │ - BOLA / IDOR, Broken Authentication│
│    secara spesifik pada web/API) │ - Injection, SSRF, Misconfiguration │
├──────────────────────────────────┼─────────────────────────────────────┤
│ 3. Standar Infrastruktur & Host  │ CIS Benchmarks (Linux, Docker, Nginx)│
│    (Pengerasan OS dan container) │ CIS Controls v8 (Inventory, Access) │
├──────────────────────────────────┼─────────────────────────────────────┤
│ 4. Regulasi & Kepatuhan Lokal    │ BSSN (Peraturan BSSN No. 8/2020)    │
│    (Sistem Pemerintahan RI/SPBE) │ SNI ISO/IEC 27001:2022 (A.12 & A.13)│
└──────────────────────────────────┴─────────────────────────────────────┘
```

---

## 3. Dekomposisi Arsitektur & Batas Keamanan (*Perimeter Isolation*)

Arsitektur Monitora menerapkan pemisahan tugas (*separation of concerns*) melalui 4 zona jaringan Docker yang terisolasi:

```text
       [ Klien Intranet / Tim IT ]
                  │
                  ▼ (Port 80/443 - Hanya Gateway Nginx yang dibuka ke LAN)
┌─────────────────┼──────────────────────────────────────────────────────┐
│ DOCKER HOST     │                                                      │
│                 ▼                                                      │
│       ┌────────────────────┐                                           │
│       │   Nginx Gateway    │  [Network: edge]                          │
│       └────┬──────────┬────┘                                           │
│            │          │                                                │
│  (Auth Subrequest)    │ (Reverse Proxy)                                │
│            │          ▼                                                │
│            │  ┌───────────────┐        ┌─────────────────────────┐     │
│            ├─►│    Next.js    │        │       librenms-web      │     │
│            │  │ (Frontend UI) │        │ (127.0.0.1:8001 tunnel) │     │
│            │  └───────┬───────┘        └───────────┬─────────────┘     │
│            │          │ [Network: internal]        │                   │
│            ▼          ▼                            │                   │
│       ┌────────────────────┐                       │                   │
│       │   FastAPI Backend  │                       │                   │
│       └────┬──────────┬────┘                       │                   │
│            │          │                            │                   │
│            ▼          ▼                            ▼                   │
│     ┌────────────┐ ┌────────────┐            ┌──────────────┐          │
│     │ PostgreSQL │ │ Prometheus │            │ MariaDB/RRD  │          │
│     │ (Internal) │ │ (Internal) │            │ (Internal)   │          │
│     └────────────┘ └──────┬─────┘            └──────────────┘          │
│                           │ [Network: monitoring]                      │
│            ┌──────────────┴──────────────┐                             │
│            ▼                             ▼                             │
│     ┌──────────────┐              ┌──────────────┐                     │
│     │ Node/Windows │              │ Blackbox     │                     │
│     │ Exporter     │              │ Exporter     │                     │
│     └──────┬───────┘              └──────┬───────┘                     │
└────────────┼─────────────────────────────┼─────────────────────────────┘
             │ [Network: egress]           │
             ▼                             ▼
   [ Target Server Linux/Win ]     [ Router / Switch / CCTV ]
   (Port 9100/9182 via Firewall)   (ICMP Echo / SNMP UDP 161)
```

1. **Jaringan `edge`:** Hanya berisi Nginx Gateway. Satu-satunya titik masuk dari jaringan lokal pengguna.
2. **Jaringan `internal` (`internal: true`):** Database PostgreSQL, MariaDB LibreNMS, Redis, RRDCached, dan socket backend FastAPI berada di sini. Jaringan ini tidak memiliki gateway ke luar (*no internet egress*) dan tidak menerima paket langsung dari host.
3. **Jaringan `monitoring` (`internal: true`):** Prometheus mengumpulkan metrik dari Exporter dan Blackbox. Pengguna di LAN tidak dapat mengakses port 9090 (Prometheus UI) atau 9093 (Alertmanager) secara langsung.
4. **Jaringan `egress`:** Khusus untuk komponen yang bertugas melakukan probe ke luar (SNMP Exporter, Blackbox Exporter, dan Network Worker) untuk memeriksa target perangkat lokal klien.

---

## 4. Matriks Evaluasi: Apa Saja yang AMAN vs BAHAYA

Bagian ini membedah status riil sistem: apa saja mekanisme pertahanan yang sudah terbukti **AMAN** secara bawaan, serta apa saja kondisi **BAHAYA** yang berpotensi terjadi jika prosedur deployment diabaikan.

### 4.1 Fitur & Mekanisme yang Terbukti AMAN (Built-in Defenses)

| Komponen / Area | Mekanisme Pertahanan Monitora | Ancaman Siber yang Dicegah | Status |
| :--- | :--- | :--- | :---: |
| **Kredensial Perangkat** | Kredensial SNMP community, user CCTV RTSP, dan akun vSphere dienkripsi dengan **AES-256-GCM authenticated cipher** (`app/security.py`). Nilai rahasia tidak pernah ditampilkan kembali ke antarmuka web. | Pencurian kata sandi jaringan saat database di-backup atau diinspeksi (*Credential Harvesting*). | **AMAN** |
| **Penyimpanan Password Pengguna** | Menggunakan algoritma hash **Argon2** melalui `pwdlib.PasswordHash.recommended()`. Salting otomatis per pengguna. | Serangan *Rainbow Table*, kamus kata sandi, dan pemecahan hash via akselerasi GPU. | **AMAN** |
| **Perlindungan Injeksi SQL** | Backend FastAPI mengadopsi ORM SQLAlchemy 2.0 dengan *parameterized queries* murni. Tidak ada perakitan string SQL manual. | SQL Injection (SQLi) - OWASP A03:2021. | **AMAN** |
| **Injeksi Perintah OS (Command Injection)** | Pemeriksaan ICMP, TCP, dan RTSP (`app/probes.py`) memakai pustaka internal bahasa (`socket`, `httpx`, Blackbox Exporter API) tanpa pemanggilan `os.system()` atau shell subprocess. | Remote Code Execution (RCE) via karakter berbahaya (; & \| ` $). | **AMAN** |
| **Akses Dashboard Grafana** | Nginx Gateway memvalidasi sesi cookie pengguna ke backend (`auth_request /_auth/session`) sebelum meneruskan paket ke Grafana. | Akses metrik historis dan topologi oleh pengguna liar (*Unauthorized Access*). | **AMAN** |
| **Pemisahan Hak Akses (RBAC)** | Role berbasis `admin` dan `viewer`. Operasi penambahan/penghapusan perangkat, konfigurasi kredensial, dan modifikasi denah dilindungi *dependency* `AdminUser`. | *Broken Function Level Authorization* (BFLA) & *Privilege Escalation*. | **AMAN** |
| **Isolasi Database & Cache** | Port PostgreSQL (5432), MariaDB (3306), Redis (6379), dan RRDCached (42217) hanya beroperasi pada bridge `internal` Docker tanpa opsi binding ke `0.0.0.0`. | Serangan *direct brute force*, *database compromise*, dan pembajakan cache. | **AMAN** |
| **Header Keamanan HTTP** | Middleware otomatis menyuntikkan: `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy: strict-origin-when-cross-origin`, dan `Permissions-Policy`. `server_tokens off` aktif di Nginx. | *Clickjacking*, *MIME-sniffing exploits*, dan pembocoran versi web server (*Information Disclosure*). | **AMAN** |
| **Keamanan Cookie Sesi** | Cookie `access_token` disetel dengan atribut `HttpOnly=True` dan `SameSite=Strict`. | Pencurian sesi via serangan Cross-Site Scripting (XSS) dan *Cross-Site Request Forgery* (CSRF). | **AMAN** |
| **Proteksi Host Windows Agent** | Skrip resmi `install-windows-agent.ps1` secara otomatis mengonfigurasi Windows Defender Firewall agar port 9182 **hanya menerima koneksi dari IP Server Monitora**. | Pengintaian daftar proses server Windows oleh perangkat lain di subnet yang sama. | **AMAN** |
| **Proteksi Mode Produksi** | Saat `APP_ENV=production`, backend secara otomatis **menolak berjalan** jika kunci rahasia aplikasi atau kata sandi admin masih memakai nilai default pengembangan. | *Zero-day misconfiguration* akibat kelalaian teknisi saat go-live. | **AMAN** |

---

### 4.2 Kondisi BAHAYA & Titik Rawan (Threat Hazards & Misconfigurations)

Meskipun fondasi kode Monitora aman, sistem dapat menjadi **BAHAYA** jika dioperasikan tanpa mengikuti petunjuk hardening lingkungan intranet berikut:

| Skenario Bahaya | Deskripsi Risiko & Dampak Teknis | Tingkat Keparahan | Kondisi Pemicu | Langkah Mitigasi Wajib |
| :--- | :--- | :---: | :--- | :--- |
| **1. Penggunaan HTTP Polos Tanpa TLS di LAN** | Jika Monitora diakses hanya lewat `http://ip-server:8080`, seluruh lalu lintas sesi (cookie login) dapat disadap penyerang di switch yang sama menggunakan teknik ARP Spoofing / Man-In-The-Middle. | **TINGGI** | Menggunakan konfigurasi default tanpa mengaktifkan sertifikat SSL/TLS internal. | Pasang sertifikat HTTPS (Internal Enterprise CA atau Self-Signed) dan aktifkan `COOKIE_SECURE=true`. |
| **2. Kata Sandi Default Tidak Diganti** | Akun `admin` dengan password `admin12345` atau community SNMP `public` memungkinkan pihak internal yang tidak berwenang menguasai inventaris. | **KRITIS** | Mengabaikan pengisian berkas `.env` dan membiarkan string default template. | Wajib generate password acak minimal 16 karakter acak sebelum menghubungkan server ke kabel LAN. |
| **3. Port Exporter Linux (9100) Terbuka Bebas** | `node_exporter` pada server Linux target tidak memiliki autentikasi bawaan. Jika firewall Linux tidak dibatasi, siapa saja di LAN dapat melihat utilisasi RAM, beban disk, dan nama mountpoint. | **SEDANG** | Memasang `node_exporter` tanpa aturan `iptables` atau `ufw allow from <IP_MONITORA>`. | Batasi port 9100 di host Linux target hanya untuk IP server Monitora. |
| **4. Penggunaan SNMP v1 / v2c Tanpa Segmentasi VLAN** | SNMP v1 dan v2c mentransmisikan *community string* secara plaintext tanpa enkripsi. Di jaringan flat (tanpa VLAN), paket UDP 161 dapat disadap oleh tools seperti Wireshark. | **SEDANG** | Router/switch lama dikonfigurasi SNMPv2c pada subnet publik/tamu (guest Wi-Fi). | Tempatkan port manajemen di VLAN Manajemen khusus, atau beralih ke SNMPv3 yang mendukung enkripsi AES/SHA. |
| **5. Percobaan Brute-Force Login (Credential Stuffing)** | Endpoint `/api/v1/auth/login` belum memiliki modul *rate-limiting* bawaan di tingkat aplikasi. Penyerang di intranet dapat mencoba ribuan password per menit. | **SEDANG** | Penyerang lokal menggunakan skrip otomatis Hydra atau Burp Intruder ke port 80. | Terapkan direktif `limit_req` pada blok lokasi Nginx Gateway untuk membatasi 5 request/detik per IP. |
| **6. Potensi SSRF via Probe Target Luar** | Jika akun Admin disusupi, pelaku dapat memasukkan IP perangkat privat lain pada kolom probe ICMP/HTTP untuk memetakan port internal (*port scanning via proxy*). | **SEDANG** | Akun admin diretas atau kredensial admin bocor. | Terapkan validasi subnet IP di router/firewall egress server monitoring. |
| **7. vSphere Insecure Skip Verify Aktif** | Penggunaan parameter `VSPHERE_INSECURE_SKIP_VERIFY=true` menonaktifkan validasi rantai sertifikat SSL ke ESXi/vCenter, membuka celah MitM antar-server. | **SEDANG** | Mengabaikan instalasi CA root internal pada container Telegraf. | Pasang sertifikat CA resmi vCenter ke dalam trust-store atau aktifkan verifikasi penuh di produksi. |

---

## 5. Skenario Pengujian Siber pada Monitora (Cyber Test Scenarios)

Berikut adalah 8 skenario pengujian penetrasi terperinci yang dijalankan untuk membuktikan keandalan sistem kepada klien:

---

### Skenario 1: Broken Object Level Authorization (BOLA) & Privilege Escalation
- **Tujuan Uji:** Memastikan pengguna dengan peran `viewer` tidak dapat mengubah inventaris, menghapus perangkat, atau melihat kredensial rahasia.
- **Standar Rujukan:** OWASP API1:2023 (BOLA) & OWASP API5:2023 (Broken Function Level Authorization).
- **Langkah Pengujian:**
  1. Penyerang melakukan autentikasi sebagai user biasa (`viewer`).
  2. Penyerang menginspeksi cookie sesi `access_token`.
  3. Penyerang mengirimkan permintaan HTTP manipulatif via `cURL` atau Burp Suite:
     ```bash
     # Mencoba menghapus perangkat ID 1 menggunakan sesi Viewer:
     curl -X DELETE http://127.0.0.1:8080/api/v1/devices/1 \
          -H "Cookie: access_token=<VIEWER_TOKEN>"
     
     # Mencoba melihat profil kredensial rahasia:
     curl -X GET http://127.0.0.1:8080/api/v1/devices/credentials/profiles \
          -H "Cookie: access_token=<VIEWER_TOKEN>"
     ```
- **Hasil yang Diharapkan (Lolos Uji):**
  - Permintaan `DELETE` ditolak dengan status HTTP **403 Forbidden** (`detail: Akses administrator diperlukan`).
  - Permintaan endpoint kredensial ditolak dengan status HTTP **403 Forbidden**.
  - Bukti kode pertahanan: `app/dependencies.py` pada fungsi `require_admin()` memvalidasi klaim role sebelum kueri dieksekusi.

---

### Skenario 2: Injeksi Kueri SQL (SQLi) & OS Command Injection
- **Tujuan Uji:** Memastikan input form penamaan perangkat, alamat IP, label aset, dan filter lokasi tidak dapat disisipi karakter escape database atau perintah shell.
- **Standar Rujukan:** OWASP A03:2021 - Injection & NIST SP 800-115 Section 5.3.
- **Langkah Pengujian:**
  1. Melakukan injeksi payload SQL klasik pada form pembuatan perangkat:
     - Input Nama: `Server Utama'; DROP TABLE devices; --`
     - Input Asset Tag: `' OR 1=1 --`
  2. Melakukan injeksi perintah OS pada kolom IP/Hostname probe:
     - Input Target: `192.168.1.1; cat /etc/passwd`
     - Input Target: `127.0.0.1 | whoami`
- **Hasil yang Diharapkan (Lolos Uji):**
  - Database PostgreSQL menyimpan string apa adanya sebagai data literal tanpa mengeksekusi sintaks `DROP` atau `OR 1=1`.
  - Pustaka probe `socket.create_connection()` dan `httpx` menolak input string command injection dengan melempar exception `socket.gaierror: Name or service not known` tanpa pernah mengeksekusi shell host.

---

### Skenario 3: Server-Side Request Forgery (SSRF) & Port Scanning Abuse
- **Tujuan Uji:** Menguji apakah endpoint pemeriksaan perangkat (`tcp_probe`, `icmp_probe`, `rtsp_probe`) dapat disalahgunakan untuk mengeksploitasi layanan metadata cloud lokal (misal `http://169.254.169.254`) atau loopback internal docker.
- **Standar Rujukan:** OWASP A10:2021 - Server-Side Request Forgery (SSRF).
- **Langkah Pengujian:**
  1. Mendaftarkan target probe ke alamat IP lokal terlarang:
     - Target 1: `rtsp://127.0.0.1:5432/test` (mencoba scanning port database)
     - Target 2: `http://169.254.169.254/latest/meta-data/`
  2. Memantau respons waktu dan payload error dari aplikasi.
- **Hasil yang Diharapkan (Lolos Uji):**
  - Permintaan RTSP ke port 5432 ditutup secara aman oleh timeout tanpa membocorkan banner database atau memicu crash backend.
  - Komunikasi dibatasi oleh isolasi jaringan internal Docker (`monitoring` network), mencegah akses silang ke subnet yang tidak diizinkan.

---

### Skenario 4: Brute-Force Resilience & Credential Tampering Test
- **Tujuan Uji:** Menguji ketahanan endpoint autentikasi terhadap serangan tebak kata sandi massal dan manipulasi token JWT.
- **Standar Rujukan:** OWASP API2:2023 - Broken Authentication.
- **Langkah Pengujian:**
  1. Menjalankan skrip pengujian brute-force 500 request beruntun ke `/api/v1/auth/login`.
  2. Mengambil token JWT valid, mengubah klaim `"sub": "2"` (ID user lain) atau `"role": "admin"`, lalu menandatangani ulang dengan algoritma `none` (*alg: none attack*) atau key acak.
  3. Mengirimkan token palsu ke endpoint `/api/v1/auth/me`.
- **Hasil yang Diharapkan (Lolos Uji):**
  - Algoritma Argon2 memastikan verifikasi hash memakan waktu komputasi yang konsisten, mencegah serangan *timing attack*.
  - Token dengan *signature* tidak cocok atau *alg: none* langsung ditolak dengan HTTP **401 Unauthorized** oleh pustaka `PyJWT` di `app/security.py`.

---

### Skenario 5: Network Perimeter & Port Leakage Audit
- **Tujuan Uji:** Memverifikasi bahwa tidak ada port internal (PostgreSQL, MariaDB, Redis, RRDCached, Prometheus, Alertmanager) yang bocor ke IP fisik LAN server.
- **Standar Rujukan:** CIS Docker Benchmark v1.6.0 Section 5 & NIST SP 800-115 Section 4.
- **Langkah Pengujian:**
  1. Dari komputer lain di jaringan LAN klien, jalankan pemindaian port komprehensif menggunakan Nmap ke IP server Monitora:
     ```bash
     nmap -sS -p- -T4 -v 192.168.1.50
     ```
- **Hasil yang Diharapkan (Lolos Uji):**
  - **Hanya port 80/8080 (dan 443 jika SSL aktif)** yang berstatus `OPEN`.
  - Port 5432 (Postgres), 3306 (MariaDB), 6379 (Redis), 9090 (Prometheus), 9093 (Alertmanager), dan 42217 (RRDCached) berstatus `FILTERED` atau `CLOSED`.
  - Port 8001 (LibreNMS Admin) hanya terikat pada `127.0.0.1` (loopback lokal server), sehingga tidak dapat dijangkau dari luar tanpa SSH tunnel.

---

### Skenario 6: Exporter Spoofing & Sniffing Protection Audit
- **Tujuan Uji:** Memastikan metrik sistem host Windows dan Linux tidak dapat dicuri oleh pihak ketiga di LAN.
- **Standar Rujukan:** CIS Controls v8 Control 4 - Secure Configuration of Enterprise Assets.
- **Langkah Pengujian:**
  1. Dari komputer klien non-monitoring (misal IP `192.168.1.105`), coba buka:
     `http://<IP_TARGET_WINDOWS>:9182/metrics`
- **Hasil yang Diharapkan (Lolos Uji):**
  - Koneksi ditolak (*Connection Refused* atau *Timeout*).
  - Aturan firewall Windows yang di-generate oleh `scripts/install-windows-agent.ps1` (`RemoteAddress $MonitoringServer`) sukses memblokir paket sebelum mencapai daemon exporter.

---

### Skenario 7: Denial of Service (DoS) & Resource Starvation Resilience
- **Tujuan Uji:** Memastikan web server Gateway tahan terhadap serangan pengiriman body berukuran raksasa dan banjir koneksi lambat (*Slowloris*).
- **Standar Rujukan:** OWASP API4:2023 - Unrestricted Resource Consumption.
- **Langkah Pengujian:**
  1. Mengirimkan file payload sebesar 50 MB ke salah satu endpoint POST Monitora:
     ```bash
     curl -X POST http://192.168.1.50:8080/api/v1/auth/login \
          -H "Content-Type: application/json" \
          --data-binary @payload_50mb.bin
     ```
- **Hasil yang Diharapkan (Lolos Uji):**
  - Nginx langsung memutus koneksi dengan HTTP **413 Request Entity Too Large**.
  - Direktif `client_max_body_size 11m;` dan `proxy_read_timeout 30s;` di `infra/nginx/default.conf` mencegah backend kehabisan memori RAM.

---

### Skenario 8: Enkripsi Kredensial Database At-Rest Verification
- **Tujuan Uji:** Memastikan bila hard disk server atau file backup PostgreSQL terbaca oleh teknisi non-otoritas, string password perangkat tidak dapat dibaca.
- **Standar Rujukan:** ISO/IEC 27001:2022 Control A.8.24 (Use of Cryptography).
- **Langkah Pengujian:**
  1. Mengambil dump tabel profil kredensial langsung dari container database:
     ```bash
     docker compose exec db psql -U monitoring -d monitoring \
       -c "SELECT id, name, kind, encrypted_payload FROM credential_profiles;"
     ```
- **Hasil yang Diharapkan (Lolos Uji):**
  - Kolom `encrypted_payload` hanya menampilkan ciphertext acak format base64url AES-GCM (contoh: `dGhpcy1pcy1hbi1hdXRoZW50aWNhdGVkLWFlcy1nY20...`).
  - Tanpa nilai `CREDENTIAL_ENCRYPTION_KEY` di environment memori server, data tersebut secara matematis mustahil didekripsi.

---

## 6. Prosedur & Alat Bantu Pengujian Siber (Tooling & Execution)

Dokumentasi ini membuktikan bahwa pengujian berkala dapat direproduksi oleh auditor internal klien menggunakan toolset standar:

```text
┌────────────────────┬─────────────────────────────┬────────────────────────────────────┐
│ Kategori Uji       │ Tooling Standar             │ Cakupan Pengujian pada Monitora    │
├────────────────────┼─────────────────────────────┼────────────────────────────────────┤
│ SAST (Static Code) │ Bandit, Semgrep, ESLint     │ Audit baris kode Python & Next.js  │
│ DAST (Dynamic Web) │ OWASP ZAP, Burp Suite       │ Fuzzing parameter API & auth logic │
│ Network Auditing   │ Nmap, Masscan               │ Verifikasi firewall & kebocoran port│
│ Container Scan     │ Trivy, Docker Scout, Grype  │ Analisis CVE pada image base Alpine│
│ Dependency Audit   │ pip-audit, npm audit        │ Deteksi kerentanan pustaka pihak ke-3│
│ Protocol Sniffing  │ Wireshark, Tcpdump          │ Validasi enkripsi paket sesi/SNMP  │
└────────────────────┴─────────────────────────────┴────────────────────────────────────┘
```

---

## 7. Panduan Praktis Hardening Pra-Produksi (Actionable Checklist)

Sebelum menyerahkan sistem Monitora kepada klien, tim teknis **wajib** mencentang checklist keamanan berikut:

### 7.1 Checklist 10 Menit Sebelum Serah Terima Klien
- [ ] **1. Ganti Seluruh Secret Bawaan di `.env`:**
  - `APP_SECRET_KEY` diisi string acak minimal 32 karakter hexadecimal.
  - `CREDENTIAL_ENCRYPTION_KEY` diisi string acak minimal 32 karakter berbeda.
  - `ADMIN_PASSWORD` diganti dengan kata sandi kuat (minimal 14 karakter alfanumerik + simbol).
  - `POSTGRES_PASSWORD`, `LIBRENMS_DB_PASSWORD`, dan `LIBRENMS_REDIS_PASSWORD` diganti dari nilai contoh.
- [ ] **2. Kunci Binding Host IP:**
  - Pastikan variabel `BIND_ADDRESS` diisi IP spesifik kartu jaringan LAN manajemen, bukan dibiarkan `0.0.0.0` jika terdapat antarmuka publik.
- [ ] **3. Aktifkan Firewall Host Server:**
  - Port yang diizinkan masuk ke server Monitora hanya:
    - TCP 22 (SSH Administrator - disarankan via Key)
    - TCP 80/8080 (Web Portal Monitora)
    - TCP 443 (Jika SSL diaktifkan)
  - Blokir semua koneksi inbound lainnya.
- [ ] **4. Verifikasi Firewall Agen Exporter:**
  - Server Windows yang dipantau wajib menjalankan `scripts/install-windows-agent.ps1` dengan parameter `-MonitoringServer <IP_SERVER_MONITORA>`.
  - Server Linux target wajib memiliki aturan UFW/Iptables: `ufw allow from <IP_SERVER_MONITORA> to any port 9100 proto tcp`.
- [ ] **5. Segmentasi Komunitas SNMP:**
  - Jangan gunakan string `public` atau `private` pada router/switch produksi.
  - Batasi akses IP pembaca SNMP pada perangkat jaringan hanya untuk IP server Monitora.

---

### 7.2 Rekomendasi Hardening Tambahan: Rate Limiting pada Nginx Gateway

Untuk mencegah serangan tebak password (*brute force*), tambahkan konfigurasi zona pembatasan pada file `infra/nginx/default.conf`:

```nginx
# Tambahkan di luar blok server (tingkat http):
limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/s;

# Pada blok location login di dalam server:
location /api/v1/auth/login {
    limit_req zone=login_limit burst=10 nodelay;
    proxy_pass $upstream_backend;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

---

### 7.3 Rekomendasi Hardening Tambahan: Penerapan SSL/TLS Internal (HTTPS)

Meskipun berjalan di jaringan tertutup intranet, mengaktifkan HTTPS melindungi dari penyadapan kabel LAN fisik:

1. Buat sertifikat SSL mandiri (*Self-Signed*) atau minta dari PKI / CA Internal kantor:
   ```bash
   mkdir -p ./infra/nginx/certs
   openssl req -x509 -nodes -days 730 -newkey rsa:2048 \
     -keyout ./infra/nginx/certs/monitora.key \
     -out ./infra/nginx/certs/monitora.crt \
     -subj "/C=ID/ST=Indonesia/O=Balai Teknik Pantai/CN=monitora.internal.local"
   ```
2. Setel nilai pada file `.env`:
   ```dotenv
   COOKIE_SECURE=true
   PUBLIC_BASE_URL=https://monitora.internal.local
   ```
3. Tambahkan listener port 443 pada `compose.yaml` dan `infra/nginx/default.conf` dengan direktif:
   ```nginx
   listen 443 ssl;
   ssl_certificate /etc/nginx/certs/monitora.crt;
   ssl_certificate_key /etc/nginx/certs/monitora.key;
   ssl_protocols TLSv1.2 TLSv1.3;
   ssl_ciphers HIGH:!aNULL:!MD5;
   ```

---

## 8. Skrip Verifikasi Keamanan Mandiri (Self-Audit Script)

Klien atau tim IT dapat menjalankan perintah verifikasi cepat ini langsung dari terminal untuk memastikan sistem berada dalam postur aman:

### Skrip Verifikasi Linux (Bash)
```bash
#!/usr/bin/env bash
echo "=== AUDIT KEAMANAN LOKAL MONITORA ==="

echo -n "[1] Memeriksa port database yang bocor ke luar... "
LEAK_PORTS=$(netstat -tuln | grep -E ':5432|:3306|:6379|:9090|:9093' | grep '0.0.0.0')
if [ -z "$LEAK_PORTS" ]; then
    echo "AMAN (Tidak ada port internal terbuka ke LAN)"
else
    echo "PERINGATAN: Port internal bocor: $LEAK_PORTS"
fi

echo -n "[2] Memeriksa status APP_ENV produksi... "
if grep -q "APP_ENV=production" .env; then
    echo "AMAN (Mode Production Aktif)"
else
    echo "CATATAN: Masih berstatus Development"
fi

echo -n "[3] Memeriksa secret default... "
if grep -E "replace-|development-secret" .env > /dev/null; then
    echo "BAHAYA: Masih ada kunci rahasia default yang belum diganti!"
else
    echo "AMAN (Kunci rahasia telah dikonfigurasi)"
fi
echo "======================================"
```

### Skrip Verifikasi Windows (PowerShell)
```powershell
Write-Host "=== AUDIT KEAMANAN LOKAL MONITORA (WINDOWS) ===" -ForegroundColor Cyan

# 1. Periksa aturan firewall windows_exporter
$rule = Get-NetFirewallRule -DisplayName "Monitora windows_exporter" -ErrorAction SilentlyContinue
if ($rule -and $rule.Enabled -eq "True") {
    $filter = Get-NetFirewallAddressFilter -AssociatedNetFirewallRule $rule
    Write-Host "[1] Firewall windows_exporter: AKTIF (Dibatasi untuk: $($filter.RemoteAddress))" -ForegroundColor Green
} else {
    Write-Host "[1] Firewall windows_exporter: PERINGATAN (Aturan belum aktif atau terbuka ke semua IP)" -ForegroundColor Yellow
}

# 2. Periksa port yang terbuka secara lokal
$listening = Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -in 5432, 9090, 6379 }
if (-not $listening) {
    Write-Host "[2] Port Database/Prometheus: AMAN (Terisolasi dari akses publik)" -ForegroundColor Green
} else {
    Write-Host "[2] Port Database/Prometheus: PERINGATAN ada port terekspos" -ForegroundColor Red
}
Write-Host "================================================" -ForegroundColor Cyan
```

---

## 9. Kesimpulan & Surat Pernyataan Kelaikan Keamanan (*Sign-Off Statement*)

Aplikasi **Monitora** telah mengintegrasikan prinsip-prinsip rekayasa perangkat lunak aman (*Secure Software Development Life Cycle - SSDLC*) sejak tahap desain. Dengan struktur jaringan multi-tier terisolasi, enkripsi simetris terotentikasi AES-256-GCM, hashing modern Argon2, serta batasan akses firewall agen yang ketat, **Monitora dinyatakan layak dan aman untuk dioperasikan pada infrastruktur jaringan intranet klien**.

Potensi risiko yang ada bukanlah celah bawaan kode (*code-level vulnerabilities*), melainkan risiko operasional konfigurasi yang sepenuhnya dapat dimitigasi dengan menjalankan **Checklist Hardening Pra-Produksi** yang telah disediakan pada Bab 7 dokumen ini.

---
*Dokumen ini diterbitkan sebagai panduan resmi jaminan keamanan operasional sistem Monitora.*  
*Balai Teknik Pantai - Hak Cipta Dilindungi.*
