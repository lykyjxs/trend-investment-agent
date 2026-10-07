#!/usr/bin/env python3
"""Calculate reproducible trade metrics from TradingView-read prices.

This module performs arithmetic only. It does not fetch market data, inspect
charts, classify patterns, or place orders.
"""

from __future__ import annotations

import json
import math
import sys
from typing import Any


def _positive_number(name: str, value: float) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value <= 0
    ):
        raise ValueError(f"{name} must be a positive number")
    return float(value)


def classify_band(
    value: float,
    normal_max: float = 8.0,
    watch_max: float = 12.0,
) -> str:
    """Classify a non-negative percentage using inclusive upper bounds."""
    for name, number in (
        ("value", value),
        ("normal_max", normal_max),
        ("watch_max", watch_max),
    ):
        if (
            isinstance(number, bool)
            or not isinstance(number, (int, float))
            or not math.isfinite(number)
        ):
            raise ValueError(f"{name} must be a finite number")
    if value < 0:
        raise ValueError("value must be non-negative")
    if normal_max < 0 or watch_max < normal_max:
        raise ValueError("thresholds must satisfy 0 <= normal_max <= watch_max")
    if value <= normal_max:
        return "normal"
    if value <= watch_max:
        return "watch"
    return "exclude"


def calculate_metrics(
    current_price: float,
    pivot_price: float,
    support_price: float,
    pressure_price: float | None = None,
) -> dict[str, float | None]:
    """Return unrounded distance, risk, reward, R multiple, and 2R target."""
    current = _positive_number("current_price", current_price)
    pivot = _positive_number("pivot_price", pivot_price)
    support = _positive_number("support_price", support_price)
    pressure = (
        None
        if pressure_price is None
        else _positive_number("pressure_price", pressure_price)
    )

    if support >= current:
        raise ValueError("support_price must be below current_price")

    pivot_distance_pct = (current - pivot) / pivot * 100
    potential_loss_pct = (current - support) / current * 100
    two_r_target = current + 2 * (current - support)

    potential_gain_pct = None
    reward_risk = None
    if pressure is not None:
        potential_gain_pct = (pressure - current) / current * 100
        reward_risk = potential_gain_pct / potential_loss_pct

    return {
        "pivot_distance_pct": pivot_distance_pct,
        "potential_loss_pct": potential_loss_pct,
        "potential_gain_pct": potential_gain_pct,
        "reward_risk": reward_risk,
        "two_r_target": two_r_target,
    }


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("Usage: calculate_trade_metrics.py '<json-object>'", file=sys.stderr)
        return 2

    try:
        payload: dict[str, Any] = json.loads(args[0])
        result = calculate_metrics(**payload)
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
