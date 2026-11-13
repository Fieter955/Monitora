class DomainException(Exception):
    status_code: int = 500
    code: str = "INTERNAL_ERROR"

    def __init__(self, detail: str, code: str | None = None) -> None:
        self.detail = detail
        self.code = code or type(self).code
        super().__init__(detail)


class DuplicateDataError(DomainException):
    """409 Conflict — Data unik sudah terdaftar."""

    status_code = 409
    code = "DUPLICATE_DATA"


class ConflictError(DomainException):
    """409 Conflict — Konflik dengan status entitas lain saat ini."""

    status_code = 409
    code = "CONFLICT"


class InvalidArgumentError(DomainException):
    """400 Bad Request — Argumen/input bisnis tidak valid."""

    status_code = 400
    code = "INVALID_ARGUMENT"


class NotFoundError(DomainException):
    """404 Not Found — Entitas/data yang dicari tidak ditemukan."""

    status_code = 404
    code = "NOT_FOUND"


class InvalidCredentialsError(DomainException):
    """401 Unauthorized — Kredensial login salah."""

    status_code = 401
    code = "INVALID_CREDENTIALS"


class UnAuthorizedError(DomainException):
    """401 Unauthorized — Sesi tidak valid, token tidak valid, atau belum login."""

    status_code = 401
    code = "UNAUTHORIZED"


class ForbiddenError(DomainException):
    """403 Forbidden — Pengguna terautentikasi tetapi tidak punya hak akses."""

    status_code = 403
    code = "FORBIDDEN"


class UnprocessableEntityError(DomainException):
    """422 Unprocessable Entity — Validasi semantik bisnis gagal."""

    status_code = 422
    code = "UNPROCESSABLE_ENTITY"


class UnsupportedMediaTypeError(DomainException):
    """415 Unsupported Media Type — Format file tidak didukung."""

    status_code = 415
    code = "UNSUPPORTED_MEDIA_TYPE"


class PayloadTooLargeError(DomainException):
    """413 Payload Too Large — Ukuran file melebihi batas maksimal."""

    status_code = 413
    code = "PAYLOAD_TOO_LARGE"


class TooManyRequestsError(DomainException):
    """429 Too Many Requests — Terlalu banyak permintaan atau percobaan login gagal."""

    status_code = 429
    code = "TOO_MANY_REQUESTS"


class ServiceUnavailableError(DomainException):
    """503 Service Unavailable — Layanan pihak ketiga atau internal tidak tersedia."""

    status_code = 503
    code = "SERVICE_UNAVAILABLE"
