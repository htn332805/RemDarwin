# Decision Log

This file records architectural and implementation decisions using a list format.
2026-01-02 03:23:15 - Initial population after project completion

*

## Decision

Use Python CLI with argparse for command-line interface

*

## Rationale

Provides standard, user-friendly CLI with automatic help generation, validation, and error handling. More robust than custom parsing.

*

## Implementation Details

- Used argparse.ArgumentParser with description and program name
- Defined optional arguments with sensible defaults (AAPL ticker, ./output dir, annual period)
- Added help text for each argument
- Restricted period choices to 'annual' or 'quarterly' for validation

*

## Decision

Organize API endpoints in a centralized dictionary with templates

*

## Rationale

Avoids hardcoded URLs, enables easy maintenance and extension of endpoints, supports dynamic URL construction.

*

## Implementation Details

- Created ENDPOINTS dict with categories as keys
- Used sub-dicts for period types ('annual', 'quarterly', 'no_period')
- Included placeholders {ticker} and {apikey} for formatting
- Handled special cases like insider_trading variants and technical_indicators

*

## Decision

Implement comprehensive error handling with continuation

*

## Rationale

Ensures script robustness, prevents crashes on individual API failures, provides user feedback on issues.

*

## Implementation Details

- Wrapped all fetch calls in try-except blocks
- Printed error messages for failed fetches
- Continued processing other endpoints
- Added final summary with success/failure counts

*

## Decision

Combine technical indicators into single CSV file

*

## Rationale

Technical indicators share common price data columns, combining them reduces file count and improves usability.

*

## Implementation Details

- Modified fetch_technical_indicators to return combined dict
- Updated main logic to save single CSV with all indicator columns
- Merged data on date assuming consistent ordering

*

## Decision

Use logging to file with console output for essential messages

*

## Rationale

Provides detailed operation tracking while keeping console clean for important user feedback.

*

## Implementation Details

- Configured logging with filemode 'w', INFO level, timestamped format
- Replaced print statements with logging calls
- Retained console output for API URLs and final summary