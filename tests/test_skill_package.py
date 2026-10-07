from __future__ import annotations

import re
import unittest
from pathlib import Path
from urllib.parse import unquote

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
REQUIRED_ROUTES = {
    "references/strategy-rules.md",
    "references/scoring-rubric.md",
    "references/tradingview-workflow.md",
    "references/casebook.md",
    "references/course-notes.md",
    "assets/daily-report-template.md",
    "assets/no-new-data-template.md",
    "assets/data-failure-template.md",
    "scripts/calculate_trade_metrics.py",
}


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

    def test_skill_routes_to_each_supporting_resource(self) -> None:
        content = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        links = set(re.findall(r"\[[^\]]+\]\(([^)]+)\)", content))
        self.assertTrue(
            REQUIRED_ROUTES <= links,
            f"SKILL.md is missing resource routes: {sorted(REQUIRED_ROUTES - links)}",
        )
        broken = sorted(link for link in links if not (SKILL_ROOT / link).is_file())
        self.assertEqual([], broken, f"SKILL.md contains broken routes: {broken}")

    def test_skill_uses_progressive_disclosure(self) -> None:
        content = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        course = (SKILL_ROOT / "references" / "course-notes.md").read_text(
            encoding="utf-8"
        )
        self.assertLess(len(content), 12_000, "SKILL.md should stay operational and compact")
        self.assertLess(len(content), len(course) // 4)

    def test_daily_template_has_report_sections_in_operational_order(self) -> None:
        template_file = SKILL_ROOT / "assets" / "daily-report-template.md"
        self.assertTrue(template_file.is_file(), "daily report template must exist")
        template = template_file.read_text(encoding="utf-8")
        headings = [
            "## 市场摘要",
            "## 接近买点观察名单（主体）",
            "## 上一交易日新触发买点（次要）",
            "## 异常与缺失",
        ]
        positions = [template.find(heading) for heading in headings]
        self.assertTrue(all(position >= 0 for position in positions), positions)
        self.assertEqual(sorted(positions), positions)
        self.assertIn("每市场最多 10 只", template)
        self.assertIn("符合者全部列出，不设数量上限", template)

    def test_daily_template_stock_entry_exposes_required_decision_fields(self) -> None:
        template_file = SKILL_ROOT / "assets" / "daily-report-template.md"
        self.assertTrue(template_file.is_file(), "daily report template must exist")
        template = template_file.read_text(encoding="utf-8")
        required_labels = {
            "股票名称",
            "行业",
            "当前价",
            "枢纽价",
            "距枢纽点",
            "条件单参考触发价",
            "支撑位",
            "止损参考价",
            "潜在亏损",
            "压力位或 2R 目标",
            "预期盈利",
            "盈亏比",
            "最终收缩",
            "评分",
            "优势",
            "缺失条件",
            "主要风险",
            "降级说明",
        }
        missing = sorted(label for label in required_labels if label not in template)
        self.assertEqual([], missing, f"missing report fields: {missing}")
        self.assertNotRegex(template, r"(?m)^[-*]\s*(?:股票)?代码\s*[：:]")
        self.assertIn("最终收缩 8%–12% 降级", template)
        self.assertIn("潜在亏损 8%–12% 降级", template)

    def test_casebook_links_only_to_bundled_images(self) -> None:
        casebook_file = SKILL_ROOT / "references" / "casebook.md"
        self.assertTrue(casebook_file.is_file(), "casebook must exist")
        casebook = casebook_file.read_text(encoding="utf-8")
        for case_name in (
            "NVIDIA",
            "腾讯",
            "捷蓝航空",
            "eBay",
            "DICK'S Sporting Goods",
            "小米",
            "移动止损与加仓",
        ):
            self.assertIn(case_name, casebook)
        image_links = re.findall(r"!\[[^\]]*\]\((images/[^)]+)\)", casebook)
        self.assertTrue(image_links, "casebook must include bundled image links")
        broken = [
            link
            for link in image_links
            if not (SKILL_ROOT / "references" / unquote(link)).is_file()
        ]
        self.assertEqual([], broken, f"casebook has broken image links: {broken}")


if __name__ == "__main__":
    unittest.main()
