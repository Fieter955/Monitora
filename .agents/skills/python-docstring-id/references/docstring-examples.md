# Contoh Docstring Google Style (Bahasa Indonesia)

Gunakan contoh berikut sebagai acuan nada dan struktur. Bahasa formal, baku,
kalimat aktif, tanpa basa-basi.

## 1. Docstring Modul

```python
"""Endpoint API untuk fitur chat konseling berbasis AI.

Modul ini menyediakan rute untuk membuat dan menutup sesi chat, mengirim
pesan ke chatbot, mengambil riwayat percakapan, serta layanan suara
(text-to-speech, speech-to-text, dan realtime WebRTC).
"""
```

## 2. Endpoint FastAPI (Route)

Parameter yang berasal dari `Depends(...)` tetap dijelaskan secara singkat.
Section `Raises:` mencantumkan `HTTPException` beserta kode status dan kondisinya.

```python
@router.get("/voice/status")
def get_voice_status(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Mengecek ketersediaan fitur suara AI untuk pengguna yang sedang login.

    Memeriksa apakah fitur AI aktif, apakah layanan TTS legacy telah
    dikonfigurasi, dan apakah pengguna memenuhi syarat untuk mode suara
    realtime berbasis WebRTC.

    Args:
        db: Sesi database SQLAlchemy yang disuntikkan oleh FastAPI.
        current_user: Pengguna terautentikasi yang melakukan permintaan.

    Returns:
        Dictionary berisi status ketersediaan suara, antara lain
        ``legacy_available``, ``realtime_available``, dan ``model``.

    Raises:
        HTTPException: 403 jika peran pengguna bukan siswa, konselor,
            atau superadmin.
    """
```

## 3. Fungsi Logika / Service

```python
def create_new_session_for_student(db: Session, student: models.Student) -> models.ChatSession:
    """Membuat sesi chat baru untuk siswa dan menutup sesi aktif sebelumnya.

    Args:
        db: Sesi database SQLAlchemy aktif.
        student: Objek siswa pemilik sesi chat.

    Returns:
        Objek ``ChatSession`` yang baru dibuat dan telah disimpan ke database.

    Raises:
        ValueError: Jika siswa tidak memiliki persetujuan (consent) yang valid.
    """
```

## 4. Generator / Streaming

```python
def stream_speech(text: str, voice: str):
    """Mengalirkan audio hasil sintesis suara secara bertahap.

    Args:
        text: Teks yang akan diubah menjadi suara.
        voice: Identitas suara yang digunakan oleh penyedia TTS.

    Yields:
        Potongan data audio (``bytes``) dalam format MP3.

    Raises:
        TTSContentTooLong: Jika panjang teks melebihi batas maksimum.
        TTSProviderError: Jika penyedia TTS mengembalikan galat.
    """
```

## 5. Fungsi Tanpa Parameter / Tanpa Nilai Balik

Section yang tidak relevan **dihilangkan**, jangan ditulis "Tidak ada".

```python
def init_scheduler() -> None:
    """Menginisialisasi dan menjalankan penjadwal tugas latar belakang aplikasi."""
```

## 6. Class (Model SQLAlchemy / Schema Pydantic / Service)

```python
class ChatSession(Base):
    """Representasi tabel ``chat_sessions`` untuk menyimpan sesi chat siswa.

    Attributes:
        id: Primary key sesi chat.
        student_id: Foreign key ke tabel siswa pemilik sesi.
        title: Judul sesi yang dibuat otomatis dari pesan pertama.
        is_active: Penanda apakah sesi masih berlangsung.
        created_at: Waktu pembuatan sesi.
    """
```

```python
class ChatRequest(BaseModel):
    """Skema payload permintaan untuk mengirim pesan ke chatbot.

    Attributes:
        message: Isi pesan yang dikirim siswa.
        session_id: ID sesi chat tujuan; opsional untuk sesi baru.
    """
```

## 7. Method di Dalam Class

```python
    def generate_reply(self, history: list[dict], message: str) -> str:
        """Menghasilkan balasan chatbot berdasarkan riwayat percakapan.

        Args:
            history: Daftar pesan sebelumnya dengan kunci ``role`` dan ``content``.
            message: Pesan terbaru dari siswa.

        Returns:
            Teks balasan yang dihasilkan model AI.
        """
```

## Kosakata Baku yang Disarankan

| Hindari            | Gunakan                         |
| :----------------- | :------------------------------ |
| Fungsi ini buat... | (langsung kata kerja) Membuat…  |
| ngambil, nge-get   | Mengambil                       |
| ngecek             | Memeriksa / Mengecek            |
| return-nya         | Mengembalikan                   |
| error              | galat / kesalahan (boleh tetap `error` untuk nama tipe) |
| user               | pengguna                        |
| di-handle          | ditangani                       |
| payload            | payload (istilah teknis boleh)  |
