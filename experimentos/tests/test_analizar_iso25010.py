import csv
import tempfile
import unittest
from pathlib import Path

from experimentos.analizar_iso25010 import (
    analyze_scenario,
    build_corrective_document_blocks,
    read_corrective_reliability_population,
    read_efficiency_population,
    read_populated_efficiency_population,
)


FIELDNAMES = [
    "Type",
    "Name",
    "Request Count",
    "Failure Count",
    "95%",
    "99%",
]


class EfficiencyPopulationTest(unittest.TestCase):
    def write_stats(self, root: Path, rows: list[dict[str, str]]) -> None:
        target = root / "eficiencia_nominal_50u_5m" / "rep-02"
        target.mkdir(parents=True)
        with (target / "locust_stats.csv").open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)

    def test_selects_get_by_identity_and_excludes_login(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_stats(
                root,
                [
                    {
                        "Type": "GET",
                        "Name": "GET /api/v1/reservas",
                        "Request Count": "100",
                        "Failure Count": "7",
                        "95%": "24",
                        "99%": "40",
                    },
                    {
                        "Type": "POST",
                        "Name": "POST /api/v1/auth/login",
                        "Request Count": "50",
                        "Failure Count": "0",
                        "95%": "9400",
                        "99%": "9500",
                    },
                    {
                        "Type": "",
                        "Name": "Aggregated",
                        "Request Count": "150",
                        "Failure Count": "7",
                        "95%": "100",
                        "99%": "2000",
                    },
                ],
            )

            result = read_efficiency_population(root, [2])[2]

            self.assertEqual(result["request"], "GET /api/v1/reservas")
            self.assertEqual(result["total_requests"], 100)
            self.assertEqual(result["failures"], 7)
            self.assertEqual(result["p95_ms"], 24.0)
            self.assertEqual(result["p99_ms"], 40.0)

    def test_rejects_unclassified_active_request(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_stats(
                root,
                [
                    {
                        "Type": "GET",
                        "Name": "GET /api/v1/otro",
                        "Request Count": "1",
                        "Failure Count": "0",
                        "95%": "10",
                        "99%": "20",
                    }
                ],
            )

            with self.assertRaisesRegex(ValueError, "sin clasificación poblacional"):
                read_efficiency_population(root, [2])

    def test_rejects_two_active_get_rows_without_joint_distribution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_stats(
                root,
                [
                    {
                        "Type": "GET",
                        "Name": "GET /api/v1/reservas",
                        "Request Count": "100",
                        "Failure Count": "0",
                        "95%": "20",
                        "99%": "40",
                    },
                    {
                        "Type": "GET",
                        "Name": "GET /api/v1/reservas/{id}",
                        "Request Count": "20",
                        "Failure Count": "2",
                        "95%": "30",
                        "99%": "50",
                    },
                ],
            )

            with self.assertRaisesRegex(ValueError, "distribución raw combinable"):
                read_efficiency_population(root, [2])


class CorrectiveReliabilityPopulationTest(unittest.TestCase):
    EVENT_FIELDS = [
        "request_type",
        "name",
        "response_time_ms",
        "status_code",
    ]

    def write_events(
        self,
        root: Path,
        repetition: int,
        events: list[dict[str, str]],
        attempt: int = 1,
        scenario: str = "fiabilidad_nominal_50u_1h_refresh",
    ) -> None:
        dirname = (
            f"rep-{repetition:02d}"
            if attempt == 1
            else f"rep-{repetition:02d}-attempt-{attempt:02d}"
        )
        target = (
            root
            / scenario
            / dirname
        )
        target.mkdir(parents=True)

        with (target / "locust_requests.csv").open(
            "w", encoding="utf-8", newline=""
        ) as file:
            writer = csv.DictWriter(file, fieldnames=self.EVENT_FIELDS)
            writer.writeheader()
            writer.writerows(events)

    def test_reconstructs_business_population_from_raw_events(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            self.write_events(
                root,
                2,
                [
                    {
                        "request_type": "GET",
                        "name": "GET /api/v1/reservas",
                        "response_time_ms": "10",
                        "status_code": "200",
                    },
                    {
                        "request_type": "GET",
                        "name": "GET /api/v1/reservas/{id}",
                        "response_time_ms": "20",
                        "status_code": "401",
                    },
                    {
                        "request_type": "GET",
                        "name": "GET /api/v1/reservas",
                        "response_time_ms": "30",
                        "status_code": "500",
                    },
                    {
                        "request_type": "POST",
                        "name": "POST /api/v1/auth/login",
                        "response_time_ms": "999",
                        "status_code": "500",
                    },
                ],
            )

            result = read_corrective_reliability_population(
                root,
                [{"_repetition": "2", "intento": "1"}],
            )[2]

            self.assertEqual(result["total_requests"], 3)
            self.assertEqual(result["http_401"], 1)
            self.assertEqual(result["http_5xx"], 1)
            self.assertAlmostEqual(
                result["failure_rate_percent"],
                100.0 / 3.0,
            )
            self.assertEqual(result["p95_ms"], 30.0)
            self.assertEqual(result["p99_ms"], 30.0)


    def test_reconstructs_populated_scenario_from_its_own_raw_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            self.write_events(
                root,
                2,
                [
                    {
                        "request_type": "GET",
                        "name": "GET /api/v1/reservas",
                        "response_time_ms": "12",
                        "status_code": "200",
                    },
                    {
                        "request_type": "GET",
                        "name": "GET /api/v1/reservas/{id}",
                        "response_time_ms": "25",
                        "status_code": "500",
                    },
                ],
                scenario="fiabilidad_nominal_50u_1h_refresh_poblada",
            )

            result = read_corrective_reliability_population(
                root,
                [{"_repetition": "2", "intento": "1"}],
                "fiabilidad_nominal_50u_1h_refresh_poblada",
            )[2]

            self.assertEqual(result["total_requests"], 2)
            self.assertEqual(result["http_401"], 0)
            self.assertEqual(result["http_5xx"], 1)
            self.assertAlmostEqual(
                result["failure_rate_percent"],
                50.0,
            )
            self.assertEqual(result["p95_ms"], 25.0)
            self.assertEqual(result["p99_ms"], 25.0)
            self.assertIn(
                "fiabilidad_nominal_50u_1h_refresh_poblada",
                result["source"],
            )

    def test_document_blocks_are_generated_from_ten_raw_repetitions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = []

            for repetition in range(1, 11):
                self.write_events(
                    root,
                    repetition,
                    [
                        {
                            "request_type": "GET",
                            "name": "GET /api/v1/reservas",
                            "response_time_ms": str(repetition),
                            "status_code": "200",
                        }
                    ],
                )
                rows.append(
                    {
                        "_repetition": str(repetition),
                        "intento": "1",
                    }
                )

            blocks = build_corrective_document_blocks(root, rows)

            self.assertIn(
                "Las diez repeticiones correctivas suman 10 GET de negocio",
                blocks["markdown"],
            )
            self.assertIn(
                "con 0 HTTP 401 y 0 HTTP 5xx",
                blocks["markdown"],
            )
            self.assertIn(
                "| Tasa HTTP 5xx | 8 | 0,000000 %",
                blocks["markdown"],
            )
            self.assertIn(
                "| p95 GET negocio | 8 | 5,500000 ms",
                blocks["markdown"],
            )
            self.assertIn(
                "| p99 GET negocio | 8 | 5,500000 ms",
                blocks["markdown"],
            )
            self.assertIn(
                "Media 0,000000\\%; IC95 [0,000000; 0,000000]\\%",
                blocks["latex"],
            )

    def test_document_blocks_require_all_ten_raw_repetitions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = []

            for repetition in range(1, 10):
                self.write_events(
                    root,
                    repetition,
                    [
                        {
                            "request_type": "GET",
                            "name": "GET /api/v1/reservas",
                            "response_time_ms": "5",
                            "status_code": "200",
                        }
                    ],
                )
                rows.append(
                    {
                        "_repetition": str(repetition),
                        "intento": "1",
                    }
                )

            with self.assertRaisesRegex(
                ValueError,
                "se requieren las repeticiones raw 1..10",
            ):
                build_corrective_document_blocks(root, rows)


    def test_analyzer_rejects_csv_raw_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = []

            for repetition in range(1, 11):
                if 2 <= repetition <= 9:
                    self.write_events(
                        root,
                        repetition,
                        [
                            {
                                "request_type": "GET",
                                "name": "GET /api/v1/reservas",
                                "response_time_ms": "5",
                                "status_code": "200",
                            }
                        ],
                    )

                rows.append(
                    {
                        "escenario": "fiabilidad_nominal_50u_1h_refresh",
                        "_repetition": str(repetition),
                        "repeticion": str(repetition),
                        "intento": "1",
                        "usuarios": "50",
                        "duracion": "1h",
                        "total_requests": "999" if repetition == 2 else "1",
                        "failures": "0",
                        "failure_rate_percent": "0",
                        "p95_ms": "5",
                        "p99_ms": "5",
                        "valida": "si",
                        "observacion": "test",
                    }
                )

            with self.assertRaisesRegex(
                ValueError,
                "total_requests no coincide con raw",
            ):
                analyze_scenario(
                    "fiabilidad_nominal_50u_1h_refresh",
                    rows,
                    root,
                )


class PopulatedEfficiencyPopulationTest(unittest.TestCase):
    fields = ["request_type", "name", "response_time_ms", "status_code"]

    def write_population(self, root, events, *, valid=True):
        target = root / "eficiencia_nominal_50u_5m_poblada" / "rep-02"
        target.mkdir(parents=True)
        for name in ("locust_stats.csv", "locust_stats_history.csv", "locust_failures.csv",
                     "locust_exceptions.csv", "locust.log", "locust-report.html",
                     "locust-final-stats.json", "deployed-software-sha.txt", "harness-sha256.txt",
                     "dataset-sha256.txt", "SHA256SUMS"):
            (target / name).write_text("evidence\n", encoding="utf-8")
        (target / "metadata.json").write_text(__import__("json").dumps({
            "duration_completed": valid, "evidence_complete": valid,
            "dataset_verified": valid, "software_sha_consistent": valid,
            "harness_consistent": valid}), encoding="utf-8")
        with (target / "locust_requests.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=self.fields); writer.writeheader(); writer.writerows(events)

    def test_combines_both_gets_excludes_auth_and_preserves_5xx(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_population(root, [
                {"request_type":"GET", "name":"GET /api/v1/reservas", "response_time_ms":"10", "status_code":"200"},
                {"request_type":"GET", "name":"GET /api/v1/reservas/{id}", "response_time_ms":"20", "status_code":"500"},
                {"request_type":"POST", "name":"POST /api/v1/auth/login", "response_time_ms":"999", "status_code":"200"},
                {"request_type":"POST", "name":"POST /api/v1/auth/refresh", "response_time_ms":"999", "status_code":"200"},
            ])
            result = read_populated_efficiency_population(root, [2])[2]
            self.assertEqual((result["total_get"], result["listado"], result["by_id"], result["http_5xx"]), (2, 1, 1, 1))
            self.assertEqual((result["p95_ms"], result["p99_ms"]), (20.0, 20.0))

    def test_degenerate_or_unclassified_population_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_population(root, [{"request_type":"GET", "name":"GET /api/v1/reservas", "response_time_ms":"10", "status_code":"200"}])
            with self.assertRaisesRegex(ValueError, "población degenerada"):
                read_populated_efficiency_population(root, [2])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_population(root, [
                {"request_type":"GET", "name":"GET /api/v1/reservas", "response_time_ms":"10", "status_code":"200"},
                {"request_type":"GET", "name":"GET /api/v1/reservas/{id}", "response_time_ms":"20", "status_code":"200"},
                {"request_type":"GET", "name":"GET /api/v1/otra", "response_time_ms":"30", "status_code":"200"},
            ])
            with self.assertRaisesRegex(ValueError, "no clasificada"):
                read_populated_efficiency_population(root, [2])


if __name__ == "__main__":
    unittest.main()
