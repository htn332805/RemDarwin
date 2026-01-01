# Product Context

This file provides a high-level overview of the project and the expected product that will be created. Initially it is based upon projectBrief.md (if provided) and all other available project-related information in the working directory. This file is intended to be updated as the project evolves, and should be used to inform all other modes of the project's goals and context.

2025-12-31 23:22:25 - Initial population based on projectBrief.md

## Project Goal

MyCFATool is a personal, institutional-grade financial data platform designed to automate the collection, storage, verification, analysis, and visualization of equity financial data.  
The system will integrate with Financial Modeling Prep (FMP) to retrieve financial statements, ratios, metrics, and historical prices, store them in SQLite databases, and expose the data via a Python Dash dashboard for professional-grade technical and fundamental analysis.

## Key Features

- Automatically download and retrieve financial data from Financial Modeling Prep (FMP).
- Store all retrieved data as CSV files and SQLite databases named `<TICKER>_sqlite.db`.
- Build a Python Dash dashboard to visualize historical financial trends, display technical indicators, and forecast future financial performance.
- Support both quarterly and annual financial data.
- Retrieve and compute financial ratios and metrics.
- Independently recalculate and verify all ratios against reported values.
- Implement institutional-level data validation and audit checks.
- Enable incremental data updates, avoiding duplicates and appending only new records.

## Overall Architecture

MyCFATool/
├── data/
│ ├── raw/
│ │ ├── csv/
│ │ └── api_responses/
│ ├── processed/
│ └── audit_logs/
├── database/
│ └── <TICKER>_sqlite.db
├── ingestion/
│ ├── fmp_client.py
│ ├── data_fetcher.py
│ ├── data_validator.py
│ └── data_updater.py
├── analytics/
│ ├── fundamentals.py
│ ├── ratios.py
│ ├── technicals.py
│ └── forecasting.py
├── dashboard/
│ ├── app.py
│ ├── layouts.py
│ ├── callbacks.py
│ └── components/
├── config/
│ ├── settings.yaml
│ └── tickers.yaml
├── tests/
│ ├── test_ingestion.py
│ ├── test_ratios.py
│ └── test_data_integrity.py
└── README.md