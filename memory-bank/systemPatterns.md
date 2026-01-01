# System Patterns *Optional*

This file documents recurring patterns and standards used in the project.
It is optional, but recommended to be updated as the project evolves.
2025-12-31 23:22:25 - Initial population.

## Coding Patterns

- Use Python classes for modular components (e.g., FMPClient, DataUpdater)

## Architectural Patterns

- MVC-like structure with ingestion, analytics, dashboard separation

## Testing Patterns

- Unit tests for key modules

[2026-01-01 14:07:32] - Candlestick pattern detection methods added to TechnicalAnalyzer for Doji and Engulfing patterns using OHLC data, returning pattern presence, signal, and strength metrics.

[2026-01-01 15:17:00] - Implemented repository layer architecture with core/ (config, database, exceptions), domain/repositories/ (TickerRepository, FinancialDataRepository), consolidating data access logic from RatioValidator, DataUpdater, TechnicalAnalyzer using SQLAlchemy ORM for unified queries.

[2026-01-01 15:20:30] - Implemented service layer pattern with FundamentalAnalysisService consolidating fundamental analysis computations, standardizing interfaces with dict returns including 'value' and 'interpretation', and grouping methods by category (liquidity, profitability, leverage, valuation, bankruptcy).

[2026-01-01 15:24:09] - Extended service layer with ValuationService for DCF valuation and ForecastingService for time-series forecasting, utilizing FinancialDataRepository and FundamentalAnalysisService, maintaining standardized interfaces and integrating with layered architecture.

[2026-01-01 15:27:00] - Implemented DataIngestionService to orchestrate FMP client and repository operations, consolidating ingestion logic and eliminating direct database connections in ingestion modules.

[2026-01-01 12:10:11] - Enhanced API data validation pattern: Extended ValidationMixin usage to FMPClient class for comprehensive response validation including data types, ranges, consistency checks, and formats, raising ValidationError on failures to ensure data integrity before ingestion.

[2026-01-01 20:41:00] - Implemented Redis caching pattern: Added distributed caching layer to FinancialDataRepository using Redis for frequently accessed financial data. Pattern includes cache-first lookup with database fallback, TTL-based expiration (statements: 1h, ratios: 30m, prices: 15m), JSON serialization for complex data structures, pattern-based cache invalidation on data updates, and graceful degradation when Redis unavailable. Cache keys follow structured naming convention (e.g., "income_statement:{ticker}:{period_type}:{fiscal_date}") for efficient pattern matching and invalidation.