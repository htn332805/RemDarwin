# System Patterns *Optional*

This file documents recurring patterns and standards used in the project.
2026-01-02 03:23:22 - Initial population after project completion

*

## Coding Patterns

- **Modular Function Design**: Each fetch operation is a separate function with clear responsibilities
- **Consistent Parameter Order**: (ticker, api_key) for most functions, with period where applicable
- **Error Handling Pattern**: Try-except blocks with logging and continuation
- **URL Construction**: Template formatting with placeholders for dynamic values

*

## Architectural Patterns

- **CLI Application**: Command-line interface with argparse for argument processing
- **Template Method**: Endpoint templates with placeholders for API URL construction
- **Observer Pattern**: Logging system tracks operations without interfering with core logic
- **Strategy Pattern**: Different fetch functions for different endpoint categories

*

## Testing Patterns

- **Atomic Subtask Testing**: Each feature tested individually with 100% coverage
- **Integration Testing**: End-to-end testing of complete script functionality
- **Error Scenario Testing**: Testing failure modes and error handling
- **Output Validation**: Verification of CSV files, log files, and console output

*

## Data Processing Patterns

- **CSV Export Pattern**: DictWriter for structured data export with automatic headers
- **Data Merging**: Combining related data (technical indicators) on common keys
- **Graceful Degradation**: Continue processing despite individual data fetch failures