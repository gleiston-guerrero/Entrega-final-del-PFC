"""Reconciliación offline de los derivados publicados con la evidencia versionada."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

EXPERIMENTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXPERIMENTS))

from analizar_e3 import analyze_all, jacoco_summary
from analizar_iso25010 import (
    EXPECTED_REPETITIONS, RELIABILITY_RAW_DIRS, POPULATED_EFFICIENCY_SCENARIO,
    read_rows, read_corrective_reliability_population, read_populated_efficiency_population,
    validate_design,
    ANALYZED_REPETITIONS, POPULATED_RELIABILITY_SCENARIO, summarize,
)

RESULTS = EXPERIMENTS / "resultados"
RAW = RESULTS / "raw"
MANUSCRIPT = EXPERIMENTS.parent / "docs/secciones/04-observabilidad-iso.tex"


class RealEvidenceTest(unittest.TestCase):
    def test_both_corrective_csvs_match_all_ten_raw_repetitions(self):
        for filename in ("iso25010-correctiva.csv", "iso25010-correctiva-poblada.csv"):
            scenarios = read_rows(RESULTS / filename)
            self.assertTrue(scenarios)
            for scenario, rows in scenarios.items():
                with self.subTest(campaign=filename, scenario=scenario):
                    self.assertIn(scenario, RELIABILITY_RAW_DIRS)
                    validate_design(scenario, rows)
                    population = read_corrective_reliability_population(RAW, rows, scenario)
                    self.assertEqual(set(population), EXPECTED_REPETITIONS)
                    for row in rows:
                        observed = population[int(row["repeticion"])]
                        self.assertEqual(int(row["total_requests"]), observed["total_requests"])
                        self.assertEqual(int(row["failures"]), observed["http_5xx"])
                        for field in ("failure_rate_percent", "p95_ms", "p99_ms"):
                            self.assertAlmostEqual(float(row[field]), observed[field], delta=1e-6)
                    if scenario == POPULATED_RELIABILITY_SCENARIO:
                        self.assertEqual(sum(r["total_requests"] for r in population.values()), 895136)
                        self.assertEqual(sum(r["http_5xx"] for r in population.values()), 42)
                        self.assertEqual(sum(r["http_401"] for r in population.values()), 0)
                        selected = [population[r] for r in sorted(ANALYZED_REPETITIONS)]
                        self.assertEqual(sum(r["total_requests"] for r in selected), 716099)
                        manuscript = MANUSCRIPT.read_text(encoding="utf-8")
                        for field in ("failure_rate_percent", "p95_ms", "p99_ms"):
                            mean, _, low, high = summarize([r[field] for r in selected])
                            for value in (mean, low, high):
                                self.assertIn(f"{value:.6f}".replace(".", ","), manuscript)

    def test_populated_efficiency_csv_matches_all_ten_raw_repetitions(self):
        rows = read_rows(RESULTS / "iso25010-eficiencia-poblada.csv")[POPULATED_EFFICIENCY_SCENARIO]
        validate_design(POPULATED_EFFICIENCY_SCENARIO, rows)
        population = read_populated_efficiency_population(RAW, sorted(EXPECTED_REPETITIONS))
        for row in rows:
            with self.subTest(repetition=row["repeticion"]):
                observed = population[int(row["repeticion"])]
                self.assertEqual(int(row["total_requests"]), observed["total_get"])
                self.assertEqual(int(row["failures"]), observed["http_5xx"])
                self.assertAlmostEqual(float(row["failure_rate_percent"]),
                                       100 * observed["http_5xx"] / observed["total_get"], delta=1e-6)
                for field in ("p95_ms", "p99_ms"):
                    self.assertAlmostEqual(float(row[field]), observed[field], delta=1e-6)

    def test_canonical_backend_coverage_matches_manuscript(self):
        manuscript = MANUSCRIPT.read_text(encoding="utf-8")
        for service, label, covered, missed, threshold in (
            ("usuarios", "Usuarios", 1735, 329, 70),
            ("reservas", "Reservas", 2730, 506, 80),
        ):
            for repetition in range(1, 4):
                path = (RESULTS / "evidencia-e3-canonica/e3_mantenibilidad"
                        / f"rep-{repetition:02d}" / service / "report/jacoco.csv")
                with self.subTest(source=str(path)):
                    metrics = jacoco_summary(path)
                    self.assertEqual((metrics["line_covered"], metrics["line_missed"]), (covered, missed))
                    percentage = f"{metrics['line_percentage']:.4f}".replace(".", ",")
                    self.assertIn(f"{label} & Líneas & {percentage} & {threshold} & CUMPLE", manuscript)

    def test_published_e3_analysis_matches_canonical_evidence(self):
        actual = analyze_all(RESULTS / "evidencia-e3-canonica")
        expected = json.loads((RESULTS / "analisis-e3.json").read_text(encoding="utf-8"))
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
