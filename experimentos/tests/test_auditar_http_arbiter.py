from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


EXPERIMENTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXPERIMENTS))

from auditar_http_arbiter import (  # noqa: E402
    central_http_census,
    raw_runs,
    rendered_census,
    request_status,
)


RAW = EXPERIMENTS / "resultados" / "arbiter" / "campaign" / "raw"
SUMMARY = EXPERIMENTS / "resultados" / "arbiter" / "campaign" / "summary" / "runs.json"


class ArbiterHttpEvidenceTest(unittest.TestCase):
    def test_central_census_is_derived_from_the_ten_raw_cells(self):
        expected = {
            ("esc2", "s0"): (400, 400, 0, 0),
            ("esc2", "s1"): (400, 400, 0, 0),
            ("esc2", "s2"): (400, 348, 0, 52),
            ("esc2", "s3"): (400, 400, 0, 0),
            ("esc2", "s4"): (400, 396, 0, 4),
            ("esc3", "s0"): (1600, 1586, 0, 14),
            ("esc3", "s1"): (1600, 1173, 0, 427),
            ("esc3", "s2"): (1600, 1381, 0, 219),
            ("esc3", "s3"): (1600, 1600, 0, 0),
            ("esc3", "s4"): (1600, 1368, 0, 232),
        }
        census = central_http_census(RAW)
        self.assertEqual(set(census), set(expected))
        for key, values in expected.items():
            counts = census[key]
            self.assertEqual(
                (counts["requests"], counts["2xx"], counts["4xx"], counts["5xx"]),
                values,
                key,
            )
            self.assertEqual(counts["other"], 0, key)
        percentages = {(row["scenario"], row["strategy"]): row["error_percentage"]
                       for row in rendered_census(RAW)}
        self.assertEqual(percentages, {
            ("esc2", "s0"): 0.0,
            ("esc2", "s1"): 0.0,
            ("esc2", "s2"): 13.0,
            ("esc2", "s3"): 0.0,
            ("esc2", "s4"): 1.0,
            ("esc3", "s0"): 0.875,
            ("esc3", "s1"): 26.6875,
            ("esc3", "s2"): 13.6875,
            ("esc3", "s3"): 0.0,
            ("esc3", "s4"): 14.5,
        })

    def test_http_errors_retain_latency_and_are_in_run_latency_means(self):
        summaries = {row["run_id"]: row for row in
                     json.loads(SUMMARY.read_text(encoding="utf-8"))}
        errors = 0
        central_requests = 0
        for run in raw_runs(RAW):
            if run.get("scenario") not in {"esc2", "esc3"} \
                    or not 2 <= int(run["repetition"]) <= 9:
                continue
            requests = [row for row in run["records"] if row.get("type") == "REQUEST"]
            central_requests += len(requests)
            observed_mean = sum(float(row["latency_ms"]) for row in requests) / len(requests)
            self.assertAlmostEqual(
                observed_mean,
                summaries[run["run_id"]]["latency_ms"],
                delta=1e-9,
            )
            for row in requests:
                self.assertIsInstance(row.get("sent_ns"), int)
                self.assertIsInstance(row.get("received_ns"), int)
                self.assertIsInstance(row.get("latency_ms"), (int, float))
                self.assertEqual(
                    row["latency_ms"],
                    (row["received_ns"] - row["sent_ns"]) / 1_000_000,
                )
                if request_status(row) >= 400:
                    errors += 1
                    self.assertEqual(row["allocation"]["status"], "HTTP_ERROR")
        self.assertEqual(central_requests, 10_000)
        self.assertEqual(errors, 948)


if __name__ == "__main__":
    unittest.main()
