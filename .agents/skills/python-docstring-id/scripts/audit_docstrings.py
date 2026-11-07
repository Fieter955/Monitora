"""Mengaudit kelengkapan docstring Google style berbahasa Indonesia.

Skrip ini memeriksa docstring modul, class, fungsi, dan method, lalu
melaporkan elemen yang belum memiliki docstring atau belum memuat section
``Args:``, ``Returns:``/``Yields:``, maupun ``Raises:`` sesuai isi fungsinya.
Skrip juga memberi peringatan heuristik untuk docstring yang tampak masih
berbahasa Inggris.

Contoh penggunaan:
    python audit_docstrings.py backend
    python audit_docstrings.py backend/api/routes --summary
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

from strip_comments import DEFAULT_EXCLUDES, collect_python_files

ENGLISH_HINTS = re.compile(
    r"\b(the|returns?|this|function|given|which|should|args?:\s*$|if the|of the|for the)\b",
    re.IGNORECASE,
)
IGNORED_PARAMS = {"self", "cls"}


def function_params(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    """Mengambil nama parameter fungsi yang wajib didokumentasikan.

    Args:
        node: Node AST fungsi atau method.

    Returns:
        Daftar nama parameter, tidak termasuk ``self`` dan ``cls``.
    """
    args = node.args
    names = [a.arg for a in args.posonlyargs + args.args + args.kwonlyargs]
    if args.vararg:
        names.append(args.vararg.arg)
    if args.kwarg:
        names.append(args.kwarg.arg)
    return [name for name in names if name not in IGNORED_PARAMS]


def own_body_nodes(node: ast.AST):
    """Menelusuri node di dalam fungsi tanpa masuk ke fungsi/class bersarang.

    Args:
        node: Node AST fungsi yang akan ditelusuri.

    Yields:
        Setiap node turunan milik fungsi tersebut secara langsung.
    """
    stack = list(ast.iter_child_nodes(node))
    while stack:
        child = stack.pop()
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        yield child
        stack.extend(ast.iter_child_nodes(child))


def check_function(node: ast.FunctionDef | ast.AsyncFunctionDef, doc: str) -> list[str]:
    """Memeriksa kelengkapan section docstring pada sebuah fungsi.

    Args:
        node: Node AST fungsi atau method.
        doc: Isi docstring fungsi tersebut.

    Returns:
        Daftar pesan masalah; kosong jika docstring sudah lengkap.
    """
    issues: list[str] = []
    body = list(own_body_nodes(node))
    params = function_params(node)

    if params and "Args:" not in doc:
        issues.append("tidak ada section Args:")
    for name in params:
        if "Args:" in doc and not re.search(rf"^\s*\*{{0,2}}{re.escape(name)}\b", doc, re.MULTILINE):
            issues.append(f"parameter '{name}' belum dijelaskan")

    has_yield = any(isinstance(n, (ast.Yield, ast.YieldFrom)) for n in body)
    has_return = any(isinstance(n, ast.Return) and n.value is not None for n in body)
    if has_yield and "Yields:" not in doc:
        issues.append("tidak ada section Yields:")
    elif has_return and not has_yield and "Returns:" not in doc:
        issues.append("tidak ada section Returns:")

    has_raise = any(isinstance(n, ast.Raise) and n.exc is not None for n in body)
    if has_raise and "Raises:" not in doc:
        issues.append("tidak ada section Raises:")
    return issues


def audit_file(path: Path) -> list[str]:
    """Mengaudit seluruh docstring dalam satu berkas Python.

    Args:
        path: Lokasi berkas Python yang diaudit.

    Returns:
        Daftar pesan temuan dengan format ``baris: elemen -> masalah``.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    except (SyntaxError, UnicodeDecodeError) as exc:
        return [f"0: <berkas> -> gagal parsing: {exc}"]

    findings: list[str] = []
    module_doc = ast.get_docstring(tree)
    if not module_doc:
        findings.append("1: <modul> -> tidak ada docstring modul")
    elif ENGLISH_HINTS.search(re.sub(r"^\s*(Args|Returns|Yields|Raises|Attributes):\s*$", "", module_doc, flags=re.MULTILINE)):
        findings.append("1: <modul> -> docstring tampak berbahasa Inggris")

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        label = f"{'class' if isinstance(node, ast.ClassDef) else 'def'} {node.name}"
        doc = ast.get_docstring(node)
        if not doc:
            findings.append(f"{node.lineno}: {label} -> tidak ada docstring")
            continue
        doc_clean = re.sub(r"^\s*(Args|Returns|Yields|Raises|Attributes):\s*$", "", doc, flags=re.MULTILINE)
        if ENGLISH_HINTS.search(doc_clean):
            findings.append(f"{node.lineno}: {label} -> docstring tampak berbahasa Inggris")
        if not isinstance(node, ast.ClassDef):
            for issue in check_function(node, doc):
                findings.append(f"{node.lineno}: {label} -> {issue}")
    return sorted(findings, key=lambda item: int(item.split(":", 1)[0]))


def main() -> int:
    """Titik masuk CLI untuk audit docstring.

    Returns:
        Kode keluar proses: ``0`` jika tidak ada temuan, ``1`` jika ada.
    """
    parser = argparse.ArgumentParser(description="Audit docstring Google style berbahasa Indonesia.")
    parser.add_argument("targets", nargs="+", help="Berkas atau direktori target.")
    parser.add_argument("--summary", action="store_true", help="Hanya tampilkan jumlah temuan per berkas.")
    parser.add_argument("--exclude", action="append", default=[], help="Nama direktori tambahan yang dilewati.")
    args = parser.parse_args()

    files = collect_python_files(args.targets, DEFAULT_EXCLUDES | set(args.exclude))
    total = 0
    for file in files:
        findings = audit_file(file)
        if not findings:
            continue
        total += len(findings)
        if args.summary:
            print(f"{len(findings):4d}  {file}")
        else:
            print(f"\n{file}")
            for finding in findings:
                print(f"  {finding}")

    print(f"\nTotal temuan: {total} pada {len(files)} berkas.")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
