import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="context-optimizer-test-")
        self.addCleanup(self.directory.cleanup)
        self.workspace = Path(self.directory.name)

    def run_cli(self, command: str, source: Path, output: Path) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(PROJECT_ROOT / "src")
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["PYTHONIOENCODING"] = "utf-8"
        return subprocess.run(
            [sys.executable, "-X", "utf8", "-m", "nexura_context_optimizer.cli",
             "--workspace", str(self.workspace), command, str(source), "--output", str(output)],
            cwd=self.workspace, env=environment, text=True, encoding="utf-8",
            capture_output=True, timeout=15,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
        )

    def test_optimize_and_restore_commands_round_trip_utf8_crlf_bom(self):
        block = "event=sintetico texto=áéíóú Ω 漢字 🙂 " * 8
        original = ("\ufeff" + "\r\n\r\n".join([block] * 6 + ["FINAL"]) + "\r\n").encode("utf-8")
        source = self.workspace / "source.txt"
        output = self.workspace / "nested" / "package.json"
        restored = self.workspace / "restored.txt"
        source.write_bytes(original)
        packed = self.run_cli("optimize", source, output)
        self.assertEqual(packed.returncode, 0, packed.stderr)
        package = json.loads(output.read_text(encoding="utf-8"))
        self.assertTrue(package["dictionary"])
        self.assertIn("CTX_REPEAT_V1", package["packed_text"])
        self.assertTrue(json.loads(packed.stdout)["round_trip_exact"])
        unpacked = self.run_cli("restore", output, restored)
        self.assertEqual(unpacked.returncode, 0, unpacked.stderr)
        self.assertEqual(restored.read_bytes(), original)
        self.assertEqual(source.read_bytes(), original)

    def test_existing_destination_is_never_overwritten_for_either_command(self):
        source = self.workspace / "source.txt"
        destination = self.workspace / "existing.txt"
        source.write_text("source remains intact", encoding="utf-8")
        destination.write_bytes(b"DO NOT REPLACE")
        for command in ("optimize", "restore"):
            with self.subTest(command=command):
                result = self.run_cli(command, source, destination)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(destination.read_bytes(), b"DO NOT REPLACE")

    @unittest.skipUnless(hasattr(os, "link"), "hard links unavailable")
    def test_hard_link_alias_cannot_overwrite_source(self):
        source = self.workspace / "source.txt"
        alias = self.workspace / "alias.txt"
        original = b"source remains intact"
        source.write_bytes(original)
        os.link(source, alias)
        result = self.run_cli("optimize", source, alias)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(source.read_bytes(), original)

    def test_input_and_output_outside_workspace_are_rejected(self):
        with tempfile.TemporaryDirectory(prefix="context-outside-") as outside:
            foreign = Path(outside) / "outside.txt"
            foreign.write_bytes(b"outside")
            local = self.workspace / "local.txt"
            local.write_bytes(b"local")
            cases = [(foreign, self.workspace / "new.json"), (local, Path(outside) / "new.json")]
            for source, output in cases:
                with self.subTest(source=source.name, output=str(output)):
                    result = self.run_cli("optimize", source, output)
                    self.assertEqual(result.returncode, 2)
                    self.assertFalse(output.exists())

    def test_corrupt_package_fails_without_writing_output(self):
        from nexura_context_optimizer.package import make_package
        package = make_package(b"synthetic text")
        package["packed_text"] = "changed text"
        source = self.workspace / "corrupt.json"
        output = self.workspace / "restored.txt"
        source.write_text(json.dumps(package), encoding="utf-8")
        result = self.run_cli("restore", source, output)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(output.exists())

    def test_invalid_utf8_fails_without_writing_output(self):
        source = self.workspace / "invalid.txt"
        output = self.workspace / "package.json"
        source.write_bytes(b"invalid: \xff")
        result = self.run_cli("optimize", source, output)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(output.exists())

    def test_invalid_and_duplicate_json_fail_without_writing_output(self):
        source = self.workspace / "invalid.json"
        output = self.workspace / "restored.txt"
        for content in ('{', '{"format": "a", "format": "b"}'):
            with self.subTest(content=content):
                source.write_text(content, encoding="utf-8")
                result = self.run_cli("restore", source, output)
                self.assertEqual(result.returncode, 2)
                self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
