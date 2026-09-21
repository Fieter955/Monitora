# Uji LibreNMS dengan perangkat fisik dari laptop Windows

Panduan ini dipakai untuk menguji jalur yang benar-benar digunakan Monitora:

```text
Monitora/LibreNMS di container
        |
Docker Desktop + WSL2
        |
Windows 11
        |
Ethernet khusus lab (192.168.250.10/24)
        |
perangkat jaringan fisik
```

Pengujian ini membuktikan discovery SNMP, inventaris port, polling, LLDP/CDP, dan respons ketika kabel atau port berubah. Laptop tetap boleh memakai Wi-Fi untuk internet. Ethernet dipakai khusus untuk lab dan tidak diberi default gateway agar rute internet tidak terganggu.

## Topologi yang direkomendasikan

Laptop hanya membutuhkan satu kabel ke switch utama. Semua perangkat lain tetap tersambung melalui router, switch utama, dan switch cabang seperti jaringan sebenarnya. Kabel tidak perlu dipindah-pindahkan dari laptop ke setiap perangkat.

```text
Internet/ISP (boleh tidak disambungkan saat lab)
                       |
                 port WAN Router-LAB
                  192.168.250.1
                       |
                 port LAN router
                       |
                port 1 SW-CORE-LAB
                 192.168.250.2
                  /            \
        port 2   /              \ port 3/uplink
                /                \
Laptop Windows 11              SW-ACCESS-LAB
Ethernet 192.168.250.10         192.168.250.4
Wi-Fi tetap untuk internet        /        \
                                AP-LAB     Client-LAB
                              192.168.250.3 192.168.250.20
```

Urutan logisnya adalah **router LAN -> switch utama -> switch cabang/perangkat**. Laptop ditempatkan sebagai salah satu perangkat pada switch utama, sama seperti VM Monitora nantinya berada pada jaringan manajemen instansi. Router boleh tetap menyediakan DHCP untuk client, tetapi semua IP manajemen dan IP laptop sebaiknya statis atau memakai DHCP reservation.

Gunakan kabel Ethernet biasa; perangkat modern umumnya mendukung auto MDI-X. Jangan sambungkan jaringan lab ke LAN produksi. Port WAN router boleh dibiarkan kosong selama pengujian lokal agar lab tetap terisolasi.

Jika hanya tersedia router dan satu switch, gunakan:

```text
Router port LAN ----- Switch utama ----- Laptop
                          |
                     perangkat lain
```

Hub atau unmanaged switch tetap dapat dipasang sebagai penghubung kabel, tetapi tidak mempunyai IP manajemen, SNMP, atau daftar status port. Monitora dapat memantau perangkat di belakangnya, tetapi tidak dapat memastikan port mana pada hub yang bermasalah. Untuk pengujian port dan LLDP/CDP, setidaknya salah satu switch harus managed.

## Alamat lab

| Perangkat | Alamat | Catatan |
| --- | --- | --- |
| Laptop Ethernet | `192.168.250.10/24` | Gateway dan DNS dikosongkan |
| Router lab | `192.168.250.1/24` | Gunakan port LAN, bukan WAN |
| Managed switch utama | `192.168.250.2/24` | Aktifkan SNMP read-only dan LLDP/CDP |
| Access point | `192.168.250.3/24` | Mode bridge/AP; DHCP dan NAT dimatikan |
| Managed switch akses | `192.168.250.4/24` | Opsional, diperlukan untuk uji link LLDP antarswitch |
| Client uji | `192.168.250.20/24` | Opsional |
| Kamera uji | `192.168.250.30/24` | Opsional |

Sebelum memakai subnet ini, jalankan `route print -4` dan pastikan `192.168.250.0/24` tidak sedang digunakan Wi-Fi, VPN, atau jaringan lain. Jika bentrok, pilih satu subnet RFC1918 lain dan ganti seluruh alamat secara konsisten.

## Konfigurasi Windows

1. Sambungkan laptop ke internet melalui Wi-Fi bila diperlukan.
2. Buka **Settings > Network & internet > Advanced network settings > More network adapter options**.
3. Buka properti adapter Ethernet, lalu atur IPv4 manual:
   - IP: `192.168.250.10`
   - subnet mask: `255.255.255.0`
   - default gateway: kosong
   - DNS: kosong
4. Pastikan Ethernet dikategorikan sebagai jaringan private jika kebijakan Windows mengizinkan.
5. Jangan membuat network bridge antara Wi-Fi dan Ethernet dan jangan mengaktifkan Internet Connection Sharing. Docker Desktop cukup melakukan koneksi keluar melalui NAT-nya.

Pengaturan tanpa gateway penting agar Windows tetap memakai Wi-Fi untuk internet, tetapi mengirim trafik `192.168.250.0/24` langsung melalui Ethernet.

## Konfigurasi perangkat

1. Beri setiap perangkat alamat manajemen statis sesuai tabel.
2. Pastikan hanya ada satu DHCP server. Untuk lab yang deterministik, matikan DHCP pada seluruh perangkat dan gunakan IP statis.
3. Aktifkan SNMP read-only. Gunakan SNMPv3 jika perangkat mendukung; SNMPv2c boleh dipakai pada lab terisolasi.
4. Aktifkan LLDP pada semua managed switch. Aktifkan CDP bila perangkat Cisco memerlukannya.
5. Isi hostname, deskripsi port, dan lokasi agar hasil discovery mudah dikenali.
6. Jangan menyimpan community string atau password dalam dokumentasi maupun Git.

Dalam panduan ini, **target/perangkat yang diuji** berarti setiap perangkat yang memiliki IP manajemen, misalnya router, managed switch, access point, atau kamera. Hub/unmanaged switch tidak menjadi target SNMP karena tidak mempunyai alamat manajemen. Jalankan preflight satu kali untuk setiap IP target, misalnya:

```powershell
.\scripts\test-librenms-lab.ps1 -Target 192.168.250.1 # router
.\scripts\test-librenms-lab.ps1 -Target 192.168.250.2 # switch utama
.\scripts\test-librenms-lab.ps1 -Target 192.168.250.4 # switch cabang
```

## Preflight dari Windows dan container

Dari root repository, jalankan PowerShell:

```powershell
.\scripts\test-librenms-lab.ps1 -Target 192.168.250.2
```

Skrip memeriksa konflik rute, status Compose, ping dari Windows, ping dari container LibreNMS, dan validasi instalasi LibreNMS. Ping yang berhasil belum membuktikan SNMP; pemeriksaan SNMP dilakukan saat perangkat ditambahkan dan di-discover oleh LibreNMS.

Jika Windows dapat melakukan ping tetapi container tidak, periksa firewall Windows, VPN, kebijakan endpoint security, dan restart Docker Desktop. Jangan mengubah Docker menjadi bridged network sebelum penyebabnya dipastikan.

## Aktivasi LibreNMS dan discovery Monitora

1. Pastikan stack berjalan dengan `docker compose up -d --build`.
2. Buka `http://127.0.0.1:8001`, selesaikan pembuatan admin LibreNMS, lalu buat API token khusus Monitora.
3. Isi `LIBRENMS_API_TOKEN` pada `.env`, kemudian jalankan:

   ```powershell
   docker compose up -d backend network-worker
   ```

4. Buka `http://localhost:8080/perangkat` dan tambah managed switch terlebih dahulu.
5. Isi alamat IP manajemen dan kredensial SNMP read-only.
6. Tombol **Uji koneksi** memastikan API LibreNMS tersedia. Verifikasi SNMP ke perangkat sesungguhnya terjadi setelah **Simpan & temukan port** dijalankan.
7. Tunggu satu siklus discovery/polling, lalu pastikan port, status operasional, kecepatan, error/discard, dan identitas perangkat muncul.
8. Tambahkan router, switch akses, dan AP. Tambahkan kedua switch agar link LLDP/CDP dapat dipetakan.
9. Tandai port uplink/AP/server sebagai `wajib`, port kosong sebagai `cadangan`, dan port pengguna yang tidak perlu alert sebagai `diabaikan`.

## Matriks uji kondisi jaringan

Interval sinkronisasi Monitora saat ini 60 detik dan kondisi port baru dianggap mismatch setelah dua observasi. Beri waktu sekitar 2-3 menit sebelum menilai hasil.

| Uji | Tindakan | Hasil yang harus terlihat |
| --- | --- | --- |
| Discovery SNMP | Simpan managed switch dengan kredensial benar | Identitas perangkat dan daftar port ditemukan |
| Kredensial salah | Ubah community/user sementara | Discovery gagal dengan pesan yang dapat ditindaklanjuti; rahasia tidak tampil |
| AP mati | Cabut kabel AP dari switch | AP offline dan port wajib tempat AP terhubung berubah down |
| Uplink putus | Cabut uplink SW-ACCESS | Switch akses dan perangkat di belakangnya terdampak; uplink menjadi kandidat akar masalah |
| Port cadangan aktif | Colok client ke port yang ditandai cadangan | Status `unexpected active` muncul setelah dua siklus |
| Polling berhenti | Matikan SNMP sementara | Data ditandai terlambat/unknown, bukan disimpulkan sebagai kabel putus tanpa bukti |
| LLDP/CDP | Hubungkan dua managed switch dengan LLDP/CDP aktif | Jalur menampilkan nama perangkat dan port pada kedua ujung |
| Pemulihan | Sambungkan kembali kabel/aktifkan SNMP | Status kembali sehat setelah polling berikutnya |
| Persistensi | Restart Docker Desktop | Perangkat, port, dan aturan port tetap tersimpan |

Catat waktu tindakan, waktu perubahan pertama terlihat, nama perangkat, nomor port, pesan aplikasi, dan hasil aktual. Jangan melakukan uji cabut kabel pada LAN produksi.

## Kesetaraan dengan deployment ESXi

Saat dipindahkan ke instansi, pola jaringannya tetap sama:

| Lab laptop | ESXi produksi/staging |
| --- | --- |
| Ethernet khusus lab | vNIC VM Monitora |
| `192.168.250.10` | IP statis VM pada VLAN monitoring |
| Kabel ke managed switch lab | ESXi port group/uplink menuju jaringan instansi |
| Route lokal ke subnet lab | Route/firewall antar-VLAN menuju IP manajemen perangkat |
| Docker Desktop/WSL2 NAT | Docker Engine pada VM Linux |

Karena itu, target pengujian bukan menyamakan alamat IP, melainkan memastikan VM/laptop mempunyai jalur dua arah yang diizinkan menuju IP manajemen perangkat untuk ICMP, SNMP UDP 161, HTTP/HTTPS, RTSP, dan TCP 9100. Di instansi, SNMP sebaiknya dibatasi agar hanya menerima permintaan dari IP VM Monitora.

## Kriteria lulus

- Semua managed device dapat ditemukan menggunakan kredensial read-only.
- Port dan statusnya konsisten dengan lampu/link fisik perangkat.
- LLDP/CDP menemukan koneksi antarswitch yang benar.
- Skenario kabel putus, port cadangan aktif, data stale, dan pemulihan menghasilkan status yang tepat.
- Data tetap ada setelah Docker Desktop direstart.
- Seluruh hasil dan keterbatasan perangkat dicatat sebelum membuat VM ESXi.
