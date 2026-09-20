import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from experimentos.analizar_iso25010 import (
    POPULATED_EFFICIENCY_SCENARIO,
    read_populated_efficiency_population,
)


EVENT_FIELDS = [
    "request_type",
    "name",
    "response_time_ms",
    "status_code",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


class PopulatedEfficiencyCampaignIntegrityTest(unittest.TestCase):
    def refresh_manifest(self, target: Path) -> None:
        manifest = target / "SHA256SUMS"
        entries = []

        for path in sorted(target.iterdir()):
            if path.is_file() and path.name != "SHA256SUMS":
                entries.append(
                    f"{sha256_file(path)}  {path.name}"
                )

        manifest.write_text(
            "\n".join(entries) + "\n",
            encoding="utf-8",
        )

    def write_repetition(
        self,
        raw_root: Path,
        repetition: int,
    ) -> Path:
        target = (
            raw_root
            / POPULATED_EFFICIENCY_SCENARIO
            / f"rep-{repetition:02d}"
        )
        target.mkdir(parents=True)

        evidence_sha = "a" * 40
        software_sha = "b" * 40

        dataset = target / "dataset.csv"
        dataset.write_text(
            "id\n1\n",
            encoding="utf-8",
        )
        dataset_sha = sha256_file(dataset)

        (target / "dataset-sha256.txt").write_text(
            f"{dataset_sha}  dataset.csv\n",
            encoding="utf-8",
        )

        (target / "evidence-git-sha.txt").write_text(
            evidence_sha + "\n",
            encoding="utf-8",
        )
        (target / "deployed-software-sha.txt").write_text(
            software_sha + "\n",
            encoding="utf-8",
        )

        for name in (
            "harness-sha256.txt",
            "harness-before-sha256.txt",
            "harness-after-sha256.txt",
        ):
            (target / name).write_text(
                "harness-estable\n",
                encoding="utf-8",
            )

        for name in (
            "locust_stats.csv",
            "locust_stats_history.csv",
            "locust_failures.csv",
            "locust_exceptions.csv",
            "locust.log",
            "locust-report.html",
            "locust-final-stats.json",
            "deployment-before.txt",
            "deployment-after.txt",
            "elapsed-seconds.txt",
            "start_utc.txt",
            "end_utc.txt",
        ):
            (target / name).write_text(
                f"evidence-{repetition}\n",
                encoding="utf-8",
            )

        (target / "locust-exit-code.txt").write_text(
            "0\n",
            encoding="utf-8",
        )

        metadata = {
            "scenario": POPULATED_EFFICIENCY_SCENARIO,
            "repetition": repetition,
            "mode": "official",
            "evidence_git_sha": evidence_sha,
            "deployed_software_sha": software_sha,
            "planned_duration_seconds": 300,
            "duration_completed": True,
            "evidence_complete": True,
            "dataset_verified": True,
            "software_sha_consistent": True,
            "deployment_after_valid": True,
            "harness_consistent": True,
            "locust_exit_code": 0,
        }

        (target / "metadata.json").write_text(
            json.dumps(metadata),
            encoding="utf-8",
        )

        with (target / "locust_requests.csv").open(
            "w",
            encoding="utf-8",
            newline="",
        ) as stream:
            writer = csv.DictWriter(
                stream,
                fieldnames=EVENT_FIELDS,
            )
            writer.writeheader()
            writer.writerows(
                [
                    {
                        "request_type": "GET",
                        "name": "GET /api/v1/reservas",
                        "response_time_ms": str(10 + repetition),
                        "status_code": "200",
                    },
                    {
                        "request_type": "GET",
                        "name": "GET /api/v1/reservas/{id}",
                        "response_time_ms": str(20 + repetition),
                        "status_code": "200",
                    },
                ]
            )

        self.refresh_manifest(target)
        return target

    def write_campaign(self, raw_root: Path) -> None:
        for repetition in range(1, 11):
            self.write_repetition(
                raw_root,
                repetition,
            )

    def test_accepts_complete_independent_campaign(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            raw_root = Path(directory)
            self.write_campaign(raw_root)

            result = read_populated_efficiency_population(
                raw_root,
                list(range(1, 11)),
            )

            self.assertEqual(len(result), 10)

    def test_rejects_corrupted_manifest_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            raw_root = Path(directory)
            self.write_campaign(raw_root)

            target = (
                raw_root
                / POPULATED_EFFICIENCY_SCENARIO
                / "rep-01"
                / "locust.log"
            )
            target.write_text(
                "evidencia-corrupta\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError,
                "SHA-256 no coincide",
            ):
                read_populated_efficiency_population(
                    raw_root,
                    list(range(1, 11)),
                )

    def test_rejects_pseudoreplication(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            raw_root = Path(directory)
            self.write_campaign(raw_root)

            rep01 = (
                raw_root
                / POPULATED_EFFICIENCY_SCENARIO
                / "rep-01"
            )
            rep02 = (
                raw_root
                / POPULATED_EFFICIENCY_SCENARIO
                / "rep-02"
            )

            (rep02 / "locust_requests.csv").write_bytes(
                (rep01 / "locust_requests.csv").read_bytes()
            )
            self.refresh_manifest(rep02)

            with self.assertRaisesRegex(
                ValueError,
                "pseudorreplicación detectada",
            ):
                read_populated_efficiency_population(
                    raw_root,
                    list(range(1, 11)),
                )

    def test_rejects_cross_repetition_inconsistency(self) -> None:
        cases = (
            "deployed_software_sha",
            "dataset_sha256",
            "harness_manifest_sha256",
        )

        for case in cases:
            with self.subTest(case=case):
                with tempfile.TemporaryDirectory() as directory:
                    raw_root = Path(directory)
                    self.write_campaign(raw_root)

                    target = (
                        raw_root
                        / POPULATED_EFFICIENCY_SCENARIO
                        / "rep-10"
                    )

                    if case == "deployed_software_sha":
                        different_sha = "c" * 40

                        (target / "deployed-software-sha.txt").write_text(
                            different_sha + "\n",
                            encoding="utf-8",
                        )

                        metadata_path = target / "metadata.json"
                        metadata = json.loads(
                            metadata_path.read_text(encoding="utf-8")
                        )
                        metadata["deployed_software_sha"] = different_sha
                        metadata_path.write_text(
                            json.dumps(metadata),
                            encoding="utf-8",
                        )

                    elif case == "dataset_sha256":
                        dataset = target / "dataset.csv"
                        dataset.write_text(
                            "id\n2\n",
                            encoding="utf-8",
                        )

                        (target / "dataset-sha256.txt").write_text(
                            f"{sha256_file(dataset)}  dataset.csv\n",
                            encoding="utf-8",
                        )

                    else:
                        (target / "harness-sha256.txt").write_text(
                            "harness-distinto\n",
                            encoding="utf-8",
                        )

                    self.refresh_manifest(target)

                    with self.assertRaisesRegex(
                        ValueError,
                        f"inconsistencia entre repeticiones en {case}",
                    ):
                        read_populated_efficiency_population(
                            raw_root,
                            list(range(1, 11)),
                        )


if __name__ == "__main__":
    unittest.main()
