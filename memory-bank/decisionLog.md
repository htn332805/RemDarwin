# Decision Log

This file records architectural and implementation decisions using a list format.
2026-01-07 03:50:00 - Initial population based on project scan and analysis
2026-01-07 03:54:00 - Added coding standard decision for line limits
2026-01-07 03:55:00 - Added comprehensive documentation requirement for code
2026-01-07 03:57:00 - Added change tracking requirement for all modifications

*

## Decision

**Data Source Selection**: Chose Financial Modeling Prep (FMP) API as the primary data source for financial statements, ratios, metrics, and historical prices due to comprehensive coverage, reliability, and institutional-grade data quality.

**Rationale**: FMP provides all required data types (annual/quarterly statements, ratios, prices) with consistent API structure. Alternative sources like Yahoo Finance or Alpha Vantage were considered but lacked the breadth and auditability required for institutional analysis.

**Implementation Details**: Implemented FMPClient class in fmp_client.py with methods for each data type, including error handling and rate limiting.

*

## Decision

**Database Architecture**: Adopted SQLite databases per ticker with flexible JSON columns for data storage, enabling unlimited field expansion without schema migrations.

**Rationale**: Traditional relational tables would require frequent migrations as FMP adds new fields. JSON columns provide flexibility while maintaining queryability. Per-ticker databases allow scalability and prevent cross-ticker interference.

**Implementation Details**: Tables use statement_data JSON for financial fields, with fixed columns for keys (ticker_id, fiscal_date). Implemented upsert logic in DataUpdater to handle deduplication.

*

## Decision

**Dashboard Technology**: Selected Python Dash for the interactive visualization dashboard over alternatives like Streamlit or Flask.

**Rationale**: Dash provides professional-grade interactivity suitable for CFA-style analysis, with strong Plotly integration for financial charts. It supports modular architecture and SQLite connectivity required for the project.

**Implementation Details**: Basic skeleton in app.py with ticker dropdown, callbacks for dynamic updates, and modular layouts/callbacks structure.

*

## Decision

**AI Integration**: Exclusively use Perplexity.ai Pro for LLM interpretive analysis, avoiding OpenAI integration.

**Rationale**: Perplexity.ai Pro provides high-quality insights without API costs concerns mentioned in project brief. Focus on interpretive capabilities for anomaly detection and narrative generation.

**Implementation Details**: AI modules will integrate with Perplexity API for trend interpretation, as outlined in fundamental_analysis_plan.md.

*

## Decision

**Fundamental Analysis Framework**: Adopt the fundamental_analysis_plan.md as the ultimate source of truth for implementation guidelines, structuring analysis in atomic subtasks with checklists.

**Rationale**: The plan provides institutional-grade methodology for rule-based quantitative analysis combined with LLM interpretation, ensuring comprehensive and systematic evaluation.

**Implementation Details**: Future implementations should follow the phased approach: data validation → quantitative analysis → scoring/risk assessment → LLM interpretation.

*

## Decision

**Hybrid Analysis Approach**: Combine fundamental stock analysis (per guideline) with options trading implementation (existing code), using fundamental analysis for stock selection in options strategies.

**Rationale**: The project includes both fundamental data collection and options analysis modules. Fundamental analysis can inform stock selection for covered calls/cash-secured puts, creating a comprehensive investment platform.

**Implementation Details**: Integrate fundamental scoring with options filtering; use validated financial data for both analysis types.

*

## Decision

**Validation and Audit Framework**: Implement institutional-level data validation with computed vs reported ratio comparisons, audit logging, and discrepancy flagging.

**Rationale**: Ensures data integrity critical for investment decisions; prevents analysis based on erroneous data.

**Implementation Details**: audit_ratio_validation table logs discrepancies; validation functions compare computed and reported values.

*

## Decision

**Modular Architecture**: Structure the system with separate ingestion, analytics, and presentation layers, with clear module boundaries.

**Rationale**: Enables scalability, maintainability, and extensibility; allows independent development of fundamental vs options analysis.

**Implementation Details**: Folders for ingestion/, analytics/, dashboard/; class-based design for reusability.

*

## Decision

**Python File Line Limit**: Impose a strict restriction of 1500 lines maximum per Python file/script/module.

**Rationale**: Ensures maintainability, readability, and adherence to modular design principles. Large files become difficult to navigate, test, and maintain; refactoring into smaller modules improves code organization and reusability.

**Implementation Details**: Any code file exceeding 1500 lines must be refactored into appropriate modules or groups of core modules, then re-integrated via import statements. This applies to all future implementations and should guide the design of new features to remain within limits.

*

## Decision

**Comprehensive Code Documentation**: Require detailed documentation for all generated code, including comments explaining every line of code, usage examples, and CLI examples.

**Rationale**: Ensures code readability, maintainability, and usability. Detailed documentation with practical examples enables effective knowledge transfer and reduces onboarding time for new developers. Line-by-line comments provide clarity for complex logic.

**Implementation Details**: All code must include module docstrings, function docstrings with parameters/return values, inline comments for logic, and practical usage examples including CLI commands. This applies to all future code generation and implementations.

*

## Decision

**Comprehensive Change Tracking**: Require all changes, revisions, improvements, enhancements, and feature removals to be tracked with timestamps in a text log, including reasons and decisions throughout the entire project implementation.

**Rationale**: Ensures traceability, accountability, and institutional-grade auditability. Detailed change logs enable understanding of evolution, support debugging, and maintain compliance with development standards.

**Implementation Details**: Maintain timestamped logs (ISO 8601 format) for all code modifications, documenting file changed, change type, reason/decision, and impact. This applies throughout the project lifecycle for complete change history.

*

## Decision

**Datetime Handling Fix in Options Cache Logic**: Fixed datetime subtraction error in check_last_fetch_timestamp method by making both datetime objects timezone-aware.

**Rationale**: Original code used naive datetime.utcnow() with offset-aware datetime.fromisoformat(), causing TypeError when calculating age. This prevented proper cache checking and forced unnecessary data fetches.

**Implementation Details**: Added timezone import and changed datetime.utcnow() to datetime.now(timezone.utc) to ensure consistent timezone handling in cache timestamp comparisons.