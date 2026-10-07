from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "tradingview-trend-investing"
REQUIRED = {
    "SKILL.md",
    "agents/openai.yaml",
    "assets/daily-report-template.md",
    "assets/no-new-data-template.md",
    "assets/data-failure-template.md",
    "references/course-notes.md",
    "references/strategy-rules.md",
    "references/scoring-rubric.md",
    "references/tradingview-workflow.md",
    "references/casebook.md",
    "scripts/calculate_trade_metrics.py",
}
ALLOWED_FRONTMATTER = {"name", "description", "license", "allowed-tools", "metadata"}


class SkillPackageTests(unittest.TestCase):
    def test_required_package_files_exist(self) -> None:
        missing = sorted(path for path in REQUIRED if not (SKILL_ROOT / path).is_file())
        self.assertEqual([], missing, f"missing skill files: {missing}")

    def test_skill_frontmatter_is_complete_and_supported(self) -> None:
        skill_file = SKILL_ROOT / "SKILL.md"
        self.assertTrue(skill_file.is_file(), "SKILL.md must exist")
        content = skill_file.read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        self.assertIsNotNone(match, "SKILL.md must begin with YAML frontmatter")
        frontmatter = {}
        for line in match.group(1).splitlines():
            key, separator, value = line.partition(":")
            if separator:
                frontmatter[key.strip()] = value.strip().strip('"')
        self.assertEqual("tradingview-trend-investing", frontmatter.get("name"))
        self.assertTrue(frontmatter.get("description"))
        self.assertFalse(set(frontmatter) - ALLOWED_FRONTMATTER)
        self.assertNotIn("TODO", content)

    def test_openai_metadata_invokes_the_skill(self) -> None:
        metadata_file = SKILL_ROOT / "agents" / "openai.yaml"
        self.assertTrue(metadata_file.is_file(), "agents/openai.yaml must exist")
        metadata = metadata_file.read_text(encoding="utf-8")
        self.assertRegex(
            metadata,
            r'default_prompt:\s*"[^"]*\$tradingview-trend-investing[^"]*"',
        )
        self.assertRegex(metadata, r"allow_implicit_invocation:\s*true")
        self.assertNotRegex(metadata, r"(?m)^dependencies:")


if __name__ == "__main__":
    unittest.main()
