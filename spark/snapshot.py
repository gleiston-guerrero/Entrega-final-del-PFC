"""Shared, secret-free snapshot SQL for both engines."""
import os
import re

TABLES = ("solicitudes_reserva", "reservas", "historial_solicitudes",
          "bloqueos_agenda", "configuraciones_reserva")


def source_sql(table, timestamp=None):
    if table not in TABLES:
        raise ValueError("Tabla no permitida")
    timestamp = timestamp or os.getenv("RESERVAS_SNAPSHOT_TIMESTAMP")
    suffix = ""
    if timestamp:
        if not re.fullmatch(r"[0-9]+\.[0-9]+", timestamp):
            raise ValueError("Timestamp HLC no valido")
        suffix = f" AS OF SYSTEM TIME '{timestamp}'"
    return f"SELECT * FROM public.{table}{suffix}"
