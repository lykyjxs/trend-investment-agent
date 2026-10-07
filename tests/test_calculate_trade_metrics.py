from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "skills"
    / "tradingview-trend-investing"
    / "scripts"
    / "calculate_trade_metrics.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("calculate_trade_metrics", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class CalculateMetricsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(MODULE_PATH.is_file(), "metric calculator must exist")
        self.module = load_module()

    def test_calculates_signed_pivot_distance_and_trade_metrics(self) -> None:
        metrics = self.module.calculate_metrics(100, 105, 95, 120)

        self.assertAlmostEqual(-4.7619047619, metrics["pivot_distance_pct"])
        self.assertAlmostEqual(5.0, metrics["potential_loss_pct"])
        self.assertAlmostEqual(20.0, metrics["potential_gain_pct"])
        self.assertAlmostEqual(4.0, metrics["reward_risk"])
        self.assertAlmostEqual(110.0, metrics["two_r_target"])

    def test_reports_positive_distance_after_breakout(self) -> None:
        metrics = self.module.calculate_metrics(104, 100, 98, 110)
        self.assertAlmostEqual(4.0, metrics["pivot_distance_pct"])

    def test_uses_two_r_target_without_inventing_pressure_metrics(self) -> None:
        metrics = self.module.calculate_metrics(100, 98, 95)

        self.assertIsNone(metrics["potential_gain_pct"])
        self.assertIsNone(metrics["reward_risk"])
        self.assertAlmostEqual(110.0, metrics["two_r_target"])

    def test_classifies_inclusive_threshold_boundaries(self) -> None:
        cases = [
            (8.0, "normal"),
            (8.01, "watch"),
            (12.0, "watch"),
            (12.01, "exclude"),
        ]
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(expected, self.module.classify_band(value))

    def test_rejects_non_positive_prices(self) -> None:
        invalid_inputs = [
            (0, 100, 95, 120),
            (100, 0, 95, 120),
            (100, 105, 0, 120),
            (100, 105, 95, 0),
        ]
        for values in invalid_inputs:
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    self.module.calculate_metrics(*values)

    def test_rejects_support_without_positive_risk_distance(self) -> None:
        for support in (100, 101):
            with self.subTest(support=support):
                with self.assertRaises(ValueError):
                    self.module.calculate_metrics(100, 105, support, 120)

    def test_cli_accepts_json_and_emits_json(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                json.dumps(
                    {
                        "current_price": 100,
                        "pivot_price": 105,
                        "support_price": 95,
                        "pressure_price": None,
                    }
                ),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        result = json.loads(completed.stdout)
        self.assertAlmostEqual(-4.7619047619, result["pivot_distance_pct"])
        self.assertEqual(110.0, result["two_r_target"])


if __name__ == "__main__":
    unittest.main()
