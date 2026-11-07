class DomainException(Exception):
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class DuplicateDataError(DomainException):
    """409 Conflict — Data unik sudah terdaftar."""
    pass


class ConflictError(DomainException):
    """409 Conflict — Konflik dengan status entitas lain saat ini."""
    pass


class InvalidArgumentError(DomainException):
    """400 Bad Request — Argumen/input bisnis tidak valid."""
    pass


class NotFoundError(DomainException):
    """404 Not Found — Entitas/data yang dicari tidak ditemukan."""
    pass


class InvalidCredentialsError(DomainException):
    """401 Unauthorized — Kredensial login salah."""
    pass


class UnAuthorizedError(DomainException):
    """401 Unauthorized — Sesi tidak valid, token tidak valid, atau belum login."""
    pass


class ForbiddenError(DomainException):
    """403 Forbidden — Pengguna terautentikasi tetapi tidak punya hak akses."""
    pass


class UnprocessableEntityError(DomainException):
    """422 Unprocessable Entity — Validasi semantik bisnis gagal."""
    pass


class UnsupportedMediaTypeError(DomainException):
    """415 Unsupported Media Type — Format file tidak didukung."""
    pass


class PayloadTooLargeError(DomainException):
    """413 Payload Too Large — Ukuran file melebihi batas maksimal."""
    pass


class TooManyRequestsError(DomainException):
    """429 Too Many Requests — Terlalu banyak permintaan atau percobaan login gagal."""
    pass


class ServiceUnavailableError(DomainException):
    """503 Service Unavailable — Layanan pihak ketiga atau internal tidak tersedia."""
    pass
