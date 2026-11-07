import ast
import sys
from pathlib import Path

REQUIRED_DIRS = [
    "core",
    "db",
    "models",
    "schemas",
    "services",
    "api",
    "api/routes",
]

ALLOWED_TOP_LEVEL_DIRS = {
    "core",
    "db",
    "models",
    "schemas",
    "services",
    "ai",
    "api",
    "tests",
    "alembic",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
}

LAYER_ORDER = {
    "core": 1,
    "db": 2,
    "models": 3,
    "schemas": 4,
    "ai": 5,
    "services": 6,
    "api": 7,
    "main": 8,
}

INTERNAL_PACKAGES = {"core", "db", "models", "schemas", "services", "ai", "api"}
DB_CALL_METHODS = {"query", "add", "add_all", "commit", "delete", "execute", "scalar", "scalars", "flush", "rollback"}


def get_layer(rel_path: Path) -> str | None:
    parts = rel_path.parts
    if len(parts) == 1 and parts[0] == "main.py":
        return "main"
    if parts and parts[0] in LAYER_ORDER:
        return parts[0]
    return None


def collect_used_names(tree: ast.AST) -> set[str]:
    used: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            used.add(node.id)
    return used


def audit_backend(root: Path) -> list[str]:
    errors: list[str] = []
    root = root.resolve()
    root_name = root.name

    if not (root / "main.py").is_file():
        errors.append("[FAIL] File 'main.py' tidak ditemukan di root backend.")

    for req_dir in REQUIRED_DIRS:
        dir_path = root / req_dir
        if not dir_path.is_dir():
            errors.append(f"[FAIL] Folder wajib '{req_dir}/' belum ada.")
        else:
            init_file = dir_path / "__init__.py"
            if not init_file.is_file():
                errors.append(f"[FAIL] File '{req_dir}/__init__.py' belum ada.")

    for item in root.iterdir():
        if item.is_dir() and not item.name.startswith(".") and item.name not in ALLOWED_TOP_LEVEL_DIRS:
            errors.append(
                f"[FAIL] Folder non-standar '{item.name}/' ditemukan di root backend. "
                f"Pindahkan isinya ke layer yang sesuai lalu hapus folder tersebut."
            )

    for py_file in sorted(root.rglob("*.py")):
        rel_path = py_file.relative_to(root)
        if any(part in {".venv", "venv", "__pycache__", "alembic"} for part in rel_path.parts):
            continue

        content = py_file.read_text(encoding="utf-8", errors="replace")

        if py_file.name == "__init__.py":
            if content.strip():
                errors.append(
                    f"[FAIL] {rel_path}: '__init__.py' WAJIB kosong total (0 baris). "
                    f"Dilarang menaruh re-export, import, atau '__all__'."
                )
            continue

        try:
            tree = ast.parse(content, filename=str(rel_path))
        except SyntaxError as exc:
            errors.append(f"[FAIL] {rel_path}:{exc.lineno}: SyntaxError: {exc.msg}")
            continue

        layer = get_layer(rel_path)
        used_names = collect_used_names(tree)

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        errors.append(
                            f"[FAIL] {rel_path}:{node.lineno}: Penggunaan '__all__' dilarang keras."
                        )
                if isinstance(node.value, ast.Subscript):
                    base_name = ""
                    if isinstance(node.value.value, ast.Name):
                        base_name = node.value.value.id
                    elif isinstance(node.value.value, ast.Attribute):
                        base_name = node.value.value.attr
                    if base_name == "Annotated":
                        slice_nodes = (
                            node.value.slice.elts
                            if isinstance(node.value.slice, ast.Tuple)
                            else [node.value.slice]
                        )
                        has_depends = any(
                            isinstance(s, ast.Call)
                            and (
                                (isinstance(s.func, ast.Name) and s.func.id == "Depends")
                                or (isinstance(s.func, ast.Attribute) and s.func.attr == "Depends")
                            )
                            for s in slice_nodes
                        )
                        if has_depends:
                            errors.append(
                                f"[FAIL] {rel_path}:{node.lineno}: Definisi type alias 'Annotated' dengan 'Depends' dilarang. "
                                f"Gunakan pemanggilan eksplisit '= Depends(...)' langsung pada signature parameter endpoint."
                            )

            if layer == "main" and isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and node.func.attr == "add_api_route":
                    errors.append(
                        f"[FAIL] {rel_path}:{node.lineno}: Pemanggilan 'add_api_route' dilarang. "
                        f"Gunakan APIRouter (mis. 'internal_router = APIRouter(...)') dan daftarkan dengan 'app.include_router(...)'."
                    )

            if isinstance(node, ast.ImportFrom) and node.module:
                mod_parts = node.module.split(".")
                first_part = mod_parts[0]

                if first_part == root_name:
                    errors.append(
                        f"[FAIL] {rel_path}:{node.lineno}: Import menyertakan prefix nama folder root "
                        f"('from {node.module} import ...'). Gunakan 'from {'.'.join(mod_parts[1:])} import ...'."
                    )
                    if len(mod_parts) > 1:
                        mod_parts = mod_parts[1:]
                        first_part = mod_parts[0]

                if first_part in INTERNAL_PACKAGES and len(mod_parts) == 1:
                    errors.append(
                        f"[FAIL] {rel_path}:{node.lineno}: Barrel import 'from {first_part} import ...' dilarang. "
                        f"Import langsung dari file modul spesifiknya (mis. 'from {first_part}.<modul> import ...')."
                    )

                if layer and first_part in LAYER_ORDER:
                    src_rank = LAYER_ORDER[layer]
                    target_rank = LAYER_ORDER[first_part]
                    if target_rank > src_rank:
                        errors.append(
                            f"[FAIL] {rel_path}:{node.lineno}: Pelanggaran arah layer! "
                            f"Layer '{layer}' tidak boleh meng-import dari layer di bawahnya ('{first_part}')."
                        )
                    if layer == "api" and rel_path.name == "deps.py" and node.module.startswith("api.routes"):
                        errors.append(
                            f"[FAIL] {rel_path}:{node.lineno}: 'api/deps.py' tidak boleh meng-import dari 'api.routes'."
                        )

                if layer in {"core", "db", "models", "schemas", "services", "ai"}:
                    for alias in node.names:
                        if alias.name == "HTTPException":
                            errors.append(
                                f"[FAIL] {rel_path}:{node.lineno}: Layer '{layer}' dilarang memakai 'HTTPException'. "
                                f"Gunakan subclass 'DomainException' dari 'core/exceptions.py'."
                            )

                for alias in node.names:
                    if alias.name == "*":
                        errors.append(
                            f"[FAIL] {rel_path}:{node.lineno}: Wildcard import ('import *') dilarang."
                        )
                        continue
                    bound_name = alias.asname or alias.name
                    if bound_name not in used_names:
                        errors.append(
                            f"[FAIL] {rel_path}:{node.lineno}: Unused import / indikasi re-export sisa ('{bound_name}'). "
                            f"Hapus import yang tidak dipakai di file ini."
                        )

            if isinstance(node, ast.Import):
                for alias in node.names:
                    bound_name = alias.asname or alias.name.split(".")[0]
                    if bound_name not in used_names:
                        errors.append(
                            f"[FAIL] {rel_path}:{node.lineno}: Unused import ('{bound_name}'). "
                            f"Hapus import yang tidak dipakai di file ini."
                        )

            if isinstance(node, ast.Call) and rel_path.parts[:2] == ("api", "routes"):
                if isinstance(node.func, ast.Attribute) and node.func.attr in DB_CALL_METHODS:
                    if isinstance(node.func.value, ast.Name) and node.func.value.id in {"db", "session"}:
                        errors.append(
                            f"[FAIL] {rel_path}:{node.lineno}: Operasi database langsung ('{node.func.value.id}.{node.func.attr}()') "
                            f"di dalam router dilarang. Pindahkan ke layer 'services/'."
                        )

        if rel_path.parts[:2] == ("api", "routes") and py_file.name != "__init__.py":
            router_http_methods = {"get", "post", "put", "patch", "delete", "options", "head", "api_route"}
            for item in tree.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not item.name.startswith("_"):
                        has_router = False
                        for dec in item.decorator_list:
                            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                                if dec.func.attr in router_http_methods:
                                    has_router = True
                                    break
                            elif isinstance(dec, ast.Attribute) and dec.attr in router_http_methods:
                                has_router = True
                                break
                        if not has_router:
                            errors.append(
                                f"[FAIL] {rel_path}:{item.lineno}: Fungsi '{item.name}' bukan endpoint router. "
                                f"File di 'api/routes/' HANYA boleh berisi endpoint route terdekorasi. "
                                f"Pindahkan fungsi non-route ke layer yang sesuai: "
                                f"logika bisnis -> 'services/', dependensi -> 'api/deps.py', utilitas -> 'core/'."
                            )

    # Cek apakah seluruh subclass DomainException sudah didaftarkan di main.py
    exc_file = root / "core" / "exceptions.py"
    if not exc_file.is_file():
        exc_file = root / "core" / "exception.py"
    main_file = root / "main.py"

    if exc_file.is_file() and main_file.is_file():
        try:
            exc_tree = ast.parse(exc_file.read_text(encoding="utf-8", errors="replace"))
            main_tree = ast.parse(main_file.read_text(encoding="utf-8", errors="replace"))

            domain_exceptions: set[str] = set()
            for node in ast.walk(exc_tree):
                if isinstance(node, ast.ClassDef) and node.name != "DomainException":
                    for base in node.bases:
                        if isinstance(base, ast.Name) and base.id == "DomainException":
                            domain_exceptions.add(node.name)

            handled_exceptions: set[str] = set()
            for node in ast.walk(main_tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for dec in node.decorator_list:
                        if (
                            isinstance(dec, ast.Call)
                            and isinstance(dec.func, ast.Attribute)
                            and dec.func.attr == "exception_handler"
                            and dec.args
                            and isinstance(dec.args[0], ast.Name)
                        ):
                            handled_exceptions.add(dec.args[0].id)

            unhandled = sorted(domain_exceptions - handled_exceptions)
            for exc_name in unhandled:
                errors.append(
                    f"[FAIL] main.py: Subclass DomainException '{exc_name}' belum didaftarkan "
                    f"pada '@app.exception_handler({exc_name})' di main.py."
                )
        except SyntaxError:
            pass

    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print("Penggunaan: python audit_structure.py <path_ke_backend>")
        return 2

    target = Path(sys.argv[1])
    if not target.is_dir():
        print(f"[ERROR] Direktori tidak ditemukan: {target}")
        return 2

    errors = audit_backend(target)
    if not errors:
        print(f"[PASS] Struktur backend di '{target}' 100% bersih dan patuh aturan layer!")
        return 0

    print(f"Ditemukan {len(errors)} pelanggaran struktur pada '{target}':\n")
    for err in errors:
        print(f"  {err}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
