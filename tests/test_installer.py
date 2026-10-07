from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = REPO_ROOT / "tools" / "install-tradingview-trend-skill.ps1"
POWERSHELL = shutil.which("pwsh") or shutil.which("powershell")


class InstallerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(INSTALLER.is_file(), "installer script must exist")
        self.assertIsNotNone(POWERSHELL, "PowerShell executable is required")
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.source = self.root / "source" / "tradingview-trend-investing"
        self.destination = self.root / "personal-skills" / "tradingview-trend-investing"
        (self.source / "references").mkdir(parents=True)
        (self.source / "SKILL.md").write_text("skill-v1\n", encoding="utf-8")
        (self.source / "references" / "rules.md").write_text(
            "rules-v1\n", encoding="utf-8"
        )

    def run_installer(self, source: Path, destination: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                str(POWERSHELL),
                "-NoProfile",
                "-File",
                str(INSTALLER),
                "-Source",
                str(source),
                "-Destination",
                str(destination),
            ],
            capture_output=True,
            encoding="utf-8",
            text=True,
        )

    def test_installs_every_source_file_and_verifies_hashes(self) -> None:
        completed = self.run_installer(self.source, self.destination)

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("skill-v1\n", (self.destination / "SKILL.md").read_text())
        self.assertEqual(
            "rules-v1\n",
            (self.destination / "references" / "rules.md").read_text(),
        )
        self.assertIn("2 files", completed.stdout)
        self.assertIn("SHA-256", completed.stdout)

    def test_overwrites_matching_files_without_deleting_unrelated_target_files(self) -> None:
        self.destination.mkdir(parents=True)
        (self.destination / "SKILL.md").write_text("old\n", encoding="utf-8")
        (self.destination / "local-note.txt").write_text("keep\n", encoding="utf-8")

        completed = self.run_installer(self.source, self.destination)

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("skill-v1\n", (self.destination / "SKILL.md").read_text())
        self.assertEqual("keep\n", (self.destination / "local-note.txt").read_text())

    def test_rejects_a_destination_without_the_exact_skill_leaf_name(self) -> None:
        unsafe_destination = self.root / "personal-skills"

        completed = self.run_installer(self.source, unsafe_destination)

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("destination leaf", completed.stderr.lower())
        self.assertFalse((unsafe_destination / "SKILL.md").exists())

    def test_rejects_a_source_without_the_exact_skill_leaf_name(self) -> None:
        unsafe_source = self.root / "source"

        completed = self.run_installer(unsafe_source, self.destination)

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("source leaf", completed.stderr.lower())
        self.assertFalse(self.destination.exists())


if __name__ == "__main__":
    unittest.main()
