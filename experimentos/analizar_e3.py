"""Analiza las tres campañas E3 sin modificar evidencia raw."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from e3_instrumental import atomic_json, student_n3, wilson


MOTORS = ("chromium", "firefox", "webkit")
COMPONENTS = ("auth", "usuarios", "academico", "reservas", "gateway", "web", "android")
BACKEND_COMPONENTS = ("auth", "usuarios", "academico", "reservas", "gateway")
MAINTENANCE_THRESHOLDS = {
    **{(name, "lines"): 70.0 for name in ("auth", "usuarios", "academico", "gateway", "web", "android")},
    ("reservas", "lines"): 80.0,
    ("reservas", "branch"): 48.0,
    ("web", "branches"): 70.0,
    ("web", "functions"): 70.0,
    ("web", "statements"): 70.0,
}


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=Path(__file__).parent / "resultados/raw")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def repetitions(root: Path) -> list[Path]:
    expected = [root / f"rep-{number:02d}" for number in (1, 2, 3)]
    if any(not path.is_dir() for path in expected):
        raise ValueError(f"Se requieren exactamente rep-01..rep-03 en {root}")
    extras = [path for path in root.glob("rep-*") if path not in expected]
    if extras:
        raise ValueError(f"Repeticiones no prerregistradas: {extras}")
    manifests = [json.loads((path / "manifest.json").read_text(encoding="utf-8")) for path in expected]
    if len({item.get("git_sha") for item in manifests}) != 1:
        raise ValueError(f"SHA diferente entre repeticiones de {root.name}")
    if any(not item.get("evidence_complete") for item in manifests):
        raise ValueError(f"Evidencia incompleta en {root.name}")
    return expected


def analyze_security(root: Path) -> dict[str, Any]:
    reps = repetitions(root)
    cases_by_rep: list[dict[str, dict[str, str]]] = []
    flaky = False
    for rep in reps:
        with (rep / "decisiones.csv").open(encoding="utf-8") as handle:
            current = list(csv.DictReader(handle))
        if len(current) != 7:
            raise ValueError(f"{rep} no contiene siete decisiones")
        if {row["decision_id"] for row in current} != {
            "admin_login_permitido", "admin_login_invalido_401", "reservas_sin_token_401",
            "docente_login_permitido", "docente_crea_consulta_cancela",
            "admin_piso_scope_permitido", "admin_piso_fuera_scope_403",
        }:
            raise ValueError(f"{rep} no coincide con la matriz de seguridad prerregistrada")
        cases = {row["decision_id"]: row for row in current}
        if len(cases) != len(current):
            raise ValueError(f"{rep} contiene decision_id duplicados")
        cases_by_rep.append(cases)
        flaky |= json.loads((rep / "manifest.json").read_text(encoding="utf-8")).get("flaky", False)
    baseline = cases_by_rep[0]
    compared_fields = ("expected_http", "observed_http", "assertion_pass")
    for number, cases in enumerate(cases_by_rep[1:], 2):
        if set(cases) != set(baseline):
            raise ValueError(f"rep-{number:02d} no tiene el mismo conjunto de decisiones de seguridad")
        for decision_id, row in cases.items():
            if any(row[field] != baseline[decision_id][field] for field in compared_fields):
                raise ValueError(f"rep-{number:02d} diverge en la decisión de seguridad {decision_id}")
    rows = list(baseline.values())
    correct = sum(row["assertion_pass"].lower() == "true" for row in rows)
    pairs = [list(zip(row["expected_http"].split("/"), row["observed_http"].split("/")))
             for row in rows]
    false_allowed = sum(any(expected in {"401", "403"} and observed.startswith("2")
                            for expected, observed in decision) for decision in pairs)
    false_rejected = sum(any(expected.startswith("2") and not observed.startswith("2")
                             for expected, observed in decision) for decision in pairs)
    low, high = wilson(correct, len(rows))
    passed = correct == len(rows) and false_allowed == 0 and false_rejected == 0 and not flaky
    return {"total": len(rows), "correct": correct, "proportion": correct / len(rows),
            "wilson95": [low, high], "false_allowed": false_allowed,
            "false_rejected": false_rejected, "flaky": flaky,
            "repetitions": len(reps),
            "repeatability": {"successful_repetitions": len(reps), "identical_case_set": True,
                               "identical_results": True},
            "decision": "CUMPLE" if passed else "NO CUMPLE",
            "unfavorable": [row for row in rows if row["assertion_pass"].lower() != "true"]}


def jacoco_summary(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"JaCoCo CSV vacío: {path}")
    def total(field: str) -> int:
        return sum(int(row[field]) for row in rows)
    line_missed, line_covered = total("LINE_MISSED"), total("LINE_COVERED")
    complexity_missed = total("COMPLEXITY_MISSED")
    complexity_covered = total("COMPLEXITY_COVERED")
    complexities = [int(row["COMPLEXITY_MISSED"]) + int(row["COMPLEXITY_COVERED"]) for row in rows]
    maximum = max(complexities)
    maximum_rows = [row for row, value in zip(rows, complexities) if value == maximum]
    return {
        "line_missed": line_missed, "line_covered": line_covered,
        "line_percentage": line_covered * 100 / (line_missed + line_covered),
        "complexity_missed": complexity_missed, "complexity_covered": complexity_covered,
        "complexity_total": complexity_missed + complexity_covered, "classes": len(rows),
        "complexity_mean_per_class": (complexity_missed + complexity_covered) / len(rows),
        "complexity_max_class": maximum,
        "complexity_max_classes": [f"{row['PACKAGE']}.{row['CLASS']}" for row in maximum_rows],
    }


def analyze_maintenance(root: Path) -> dict[str, Any]:
    reps = repetitions(root)
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    backend_by_rep: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rep in reps:
        with (rep / "metricas.csv").open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                grouped[(row["component"], row["metric"])].append(row)
        for component in BACKEND_COMPONENTS:
            backend_by_rep[component].append(jacoco_summary(rep / component / "report" / "jacoco.csv"))
    if {component for component, metric in grouped if metric == "lines"} != set(COMPONENTS):
        raise ValueError("Faltan componentes de mantenibilidad")
    if set(grouped) != set(MAINTENANCE_THRESHOLDS):
        raise ValueError("Las métricas de mantenibilidad difieren del prerregistro")
    metrics: list[dict[str, Any]] = []
    for (component, metric), rows in sorted(grouped.items()):
        if len(rows) != 3:
            raise ValueError(f"{component}/{metric} no tiene n=3")
        thresholds = {float(row["threshold"]) for row in rows}
        if len(thresholds) != 1:
            raise ValueError(f"Umbral variable en {component}/{metric}")
        values = [float(row["percentage"]) for row in rows]
        if component in BACKEND_COMPONENTS and metric == "lines":
            values = [item["line_percentage"] for item in backend_by_rep[component]]
        stats = student_n3(values)
        threshold = thresholds.pop()
        if threshold != MAINTENANCE_THRESHOLDS[(component, metric)]:
            raise ValueError(f"Umbral no prerregistrado en {component}/{metric}")
        commands_ok = all(int(row["exit_code"]) == 0 for row in rows)
        passed = commands_ok and stats["ci95_low"] >= threshold
        metrics.append({"component": component, "metric": metric, "n": 3,
                        "values": values,
                        **stats, "threshold": threshold, "commands_ok": commands_ok,
                        "decision": "CUMPLE" if passed else "NO CUMPLE"})
    overall = all(item["decision"] == "CUMPLE" for item in metrics)
    complexity = {}
    for component, values in backend_by_rep.items():
        if any(value != values[0] for value in values[1:]):
            raise ValueError(f"JaCoCo difiere entre repeticiones para {component}")
        complexity[component] = values[0]
    return {"metrics": metrics, "complexity": complexity, "decision": "CUMPLE" if overall else "NO CUMPLE",
            "unfavorable": [item for item in metrics if item["decision"] != "CUMPLE"]}


def analyze_compatibility(root: Path) -> dict[str, Any]:
    reps = repetitions(root)
    output: dict[str, Any] = {}
    for motor in MOTORS:
        summaries = [json.loads((rep / motor / "summary.json").read_text(encoding="utf-8")) for rep in reps]
        baseline = summaries[0]
        fields = ("total", "passed", "failed", "skipped", "flaky", "interrupted", "exit_code")
        if any(any(item[field] != baseline[field] for field in fields) for item in summaries[1:]):
            raise ValueError(f"Las repeticiones de {motor} divergen en su resumen")
        total, passed_count = baseline["total"], baseline["passed"]
        failed, skipped, flaky = baseline["failed"], baseline["skipped"], baseline["flaky"]
        if total <= 0:
            raise ValueError(f"{motor} no tiene casos elegibles")
        low, high = wilson(passed_count, total)
        passed = (passed_count == total and failed == 0 and skipped == 0 and flaky == 0
                  and baseline["interrupted"] == 0 and baseline["exit_code"] == 0)
        output[motor] = {"total": total, "passed": passed_count,
                         "failed": failed, "skipped": skipped, "flaky": flaky,
                         "proportion": passed_count / total, "wilson95": [low, high],
                         "repetitions": len(reps),
                         "repeatability": {"successful_repetitions": len(reps),
                                            "identical_summary": True,
                                            "case_identity_verifiable": False},
                         "decision": "CUMPLE" if passed else "NO CUMPLE"}
    overall = all(item["decision"] == "CUMPLE" for item in output.values())
    return {"motors": output, "decision": "CUMPLE" if overall else "NO CUMPLE",
            "unfavorable": {key: value for key, value in output.items()
                              if value["decision"] != "CUMPLE"}}


def analyze_all(raw_root: Path) -> dict[str, Any]:
    return {
        "security": analyze_security(raw_root / "e3_seguridad"),
        "maintenance": analyze_maintenance(raw_root / "e3_mantenibilidad"),
        "compatibility": analyze_compatibility(raw_root / "e3_compatibilidad"),
    }


def main() -> int:
    args = arguments()
    atomic_json(args.output, analyze_all(args.raw_root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
