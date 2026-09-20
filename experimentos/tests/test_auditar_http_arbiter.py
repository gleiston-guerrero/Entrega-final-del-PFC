from __future__ import annotations

import json
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


EXPERIMENTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXPERIMENTS))

from auditar_http_arbiter import (  # noqa: E402
    central_http_census,
    raw_runs,
    rendered_census,
    request_status,
    campaign_census,
    check_manuscript,
    check_run_latency,
    check_summary,
    nominal_statuses,
)


RAW = EXPERIMENTS / "resultados" / "arbiter" / "campaign" / "raw"
SUMMARY = EXPERIMENTS / "resultados" / "arbiter" / "campaign" / "summary" / "runs.json"


class ArbiterHttpEvidenceTest(unittest.TestCase):
    def test_complete_census_and_manuscript_use_real_evidence(self):
        rows = campaign_census(RAW)
        check_manuscript(rows, EXPERIMENTS.parent / "docs/secciones/04-observabilidad-iso.tex")
        census = {(r["scenario"], r["strategy"]): r for r in rows}
        expected = {("esc1", "production"): (58040, 57969, 71),
                    ("esc4", "s3"): (1600, 1600, 0),
                    ("esc4", "s4"): (1600, 1249, 351)}
        for key, values in expected.items():
            row = census[key]
            self.assertEqual((row["requests"], row["2xx"], row["500"]), values)
            self.assertEqual(row["4xx"], 0)
            self.assertEqual(row["other"], 0)
            self.assertEqual(row["5xx"], row["500"])
        self.assertEqual([r["500"] for r in census["esc4", "s4"]["repetitions"]],
                         [62, 52, 93, 5, 52, 5, 69, 13])
        self.assertEqual([r["500"] for r in census["esc1", "production"]["repetitions"]],
                         [0, 26, 10, 31, 0, 0, 1, 3])
        self.assertEqual(census["esc4", "s4"]["error_percentage"], 21.9375)

    def test_real_summary_includes_latency_of_all_contention_and_failure_runs(self):
        check_summary(RAW, SUMMARY)

    def test_significant_raw_latency_change_is_rejected(self):
        run = next(r for r in raw_runs(RAW) if r["scenario"] == "esc4" and r["strategy"] == "s4")
        summary = next(r for r in json.loads(SUMMARY.read_text(encoding="utf-8"))
                       if r["run_id"] == run["run_id"])
        changed = copy.deepcopy(run)
        record = next(r for r in changed["records"] if r.get("type") == "REQUEST")
        record["latency_ms"] += 100
        with self.assertRaisesRegex(ValueError, "timestamps"):
            check_run_latency(changed, summary)
        # Incluso si se altera también el timestamp, la media publicada lo detecta.
        record["received_ns"] += 100_000_000
        record["latency_ms"] = (record["received_ns"] - record["sent_ns"]) / 1_000_000
        with self.assertRaisesRegex(ValueError, "media de latencia"):
            check_run_latency(changed, summary)

    def test_missing_central_run_is_rejected(self):
        runs = list(raw_runs(RAW))
        runs = [r for r in runs if not (r["scenario"] == "esc4" and r["strategy"] == "s4"
                                      and r["repetition"] == 2)]
        with patch("auditar_http_arbiter.raw_runs", return_value=iter(runs)):
            with self.assertRaisesRegex(ValueError, "Faltan corridas"):
                campaign_census(RAW)

    def test_nominal_unclassified_or_inconsistent_failures_are_rejected(self):
        import io
        run = {"run_id": "esc1-production-r03"}
        stats = "Type,Name,Request Count,Failure Count\nGET,GET /api/v1/reservas,10,1\n"
        for detail in ("", "GET,GET /api/v1/reservas,ConnectionError,1\n"):
            with self.subTest(detail=detail):
                failures = "Method,Name,Error,Occurrences\n" + detail
                with patch.object(Path, "open", side_effect=[io.StringIO(stats), io.StringIO(failures)]):
                    with self.assertRaises(ValueError):
                        nominal_statuses(RAW, run)

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
