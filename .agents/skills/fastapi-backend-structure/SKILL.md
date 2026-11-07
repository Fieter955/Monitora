---
name: fastapi-backend-structure
description: >-
  Restructure and refactor any Python/FastAPI backend codebase into a clean,
  strictly layered directory architecture (core, db, models, schemas, services,
  api, main.py, and optional ai/) with DomainException handling, zero-byte
  __init__.py files, and zero backward-compatibility shims. Use when asked to
  migrate, refactor, standardize, or audit backend folder structure following
  dokumentasi.md conventions.
---

# FastAPI Backend Layered Structure Refactoring

Skill ini merombak dan menstandarisasi kode backend Python/FastAPI apa pun agar mengikuti arsitektur berlapis (*layered architecture*) yang bersih dan ketat sesuai standar proyek pada `dokumentasi.md` — berlaku untuk aplikasi backend umum (CRUD, REST API, microservice) maupun aplikasi berbasis AI.

---

## 1. Aturan Mutlak (Wajib Dipatuhi Tanpa Kompromi)

### A. Larangan Keras "Main Aman" (Zero Legacy & Zero Shim Policy)
Saat memindahkan kode ke struktur baru, **DILARANG KERAS**:
1. **Mengisi `__init__.py`**: Seluruh file `__init__.py` di setiap paket (`api/`, `api/routes/`, `core/`, `db/`, `models/`, `schemas/`, `services/`, `ai/`) **wajib kosong total (0 baris / 0 byte)**.
2. **Memakai `__all__` atau Barrel Export**: Dilarang menulis `__all__ = [...]` atau meng-import modul/class ke dalam `__init__.py` agar bisa dipanggil singkat (`from models import User` -> **DILARANG**).
3. **Menyisakan Variabel/Fungsi/Re-export Lama**: Saat memindahkan fungsi, class, atau variabel ke file baru, **hapus tuntas** dari file asalnya. Dilarang meninggalkan alias atau re-export di file lama hanya demi mencegah `ImportError` di tempat lain.
4. **Saling Import Silang (Circular / Cross Re-import)**: Setiap simbol hanya boleh didefinisikan di satu tempat (*Single Source of Truth*) dan di-import langsung dari modul spesifiknya.
5. **Menyertakan Prefix Nama Folder Root**: Semua import internal wajib relatif terhadap root backend secara langsung (contoh: `from schemas.user import UserCreate`, **bukan** `from latian2.schemas.user import UserCreate` atau `from backend.schemas.user import UserCreate`).
6. **Menyisakan File/Folder Lama**: Setelah isi file lama dimigrasikan dan seluruh *call site* (termasuk `tests/` dan `alembic/`) diperbarui, file/folder lama **wajib dihapus**.

### B. Aliran Dependensi Satu Arah (Strict Top-Down Layering)
Arah import **hanya boleh mengalir dari atas ke bawah** dan tidak boleh melompat balik ke atas:

```text
core (config, security, exceptions)
  ↓
db (base, session)
  ↓
models
  ↓
schemas
  ↓
services (+ ai/ opsional bila memakai LLM/RAG/embedding)
  ↓
api (deps, routes)
  ↓
main.py
```

| Layer | Boleh Import Dari | DILARANG Import Dari |
| :--- | :--- | :--- |
| `core/` | Library standar / pihak ketiga, sesama `core/` (`config` -> `security`) | `db`, `models`, `schemas`, `services`, `ai`, `api`, `main` |
| `db/` | `core.config`, SQLAlchemy | `models`*, `schemas`, `services`, `ai`, `api`, `main` |
| `models/` | `db.base`, SQLAlchemy | `schemas`, `services`, `ai`, `api`, `main` |
| `schemas/` | Pydantic, tipe standar | `db`, `models`, `services`, `ai`, `api`, `main` |
| `services/` | `core`, `db`, `models`, `schemas`, `ai` (jika ada) | `api` (`deps`, `routes`), `main`, `fastapi.HTTPException` |
| `ai/` (opsional) | `core`, `schemas`, SDK AI/LLM | `api`, `main`, `fastapi.HTTPException` |
| `api/deps.py` | `core`, `db.session`, `models`, `schemas`, `services` | `api.routes`, `main` |
| `api/routes/` | `core`, `schemas`, `services`, `models` (hanya type hint), `api.deps` | Operasi DB langsung (`db.query`, `db.add`, `db.commit`), `main` |
| `main.py` | `core.config`, `core.exceptions`, `api.routes.*` | Operasi bisnis atau query DB langsung |

*\*Catatan Alembic: Hanya jika proyek menggunakan Alembic, registrasi metadata model dilakukan di `alembic/env.py`, bukan dengan menumpuk re-export di `models/__init__.py`.*

### C. Larangan Penggunaan Type Alias `Annotated` untuk Dependency Injection
Dependency Injection pada endpoint FastAPI **wajib eksplisit** menggunakan `Depends(...)`:
1. **Dilarang Membungkus `Depends(...)` ke dalam Type Alias `Annotated`**: Dilarang membuat alias seperti `DbSession = Annotated[Session, Depends(get_db)]`, `CurrentUser = Annotated[User, Depends(get_current_user)]`, atau `AdminUser = Annotated[User, Depends(require_admin)]`.
2. **Semua Endpoint Wajib Menampilkan Pemanggilan `Depends(...)` Secara Terbuka**: Parameter handler endpoint wajib secara eksplisit menyatakan pemanggilan dependency, contohnya:
   - `db: Session = Depends(get_db)`
   - `current_user: User = Depends(get_current_user)`
   - `_: User = Depends(require_admin)`
3. **Prinsip**: *Explicit is better than implicit*. Setiap developer dan auditor kode harus dapat langsung membaca ketergantungan (dependencies) fungsi endpoint dari signature-nya tanpa harus menelusuri alias tipe di file terpisah.

### D. Larangan Handler Route Polos & Pendaftaran Manual `app.add_api_route`
Semua fungsi penanganan request HTTP di dalam `api/routes/` **wajib terdaftar melalui `APIRouter`**:
1. **Dilarang Mendeklarasikan Fungsi Route Polos (Bare Functions)**: Seluruh fungsi di `api/routes/` yang bertindak sebagai route handler wajib didekorasi dengan router (misalnya `@router.get(...)`, `@router.post(...)`, dsb.).
2. **Endpoint Khusus/Internal Wajib Menggunakan Sub-Router**: Untuk endpoint reverse-proxy subrequest (seperti Nginx `auth_request`), Prometheus discovery/metrics, atau endpoint internal lainnya yang tidak boleh muncul di OpenAPI/Swagger:
   - Buat sub-router khusus di modul route terkait:
     ```python
     internal_router = APIRouter(prefix="/internal/...", tags=["internal"], include_in_schema=False)
     ```
   - Dekorasi handler fungsi dengan sub-router tersebut (misalnya `@internal_router.get(...)`).
3. **Dilarang Menggunakan `app.add_api_route` di `main.py`**: Di `main.py`, selalu gunakan `app.include_router(...)` untuk mendaftarkan seluruh router (baik router publik maupun `internal_router`). Dilarang mendaftarkan route satu per satu secara manual dengan `app.add_api_route(...)`.
4. **Larangan Fungsi Non-Endpoint di `api/routes/`**: File di dalam `api/routes/` **HANYA** boleh berisi fungsi handler endpoint yang terdaftar pada router. Dilarang menaruh fungsi pembantu/helper, kalkulasi bisnis, atau fungsi dependensi di dalam file routes. Jika fungsinya bukan endpoint router:
   - **Logika Bisnis / Query Database / Manipulasi Data**: Wajib dipindahkan ke `services/<domain>.py`.
   - **Injeksi Dependensi / Generator / Validasi Token (`Depends`)**: Wajib dipindahkan ke `api/deps.py`.
   - **Utilitas Umum / Helper Murni**: Wajib dipindahkan ke `core/` (misalnya `core/utils.py`).

---

## 2. Target Struktur Direktori Backend

Semua modul diletakkan langsung di bawah root direktori backend (misalnya `backend/` atau folder kerja backend target):

```text
<backend_root>/
├── main.py                  # Inisialisasi FastAPI, lifespan, middleware, exception handlers, include_router
├── api/
│   ├── __init__.py          # WAJIB KOSONG (0 byte)
│   ├── deps.py              # Dependency injection: get_db, oauth2_scheme, get_current_user
│   └── routes/
│       ├── __init__.py      # WAJIB KOSONG (0 byte)
│       ├── auth.py          # Endpoint autentikasi (/auth/...)
│       ├── user.py          # Endpoint user (/user/...)
│       └── <domain>.py      # Endpoint domain lainnya
├── core/
│   ├── __init__.py          # WAJIB KOSONG (0 byte)
│   ├── config.py            # Pydantic BaseSettings & instansiasi `settings`
│   ├── security.py          # Hashing password (pwdlib/argon2) & JWT encode/decode
│   └── exceptions.py        # Hierarki DomainException (tanpa HTTPException)
├── db/
│   ├── __init__.py          # WAJIB KOSONG (0 byte)
│   ├── base.py              # SQLAlchemy DeclarativeBase (`class Base(DeclarativeBase)`)
│   └── session.py           # Engine (`create_engine`) & session factory (`sessionmaker` / `SessionLocal`)
├── models/
│   ├── __init__.py          # WAJIB KOSONG (0 byte)
│   └── <domain>.py          # Representasi tabel SQLAlchemy (mis. user.py)
├── schemas/
│   ├── __init__.py          # WAJIB KOSONG (0 byte)
│   ├── auth.py              # Pydantic schema untuk Token & TokenPayload
│   └── <domain>.py          # Pydantic schema request/response (Create, Update, Response)
├── services/
│   ├── __init__.py          # WAJIB KOSONG (0 byte)
│   └── <domain>.py          # Logika bisnis, validasi domain, & query database
├── ai/                      # OPSIONAL: HANYA dibuat jika aplikasi memakai LLM/RAG/embeddings!
│   ├── __init__.py          # WAJIB KOSONG (0 byte)
│   ├── llm.py
│   ├── prompts.py
│   ├── embeddings.py
│   └── rag.py
├── tests/                   # Pengujian otomatis (pytest)
├── Dockerfile
└── .env
```

> **Aturan Folder `ai/`**: Jangan pernah membuat folder `ai/` pada aplikasi backend general (e-commerce, manajemen user, keuangan, inventori, dll.) yang tidak memiliki fitur AI. Buat folder `ai/` **hanya** jika kode sumber benar-benar memanggil LLM, prompt template, vector embeddings, atau RAG.

---

## 3. Standar `DomainException` & Exception Handler

Service dan dependency **dilarang** melempar `fastapi.HTTPException`. Semua error domain didefinisikan di `core/exceptions.py` (atau `core/exception.py` jika proyek sudah menamainya demikian, pastikan konsisten) dan dipetakan ke status HTTP di `main.py`:

### Definisi di `core/exceptions.py`
```python
class DomainException(Exception):
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class DuplicateDataError(DomainException):
    """409 Conflict — Data unik (seperti email/username) sudah terdaftar."""
    pass


class InvalidArgumentError(DomainException):
    """400 Bad Request — Argumen/input bisnis tidak valid."""
    pass


class NotFoundError(DomainException):
    """404 Not Found — Entitas/data yang dicari tidak ditemukan."""
    pass


class InvalidCredentialsError(DomainException):
    """401 Unauthorized — Kredensial login (email/password) salah."""
    pass


class UnAuthorizedError(DomainException):
    """401 Unauthorized — Token tidak valid, kedaluwarsa, atau belum login."""
    pass


class ForbiddenError(DomainException):
    """403 Forbidden — Pengguna terautentikasi tetapi tidak punya hak akses."""
    pass
```
*(Boleh menambahkan subclass `DomainException` spesifik lainnya di `core/exceptions.py` hanya jika domain aplikasi membutuhkannya, dan wajib didaftarkan handler-nya di `main.py`).*

### Registrasi Handler di `main.py`
Setiap subclass `DomainException` ditangani dengan `@app.exception_handler(...)` di `main.py` yang mengembalikan `JSONResponse`. Lihat contoh kode lengkap setiap layer di [references/layer-templates.md](./references/layer-templates.md).

---

## 4. Alur Kerja Migrasi & Refactoring (Step-by-Step)

1. **Investigasi & Pemetaan Awal**:
   - Pindai seluruh file di target direktori backend.
   - Identifikasi apakah aplikasi menggunakan komponen AI/LLM (untuk memutuskan perlu tidaknya folder `ai/`).
   - Petakan setiap class, fungsi, konstanta, model DB, schema Pydantic, query DB, dan route ke 6 layer utama (`core`, `db`, `models`, `schemas`, `services`, `api`) + `main.py`.
2. **Baca Template Referensi**:
   - Baca [references/layer-templates.md](./references/layer-templates.md) untuk memastikan gaya penulisan `config.py`, `security.py`, `exceptions.py`, `db/session.py`, `api/deps.py`, `services/`, `routes/`, dan `main.py` seragam.
3. **Bangun Layer dari Atas ke Bawah**:
   - **Tahap 1 (`core/`)**: Pindahkan konfigurasi environment ke `core/config.py`, fungsi hash/JWT ke `core/security.py`, dan buat hierarki `DomainException` di `core/exceptions.py`.
   - **Tahap 2 (`db/`)**: Pindahkan `Base` ke `db/base.py` dan engine/session ke `db/session.py`.
   - **Tahap 3 (`models/`)**: Pecah model SQLAlchemy ke `models/<domain>.py`.
   - **Tahap 4 (`schemas/`)**: Pecah schema Pydantic ke `schemas/<domain>.py` dan `schemas/auth.py`.
   - **Tahap 5 (`services/` & opsional `ai/`)**: Ekstrak seluruh logika bisnis dan operasi database (`db.query`, `db.add`, `db.commit`, `db.refresh`) dari router/controller ke `services/<domain>.py`. Ganti semua `raise HTTPException(...)` dengan subclass `DomainException`.
   - **Tahap 6 (`api/`)**: Pindahkan fungsi generator dependency (`get_db`), skema keamanan (`oauth2_scheme`), dan fungsi verifikasi pengguna/izin (`get_current_user`, `require_admin`) ke `api/deps.py`. **Dilarang membuat type alias `Annotated[..., Depends(...)]`**. Bersihkan `api/routes/<domain>.py` agar setiap fungsi endpoint didekorasi oleh `router` atau `internal_router` dan setiap parameter dependency memanggil `Depends(...)` secara eksplisit (contoh: `db: Session = Depends(get_db)`).
   - **Tahap 7 (`main.py`)**: Rakit `FastAPI(lifespan=...)`, middleware (`TrustedHostMiddleware`, dll.), `@app.exception_handler(...)` untuk seluruh `DomainException`, dan daftarkan seluruh router publik serta internal menggunakan `app.include_router(...)` (**Dilarang menggunakan `app.add_api_route(...)`**).
4. **Pembersihan Total (Zero-Shim Cleanup)**:
   - Pastikan seluruh `__init__.py` berukuran 0 byte.
   - Hapus semua file/folder lama yang sudah dipindahkan.
   - Perbarui semua statement `import` di seluruh proyek (termasuk `tests/` dan `alembic/`) agar langsung mengarah ke modul baru tanpa prefix folder root di luar backend.
5. **Verifikasi Otomatis dengan Script Auditor**:
   - Jalankan script auditor yang disediakan oleh skill ini:
     ```powershell
     python .agents/skills/fastapi-backend-structure/scripts/audit_structure.py <path_ke_backend>
     ```
   - Jalankan kompilasi sintaks Python:
     ```powershell
     python -m compileall -q <path_ke_backend>
     ```
   - Jika script auditor melaporkan pelanggaran (`[FAIL]`), perbaiki hingga 0 pelanggaran sebelum menyelesaikan tugas. Jika ada test suite (`pytest`), jalankan dan pastikan lulus.

