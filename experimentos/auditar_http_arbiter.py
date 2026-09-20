#!/usr/bin/env python3
"""Deriva el censo HTTP ARBITER directamente de los manifiestos raw."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
import math
from pathlib import Path
import re
from typing import Any, Iterable


CENTRAL_REPETITIONS = range(2, 10)
COMPARISON_SCENARIOS = ("esc2", "esc3")
STRATEGIES = ("s0", "s1", "s2", "s3", "s4")
CAMPAIGN_CELLS = (("esc1", "production"),) + tuple(
    (scenario, strategy) for scenario in COMPARISON_SCENARIOS for strategy in STRATEGIES
) + (("esc4", "s3"), ("esc4", "s4"))


def raw_runs(raw: Path) -> Iterable[dict[str, Any]]:
    """Lee únicamente los manifiestos JSON de corrida, no resúmenes derivados."""
    for path in sorted(raw.glob("*.json")):
        yield json.loads(path.read_text(encoding="utf-8"))


def request_status(record: dict[str, Any]) -> int:
    """Recupera el HTTP preservado; una respuesta normal del endpoint es 200."""
    allocation = record.get("allocation") or {}
    response = allocation.get("backend_response") or {}
    if "httpStatus" in response:
        return int(response["httpStatus"])
    if allocation.get("status") == "HTTP_ERROR":
        raise ValueError("HTTP_ERROR sin httpStatus preservado")
    return 200


def nominal_statuses(raw: Path, run: dict[str, Any]) -> Counter:
    """Esc-1 conserva CSV Locust, no eventos REQUEST dentro del JSON.

    El harness marca como fallo cualquier respuesta distinta de 200. Solo se
    infieren los 200 restantes si todos los fallos tienen código preservado.
    """
    directory = raw / run["run_id"]
    with (directory / "locust_stats.csv").open(encoding="utf-8", newline="") as stream:
        rows = [row for row in csv.DictReader(stream) if row["Type"] == "GET"]
    if len(rows) != 1 or rows[0]["Name"] != "GET /api/v1/reservas":
        raise ValueError(f"{directory}: población GET inesperada")
    total, failed = int(rows[0]["Request Count"]), int(rows[0]["Failure Count"])
    if not 0 <= failed <= total or total == 0:
        raise ValueError(f"{directory}: conteos inválidos")
    codes = Counter()
    with (directory / "locust_failures.csv").open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["Method"] != "GET":
                continue
            match = re.fullmatch(r"CatchResponseError\('HTTP esperado 200, recibido (\d{3})'\)", row["Error"])
            if row["Name"] != rows[0]["Name"] or not match:
                raise ValueError(f"{directory}: fallo GET sin código HTTP clasificable")
            code, count = int(match[1]), int(row["Occurrences"])
            if code == 200 or not 100 <= code <= 599 or count <= 0:
                raise ValueError(f"{directory}: fallo HTTP inválido")
            codes[code] += count
    if sum(codes.values()) != failed:
        raise ValueError(f"{directory}: failures no coincide con el detalle HTTP")
    codes[200] += total - failed
    return codes


def campaign_census(raw: Path) -> list[dict[str, Any]]:
    """Censo r2-r9, incluidas las corridas nominales fallidas; exige 104 celdas."""
    rows = []
    seen = set()
    for run in raw_runs(raw):
        repetition = int(run["repetition"])
        if repetition not in CENTRAL_REPETITIONS:
            continue
        cell = (run["scenario"], run["strategy"])
        key = (*cell, repetition)
        if cell not in CAMPAIGN_CELLS or key in seen:
            raise ValueError(f"Corrida inesperada o duplicada: {key}")
        seen.add(key)
        if run["scenario"] == "esc1":
            codes = nominal_statuses(raw, run)
        else:
            codes = Counter(request_status(record) for record in run["records"]
                            if record.get("type") == "REQUEST")
        if not sum(codes.values()):
            raise ValueError(f"{run['run_id']}: no hay solicitudes")
        counts = {"requests": sum(codes.values()), "500": codes[500]}
        for family in (2, 4, 5):
            counts[f"{family}xx"] = sum(n for code, n in codes.items() if code // 100 == family)
        counts["other"] = counts["requests"] - sum(counts[f"{f}xx"] for f in (2, 4, 5))
        rows.append({"scenario": cell[0], "strategy": cell[1], "repetition": repetition,
                     **counts})
    expected = {(*cell, rep) for cell in CAMPAIGN_CELLS for rep in CENTRAL_REPETITIONS}
    if seen != expected:
        raise ValueError(f"Faltan corridas centrales: {sorted(expected - seen)}")
    result = []
    for scenario, strategy in CAMPAIGN_CELLS:
        repetitions = sorted((r for r in rows if (r["scenario"], r["strategy"]) == (scenario, strategy)),
                             key=lambda r: r["repetition"])
        counts = {key: sum(r[key] for r in repetitions)
                  for key in ("requests", "2xx", "4xx", "5xx", "500", "other")}
        errors = counts["requests"] - counts["2xx"]
        result.append({"scenario": scenario, "strategy": strategy, **counts,
                       "errors": errors, "error_percentage": 100 * errors / counts["requests"],
                       "repetitions": repetitions})
    return result


def check_run_latency(run: dict[str, Any], summary: dict[str, Any]) -> None:
    """Contrasta timestamps, latencias y media publicada sin excluir HTTP 500."""
    requests = [r for r in run["records"] if r.get("type") == "REQUEST"]
    if not requests or summary["requests"] != len(requests):
        raise ValueError(f"{run['run_id']}: número de REQUEST inconsistente")
    for record in requests:
        latency = float(record["latency_ms"])
        elapsed = (record["received_ns"] - record["sent_ns"]) / 1_000_000
        if not math.isfinite(latency) or latency < 0 or latency != elapsed:
            raise ValueError(f"{run['run_id']}: latencia distinta de timestamps")
    mean = sum(float(r["latency_ms"]) for r in requests) / len(requests)
    if not math.isclose(mean, summary["latency_ms"], rel_tol=0, abs_tol=1e-9):
        raise ValueError(f"{run['run_id']}: media de latencia distinta del resumen")


def check_summary(raw: Path, path: Path) -> None:
    summaries = json.loads(path.read_text(encoding="utf-8"))
    indexed = {r["run_id"]: r for r in summaries}
    runs = list(raw_runs(raw))
    if len(indexed) != len(summaries) or set(indexed) != {r["run_id"] for r in runs}:
        raise ValueError("El resumen no contiene exactamente las corridas RAW")
    for run in runs:
        if run["scenario"] != "esc1":
            check_run_latency(run, indexed[run["run_id"]])


def latex_census_row(row: dict[str, Any]) -> str:
    def number(value: int) -> str:
        return f"{value:,}".replace(",", r"\,")
    percentage = f"{row['error_percentage']:.4f}".replace(".", ",") if row["errors"] else "0"
    strategy = "Producción" if row["strategy"] == "production" else row["strategy"].upper()
    values = [row["scenario"][-1], strategy] + [number(row[k]) for k in ("requests", "2xx", "4xx", "5xx")]
    return " & ".join(values + [percentage + r"\% \\"])


def check_manuscript(rows: list[dict[str, Any]], path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for row in rows:
        if latex_census_row(row) not in text:
            raise ValueError(f"El manuscrito difiere del censo: {row['scenario']}/{row['strategy']}")


def central_http_census(raw: Path) -> dict[tuple[str, str], Counter]:
    """Cuenta la población r2-r9 usada por Esc-2/Esc-3 en las comparaciones."""
    result = {(scenario, strategy): Counter()
              for scenario in COMPARISON_SCENARIOS for strategy in STRATEGIES}
    for run in raw_runs(raw):
        scenario = run.get("scenario")
        strategy = run.get("strategy")
        repetition = int(run.get("repetition", 0))
        if scenario not in COMPARISON_SCENARIOS or repetition not in CENTRAL_REPETITIONS:
            continue
        key = (scenario, strategy)
        if key not in result:
            raise ValueError(f"Estrategia inesperada en raw: {key}")
        for record in run.get("records", []):
            if record.get("type") != "REQUEST":
                continue
            code = request_status(record)
            result[key]["requests"] += 1
            if 200 <= code < 300:
                result[key]["2xx"] += 1
            elif 400 <= code < 500:
                result[key]["4xx"] += 1
            elif 500 <= code < 600:
                result[key]["5xx"] += 1
            else:
                result[key]["other"] += 1
    return result


def rendered_census(raw: Path) -> list[dict[str, Any]]:
    rows = []
    for (scenario, strategy), counts in central_http_census(raw).items():
        errors = counts["4xx"] + counts["5xx"] + counts["other"]
        rows.append({"scenario": scenario, "strategy": strategy,
                     "requests": counts["requests"], "2xx": counts["2xx"],
                     "4xx": counts["4xx"], "5xx": counts["5xx"],
                     "other": counts["other"],
                     "errors": errors,
                     "error_percentage": 100 * errors / counts["requests"]})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("--all-scenarios", action="store_true", help="Incluye Esc-1 y Esc-4 y detalle r2-r9")
    parser.add_argument("--check-summary", type=Path, help="Comprueba latencias RAW contra runs.json")
    parser.add_argument("--check-manuscript", type=Path, help="Contrasta las 13 filas HTTP del manuscrito")
    args = parser.parse_args()
    try:
        rows = campaign_census(args.raw) if args.all_scenarios or args.check_manuscript else rendered_census(args.raw)
        if args.check_summary:
            check_summary(args.raw, args.check_summary)
        if args.check_manuscript:
            check_manuscript(rows, args.check_manuscript)
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    except (OSError, ValueError, KeyError) as error:
        print(f"ERROR: {error}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
