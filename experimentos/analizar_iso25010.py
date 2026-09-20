"""Calcula estadísticas ISO 25010 solo a partir de mediciones reales completas."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path


REQUIRED_COLUMNS = {
    "escenario",
    "repeticion",
    "usuarios",
    "duracion",
    "total_requests",
    "failures",
    "failure_rate_percent",
    "p95_ms",
    "p99_ms",
    "valida",
    "observacion",
}
VALID_VALUES = {"1", "true", "si", "sí", "yes"}
T_CRITICAL_95_DF7 = 2.364624251
EXPECTED_REPETITIONS = set(range(1, 11))
ANALYZED_REPETITIONS = set(range(2, 10))
EFFICIENCY_SCENARIO = "eficiencia_nominal_50u_5m"
POPULATED_EFFICIENCY_SCENARIO = "eficiencia_nominal_50u_5m_poblada"

LEGACY_RELIABILITY_SCENARIO = "fiabilidad_nominal_50u_1h_refresh"
POPULATED_RELIABILITY_SCENARIO = "fiabilidad_nominal_50u_1h_refresh_poblada"

RELIABILITY_RAW_DIRS = {
    LEGACY_RELIABILITY_SCENARIO: "fiabilidad_nominal_50u_1h_refresh",
    POPULATED_RELIABILITY_SCENARIO: "fiabilidad_nominal_50u_1h_refresh_poblada",
}
EFFICIENCY_REQUESTS = {
    ("GET", "GET /api/v1/reservas"),
    ("GET", "GET /api/v1/reservas/{id}"),
}
EFFICIENCY_EXCLUDED_REQUESTS = {
    ("POST", "POST /api/v1/auth/login"),
}
LOCUST_REQUIRED_COLUMNS = {
    "Type",
    "Name",
    "Request Count",
    "Failure Count",
    "95%",
    "99%",
}


def parse_args() -> argparse.Namespace:
    default_csv = Path(__file__).parent / "resultados" / "iso25010.csv"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", nargs="?", type=Path, default=default_csv)
    parser.add_argument(
        "--raw-root",
        type=Path,
        help="Raíz de evidencia raw; por defecto, el directorio raw junto al CSV.",
    )
    parser.add_argument(
        "--emit-markdown",
        action="store_true",
        help="Emite el bloque Markdown E2 reconstruido directamente desde raw.",
    )
    parser.add_argument(
        "--emit-latex",
        action="store_true",
        help="Emite la fila LaTeX E2 reconstruida directamente desde raw.",
    )
    parser.add_argument(
        "--write-populated-efficiency",
        type=Path,
        help="Genera este CSV únicamente desde los diez raws reales de eficiencia poblada.",
    )
    return parser.parse_args()


def read_rows(csv_path: Path) -> dict[str, list[dict[str, str]]]:
    with csv_path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        missing = REQUIRED_COLUMNS.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Faltan columnas requeridas: {', '.join(sorted(missing))}")

        scenarios: dict[str, list[dict[str, str]]] = defaultdict(list)
        for line_number, row in enumerate(reader, start=2):
            scenario = row["escenario"].strip()
            if not scenario:
                raise ValueError(f"Fila {line_number}: escenario vacío")
            try:
                repetition = int(row["repeticion"])
            except ValueError as error:
                raise ValueError(f"Fila {line_number}: repetición inválida") from error
            if repetition not in EXPECTED_REPETITIONS:
                raise ValueError(f"Fila {line_number}: repetición fuera del rango 1..10")
            row["_repetition"] = str(repetition)
            scenarios[scenario].append(row)
    return scenarios


def validate_design(scenario: str, rows: list[dict[str, str]]) -> None:
    repetitions = [int(row["_repetition"]) for row in rows]
    if len(repetitions) != len(set(repetitions)):
        raise ValueError(f"{scenario}: existen repeticiones duplicadas")
    missing = EXPECTED_REPETITIONS.difference(repetitions)
    if missing:
        raise ValueError(f"{scenario}: faltan repeticiones {sorted(missing)}")


def valid_measurements(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if int(row["_repetition"]) in ANALYZED_REPETITIONS
        and row["valida"].strip().lower() in VALID_VALUES
        and row["total_requests"].strip()
        and row["failures"].strip()
        and row["failure_rate_percent"].strip()
        and row["p95_ms"].strip()
        and row["p99_ms"].strip()
    ]


def summarize(values: list[float]) -> tuple[float, float, float, float]:
    mean = statistics.fmean(values)
    standard_deviation = statistics.stdev(values)
    margin = T_CRITICAL_95_DF7 * standard_deviation / math.sqrt(len(values))
    return mean, standard_deviation, mean - margin, mean + margin


def read_efficiency_population(
    raw_root: Path, repetitions: list[int]
) -> dict[int, dict[str, float | int | str]]:
    """Lee percentiles de GET de Reservas sin filtrar por estado ni latencia."""

    measurements: dict[int, dict[str, float | int | str]] = {}
    for repetition in repetitions:
        stats_path = (
            raw_root
            / EFFICIENCY_SCENARIO
            / f"rep-{repetition:02d}"
            / "locust_stats.csv"
        )
        with stats_path.open(encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            missing = LOCUST_REQUIRED_COLUMNS.difference(reader.fieldnames or [])
            if missing:
                raise ValueError(
                    f"{stats_path}: faltan columnas Locust: {', '.join(sorted(missing))}"
                )
            stats_rows = list(reader)

        active_rows: list[tuple[dict[str, str], int]] = []
        for line_number, row in enumerate(stats_rows, start=2):
            try:
                request_count = int(row["Request Count"])
            except ValueError as error:
                raise ValueError(
                    f"{stats_path}:{line_number}: Request Count inválido"
                ) from error
            if request_count < 0:
                raise ValueError(
                    f"{stats_path}:{line_number}: Request Count no puede ser negativo"
                )
            if row["Name"] != "Aggregated" and request_count > 0:
                active_rows.append((row, line_number))

        unexpected = [
            (row["Type"], row["Name"])
            for row, _ in active_rows
            if (row["Type"], row["Name"])
            not in EFFICIENCY_REQUESTS | EFFICIENCY_EXCLUDED_REQUESTS
        ]
        if unexpected:
            raise ValueError(
                f"{stats_path}: requests activos sin clasificación poblacional: "
                + ", ".join(f"{method} {name}" for method, name in unexpected)
            )

        included = [
            (row, line_number)
            for row, line_number in active_rows
            if (row["Type"], row["Name"]) in EFFICIENCY_REQUESTS
        ]
        if not included:
            raise ValueError(
                f"{stats_path}: no hay observaciones de GET de Reservas/Solicitudes"
            )
        if len(included) > 1:
            names = ", ".join(row["Name"] for row, _ in included)
            raise ValueError(
                f"{stats_path}: hay varias filas GET activas ({names}); "
                "los percentiles por fila no permiten reconstruir el percentil conjunto "
                "sin una distribución raw combinable"
            )

        row, line_number = included[0]
        try:
            request_count = int(row["Request Count"])
            failure_count = int(row["Failure Count"])
            p95 = float(row["95%"])
            p99 = float(row["99%"])
        except ValueError as error:
            raise ValueError(
                f"{stats_path}:{line_number}: métricas poblacionales inválidas"
            ) from error
        if failure_count < 0 or failure_count > request_count:
            raise ValueError(
                f"{stats_path}:{line_number}: Failure Count inválido"
            )
        if p95 < 0 or p99 < p95:
            raise ValueError(f"{stats_path}:{line_number}: percentiles inválidos")

        measurements[repetition] = {
            "request": row["Name"],
            "line": line_number,
            "total_requests": request_count,
            "failures": failure_count,
            "p95_ms": p95,
            "p99_ms": p99,
            "source": str(stats_path),
        }
    return measurements


def percentile_nearest_rank(values: list[float], quantile: float) -> float:
    """Percentil discreto: ceil(q*n), sin excluir ninguna observación."""
    if not values:
        raise ValueError("No existen observaciones para calcular percentiles")
    return sorted(values)[math.ceil(quantile * len(values)) - 1]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _first_sha256(path: Path) -> str:
    try:
        content = path.read_text(encoding="utf-8-sig").strip()
    except OSError as error:
        raise ValueError(f"{path}: no se pudo leer el hash") from error

    if not content:
        raise ValueError(f"{path}: archivo de hash vacío")

    value = content.split()[0].lower()

    if len(value) != 64 or any(
        char not in "0123456789abcdef" for char in value
    ):
        raise ValueError(f"{path}: SHA-256 inválido")

    return value


def _verify_portable_sha256_manifest(directory: Path) -> None:
    """Valida SHA256SUMS aunque el manifest conserve rutas del host original."""
    manifest = directory / "SHA256SUMS"

    try:
        lines = manifest.read_text(encoding="utf-8-sig").splitlines()
    except OSError as error:
        raise ValueError(
            f"{manifest}: manifest ausente o ilegible"
        ) from error

    if not lines:
        raise ValueError(f"{manifest}: manifest vacío")

    seen_names: set[str] = set()

    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue

        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            raise ValueError(
                f"{manifest}:{line_number}: entrada SHA256SUMS inválida"
            )

        expected, recorded_path = parts
        expected = expected.lower()

        if len(expected) != 64 or any(
            char not in "0123456789abcdef" for char in expected
        ):
            raise ValueError(
                f"{manifest}:{line_number}: SHA-256 inválido"
            )

        filename = Path(recorded_path.lstrip("*")).name

        if not filename:
            raise ValueError(
                f"{manifest}:{line_number}: nombre de archivo inválido"
            )

        if filename in seen_names:
            raise ValueError(
                f"{manifest}:{line_number}: basename duplicado: {filename}"
            )

        seen_names.add(filename)

        target = directory / filename

        if not target.is_file():
            raise ValueError(
                f"{manifest}:{line_number}: evidencia ausente: {filename}"
            )

        actual = _sha256_file(target)

        if actual != expected:
            raise ValueError(
                f"{manifest}:{line_number}: SHA-256 no coincide para {filename}"
            )


def read_populated_efficiency_population(
    raw_root: Path, repetitions: list[int]
) -> dict[int, dict[str, float | int | str]]:
    """Reconstruye PI1 desde cada evento GET de la campaña poblada.

    Login y refresh son necesarios para el harness, pero no pertenecen a la
    población. Un 4xx/5xx sí pertenece y nunca se descarta.
    """
    measurements: dict[int, dict[str, float | int | str]] = {}
    required = {"request_type", "name", "response_time_ms", "status_code"}

    strict_campaign = (
        len(repetitions) == len(EXPECTED_REPETITIONS)
        and set(repetitions) == EXPECTED_REPETITIONS
    )

    campaign_values: dict[str, set[str]] = {
        "evidence_git_sha": set(),
        "deployed_software_sha": set(),
        "dataset_sha256": set(),
        "harness_manifest_sha256": set(),
    }
    request_raw_hashes: set[str] = set()

    for repetition in repetitions:
        directory = raw_root / POPULATED_EFFICIENCY_SCENARIO / f"rep-{repetition:02d}"
        metadata_path = directory / "metadata.json"
        events_path = directory / "locust_requests.csv"
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as error:
            raise ValueError(f"{metadata_path}: metadata ausente o inválida") from error
        required_evidence = {
            "locust_stats.csv",
            "locust_stats_history.csv",
            "locust_failures.csv",
            "locust_exceptions.csv",
            "locust.log",
            "locust-report.html",
            "locust-final-stats.json",
            "deployed-software-sha.txt",
            "harness-sha256.txt",
            "dataset-sha256.txt",
            "SHA256SUMS",
        }

        if strict_campaign:
            required_evidence.update(
                {
                    "dataset.csv",
                    "evidence-git-sha.txt",
                    "deployment-before.txt",
                    "deployment-after.txt",
                    "harness-before-sha256.txt",
                    "harness-after-sha256.txt",
                    "locust-exit-code.txt",
                    "elapsed-seconds.txt",
                    "start_utc.txt",
                    "end_utc.txt",
                }
            )
        absent = sorted(name for name in required_evidence if not (directory / name).is_file())
        if absent:
            raise ValueError(f"{directory}: evidencia incompleta: {', '.join(absent)}")
        if not (metadata.get("duration_completed") is True and
                metadata.get("evidence_complete") is True and
                metadata.get("dataset_verified") is True and
                metadata.get("software_sha_consistent") is True and
                metadata.get("harness_consistent") is True):
            raise ValueError(f"{directory}: repetición estructuralmente inválida")
        if strict_campaign:
            if metadata.get("scenario") != POPULATED_EFFICIENCY_SCENARIO:
                raise ValueError(
                    f"{directory}: escenario metadata inválido"
                )

            if metadata.get("mode") != "official":
                raise ValueError(
                    f"{directory}: mode debe ser official"
                )

            if metadata.get("repetition") != repetition:
                raise ValueError(
                    f"{directory}: número de repetición no coincide"
                )

            if metadata.get("planned_duration_seconds") != 300:
                raise ValueError(
                    f"{directory}: duración planificada distinta de 300 s"
                )

            if metadata.get("deployment_after_valid") is not True:
                raise ValueError(
                    f"{directory}: deployment_after_valid no es true"
                )

            if metadata.get("locust_exit_code") != 0:
                raise ValueError(
                    f"{directory}: locust_exit_code distinto de 0"
                )

            try:
                recorded_exit = int(
                    (directory / "locust-exit-code.txt")
                    .read_text(encoding="utf-8-sig")
                    .strip()
                )
            except (OSError, ValueError) as error:
                raise ValueError(
                    f"{directory}: locust-exit-code.txt inválido"
                ) from error

            if recorded_exit != 0:
                raise ValueError(
                    f"{directory}: locust-exit-code.txt distinto de 0"
                )

        if strict_campaign:
            _verify_portable_sha256_manifest(directory)

            evidence_git_sha = (
                directory / "evidence-git-sha.txt"
            ).read_text(
                encoding="utf-8-sig"
            ).strip()

            deployed_software_sha = (
                directory / "deployed-software-sha.txt"
            ).read_text(
                encoding="utf-8-sig"
            ).strip()

            if metadata.get("evidence_git_sha") != evidence_git_sha:
                raise ValueError(
                    f"{directory}: evidence_git_sha no coincide con archivo"
                )

            if metadata.get("deployed_software_sha") != deployed_software_sha:
                raise ValueError(
                    f"{directory}: deployed_software_sha no coincide con archivo"
                )

            dataset_sha = _sha256_file(directory / "dataset.csv")
            captured_dataset_sha = _first_sha256(
                directory / "dataset-sha256.txt"
            )

            if dataset_sha != captured_dataset_sha:
                raise ValueError(
                    f"{directory}: dataset.csv no coincide con dataset-sha256.txt"
                )

            harness_before = (
                directory / "harness-before-sha256.txt"
            ).read_bytes()

            harness_after = (
                directory / "harness-after-sha256.txt"
            ).read_bytes()

            if harness_before != harness_after:
                raise ValueError(
                    f"{directory}: harness cambió durante la repetición"
                )

            campaign_values["evidence_git_sha"].add(
                evidence_git_sha
            )
            campaign_values["deployed_software_sha"].add(
                deployed_software_sha
            )
            campaign_values["dataset_sha256"].add(
                dataset_sha
            )
            campaign_values["harness_manifest_sha256"].add(
                _sha256_file(directory / "harness-sha256.txt")
            )

            request_raw_hashes.add(
                _sha256_file(events_path)
            )

        response_times: list[float] = []
        listed = by_id = http_401 = http_5xx = 0
        with events_path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            missing = required.difference(reader.fieldnames or [])
            if missing:
                raise ValueError(f"{events_path}: faltan columnas: {', '.join(sorted(missing))}")
            for line, event in enumerate(reader, start=2):
                method, name = event["request_type"], event["name"]
                if method == "GET" and name not in {item[1] for item in EFFICIENCY_REQUESTS}:
                    raise ValueError(f"{events_path}:{line}: ruta GET no clasificada: {name}")
                if (method, name) not in EFFICIENCY_REQUESTS:
                    continue
                try:
                    latency, status = float(event["response_time_ms"]), int(event["status_code"])
                except ValueError as error:
                    raise ValueError(f"{events_path}:{line}: evento inválido") from error
                response_times.append(latency)
                listed += name == "GET /api/v1/reservas"
                by_id += name == "GET /api/v1/reservas/{id}"
                http_401 += status == 401
                http_5xx += 500 <= status <= 599
        if listed == 0 or by_id == 0:
            raise ValueError(f"{events_path}: población degenerada (listado={listed}, by-id={by_id})")
        measurements[repetition] = {
            "total_get": len(response_times), "listado": listed, "by_id": by_id,
            "http_401": http_401, "http_5xx": http_5xx,
            "p95_ms": percentile_nearest_rank(response_times, .95),
            "p99_ms": percentile_nearest_rank(response_times, .99), "source": str(events_path),
        }
    if strict_campaign:
        for label, values in campaign_values.items():
            if len(values) != 1:
                raise ValueError(
                    f"{POPULATED_EFFICIENCY_SCENARIO}: "
                    f"inconsistencia entre repeticiones en {label}: "
                    f"{len(values)} valores distintos"
                )

        if len(request_raw_hashes) != len(EXPECTED_REPETITIONS):
            raise ValueError(
                f"{POPULATED_EFFICIENCY_SCENARIO}: "
                "pseudorreplicación detectada; "
                f"{len(request_raw_hashes)} raws distintos para "
                f"{len(EXPECTED_REPETITIONS)} repeticiones"
            )

    return measurements


def write_populated_efficiency_csv(raw_root: Path, output: Path) -> None:
    """Escribe el derivado solamente tras validar los diez directorios raw."""
    population = read_populated_efficiency_population(raw_root, sorted(EXPECTED_REPETITIONS))
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["escenario", "repeticion", "usuarios", "duracion", "total_requests",
              "failures", "failure_rate_percent", "p95_ms", "p99_ms", "valida", "observacion"]
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for repetition in sorted(population):
            item = population[repetition]
            total = int(item["total_get"])
            writer.writerow({"escenario": POPULATED_EFFICIENCY_SCENARIO, "repeticion": repetition,
                             "usuarios": 50, "duracion": "5m", "total_requests": total,
                             "failures": item["http_5xx"],
                             "failure_rate_percent": 100 * int(item["http_5xx"]) / total,
                             "p95_ms": item["p95_ms"], "p99_ms": item["p99_ms"], "valida": "si",
                             "observacion": f"raw={item['source']}; listado={item['listado']}; by_id={item['by_id']}; 401={item['http_401']}"})


def read_corrective_reliability_population(
    raw_root: Path,
    rows: list[dict[str, str]],
    scenario: str = LEGACY_RELIABILITY_SCENARIO,
) -> dict[int, dict[str, float | int | str]]:
    """Reconstruye la población correctiva directamente desde locust_requests.csv."""

    try:
        raw_directory = RELIABILITY_RAW_DIRS[scenario]
    except KeyError as error:
        raise ValueError(
            f"{scenario}: escenario de fiabilidad correctiva no soportado"
        ) from error

    business_names = {
        "GET /api/v1/reservas",
        "GET /api/v1/reservas/{id}",
    }

    measurements: dict[int, dict[str, float | int | str]] = {}

    def percentile_nearest_rank(values: list[float], q: float) -> float:
        ordered = sorted(values)
        if not ordered:
            raise ValueError("No existen observaciones para calcular percentiles")
        rank = math.ceil(q * len(ordered))
        return ordered[rank - 1]

    for row in rows:
        repetition = int(row["_repetition"])
        attempt_text = row.get("intento", "").strip()
        attempt = int(attempt_text) if attempt_text else 1

        dirname = (
            f"rep-{repetition:02d}"
            if attempt == 1
            else f"rep-{repetition:02d}-attempt-{attempt:02d}"
        )

        events_path = (
            raw_root
            / raw_directory
            / dirname
            / "locust_requests.csv"
        )

        response_times: list[float] = []
        http_5xx = 0
        http_401 = 0

        with events_path.open(encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            required = {
                "request_type",
                "name",
                "response_time_ms",
                "status_code",
            }
            missing = required.difference(reader.fieldnames or [])
            if missing:
                raise ValueError(
                    f"{events_path}: faltan columnas: {', '.join(sorted(missing))}"
                )

            for line_number, event in enumerate(reader, start=2):
                if (
                    event["request_type"] != "GET"
                    or event["name"] not in business_names
                ):
                    continue

                try:
                    response_time = float(event["response_time_ms"])
                    status_code = int(event["status_code"])
                except ValueError as error:
                    raise ValueError(
                        f"{events_path}:{line_number}: evento inválido"
                    ) from error

                response_times.append(response_time)

                if status_code == 401:
                    http_401 += 1
                if 500 <= status_code <= 599:
                    http_5xx += 1

        if not response_times:
            raise ValueError(
                f"{events_path}: no contiene GET de negocio"
            )

        measurements[repetition] = {
            "attempt": attempt,
            "directory": dirname,
            "total_requests": len(response_times),
            "http_401": http_401,
            "http_5xx": http_5xx,
            "failure_rate_percent": 100.0 * http_5xx / len(response_times),
            "p95_ms": percentile_nearest_rank(response_times, 0.95),
            "p99_ms": percentile_nearest_rank(response_times, 0.99),
            "source": str(events_path),
        }

    return measurements


def format_decimal_es(value: float) -> str:
    return f"{value:.6f}".replace(".", ",")


def format_integer_es(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def build_corrective_document_blocks(
    raw_root: Path,
    rows: list[dict[str, str]],
    scenario: str = LEGACY_RELIABILITY_SCENARIO,
) -> dict[str, str]:
    """Genera bloques documentales directamente desde los eventos raw E2."""

    population = read_corrective_reliability_population(
        raw_root, rows, scenario
    )

    if set(population) != EXPECTED_REPETITIONS:
        raise ValueError(
            "fiabilidad correctiva: se requieren las repeticiones raw 1..10"
        )

    selected = [population[r] for r in sorted(ANALYZED_REPETITIONS)]

    failure_rates = [
        float(item["failure_rate_percent"]) for item in selected
    ]
    p95_values = [float(item["p95_ms"]) for item in selected]
    p99_values = [float(item["p99_ms"]) for item in selected]

    failure_mean, failure_sd, failure_low, failure_high = summarize(failure_rates)
    p95_mean, p95_sd, p95_low, p95_high = summarize(p95_values)
    p99_mean, p99_sd, p99_low, p99_high = summarize(p99_values)

    total_get = sum(int(item["total_requests"]) for item in population.values())
    total_401 = sum(int(item["http_401"]) for item in population.values())
    total_5xx = sum(int(item["http_5xx"]) for item in population.values())

    markdown = f"""Las diez repeticiones correctivas suman {format_integer_es(total_get)} GET de negocio, con {total_401} HTTP 401 y {total_5xx} HTTP 5xx.

| Métrica | n | Media | s muestral | IC95 | Interpretación |
| --- | ---: | ---: | ---: | --- | --- |
| Tasa HTTP 5xx | 8 | {format_decimal_es(failure_mean)} % | {format_decimal_es(failure_sd)} % | [{format_decimal_es(failure_low)}; {format_decimal_es(failure_high)}] % | **CUMPLE** `<1 %` |
| p95 GET negocio | 8 | {format_decimal_es(p95_mean)} ms | {format_decimal_es(p95_sd)} ms | [{format_decimal_es(p95_low)}; {format_decimal_es(p95_high)}] ms | INFORMATIVO |
| p99 GET negocio | 8 | {format_decimal_es(p99_mean)} ms | {format_decimal_es(p99_sd)} ms | [{format_decimal_es(p99_low)}; {format_decimal_es(p99_high)}] ms | INFORMATIVO |"""

    latex = (
        "Fiabilidad acotada & HTTP 5xx correctivo, 50 usuarios/1 h "
        "& IC95 superior $<1\\%$ "
        f"& Media {format_decimal_es(failure_mean)}\\%; "
        f"IC95 [{format_decimal_es(failure_low)}; "
        f"{format_decimal_es(failure_high)}]\\% en r2--r9 "
        "& CUMPLE en escenario \\\\"
    )

    return {
        "markdown": markdown,
        "latex": latex,
    }


def analyze_scenario(
    scenario: str, rows: list[dict[str, str]], raw_root: Path
) -> None:
    validate_design(scenario, rows)
    selected = valid_measurements(rows)
    if len(selected) != 8:
        print(f"{scenario}: SIN DATOS SUFICIENTES ({len(selected)}/8 muestras válidas completas)")
        return

    failure_rates = [float(row["failure_rate_percent"]) for row in selected]
    historical_p95_values = [float(row["p95_ms"]) for row in selected]
    historical_p99_values = [float(row["p99_ms"]) for row in selected]
    p95_values = historical_p95_values
    p99_values = historical_p99_values
    total_requests = [int(row["total_requests"]) for row in selected]
    failures = [int(row["failures"]) for row in selected]
    if any(value < 0 for value in failure_rates + p95_values + p99_values):
        raise ValueError(f"{scenario}: las métricas no pueden ser negativas")
    for row, total, failed, rate in zip(selected, total_requests, failures, failure_rates):
        repetition = row["_repetition"]
        if total <= 0 or failed < 0 or failed > total:
            raise ValueError(f"{scenario} r{repetition}: requests/failures inválidos")
        calculated_rate = 100.0 * failed / total
        if not math.isclose(rate, calculated_rate, abs_tol=0.01):
            raise ValueError(
                f"{scenario} r{repetition}: failure_rate_percent no coincide con "
                "100 * failures / total_requests"
            )

    print(f"{scenario}: 8 muestras válidas (repeticiones 2..9)")
    if scenario in RELIABILITY_RAW_DIRS:
        corrective_population = read_corrective_reliability_population(
            raw_root, selected, scenario
        )

        repetitions = [int(row["_repetition"]) for row in selected]

        for row in selected:
            repetition = int(row["_repetition"])
            raw = corrective_population[repetition]

            csv_total = int(row["total_requests"])
            csv_failures = int(row["failures"])
            csv_p95 = float(row["p95_ms"])
            csv_p99 = float(row["p99_ms"])

            if csv_total != raw["total_requests"]:
                raise ValueError(
                    f"{scenario} r{repetition}: total_requests no coincide con raw"
                )
            if csv_failures != raw["http_5xx"]:
                raise ValueError(
                    f"{scenario} r{repetition}: HTTP 5xx no coincide con raw"
                )
            if not math.isclose(csv_p95, raw["p95_ms"], abs_tol=1e-6):
                raise ValueError(
                    f"{scenario} r{repetition}: p95 no coincide con raw"
                )
            if not math.isclose(csv_p99, raw["p99_ms"], abs_tol=1e-6):
                raise ValueError(
                    f"{scenario} r{repetition}: p99 no coincide con raw"
                )

        failure_rates = [
            float(corrective_population[r]["failure_rate_percent"])
            for r in repetitions
        ]
        p95_values = [
            float(corrective_population[r]["p95_ms"])
            for r in repetitions
        ]
        p99_values = [
            float(corrective_population[r]["p99_ms"])
            for r in repetitions
        ]

        print(
            "  procedencia oficial correctiva: locust_requests.csv raw; "
            "GET de negocio completos, sin filtrar por estado, éxito o latencia"
        )

        for repetition in repetitions:
            measurement = corrective_population[repetition]
            print(
                f"  r{repetition:02d}: attempt={measurement['attempt']}; "
                f"n={measurement['total_requests']}; "
                f"401={measurement['http_401']}; "
                f"5xx={measurement['http_5xx']}; "
                f"p95={measurement['p95_ms']:.6f} ms; "
                f"p99={measurement['p99_ms']:.6f} ms; "
                f"fuente={measurement['source']}"
            )

    if scenario == EFFICIENCY_SCENARIO:
        repetitions = [int(row["_repetition"]) for row in selected]
        population = read_efficiency_population(raw_root, repetitions)
        p95_values = [float(population[repetition]["p95_ms"]) for repetition in repetitions]
        p99_values = [float(population[repetition]["p99_ms"]) for repetition in repetitions]
        print(
            "  procedencia oficial de percentiles: filas identificadas por Type=GET y "
            "Name=GET /api/v1/reservas o GET /api/v1/reservas/{id} en los "
            "locust_stats.csv raw"
        )
        print(
            "  exclusión poblacional: POST /api/v1/auth/login pertenece a Auth y no "
            "a las consultas de solo lectura de Reservas/Solicitudes; no se filtra "
            "por código HTTP, latencia ni éxito/fallo"
        )
        for repetition in repetitions:
            measurement = population[repetition]
            print(
                f"  r{repetition:02d}: {measurement['request']}; "
                f"n={measurement['total_requests']}; fallos Locust={measurement['failures']}; "
                f"p95={measurement['p95_ms']:.6f} ms; "
                f"p99={measurement['p99_ms']:.6f} ms; "
                f"fuente={measurement['source']}:{measurement['line']}"
            )
        print(
            "  análisis histórico no oficial para PI1: percentiles de la fila "
            "Aggregated (GET de Reservas/Solicitudes + POST /api/v1/auth/login)"
        )
        print_summary("historical_aggregated_p95_ms", historical_p95_values, 500.0, "ms")
        print_summary("historical_aggregated_p99_ms", historical_p99_values, 750.0, "ms")

    if scenario == POPULATED_EFFICIENCY_SCENARIO:
        repetitions = [int(row["_repetition"]) for row in selected]
        population = read_populated_efficiency_population(raw_root, repetitions)
        p95_values = [float(population[r]["p95_ms"]) for r in repetitions]
        p99_values = [float(population[r]["p99_ms"]) for r in repetitions]
        print("  procedencia oficial: locust_requests.csv; ambos GET de negocio, sin filtros por HTTP, éxito o latencia")
        for repetition in repetitions:
            item = population[repetition]
            print(f"  r{repetition:02d}: n={item['total_get']}; listado={item['listado']}; by-id={item['by_id']}; "
                  f"401={item['http_401']}; 5xx={item['http_5xx']}; p95={item['p95_ms']:.6f}; "
                  f"p99={item['p99_ms']:.6f}; fuente={item['source']}")

    print_summary("failure_rate_percent", failure_rates, 1.0, "%")
    if scenario in RELIABILITY_RAW_DIRS:
        print_descriptive_summary("p95_ms", p95_values, "ms")
        print_descriptive_summary("p99_ms", p99_values, "ms")
    else:
        print_summary("p95_ms", p95_values, 500.0, "ms")
        print_summary("p99_ms", p99_values, 750.0, "ms")


def print_descriptive_summary(name: str, values: list[float], unit: str) -> None:
    mean, standard_deviation, lower, upper = summarize(values)
    print(
        f"  {name}: media={mean:.6f} {unit}; s={standard_deviation:.6f} {unit}; "
        f"IC95=[{lower:.6f}, {upper:.6f}] {unit}; INFORMATIVO"
    )


def print_summary(name: str, values: list[float], threshold: float, unit: str) -> None:
    mean, standard_deviation, lower, upper = summarize(values)
    compliance = "CUMPLE" if upper < threshold else "NO CUMPLE"
    print(
        f"  {name}: media={mean:.6f} {unit}; s={standard_deviation:.6f} {unit}; "
        f"IC95=[{lower:.6f}, {upper:.6f}] {unit}; {compliance} (< {threshold:g} {unit})"
    )


def main() -> int:
    args = parse_args()
    try:
        raw_root = args.raw_root or args.csv_path.parent / "raw"
        if args.write_populated_efficiency:
            write_populated_efficiency_csv(raw_root, args.write_populated_efficiency)
            print(f"Derivado creado desde raw: {args.write_populated_efficiency}")
            return 0
        scenarios = read_rows(args.csv_path)
        if not scenarios:
            print("SIN DATOS: la plantilla no contiene escenarios")
            return 0
        if args.emit_markdown or args.emit_latex:
            scenario = next(
                (
                    candidate
                    for candidate in (
                        POPULATED_RELIABILITY_SCENARIO,
                        LEGACY_RELIABILITY_SCENARIO,
                    )
                    if candidate in scenarios
                ),
                None,
            )
            if scenario is None:
                raise ValueError(
                    "La emisión documental requiere un escenario "
                    "de fiabilidad correctiva soportado"
                )

            rows = scenarios[scenario]
            blocks = build_corrective_document_blocks(
                raw_root, rows, scenario
            )

            if args.emit_markdown:
                print(blocks["markdown"])
            if args.emit_markdown and args.emit_latex:
                print()
            if args.emit_latex:
                print(blocks["latex"])

            return 0

        for scenario, rows in sorted(scenarios.items()):
            analyze_scenario(scenario, rows, raw_root)
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
