# TradingView Trend Investing Agent

This repository packages the trend-investing framework taught by the Chinese creator Saodisang as a reusable Codex skill. It is designed for a daily, research-only review of A-share, Hong Kong, and US stocks in TradingView.

The project does not place orders. It produces watchlists, risk calculations, and conditional-order reference prices that must be reviewed and entered by the user.

## What the skill does

- Screens A-share, Hong Kong, and US common stocks in the TradingView web interface.
- Reviews Stage 2 trends, volatility contraction patterns (VCP), pivots, support, resistance, and risk.
- Prioritizes stocks that are approaching a valid buy point.
- Reports every newly triggered buy point that satisfies the hard rules.
- Produces a structured daily report without displaying ticker symbols.
- Uses a deterministic local script for arithmetic such as pivot distance, loss percentage, reward-to-risk ratio, and 2R targets.

Market data must come from the current TradingView user interface. Search engines, other financial websites, market-data APIs, cached quotes, and previous reports may not be used to fill missing fields.

## Canonical screening rules

The initial TradingView screen uses the same hard conditions in all three markets:

- Common stock
- Market capitalization greater than **50 billion in the market's local currency**
  - A-share: more than CNY 50 billion
  - Hong Kong: more than HKD 50 billion
  - United States: more than USD 50 billion
- Price > SMA50
- SMA50 > SMA150
- SMA150 > SMA200

Passing the screen only establishes a trend-qualified candidate pool. It does not mean that a valid buy point exists.

## Daily report

The report is centered on the near-buy watchlist:

- The current price must be below the pivot and no more than 8% away.
- The score must be at least 60 out of 100.
- Each market may contain at most 10 observation candidates.
- A final contraction or stop risk above 8% and up to 12% is downgraded and explicitly labelled.
- Values above 12% are excluded.

The secondary section lists newly triggered buy points:

- The latest completed session must be the first breakout above the pivot.
- The price may be no more than 8% above the pivot.
- Final contraction and potential loss must both be no more than 8%.
- Every qualifying new trigger is included; there is no per-market limit.

The first run reviews the latest five trading sessions to establish a baseline. Later runs report only first-time triggers from the latest completed session that have not already appeared in the same Codex task.

## Market benchmarks

- A-share: CSI 300
- Hong Kong technology-related industries: Hang Seng TECH Index
- Other Hong Kong industries: Hang Seng Index
- US technology-related industries: Nasdaq-100
- Other US industries: S&P 500

Industry classification must be read from TradingView rather than inferred from the company name.

## Repository structure

```text
automation/                         Daily automation prompt
docs/superpowers/                   Design and implementation records
evals/tradingview-trend-investing/  Behavioral evaluation scenarios
skills/tradingview-trend-investing/ Installable Codex skill
tests/                              Package, installer, and calculator tests
tools/                              Reference builder and installer
trend-investment.md                 Distilled source-course transcript
trend-investment-images/            Source images used by the notes
```

The skill package contains:

- `SKILL.md` — compact operating instructions and resource routing
- `references/strategy-rules.md` — canonical classification and risk rules
- `references/scoring-rubric.md` — the 100-point scoring model
- `references/tradingview-workflow.md` — TradingView-only operating procedure
- `references/casebook.md` — selected chart examples
- `references/course-notes.md` — the source notes for theory lookups
- `assets/` — daily, no-new-data, and failure report templates
- `scripts/calculate_trade_metrics.py` — arithmetic-only trade metric calculator

## Install the skill

From PowerShell at the repository root:

```powershell
.\tools\install-tradingview-trend-skill.ps1
```

The installer copies only files listed in the skill manifest to:

```text
C:\Users\<username>\.codex\skills\tradingview-trend-investing
```

It verifies every copied file with SHA-256.

## Run the tests

```powershell
python -m unittest discover -s tests -v
```

Validate the skill metadata and package structure with the Codex skill validator when it is available in the local runtime.

## Daily automation

`automation/daily-trend-report-prompt.md` contains the prompt used by the 08:00 Asia/Shanghai daily task. The task opens TradingView through the local browser, checks the latest completed trading session for each market, and sends either:

- the complete report,
- a concise no-new-data message, or
- an explicit partial or total data-failure report.

The automation must not substitute approximate moving-average filters when the saved TradingView screener, login, subscription, or market permissions prevent verification.

## Disclaimer

This repository is for research and education only. It does not provide personalized investment advice, execute trades, or guarantee that a breakout, support level, target, or rating will be correct.
