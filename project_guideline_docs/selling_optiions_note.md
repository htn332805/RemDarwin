## Summary

- Combined plan for an institutional-grade automated options-selling system focused on covered calls and cash‑secured puts.
- Architecture layers: data ingestion, option chain fetcher, Greeks & IV surface builders, quantitative screening, LLM interpretation, decision matrix, execution/routing, monitoring, backtesting, and reporting.
- System is regime-aware: normal, high volatility, earnings, holidays, sector events, and portfolio-level coordination influence filters, thresholds, and sizing.
- Emphasis on performance, validation, caching, and scalability: low-latency updates, high coverage, and automated quality checks.

## Action Items

- **(Phase 1 – Team)** Implement option chain fetcher, Greeks calculator, and basic quantitative filters.
- **(Phase 1 – Team)** Add bid/ask spreads, liquidity metrics, and database schema with partitioning/indexes.
- **(Phase 2 (Weeks 5-8) – Team)** Build IV surface builder, expiration-range filters, and integrate LLM decision layer.
- **(Phase 3 (Weeks 9-12) – Team)** Implement loss-potential limits, position-sizing, and full risk-management rules; run backtests.
- **(Phase 4 (Weeks 13-16) – Team)** Deliver execution interface, multi-broker routing, and monitoring dashboards.
- **(Phase 5 (Weeks 17-20) – Team)** Run live testing, reconcile, and deploy to production; tune thresholds.
- **(Ongoing – System/Operations)** Backtest across regimes, calibrate composite thresholds quarterly, and monitor automated vs override frequency.
- **(Quarterly – System)** Recalibrate composite threshold and filter parameters using backtesting and Monte Carlo.

## Data Collection & Validation

- Goals: full option-chain coverage, Greeks, IV surfaces, open interest/volume, bid/ask spreads, and frequent quote updates with validation/gap-filling.
- Validators perform structure checks, underlying price parity, per-contract checks (bid/ask, Greeks, IV, volume, OI, DTE), and gap-filling via interpolation while marking filled entries.
- Performance targets: &gt;95% coverage overall, chain-refresh latency &lt;10s, Greeks within 0.5–1% of industry, validated updates stored with quality score.
- Caching and batch classes used to meet latency targets and scale to 10k+ evaluations.

| **Component** | **Key Responsibilities** | **Target Metrics** |
| --- | --- | --- |
| Option Chain Fetcher | Fetch full chain, bid/ask, OI/volume, cache results | &gt;99.5% fetch success, &lt;8s avg fetch |
| Greeks Calculator | Black‑Scholes Greeks, batch/caching, fallback to API | Greeks within 0.5% industry, &lt;50ms w/ cache |
| IV Surface Builder | Build/interpolate strike×expiry matrix, store stats | &lt;100ms build, &gt;90% coverage |
| Real-Time Quote Manager | Async updates, alerting, validation | &lt;30s latency, support 500+ symbols |
| Data Validator | Structure checks, gap-fill, parity checks | Quality score reported; minimal false fills |

## Liquidity, Bid/Ask, And Thresholds

- Liquidity metrics: spread_pct, volume_score, open_interest_score, composite liquidity_score, effective_spread, market_impact_estimate.
- Contracts are scored and marked liquid/illiquid using percentile thresholds; thresholds adapt by regime (e.g., tighter in normal, stricter size limits in high volatility).
- AdaptiveLiquidityManager provides preset thresholds (normal, high‑vol, earnings, holiday, sector, portfolio) and assesses portfolio-level liquidity quickly.

## Screening Filters And Rules

- Core quantitative filters: premium yield, delta range, IV percentile, expiration window, liquidity thresholds, ownership/cash verification, credit/sector limits.
- Premium yield: annualized yield = (premium / underlying) \* (days_in_year / DTE) adjusted for spreads and costs; default min \~2–3% but regime-adjusted.
- Delta filter: target moderate OTM delta \~0.15–0.35; widen/contract by regime.
- IV percentile: percentile vs 365-day lookback, typical acceptable range 20–60%, with regime-dependent adjustments.
- Expiration windows: base 30–90 days, adjusted for volatility/earnings/holidays.
- Cash-secured put checklist: 100% cash, premium yield &gt;3% typical, delta -0.15 to -0.35, earnings &gt;14 days, credit ≥BBB+, sector diversification caps.

| **Filter** | **Primary Rule** | **Regime Adjustments** |
| --- | --- | --- |
| Premium Yield | Min annualized yield (\~2–3%) | Lenient in high vol, stricter near earnings |
| Delta Range | 0.15–0.35 target | Expand in high vol, constrict near earnings |
| IV Percentile | 20–60% typical | Expand in crises, constrict for earnings |
| Expiration Range | 30–90 days base | Shorten near earnings, lengthen for holidays |
| Liquidity Thresholds | Min OI/volume, max spread_pct | Tighten in low-liquidity regimes |

## Ownership Verification And Cash Checks

- StockOwnershipVerifier confirms owned quantity, settlement status, margin availability, and caches positions briefly (e.g., 5 minutes).
- Covered calls blocked without verified ownership; cash-secured puts require full cash coverage.
- Verification includes warnings and recommended actions (do not execute, increase margin, reduce size).

## Decision Framework And LLM Integration

- Composite Score = 0.7*quantitative + 0.2*LLM + 0.1\*risk_adjustment.
- Execution gate: ≥7.5/10 (baseline) allows full automated execution; 6.5–7.4 requires human review/partial sizing; &lt;6.5 rejects and escalates.
- LLM provides narrative, scenario analysis, exit strategies, and a confidence score; confidence bands alter sizing (e.g., &gt;0.8 full, 0.6–0.8 reduce).
- Human-in-the-loop: mandatory for borderline scores and crisis regimes; target override frequency &lt;5–10%.
- LLM performance targets: &gt;85% alignment with quantitative signals, response &lt;5s, cost constraints per usage.

## Execution, Routing, And Order Rules

- Order types: limit preferred, market/IOC for urgent cases; TIF chosen by event timing (Day, GTC, IOC, FOK, GTD).
- Limit price logic: aim near midpoint with concession (e.g., 0.5–1% better than midpoint), adjust for spread & IV.
- Multi-broker routing to optimize fills and diversify counterparty risk.
- Execution monitoring: real-time fill tracking, auto-repricing for partial fills, slippage alerts (&gt;2% premium), and reconciliation.

## Risk Management, Position Sizing, And Loss Monitoring

- Position sizing: max \~5% per trade, max 10 positions baseline; sector concentration caps (25% baseline, 20% for cash-secured puts).
- Greeks limits: net delta ±0.2, gamma ±0.05, vega notional &lt;2% portfolio (example targets).
- LossPotentialLimits aim practical loss exposure ≤5% position value; LossPotentialMonitor flags breaches and recommends size reductions.
- Stop-loss/adjustment rules: triggers on premium decay (20%), volatility spikes, or breach of loss potential; portfolio VaR and stress tests run regularly.
- Operational SLAs: execution success &gt;99%, alert latency &lt;1 minute for critical alerts, monitoring latency targets &lt;30s–1min depending on severity.

## Backtesting, Optimization, And Validation

- Backtests require 10+ years options history, regime tagging, walk-forward tests, transaction-cost modeling.
- Optimization: genetic algorithms for thresholds, Monte Carlo for weight calibration, seasonal adjustments.
- Targets: backtested Sharpe &gt;1.2–1.5, out-of-sample within \~10% of in-sample, max drawdown &lt;15% (goal).
- Validation: calibrate LLM outputs against outcomes and validate daily reconciliation and weekly stress tests.

| **Area** | **Method** | **Success Criteria** |
| --- | --- | --- |
| Backtesting | 10+ years, walk-forward, regime segmentation | Sharpe &gt;1.2, OOS within 10% |
| Optimization | Genetic algs, Monte Carlo | Stable thresholds across regimes |
| LLM Calibration | Compare narratives to outcomes | &gt;85% alignment with quantitative signals |
| Monitoring | Real-time P&L, Greeks, alerts | Uptime 99.9%, alert latency &lt;1 min |

## Monitoring, Reporting, And Dashboards

- Dashboards: real-time P&L, Greeks visualization, sector exposures, liquidity metrics, and alerts (Info→Warning→Critical→Emergency).
- Reporting: automated monthly reports with trade rationale, attribution, tax export, and benchmark comparisons.
- Alerts escalate by severity with automated mitigation actions and human escalation for critical events.

## Decisions

- Adopt the composite scoring with 70/20/10 weighting and 7.5/10 baseline for automated full execution.
- Require human review for borderline composite scores and tighten automation in crisis regimes.
- Use regime-aware adaptive filters across IV percentiles, expiration ranges, and liquidity thresholds.
- Prioritize caching and batch processing to meet latency targets for screening and LLM calls.