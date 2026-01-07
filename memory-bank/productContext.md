# Product Context

This file provides a high-level overview of the project and the expected product that will be created. Initially it is based upon projectBrief.md (if provided) and all other available project-related information in the working directory. This file is intended to be updated as the project evolves, and should be used to inform all other modes of the project's goals and context.
2026-01-02 03:22:55 - Initial population after project completion

*

## Project Goal

Build an automated simulated options selling and stock investment system that provides trading advice and simulates trades for covered calls, cash-secured puts, and long-term stock positions. The system uses fundamental analysis for stock screening and technical analysis for trade timing, entry, and exit decisions, combining institutional-grade risk management with AI-powered interpretive capabilities in a simulation environment.

## Key Features

**Core Strategy Components:**
- Covered calls: Simulated selling of call options against owned stock positions
- Cash-secured puts: Simulated selling of put options with 100% cash backing
- Long-term stock investments: Simulated buy-and-hold positions with fundamental screening
- Institutional-grade risk management with position sizing and Greeks limits
- Historical and simulated options chain data with Greeks calculations (delta, gamma, theta, vega, rho)
- Bid-ask spread analysis and liquidity metrics
- Implied volatility surface modeling and term structure analysis

**Fundamental Analysis Screening:**
- Comprehensive financial statement analysis (income, balance sheet, cash flow)
- Valuation metrics (P/E, P/B, EV/EBITDA) and financial ratios
- Industry and peer comparisons with statistical benchmarking
- Company quality and growth assessments (ROE, debt levels, earnings consistency)

**Technical Analysis Timing:**
- Price trend identification using moving averages and trend lines
- Momentum and oscillator indicators (RSI, MACD, stochastic)
- Support/resistance level analysis and breakout detection
- Entry/exit signal generation with confirmation mechanisms

**Quantitative Screening Engine:**
- Rule-based filters for premium yield, moneyness, time to expiration
- Liquidity requirements (open interest >100, bid-ask spreads <5%)
- Volatility percentile constraints (20th-60th percentile)
- Sector diversification and concentration limits
- Earnings proximity filters (>14 days from expiration)

**Risk Management Framework:**
- Position sizing: 5% max allocation per trade, portfolio diversification (10 positions max)
- Greeks exposure limits: Net delta ±0.2, gamma ±0.05, vega <2%
- Value at Risk (VaR) daily calculation at 95% confidence
- Expected Shortfall weekly stress testing with 20+ scenarios
- Stop-loss triggers: 20% premium decay or volatility spikes
- Counterparty risk monitoring with brokerage concentration limits

**LLM Integration Layer:**
- AI-driven risk assessment and trade rationale generation
- Pre-trade approval workflow combining quantitative scores (70%) with LLM confidence (20%)
- Risk adjustment factor (10%) for portfolio impact consideration
- Prompt engineering framework with contextual market analysis

**Backtesting and Optimization:**
- Multi-regime backtesting across bull/bear/crisis market conditions
- Walk-forward testing with 2-year train/test windows
- Performance attribution analysis (premium decay vs underlying movement)
- Genetic algorithm parameter optimization for filter thresholds
- Transaction cost modeling with commissions and slippage

**Simulation and Advice:**
- Simulated trade execution with position tracking and P&L calculation
- User advice generation based on combined fundamental/technical analysis
- Interactive dashboard with simulation results, Greeks visualization, and risk alerts
- Custom alerting system for trade opportunities and risk warnings
- Historical performance simulation, heatmaps, and trade-by-trade analysis

*

## Overall Architecture

### Core System Components
1. **Data Layer**: Extended FMP API integration with on-demand options chain data via CLI commands, Greeks calculations, bid-ask spreads, and historical market data
2. **Quantitative Screening Engine**: Rule-based filters for covered calls and cash-secured puts with liquidity and volatility constraints
3. **Risk Management Framework**: Institutional-grade position sizing, Greeks monitoring, VaR/ES calculations, and automated risk controls
4. **LLM Interpretation Layer**: AI-driven risk assessment with prompt engineering framework and confidence calibration
5. **Decision Matrix**: Automated trade selection combining quantitative scores (70%) with LLM insights (20%) and portfolio impact (10%)
6. **Backtesting Engine**: Multi-regime historical testing with walk-forward validation and performance attribution
7. **Execution Interface**: Brokerage API integration with authentication, order routing, and position reconciliation
8. **Monitoring Dashboard**: Real-time visualization with Greeks exposure, risk alerts, and performance analytics

### Technology Stack
- **Language**: Python with CLI interface for on-demand data processing
- **Data Storage**: SQLite/PostgreSQL with partitioning for options chains and trade history
- **LLM Integration**: OpenAI/Claude API with custom prompt templates and response parsing
- **Brokerage APIs**: Alpaca/Interactive Brokers with OAuth authentication and rate limiting
- **Visualization**: Plotly/Dash for interactive charts, Grafana for monitoring dashboards
- **Data Updates**: CLI commands for on-demand option chain refreshes
- **Caching**: Redis for API responses and computed Greeks to reduce latency

### Key Integration Points
- Options chain data flows from FMP API through validation and gap-filling to risk management
- Quantitative filters feed into LLM analysis for trade rationale generation
- Risk metrics integrate with position sizing algorithms and stop-loss triggers
- Backtesting results calibrate filter thresholds and scoring weights
- Dashboard provides unified view of portfolio positions, Greeks, and alerts

2026-01-04 22:47:19 - Expanded subtask 7.3 "Implement monitoring and alert systems" in fundamental_analysis_plan.md with detailed elaboration including context, explanations, and comprehensive example covering all possible catalysts and scenarios.
2026-01-05 03:54:00 - Expanded "Expected shortfall: Weekly stress testing" subtask in selling_option_subtask3.md with detailed elaboration including context, explanations, and comprehensive example covering all possible catalysts and scenarios.
2026-01-05 06:25:00 - Expanded "Custom alerting based on user preferences" subtask in selling_option_subtask8.md with detailed elaboration including context, explanations, and comprehensive example covering all possible catalysts and scenarios.
2026-01-07 01:00:00 - Clarified project scope: RemDarwin is an automated simulated system providing trading advice and simulating trades for options selling (covered calls, cash-secured puts) and long-term stock investments, using fundamental analysis for stock screening and technical analysis for trade timing/entry/exit.