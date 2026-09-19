#!/usr/bin/env python3
"""Verifica SHA-256 sin regenerar datos ni manifiestos (solo biblioteca estándar).

Por defecto descubre archivos rastreados con git ls-files. --include-untracked
permite revisar manifiestos nuevos antes de stage/commit. --manifest restringe
la comprobación a paquetes explícitos, por ejemplo copias temporales de pruebas.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
from pathlib import Path, PurePosixPath

NAMES = frozenset({"SHA256SUMS", "SHA256SUMS.txt", "MANIFEST-SHA256.txt"})
# Única excepción histórica: sus rutas parten de la raíz, no de su carpeta.
ROOT_BASED = frozenset({"experimentos/resultados/SHA256SUMS"})
LINE = re.compile(r"([0-9a-fA-F]{64}) ([ *])(.+)")


def discover(root: Path, include_untracked: bool = False) -> list[str]:
    command = ["git", "-C", str(root), "ls-files", "-z", "--cached"]
    if include_untracked:
        command += ["--others", "--exclude-standard"]
    result = subprocess.run(command, check=True, capture_output=True)
    files = result.stdout.decode("utf-8").split("\0")
    return sorted({p for p in files if PurePosixPath(p).name in NAMES})


def safe_path(base: Path, relative: str) -> Path:
    path = PurePosixPath(relative)
    if (not relative or path.is_absolute() or ".." in path.parts
            or "\\" in relative or ":" in relative or "\0" in relative):
        raise ValueError(f"ruta relativa inválida: {relative!r}")
    target = (base / relative).resolve()
    if not target.is_relative_to(base.resolve()):
        raise ValueError(f"ruta fuera de la base: {relative!r}")
    return target


def manifest_base(root: Path, manifest: str) -> Path:
    return root if manifest in ROOT_BASED else safe_path(root, manifest).parent


def parse(text: str) -> list[tuple[str, str]]:
    entries = []
    seen = set()
    for number, line in enumerate(text.splitlines(), 1):
        match = LINE.fullmatch(line)
        if not match:
            raise ValueError(f"línea {number} inválida")
        digest, _, relative = match.groups()
        normalized = PurePosixPath(relative).as_posix()
        if normalized in seen:
            raise ValueError(f"línea {number}: ruta duplicada {relative!r}")
        seen.add(normalized)
        entries.append((digest.lower(), relative))
    if not entries:
        raise ValueError("manifiesto vacío")
    return entries


def verify(root: Path, manifests: list[str]) -> dict[str, int]:
    totals = dict(manifests=len(manifests), entries=0, ok=0, failed=0)
    print("MANIFEST | BASE | ENTRIES | OK | FAILED")
    if not manifests:
        print("FAILED: no se descubrieron manifiestos")
        totals["failed"] += 1
    for manifest in manifests:
        count = ok = failed = 0
        base_label = "?"
        try:
            path = safe_path(root, manifest)
            base = manifest_base(root, manifest)
            base_label = base.relative_to(root).as_posix()
            entries = parse(path.read_text(encoding="utf-8"))
            count = len(entries)
            for expected, relative in entries:
                try:
                    target = safe_path(base, relative)
                    if target == path:
                        raise ValueError("autorreferencia")
                    with target.open("rb") as stream:
                        actual = hashlib.file_digest(stream, "sha256").hexdigest()
                    if actual != expected:
                        print(f"MISMATCH: {manifest}: {relative}")
                        failed += 1
                    else:
                        ok += 1
                except FileNotFoundError:
                    print(f"MISSING: {manifest}: {relative}")
                    failed += 1
                except (OSError, ValueError) as error:
                    print(f"FAILED: {manifest}: {relative}: {error}")
                    failed += 1
        except (OSError, ValueError) as error:
            print(f"FAILED: {manifest}: {error}")
            failed += 1
        print(f"{manifest} | {base_label} | {count} | {ok} | {failed}")
        totals["entries"] += count
        totals["ok"] += ok
        totals["failed"] += failed
    print(" ".join(f"{key}={value}" for key, value in totals.items()))
    return totals


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--include-untracked", action="store_true")
    group.add_argument("--manifest", action="append", help="ruta relativa a --root; repetible")
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        manifests = args.manifest if args.manifest is not None else discover(root, args.include_untracked)
        return int(verify(root, manifests)["failed"] != 0)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"FAILED: descubrimiento: {error}")
        print("manifests=0 entries=0 ok=0 failed=1")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
