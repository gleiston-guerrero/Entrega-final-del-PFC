"""Compare complete materialized outputs before accepting performance evidence."""
from __future__ import annotations
import argparse
from datetime import datetime, time
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_local import ROOT, report_error, validate, write_json

COLUMNS = """reserva_id solicitud_id laboratorio_id responsable_id fecha_reserva hora_inicio
hora_fin estado_reserva codigo_reserva solicitante_id docente_id materia_id periodo_lectivo_id
numero_participantes solicitud_creada_en anio_reserva trimestre_reserva mes_reserva
participantes_laboratorio_trimestre segmento_participantes""".split()
NUMERIC = {"numero_participantes", "anio_reserva", "trimestre_reserva",
           "participantes_laboratorio_trimestre", "segmento_participantes"}
DATES = {"fecha_reserva", "solicitud_creada_en", "mes_reserva"}


def source_hashes():
    paths = ["spark/baseline.py", "spark/pipeline.py", "spark/snapshot.py",
             "spark/requirements.txt", "experimentos/verify_equivalence.py",
             "experimentos/prepare_local.py", "experimentos/run_comparison.py"]
    return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}


def normalize(frame):
    import pandas as pd
    if set(frame.columns) != set(COLUMNS):
        raise ValueError("Columnas de salida incompatibles")
    data = frame[COLUMNS].copy()
    for column in COLUMNS:
        if column in NUMERIC:
            data[column] = pd.to_numeric(data[column], errors="raise").astype("Float64")
        elif column in DATES:
            data[column] = pd.to_datetime(data[column], utc=True).astype("datetime64[us, UTC]")
        elif column in {"hora_inicio", "hora_fin"}:
            def clock(value):
                if pd.isna(value):
                    return None
                if isinstance(value, datetime):
                    value = value.time()
                elif not isinstance(value, time):
                    value = time.fromisoformat(str(value))
                return value.isoformat(timespec="microseconds")
            data[column] = data[column].map(clock).astype("string")
        else:
            data[column] = data[column].map(lambda v: None if pd.isna(v) else str(v)).astype("string")
    if data.empty or data.reserva_id.isna().any() or data.reserva_id.duplicated().any():
        raise ValueError("reserva_id vacio, nulo o duplicado")
    return data.sort_values("reserva_id").reset_index(drop=True)


def compare(left, right):
    import pandas as pd
    a, b = normalize(left), normalize(right)
    pd.testing.assert_frame_equal(a, b, check_exact=True)
    return {"rows": len(a), "columns": COLUMNS,
            "normalized_sha256": hashlib.sha256(a.to_json(orient="split", date_unit="us").encode()).hexdigest()}


def require_report(report, config, environment=None, check_sources=True):
    if (report.get("status") != "equivalent" or report.get("rows", 0) <= 0 or
            report.get("columns") != COLUMNS or
            report.get("snapshot_id") != config["dataset"]["snapshot_id"] or
            report.get("read_timestamp") != config["dataset"]["inventory"]["read_timestamp"]):
        raise ValueError("Falta equivalencia completa para este snapshot")
    checks = report.get("checks", [])
    if ([c.get("parallelism") for c in checks] != [1, 2, 4, 6, 8] or
            any(c.get("rows") != report["rows"] or c.get("columns") != COLUMNS or
                c.get("normalized_sha256") != report.get("normalized_sha256") for c in checks)):
        raise ValueError("Falta equivalencia en uno o mas grados")
    if check_sources and report.get("source_sha256") != source_hashes():
        raise ValueError("Codigo modificado desde la equivalencia")
    if environment is not None and report.get("environment") != environment:
        raise ValueError("Entorno modificado desde la equivalencia")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    from run_comparison import load_config, execute_pandas_worker, execute_spark_worker, utc_now
    import pandas as pd
    config = load_config(args.config)
    output = args.output.resolve()
    environment = validate(config, output)
    output.mkdir(parents=True, exist_ok=False)
    print("Materializando pandas", flush=True)
    execute_pandas_worker(output / "pandas.parquet")
    # Every benchmark degree must pass functional equivalence on the pinned snapshot.
    left = pd.read_parquet(output / "pandas.parquet")
    checks = []
    for n in config["execution"]["parallelism_levels"]:
        print(f"Verificando Spark N={n}", flush=True)
        target = output / f"spark-{n}.parquet"
        execute_spark_worker(target, n)
        checks.append({"parallelism": n, **compare(left, pd.read_parquet(target))})
        print(f"Equivalencia N={n}: {checks[-1]['rows']} filas correctas", flush=True)
    report = {**checks[0], "status": "equivalent", "checks": checks,
              "snapshot_id": config["dataset"]["snapshot_id"],
              "read_timestamp": config["dataset"]["inventory"]["read_timestamp"],
              "environment": environment, "source_sha256": source_hashes(), "verified_at": utc_now()}
    write_json(output / "equivalence.json", report)
    print(output / "equivalence.json")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        report_error(error)
        print(f"Equivalencia fallo ({type(error).__name__}); no aceptar resultados.", file=sys.stderr)
        raise SystemExit(1)
