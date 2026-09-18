import argparse
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from experimentos import finalizar_evidencia_iso25010
from experimentos import registrar_iso25010


class RegistrarFiabilidadTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.evidence = self.root / "fiabilidad_nominal_50u_1h" / "rep-02"
        self.evidence.mkdir(parents=True)
        for name in registrar_iso25010.RELIABILITY_EVIDENCE:
            (self.evidence / name).write_text("evidencia\n", encoding="utf-8")
        self.csv_path = self.root / "iso25010.csv"
        self.csv_path.write_text(
            "escenario,repeticion,usuarios,duracion,total_requests,failures,"
            "failure_rate_percent,p95_ms,p99_ms,valida,observacion\n"
            "fiabilidad_nominal_50u_1h,2,50,1h,,,,,,,\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp.cleanup()

    def metadata(self, *, completed=True, exit_code=0):
        data = {
            "status": "completed" if completed else "aborted",
            "scenario": "fiabilidad_nominal_50u_1h",
            "repetition": 2,
            "users": 50,
            "spawn_rate": 10,
            "planned_duration": "1h",
            "planned_duration_seconds": 3600,
            "started_at_utc": "2026-09-10T10:00:00Z",
            "finished_at_utc": "2026-09-10T11:00:00Z",
            "git_branch": "feature/entrega-4",
            "git_sha": "a" * 40,
            "git_worktree_clean_before": True,
            "python_version": "Python 3.12.0",
            "locust_version": "locust 2.31.6",
            "deployment_fingerprint_before": "container image digest",
            "deployment_fingerprint_after": "container image digest",
            "environment_consistent": completed,
            "duration_completed": completed,
            "execution_completed": completed,
            "evidence_complete": completed,
            "reservas_log_capture_succeeded": completed,
            "reservas_log_content_length": 0,
            "locust_exit_code": exit_code,
        }
        (self.evidence / "metadata.json").write_text(json.dumps(data), encoding="utf-8")

    def args(self, *, http_5xx=0):
        return argparse.Namespace(
            scenario="fiabilidad_nominal_50u_1h",
            repetition=2,
            total_requests=1000,
            http_5xx=http_5xx,
            p95_ms=100.0,
            p99_ms=200.0,
            evidence_dir=self.evidence,
            observation="",
            csv_path=self.csv_path,
        )

    def read_row(self):
        with self.csv_path.open(encoding="utf-8", newline="") as stream:
            return next(csv.DictReader(stream))

    def test_completed_without_errors_is_valid(self):
        self.metadata(exit_code=0)
        (self.evidence / "reservas-service.log").write_text("", encoding="utf-8")
        registrar_iso25010.update_csv(self.args())
        self.assertEqual("si", self.read_row()["valida"])

    def test_completed_with_real_http_500_is_valid_and_preserved(self):
        self.metadata(exit_code=1)
        registrar_iso25010.update_csv(self.args(http_5xx=7))
        row = self.read_row()
        self.assertEqual("7", row["failures"])
        self.assertEqual("0.700000", row["failure_rate_percent"])
        self.assertEqual("si", row["valida"])

    def test_aborted_execution_is_rejected(self):
        self.metadata(completed=False, exit_code=2)
        with self.assertRaisesRegex(ValueError, "no consta como completada"):
            registrar_iso25010.update_csv(self.args())

    def test_incomplete_evidence_is_rejected(self):
        self.metadata()
        (self.evidence / "prometheus-p95-result.txt").unlink()
        with self.assertRaisesRegex(ValueError, "Falta evidencia real"):
            registrar_iso25010.update_csv(self.args())

    def test_failed_log_capture_is_rejected(self):
        self.metadata()
        metadata_path = self.evidence / "metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["reservas_log_capture_succeeded"] = False
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "captura de logs"):
            registrar_iso25010.update_csv(self.args())


class RegistrarFiabilidadCorrectivaTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.evidence = (
            self.root
            / registrar_iso25010.CORRECTIVE_RELIABILITY
            / "rep-02"
        )
        self.evidence.mkdir(parents=True)
        for name in registrar_iso25010.CORRECTIVE_EVIDENCE - {"SHA256SUMS"}:
            (self.evidence / name).write_text("evidencia\n", encoding="utf-8")
        self._write_stats(business_gets=100, login=50, refresh=50)
        self._write_request_events()
        (self.evidence / "phase-boundaries.json").write_text(
            json.dumps(
                {
                    "start_epoch": 1000,
                    "split_epoch": 1900,
                    "finish_epoch": 4600,
                }
            ),
            encoding="utf-8",
        )
        self._write_prometheus_arrival()
        self.csv_path = self.root / "iso25010-correctiva.csv"
        self.csv_path.write_text(
            "escenario,repeticion,intento,usuarios,duracion,total_requests,failures,"
            "failure_rate_percent,p95_ms,p99_ms,valida,observacion\n"
            f"{registrar_iso25010.CORRECTIVE_RELIABILITY},2,,50,1h,,,,,,,\n",
            encoding="utf-8",
        )
        self._write_metadata(exit_code=1)

    def tearDown(self):
        self.temp.cleanup()

    def _write_stats(
        self,
        *,
        business_gets: int,
        login: int,
        refresh: int,
        write_final: bool = True,
    ) -> None:
        (self.evidence / "locust_stats.csv").write_text(
            "Type,Name,Request Count,Failure Count\n"
            f"GET,GET /api/v1/reservas,{business_gets},7\n"
            f"POST,POST /api/v1/auth/login,{login},0\n"
            f"POST,POST /api/v1/auth/refresh,{refresh},0\n"
            f",Aggregated,{business_gets + login + refresh},7\n",
            encoding="utf-8",
        )
        if write_final:
            self._write_final_stats(
                business_gets=business_gets,
                login=login,
                refresh=refresh,
            )

    def _write_final_stats(
        self, *, business_gets: int, login: int, refresh: int
    ) -> None:
        payload = {
            "entries": [
                {
                    "request_type": "GET",
                    "name": "GET /api/v1/reservas",
                    "request_count": business_gets,
                    "failure_count": 7,
                },
                {
                    "request_type": "POST",
                    "name": "POST /api/v1/auth/login",
                    "request_count": login,
                    "failure_count": 0,
                },
                {
                    "request_type": "POST",
                    "name": "POST /api/v1/auth/refresh",
                    "request_count": refresh,
                    "failure_count": 0,
                },
            ]
        }
        (self.evidence / "locust-final-stats.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )

    def _write_request_events(self) -> None:
        rows = [
            "timestamp_epoch,request_type,name,response_time_ms,status_code,outcome,error"
        ]
        rows.extend(
            f"{1001 + index if index < 80 else 1901 + index},GET,GET /api/v1/reservas,10,"
            f"{500 if index < 7 else 200},{'failure' if index < 7 else 'success'},"
            for index in range(100)
        )
        rows.append("1000,POST,POST /api/v1/auth/login,20,200,success,")
        rows.append("1870,POST,POST /api/v1/auth/refresh,20,200,success,")
        (self.evidence / "locust_requests.csv").write_text(
            "\n".join(rows) + "\n", encoding="utf-8"
        )

    def _write_prometheus_arrival(
        self,
        *,
        status: str = "success",
        result: list[dict[str, object]] | None = None,
    ) -> None:
        if result is None:
            result = [
                {
                    "metric": {
                        "job": "reservas-solicitudes-service",
                        "method": "GET",
                        "uri": "/api/v1/reservas",
                        "status": "200",
                    },
                    "values": [[1000, "0"], [1900, "80"], [4600, "100"]],
                }
            ]
        payload = {"status": status, "data": {"resultType": "matrix", "result": result}}
        (self.evidence / "prometheus-reservas-status-by-uri-result.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )

    def _write_metadata(self, *, completed: bool = True, exit_code: int = 1) -> None:
        sha = "b" * 40
        metadata = {
            "status": "running",
            "scenario": registrar_iso25010.CORRECTIVE_RELIABILITY,
            "repetition": 2,
            "attempt": 1,
            "users": 50,
            "spawn_rate": 10,
            "planned_duration": "1h",
            "planned_duration_seconds": 3600,
            "started_at_utc": "2026-09-13T10:00:00Z",
            "finished_at_utc": "2026-09-13T11:00:00Z",
            "git_branch": "feature/entrega-4",
            "git_sha": sha,
            "git_sha_after": sha,
            "git_worktree_clean_before": True,
            "python_version": "Python 3.12.0",
            "locust_version": "locust 2.31.6",
            "deployment_fingerprint_before": "container image digest",
            "deployment_fingerprint_after": "container image digest",
            "environment_consistent": completed,
            "duration_completed": completed,
            "elapsed_seconds": 3601.0 if completed else 120.0,
            "execution_completed": False,
            "evidence_complete": False,
            "reservas_log_capture_succeeded": completed,
            "reservas_log_content_length": 10,
            "gateway_log_capture_succeeded": completed,
            "gateway_log_content_length": 10,
            "locust_exit_code": exit_code,
        }
        (self.evidence / "metadata.json").write_text(
            json.dumps(metadata), encoding="utf-8"
        )

    def args(self, *, http_5xx: int = 7):
        return argparse.Namespace(
            scenario=registrar_iso25010.CORRECTIVE_RELIABILITY,
            repetition=2,
            attempt=1,
            total_requests=100,
            http_5xx=http_5xx,
            p95_ms=100.0,
            p99_ms=200.0,
            evidence_dir=self.evidence,
            observation="resultado adverso preservado",
            csv_path=self.csv_path,
        )

    def finalize(self):
        return finalizar_evidencia_iso25010.finalize(
            self.evidence, registrar_iso25010.CORRECTIVE_RELIABILITY, 2
        )

    def test_corrective_scenario_is_recognized_and_path_is_distinct(self):
        self.assertIn(
            registrar_iso25010.CORRECTIVE_RELIABILITY,
            registrar_iso25010.SCENARIOS,
        )
        self.assertNotEqual(
            registrar_iso25010.CORRECTIVE_RELIABILITY,
            registrar_iso25010.HISTORICAL_RELIABILITY,
        )
        self.assertIn(registrar_iso25010.CORRECTIVE_RELIABILITY, self.evidence.parts)

    def test_retry_attempt_has_separate_path_and_is_recorded(self):
        retry = self.evidence.with_name("rep-02-attempt-02")
        self.evidence.rename(retry)
        self.evidence = retry
        metadata_path = self.evidence / "metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["attempt"] = 2
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        result = finalizar_evidencia_iso25010.finalize(
            self.evidence, registrar_iso25010.CORRECTIVE_RELIABILITY, 2, 2
        )
        self.assertTrue(result["execution_completed"])
        args = argparse.Namespace(**{**vars(self.args()), "attempt": 2})
        registrar_iso25010.update_csv(args)
        with self.csv_path.open(encoding="utf-8", newline="") as stream:
            row = next(csv.DictReader(stream))
        self.assertEqual("2", row["repeticion"])
        self.assertEqual("2", row["intento"])

    def test_short_duration_remains_invalid(self):
        metadata_path = self.evidence / "metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["elapsed_seconds"] = 3594.999
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        result = self.finalize()
        self.assertFalse(result["execution_completed"])
        self.assertFalse(result["duration_evidence_valid"])

    def test_zero_business_gets_is_rejected_and_auth_is_not_population(self):
        self._write_stats(business_gets=0, login=50, refresh=50)
        metadata = self.finalize()
        self.assertEqual(0, metadata["business_get_count"])
        self.assertFalse(metadata["business_population_valid"])
        with self.assertRaisesRegex(ValueError, "no consta como completada"):
            registrar_iso25010.update_csv(self.args())

    def test_login_and_refresh_must_be_separate_from_business_population(self):
        self._write_stats(business_gets=100, login=50, refresh=0)
        metadata = self.finalize()
        self.assertEqual(100, metadata["business_get_count"])
        self.assertFalse(metadata["request_names_separated"])
        self.assertFalse(metadata["execution_completed"])

    def test_event_log_must_cover_every_business_get(self):
        self._write_stats(business_gets=101, login=50, refresh=50)
        metadata = self.finalize()
        self.assertFalse(metadata["business_events_consistent"])
        self.assertFalse(metadata["execution_completed"])

    def test_periodic_csv_may_lag_behind_exact_final_snapshot(self):
        # locust_stats.csv puede quedar unos requests detrás al finalizar.
        self._write_stats(
            business_gets=89,
            login=50,
            refresh=49,
            write_final=False,
        )
        self._write_final_stats(
            business_gets=100,
            login=50,
            refresh=50,
        )
        metadata = self.finalize()
        self.assertTrue(metadata["execution_completed"])
        self.assertEqual(100, metadata["business_get_count"])
        self.assertTrue(metadata["business_events_consistent"])

    def test_complete_hour_with_500_and_locust_exit_one_is_valid(self):
        metadata = self.finalize()
        self.assertTrue(metadata["execution_completed"])
        self.assertEqual(1, metadata["locust_exit_code"])
        registrar_iso25010.update_csv(self.args(http_5xx=7))
        with self.csv_path.open(encoding="utf-8", newline="") as stream:
            row = next(csv.DictReader(stream))
        self.assertEqual("7", row["failures"])
        self.assertEqual("si", row["valida"])

    def test_empty_auxiliary_logs_do_not_invalidate_structured_evidence(self):
        (self.evidence / "gateway-service.log").write_text("", encoding="utf-8")
        (self.evidence / "reservas-service.log").write_text("", encoding="utf-8")
        metadata = self.finalize()
        self.assertTrue(metadata["execution_completed"])

    def test_fractional_event_inside_final_second_is_valid(self):
        boundaries = {"start_epoch": 1000.0, "split_epoch": 1900.0, "finish_epoch": 4600.5}
        (self.evidence / "phase-boundaries.json").write_text(
            json.dumps(boundaries), encoding="utf-8"
        )
        events_path = self.evidence / "locust_requests.csv"
        rows = events_path.read_text(encoding="utf-8").splitlines()
        rows[-3] = rows[-3].replace(rows[-3].split(",", 1)[0], "4600.25", 1)
        events_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
        self._write_prometheus_arrival(
            result=[
                {
                    "metric": {
                        "job": "reservas-solicitudes-service",
                        "method": "GET",
                        "uri": "/api/v1/reservas",
                        "status": "200",
                    },
                    "values": [[1000.0, "0"], [1900.0, "80"], [4600.5, "100"]],
                }
            ]
        )
        self.assertTrue(self.finalize()["execution_completed"])

    def test_event_really_after_precise_finish_is_invalid(self):
        boundaries = {"start_epoch": 1000.0, "split_epoch": 1900.0, "finish_epoch": 4600.5}
        (self.evidence / "phase-boundaries.json").write_text(
            json.dumps(boundaries), encoding="utf-8"
        )
        events_path = self.evidence / "locust_requests.csv"
        rows = events_path.read_text(encoding="utf-8").splitlines()
        rows[-3] = rows[-3].replace(rows[-3].split(",", 1)[0], "4600.500001", 1)
        events_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
        result = self.finalize()
        self.assertFalse(result["execution_completed"])
        self.assertIn("fuera del intervalo", result["launcher_error"])

    def test_event_at_900_boundary_belongs_only_to_second_phase(self):
        events_path = self.evidence / "locust_requests.csv"
        rows = events_path.read_text(encoding="utf-8").splitlines()
        rows[1] = rows[1].replace("1001,", "1900,", 1)
        events_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
        self.finalize()
        phases = json.loads(
            (self.evidence / "phase-summary.json").read_text(encoding="utf-8")
        )
        self.assertEqual(79, phases["t_lt_900"]["get_total"])
        self.assertEqual(21, phases["t_gte_900"]["get_total"])

    def test_denominator_and_5xx_must_match_business_events(self):
        self.finalize()
        with self.assertRaisesRegex(ValueError, "total_requests no coincide"):
            registrar_iso25010.validate_evidence(
                argparse.Namespace(**{**vars(self.args()), "total_requests": 150})
            )
        with self.assertRaisesRegex(ValueError, "http_5xx no coincide"):
            registrar_iso25010.validate_evidence(
                argparse.Namespace(**{**vars(self.args()), "http_5xx": 6})
            )

    def test_incomplete_execution_is_invalid(self):
        self._write_metadata(completed=False, exit_code=2)
        metadata = self.finalize()
        self.assertFalse(metadata["execution_completed"])

    def test_missing_manifest_is_invalid(self):
        self.finalize()
        (self.evidence / "SHA256SUMS").unlink()
        with self.assertRaisesRegex(ValueError, "Falta evidencia real"):
            registrar_iso25010.validate_evidence(self.args())

    def test_incorrect_hash_is_invalid(self):
        self.finalize()
        (self.evidence / "locust.log").write_text("alterado\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Hash incorrecto"):
            registrar_iso25010.validate_evidence(self.args())

    def test_valid_manifest_covers_every_evidence_file(self):
        metadata = self.finalize()
        entries = registrar_iso25010.verify_sha256_manifest(self.evidence)
        self.assertTrue(metadata["manifest_valid"])
        self.assertEqual(metadata["manifest_entries"], entries)
        phases = json.loads(
            (self.evidence / "phase-summary.json").read_text(encoding="utf-8")
        )
        self.assertEqual(80, phases["t_lt_900"]["get_total"])
        self.assertEqual(7, phases["t_lt_900"]["http_5xx"])
        self.assertEqual(1, phases["t_lt_900"]["refresh"])
        self.assertEqual(20, phases["t_gte_900"]["get_total"])
        self.assertTrue(phases["prometheus_reservas"]["arrival_after_900"])

    def test_aborted_state_has_a_valid_manifest_and_final_metadata_hash(self):
        self._write_metadata(completed=False, exit_code=2)
        metadata = self.finalize()
        self.assertEqual("aborted", metadata["status"])
        entries = registrar_iso25010.verify_sha256_manifest(self.evidence)
        self.assertEqual(metadata["manifest_entries"], entries)
        manifest = (self.evidence / "SHA256SUMS").read_text(encoding="utf-8")
        metadata_digest = hashlib.sha256(
            (self.evidence / "metadata.json").read_bytes()
        ).hexdigest()
        self.assertIn(f"{metadata_digest}  metadata.json", manifest)

    def test_file_modified_after_hash_fails_verification(self):
        self.finalize()
        (self.evidence / "locust.log").write_text("posterior al hash\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Hash incorrecto"):
            registrar_iso25010.verify_sha256_manifest(self.evidence)

    def test_manifest_has_exact_coverage(self):
        self.finalize()
        (self.evidence / "archivo-no-manifestado.txt").write_text("nuevo\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "no cubre exactamente"):
            registrar_iso25010.verify_sha256_manifest(self.evidence)


class PrometheusArrivalValidationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "prometheus.json"
        self.start = 1000
        self.split = 1900
        self.finish = 4600

    def tearDown(self):
        self.temp.cleanup()

    def write(self, payload: object) -> None:
        self.path.write_text(json.dumps(payload), encoding="utf-8")

    def payload(self, values, *, labels=None, status="success"):
        return {
            "status": status,
            "data": {
                "resultType": "matrix",
                "result": [
                    {
                        "metric": labels
                        or {
                            "job": "reservas-solicitudes-service",
                            "method": "GET",
                            "uri": "/api/v1/reservas",
                            "status": "200",
                        },
                        "values": values,
                    }
                ],
            },
        }

    def validate(self):
        return finalizar_evidencia_iso25010.validate_prometheus_arrival(
            self.path,
            start_epoch=self.start,
            split_epoch=self.split,
            finish_epoch=self.finish,
        )

    def test_status_other_than_success_is_invalid(self):
        self.write(self.payload([[1000, "0"], [4600, "1"]], status="error"))
        with self.assertRaisesRegex(ValueError, "status=success"):
            self.validate()

    def test_empty_result_is_invalid(self):
        self.write({"status": "success", "data": {"resultType": "matrix", "result": []}})
        with self.assertRaisesRegex(ValueError, "no devolvió series"):
            self.validate()

    def test_activity_only_before_900_is_invalid(self):
        self.write(self.payload([[1000, "0"], [1900, "20"], [4600, "20"]]))
        with self.assertRaisesRegex(ValueError, "después de t=900"):
            self.validate()

    def test_get_activity_after_900_is_valid(self):
        self.write(self.payload([[1000, "0"], [1900, "20"], [4600, "21"]]))
        self.assertTrue(self.validate()["arrival_after_900"])

    def test_unrecognized_labels_are_invalid(self):
        labels = {"verb": "GET", "path": "/api/v1/reservas", "code": "200"}
        self.write(self.payload([[1000, "0"], [1900, "20"], [4600, "21"]], labels=labels))
        with self.assertRaisesRegex(ValueError, "labels reconocidos"):
            self.validate()

    def test_corrupt_json_is_invalid(self):
        self.path.write_text("{no-json", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "corrupta"):
            self.validate()


if __name__ == "__main__":
    unittest.main()
