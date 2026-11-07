"""Menghapus seluruh komentar ``#`` dari berkas Python secara aman.

Skrip ini memakai modul ``tokenize`` sehingga karakter ``#`` yang berada di
dalam string (misalnya ``"#FF0000"``) atau docstring tidak ikut terhapus.
Setiap berkas hasil modifikasi diverifikasi ulang dengan membandingkan AST
sebelum dan sesudah; bila berbeda, berkas tidak ditulis.

Contoh penggunaan:
    python strip_comments.py backend --dry-run
    python strip_comments.py backend
    python strip_comments.py backend/api/routes/chat.py
"""

from __future__ import annotations

import argparse
import ast
import io
import sys
import tokenize
from pathlib import Path

DEFAULT_EXCLUDES = {
    "venv",
    ".venv",
    "env",
    "__pycache__",
    "node_modules",
    "site-packages",
    ".git",
    ".pytest_cache",
    ".mypy_cache",
}


def collect_python_files(targets: list[str], excludes: set[str]) -> list[Path]:
    """Mengumpulkan daftar berkas ``.py`` dari path target.

    Args:
        targets: Daftar path berkas atau direktori yang akan dipindai.
        excludes: Nama direktori yang dilewati saat pemindaian rekursif.

    Returns:
        Daftar ``Path`` berkas Python yang terurut dan tanpa duplikasi.
    """
    files: set[Path] = set()
    for target in targets:
        path = Path(target)
        if path.is_file() and path.suffix == ".py":
            files.add(path.resolve())
        elif path.is_dir():
            for file in path.rglob("*.py"):
                if not any(part in excludes for part in file.parts):
                    files.add(file.resolve())
    return sorted(files)


def strip_comments(source: str) -> tuple[str, int]:
    """Menghapus seluruh token komentar dari kode sumber Python.

    Baris yang hanya berisi komentar dihapus seluruhnya, sedangkan komentar
    di akhir baris kode (inline) dipotong beserta spasi sebelumnya.

    Args:
        source: Isi lengkap berkas Python dalam bentuk string.

    Returns:
        Tuple berisi kode sumber baru dan jumlah komentar yang dihapus.

    Raises:
        tokenize.TokenError: Jika kode sumber tidak dapat ditokenisasi.
    """
    lines = io.StringIO(source).readlines()
    comment_cols: dict[int, int] = {}
    tokens = tokenize.generate_tokens(io.StringIO(source).readline)
    for tok in tokens:
        if tok.type == tokenize.COMMENT:
            comment_cols[tok.start[0]] = tok.start[1]

    if not comment_cols:
        return source, 0

    result: list[str] = []
    for index, line in enumerate(lines, start=1):
        col = comment_cols.get(index)
        if col is None:
            result.append(line)
            continue
        ending = "\r\n" if line.endswith("\r\n") else ("\n" if line.endswith("\n") else "")
        prefix = line[:col]
        if prefix.strip() == "":
            continue
        result.append(prefix.rstrip() + ending)

    return "".join(result), len(comment_cols)


def process_file(path: Path, dry_run: bool) -> tuple[int, str | None]:
    """Memproses satu berkas: menghapus komentar lalu memverifikasi AST.

    Args:
        path: Lokasi berkas Python yang akan diproses.
        dry_run: Jika ``True``, berkas tidak ditulis ulang.

    Returns:
        Tuple berisi jumlah komentar yang dihapus dan pesan galat
        (``None`` bila berhasil).
    """
    raw = path.read_bytes()
    bom = b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b""
    try:
        source = raw[len(bom):].decode("utf-8")
    except UnicodeDecodeError:
        return 0, "bukan berkas UTF-8"

    try:
        original_ast = ast.dump(ast.parse(source))
        new_source, removed = strip_comments(source)
        new_ast = ast.dump(ast.parse(new_source))
    except (SyntaxError, tokenize.TokenError) as exc:
        return 0, f"gagal parsing: {exc}"

    if original_ast != new_ast:
        return 0, "AST berubah setelah penghapusan, berkas dilewati"

    if removed and not dry_run:
        path.write_bytes(bom + new_source.encode("utf-8"))
    return removed, None


def main() -> int:
    """Titik masuk CLI untuk menghapus komentar dari berkas target.

    Returns:
        Kode keluar proses: ``0`` jika semua berkas berhasil, ``1`` jika ada
        berkas yang gagal diproses.
    """
    parser = argparse.ArgumentParser(description="Hapus semua komentar # dari berkas Python.")
    parser.add_argument("targets", nargs="+", help="Berkas atau direktori target.")
    parser.add_argument("--dry-run", action="store_true", help="Tampilkan hasil tanpa menulis berkas.")
    parser.add_argument("--exclude", action="append", default=[], help="Nama direktori tambahan yang dilewati.")
    args = parser.parse_args()

    excludes = DEFAULT_EXCLUDES | set(args.exclude)
    files = collect_python_files(args.targets, excludes)
    total_removed = 0
    failures = 0

    for file in files:
        removed, error = process_file(file, args.dry_run)
        if error:
            failures += 1
            print(f"[GAGAL] {file}: {error}")
        elif removed:
            total_removed += removed
            print(f"[{'DRY' if args.dry_run else 'OK'}] {file}: {removed} komentar")

    mode = "akan dihapus" if args.dry_run else "dihapus"
    print(f"\nTotal: {total_removed} komentar {mode} dari {len(files)} berkas. Gagal: {failures}.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
