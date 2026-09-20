"""Genera y verifica un manifiesto SHA256 del paquete experimentos/evidencia-17.

No modifica ni regenera evidencia; solo calcula/compara huellas SHA256 de los
bytes actualmente presentes en disco. Rutas relativas al paquete, orden
determinista (ordenadas alfabéticamente), y el propio manifiesto nunca se
incluye dentro de sí mismo.

Uso:
    python experimentos/verificar_manifiesto_evidencia17.py generar
    python experimentos/verificar_manifiesto_evidencia17.py verificar

BLOCKED_BY_20: no se debe commitear el manifiesto generado mientras la
corrección #20 (preservación EOL/bytes originales) no esté fusionada en
main, porque algunos archivos del paquete (comparacion.json, config.json)
tienen hashes internos calculados sobre bytes CRLF que Git normaliza
actualmente a LF; regenerar el manifiesto antes de #20 lo dejaría obsoleto
en cuanto esos bytes se corrijan.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

PAQUETE = Path(__file__).resolve().parent / "evidencia-17"
NOMBRE_MANIFIESTO = "SHA256SUMS.txt"


def listar_archivos(paquete: Path) -> list[Path]:
    manifiesto = paquete / NOMBRE_MANIFIESTO
    archivos = [p for p in paquete.rglob("*") if p.is_file() and p != manifiesto]
    return sorted(archivos, key=lambda p: p.relative_to(paquete).as_posix())


def calcular_manifiesto(paquete: Path) -> str:
    lineas = []
    for archivo in listar_archivos(paquete):
        huella = hashlib.sha256(archivo.read_bytes()).hexdigest()
        ruta_relativa = archivo.relative_to(paquete).as_posix()
        lineas.append(f"{huella}  {ruta_relativa}")
    return "\n".join(lineas) + "\n"


def generar(paquete: Path) -> Path:
    destino = paquete / NOMBRE_MANIFIESTO
    destino.write_text(calcular_manifiesto(paquete), encoding="utf-8", newline="\n")
    return destino


def verificar(paquete: Path) -> bool:
    manifiesto = paquete / NOMBRE_MANIFIESTO
    if not manifiesto.exists():
        print(f"No existe {manifiesto}", file=sys.stderr)
        return False
    esperado = manifiesto.read_text(encoding="utf-8")
    actual = calcular_manifiesto(paquete)
    if esperado != actual:
        esperadas = dict(line.split("  ", 1)[::-1] for line in esperado.splitlines() if line)
        actuales = dict(line.split("  ", 1)[::-1] for line in actual.splitlines() if line)
        for ruta in sorted(set(esperadas) | set(actuales)):
            if esperadas.get(ruta) != actuales.get(ruta):
                print(f"MISMATCH: {ruta}", file=sys.stderr)
        return False
    print(f"OK: {len(actual.splitlines())} archivos verificados")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("accion", choices=["generar", "verificar"])
    parser.add_argument("--paquete", type=Path, default=PAQUETE)
    args = parser.parse_args()
    if args.accion == "generar":
        destino = generar(args.paquete)
        print(f"Manifiesto escrito en {destino}")
        return 0
    return 0 if verificar(args.paquete) else 1


if __name__ == "__main__":
    raise SystemExit(main())
