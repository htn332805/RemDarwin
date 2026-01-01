# Decision Log

This file records architectural and implementation decisions using a list format.
2025-12-31 23:22:25 - Initial population.

## Decision

Use SQLite with JSON columns for flexibility in financial data storage.

## Rationale 

Allows unlimited new fields from FMP without schema changes.

## Implementation Details

As per schema in projectBrief.md