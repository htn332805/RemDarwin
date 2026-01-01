# Proposed Simplified Core Module Architecture for MyCFATool

## Overview

The current architecture has several redundancies and tight coupling, particularly in database access and class responsibilities. This proposal introduces a layered architecture with repository/service patterns to improve separation of concerns, reduce duplication, and enhance maintainability.

## Key Issues Identified

1. **Direct Database Coupling**: All analytics classes (RatioValidator, TechnicalAnalyzer, etc.) directly instantiate `sqlite3.connect`, leading to duplicate connection logic and tight coupling to SQLite.
2. **God Classes**: RatioValidator contains 40+ methods for ratio computation and validation, violating single responsibility.
3. **Inconsistent Data Access**: Some modules use ORM (DataUpdater), others use raw SQL.
4. **Redundant Patterns**: Similar patterns for ticker_id lookup, statement queries, and data extraction repeated across classes.

## Proposed Architecture

Introduce a clean layered architecture:

```
MyCFATool/
├── core/
│   ├── config.py              # Centralized configuration management
│   ├── database.py            # Database session management
│   └── exceptions.py          # Custom exceptions
├── domain/
│   ├── entities.py            # Business entities (if needed)
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── financial_data_repository.py  # Unified data access
│   │   └── ticker_repository.py
│   └── services/
│       ├── __init__.py
│       ├── fundamental_analysis_service.py  # Ratios, validation, DuPont, etc.
│       ├── technical_analysis_service.py    # Indicators, patterns
│       ├── forecasting_service.py           # ARIMA, etc.
│       ├── valuation_service.py             # DCF, DDM, multiples
│       └── data_ingestion_service.py        # Orchestrates ingestion
├── infrastructure/
│   ├── fmp_client.py          # External API client
│   └── scheduler.py           # Task scheduling
├── presentation/
│   ├── dashboard/
│   │   ├── app.py
│   │   ├── layouts.py
│   │   ├── callbacks.py
│   │   └── components/         # Reusable UI components
│   │       ├── __init__.py
│   │       ├── chart_component.py
│   │       ├── table_component.py
│   │       └── filter_component.py
│   └── cli/
│       └── __init__.py         # Command-line interfaces
├── config/
│   └── settings.yaml
├── data/
│   ├── raw/
│   └── processed/
├── tests/
└── README.md
```

## Consolidation Details

### 1. Repository Layer

**FinancialDataRepository**: Consolidates all data access logic from DataUpdater, RatioValidator, TechnicalAnalyzer, etc.

- Methods for querying statements, ratios, historical prices
- Uses SQLAlchemy ORM consistently
- Handles ticker/source lookups centrally

### 2. Service Layer

**FundamentalAnalysisService**: Consolidates RatioValidator functionality

- Ratio computations
- Validation against reported data
- DuPont analysis, Altman Z-score, etc.
- Depends on FinancialDataRepository

**TechnicalAnalysisService**: Consolidates TechnicalAnalyzer

- Indicator calculations
- Pattern detection
- Depends on FinancialDataRepository

**ValuationService**: Consolidates DCF and other valuation methods

**DataIngestionService**: Orchestrates ingestion using FMPClient and FinancialDataRepository

### 3. Interface Simplifications

- **Unified Response Format**: All service methods return standardized dicts with consistent keys (value, signal, interpretation)
- **Common Parameters**: ticker_symbol, period_type, fiscal_date across methods
- **Error Handling**: Centralized exception handling with custom exceptions

### 4. File Reorganizations

- **analytics/validation.py** → **domain/services/fundamental_analysis_service.py**
- **analytics/technicals.py** → **domain/services/technical_analysis_service.py**
- **analytics/dcf.py** → **domain/services/valuation_service.py**
- **analytics/forecasting.py** → **domain/services/forecasting_service.py**
- **ingestion/data_updater.py** → **domain/repositories/financial_data_repository.py** (partially, merge with models.py logic)
- **dashboard/components/**: Already good, enhance with base classes

## Benefits

1. **Reduced Duplication**: Centralize database access, eliminate repeated query patterns
2. **Clear Separation**: Repository handles data, services handle logic, infrastructure external deps
3. **Testability**: Services can be mocked with repository interfaces
4. **Maintainability**: Changes to database schema isolated to repository layer
5. **Extensibility**: Easy to add new analysis methods or data sources
6. **Compatibility**: Existing dashboard callbacks can adapt to new service interfaces with minimal changes

## Migration Plan

1. Implement Repository layer first
2. Migrate one service at a time (start with FundamentalAnalysisService)
3. Update tests accordingly
4. Update dashboard callbacks to use services
5. Deprecate old classes

## Open Questions

- Should entities be introduced for complex data structures?
- How to handle caching for performance-critical operations?
- Integration with existing cloud database support?