---
name: tsdoc-id
description: Merapikan dokumentasi kode TypeScript/React di frontend dengan TSDoc berbahasa Indonesia yang ringkas (komponen bersama, props interface, custom hook, context, utilitas lib, dan tipe domain), sekaligus membersihkan komentar inline yang hanya menjelaskan "apa" sambil mempertahankan komentar "mengapa". Gunakan saat diminta menambahkan/merapikan dokumentasi, JSDoc/TSDoc, atau komentar di frontend Next.js.
---

# TSDoc Indonesia (Frontend Next.js + TypeScript)

Skill ini adalah pasangan frontend untuk `/python-docstring-id`, namun **filosofinya berbeda**:
TypeScript sudah menjadi dokumentasi kontrak (tipe, interface, union literal). TSDoc hanya
ditambahkan di tempat yang **memberi nilai bagi pemakai API** (muncul di hover/autocomplete IDE),
bukan di setiap fungsi.

> Perilaku kode **tidak boleh berubah**. Yang diubah hanya komentar dan blok TSDoc.

## Keputusan yang Sudah Ditetapkan

| Aspek | Keputusan |
| :-- | :-- |
| Format | TSDoc `/** ... */` dengan tag `@param`, `@returns`, `@throws`, `@default`, `@example`, `@remarks` |
| Bahasa | Bahasa Indonesia baku; istilah teknis lazim boleh tetap Inggris |
| Komentar inline `//` | Hapus yang menjelaskan **apa**; pertahankan/rapikan yang menjelaskan **mengapa** |
| Kode yang dikomentari | Hapus (riwayat ada di git) |
| Cakupan wajib | Lihat tabel "Kapan Wajib TSDoc" |
| Tidak wajib | Helper lokal kecil, handler `onClick` inline, komponen `page.tsx`/`layout.tsx` yang trivial |

## Kapan Wajib TSDoc

| Lokasi | Elemen | Isi minimum |
| :-- | :-- | :-- |
| `frontend/hooks/` | Setiap hook yang diekspor | Ringkasan, `@param`, `@returns` (bentuk objek/tuple), `@remarks` untuk side effect/cleanup |
| `frontend/lib/` | Fungsi & konstanta yang diekspor | Ringkasan, `@param`, `@returns`, `@throws` bila melempar error |
| `frontend/lib/types.ts`, `frontend/types/` | Interface/type domain | Ringkasan tipe; field yang maknanya tidak jelas dari nama (unit, format, nilai enum) |
| `frontend/context/` | Provider & hook context | Ringkasan, nilai yang disediakan, syarat pemakaian (harus di dalam Provider) |
| `frontend/components/ui/`, `layout/` | Komponen bersama | Ringkasan komponen ringkas dan fungsional |
| `frontend/components/features/`, `eeg/`, `Laporan/` | Komponen utama yang diekspor | Ringkasan fungsional satu baris; hindari boilerplate pada interface props |

Elemen non-ekspor, helper lokal camelCase di berkas komponen, dan interface props standar
tidak wajib TSDoc (self-explanatory dari nama dan TypeScript signature).

## Standar Human-Crafted (Anti-Pola Robotik AI)
Agar kode tetap terlihat natural dan profesional seperti ditulis oleh software engineer manusia (bukan bot AI):

1. **Dilarang Mendokumentasikan Field yang Sudah Jelas (*Obvious*)**:
   - Jangan mendokumentasikan properti seperti `isOpen`, `onClose`, `className`, `disabled`, `children`, `label`, `onClick`, `id`, `name`.
   - Menulis `/** Menentukan apakah modal sedang terbuka. */` di atas `isOpen: boolean` adalah tanda paling kentara buatan AI (*dead giveaway*). Biarkan field tersebut *clean*.
2. **Hindari Rumus Pembuka Monoton**:
   - Jangan membuka setiap baris TSDoc dengan formula seragam kaku seperti `"Menampilkan [Nama Komponen] yang..."` atau `"Properti untuk komponen {@link X}"`.
   - Gunakan deskripsi fungsional langsung seperti gaya penulisan senior developer, contoh:
     - *"Modal panduan setup dan pairing konektor SI-Konseling Bridge."*
     - *"Panel telemetri hardware dan status koneksi EEG real-time."*
     - *"Canvas plot topografi 2D interpolasi daya spektral (IDW)."*
3. **Props Interface Tidak Perlu TSDoc Terpisah jika Komponen Utama Sudah Jelas**:
   - Jika komponen React utama sudah memiliki TSDoc, interface `XProps` pendamping tidak perlu diberi komentar boilerplate duplikat (`/** Properti untuk komponen X */`), kecuali ada prop kompleks yang membutuhkan penjelasan logika khusus.
4. **Helper UI / Styling Lokal Bebas dari TSDoc Formal**:
   - Fungsi helper kecil di file komponen seperti pemetaan kelas Tailwind (`priorityBadgeClass`) tidak perlu dipaksa ber-TSDoc formal `@param`/`@returns`. Cukup kode yang bersih dan *intention-revealing*.
5. **Dilarang Komentar Banner / Strip Dekoratif (`// -----`, `// =====`, `// --- JUDUL ---`)**:
   - Garis pemisah artifisial (`// -----------------------`) adalah ciri khas generator teks AI dan sangat tidak wajar ditulis developer manusia.
   - Hapus total seluruh komentar strip atau pembatas seksi. Biarkan struktur kode (early return, helper terpisah, komponen modular) yang berbicara sendiri.

## Alat Bantu

Script berada di `.agents/skills/tsdoc-id/scripts/` dan dijalankan dari root repo.
Script memakai paket `typescript` dari `frontend/node_modules` (tanpa dependensi baru).

- `audit_tsdoc.cjs` — melaporkan elemen wajib (sesuai tabel di atas) yang belum ber-TSDoc,
  `@param` yang tidak cocok dengan signature, TSDoc yang tampak berbahasa Inggris, serta
  blok kode yang dikomentari.

```powershell
node .agents/skills/tsdoc-id/scripts/audit_tsdoc.cjs frontend --summary
node .agents/skills/tsdoc-id/scripts/audit_tsdoc.cjs frontend/hooks
```

Contoh gaya penulisan lengkap: [references/tsdoc-examples.md](references/tsdoc-examples.md).
**Baca berkas contoh tersebut sebelum menulis TSDoc apa pun.**

## Alur Kerja

### Langkah 0 — Persiapan & Baseline
1. Pastikan working tree git bersih (`git status`); jika tidak, sarankan commit/stash.
2. Tentukan target. Default: `frontend/hooks`, `frontend/lib`, `frontend/context`,
   `frontend/components`. Jika pengguna menyebut berkas/folder tertentu, gunakan itu.
3. Jalankan baseline: `cd frontend && node_modules/.bin/tsc --noEmit` (harus exit 0) dan
   `npm run lint`. Catat kegagalan yang sudah ada sebelumnya; jangan memperbaikinya di sini.
4. Jalankan audit untuk mendapat daftar kerja.

### Langkah 1 — Bersihkan Komentar Inline (per berkas)
Klasifikasikan setiap komentar `//` dan `/* */` non-TSDoc:

| Jenis | Tindakan |
| :-- | :-- |
| Menjelaskan **apa** (`// set loading true`, `// map data`) | Hapus |
| Banner / strip dekoratif (`// -----`, `// =====`, `// --- JUDUL ---`) | **Hapus total** (anti-pola bot AI) |
| Menutupi nama buruk (`const d = ... // durasi detik`) | Hapus; **jangan** rename di skill ini kecuali variabel lokal dan pengguna setuju — laporkan sebagai saran `/clean-code` |
| Kode yang dikomentari | Hapus |
| Menjelaskan **mengapa** (workaround browser, batasan backend, alasan bisnis) | Pertahankan; rapikan ke Bahasa Indonesia ringkas |
| Komentar header berkas `//` yang menjelaskan konteks modul | Pindahkan ke TSDoc fungsi/ekspor utama atau `@remarks` |
| Direktif tooling (`// eslint-disable-next-line ...`, `// @ts-expect-error ...`, `"use client"`) | **Jangan disentuh** |
| Penanda section JSX (`{/* Header */}`) di komponen panjang | Boleh dipertahankan jika membantu navigasi; jika komponen sangat panjang, sarankan ekstraksi komponen |

Jangan menghapus komentar dengan regex/find-replace massal — baca konteksnya.

### Langkah 2 — Tulis/Perbarui TSDoc
1. Baca seluruh berkas dan pahami alur (ikuti import bila perlu untuk mengetahui bentuk return).
2. Tambahkan TSDoc sesuai tabel "Kapan Wajib TSDoc".
3. TSDoc yang sudah ada dan sudah berbahasa Indonesia: **pertahankan**, cukup lengkapi tag
   yang kurang. Ganti hanya bila salah, berbahasa Inggris, atau tidak informatif.
4. Jangan mengubah kode di luar komentar (nama, logika, urutan, import, format).

### Langkah 3 — Verifikasi
```powershell
node .agents/skills/tsdoc-id/scripts/audit_tsdoc.cjs frontend --summary
cd frontend; node_modules/.bin/tsc --noEmit; npm run lint
```
1. `tsc --noEmit` wajib exit 0; lint tidak boleh menambah error baru dibanding baseline.
2. Ulangi Langkah 2 hingga temuan audit untuk target = 0 (peringatan bahasa Inggris boleh
   diabaikan bila false positive istilah teknis).
3. `git diff` hanya boleh berisi perubahan komentar/TSDoc. Jika ada perubahan kode, batalkan.
4. **Dilarang** mengubah test, menambah `@ts-ignore`, atau mematikan rule lint agar lolos.

### Langkah 4 — Laporan
Laporkan singkat: jumlah berkas diubah, TSDoc ditambah/diperbarui, komentar dihapus,
saran `/clean-code` (nama buruk, komponen terlalu panjang), dan hasil audit akhir.

## Aturan Penulisan TSDoc

### Struktur
```ts
/**
 * Ringkasan satu kalimat diawali kata kerja, diakhiri titik.
 *
 * @remarks
 * Konteks opsional: alasan desain, side effect, batasan browser/backend.
 *
 * @param namaParam - Makna dan batasan nilai parameter.
 * @returns Makna nilai balik beserta bentuk pentingnya.
 * @throws {@link Error} Kondisi error dilempar.
 *
 * @example
 * ```tsx
 * const { isOpen } = useKeyboardOpen();
 * ```
 */
```

### Aturan Wajib
1. **Ringkasan** ditulis ringkas, jelas, dan fungsional. Untuk fungsi/hook diawali kata kerja
   (*Mengambil*, *Menghitung*, *Mendeteksi*, *Normalisasi*). Untuk komponen dan tipe/interface:
   frasa fungsional to-the-point (*Modal pairing bridge...*, *Payload telemetry...*).
   Hindari formula kaku "Menampilkan komponen X yang berfungsi untuk...".
   Jangan diawali "Fungsi ini…" / "Hook ini…".
2. **`@param nama -`** (dengan tanda hubung, sesuai TSDoc) untuk parameter fungsi/hook.
   Untuk parameter objek destructuring, cukup jelaskan field yang tidak jelas dari namanya.
3. **Jangan mengulang tipe** (`@param id - string id`). TypeScript sudah menyatakannya; jelaskan
   **makna**, unit (ms, µV²/Hz, detik), dan batasan.
4. **`@returns`** wajib bila mengembalikan nilai non-`void` pada fungsi lib/hook.
   Komponen React **tidak** perlu `@returns`.
5. **`@throws`** bila fungsi melempar error secara eksplisit.
6. **`@default`** pada prop/opsi opsional yang memiliki nilai default tidak intuitif.
7. **`@example`** hanya untuk hook/utilitas yang pemakaiannya tidak langsung jelas.
8. **`@remarks`** untuk "mengapa": workaround, side effect (listener, timer, WebSocket),
   kebutuhan cleanup, atau syarat (harus di dalam `ToastProvider`).
9. Field interface yang jelas dari namanya (`id`, `name`, `created_at`, `isOpen`, `onClose`, `className`, `disabled`, `children`) **DILARANG** didokumentasikan (noise).
10. Tag yang tidak relevan dihilangkan; jangan menulis "Tidak ada".
11. Fungsi sederhana cukup TSDoc satu baris: `/** Konversi durasi detik ke format mm:ss. */`.

### Gaya Bahasa
- Bahasa Indonesia baku, kalimat aktif, ringkas.
- Istilah teknis lazim boleh Inggris (*hook*, *props*, *render*, *WebSocket*, *payload*, *debounce*).
- Identifier ditulis dengan backtick tunggal: `session_id`, `useToast`.
- Rujuk simbol lain dengan `{@link NamaSimbol}`.
- Panjang baris ±100 karakter.

## Larangan
- Jangan mengubah logika, nama, signature, import, urutan, atau format kode.
- Jangan menambah `any`, `@ts-ignore`, atau `eslint-disable` baru.
- Jangan menulis TSDoc generik ("Komponen untuk menampilkan data.") — sebutkan data apa,
  untuk siapa, dan perilaku pentingnya.
- Jangan mendokumentasi setiap helper lokal/handler inline (noise).
- Dilarang membuat komentar banner / strip pembatas seksi (`// -----`, `// =====`, `// --- JUDUL ---`).
- Jangan menghapus direktif tooling atau komentar lisensi.
- Jangan memanipulasi test atau konfigurasi lint/tsconfig agar verifikasi lolos.

