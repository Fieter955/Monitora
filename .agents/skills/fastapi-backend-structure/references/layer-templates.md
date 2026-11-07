# Template & Pola Kode Standar per Layer

Dokumen referensi ini berisi pola implementasi standar untuk setiap layer pada struktur backend FastAPI. Gunakan pola ini saat memigrasikan atau merombak kode lama.

---

## 1. Layer `core/`

### `core/config.py`
Menggunakan `pydantic_settings.BaseSettings` untuk memuat variabel dari `.env`:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    ALGORITHM: str
    SECRET_KEY: str
    EXPIRED_TOKEN_ACCESS_MINUTES: int
    ALLOWED_HOST: list[str]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
```

### `core/exceptions.py` (atau `core/exception.py`)
Hierarki `DomainException` murni Python (tanpa ketergantungan pada `fastapi.HTTPException`):
```python
class DomainException(Exception):
    pass


class DuplicateDataError(DomainException):
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class InvalidArgumentError(DomainException):
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class NotFoundError(DomainException):
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class InvalidCredentialsError(DomainException):
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class UnAuthorizedError(DomainException):
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class ForbiddenError(DomainException):
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)
```

### `core/security.py`
Menangani hashing password dan pembuatan/verifikasi token JWT:
```python
from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash

from core.config import settings

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(data: dict, expired_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expired_delta or timedelta(minutes=settings.EXPIRED_TOKEN_ACCESS_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        settings.ALGORITHM,
    )


def decode_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )
```

---

## 2. Layer `db/`

### `db/base.py`
Hanya berisi deklarasi `Base` SQLAlchemy:
```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

### `db/session.py`
Berisi koneksi `engine` dan pembuatan session database:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)
```

---

## 3. Layer `models/`

### `models/user.py`
Hanya berisi definisi tabel SQLAlchemy (`Base` di-import dari `db.base`):
```python
from sqlalchemy import Column, Integer, String

from db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(256), unique=True, nullable=False)
    password = Column(String(256), nullable=False)
```

---

## 4. Layer `schemas/`

### `schemas/user.py`
Hanya berisi kontrak data request/response Pydantic:
```python
from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserCreateResponse(BaseModel):
    id: int
    name: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)
```

### `schemas/auth.py`
```python
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayLoad(BaseModel):
    sub: str | None = None
```

---

## 5. Layer `services/`

### `services/user.py`
Berisi seluruh query DB, aturan validasi bisnis, dan melempar `DomainException` (bukan `HTTPException`):
```python
from sqlalchemy.orm import Session

from core.exceptions import DuplicateDataError, NotFoundError
from core.security import hash_password
from models.user import User
from schemas.user import UserCreate


def get_user(email: str, db: Session) -> User | None:
    return db.query(User).filter(User.email == email).first()


def is_email_registered(email: str, db: Session) -> bool:
    return get_user(email, db) is not None


def create_user(data: UserCreate, db: Session) -> User:
    if is_email_registered(data.email, db):
        raise DuplicateDataError("Email sudah terdaftar")

    user = User(
        name=data.name,
        email=data.email,
        password=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
```

---

## 6. Layer `api/`

### `api/deps.py`
Menyediakan dependency FastAPI (`get_db`, `oauth2_scheme`, `get_current_user`, `require_admin`):

> [!IMPORTANT]
> **Larangan Type Alias `Annotated`**: Dilarang membuat alias seperti `DbSession = Annotated[Session, Depends(get_db)]` atau `CurrentUser = Annotated[User, Depends(get_current_user)]`. Seluruh endpoint harus memanggil `Depends(...)` secara eksplisit pada parameternya.

```python
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.orm import Session

from core.exceptions import ForbiddenError, UnAuthorizedError
from core.security import decode_token
from db.session import SessionLocal
from models.user import User
from services.user import get_user


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_token(token)
        email: str | None = payload.get("sub")
        if email is None:
            raise UnAuthorizedError("Token tidak valid")
    except jwt.PyJWTError:
        raise UnAuthorizedError("Token tidak valid")

    current_user: User | None = get_user(email, db)
    if current_user is None:
        raise UnAuthorizedError("Pengguna tidak ditemukan")

    return current_user


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "admin":
        raise ForbiddenError("Akses administrator diperlukan")
    return current_user
```

### `api/routes/user.py`
Router tipis — tidak ada `db.query(...)` atau `db.commit()` langsung di sini:
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from models.user import User
from schemas.user import UserCreate, UserCreateResponse
from services.user import create_user

router = APIRouter(prefix="/user", tags=["users"])


@router.post("/", response_model=UserCreateResponse)
def create_user_api(
    data: UserCreate,
    db: Session = Depends(get_db),
):
    return create_user(data, db)


@router.get("/me", response_model=UserCreateResponse)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user
```

### `api/routes/auth.py` (Contoh Router Publik & Sub-Router Internal)
```python
from fastapi import APIRouter, Depends, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db, require_admin
from core.exceptions import InvalidCredentialsError
from core.security import create_access_token, verify_password
from models.user import User
from schemas.auth import Token
from services.user import get_user

router = APIRouter(prefix="/auth", tags=["auth"])
internal_router = APIRouter(
    prefix="/internal/auth", tags=["internal"], include_in_schema=False
)


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user: User | None = get_user(form_data.username, db)
    if user is None or not verify_password(form_data.password, user.password):
        raise InvalidCredentialsError("Email atau password salah")

    token: str = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


# Endpoint subrequest internal (reverse-proxy auth_request) didekorasi dengan internal_router
@internal_router.get("/admin")
def authorize_admin(_: User = Depends(require_admin)) -> Response:
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@internal_router.get("/session")
def authorize_session(_: User = Depends(get_current_user)) -> Response:
    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

> [!NOTE]
> **Endpoint Internal & Discovery**: Jangan pernah mendeklarasikan fungsi handler polos tanpa dekorator lalu mendaftarkannya dengan `app.add_api_route` di `main.py`. Gunakan `internal_router = APIRouter(..., include_in_schema=False)` dan daftarkan via `app.include_router(...)`.

---

## 7. Entry Point `main.py`

Menggabungkan `lifespan`, middleware, `@app.exception_handler(...)` untuk seluruh subclass `DomainException`, dan `app.include_router(...)`:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from api.routes.auth import router as auth_router
from api.routes.user import router as user_router
from core.config import settings
from core.exceptions import (
    DuplicateDataError,
    ForbiddenError,
    InvalidArgumentError,
    InvalidCredentialsError,
    NotFoundError,
    UnAuthorizedError,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("memulai aplikasi")
    yield
    print("menutup aplikasi")


app = FastAPI(
    title="Backend API",
    description="Aplikasi Backend FastAPI",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOST,
)


@app.exception_handler(DuplicateDataError)
def duplicate_data_error_handler(request: Request, exc: DuplicateDataError):
    return JSONResponse(
        status_code=409,
        content={"detail": exc.detail},
    )


@app.exception_handler(InvalidArgumentError)
def invalid_argument_error_handler(request: Request, exc: InvalidArgumentError):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.detail},
    )


@app.exception_handler(NotFoundError)
def not_found_error_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": exc.detail},
    )


@app.exception_handler(InvalidCredentialsError)
def invalid_credentials_error_handler(request: Request, exc: InvalidCredentialsError):
    return JSONResponse(
        status_code=401,
        headers={"WWW-Authenticate": "Bearer"},
        content={"detail": exc.detail},
    )


@app.exception_handler(UnAuthorizedError)
def un_authorized_error_handler(request: Request, exc: UnAuthorizedError):
    return JSONResponse(
        status_code=401,
        headers={"WWW-Authenticate": "Bearer"},
        content={"detail": exc.detail},
    )


@app.exception_handler(ForbiddenError)
def forbidden_error_handler(request: Request, exc: ForbiddenError):
    return JSONResponse(
        status_code=403,
        content={"detail": exc.detail},
    )


app.include_router(user_router)
app.include_router(auth_router)
app.include_router(auth.internal_router)
```

> [!WARNING]
> **Dilarang keras memakai `app.add_api_route(...)`**. Seluruh rute (publik maupun internal reverse-proxy/discovery) wajib dikelompokkan ke dalam `APIRouter` dan didaftarkan dengan `app.include_router(...)`.

