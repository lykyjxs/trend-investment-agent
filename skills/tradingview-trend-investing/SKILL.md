---
name: tradingview-trend-investing
description: Use when applying the 扫地僧 trend-investing framework in TradingView to screen or review A-share, Hong Kong, or US stocks, including Stage 2, VCP, pivot, near-buy watchlists, newly triggered buy points, or a daily market review.
---

# TradingView 趋势投资

Use only TradingView UI data for market screening and chart review. Never place an order. Treat any condition-order price as a reference that the user must verify and enter personally. Do not use another website, API, package, search result, cached quote, or old report to fill a missing TradingView field.

## Load only what the current step needs

- Read [strategy rules](references/strategy-rules.md) before classifying Stage 2, VCP, pivots, observation candidates, or new triggers.
- Read [scoring rubric](references/scoring-rubric.md) before assigning the 100-point score.
- Read [TradingView workflow](references/tradingview-workflow.md) before operating the screener or charts.
- Read [casebook](references/casebook.md) only when a chart pattern is ambiguous or an example would resolve it.
- Read [course notes](references/course-notes.md) only when distilled rules do not answer a theory question or the user asks for the original basis.
- Use the [daily report template](assets/daily-report-template.md) for a normal run, the [no-new-data template](assets/no-new-data-template.md) when no market has a new completed session, and the [data-failure template](assets/data-failure-template.md) for partial or total TradingView failure.
- Use [trade metric calculator](scripts/calculate_trade_metrics.py) for pivot distance, risk, reward, R multiple, and 2R target. Supply only prices read from the current TradingView UI.

## Non-negotiable decisions

- The observation list is the primary section: current price below the pivot by no more than 8%, score at least 60, at most 10 names per market.
- A final contraction above 8% and up to 12%, or risk above 8% and up to 12%, is observation-only and must carry the specific downgrade reason. Above 12% is excluded.
- A new trigger is a first breakout on the latest completed session, no more than 8% above the pivot, with final contraction and risk no more than 8%. List every qualifying new trigger.
- On the first run, look back 5 trading days. Later, report only the previous completed session's new triggers and suppress names already reported in this Codex task.
- A reward below 2R does not erase a breakout. Keep it in the new-trigger section and mark it not recommended.
- If no objective overhead swing high exists, write “no clear pressure” and show a separately labelled 2R target. Never call the calculated target a pressure level.
- Volume and relative volume are status fields, not score components.
- Show the company name and TradingView industry, but never show the ticker/code in the user-facing report.

## Run sequence

1. Check TradingView login, market data dates, and the latest report in this task.
2. Screen CN, HK, and US common stocks with the local-currency market-cap and moving-average filters in the workflow.
3. Map each company to the correct market index from its TradingView industry.
4. Review index and stock weekly/daily charts; identify stage, VCP, pivot, support, pressure, risk, and danger signals.
5. Calculate metrics, apply hard gates, then score. Never use score to override a hard exclusion.
6. Build the primary observation list and the secondary incremental new-trigger list.
7. Render the appropriate template and state every missing TradingView field or failed market.

## Final check

Before sending, verify the data source is TradingView-only, observation/breakout direction is correct, 8% and 12% boundaries are inclusive as specified, new triggers are deduplicated, 2R is not mislabelled as pressure, no code is shown, and no order was placed.
