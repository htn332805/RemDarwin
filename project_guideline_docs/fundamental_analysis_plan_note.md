## Summary

- Project to build a financial-ratio calculation CLI and institutional analysis pipeline integrating rule-based scoring, peer benchmarking, valuation models, stress testing, and LLM-driven narratives.
- Core deliverables: a ratios/RatioCalculator class for compute\_{ratio}\_metric methods; a CLI to call metrics and batch analyses; compute_metrics() for categorized outputs and validation; ThresholdScorer, PeerComparator, DecisionMatrix, and LLM API layer.
- Institutional workflow: data validation/preparation → compute metrics → scoring and risk assessment → valuation and scenario analysis → LLM interpretive narratives → decision rules, automation, dashboards, monitoring, and backtesting.
- Priorities: robust input validation, division-by-zero handling, peer benchmarking, liquidity and cash-flow metrics, auditability of LLM outputs, and rigorous testing/backtesting before production.

## Action Items

- **(Implementer)** Build RatioCalculator class to compute liquidity, efficiency, profitability, solvency, valuation, and per-share ratios with validation and error handling.
- **(Implementer)** Implement CLI (command.py) using argparse mapping -m/--metric to compute methods; support positional numeric inputs converted to floats.
- **(Implementer)** Compile unique ratio list, define formulas and required inputs, and implement compute\_{ratio}\_metric methods with clear missing-input and division-by-zero messages.
- **(Implementer)** Create compute_metrics() to produce categorized ratio dictionary, skip missing metrics gracefully, and flag negative/zero/discordant values.
- **(Implementer)** Design ThresholdScorer and industry threshold library to map ratios to tiered scores and aggregate category scores.
- **(Implementer)** Develop PeerComparator for percentile, z-score, and quartile benchmarking using selected peer groups.
- **(Implementer)** Implement DecisionMatrix to weight valuation/quality/growth/risk by investment style and generate recommendations.
- **(Implementer)** Build valuation modules: DCF (multi-stage + sensitivity), multiples (P/E, EV/EBITDA, P/B, P/S), EV/FCF, FCF yield, PEG, and dividend sustainability checks.
- **(Implementer)** Add anomaly detection routines (Z-score, modified Z, IQR, Grubbs/Dixon; optional ML methods like isolation forest/autoencoders) and peer-benchmarking outputs.
- **(Implementer)** Create LLM API layer with prompt templates, caching, confidence scoring, logging, and QA for narrative outputs (drivers, risks, anomalies, scenarios).
- **(Implementer)** Implement CLI tooling for batch/portfolio analysis, LLM classification/regression CLIs, and nearest-neighbor/embedding-based peer discovery.
- **(Implementer)** Build dashboards (Dash/Plotly) showing overview, valuation, risk heatmaps, DCF sensitivity, Monte Carlo, and scenario toggles.
- **(Implementer)** Implement monitoring/alerting for feed issues, large metric shifts, catalysts, and model drift; include escalation protocols.
- **(Implementer)** Execute testing: unit tests for each compute method, integration tests for CLI, backtests (50–100 stocks), walk-forward validation of predictive models, and correlation checks vs. institutional ratings.
- \[ \] Decide canonical metric naming convention, input unit conventions, primary data sources for peers, default scoring thresholds, and CLI verbosity/narrative options.

## Ratios And Key Formulas

- Implement compute\_{ratio}\_metric methods grouped by category with input validation and returns as numeric values. Required rules: missing numeric inputs produce "Missing required input: {input_name}" and division-by-zero should produce clear errors.
- Liquidity: current_ratio = current_assets / current_liabilities; quick_ratio; cash_ratio.
- Efficiency: dso, dio, operating_cycle, dpo, ccc, receivables_turnover, inventory_turnover, asset_turnover, fixed_asset_turnover.
- Profitability: gross_profit_margin, operating_profit_margin, pretax_profit_margin, net_profit_margin, roa, roe, roce, effective_tax_rate, ebit_per_revenue.
- Solvency: debt_ratio, debt_equity_ratio, long_term_debt_to_cap, interest_coverage, cash_flow_to_debt, equity_multiplier.
- Valuation: price_book, price_sales, pe_ratio, price_cash_flow, dividend_yield, dividend_payout, ev_ebitda, market_cap_to_revenue, ev_fcf, fcf_yield.
- Per-Share: revenue_per_share, net_income_per_share, ocf_per_share, fcf_per_share, book_value_per_share, tangible_book_value_per_share, cash_per_share.

Table: Required Inputs And Example Formula

| **Metric** | **Required Inputs / Formula** |
| --- | --- |
| current_ratio | current_assets / current_liabilities |
| roa | net_income / total_assets |
| ev_ebitda | (enterprise_value) / ebitda |
| fcf_per_share | free_cash_flow / shares_outstanding |
| debt_equity_ratio | total_debt / total_equity |

## Compute Metrics, Validation, And Data Preparation

- compute_metrics() should return a structured dictionary of categories: liquidity, profitability, solvency, efficiency, valuation, per_share, cash_flow, expenses, tax_n_interest, others.
- Data validation rules:
  - Ensure presence of income_statement, balance_sheet, cash_flow_statement and core fields (revenue, net_income, total_assets, total_debt, shares_outstanding).
  - Validate numeric types, non-null values, and date formats.
  - Quality checks: revenue &gt; 0, gross_profit ≤ revenue, total_assets ≥ total_liabilities (flag exceptions), reasonable shares_outstanding.
- Normalization: per-share conversions, inflation/currency harmonization, share-count harmonization (adjust for splits), flag restatements.
- Historical aggregation: require minimum 3–5 periods (ideally 5–10), produce time series and TTM conversions, handle gaps with interpolation flags.
- Validation steps: recalculate key ratios from raw statements and compare to computed results; flag discrepancies &gt;1–2%; detect unit/currency mismatches.

## Scoring, Risk Assessment, And Decision Rules

- Scoring frameworks by category, aggregated to composite 0–100:
  - Liquidity: score current/quick/cash ratios with thresholds, trend analysis, peer comparison.
  - Profitability: score ROA/ROE/margins vs peer medians using point systems (e.g., 3/2/1/0).
  - Solvency: score leverage measures and interest coverage; compute Z-score for bankruptcy risk.
  - Efficiency: turnover ratios and WC metrics scored and compared to peers.
  - Income/dividend: FCF coverage, payout ratios, dividend CAGR, FCFY—score for income appeal.
- Composite aggregation examples: weights (profitability 40%, valuation 30%, risk 30%); normalize components and map composite to Buy/Hold/Sell thresholds (Buy &gt;75, Hold 45–75, Sell &lt;45).
- Position sizing rules map composite bands to allocation ranges and adjust for volatility, correlation, and diversification constraints.
- DecisionMatrix should allow style-based weight presets and qualitative overrides.

Table: Scoring Components And Example Weights

| **Component** | **Example Weight** |
| --- | --- |
| Profitability | 40% |
| Valuation | 30% |
| Risk / Solvency | 30% |

## Valuation, Modeling, And Sensitivity

- Multiples: compute P/E, P/B, P/S, EV/EBITDA; compare to historical and peer medians; provide percentile/quartile placement.
- PEG: PEG = P/E ÷ expected_EPS_growth%; use forward consensus or 3–5yr CAGR; interpret &lt;1 attractive.
- Cash-flow valuation: FCF yield (equity and enterprise), EV/FCF; flag industry norms.
- DCF: multi-stage DCF accepting WACC, stage growth assumptions, margins, capex, working capital changes; include sensitivity and scenario analysis and flag aggressive assumptions (terminal growth &gt; GDP, unusually low WACC).
- Dividend valuation: yield, payout ratio, coverage by FCF (prefer &gt;1.25x) and sustainability checks.
- Provide scenario-weighted valuations, sensitivity tables, Monte Carlo for confidence intervals, and combined triangulation across methods.

## LLM Integration, Narratives, And Automation

- LLM roles: generate qualitative narratives, anomalies explanations, scenario summaries, investment theses, catalysts, and suggested analyst actions.
- Templates: 5-year performance trends, key drivers, anomalies and severity, qualitative ratio context and implications.
- Hybrid scoring: combine rule-based scores with LLM sentiment/confidence adjustments (weighted combinations, threshold overrides, or explanatory additions).
- LLM API layer must include prompt templates, caching, confidence scoring, logging, and fallback rules for auditability.
- CLIs:
  - llm_classifier.py for batch classification types (risk_profile, valuation, financial_health, quality, ESG, etc.).
  - llm regression workflows to extract text features and combine with numeric features for predictions (EPS growth, margin compression, ROE changes).
- Automation: scheduled runs, alerting on significant shifts, dashboards with interactive sliders and scenario toggles, nearest-neighbor peer discovery using embeddings and vector DB.

## Monitoring, Alerts, Testing, And Validation

- Monitoring: data feed health, metric drift, event-driven alerts (earnings surprises, restatements, dividend changes, M&A).
- Alerts: threshold-based and pattern-recognition triggers with escalation protocols and prescribed actions.
- Testing: unit tests for compute methods (normal, missing inputs, zero denominators, negative values); integration tests for CLI flows; backtests across market regimes.
- Validation: correlate composite scores with institutional ratings and credit/analyst outputs; target &gt;70% directional alignment and maintain audit trails.
- Parameter management: refine thresholds/weights via backtesting, ROC analysis, sensitivity testing, and maintain a regime-driven parameter library updated regularly.

## Decisions

- Implement CLI and RatioCalculator as core deliverables for immediate usage.
- Build compute_metrics() and validation pipeline before scoring modules to ensure reliable inputs.
- Prioritize liquidity and cash-flow metrics to support dividend and solvency assessments.
- Adopt a hybrid architecture: rule-based quantitative scoring + LLM-driven qualitative interpretation and scenarios.
- Use Cisco (CSCO) case templates to calibrate thresholds and peer groups before production rollout.
- Provide reproducible CLI tooling and stakeholder-facing Dash dashboards; maintain rigorous testing and walk-forward validation.

## Open Questions

- Which canonical metric naming convention should the CLI accept (snake_case, hyphen, synonyms)?
- Preferred units and scale conventions for inputs (absolute dollars, millions, normalized); should CLI accept a unit flag?
- Which primary data sources/vendors will provide financial statements, peer lists, and intraday market data in production?
- How to build and maintain industry-specific threshold libraries and update cadence (quarterly, annually)?
- What governance and human-review thresholds trigger manual analyst intervention on LLM outputs?
- What SLAs, cost controls, and model-governance practices should constrain LLM usage and ensure auditability?