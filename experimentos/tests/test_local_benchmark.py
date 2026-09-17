"""Unit fixtures only: these tests are not performance evidence."""
import copy
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prepare_local import digest, connection_identity, validate, report_error, LocalValidationError
from snapshot import source_sql
from verify_equivalence import COLUMNS, NUMERIC, DATES, compare, require_report


class SnapshotTests(unittest.TestCase):
    def test_external_traceback_preserves_origin_without_secrets(self):
        def driver_connect():
            raise AssertionError("synthetic-secret-in-driver-message")

        output = io.StringIO()
        try:
            try:
                driver_connect()
            except AssertionError as error:
                raise RuntimeError("synthetic-secret-in-wrapper") from error
        except RuntimeError as error:
            report_error(error, output)
        diagnostic = output.getvalue()
        self.assertIn("driver_connect", diagnostic)
        self.assertIn("AssertionError", diagnostic)
        self.assertIn("RuntimeError", diagnostic)
        self.assertIn("test_local_benchmark.py", diagnostic)
        self.assertNotIn("synthetic-secret", diagnostic)

    def test_controlled_validation_message_is_preserved(self):
        output = io.StringIO()
        report_error(LocalValidationError("Timestamp HLC no valido"), output)
        self.assertIn("Timestamp HLC no valido", output.getvalue())

    def test_fingerprint_is_order_independent(self):
        self.assertEqual(digest({"a": 1, "b": 2}), digest({"b": 2, "a": 1}))
        self.assertNotEqual(digest({"rows": 1}), digest({"rows": 2}))

    def test_timestamp_is_pinned_and_not_sql_injection(self):
        self.assertEqual(source_sql("reservas", "123.000"),
                         "SELECT * FROM public.reservas AS OF SYSTEM TIME '123.000'")
        with self.assertRaises(ValueError):
            source_sql("reservas", "123'; DROP TABLE reservas")
        with self.assertRaises(ValueError):
            source_sql("unknown", "123.000")

    def test_absent_equivalence_rejected(self):
        with self.assertRaises(ValueError):
            require_report({}, {})

    def test_cpu_guard_precedes_database_read(self):
        with patch("prepare_local.connection_identity"), patch("psutil.cpu_count", return_value=6), \
                patch("prepare_local.inventory") as read:
            with self.assertRaises(ValueError):
                validate({})
            read.assert_not_called()

    def test_existing_output_precedes_database_read(self):
        config = {"execution": {"parallelism_levels": [1, 2, 4, 6, 8],
                                "warmup_iterations": 1, "measured_iterations": 5}}
        with tempfile.TemporaryDirectory() as folder, patch("prepare_local.connection_identity"), \
                patch("psutil.cpu_count", return_value=8), patch("prepare_local.inventory") as read:
            with self.assertRaises(ValueError):
                validate(config, Path(folder))
            read.assert_not_called()

    def test_connection_mismatch_and_override_rejected(self):
        with tempfile.NamedTemporaryFile() as jar:
            env = {"RESERVAS_JDBC_URL": "jdbc:postgresql://localhost:26261/reservas_db?sslmode=disable",
                   "RESERVAS_PANDAS_URL": "postgresql+psycopg://localhost:26261/reservas_db?sslmode=disable",
                   "RESERVAS_DB_USERNAME": "unit", "RESERVAS_DB_PASSWORD": "synthetic-test-only",
                   "POSTGRES_JDBC_JAR": jar.name}
            with patch.dict(os.environ, env):
                self.assertEqual(connection_identity()["port"], 26261)
                os.environ["RESERVAS_PANDAS_URL"] = env["RESERVAS_PANDAS_URL"].replace("26261", "26257")
                with self.assertRaises(ValueError):
                    connection_identity()
                os.environ["RESERVAS_PANDAS_URL"] = env["RESERVAS_PANDAS_URL"] + "&host=other"
                with self.assertRaises(ValueError):
                    connection_identity()


class EquivalenceTests(unittest.TestCase):
    def setUp(self):
        import pandas as pd
        row = {c: 1 if c in NUMERIC else "2026-01-01" if c in DATES else
               "08:00:00" if c in {"hora_inicio", "hora_fin"} else "id" for c in COLUMNS}
        self.left = pd.DataFrame([row, {**row, "reserva_id": "id2"}])

    def test_order_numeric_and_date_normalization(self):
        import pandas as pd
        right = self.left.iloc[::-1].copy()
        right["numero_participantes"] = right.numero_participantes.astype(float)
        right["solicitud_creada_en"] = pd.to_datetime(right.solicitud_creada_en, utc=True)
        self.assertEqual(compare(self.left, right)["rows"], 2)

    def test_equal_counts_changed_value_rejected(self):
        right = self.left.copy()
        right.loc[0, "numero_participantes"] = 99
        with self.assertRaises(AssertionError):
            compare(self.left, right)

    def test_changed_id_rejected(self):
        right = self.left.copy()
        right.loc[0, "reserva_id"] = "other"
        with self.assertRaises(AssertionError):
            compare(self.left, right)

    def test_duplicates_rejected(self):
        right = self.left.copy()
        right.loc[1, "reserva_id"] = "id"
        with self.assertRaises(ValueError):
            compare(self.left, right)

    def test_missing_column_rejected(self):
        with self.assertRaises(ValueError):
            compare(self.left, self.left.drop(columns="mes_reserva"))

    def test_null_is_not_string_null(self):
        right = self.left.copy()
        self.left.loc[0, "estado_reserva"] = None
        right.loc[0, "estado_reserva"] = "None"
        with self.assertRaises(AssertionError):
            compare(self.left, right)


if __name__ == "__main__":
    unittest.main()
