"""Fixtures matemáticas en memoria: NO constituyen evidencia experimental."""

import copy
import ast
from pathlib import Path
from unittest.mock import Mock
import unittest

from experimentos.analyze_speedup import summarize


class SpeedupTests(unittest.TestCase):
    def test_terminal_write_and_explicit_overwrite(self):
        # Exercise the actual exporter without requiring a JVM in unit tests.
        tree = ast.parse((Path(__file__).resolve().parents[2] / "spark/pipeline.py").read_text(encoding="utf-8"))
        exporter = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                        and node.name == "exportar_parquet")
        namespace = {"DataFrame": object}
        exec(compile(ast.Module(body=[exporter], type_ignores=[]), "pipeline.py", "exec"), namespace)
        data = Mock()
        namespace["exportar_parquet"](data, "destination")
        data.write.mode.assert_called_once_with("errorifexists")
        data.write.mode.return_value.parquet.assert_called_once_with("destination")
        data.reset_mock()
        namespace["exportar_parquet"](data, "destination", True)
        data.write.mode.assert_called_once_with("overwrite")

    def setUp(self):
        self.config = {"batch_id": "unit-test", "dataset": {"id": "fixture", "snapshot_id": "fixture"},
                       "execution": {"parallelism_levels": [1, 2, 4, 6, 8],
                                     "measured_iterations": 2, "warmup_iterations": 1}}
        self.payload = {"results": []}
        for treatment, n in [("pandas-baseline", 1)] + [("pyspark-pipeline", n) for n in [1, 2, 4, 6, 8]]:
            for warmup, iterations in [(True, [1]), (False, [1, 2])]:
                for iteration in iterations:
                    self.payload["results"].append({
                        "protocol_version": "1.1", "status": "completed",
                        "run_id": f"{treatment}-{n}-{warmup}-{iteration}", "batch_id": "unit-test",
                        "dataset_id": "fixture", "dataset_snapshot_id": "fixture",
                        "environment": {"host": "unit-test"}, "rows_processed": 10,
                        "started_at": "unit-test", "treatment": treatment,
                        "parallelism": n, "warmup": warmup, "iteration": iteration,
                        "duration_ms": 100 * (0.25 + 0.75/n) if treatment == "pyspark-pipeline" else 200,
                    })

    def test_known_amdahl_identity(self):
        summary, fit = summarize(self.payload, self.config)
        self.assertAlmostEqual(fit["serial_fraction"], 0.25)
        self.assertAlmostEqual(fit["rmse_normalized_time"], 0)
        self.assertEqual(summary[1]["speedup_vs_pandas"], 2)
        self.assertEqual(summary[1]["speedup_vs_spark1"], 1)
        self.assertEqual(summary[1]["stddev_ms"], 0)

    def test_empty_evidence_rejected(self):
        with self.assertRaisesRegex(ValueError, "pendiente"):
            summarize({"results": []}, self.config)

    def test_incomplete_batch_rejected(self):
        self.payload["results"].pop()
        with self.assertRaisesRegex(ValueError, "incompleto"):
            summarize(self.payload, self.config)

    def test_failed_warmup_rejected(self):
        self.payload["results"][0]["status"] = "failed"
        with self.assertRaisesRegex(ValueError, "fallos"):
            summarize(self.payload, self.config)

    def test_duplicate_rejected(self):
        self.payload["results"].append(copy.deepcopy(self.payload["results"][0]))
        with self.assertRaisesRegex(ValueError, "duplicado"):
            summarize(self.payload, self.config)

    def test_different_rows_rejected(self):
        self.payload["results"][0]["rows_processed"] = 11
        with self.assertRaisesRegex(ValueError, "filas"):
            summarize(self.payload, self.config)

    def test_mixed_environment_rejected(self):
        self.payload["results"][0]["environment"] = {"host": "another"}
        with self.assertRaisesRegex(ValueError, "entorno"):
            summarize(self.payload, self.config)


if __name__ == "__main__":
    unittest.main()
