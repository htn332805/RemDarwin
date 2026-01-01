# Decision Log

This file records architectural and implementation decisions using a list format.
2025-12-31 23:22:25 - Initial population.

## Decision

Use SQLite with JSON columns for flexibility in financial data storage.

## Rationale 

Allows unlimited new fields from FMP without schema changes.

## Implementation Details

As per schema in projectBrief.md

[2026-01-01 10:01:55] - Decision to implement Altman Z-Score bankruptcy prediction model

## Rationale

Adding institutional-level financial analysis tools to support advanced equity analysis. The Altman Z-Score is a widely used metric for assessing bankruptcy risk.

## Implementation Details

Added compute_altman_z_score method to RatioValidator class in MyCFATool/analytics/validation.py. Method computes Z-score using the standard formula with 5 components, handles missing data gracefully, and provides risk interpretation. Uses market price for market value of equity. Unit tests added for full coverage.

[2026-01-01 10:15:00] - Decision to implement Beneish M-Score earnings manipulation detection model

## Rationale

Enhancing financial validation capabilities with institutional-grade tools for detecting potential earnings manipulation, complementing existing analysis methods.

## Implementation Details

Added compute_beneish_m_score method to RatioValidator class, calculating M-Score from 8 financial ratios over two periods. Threshold > -2.22 indicates manipulation risk. Handles missing data and insufficient periods. Unit tests added for comprehensive coverage including risk levels and edge cases.

[2026-01-01 10:25:00] - Decision to implement compare_to_peers method for peer comparison functionality

## Rationale

Enhancing financial analysis capabilities with peer benchmarking to provide relative performance insights, enabling investors to assess company ratios against industry standards.

## Implementation Details

Added compare_to_peers method to RatioValidator class, computing company ratios and comparing against provided peer averages, calculating differences and z-scores where applicable. Handles missing peer data and company computation failures gracefully. Unit tests added for full coverage of scenarios including above/below average, missing std dev, and edge cases.

[2026-01-01 10:34:00] - Decision to implement Merton's Distance to Default (DD) credit risk model

## Rationale

Integrating advanced credit risk assessment tools to provide institutional-level default probability analysis, enhancing the platform's capabilities for risk management and investment decision-making.

## Implementation Details

Added compute_merton_dd method to RatioValidator class in MyCFATool/analytics/validation.py. Method calculates Distance to Default using Merton's structural model formula: DD = [ln(MV_Equity / Debt) + (rf - 0.5*sigma^2)*T] / (sigma * sqrt(T)), where sigma is volatility from equity price returns. Computes default probability as norm.cdf(-DD) and provides risk interpretation. Handles missing data (price, debt, shares, historical prices) and edge cases (zero values). Unit tests added for full coverage including safe/high risk scenarios, missing data, and invalid inputs.

[2026-01-01 10:39:00] - Decision to implement Ohlson O-Score bankruptcy prediction model

## Rationale

Expanding financial risk assessment capabilities with the Ohlson O-Score, a comprehensive bankruptcy prediction model that incorporates multiple financial variables and multi-period change indicators for more robust distress risk evaluation.

## Implementation Details

Added compute_ohlson_o_score method to RatioValidator class in MyCFATool/analytics/validation.py. Method computes O-Score using 9 variables: log(TA), TL/TA, WC/TA, CL/CA, EBIT/TA, NI(t-1)/NI(t), FFO/TA, NI(t)/NI(t-1), NI(t-1)/NI(t-2) from current and two previous fiscal periods. Scores > 0.5 indicate high distress risk. Handles multi-period data gracefully, returning None if insufficient historical data. Unit tests added for full coverage including low/high risk scenarios and edge cases.

[2026-01-01 10:58:00] - Decision to implement Dividend Discount Model valuation method

## Rationale

To provide institutional-grade equity valuation tools, complementing existing analysis methods.

## Implementation Details

Added compute_ddm_valuation method to RatioValidator class in MyCFATool/analytics/validation.py. Uses Gordon Growth Model: intrinsic_value = DPS / (required_return - growth_rate). DPS calculated from dividendsPaid / sharesOutstanding. Compares intrinsic value to market price for valuation assessment. Handles missing data and invalid inputs. Unit tests added for full coverage.

[2026-01-01 11:00:20] - Decision to implement Credit Rating Estimation using scorecard approach

## Rationale

To enhance credit risk assessment capabilities, providing estimated S&P credit ratings based on key financial ratios for better investment decision-making.

## Implementation Details

Added estimate_credit_rating method to RatioValidator class in MyCFATool/analytics/validation.py. Uses scorecard with points for ROA, debt ratio, interest coverage, ROE, current ratio, and cash flow to debt ratio. Total score maps to ratings AAA to D. Handles missing data gracefully. Added unit tests in test_validation.py for various rating levels, achieving full test coverage.

[2026-01-01 13:56:35] - Decision to implement volume-based and OHLC technical indicators

## Rationale

Expanding technical analysis capabilities with volume-based indicators (OBV, VROC) and trend/volatility measures (ATR, ADX) to provide more comprehensive market analysis tools for the dashboard.

## Implementation Details

Added compute_obv, compute_vroc, compute_atr, and compute_adx methods to TechnicalAnalyzer class in MyCFATool/analytics/technicals.py. Each method follows existing patterns: queries historical_price data, validates sufficient periods, computes indicators using pandas/numpy, provides signal interpretation, and returns standardized dict results. OBV uses cumulative volume based on price direction, VROC measures volume change percentage, ATR calculates average true range for volatility, ADX assesses trend strength with directional indicators.

[2026-01-01 14:07:32] - Decision to implement Doji and Engulfing candlestick pattern detection

## Rationale

Expanding technical analysis capabilities with candlestick patterns for market sentiment and reversal signals, providing traders with pattern recognition tools based on OHLC data.

## Implementation Details

Added detect_doji and detect_engulfing methods to TechnicalAnalyzer class in MyCFATool/analytics/technicals.py. Doji detection identifies candles with small body relative to range (threshold 5%), returns pattern presence, 'indecision' signal, and strength (1 - body/range). Engulfing detection identifies bullish/bearish engulfing where current candle body engulfs previous, returns pattern presence, signal ('bullish'/'bearish'/'neutral'), and strength (current_body/previous_body ratio). Both methods query latest OHLC data up to fiscal_date, handle insufficient data, and return standardized dict results with interpretations. Module import tested successfully.

[2026-01-01 14:38:00] - Decision to implement automated data ingestion with deduplication and logging

## Rationale

To operationalize the data pipeline with incremental updates, preventing duplicates and enabling scheduled refreshes for maintaining up-to-date financial data without manual intervention.

## Implementation Details

Enhanced DataUpdater class with logging framework (console and file), error handling with transaction rollback, and deduplication based on unique keys (ticker_id, period_type, fiscal_date). Added DataScheduler class using APScheduler for background automated updates with configurable intervals (weekly for statements/ratios, daily for prices). Updated settings.yaml with scheduler config. Tested logging functionality.

[2026-01-01 14:45:00] - Decision to implement multi-ticker portfolio analysis dashboard

## Rationale

To extend dashboard capabilities from single-ticker analysis to portfolio-level insights, enabling users to analyze aggregated metrics, weighted calculations, and comparative visualizations for multiple holdings.

## Implementation Details

Added Portfolio tab to layouts.py with multi-select dropdown, dynamic weight inputs, and components for portfolio summary table, pie chart for asset allocation, performance chart, and risk metrics table. Implemented compute_portfolio_aggregates function for weighted sums of financial statements and weighted averages of ratios. Implemented compute_portfolio_risks for aggregate risk scores. Added callbacks for dynamic UI updates and portfolio computations. Integrated into base_layout and display_page without disrupting existing single-ticker features.

[2026-01-01 15:03:22] - Decision to implement cloud database support with SQLAlchemy ORM

## Rationale

To enable scalability and remote access by supporting cloud databases like PostgreSQL on AWS RDS, while maintaining compatibility with existing SQLite for local development.

## Implementation Details

Installed SQLAlchemy and psycopg2-binary. Created SQLAlchemy models in models.py for all tables with appropriate column types and constraints. Refactored database_setup.py to use SQLAlchemy engine for schema creation and session for initialization. Updated DataUpdater class to use SQLAlchemy sessions for all CRUD operations, including upsert logic with model instances. Added database configuration in settings.yaml for type (sqlite/postgresql) and connection strings. Updated scheduler.py to create DataUpdater without db_path parameter. Ensured ORM abstraction allows seamless switching between SQLite and PostgreSQL without code changes. Tested schema creation with SQLite successfully.

[2026-01-01 15:17:00] - Decision to implement repository layer for simplified MyCFATool architecture

## Rationale

To consolidate data access logic, reduce duplication, and improve separation of concerns by introducing a layered architecture with repository/service patterns, moving away from direct database coupling in analytics classes.

## Implementation Details

Created core/ module with config.py (centralized configuration), database.py (SQLAlchemy session management), exceptions.py (custom exceptions). Implemented domain/repositories/ with TickerRepository for ticker management and FinancialDataRepository consolidating data access from RatioValidator, DataUpdater, TechnicalAnalyzer using SQLAlchemy ORM. Updated existing database_setup.py and data_updater.py to use new core config. Tested repository layer successfully with existing database setup.

[2026-01-01 15:20:30] - Decision to migrate fundamental analysis logic to FundamentalAnalysisService and refactor RatioValidator to use repository

## Rationale

To improve code organization, eliminate direct database connections, and standardize interfaces by extracting computational logic into a dedicated service layer, while ensuring all existing functionality is maintained.

## Implementation Details

Migrated core ratio computation, validation, and bankruptcy scoring methods from RatioValidator to new FundamentalAnalysisService in domain/services/. Consolidated related methods into logical groups (liquidity, profitability, leverage, valuation, bankruptcy). Standardized method signatures to (ticker_symbol, period_type, fiscal_date) and return formats to dicts with 'value' and 'interpretation'. Refactored RatioValidator to use FinancialDataRepository instead of sqlite3 direct connections, removing db_path dependency and eliminating direct SQL queries. Updated imports and __init__ methods accordingly. Service uses FinancialDataRepository for data access.

[2026-01-01 15:24:09] - Decision to consolidate valuation and forecasting logic into dedicated services

## Rationale

To centralize valuation (DCF) and forecasting (time-series) methods into service layer, utilizing FinancialDataRepository for data access, standardizing interfaces, and integrating with the new architecture for better separation of concerns and maintainability.

## Implementation Details

Created ValuationService in domain/services/ migrating DCF valuation methods (compute_free_cash_flow, project_free_cash_flows, compute_wacc, compute_terminal_value, compute_intrinsic_value, compute_dcf_valuation, perform_sensitivity_analysis) from analytics/dcf.py, refactored to use FinancialDataRepository, standardized method signatures to (ticker_symbol, period_type, fiscal_date), and return consistent dict formats. Created ForecastingService migrating time-series forecasting methods (arima_forecast, exponential_smoothing_forecast, linear_regression_forecast) from analytics/forecasting.py, refactored to use FinancialDataRepository and FundamentalAnalysisService for ratio computations, maintaining existing functionality while integrating with service architecture.

[2026-01-01 17:48:00] - Decision to implement batch ingestion for multiple tickers: To expand data coverage and support automated ingestion for S&P 500 constituents and other large ticker lists, implemented batch processing in DataIngestionService.ingest_batch_tickers with configurable concurrency and error handling. Added FMPClient methods get_sp500_tickers and get_available_tickers for dynamic ticker fetching.

## Implementation Details

Extended FMPClient with get_sp500_tickers() and get_available_tickers(limit) methods using FMP API endpoints. Added ingest_batch_tickers to DataIngestionService for processing multiple tickers sequentially with continue_on_error option. Updated DataScheduler with update_all_data_batch method and _get_ticker_list supporting static, sp500, and dynamic sources. Modified settings.yaml with tickers_source, tickers_limit, and batch_ingestion config. Updated dashboard layouts to use get_available_tickers() from TickerRepository for dynamic ticker lists.

[2026-01-01 18:16:29] - Decision to enable testing mode with limited S&P 500 tickers: To facilitate validation testing with a subset of tickers without overwhelming the system or API limits, added testing configuration section to settings.yaml with enabled flag and configurable tickers_limit. Modified DataScheduler._get_ticker_list to prioritize testing mode, using first N S&P 500 tickers when testing.enabled is true.

## Implementation Details

Added testing: section to settings.yaml with enabled: true and tickers_limit: 10. Updated scheduler.py _get_ticker_list to check config.get("testing", {}).get("enabled", False) and if true, fetch S&P 500 tickers and slice to testing.tickers_limit. Preserves original production settings (static tickers, sp500 full list, dynamic) when testing is disabled. Allows easy switching between testing and production modes by changing one flag.

[2026-01-01 19:45:00] - Decision to configure system for full S&P 500 ticker processing

## Rationale

To expand data coverage to all S&P 500 constituents for comprehensive market analysis, moving from limited testing set to production full set.

## Implementation Details

Updated settings.yaml: set testing.enabled=false and tickers_source='sp500'. System now uses full ~500 S&P 500 tickers for batch ingestion, ensuring efficient processing through sequential batch mode with error handling.

[2026-01-01 19:46:13] - Decision to implement Redis-based distributed rate limiting for FMP API

## Rationale

To ensure compliance with FMP's 120 requests per minute limit across multiple container instances in production deployment, implementing distributed rate limiting using Redis to coordinate API calls across all instances.

## Implementation Details

Added Redis configuration to settings.yaml with host, port, db, and password settings. Created RedisRateLimiter class in ingestion/rate_limiter.py using Redis sorted sets for sliding window rate limiting (120 requests per 60 seconds). Updated FMPClient class to initialize Redis client and rate limiter in __init__, replaced in-memory rate limiting with distributed Redis-based approach. Added proper error handling for rate limiter timeouts and Redis failures. Rate limiter gracefully degrades by allowing requests if Redis is unavailable.

[2026-01-01 19:57:41] - Decision to implement comprehensive load testing using Locust framework

## Rationale

To validate performance of MyCFATool production deployment under concurrent user load (10-50 users), ensuring the application can handle realistic user interactions with the dashboard including authentication, data retrieval, analysis, and report generation.

## Implementation Details

Added Locust 2.0.0 to requirements.txt. Created locustfile.py with HttpUser classes simulating different user patterns: LightUser (overview browsing), HeavyUser (deep analysis), MixedUser (balanced usage). Implemented authentication simulation, ticker selection, financial data loading, technical analysis, portfolio creation, and PDF generation. Added load_test_config.yaml for environment-specific configuration (local/staging/production) with performance thresholds. Created comprehensive LOAD_TESTING_README.md with execution instructions and best practices. Tests validate response time percentiles (95p, 99p) and failure rates against configurable thresholds, providing automated pass/fail assessment.

[2026-01-01 20:04:02] - Decision to implement automated AWS deployment with Terraform + ECS

## Rationale

To enable reliable, repeatable production deployments with infrastructure as code, supporting staging and production environments with automated provisioning, secrets management, health validation, load testing, and rollback capabilities.

## Implementation Details

Extended Terraform configuration (main.tf) with complete AWS infrastructure: VPC with private subnets, RDS PostgreSQL with encryption and Multi-AZ, ECS Fargate cluster and service with ALB, ECR repository, security groups, IAM roles, CloudWatch logging, and Secrets Manager integration. Created automated deployment scripts: deploy.sh (infrastructure + application), setup_secrets.sh (AWS Secrets Manager), health_check.sh (validation), run_load_test.sh (performance testing), rollback.sh (failure recovery). All scripts support staging/production environments with error handling and logging. Provided comprehensive DEPLOYMENT_README.md with step-by-step instructions, troubleshooting, cost optimization, and security considerations.

[2026-01-01 12:10:00] - Decision to enhance API data validation in FMPClient

## Rationale

To ensure data integrity and quality from FMP API responses by implementing comprehensive validation checks including data types, ranges, consistency, and formats, preventing corrupt or invalid data from entering the system.

## Implementation Details

Modified _validate_response_data method in MyCFATool/ingestion/fmp_client.py to include: data type validation for financial fields (numeric checks using ValidationMixin.validate_numeric), range checks (non-negative for assets/liabilities/equity), consistency checks (balance sheet assets ≈ liabilities + equity with 1% tolerance), date format validation, and required fields validation. Changed FMPClient to inherit ValidationMixin, added ValidationError raises instead of ValueError. Defined lists of non-negative fields (assets, liabilities, equity, etc.) and general numeric fields (revenue, netIncome, etc.). Validation integrates with existing retry logic by occurring before data processing.

[2026-01-01 20:41:00] - Decision to implement Redis-based caching for financial data repository

## Rationale

To improve performance and reduce database load for frequently accessed financial data (statements, ratios, prices) by implementing a Redis caching layer in the repository pattern, enabling faster response times for dashboard queries and analysis operations while maintaining data consistency through proper cache invalidation.

## Implementation Details

Added Redis configuration section to settings.yaml with caching enabled flag and TTL settings (statements: 3600s, ratios: 1800s, prices: 900s). Updated requirements.txt to pin redis==4.6.0 and installed package. Implemented caching methods in FinancialDataRepository: _init_redis for client initialization with graceful degradation, _get_from_cache/_store_in_cache for data retrieval/storage with JSON serialization, _delete_from_cache/_delete_cache_keys_by_pattern for invalidation. Modified get_* methods (income_statement, balance_sheet, cash_flow, ratios, historical_price_at_date, historical_prices_ordered) to check cache first, store results on database hits, with structured cache keys. Updated upsert_* methods to invalidate relevant cache patterns after successful insertions. Added debug-level logging for cache hits/misses. System gracefully degrades to database-only operation when Redis is unavailable, preserving all existing functionality.