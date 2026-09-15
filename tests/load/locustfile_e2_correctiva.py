"""Campaña E2 correctiva: mismas tareas y evidencia temporal por request."""

from __future__ import annotations

import csv
import json
import os
import time
from pathlib import Path
from typing import Any, TextIO

from locust import events

from locustfile import ReservasUser


_stream: TextIO | None = None
_writer: csv.writer | None = None
_rows_since_flush = 0


@events.test_start.add_listener
def start_request_evidence(environment: Any, **kwargs: Any) -> None:
    del environment, kwargs
    global _stream, _writer, _rows_since_flush
    destination = os.environ.get("LOCUST_REQUEST_LOG")
    if not destination:
        raise RuntimeError("LOCUST_REQUEST_LOG es obligatorio para la campaña E2 correctiva")
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    _stream = path.open("x", encoding="utf-8", newline="")
    _writer = csv.writer(_stream)
    _writer.writerow(
        (
            "timestamp_epoch",
            "request_type",
            "name",
            "response_time_ms",
            "status_code",
            "outcome",
            "error",
        )
    )
    _stream.flush()
    _rows_since_flush = 0


@events.request.add_listener
def record_request(
    request_type: str,
    name: str,
    response_time: float,
    response_length: int,
    response: Any = None,
    context: Any = None,
    exception: BaseException | None = None,
    **kwargs: Any,
) -> None:
    del response_length, context, kwargs
    global _rows_since_flush
    if _writer is None or _stream is None:
        return
    status_code = getattr(response, "status_code", 0) if response is not None else 0
    _writer.writerow(
        (
            f"{time.time():.6f}",
            request_type,
            name,
            f"{response_time:.6f}",
            status_code,
            "failure" if exception is not None else "success",
            str(exception) if exception is not None else "",
        )
    )
    _rows_since_flush += 1
    if _rows_since_flush >= 100:
        _stream.flush()
        _rows_since_flush = 0


@events.test_stop.add_listener
def stop_request_evidence(environment: Any, **kwargs: Any) -> None:
    del kwargs
    global _stream, _writer, _rows_since_flush
    if _stream is not None:
        _stream.close()

    final_stats = os.environ.get("LOCUST_FINAL_STATS")
    if final_stats:
        entries = sorted(
            (
                {
                    "request_type": str(entry.method),
                    "name": str(entry.name),
                    "request_count": int(entry.num_requests),
                    "failure_count": int(entry.num_failures),
                }
                for entry in environment.stats.entries.values()
            ),
            key=lambda row: (row["request_type"], row["name"]),
        )
        Path(final_stats).write_text(
            json.dumps({"entries": entries}, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    _stream = None
    _writer = None
    _rows_since_flush = 0
