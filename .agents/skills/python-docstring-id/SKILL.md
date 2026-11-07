---
name: python-docstring-id
description: Bersihkan kode Python/FastAPI di backend dengan menghapus SEMUA komentar `#` lalu menulis ulang docstring Google style berbahasa Indonesia yang profesional (deskripsi, Args, Returns/Yields, Raises, Attributes) untuk modul, class, method, fungsi helper, service, dan endpoint route. Gunakan saat diminta menghapus komentar, merapikan dokumentasi, atau menambahkan docstring berbahasa Indonesia di backend.
---

# Python Docstring Indonesia (FastAPI Backend)

Skill ini melakukan dua hal pada kode Python di `backend/`:

1. **Menghapus semua komentar `#`** — tanpa pengecualian (termasuk `# type: ignore`,
   `# noqa`, `TODO`, shebang, dan deklarasi encoding).
2. **Menulis ulang seluruh docstring** dalam **Google style berbahasa Indonesia** untuk
   setiap modul, class, method, fungsi publik, fungsi helper `_privat`, dan endpoint route.

> Perilaku kode **tidak boleh berubah**. Yang diubah hanya komentar dan docstring.

## Keputusan yang Sudah Ditetapkan

| Aspek              | Keputusan                                                              |
| :----------------- | :--------------------------------------------------------------------- |
| Format docstring   | Google style: ringkasan + `Args:` / `Returns:` / `Yields:` / `Raises:` / `Attributes:` |
| Bahasa             | Bahasa Indonesia baku dan profesional                                  |
| Komentar `#`       | Hapus semua, tanpa pengecualian                                         |
| Cakupan            | Seluruh `backend/` (routes, services, core, models, schemas, db, dll.) |
| Docstring lama     | Ditulis ulang semua agar seragam                                       |
| Elemen wajib       | Modul, class, method, fungsi publik, fungsi helper `_privat`, endpoint |

## Alat Bantu

Semua script berada di `.agents/skills/python-docstring-id/scripts/` dan dijalankan dari root repo.

- `strip_comments.py` — menghapus komentar menggunakan `tokenize` (aman: `#` di dalam
  string seperti `'#FF0000'` atau di dalam docstring **tidak** ikut terhapus). Setiap
  berkas diverifikasi dengan membandingkan AST sebelum/sesudah; jika berbeda, berkas dilewati.
- `audit_docstrings.py` — melaporkan elemen tanpa docstring, section yang kurang
  (`Args`, `Returns`, `Yields`, `Raises`), parameter yang belum dijelaskan, serta
  docstring yang tampak masih berbahasa Inggris.

Contoh lengkap gaya penulisan: [references/docstring-examples.md](references/docstring-examples.md).
**Baca berkas contoh tersebut sebelum menulis docstring apa pun.**

## Alur Kerja

### Langkah 0 — Persiapan & Baseline Testing
1. Pastikan working tree git bersih (`git status`). Jika ada perubahan yang belum di-commit,
   beri tahu pengguna dan sarankan commit/stash terlebih dahulu agar perubahan mudah di-review.
2. Tentukan target. Default: `backend`. Jika pengguna menyebut folder/berkas tertentu, gunakan itu.
3. **Wajib Menjalankan Baseline Test SEBELUM Perubahan**:
   Jalankan test suite yang relevan dengan target (misalnya `pytest backend/tests` atau uji berkas terkait).
   - Catat status seluruh pengujian (harus hijau/lulus semua sebelum lanjut).
   - Jika dari awal ada pengujian yang gagal, hentikan proses dan laporkan ke pengguna; jangan melakukan refaktor atau modifikasi sebelum baseline stabil.

### Langkah 1 — Hapus Komentar
```powershell
python .agents/skills/python-docstring-id/scripts/strip_comments.py backend --dry-run
python .agents/skills/python-docstring-id/scripts/strip_comments.py backend
```
- Tinjau output dry-run terlebih dahulu. Laporkan berkas berstatus `[GAGAL]` ke pengguna.
- **Jangan** menghapus komentar secara manual dengan regex atau find-replace.
- Sebelum menghapus, baca sekilas komentar yang mengandung informasi penting
  (alasan bisnis, peringatan, rumus). Informasi tersebut **dipindahkan ke docstring**
  fungsi terkait pada Langkah 2, bukan dibuang begitu saja.

### Langkah 2 — Tulis Ulang Docstring (per berkas)
Kerjakan berkas satu per satu, dimulai dari `backend/api/routes/`, lalu `services/`,
`core/`, `models`, `schemas`, dan sisanya. Untuk setiap berkas:

1. Baca seluruh isi berkas dan pahami alur logikanya (ikuti pemanggilan ke service
   bila perlu untuk mengetahui tipe nilai balik dan exception yang dilempar).
2. Tambahkan/ganti **docstring modul** di baris paling atas (sebelum import).
3. Untuk setiap class, method, dan fungsi (termasuk `_privat` dan fungsi bersarang),
   tulis docstring sesuai aturan di bawah.
4. Ganti docstring lama sepenuhnya; jangan mempertahankan kalimat bahasa Inggris.
5. Jangan mengubah kode di luar docstring (nama, logika, urutan, import, format).

### Langkah 3 — Verifikasi, Testing Ulang & Root Cause Analysis
```powershell
python .agents/skills/python-docstring-id/scripts/audit_docstrings.py backend --summary
python .agents/skills/python-docstring-id/scripts/audit_docstrings.py backend/api/routes
python -m compileall -q backend
```
1. **Verifikasi Sintaks dan Struktur**:
   - Pastikan `compileall` sukses tanpa syntax error.
   - Ulangi Langkah 2 untuk berkas yang masih memiliki temuan audit hingga total temuan 0
     (peringatan "tampak berbahasa Inggris" boleh diabaikan bila ternyata false positive,
     misalnya istilah teknis).
2. **Jalankan Test Suite Pasca-Perubahan**:
   - Jalankan test suite yang sama seperti pada Langkah 0 (`pytest backend/tests`).
   - Seluruh test **wajib lulus 100%**.
3. **Protokol Jika Ada Test yang Gagal**:
   - **DILARANG KERAS** memodifikasi assertions, me-mock paksa, mengubah test case agar lolos, atau mengabaikan test!
   - Baca dan pelajari salinan traceback dan kode sumber yang memicu kegagalan secara menyeluruh.
   - Pahami penyebab aslinya: apakah ada string/docstring multiline yang salah kutip, indentation error, token yang terpotong saat stripping komentar, atau ada logika yang tak sengaja tersenggol.
   - Perbaiki murni di level struktur docstring/komentar tanpa mengutak-atik logika asli program hingga test kembali hijau secara organik dan sah.
4. Periksa `git diff --stat` dan pastikan hanya berkas `.py` yang berubah murni pada area komentar dan docstring.

### Langkah 4 — Laporan
Laporkan secara singkat: jumlah komentar terhapus, jumlah berkas yang docstring-nya
ditulis ulang, berkas yang gagal/dilewati, dan hasil audit akhir.

## Aturan Penulisan Docstring

### Struktur
```python
"""Ringkasan satu kalimat diawali kata kerja, diakhiri titik.

Paragraf penjelasan opsional: konteks bisnis, alur penting, atau batasan.

Args:
    nama_param: Penjelasan makna dan batasan nilai parameter.

Returns:
    Penjelasan nilai yang dikembalikan beserta tipe/struktur pentingnya.

Raises:
    NamaException: Kondisi yang menyebabkan exception dilempar.
"""
```

### Aturan Wajib
1. **Ringkasan** diawali kata kerja berimbuhan "me-": *Mengambil*, *Membuat*, *Memeriksa*,
   *Menghitung*, *Memperbarui*, *Menghapus*, *Mengirim*. Jangan diawali "Fungsi ini…".
2. **Args:** cantumkan setiap parameter kecuali `self`/`cls`, dengan urutan sesuai signature.
   Parameter `*args`/`**kwargs` ditulis sebagai `*args:` dan `**kwargs:`.
   Jangan mengulang tipe jika sudah ada type hint; jelaskan **makna**-nya.
3. **Returns:** wajib jika fungsi mengembalikan nilai. Untuk endpoint, jelaskan isi respons
   (field utama dict/schema, atau jenis `StreamingResponse`/`Response`).
4. **Yields:** dipakai untuk generator, menggantikan `Returns:`.
5. **Raises:** wajib jika fungsi melempar exception secara eksplisit. Untuk `HTTPException`,
   sebutkan kode status dan kondisinya, contoh: `HTTPException: 404 jika sesi chat tidak ditemukan.`
   Exception yang dilempar dari service yang dipanggil dan tidak ditangkap juga boleh disebut
   bila relevan bagi pemanggil.
6. **Attributes:** untuk class model SQLAlchemy, schema Pydantic, dataclass, dan konfigurasi —
   jelaskan setiap kolom/field.
7. Section yang tidak relevan **dihilangkan** (jangan menulis "Tidak ada").
8. Fungsi sangat sederhana tanpa parameter dan tanpa nilai balik cukup docstring satu baris.

### Khusus Endpoint FastAPI
- Docstring endpoint tampil sebagai *description* di Swagger (`/docs`), maka tulis dengan
  bahasa yang juga dapat dipahami konsumen API.
- Jelaskan siapa yang boleh mengakses (peran: siswa, konselor, superadmin) jika ada
  pengecekan peran, fitur (`require_feature`), atau persetujuan (`require_student_consent`).
- Parameter dependency (`db`, `current_user`, `request`) dijelaskan singkat dan konsisten:
  - `db`: Sesi database SQLAlchemy yang disuntikkan oleh FastAPI.
  - `current_user`: Pengguna terautentikasi yang melakukan permintaan.
  - `request`: Objek permintaan HTTP mentah dari Starlette.
- Path/query parameter dan body payload dijelaskan maknanya (contoh: `session_id: ID sesi chat yang akan ditutup.`).

### Gaya Bahasa
- Bahasa Indonesia baku, kalimat aktif, ringkas, tanpa bahasa gaul.
- Istilah teknis yang lazim boleh tetap dalam bahasa Inggris (*token*, *payload*, *endpoint*,
  *streaming*, *WebRTC*), ditulis apa adanya atau dengan format kode untuk identifier.
- Nama identifier, field, dan nilai literal ditulis dengan backtick ganda: ``session_id``.
- Indentasi docstring mengikuti indentasi blok fungsi; panjang baris maksimal ±88 karakter.

## Larangan
- **DILARANG KERAS memanipulasi test**: Dilarang mengubah assertion test, menonaktifkan test (`@pytest.mark.skip`), mengabaikan error secara diam-diam, atau menambahkan mock palsu hanya agar test kelihatan berhasil. Testing harus lulus murni dan jujur!
- Jangan mengubah logika, nama fungsi/variabel, signature, import, atau urutan kode aplikasi.
- Jangan menambahkan komentar `#` baru dalam bentuk apa pun.
- Jangan menghapus komentar dengan regex (berisiko merusak string seperti warna hex `#FF0000`).
- Jangan menulis docstring generik yang tidak informatif (mis. "Fungsi untuk memproses data.").
  Setiap docstring harus menjelaskan input, proses inti, dan output secara spesifik.
