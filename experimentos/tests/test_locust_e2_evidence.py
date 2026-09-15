import csv
import importlib.util
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


class Hook:
    def add_listener(self, function):
        return function


fake_locust = types.ModuleType("locust")
fake_locust.events = types.SimpleNamespace(
    test_start=Hook(), request=Hook(), test_stop=Hook()
)
fake_base = types.ModuleType("locustfile")
fake_base.ReservasUser = object

MODULE_PATH = Path(__file__).parents[2] / "tests" / "load" / "locustfile_e2_correctiva.py"
SPEC = importlib.util.spec_from_file_location("scli_e2_evidence_under_test", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
with patch.dict(sys.modules, {"locust": fake_locust, "locustfile": fake_base}):
    SPEC.loader.exec_module(module)


class Response:
    def __init__(self, status_code: int):
        self.status_code = status_code


class CorrectiveRequestEvidenceTest(unittest.TestCase):
    def test_records_only_metadata_without_headers_bodies_or_tokens(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "locust_requests.csv"
            with patch.dict(os.environ, {"LOCUST_REQUEST_LOG": str(target)}):
                module.start_request_evidence(None)
                module.record_request(
                    "GET",
                    "GET /api/v1/reservas",
                    12.5,
                    123,
                    response=Response(500),
                    exception=RuntimeError("HTTP esperado 200, recibido 500"),
                )
                module.stop_request_evidence(None)

            with target.open(encoding="utf-8", newline="") as stream:
                row = next(csv.DictReader(stream))
            self.assertEqual("GET /api/v1/reservas", row["name"])
            self.assertEqual("500", row["status_code"])
            self.assertEqual("failure", row["outcome"])
            content = target.read_text(encoding="utf-8")
            self.assertNotIn("Authorization", content)
            self.assertNotIn("accessToken", content)
            self.assertNotIn("refreshToken", content)


    def test_writes_exact_final_locust_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            request_log = Path(temporary) / "locust_requests.csv"
            final_stats = Path(temporary) / "locust-final-stats.json"

            entry = types.SimpleNamespace(
                method="GET",
                name="GET /api/v1/reservas",
                num_requests=101,
                num_failures=0,
            )
            environment = types.SimpleNamespace(
                stats=types.SimpleNamespace(entries={("reservas", "GET"): entry})
            )

            with patch.dict(
                os.environ,
                {
                    "LOCUST_REQUEST_LOG": str(request_log),
                    "LOCUST_FINAL_STATS": str(final_stats),
                },
            ):
                module.start_request_evidence(environment)
                module.stop_request_evidence(environment)

            payload = json.loads(final_stats.read_text(encoding="utf-8"))
            self.assertEqual(1, len(payload["entries"]))
            self.assertEqual(101, payload["entries"][0]["request_count"])
            self.assertEqual(
                "GET /api/v1/reservas",
                payload["entries"][0]["name"],
            )


if __name__ == "__main__":
    unittest.main()
