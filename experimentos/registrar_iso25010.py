"""Registra una repetición real verificada en la plantilla ISO 25010."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import tempfile
from pathlib import Path


HISTORICAL_RELIABILITY = "fiabilidad_nominal_50u_1h"
CORRECTIVE_RELIABILITY = "fiabilidad_nominal_50u_1h_refresh"
RELIABILITY_SCENARIOS = {HISTORICAL_RELIABILITY, CORRECTIVE_RELIABILITY}
SCENARIOS = {"eficiencia_nominal_50u_5m", *RELIABILITY_SCENARIOS}
BUSINESS_REQUESTS = {
    ("GET", "GET /api/v1/reservas"),
    ("GET", "GET /api/v1/reservas/{id}"),
}
SESSION_REQUESTS = {
    ("POST", "POST /api/v1/auth/login"),
    ("POST", "POST /api/v1/auth/refresh"),
}


def attempt_directory_name(repetition: int, attempt: int) -> str:
    if repetition not in range(1, 11) or attempt < 1:
        raise ValueError("Repetición/intento fuera de rango")
    base = f"rep-{repetition:02d}"
    return base if attempt == 1 else f"{base}-attempt-{attempt:02d}"
RELIABILITY_EVIDENCE = {
    "metadata.json",
    "environment.txt",
    "locust_stats.csv",
    "locust_stats_history.csv",
    "locust_failures.csv",
    "locust_exceptions.csv",
    "locust-report.html",
    "locust.log",
    "prometheus-5xx-count.promql",
    "prometheus-5xx-percent.promql",
    "prometheus-p95.promql",
    "prometheus-5xx-result.txt",
    "prometheus-5xx-percent-result.txt",
    "prometheus-p95-result.txt",
    "prometheus-health-before.txt",
    "prometheus-health-after.txt",
    "gateway-health-before.json",
    "gateway-health-after.json",
    "reservas-health-before.json",
    "reservas-health-after.json",
    "docker-stats-before.txt",
    "docker-stats-after.txt",
    "cockroach-containers-before.txt",
    "cockroach-containers-after.txt",
    "deployment-state-before.txt",
    "deployment-state-after.txt",
    "reservas-service.log",
}
CORRECTIVE_EVIDENCE = RELIABILITY_EVIDENCE | {
    "locust_requests.csv",
    "locust-final-stats.json",
    "phase-summary.json",
    "gateway-service.log",
    "phase-boundaries.json",
    "prometheus-gateway-status-by-uri.promql",
    "prometheus-gateway-status-by-uri-result.json",
    "prometheus-reservas-status-by-uri.promql",
    "prometheus-reservas-status-by-uri-result.json",
    "SHA256SUMS",
}


def request_population(evidence_dir: Path) -> dict[str, int | bool]:
    counts: dict[tuple[str, str], int] = {}
    final_stats = evidence_dir / "locust-final-stats.json"

    if final_stats.is_file():
        try:
            payload = json.loads(final_stats.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError("Snapshot final de Locust ausente o corrupto") from error

        entries = payload.get("entries")
        if not isinstance(entries, list):
            raise ValueError("Snapshot final de Locust sin entries válidas")

        for row in entries:
            if not isinstance(row, dict):
                raise ValueError("Entrada inválida en snapshot final de Locust")
            key = (
                str(row.get("request_type", "")),
                str(row.get("name", "")),
            )
            count = row.get("request_count")
            if (
                isinstance(count, bool)
                or not isinstance(count, int)
                or count < 0
            ):
                raise ValueError(f"Request Count final inválido para {key}")
            counts[key] = counts.get(key, 0) + count
    else:
        with (evidence_dir / "locust_stats.csv").open(
            encoding="utf-8-sig", newline=""
        ) as stream:
            rows = list(csv.DictReader(stream))

        for row in rows:
            key = (row.get("Type", ""), row.get("Name", ""))
            if key == ("", "Aggregated"):
                continue
            try:
                count = int(row.get("Request Count", "0"))
            except ValueError as error:
                raise ValueError(f"Request Count inválido para {key}") from error
            counts[key] = counts.get(key, 0) + count

    business_get_count = sum(counts.get(key, 0) for key in BUSINESS_REQUESTS)
    login_count = counts.get(("POST", "POST /api/v1/auth/login"), 0)
    refresh_count = counts.get(("POST", "POST /api/v1/auth/refresh"), 0)
    protected_names = {name for _, name in BUSINESS_REQUESTS | SESSION_REQUESTS}
    identity_collision = any(
        name in protected_names
        and (request_type, name) not in BUSINESS_REQUESTS | SESSION_REQUESTS
        and count > 0
        for (request_type, name), count in counts.items()
    )
    names_separated = login_count > 0 and refresh_count > 0 and not identity_collision
    return {
        "business_get_count": business_get_count,
        "login_request_count": login_count,
        "refresh_request_count": refresh_count,
        "business_population_valid": business_get_count > 0,
        "request_names_separated": names_separated,
    }


def business_event_metrics(evidence_dir: Path) -> dict[str, int]:
    with (evidence_dir / "locust_requests.csv").open(
        encoding="utf-8-sig", newline=""
    ) as stream:
        rows = list(csv.DictReader(stream))
    business = [
        row
        for row in rows
        if (row.get("request_type"), row.get("name")) in BUSINESS_REQUESTS
    ]
    five_xx = sum(
        1
        for row in business
        if row.get("status_code", "").isdigit()
        and 500 <= int(row["status_code"]) <= 599
    )
    return {"business_event_count": len(business), "business_http_5xx": five_xx}


def verify_sha256_manifest(evidence_dir: Path) -> int:
    manifest = evidence_dir / "SHA256SUMS"
    if not manifest.is_file():
        raise ValueError("Falta SHA256SUMS en la repetición")
    expected: dict[str, str] = {}
    for line in manifest.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        try:
            digest, relative = line.split("  ", 1)
        except ValueError as error:
            raise ValueError("Línea inválida en SHA256SUMS") from error
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise ValueError(f"Hash SHA-256 inválido para {relative}")
        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts or relative in expected:
            raise ValueError(f"Ruta inválida o duplicada en SHA256SUMS: {relative}")
        expected[relative] = digest

    actual_files = {
        path.relative_to(evidence_dir).as_posix(): path
        for path in evidence_dir.rglob("*")
        if path.is_file() and path.name != "SHA256SUMS"
    }
    if set(expected) != set(actual_files):
        missing = sorted(set(actual_files) - set(expected))
        extra = sorted(set(expected) - set(actual_files))
        raise ValueError(f"SHA256SUMS no cubre exactamente la evidencia: faltan={missing}, sobran={extra}")
    for relative, path in actual_files.items():
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected[relative]:
            raise ValueError(f"Hash incorrecto: {relative}")
    return len(expected)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", required=True, choices=sorted(SCENARIOS))
    parser.add_argument("--repetition", required=True, type=int, choices=range(1, 11))
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--total-requests", required=True, type=int)
    parser.add_argument("--http-5xx", required=True, type=int)
    parser.add_argument("--p95-ms", required=True, type=float)
    parser.add_argument("--p99-ms", required=True, type=float)
    parser.add_argument("--evidence-dir", required=True, type=Path)
    parser.add_argument("--observation", default="")
    parser.add_argument("--csv-path", type=Path)
    args = parser.parse_args()
    if args.attempt < 1:
        parser.error("--attempt debe ser mayor o igual que 1")
    if args.csv_path is None:
        filename = (
            "iso25010-correctiva.csv"
            if args.scenario == CORRECTIVE_RELIABILITY
            else "iso25010.csv"
        )
        args.csv_path = Path(__file__).parent / "resultados" / filename
    return args


def validate_evidence(args: argparse.Namespace) -> None:
    attempt = getattr(args, "attempt", 1)
    expected_suffix = Path(args.scenario) / attempt_directory_name(
        args.repetition, attempt
    )
    if not args.evidence_dir.resolve().as_posix().endswith(expected_suffix.as_posix()):
        raise ValueError("La ruta de evidencia no coincide con escenario/repetición")
    required_names = {"metadata.json", "locust_stats.csv", "prometheus-5xx-result.txt"}
    if args.scenario in RELIABILITY_SCENARIOS:
        required_names = (
            CORRECTIVE_EVIDENCE
            if args.scenario == CORRECTIVE_RELIABILITY
            else RELIABILITY_EVIDENCE
        )
    for path in (args.evidence_dir / name for name in sorted(required_names)):
        allow_empty = path.name in {"gateway-service.log", "reservas-service.log"}
        if not path.is_file() or (path.stat().st_size == 0 and not allow_empty):
            raise ValueError(f"Falta evidencia real: {path}")
    metadata_path = args.evidence_dir / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
    if metadata.get("scenario") != args.scenario or metadata.get("repetition") != args.repetition:
        raise ValueError("Los metadatos no coinciden con escenario/repetición")
    if metadata.get("attempt", 1) != attempt:
        raise ValueError("Los metadatos no coinciden con el intento solicitado")
    if args.scenario in RELIABILITY_SCENARIOS:
        if metadata.get("status") != "completed" or metadata.get("execution_completed") is not True:
            raise ValueError("La ejecución experimental no consta como completada")
        if metadata.get("duration_completed") is not True:
            raise ValueError("La ejecución no completó la duración planificada")
        if metadata.get("evidence_complete") is not True:
            raise ValueError("La recolección de evidencia no consta como completa")
        if metadata.get("reservas_log_capture_succeeded") is not True:
            raise ValueError("La captura de logs de Reservas no consta como exitosa")
        if not isinstance(metadata.get("reservas_log_content_length"), int):
            raise ValueError("Falta la longitud del contenido capturado en logs de Reservas")
        if metadata.get("environment_consistent") is not True:
            raise ValueError("El entorno o despliegue cambió durante la repetición")
        if metadata.get("git_worktree_clean_before") is not True:
            raise ValueError("El árbol Git no estaba limpio al iniciar la repetición")
        if metadata.get("users") != 50 or metadata.get("spawn_rate") != 10:
            raise ValueError("Los metadatos no corresponden a 50 usuarios y spawn-rate 10")
        if metadata.get("planned_duration") != "1h" or metadata.get("planned_duration_seconds") != 3600:
            raise ValueError("Los metadatos no corresponden a la duración oficial de una hora")
        if isinstance(metadata.get("locust_exit_code"), bool) or not isinstance(
            metadata.get("locust_exit_code"), int
        ):
            raise ValueError("Falta el código de salida real de Locust")
        for field in (
            "started_at_utc", "finished_at_utc", "git_branch", "git_sha",
            "python_version", "locust_version", "deployment_fingerprint_before",
            "deployment_fingerprint_after",
        ):
            if not metadata.get(field):
                raise ValueError(f"Falta metadata obligatoria: {field}")
        if args.scenario == CORRECTIVE_RELIABILITY:
            elapsed = metadata.get("elapsed_seconds")
            if (
                isinstance(elapsed, bool)
                or not isinstance(elapsed, (int, float))
                or not math.isfinite(elapsed)
                or elapsed < 3595
            ):
                raise ValueError("La duración real no alcanza la hora con tolerancia de 5 s")
            if metadata.get("gateway_log_capture_succeeded") is not True:
                raise ValueError("La captura de logs del Gateway no consta como exitosa")
            if not isinstance(metadata.get("gateway_log_content_length"), int):
                raise ValueError("Falta la longitud de los logs del Gateway")
            population = request_population(args.evidence_dir)
            event_metrics = business_event_metrics(args.evidence_dir)
            if population["business_population_valid"] is not True:
                raise ValueError("La repetición no contiene GET de negocio")
            if population["request_names_separated"] is not True:
                raise ValueError("Login, refresh y GET no están separados correctamente")
            for field, value in population.items():
                if metadata.get(field) != value:
                    raise ValueError(f"Metadata de población inconsistente: {field}")
            for field, value in event_metrics.items():
                if metadata.get(field) != value:
                    raise ValueError(f"Metadata de eventos inconsistente: {field}")
            if metadata.get("business_events_consistent") is not True:
                raise ValueError("El registro por evento no coincide con locust_stats.csv")
            if metadata.get("prometheus_reservas_arrival_valid") is not True:
                raise ValueError("Prometheus no demuestra llegada a Reservas después de t=900 s")
            if event_metrics["business_event_count"] != population["business_get_count"]:
                raise ValueError("Los GET por evento no coinciden con locust_stats.csv")
            if args.total_requests != event_metrics["business_event_count"]:
                raise ValueError("total_requests no coincide con los GET de negocio")
            if args.http_5xx != event_metrics["business_http_5xx"]:
                raise ValueError("http_5xx no coincide con los GET de negocio")
            if metadata.get("manifest_valid") is not True:
                raise ValueError("El manifiesto no consta como válido")
            entries = verify_sha256_manifest(args.evidence_dir)
            if metadata.get("manifest_entries") != entries:
                raise ValueError("El número de entradas del manifiesto no coincide")
    elif metadata.get("status") != "completed" or metadata.get("exit_code") != 0:
        raise ValueError("La ejecución Locust no consta como completada correctamente")


def update_csv(args: argparse.Namespace) -> float:
    if args.total_requests <= 0:
        raise ValueError("total_requests debe ser mayor que cero")
    if args.http_5xx < 0 or args.http_5xx > args.total_requests:
        raise ValueError("http_5xx debe estar entre cero y total_requests")
    if not math.isfinite(args.p95_ms) or args.p95_ms < 0:
        raise ValueError("p95_ms debe ser un número real no negativo")
    if not math.isfinite(args.p99_ms) or args.p99_ms < args.p95_ms:
        raise ValueError("p99_ms debe ser válido y mayor o igual que p95_ms")
    validate_evidence(args)

    with args.csv_path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = reader.fieldnames
        rows = list(reader)
    if not fieldnames:
        raise ValueError("El CSV no contiene encabezado")

    matches = [
        row
        for row in rows
        if row["escenario"] == args.scenario
        and int(row["repeticion"]) == args.repetition
    ]
    if len(matches) != 1:
        raise ValueError("La plantilla no contiene una única fila para la repetición")
    row = matches[0]
    measured_fields = (
        "total_requests", "failures", "failure_rate_percent", "p95_ms", "p99_ms", "valida"
    )
    if any(row[field].strip() for field in measured_fields):
        raise ValueError("La fila ya contiene mediciones; no se sobrescribirá")
    if args.scenario == CORRECTIVE_RELIABILITY:
        if "intento" not in fieldnames:
            raise ValueError("La salida correctiva no contiene la columna intento")
        row["intento"] = str(getattr(args, "attempt", 1))

    failure_rate = 100.0 * args.http_5xx / args.total_requests
    row.update(
        total_requests=str(args.total_requests),
        failures=str(args.http_5xx),
        failure_rate_percent=f"{failure_rate:.6f}",
        p95_ms=f"{args.p95_ms:.6f}",
        p99_ms=f"{args.p99_ms:.6f}",
        valida="si",
        observacion=args.observation,
    )

    args.csv_path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix="iso25010-", suffix=".csv", dir=args.csv_path.parent, text=True
    )
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary_name, args.csv_path)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise
    return failure_rate


def main() -> int:
    args = parse_args()
    try:
        failure_rate = update_csv(args)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}")
        return 2
    print(
        f"Registrada {args.scenario} r{args.repetition}: "
        f"HTTP 5xx={failure_rate:.6f} %, p95={args.p95_ms:.6f} ms"
    )
    if args.repetition in (1, 10):
        print("La evidencia se conserva, pero esta repetición se excluye del análisis.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
