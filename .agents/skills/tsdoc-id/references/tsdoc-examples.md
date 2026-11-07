# Contoh TSDoc Indonesia — SI-KONSELING PRO

Semua contoh mengikuti aturan di `SKILL.md`. Tiru gaya, bukan isi.

---

## 1. Custom hook

```ts
/**
 * Mendeteksi apakah keyboard virtual perangkat seluler sedang terbuka.
 *
 * @remarks
 * Deteksi berbasis fokus elemen teks, bukan selisih `visualViewport`, karena di Firefox
 * Android `window.innerHeight` ikut menyusut sehingga selisihnya mendekati nol.
 *
 * @returns `true` bila elemen yang sedang fokus memunculkan keyboard teks.
 */
export function useKeyboardOpen(): boolean { ... }
```

```ts
/**
 * Mengelola koneksi WebSocket sesi konsultasi beserta reconnect otomatis.
 *
 * @remarks
 * Koneksi ditutup saat komponen unmount atau `consultationId` berubah.
 *
 * @param consultationId - ID sesi konsultasi; `null` menunda pembukaan koneksi.
 * @returns Objek berisi `messages` (riwayat pesan), `status` koneksi, dan `sendMessage`.
 *
 * @example
 * ```tsx
 * const { messages, sendMessage } = useConsultationSocket(id);
 * ```
 */
export function useConsultationSocket(consultationId: number | null) { ... }
```

## 2. Utilitas `lib/`

```ts
/**
 * Menjalankan `fetch` dengan percobaan ulang otomatis untuk galat jaringan dan 502/503/504.
 *
 * @remarks
 * Socket keep-alive proxy Next.js ke backend dapat basi setelah server idle sehingga
 * percobaan pertama gagal `ECONNRESET`; percobaan berikutnya memakai socket baru.
 *
 * @param input - URL tujuan permintaan.
 * @returns Respons terakhir yang diterima.
 * @throws Error bila seluruh percobaan gagal atau melewati batas waktu.
 */
export async function fetchWithRetry(input: string, options: FetchWithRetryOptions = {}) { ... }

/** Opsi tambahan {@link fetchWithRetry} di atas `RequestInit` standar. */
export interface FetchWithRetryOptions extends RequestInit {
  /** Jumlah total percobaan, termasuk yang pertama. @default 3 */
  retries?: number;
  /** Jeda dasar antar-percobaan dalam milidetik; naik linear. @default 600 */
  retryDelayMs?: number;
  /** Batas waktu per percobaan dalam milidetik. @default 15000 */
  timeoutMs?: number;
}
```

## 3. Tipe domain (`lib/types.ts`)

```ts
/** Ringkasan hasil analisis EEG mode 2D untuk satu sesi rekaman. */
export interface EEGAnalysisResult {
  id: number;
  /** Rasio daya absolut theta/beta (integral PSD), presisi penuh. */
  theta_beta_ratio: number;
  /** Kategori screening statistik, bukan diagnosis. */
  category: "Hijau" | "Kuning" | "Merah";
  /** Daya absolut theta 4–8 Hz dalam µV². */
  theta_power: number;
  created_at: string;
}
```

`id` dan `created_at` tidak didokumentasi karena jelas dari namanya.

## 4. Komponen bersama + props

```tsx
/** Properti {@link StatCard}. */
export interface StatCardProps {
  label: string;
  value: string | number;
  /** Ikon Lucide di sisi kiri; tidak dirender bila kosong. */
  icon?: LucideIcon;
  /** Varian warna aksen kartu. @default "teal" */
  tone?: "teal" | "red" | "yellow";
}

/** Menampilkan kartu statistik ringkas untuk dashboard Konselor dan Superadmin. */
export function StatCard({ label, value, icon: Icon, tone = "teal" }: StatCardProps) { ... }
```

## 5. Context

```tsx
/**
 * Mengambil fungsi notifikasi toast global.
 *
 * @remarks
 * Wajib dipanggil di dalam `ToastProvider` (sudah dipasang di `app/layout.tsx`).
 *
 * @returns Objek berisi `showToast(message, type)`.
 * @throws Error bila dipanggil di luar `ToastProvider`.
 */
export function useToast() { ... }
```

---

## Komentar inline: sebelum → sesudah

```tsx
// SEBELUM
// set loading
setLoading(true);
// ambil data siswa
const res = await apiClient.get("/students");
// const old = await fetch("/api/old-students");
const d = res.data; // daftar siswa

// SESUDAH
setLoading(true);
const res = await apiClient.get("/students");
const d = res.data;
```
Laporkan `d` sebagai saran rename `/clean-code` (mis. `students`); jangan rename tanpa persetujuan.

```tsx
// DIPERTAHANKAN — menjelaskan "mengapa"
// Safari iOS menolak autoplay audio tanpa gesture; mulai stream setelah klik pertama.
audioRef.current?.play();

// eslint-disable-next-line react-hooks/exhaustive-deps   ← direktif tooling, jangan disentuh
```

## Anti-pola

```ts
/** Fungsi untuk memproses data. */                 // generik, tidak informatif
/** @param id - string */                           // mengulang tipe
/** Hook ini digunakan untuk socket. */             // diawali "Hook ini"
/** Fetches the student list. */                    // bahasa Inggris
/** Handler klik tombol simpan. */                  // handler inline lokal: tidak perlu TSDoc
```

