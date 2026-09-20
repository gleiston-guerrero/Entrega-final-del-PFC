"""Pruebas de integridad: las mutaciones ocurren solo en temporales."""
import contextlib
import hashlib
import importlib.util
import io
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/verificar-manifiestos.py"
spec = importlib.util.spec_from_file_location("verificador", SCRIPT)
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.manifests = []
        for directory, name in [("a", "SHA256SUMS"), ("b", "SHA256SUMS.txt"),
                                ("c", "MANIFEST-SHA256.txt")]:
            folder = self.root / directory
            folder.mkdir()
            (folder / "dato con espacio.bin").write_bytes(b"historico\r\n")
            digest = hashlib.sha256(b"historico\r\n").hexdigest()
            (folder / name).write_text(f"{digest}  dato con espacio.bin\n", encoding="utf-8")
            self.manifests.append(f"{directory}/{name}")

    def run_cli(self, manifests=None):
        command = [sys.executable, str(SCRIPT), "--root", str(self.root)]
        for manifest in self.manifests if manifests is None else manifests:
            command.extend(["--manifest", manifest])
        return subprocess.run(command, capture_output=True, text=True)

    def test_valid_manifests_exit_zero(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("manifests=3 entries=3 ok=3 failed=0", result.stdout)

    def test_one_byte_mismatch_exit_nonzero(self):
        path = self.root / "b/dato con espacio.bin"
        data = bytearray(path.read_bytes())
        data[0] ^= 1
        path.write_bytes(data)
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("MISMATCH: b/SHA256SUMS.txt", result.stdout)

    def test_missing_exit_nonzero(self):
        (self.root / "c/dato con espacio.bin").unlink()
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("MISSING: c/MANIFEST-SHA256.txt", result.stdout)

    def test_malformed_and_empty_fail(self):
        for text in ["invalid\n", "", "a" * 64 + " x missing-separator\n"]:
            with self.subTest(text=text):
                (self.root / self.manifests[0]).write_text(text)
                self.assertNotEqual(self.run_cli().returncode, 0)

    def test_unreadable_entry_fails(self):
        path = self.root / "a/dato con espacio.bin"
        path.unlink()
        path.mkdir()
        self.assertNotEqual(self.run_cli().returncode, 0)

    def test_missing_manifest_fails(self):
        (self.root / self.manifests[0]).unlink()
        self.assertNotEqual(self.run_cli().returncode, 0)

    def test_discovery_uses_git_and_allowlist(self):
        output = "\0".join(self.manifests + ["a/not-a-manifest.txt", "a/SHA256SUMS.bak", ""])
        with patch.object(verifier.subprocess, "run") as run:
            run.return_value.stdout = output.encode()
            self.assertEqual(verifier.discover(self.root), self.manifests)
            self.assertEqual(run.call_args.args[0],
                             ["git", "-C", str(self.root), "ls-files", "-z", "--cached"])
            verifier.discover(self.root, True)
            self.assertIn("--others", run.call_args.args[0])

    def test_real_tracked_discovery_includes_evidence17_and_smoke(self):
        manifests = verifier.discover(ROOT)
        self.assertGreater(len(manifests), 1)
        self.assertIn("experimentos/evidencia-17/20260916/SHA256SUMS.txt", manifests)
        self.assertIn("experimentos/evidencia-e2/smoke-refresh-25m/SHA256SUMS.txt", manifests)

    def test_root_based_historical_manifest(self):
        manifest = "experimentos/resultados/SHA256SUMS"
        target = self.root / manifest
        target.parent.mkdir(parents=True)
        digest = hashlib.sha256(b"historico\r\n").hexdigest()
        target.write_text(f"{digest} *a/dato con espacio.bin\n")
        self.assertEqual(self.run_cli([manifest]).returncode, 0)

    def test_invalid_paths_and_duplicates_fail(self):
        digest = "0" * 64
        for path in ["../outside", "/absolute", "C:/absolute", "back\\slash"]:
            with self.subTest(path=path):
                (self.root / self.manifests[0]).write_text(f"{digest}  {path}\n")
                self.assertNotEqual(self.run_cli().returncode, 0)
        with self.assertRaises(ValueError):
            verifier.parse(f"{digest}  x\n{digest}  ./x\n")

    def test_empty_discovery_fails(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertGreater(verifier.verify(self.root, [])["failed"], 0)

    def test_real_evidence17_temporary_copy(self):
        source = ROOT / "experimentos/evidencia-17/20260916"
        destination = self.root / "evidencia17"
        shutil.copytree(source, destination)
        manifests = ["evidencia17/SHA256SUMS.txt"]
        result = self.run_cli(manifests)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("entries=50 ok=50 failed=0", result.stdout)
        _, relative = verifier.parse((destination / "SHA256SUMS.txt").read_text())[0]
        target = destination / relative
        content = bytearray(target.read_bytes())
        content[0] ^= 1
        target.write_bytes(content)
        result = self.run_cli(manifests)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("MISMATCH", result.stdout)
        target.unlink()
        result = self.run_cli(manifests)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("MISSING", result.stdout)


if __name__ == "__main__":
    unittest.main()
