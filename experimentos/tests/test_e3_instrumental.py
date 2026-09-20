import csv
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


EXPERIMENTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXPERIMENTS))

from analizar_e3 import analyze_all  # noqa: E402
from e3_instrumental import normalize_command, parse_playwright, prepare_repetition, student_n3, wilson  # noqa: E402
from ejecutar_e3 import jacoco_metrics  # noqa: E402


class WindowsCommandNormalizationTest(unittest.TestCase):
    @staticmethod
    def resolve(mapping):
        return lambda candidate: mapping.get(candidate)

    @patch("e3_instrumental.os.name", "nt")
    def test_wraps_mvn_cmd_on_windows(self):
        with patch("e3_instrumental.shutil.which", side_effect=self.resolve({"mvn.cmd": r"C:\\tools\\mvn.cmd"})):
            self.assertEqual(
                normalize_command(["mvn", "--version"]),
                ["cmd", "/c", r"C:\\tools\\mvn.cmd", "--version"],
            )

    @patch("e3_instrumental.os.name", "nt")
    def test_wraps_npm_cmd_on_windows(self):
        with patch("e3_instrumental.shutil.which", side_effect=self.resolve({"npm.cmd": r"C:\\node\\npm.cmd"})):
            self.assertEqual(
                normalize_command(["npm", "run", "lint"]),
                ["cmd", "/c", r"C:\\node\\npm.cmd", "run", "lint"],
            )

    @patch("e3_instrumental.os.name", "nt")
    def test_keeps_resolved_exe_direct_on_windows(self):
        with patch("e3_instrumental.shutil.which", side_effect=self.resolve({"python": r"C:\\Python\\python.exe"})):
            self.assertEqual(
                normalize_command(["python", "-V"]),
                [r"C:\\Python\\python.exe", "-V"],
            )

    @patch("e3_instrumental.os.name", "nt")
    def test_keeps_existing_cmd_wrapper(self):
        with patch("e3_instrumental.shutil.which") as which:
            command = ["cmd", "/c", "gradlew.bat", "--version"]
            self.assertEqual(normalize_command(command), command)
            which.assert_not_called()

    @patch("e3_instrumental.os.name", "posix")
    def test_non_windows_command_is_unchanged(self):
        with patch("e3_instrumental.shutil.which") as which:
            command = ["npm", "run", "lint"]
            self.assertEqual(normalize_command(command), command)
            which.assert_not_called()


class StatisticsTest(unittest.TestCase):
    def test_jacoco_line_counter_is_extracted(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "jacoco.xml"
            report.write_text(
                '<report><counter type="LINE" missed="20" covered="80"/></report>',
                encoding="utf-8",
            )
            metrics = jacoco_metrics(report)
            self.assertEqual(metrics["line"], 80.0)

    def test_wilson_is_non_degenerate_for_finite_perfect_sample(self):
        low, high = wilson(21, 21)
        self.assertLess(low, 1.0)
        self.assertAlmostEqual(high, 1.0)

    def test_student_n3_reports_degenerate_interval_when_s_is_zero(self):
        result = student_n3([70.0, 70.0, 70.0])
        self.assertEqual(result["sample_sd"], 0.0)
        self.assertEqual(result["ci95_low"], 70.0)
        self.assertEqual(result["ci95_high"], 70.0)

    def test_playwright_parser_preserves_flaky_and_skipped(self):
        report = {"suites": [{"specs": [{"tests": [
            {"status": "flaky", "results": [{"status": "failed"}, {"status": "passed"}]},
            {"status": "expected", "results": [{"status": "skipped"}]},
        ]}]}]}
        counts = parse_playwright(report)
        self.assertEqual(counts["total"], 2)
        self.assertEqual(counts["passed"], 1)
        self.assertEqual(counts["flaky"], 1)
        self.assertEqual(counts["skipped"], 1)


class GuardsTest(unittest.TestCase):
    def test_rejects_overwrite_and_changed_sha(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            identity = {"git_sha": "a" * 40, "git_branch": "feature/entrega-4", "git_worktree_clean": True}
            parameters = {"repetitions": 3}
            prepare_repetition(root, 1, identity, parameters)
            with self.assertRaises(FileExistsError):
                prepare_repetition(root, 1, identity, parameters)
            changed = dict(identity, git_sha="b" * 40)
            with self.assertRaises(ValueError):
                prepare_repetition(root, 2, changed, parameters)

    def test_dry_run_creates_no_raw(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "raw"
            result = subprocess.run(
                [sys.executable, str(EXPERIMENTS / "ejecutar_e3.py"), "compatibilidad",
                 "--repetition", "1", "--raw-root", str(root), "--dry-run"],
                cwd=EXPERIMENTS.parent, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(root.exists())


class AnalyzerTest(unittest.TestCase):
    @staticmethod
    def manifest(path: Path, campaign: str):
        path.mkdir(parents=True)
        (path / "manifest.json").write_text(json.dumps({
            "git_sha": "c" * 40, "campaign": campaign, "evidence_complete": True,
            "flaky": False,
        }), encoding="utf-8")

    def test_analyzer_applies_preregistered_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory)
            security_fields = ["decision_id", "request", "endpoint", "method", "identity",
                               "role", "expected_http", "observed_http", "assertion_pass", "attempt"]
            identifiers = [
                "admin_login_permitido", "admin_login_invalido_401", "reservas_sin_token_401",
                "docente_login_permitido", "docente_crea_consulta_cancela",
                "admin_piso_scope_permitido", "admin_piso_fuera_scope_403",
            ]
            maintenance = [(name, "lines", 80.0, 70.0) for name in
                           ("auth", "usuarios", "academico", "gateway", "web", "android")]
            maintenance.append(("reservas", "lines", 80.0, 80.0))
            maintenance.extend((("reservas", "branch", 60.0, 48.0),
                                ("web", "branches", 80.0, 70.0),
                                ("web", "functions", 80.0, 70.0),
                                ("web", "statements", 80.0, 70.0)))
            for number in (1, 2, 3):
                sec = raw / "e3_seguridad" / f"rep-{number:02d}"
                self.manifest(sec, "seguridad_gateway")
                with (sec / "decisiones.csv").open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.DictWriter(handle, fieldnames=security_fields); writer.writeheader()
                    for identifier in identifiers:
                        writer.writerow({"decision_id": identifier, "expected_http": "200",
                                         "observed_http": "200", "assertion_pass": "True", "attempt": 0})
                maint = raw / "e3_mantenibilidad" / f"rep-{number:02d}"
                self.manifest(maint, "mantenibilidad")
                with (maint / "metricas.csv").open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.DictWriter(handle, fieldnames=("component", "metric", "percentage", "threshold", "exit_code")); writer.writeheader()
                    for component, metric, percentage, threshold in maintenance:
                        writer.writerow({"component": component, "metric": metric,
                                         "percentage": percentage, "threshold": threshold, "exit_code": 0})
                for component in ("auth", "usuarios", "academico", "reservas", "gateway"):
                    report = maint / component / "report"
                    report.mkdir(parents=True)
                    (report / "jacoco.csv").write_text(
                        "GROUP,PACKAGE,CLASS,INSTRUCTION_MISSED,INSTRUCTION_COVERED,BRANCH_MISSED,BRANCH_COVERED,LINE_MISSED,LINE_COVERED,COMPLEXITY_MISSED,COMPLEXITY_COVERED,METHOD_MISSED,METHOD_COVERED\n"
                        f"{component},example,Example,0,0,0,0,20,80,2,8,0,0\n",
                        encoding="utf-8",
                    )
                comp = raw / "e3_compatibilidad" / f"rep-{number:02d}"
                self.manifest(comp, "compatibilidad_web")
                for motor in ("chromium", "firefox", "webkit"):
                    target = comp / motor; target.mkdir()
                    (target / "summary.json").write_text(json.dumps({
                        "total": 5, "passed": 5, "failed": 0, "skipped": 0,
                        "flaky": 0, "interrupted": 0, "exit_code": 0,
                    }), encoding="utf-8")
            result = analyze_all(raw)
            self.assertEqual(result["security"]["decision"], "CUMPLE")
            self.assertEqual(result["maintenance"]["decision"], "CUMPLE")
            self.assertEqual(result["compatibility"]["decision"], "CUMPLE")
            self.assertEqual(result["security"]["total"], 7)
            self.assertEqual(result["compatibility"]["motors"]["chromium"]["total"], 5)
            self.assertEqual(result["maintenance"]["metrics"][2]["values"], [80.0, 80.0, 80.0])
            self.assertEqual(result["maintenance"]["complexity"]["usuarios"]["complexity_total"], 10)
            self.assertTrue(math.isclose(result["security"]["wilson95"][1], 1.0))
            decisions = raw / "e3_seguridad" / "rep-03" / "decisiones.csv"
            with decisions.open(encoding="utf-8") as handle:
                changed = list(csv.DictReader(handle))
            changed[0]["observed_http"] = "403"
            changed[0]["assertion_pass"] = "False"
            with decisions.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=security_fields)
                writer.writeheader(); writer.writerows(changed)
            with self.assertRaisesRegex(ValueError, "diverge"):
                analyze_all(raw)


if __name__ == "__main__":
    unittest.main()
