# Kuesioner Audit Jaringan untuk Monitoring Perangkat dan Port

Dokumen ini digunakan untuk mencatat kondisi jaringan saat ini sebelum monitoring Monitora dikonfigurasi. Tujuan akhirnya adalah agar tim IT dapat mengetahui perangkat, lokasi, switch, dan nomor port yang terkait ketika terjadi gangguan.

> **Penting:** jangan menuliskan password, Wi-Fi passphrase, SNMP community, private key, atau token API di dokumen ini. Cukup nyatakan apakah akses tersedia dan siapa penanggung jawabnya.

## Petunjuk pengisian

1. Isi berdasarkan kondisi nyata, bukan rancangan yang seharusnya.
2. Gunakan kode perangkat yang konsisten, misalnya `RTR-UTAMA`, `SW-SERVER-01`, dan `AP-L2-03`.
3. Jika informasi belum diketahui, isi `Belum diketahui` dan jangan menebak.
4. Buat satu baris untuk setiap perangkat dan setiap port yang digunakan.
5. Lampirkan foto label perangkat dan kabel jika belum ada dokumentasi.

## A. Identitas instalasi

| Pertanyaan | Jawaban tim IT |
| --- | --- |
| Nama instansi/site | |
| Alamat site | |
| Nama gedung | |
| Jumlah lantai yang memakai jaringan ini | |
| Ruang yang memiliki perangkat jaringan | |
| Lokasi fisik server Monitora | |
| Nama dan kontak penanggung jawab jaringan | |
| Jam operasional jaringan | |
| Waktu pemeliharaan yang diperbolehkan | |
| Gangguan yang paling sering dilaporkan pengguna | |
| Bagaimana gangguan saat ini diketahui dan ditangani? | |

## B. Gambaran jalur jaringan

Jawab pertanyaan berikut berdasarkan urutan kabel dari ISP sampai pengguna.

1. Kabel atau perangkat dari ISP masuk ke perangkat apa?
2. Port WAN mana pada MikroTik/router utama yang terhubung ke ISP?
3. Port LAN mana yang menjadi keluaran utama dari MikroTik?
4. Setelah MikroTik, kabel masuk ke switch apa dan port nomor berapa?
5. Apakah ada switch/hub tambahan setelah switch utama?
6. Apakah terdapat kabel uplink antara Lantai 1 dan Lantai 2? Jika ada, sebutkan perangkat dan port pada kedua ujungnya.
7. Apakah ada perangkat yang tersambung melalui lebih dari satu switch/hub sebelum mencapai switch utama?
8. Apakah ada kabel atau perangkat yang fungsinya belum diketahui?
9. Apakah tim memiliki diagram jaringan lama? Jika ada, lampirkan dan tandai bagian yang sudah tidak sesuai.

Gambarkan jalur aktual secara sederhana. Contoh:

```text
ISP
  |
MikroTik (port: __________)
  |
Switch utama (port: __________)
  |-- Switch/hub Lantai 1 (port uplink: __________)
  |     `-- AP Lantai 1 (port: __________)
  `-- Switch/hub Lantai 2 (port uplink: __________)
        `-- AP Lantai 2 (port: __________)
```

## C. DHCP, IP, dan segmentasi jaringan

1. Perangkat mana yang menjadi DHCP server utama?
2. Apakah DHCP server aktif pada MikroTik?
3. Apakah DHCP server juga aktif pada router yang digunakan sebagai access point?
4. Apakah router ujung menggunakan mode **access point/bridge**, atau masih menggunakan mode **router/NAT**?
5. Kabel menuju router/AP ujung masuk ke port LAN atau WAN?
6. Berapa rentang alamat DHCP yang digunakan?
7. Apa alamat gateway dan subnet mask/prefix jaringan?
8. Apakah terdapat lebih dari satu subnet atau VLAN?
9. Jika terdapat beberapa subnet/VLAN, perangkat dan lokasi mana yang menggunakan masing-masing jaringan?
10. Apakah perangkat jaringan memiliki IP manajemen tetap atau DHCP reservation?
11. Apakah pernah terjadi konflik alamat IP atau dua DHCP server memberikan alamat pada jaringan yang sama?
12. Apakah server Monitora dapat melakukan ping ke seluruh IP manajemen perangkat?

| Jaringan/VLAN | Subnet/prefix | Gateway | DHCP server | Rentang DHCP | Digunakan oleh/lokasi |
| --- | --- | --- | --- | --- | --- |
| | | | | | |
| | | | | | |
| | | | | | |

## D. Inventaris perangkat jaringan

Isi satu baris untuk setiap MikroTik/router, switch, hub, dan access point.

| Kode perangkat | Jenis | Merek dan model | Lokasi lengkap | IP manajemen | Managed? | SNMP? | LLDP/CDP? | Daya/PoE/adaptor | Perangkat upstream | Port upstream | Akses admin tersedia? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| | | | | | Ya/Tidak/Belum diketahui | Ya/Tidak/Belum diuji | Ya/Tidak/Belum diuji | | | | Ya/Tidak |
| | | | | | | | | | | | |
| | | | | | | | | | | | |
| | | | | | | | | | | | |

Pertanyaan tambahan:

1. Perangkat mana yang menjadi router/gateway utama?
2. Switch mana yang menjadi switch utama atau switch server?
3. Perangkat mana yang merupakan managed switch?
4. Perangkat mana yang tidak memiliki IP manajemen?
5. Apakah istilah “hub” yang digunakan benar-benar hub/unmanaged switch, atau managed switch yang belum dikonfigurasi?
6. Apakah nama perangkat pada konfigurasi sesuai dengan label fisiknya?
7. Apakah tanggal pemasangan, serial number, dan status garansi tersedia?

## E. Pemetaan switch, hub, dan kabel

Salin tabel berikut untuk setiap switch yang memiliki port.

### Switch: `____________________________`

Lokasi: `____________________________`  
Merek/model: `____________________________`  
IP manajemen: `____________________________`  
Managed/unmanaged/belum diketahui: `____________________________`

| Port | Label kabel | Perangkat/ruang tujuan | Jenis koneksi | Kondisi normal | Klasifikasi | Catatan |
| --- | --- | --- | --- | --- | --- | --- |
| | | | Uplink/AP/server/user/cadangan | Up/Down | Wajib/Cadangan/Diabaikan | |
| | | | | | |
| | | | | | |
| | | | | | |

Gunakan klasifikasi berikut:

- **Wajib:** uplink, access point, server, CCTV, atau perangkat lain yang harus selalu aktif.
- **Cadangan:** port kosong yang normalnya tidak aktif; perlu diperiksa jika tiba-tiba aktif.
- **Diabaikan:** port pengguna atau port lain yang tidak perlu menghasilkan alert ketika mati.

Jawab untuk setiap switch/hub:

1. Port mana yang menjadi uplink menuju MikroTik atau switch di atasnya?
2. Port mana yang menghubungkan Lantai 1 dan Lantai 2?
3. Port mana yang terhubung ke access point?
4. Port mana yang terhubung ke server atau perangkat kritis?
5. Port mana yang terhubung ke hub/unmanaged switch?
6. Apakah kabel pada kedua ujung sudah memiliki label yang sama?
7. Apakah port yang tidak digunakan sudah dinonaktifkan secara administratif?
8. Apakah switch dapat menampilkan status port, trafik, error/discard, dan penggunaan PoE?

### Cabang di belakang hub/unmanaged switch

> Hub atau unmanaged switch tidak menyediakan SNMP, LLDP/CDP, atau status port. Monitora hanya dapat menunjukkan bahwa cabang atau perangkat di belakangnya bermasalah, bukan memastikan nomor port downstream yang rusak.

| Kode hub | Lokasi | Switch upstream | Port upstream | Jumlah port | Perangkat di belakangnya | Apakah pelacakan port persis wajib? |
| --- | --- | --- | --- | --- | --- | --- |
| | | | | | | Ya/Tidak |
| | | | | | | |

## F. Access point dan Wi-Fi

Isi satu baris untuk setiap access point atau router yang digunakan sebagai access point.

| Kode AP | Lokasi/lantai/ruang | Merek dan model | IP manajemen | Mode bridge/router | DHCP aktif? | NAT aktif? | Port LAN/WAN yang dipakai | Switch/hub induk | Port induk | Daya | SNMP/controller tersedia? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| | | | | | | | | | | | |
| | | | | | | | | | | | |

Untuk setiap AP, jawab:

1. SSID apa saja yang dipancarkan? Jangan tuliskan password Wi-Fi.
2. Apakah perbedaan SSID juga berarti perbedaan subnet/VLAN?
3. Apakah klien mendapatkan IP dari MikroTik atau dari AP tersebut?
4. Apakah AP memiliki IP manajemen tetap/DHCP reservation?
5. Apakah AP dapat diping dari server Monitora?
6. Apakah AP menyediakan SNMP atau dikelola melalui controller/cloud?
7. Apakah jumlah klien, channel, frekuensi, RSSI/SNR, dan utilisasi radio tersedia?
8. Apakah switch induk dapat melaporkan daya PoE untuk AP?
9. Berapa jumlah pengguna normal dan maksimum pada AP tersebut?
10. Area mana yang kehilangan Wi-Fi jika AP ini mati?

## G. Lokasi dan denah dua lantai

Gunakan satu denah terpisah untuk setiap lantai. Denah hanya perlu menunjukkan posisi perangkat; kabel antarlantai dicatat sebagai uplink pada topologi logis.

### Lantai 1

1. Ruang apa saja yang perlu dimasukkan ke Monitora?
2. Di mana posisi switch, hub, AP, rack, dan server?
3. Di mana titik masuk kabel dari lantai lain atau dari ISP?
4. Apakah tersedia denah PNG, JPG, atau WebP?
5. Siapa yang akan memverifikasi posisi perangkat pada denah?

### Lantai 2

1. Ruang apa saja yang perlu dimasukkan ke Monitora?
2. Di mana posisi switch, hub, AP, rack, dan server?
3. Di mana titik masuk kabel dari Lantai 1?
4. Apakah tersedia denah PNG, JPG, atau WebP?
5. Siapa yang akan memverifikasi posisi perangkat pada denah?

## H. Kesiapan SNMP, LLDP/CDP, dan monitoring

1. Perangkat mana yang mendukung SNMP?
2. Versi SNMP yang tersedia: v2c atau v3?
3. Apakah SNMP read-only sudah aktif?
4. Apakah UDP 161 hanya diizinkan dari IP server monitoring?
5. Siapa yang menyimpan dan mengelola kredensial SNMP? Jangan tuliskan kredensialnya di sini.
6. Apakah LLDP atau CDP aktif pada managed switch/router/AP?
7. Apakah nama perangkat dan deskripsi port sudah jelas?
8. Apakah syslog atau SNMP trap tersedia dan diperlukan?
9. Berapa lama keterlambatan deteksi yang masih dapat diterima: 1, 5, atau 15 menit?
10. Siapa yang harus menerima notifikasi dan melalui kanal apa?
11. Apakah ada jam pemeliharaan ketika alert harus dibisukan?

## I. Kebutuhan alert dan informasi tindakan

Tandai kebutuhan yang harus menghasilkan alert.

| Kondisi | Perlu alert? | Prioritas | Penerima | Waktu tunggu sebelum alert |
| --- | --- | --- | --- | --- |
| MikroTik/router utama mati | | | | |
| Switch utama mati | | | | |
| Uplink antarswitch/antarlantai mati | | | | |
| Port wajib mati | | | | |
| AP mati | | | | |
| Hub/cabang tidak dapat dijangkau | | | | |
| Utilisasi port tinggi berkelanjutan | | | | |
| Error/discard port meningkat | | | | |
| Perangkat muncul pada port cadangan | | | | |
| Data monitoring tidak diperbarui | | | | |

Untuk setiap jenis alert, informasi apa yang harus langsung terlihat oleh petugas?

- [ ] Nama perangkat
- [ ] Lantai dan ruang
- [ ] Perangkat upstream
- [ ] Nomor port upstream
- [ ] Waktu terakhir online
- [ ] Perangkat lain yang ikut terdampak
- [ ] Kemungkinan penyebab
- [ ] Langkah pemeriksaan awal
- [ ] Kontak penanggung jawab

## J. Lampiran yang diminta

- [ ] Denah Lantai 1
- [ ] Denah Lantai 2
- [ ] Foto depan dan belakang MikroTik/router utama
- [ ] Foto depan dan label setiap switch/hub
- [ ] Foto access point dan label model
- [ ] Foto label pada kedua ujung kabel uplink
- [ ] Daftar IP atau DHCP lease yang telah disanitasi
- [ ] Diagram jaringan lama
- [ ] Backup konfigurasi yang telah disanitasi dan diserahkan melalui media aman
- [ ] Daftar perangkat yang direncanakan untuk diganti

## K. Uji lapangan terkontrol

Uji hanya dilakukan pada jadwal yang disetujui dan dengan persetujuan penanggung jawab jaringan.

| Skenario | Perangkat/port uji | Hasil yang diharapkan | Hasil aktual | Lulus? |
| --- | --- | --- | --- | --- |
| Cabut kabel satu AP | | Nama AP, lokasi, switch, dan port teridentifikasi | | |
| Nonaktifkan satu port wajib | | Alert port wajib muncul setelah waktu tunggu | | |
| Putuskan uplink switch lantai | | Switch menjadi akar masalah dan perangkat turunannya dicatat sebagai terdampak | | |
| Aktifkan satu port cadangan | | Aktivitas tidak terduga terdeteksi | | |
| Hentikan polling/SNMP sementara | | Monitoring menampilkan data terlambat, bukan perangkat pasti mati | | |

## L. Klasifikasi hasil audit

Klasifikasikan setiap perangkat atau cabang setelah audit.

| Perangkat/cabang | Tingkat visibilitas | Alasan | Tindakan yang diperlukan |
| --- | --- | --- | --- |
| | Penuh/Sebagian/Tidak transparan | | |
| | | | |
| | | | |

Definisi:

- **Penuh:** managed switch/perangkat memiliki IP manajemen, SNMP dapat diakses, serta hubungan dan nomor port terdokumentasi atau ditemukan melalui LLDP/CDP.
- **Sebagian:** perangkat dapat diperiksa dengan ping atau layanan lain, tetapi detail port tidak tersedia.
- **Tidak transparan:** hub/unmanaged switch atau cabang tidak menyediakan telemetri sehingga nomor port dan penyebab downstream tidak dapat dipastikan dari Monitora.

Jika pelacakan sampai nomor port diwajibkan pada cabang yang masih `Tidak transparan`, catat penggantian hub/unmanaged switch dengan managed switch sebagai kebutuhan infrastruktur, bukan sebagai perubahan perangkat lunak.

## M. Persetujuan hasil audit

| Peran | Nama | Tanggal | Catatan/persetujuan |
| --- | --- | --- | --- |
| Pengisi dari tim IT | | | |
| Penanggung jawab jaringan | | | |
| Verifikator lapangan | | | |
| Pengelola Monitora | | | |
