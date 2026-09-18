"""Analiza un lote real del protocolo 1.1; nunca genera observaciones."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path


def summarize(payload: dict, config: dict) -> tuple[list[dict], dict]:
    records = payload["results"]
    if not records:
        raise ValueError("Evidencia experimental pendiente de ejecución real")
    levels = config["execution"]["parallelism_levels"]
    repetitions = config["execution"]["measured_iterations"]
    if len(set(levels)) < 5 or 1 not in levels or repetitions < 2:
        raise ValueError("Se requieren cinco grados, Spark(1) y varias repeticiones")
    groups = defaultdict(list)
    identities = set()
    environments = set()
    rows = set()
    run_ids = set()
    for record in records:
        if record["protocol_version"] != "1.1":
            raise ValueError("El lote no pertenece al protocolo 1.1")
        if record["status"] != "completed":
            raise ValueError("Lote con fallos: no se excluyen silenciosamente")
        if record["run_id"] in run_ids:
            raise ValueError("run_id duplicado")
        run_ids.add(record["run_id"])
        identities.add((record["batch_id"], record["dataset_id"], record["dataset_snapshot_id"]))
        environments.add(json.dumps(record["environment"], sort_keys=True))
        rows.add(record["rows_processed"])
        if not record["dataset_snapshot_id"] or not record["started_at"]:
            raise ValueError("Falta procedencia del conjunto de datos")
        duration = record["duration_ms"]
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError("Duración no válida")
        groups[(record["treatment"], record["parallelism"], record["warmup"])].append(record)
    if len(identities) != 1 or len(environments) != 1 or len(rows) != 1 or min(rows) <= 0:
        raise ValueError("Lote mezclado, entorno distinto o filas incompatibles/vacías")
    identity = next(iter(identities))
    if identity != (config["batch_id"], config["dataset"]["id"], config["dataset"]["snapshot_id"]):
        raise ValueError("La configuración no corresponde al lote")
    treatments = [("pandas-baseline", 1)] + [("pyspark-pipeline", n) for n in levels]
    expected = set()
    for warmup, count in ((False, repetitions), (True, config["execution"]["warmup_iterations"])):
        for treatment, n in treatments:
            if count == 0:
                continue
            key = (treatment, n, warmup)
            expected.add(key)
            group = groups[key]
            if len(group) != count or {r["iteration"] for r in group} != set(range(1, count + 1)):
                raise ValueError("Lote incompleto o repeticiones duplicadas")
    if set(groups) != expected:
        raise ValueError("Tratamientos o grados inesperados")
    means = {key[:2]: statistics.fmean(r["duration_ms"] for r in group)
             for key, group in groups.items() if not key[2]}
    pandas_time = means[("pandas-baseline", 1)]
    spark_time = means[("pyspark-pipeline", 1)]
    # Least squares on T(N)/T(1) = f + (1-f)/N, constrained to 0 <= f <= 1.
    numerator = sum((1 - 1/n) * (means[("pyspark-pipeline", n)] / spark_time - 1/n)
                    for n in levels if n > 1)
    denominator = sum((1 - 1/n)**2 for n in levels if n > 1)
    unconstrained = numerator / denominator
    serial = max(0.0, min(1.0, unconstrained))
    summary = []
    for treatment, n in treatments:
        mean = means[(treatment, n)]
        spark = treatment == "pyspark-pipeline"
        summary.append({
            "treatment": treatment, "parallelism": n, "repetitions": repetitions,
            "rows_processed": next(iter(rows)), "mean_ms": mean,
            "stddev_ms": statistics.stdev(r["duration_ms"] for r in groups[(treatment, n, False)]),
            "speedup_vs_pandas": pandas_time / mean,
            "speedup_vs_spark1": spark_time / mean if spark else None,
            "efficiency_vs_spark1": spark_time / mean / n if spark else None,
            "amdahl_speedup": 1 / (serial + (1-serial)/n) if spark else None,
        })
    fit = {"serial_fraction": serial, "unconstrained_serial_fraction": unconstrained,
           "boundary_fit": serial != unconstrained,
           "rmse_normalized_time": math.sqrt(statistics.fmean(
               (means[("pyspark-pipeline", n)] / spark_time - (serial + (1-serial)/n))**2
               for n in levels)),
           "method": "OLS T(N)/T(1), f constrained to [0,1]; Spark(1) reference",
           "limitation": "Effective serial fraction includes startup, JDBC, I/O and overhead; not code fraction"}
    return summary, fit


def analyze(source: Path, output: Path) -> None:
    config_path = source.with_name("config.json")
    from verify_equivalence import require_report
    config = json.loads(config_path.read_text(encoding="utf-8"))
    report = json.loads(source.with_name("equivalence.json").read_text(encoding="utf-8"))
    require_report(report, config, config["environment"], check_sources=False)
    if report["source_sha256"] != config["equivalence_source_sha256"]:
        raise ValueError("Equivalencia y codigo del lote no coinciden")
    execution = config["execution"]
    if (execution["parallelism_levels"] != [1, 2, 4, 6, 8] or
            execution["measured_iterations"] != 5 or execution["warmup_iterations"] != 1):
        raise ValueError("El lote no cumple el protocolo requerido")
    payload = json.loads(source.read_text(encoding="utf-8"))
    if any(r["rows_processed"] != report["rows"] or r["environment"] != report["environment"]
           for r in payload["results"]):
        raise ValueError("Las observaciones no corresponden a la equivalencia")
    summary, fit = summarize(payload, config)
    # Load plotting dependency before creating any output.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output.mkdir(parents=True, exist_ok=False)
    with (output / "resumen.csv").open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    provenance = {"source": str(source), "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                  "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
                  "amdahl": fit, "summary": summary}
    (output / "resumen.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    spark = sorted((r for r in summary if r["treatment"] == "pyspark-pipeline"),
                   key=lambda r: r["parallelism"])
    fig, ax = plt.subplots()
    for field, label in (("speedup_vs_pandas", "pandas / Spark(N)"),
                         ("speedup_vs_spark1", "Spark(1) / Spark(N)"),
                         ("amdahl_speedup", "Amdahl ajustado a Spark")):
        ax.plot([r["parallelism"] for r in spark], [r[field] for r in spark], "o-", label=label)
    ax.set(xlabel="Paralelismo local [N]", ylabel="Speedup", xticks=[r["parallelism"] for r in spark])
    ax.legend()
    ax.grid(True)
    fig.tight_layout()
    fig.savefig(output / "speedup.png", dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    analyze(args.input, args.output)
