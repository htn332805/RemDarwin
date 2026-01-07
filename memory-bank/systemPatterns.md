# System Patterns

This file documents recurring patterns and standards used in the project.
2026-01-07 03:50:00 - Initial population based on project scan and analysis
2026-01-07 03:54:00 - Added line limit restriction for Python files
2026-01-07 03:55:00 - Added comprehensive documentation requirement for all generated code
2026-01-07 03:57:00 - Added change tracking requirement for all modifications

*

## Coding Patterns

- **Modular Class-Based Design**: Use of classes for API clients (FMPClient), data updaters (DataUpdater), with clear initialization and method structure
- **Pandas Integration**: Extensive use of pandas DataFrames for data manipulation and analysis
- **JSON Flexibility**: SQLite databases use JSON columns for extensible data storage without schema changes
- **Error Handling**: Robust HTTP error handling in API clients with raise_for_status
- **Configuration Management**: Use of .env files and YAML for API keys and settings
- **Unit Testing Framework**: Structured unit tests for data ingestion, ratio computation, and deduplication
- **Line Limit Restriction**: All single Python files/scripts/modules must be kept under 1500 lines. Any resulting code file above this limit should be refactored into appropriate modules or groups of core modules, then re-integrated via import statements. This ensures maintainability, readability, and adherence to modular design principles.
- **Comprehensive Documentation**: All generated code must include detailed comments explaining every line of code, with usage examples and CLI examples. Documentation should include module docstrings, function docstrings with parameters and return values, inline comments for complex logic, and practical examples demonstrating how to use the code in real scenarios.

## Architectural Patterns

- **Data Pipeline Architecture**: Linear flow from ingestion (FMP API) → storage (SQLite upsert) → analysis (ratios/technicals/forecasting) → visualization (Dash dashboard)
- **Per-Ticker Database Pattern**: Separate SQLite database for each ticker to enable scalability and isolation
- **Audit and Validation Layer**: Institutional-grade validation with discrepancy flagging, audit tables, and logging
- **Modular Analytics**: Separate modules for fundamentals, technicals, forecasting, and options analysis
- **CLI Automation Pattern**: Scriptable command-line interfaces for data updates and processing
- **Hybrid Analysis Framework**: Combination of fundamental analysis (per guideline) with options trading implementation

## Testing Patterns

- **Unit Tests**: Focused on individual functions (API calls, ratio calculations, database operations)
- **Integration Tests**: End-to-end pipeline testing (API → SQLite → dashboard)
- **Data Integrity Tests**: Validation of computed vs reported ratios, deduplication checks
- **Audit Trail Verification**: Ensuring all updates are logged and discrepancies flagged

## Data Management Patterns

- **Deduplication Strategy**: Unique constraints and upsert logic to prevent duplicate records
- **Flexible Schema**: JSON columns allow unlimited new fields from API without migrations
- **Historical Versioning**: Timestamps and audit logs for data traceability
- **Incremental Updates**: Only new records added, avoiding full refreshes

## Change Tracking Patterns

- **Comprehensive Change Logging**: All changes, revisions, improvements, enhancements, and feature removals must be tracked with timestamps in a text log, including reasons and decisions throughout project implementation
- **Audit Trail Maintenance**: Maintain detailed logs for code modifications, architectural changes, and feature updates to ensure traceability and accountability
- **Timestamp Format**: Use ISO 8601 format (YYYY-MM-DD HH:MM:SS) for all change entries
- **Log Structure**: Include file modified, change type, reason/decision, and impact assessment

## AI Integration Patterns

- **Perplexity.ai Pro Focus**: Exclusive use of Perplexity.ai Pro for LLM insights, no OpenAI integration
- **Interpretive Analysis**: AI used for trend interpretation, anomaly detection, and narrative generation
- **Rule-Based + AI Hybrid**: Quantitative calculations combined with AI interpretive capabilities