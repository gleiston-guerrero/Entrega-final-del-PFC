"""Prepare and validate a real CockroachDB snapshot; never measure performance."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlsplit, parse_qs, unquote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experimentos"))
sys.path.insert(0, str(ROOT / "spark"))
if __name__ == "__main__":
    sys.modules["prepare_local"] = sys.modules[__name__]
from snapshot import TABLES, source_sql

EXPECTED = dict(zip(TABLES, (100000, 100000, 200000, 10000, 1)))
REQUIRED = ("RESERVAS_DB_USERNAME", "RESERVAS_DB_PASSWORD", "RESERVAS_JDBC_URL",
            "RESERVAS_PANDAS_URL", "POSTGRES_JDBC_JAR")


class LocalValidationError(ValueError):
    """Only controlled messages without driver errors or connection strings."""


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode()).hexdigest()


def connection_identity():
    from sqlalchemy.engine import make_url
    if any(not os.environ.get(key) for key in REQUIRED):
        raise LocalValidationError("Faltan variables requeridas: " + ", ".join(
            key for key in REQUIRED if not os.environ.get(key)))
    jar = Path(os.environ["POSTGRES_JDBC_JAR"])
    if not jar.is_file():
        raise LocalValidationError("POSTGRES_JDBC_JAR no existe")
    jdbc = os.environ["RESERVAS_JDBC_URL"]
    if not jdbc.startswith("jdbc:postgresql://"):
        raise LocalValidationError("Se requiere JDBC PostgreSQL")
    j = urlsplit(jdbc[5:])
    p = make_url(os.environ["RESERVAS_PANDAS_URL"])
    # Reject connection overrides and credentials in JDBC; properties supply credentials.
    if j.username or j.password or set(parse_qs(j.query)) - {"sslmode"}:
        raise LocalValidationError("JDBC solo admite sslmode; credenciales en variables separadas")
    if set(p.query) - {"sslmode"} or p.drivername not in {"postgresql+psycopg", "cockroachdb+psycopg"}:
        raise LocalValidationError("Pandas requiere postgresql+psycopg y solo sslmode")
    if p.username not in (None, os.environ["RESERVAS_DB_USERNAME"]) or p.password not in (
            None, os.environ["RESERVAS_DB_PASSWORD"]):
        raise LocalValidationError("Credenciales pandas distintas de las variables separadas")
    left = (j.hostname, j.port or 5432, unquote(j.path.lstrip("/")))
    right = (p.host, p.port or 5432, p.database)
    if left != right or not left[0] or not left[2]:
        raise LocalValidationError("pandas y JDBC deben usar exactamente host, puerto y base iguales")
    if parse_qs(j.query).get("sslmode", ["prefer"]) != [p.query.get("sslmode", "prefer")]:
        raise LocalValidationError("sslmode debe coincidir")
    return {"host": left[0], "port": left[1], "database": left[2], "schema": "public"}


def inventory(timestamp=None):
    from sqlalchemy import text
    from baseline import crear_motor, PandasDbConfig
    identity = connection_identity()
    engine = crear_motor(PandasDbConfig.desde_entorno())
    try:
        with engine.connect() as conn:
            conn.execute(text("SET TIME ZONE 'UTC'"))
            timestamp = timestamp or str(conn.execute(text("SELECT cluster_logical_timestamp()::STRING")).scalar_one())
            tables = {}
            for table in TABLES:
                # Full-content fingerprint detects edits that preserve row counts.
                result = conn.execute(
                    text(source_sql(table, timestamp) + " ORDER BY id"))
                fingerprint = hashlib.sha256()
                count = 0
                columns = list(result.keys())
                for row in result:
                    fingerprint.update(json.dumps([None if v is None else str(v) for v in row],
                                                  ensure_ascii=False, separators=(",", ":")).encode())
                    fingerprint.update(b"\n")
                    count += 1
                if count != EXPECTED[table]:
                    raise LocalValidationError(f"Conteo inesperado en {table}: {count}; esperado {EXPECTED[table]}")
                tables[table] = {"rows": count, "columns": columns, "content_sha256": fingerprint.hexdigest()}
        data = {"identity": identity, "tables": tables, "total_rows": sum(EXPECTED.values()),
                "seeds_sha256": hashlib.sha256((ROOT / "db/seeds.sql").read_bytes()).hexdigest()}
        return {**data, "snapshot_id": "sha256:" + digest(data), "read_timestamp": timestamp}
    finally:
        engine.dispose()


def validate(config, output=None):
    import psutil
    from run_comparison import environment_metadata
    connection_identity()
    if (psutil.cpu_count(logical=True) or 0) < 8:
        raise LocalValidationError("Se requieren al menos 8 CPU logicas")
    execution = config["execution"]
    if (execution["parallelism_levels"] != [1, 2, 4, 6, 8] or
            execution["warmup_iterations"] != 1 or execution["measured_iterations"] != 5):
        raise LocalValidationError("Protocolo requerido: N=1,2,4,6,8; warmup=1; repeticiones=5")
    if output is not None and output.exists():
        raise LocalValidationError("El directorio de salida ya existe; use uno nuevo")
    environment = environment_metadata()
    actual = inventory(config["dataset"]["inventory"]["read_timestamp"])
    if actual != config["dataset"]["inventory"] or actual["snapshot_id"] != config["dataset"]["snapshot_id"]:
        raise LocalValidationError("El snapshot/config no coincide")
    os.environ["RESERVAS_SNAPSHOT_TIMESTAMP"] = actual["read_timestamp"]
    return environment


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False)


def report_error(error, stream=None):
    """Keep real traceback locations without exposing driver messages or locals."""
    stream = stream if stream is not None else sys.stderr
    seen = set()

    def report(exc):
        if id(exc) in seen:
            return
        seen.add(id(exc))
        previous = exc.__cause__
        if previous is None and not exc.__suppress_context__:
            previous = exc.__context__
        if previous is not None:
            report(previous)
            print("Excepcion encadenada:", file=stream)
        print("Traceback (sin mensajes externos, codigo fuente ni variables locales):", file=stream)
        tb = exc.__traceback__
        while tb is not None:
            code = tb.tb_frame.f_code
            print(f'  File "{code.co_filename}", line {tb.tb_lineno}, in {code.co_name}',
                  file=stream)
            tb = tb.tb_next
        print(type(exc).__name__, file=stream)
        if isinstance(exc, LocalValidationError):
            print(str(exc), file=stream)

    report(error)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "validate"])
    parser.add_argument("--config", type=Path, default=ROOT / "experimentos/experiment-config.local.json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.action == "prepare":
        if args.config.exists():
            raise LocalValidationError("La configuracion local ya existe")
        config = json.loads((ROOT / "experimentos/experiment-config.json").read_text(encoding="utf-8"))
        data = inventory()
        config["dataset"].update(snapshot_id=data["snapshot_id"], inventory=data)
        write_json(args.config, config)
        print("Configuracion local e inventario creados; total: 410001 filas")
    else:
        from run_comparison import load_config, utc_now
        if args.output is None:
            raise LocalValidationError("validate requiere --output con un directorio nuevo")
        config = load_config(args.config)
        environment = validate(config, args.output)
        write_json(args.output / "validation.json", {
            "status": "validated",
            "snapshot_id": config["dataset"]["snapshot_id"],
            "inventory": config["dataset"]["inventory"],
            "environment": environment,
            "validated_at": utc_now(),
        })
        print("Prevalidacion correcta; equivalencia y benchmark pendientes")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        report_error(error)
        raise SystemExit(1)
