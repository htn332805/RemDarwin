# Product Context

This file provides a high-level overview of the project and the expected product that will be created. Initially it is based upon projectBrief.md and the fundamental_analysis_plan.md as the ultimate source of truth for implementation guidelines, along with other available project-related information in the working directory. This file is intended to be updated as the project evolves, and should be used to inform all other modes of the project's goals and context.
2026-01-07 03:50:00 - Initial population based on project scan and analysis

*

## Project Goal

The project, named RemDarwin (possibly referencing Charles Darwin's evolution, but implemented as MyCFATool), aims to create a personal institutional-grade financial analysis platform that automates the collection, storage, verification, analysis, and visualization of equity financial data. The system integrates with Financial Modeling Prep (FMP) API to retrieve comprehensive financial statements, ratios, metrics, and historical prices, storing them in SQLite databases with institutional-grade auditability. The platform supports CFA-style financial modeling, validation, and decision-making, with AI integration via Perplexity.ai Pro for interpretive analysis. The ultimate product is a scalable, automated tool for professional-grade fundamental and technical analysis, potentially integrated with options trading strategies as evidenced by implementation files.

The fundamental_analysis_plan.md serves as the ultimate source of truth, outlining a systematic, automated approach to fundamental stock analysis mimicking institutional firms, combining rule-based quantitative analysis with LLM interpretive capabilities.

## Key Features

- **Automated Data Ingestion**: FMP API client for financial statements (income, balance sheet, cash flow), ratios, metrics, and historical prices (annual and quarterly)
- **Flexible Storage**: SQLite databases per ticker with JSON columns for unlimited field expansion, strong deduplication, and audit trails
- **Institutional Validation**: Independent ratio recalculation with discrepancy flagging and audit logging
- **Comprehensive Analytics**: Profitability, liquidity, solvency, efficiency, and valuation ratios; technical indicators (MA, RSI, MACD); time-series forecasting (ARIMA, Prophet)
- **AI Integration**: Perplexity.ai Pro for market insights and trend analysis (no OpenAI)
- **Interactive Dashboard**: Python Dash interface for trend visualization, ratio displays, forecast charts, and audit summaries
- **Automation**: CLI-based incremental updates with deduplication and logging
- **Options Trading Component**: Implementation includes options chain analysis for covered calls and cash-secured puts, potentially using fundamental analysis for stock selection

## Overall Architecture

The architecture follows a modular design with clear separation of concerns:

- **Data Layer**: FMP API client (fmp_client.py) retrieves data; DataUpdater handles SQLite storage with upsert logic and deduplication
- **Analytics Layer**: Separate modules for fundamentals (ratios.py), technicals (technicals.py), forecasting (forecasting.py), and options analysis
- **Presentation Layer**: Dash dashboard with modular layouts and callbacks for interactive visualization
- **Infrastructure**: SQLite databases per ticker with flexible JSON schema; configuration via YAML; virtual environment management
- **Integration**: Options trading modules (IV_Surfaces.py, option_filter.py) suggest hybrid fundamental + derivatives analysis

The fundamental_analysis_plan.md provides the structured implementation guideline with atomic subtasks for data validation, quantitative analysis, scoring, and LLM interpretation, ensuring institutional-quality processes.