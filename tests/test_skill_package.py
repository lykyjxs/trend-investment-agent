from __future__ import annotations

import re
import unittest
from pathlib import Path
from urllib.parse import unquote

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "tradingview-trend-investing"
REQUIRED = {
    "SKILL.md",
    "install-manifest.txt",
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
    def test_canonical_market_cap_floor_is_50_billion_local_currency(self) -> None:
        strategy = (SKILL_ROOT / "references" / "strategy-rules.md").read_text(
            encoding="utf-8"
        )
        workflow = (SKILL_ROOT / "references" / "tradingview-workflow.md").read_text(
            encoding="utf-8"
        )
        prompt = (REPO_ROOT / "automation" / "daily-trend-report-prompt.md").read_text(
            encoding="utf-8"
        )
        normative_text = strategy + workflow + prompt
        self.assertIn("500 亿", normative_text)
        self.assertNotIn("400 亿", normative_text)

    def test_repository_readme_is_english_and_documents_the_market_cap_floor(self) -> None:
        readme_file = REPO_ROOT / "README.md"
        self.assertTrue(readme_file.is_file(), "README.md must exist")
        readme = readme_file.read_text(encoding="utf-8")
        self.assertIn("TradingView Trend Investing Agent", readme)
        self.assertIn("50 billion", readme)
        self.assertIn("local currency", readme)
        self.assertIn("TradingView", readme)

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
            "对应环境基准及阶段",
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

    def test_hard_exclusions_are_consistent_across_references(self) -> None:
        rubric = (SKILL_ROOT / "references" / "scoring-rubric.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("明显 Stage 4", rubric)
        self.assertIn("排除观察名单和新触发", rubric)
        self.assertNotIn("必要时排除观察", rubric)

    def test_failure_template_separates_field_and_market_failures(self) -> None:
        template = (SKILL_ROOT / "assets" / "data-failure-template.md").read_text(
            encoding="utf-8"
        )
        for heading in (
            "### 可选状态字段失败",
            "### 必需判断字段失败",
            "### 整个市场失败",
        ):
            self.assertIn(heading, template)
        self.assertIn("保留其余可可靠生成的候选与评分", template)
        self.assertIn("相对成交量", template)
        self.assertIn("不生成依赖该字段的候选与评分", template)

    def test_operational_contracts_are_executable_assertions(self) -> None:
        strategy = (SKILL_ROOT / "references" / "strategy-rules.md").read_text(
            encoding="utf-8"
        )
        workflow = (SKILL_ROOT / "references" / "tradingview-workflow.md").read_text(
            encoding="utf-8"
        )
        template = (SKILL_ROOT / "assets" / "daily-report-template.md").read_text(
            encoding="utf-8"
        )
        for text in (
            "位于枢纽点下方",
            "位于枢纽点上方",
            "最近 5 个交易日",
            "只列上一完整交易日",
            "恒生科技",
            "恒生指数",
            "纳斯达克 100",
            "标普 500",
            "无明确压力位",
            "2R 目标",
        ):
            self.assertIn(text, strategy + workflow + template)
        self.assertIn("只列以前未在本任务报告过的首次突破", template)
        self.assertNotRegex(template, r"(?m)^[-*]\s*(?:股票)?代码\s*[：:]")

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

    def test_daily_automation_prompt_preserves_report_contract(self) -> None:
        prompt_file = REPO_ROOT / "automation" / "daily-trend-report-prompt.md"
        self.assertTrue(prompt_file.is_file(), "daily automation prompt must exist")
        prompt = prompt_file.read_text(encoding="utf-8")
        for required_text in (
            "$tradingview-trend-investing",
            "只能使用 TradingView",
            "最近一个完整交易日",
            "每个市场最多 10 只",
            "全部列出",
            "同一任务",
            "不要显示股票代码",
            "不得下单",
            "无新数据",
            "部分失败",
        ):
            self.assertIn(required_text, prompt)


if __name__ == "__main__":
    unittest.main()
