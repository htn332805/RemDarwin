# MyCFATool – Personal Institutional-Grade Financial Analysis Platform

## 1. Project Overview

**MyCFATool** is a personal, institutional-grade financial data platform designed to automate the collection, storage, verification, analysis, and visualization of equity financial data.  
The system will integrate with **Financial Modeling Prep (FMP)** to retrieve financial statements, ratios, metrics, and historical prices, store them in **SQLite databases**, and expose the data via a **Python Dash dashboard** for professional-grade technical and fundamental analysis. It will integrate some robust AI features to help identify and analyze financial trends via perplexity.ai API using the Pro account only NO OPENAI integration

The tool is designed to support **CFA-style financial modeling, auditing, and validation** as a collections of cli command that can be scriptup and automated easily, with an emphasis on data accuracy, reproducibility, and continuous updates. It design is focus on simplicity, modularity, scalabiliyty, extensibility, and future-proofing to accommodate new data fields and analysis techniques.

---

## 2. Core Objectives

1. Automatically download and retrieve financial data from **Financial Modeling Prep (FMP)**.
2. Store all retrieved data as:
   - CSV files (for auditability)
   - SQLite databases named `<TICKER>_sqlite.db`
3. Build a **Python Dash** dashboard to:
   - Visualize historical financial trends
   - Display technical indicators
   - Forecast future financial performance
4. Support **both quarterly and annual financial data**
5. Retrieve and compute **financial ratios and metrics**
6. Independently **recalculate and verify all ratios** against reported values
7. Implement **institutional-level data validation and audit checks**
8. Enable **incremental data updates**, avoiding duplicates and appending only new records

---

## 3. Data Sources

### Primary API
- **Financial Modeling Prep (FMP)**
  - Income Statement (Annual & Quarterly)
  - Balance Sheet (Annual & Quarterly)
  - Cash Flow Statement (Annual & Quarterly)
  - Financial Ratios
  - Key Metrics
  - Enterprise Value
  - Historical Price Data (Daily)
  - Company Profile & Metadata

---

## 4. System Architecture

MyCFATool/
│
├── data/
│ ├── raw/
│ │ ├── csv/
│ │ └── api_responses/
│ ├── processed/
│ └── audit_logs/
│
├── database/
│ └── <TICKER>_sqlite.db
│
├── ingestion/
│ ├── fmp_client.py
│ ├── data_fetcher.py
│ ├── data_validator.py
│ └── data_updater.py
│
├── analytics/
│ ├── fundamentals.py
│ ├── ratios.py
│ ├── technicals.py
│ └── forecasting.py
│
├── dashboard/
│ ├── app.py
│ ├── layouts.py
│ ├── callbacks.py
│ └── components/
│
├── config/
│ ├── settings.yaml
│ └── tickers.yaml
│
├── tests/
│ ├── test_ingestion.py
│ ├── test_ratios.py
│ └── test_data_integrity.py
│
└── README.md


---

## 5. Database Design (SQLite)

Each ticker will have its own database:  
**`<TICKER>_sqlite.db`**

### Core Tables

- `income_statement_annual`
- `income_statement_quarterly`
- `balance_sheet_annual`
- `balance_sheet_quarterly`
- `cash_flow_annual`
- `cash_flow_quarterly`
- `financial_ratios_reported`
- `financial_ratios_computed`
- `key_metrics`
- `historical_prices`
- `audit_results`
- `update_log`

### Constraints
- Primary keys based on:
  - `symbol`
  - `date`
  - `period`
- Enforce **unique constraints** to prevent duplicate records

---

## 6. Data Ingestion & Update Logic

### Initial Load
- Fetch full historical datasets from FMP
- Save raw API responses to disk
- Convert to structured CSV files
- Insert into SQLite database

### Incremental Updates
- On scheduled execution (weekly/monthly):
  1. Fetch latest data from FMP
  2. Compare against existing database records
  3. Ignore duplicated records
  4. Append only new data
  5. Log all updates and changes

---

## 7. Financial Ratios & Validation

### Reported Ratios
- Retrieved directly from FMP

### Computed Ratios
- Independently calculated from raw financial statements:
  - Profitability (ROE, ROA, margins)
  - Liquidity (Current, Quick ratios)
  - Leverage (Debt ratios)
  - Efficiency (Turnover ratios)
  - Valuation (P/E, EV/EBITDA, etc.)

### Validation Process
- Compare reported vs computed values
- Flag discrepancies beyond configurable thresholds
- Store results in `audit_results` table
- Generate audit logs for institutional-grade review

---

## 8. Technical Analysis

- Historical price analysis
- Indicators:
  - Moving Averages
  - RSI
  - MACD
  - Bollinger Bands
  - Volatility measures
- Stored and recalculated on demand

---

## 9. Forecasting & Modeling

- Time-series forecasting of:
  - Revenue
  - EBITDA
  - Free Cash Flow
- Models may include:
  - Linear regression
  - ARIMA / SARIMA
  - Prophet (optional)
- Forecast results stored separately for transparency

---

## 10. Dashboard (Python Dash)

### Features
- Ticker selection
- Financial statement trend charts
- Ratio dashboards
- Technical indicator charts
- Forecast visualizations
- Audit & validation summary panels

### Design Goals
- Clean, professional, CFA-style layout
- Fast interaction using SQLite queries
- Modular and extensible architecture

---

## 11. Configuration & Security

- API keys stored in environment variables
- Configurable tickers and update frequency
- Logging and error handling throughout ingestion and analytics pipelines

---

## 12. Quality & Testing Requirements

- Unit tests for:
  - Data ingestion
  - Ratio computation
  - Duplicate detection
- Data integrity checks
- Reproducible results for audit purposes

---

## 13. Future Enhancements

- Multi-ticker portfolio analysis
- DCF valuation models
- Scenario & sensitivity analysis
- Export reports to PDF
- Cloud database support

---

## 14. Success Criteria

- Accurate, validated financial data
- Zero duplicate records
- Transparent audit trail
- Professional-grade analytics and visualization
- Easily extensible for future CFA-level research

---

Below is a future-proof SQLite schema design written in Markdown and SQL, optimized for:
Schema flexibility / column expansion
Auditability
Institutional-grade financial analysis
Safe incremental updates
Quarterly & Annual support
Separation of raw vs computed data
The design intentionally combines relational tables + semi-structured JSON columns so new fields from FMP or new computed metrics can be added without breaking the schema.
SQLite Schema Design for MyCFATool
Design Principles
Stable Core Columns
Dates, ticker, period, source, versioning
Flexible JSON Payloads
Allows unlimited future expansion
Computed vs Reported Separation
Prevents data contamination
Strong Deduplication Rules
Prevents double inserts
Audit & Reproducibility
Raw data is never overwritten
1. Metadata Tables
1.1 Ticker Registry
CREATE TABLE IF NOT EXISTS ticker (
    ticker_id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL UNIQUE,
    company_name TEXT,
    exchange TEXT,
    sector TEXT,
    industry TEXT,
    currency TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
1.2 Data Source Registry
CREATE TABLE IF NOT EXISTS data_source (
    source_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    provider TEXT NOT NULL,
    api_version TEXT,
    retrieved_at TEXT DEFAULT CURRENT_TIMESTAMP
);
2. Financial Statements (Flexible JSON-Driven)
Common Pattern
statement_data JSON holds all numeric fields
Only key identifiers are fixed columns
Works for both annual and quarterly
2.1 Income Statement
CREATE TABLE IF NOT EXISTS income_statement (
    statement_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker_id INTEGER NOT NULL,
    period_type TEXT CHECK (period_type IN ('annual', 'quarterly')),
    fiscal_date TEXT NOT NULL,
    fiscal_year INTEGER,
    fiscal_quarter INTEGER,
    statement_data JSON NOT NULL,
    source_id INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (ticker_id, period_type, fiscal_date),
    FOREIGN KEY (ticker_id) REFERENCES ticker(ticker_id),
    FOREIGN KEY (source_id) REFERENCES data_source(source_id)
);
2.2 Balance Sheet
CREATE TABLE IF NOT EXISTS balance_sheet (
    statement_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker_id INTEGER NOT NULL,
    period_type TEXT CHECK (period_type IN ('annual', 'quarterly')),
    fiscal_date TEXT NOT NULL,
    fiscal_year INTEGER,
    fiscal_quarter INTEGER,
    statement_data JSON NOT NULL,
    source_id INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (ticker_id, period_type, fiscal_date),
    FOREIGN KEY (ticker_id) REFERENCES ticker(ticker_id),
    FOREIGN KEY (source_id) REFERENCES data_source(source_id)
);
2.3 Cash Flow Statement
CREATE TABLE IF NOT EXISTS cash_flow (
    statement_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker_id INTEGER NOT NULL,
    period_type TEXT CHECK (period_type IN ('annual', 'quarterly')),
    fiscal_date TEXT NOT NULL,
    fiscal_year INTEGER,
    fiscal_quarter INTEGER,
    statement_data JSON NOT NULL,
    source_id INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (ticker_id, period_type, fiscal_date),
    FOREIGN KEY (ticker_id) REFERENCES ticker(ticker_id),
    FOREIGN KEY (source_id) REFERENCES data_source(source_id)
);
3. Historical Prices (Normalized but Extendable)
CREATE TABLE IF NOT EXISTS historical_price (
    price_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker_id INTEGER NOT NULL,
    trade_date TEXT NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    adj_close REAL,
    volume INTEGER,
    extra_data JSON,
    source_id INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (ticker_id, trade_date),
    FOREIGN KEY (ticker_id) REFERENCES ticker(ticker_id),
    FOREIGN KEY (source_id) REFERENCES data_source(source_id)
);
4. Financial Ratios & Metrics
4.1 Reported Ratios (From FMP)
CREATE TABLE IF NOT EXISTS financial_ratio_reported (
    ratio_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker_id INTEGER NOT NULL,
    period_type TEXT CHECK (period_type IN ('annual', 'quarterly')),
    fiscal_date TEXT NOT NULL,
    ratio_data JSON NOT NULL,
    source_id INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (ticker_id, period_type, fiscal_date),
    FOREIGN KEY (ticker_id) REFERENCES ticker(ticker_id),
    FOREIGN KEY (source_id) REFERENCES data_source(source_id)
);
4.2 Computed Ratios (Internal Calculations)
CREATE TABLE IF NOT EXISTS financial_ratio_computed (
    ratio_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker_id INTEGER NOT NULL,
    period_type TEXT CHECK (period_type IN ('annual', 'quarterly')),
    fiscal_date TEXT NOT NULL,
    ratio_data JSON NOT NULL,
    calculation_version TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (ticker_id, period_type, fiscal_date, calculation_version),
    FOREIGN KEY (ticker_id) REFERENCES ticker(ticker_id)
);
5. Key Metrics & Valuation Data
CREATE TABLE IF NOT EXISTS key_metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker_id INTEGER NOT NULL,
    period_type TEXT CHECK (period_type IN ('annual', 'quarterly')),
    fiscal_date TEXT NOT NULL,
    metric_data JSON NOT NULL,
    source_id INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (ticker_id, period_type, fiscal_date),
    FOREIGN KEY (ticker_id) REFERENCES ticker(ticker_id),
    FOREIGN KEY (source_id) REFERENCES data_source(source_id)
);
6. Forecasting Outputs
CREATE TABLE IF NOT EXISTS forecast (
    forecast_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker_id INTEGER NOT NULL,
    model_name TEXT NOT NULL,
    target_variable TEXT NOT NULL,
    forecast_start_date TEXT,
    forecast_end_date TEXT,
    forecast_data JSON NOT NULL,
    model_parameters JSON,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticker_id) REFERENCES ticker(ticker_id)
);
7. Audit & Validation Framework
7.1 Ratio Validation Results
CREATE TABLE IF NOT EXISTS audit_ratio_validation (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker_id INTEGER NOT NULL,
    fiscal_date TEXT NOT NULL,
    ratio_name TEXT NOT NULL,
    reported_value REAL,
    computed_value REAL,
    absolute_diff REAL,
    relative_diff REAL,
    pass_flag INTEGER CHECK (pass_flag IN (0,1)),
    tolerance REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticker_id) REFERENCES ticker(ticker_id)
);
7.2 Data Update Log
CREATE TABLE IF NOT EXISTS update_log (
    update_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker_id INTEGER NOT NULL,
    table_name TEXT NOT NULL,
    records_added INTEGER,
    records_skipped INTEGER,
    update_type TEXT,
    executed_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticker_id) REFERENCES ticker(ticker_id)
);
8. Indexing Strategy (Performance)
CREATE INDEX IF NOT EXISTS idx_income_statement_lookup
ON income_statement (ticker_id, period_type, fiscal_date);

CREATE INDEX IF NOT EXISTS idx_price_lookup
ON historical_price (ticker_id, trade_date);

CREATE INDEX IF NOT EXISTS idx_ratio_lookup
ON financial_ratio_computed (ticker_id, fiscal_date);
9. Why This Schema Is Future-Proof
✔ JSON columns allow unlimited new financial fields
✔ No schema migration required for new FMP attributes
✔ Strong uniqueness constraints prevent duplicates
✔ Supports institutional audit & recomputation
✔ Dash-friendly query patterns
✔ Compatible with Python, Pandas, and SQLAlchemy

Perfect! I’ll create starter Python modules for your MyCFATool project:
FMP client – fetch financial data and ratios.
Updater – store and update data in SQLite with deduplication.
Dash app skeleton – basic dashboard to visualize financials.
All modules are extensible and ready for your future expansion.
1️⃣ fmp_client.py – Financial Modeling Prep API Client
import requests
import os
import pandas as pd

class FMPClient:
    """
    Client for Financial Modeling Prep (FMP) API.
    Retrieves financial statements, ratios, metrics, and historical prices.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("FMP_API_KEY")
        self.base_url = "https://financialmodelingprep.com/api/v3/"

    def _get(self, endpoint: str, params: dict = None):
        if params is None:
            params = {}
        params["apikey"] = self.api_key
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_income_statement(self, ticker: str, period: str = "annual", limit: int = 120):
        endpoint = f"income-statement/{ticker}"
        if period not in ["annual", "quarterly"]:
            raise ValueError("period must be 'annual' or 'quarterly'")
        data = self._get(endpoint, {"period": period, "limit": limit})
        return pd.DataFrame(data)

    def get_balance_sheet(self, ticker: str, period: str = "annual", limit: int = 120):
        endpoint = f"balance-sheet-statement/{ticker}"
        data = self._get(endpoint, {"period": period, "limit": limit})
        return pd.DataFrame(data)

    def get_cash_flow(self, ticker: str, period: str = "annual", limit: int = 120):
        endpoint = f"cash-flow-statement/{ticker}"
        data = self._get(endpoint, {"period": period, "limit": limit})
        return pd.DataFrame(data)

    def get_ratios(self, ticker: str, period: str = "annual", limit: int = 120):
        endpoint = f"ratios/{ticker}"
        data = self._get(endpoint, {"period": period, "limit": limit})
        return pd.DataFrame(data)

    def get_historical_price(self, ticker: str, timeseries: int = 365):
        endpoint = f"historical-price-full/{ticker}"
        data = self._get(endpoint, {"serietype": "line", "timeseries": timeseries})
        return pd.DataFrame(data.get("historical", []))
2️⃣ data_updater.py – SQLite Updater & Deduplicator
import sqlite3
import pandas as pd
import json
from datetime import datetime

class DataUpdater:
    """
    Handles storage and updating of FMP data in SQLite.
    Avoids duplicates and appends new data automatically.
    """

    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON;")

    def upsert_dataframe(self, df: pd.DataFrame, table: str, unique_cols: list):
        """
        Upserts a DataFrame into a table using unique constraints.
        Converts all non-numeric fields to JSON strings for flexibility.
        """
        if df.empty:
            return 0, 0

        cursor = self.conn.cursor()
        records_added = 0
        records_skipped = 0

        for _, row in df.iterrows():
            # Convert row to dict and JSON for flexible columns
            row_dict = row.to_dict()
            json_data = json.dumps(row_dict)
            fiscal_date = row_dict.get("date") or row_dict.get("calendarDate") or datetime.now().strftime("%Y-%m-%d")
            # Check duplicate
            query = f"""
            SELECT 1 FROM {table}
            WHERE {" AND ".join([f"{col} = ?" for col in unique_cols])}
            LIMIT 1
            """
            cursor.execute(query, tuple(row_dict[col] for col in unique_cols))
            exists = cursor.fetchone()
            if exists:
                records_skipped += 1
                continue

            # Insert record
            insert_query = f"""
            INSERT INTO {table} (ticker_id, period_type, fiscal_date, statement_data, created_at)
            VALUES (?, ?, ?, ?, ?)
            """
            cursor.execute(insert_query, (
                row_dict.get("ticker_id"),
                row_dict.get("period_type", "annual"),
                fiscal_date,
                json_data,
                datetime.now().isoformat()
            ))
            records_added += 1

        self.conn.commit()
        return records_added, records_skipped

    def close(self):
        self.conn.close()
✅ Note: This is generic for income, balance sheet, cash flow, ratios. You can extend upsert_dataframe for other tables.
3️⃣ app.py – Dash Dashboard Skeleton
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import sqlite3
import pandas as pd

# -------------------------
# App Initialization
# -------------------------
app = dash.Dash(__name__)
app.title = "MyCFATool Dashboard"

DB_PATH = "AAPL_sqlite.db"  # example

# -------------------------
# Layout
# -------------------------
app.layout = html.Div([
    html.H1("MyCFATool Financial Dashboard"),
    html.Label("Select Ticker:"),
    dcc.Dropdown(
        id="ticker-dropdown",
        options=[{"label": "AAPL", "value": "AAPL"}],  # extend dynamically
        value="AAPL"
    ),
    html.Br(),
    html.Div(id="dashboard-content")
])

# -------------------------
# Callbacks
# -------------------------
@app.callback(
    Output("dashboard-content", "children"),
    Input("ticker-dropdown", "value")
)
def update_dashboard(ticker):
    conn = sqlite3.connect(f"{ticker}_sqlite.db")
    df = pd.read_sql("SELECT fiscal_date, json_extract(statement_data, '$.revenue') AS revenue FROM income_statement ORDER BY fiscal_date", conn)
    conn.close()

    if df.empty:
        return html.P("No data available.")

    return html.Div([
        dcc.Graph(
            figure={
                "data": [
                    {"x": df["fiscal_date"], "y": df["revenue"], "type": "line", "name": ticker}
                ],
                "layout": {"title": f"{ticker} Revenue Trend"}
            }
        )
    ])

# -------------------------
# Run Server
# -------------------------
if __name__ == "__main__":
    app.run_server(debug=True)
✅ Notes / Next Steps:
FMP Client
Can be extended for key_metrics, forecasting, and extra ratios.
Updater
Handles deduplication.
Can be enhanced with batch inserts for performance.
Add audit logging table updates.
Dash App
Skeleton supports dynamic ticker selection.
Easily extendable for ratios, forecasts, technical charts.
JSON parsing in statement_data allows any new fields from FMP without schema changes.

Here’s a comprehensive, step-by-step roadmap to build your MyCFATool from scratch. I structured it so you can go from data ingestion → storage → analysis → dashboard → automation, with milestones for future enhancements.
MyCFATool Build Roadmap
Phase 0 – Project Setup
Goals: Establish the environment, repository, and basic structure.
Steps:
Initialize Git repository for version control.
Create Python virtual environment:
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
Install required libraries:
pip install requests pandas dash sqlite3 sqlalchemy plotly python-dotenv
Organize project folders:
MyCFATool/
├── data/
├── database/
├── ingestion/
├── analytics/
├── dashboard/
├── config/
├── tests/
└── projectBrief.md
Set up .env or config/settings.yaml for API keys and global parameters.
Phase 1 – Data Ingestion & FMP Client
Goals: Retrieve financial and price data from FMP.
Steps:
Create fmp_client.py:
Functions: get_income_statement, get_balance_sheet, get_cash_flow, get_ratios, get_historical_price.
Test API client for one ticker (e.g., AAPL) and store results in CSV.
Create unit tests for API response validation.
Extend client to handle annual and quarterly data.
Deliverable: Verified API client capable of fetching all required data.
Phase 2 – Database Design & Updater
Goals: Store all data in SQLite with flexibility and auditability.
Steps:
Design SQLite schema (see previous schema with JSON columns).
Create data_updater.py:
Functions: upsert_dataframe, deduplication logic, logging.
Test inserting sample data from CSV/API into SQLite.
Implement unique constraints to prevent duplicates.
Add audit logs for each insert/update.
Deliverable: SQLite database ready with initial data.
Phase 3 – Financial Ratio Computation & Validation
Goals: Compute ratios and compare to FMP reported ratios.
Steps:
Create analytics/ratios.py:
Compute profitability, liquidity, leverage, efficiency, and valuation ratios.
Create analytics/fundamentals.py:
Aggregate and clean statements for calculation.
Implement validation:
Compare computed vs reported values.
Store differences in audit_ratio_validation.
Add unit tests for all calculations.
Deliverable: Verified, auditable ratios in database.
Phase 4 – Technical Analysis Module
Goals: Add historical price analysis for trend detection.
Steps:
Create analytics/technicals.py:
Compute moving averages, RSI, MACD, Bollinger Bands.
Store results in SQLite (optional JSON for flexibility).
Test retrieval and plotting using Pandas/Plotly.
Deliverable: Technical analysis ready for integration in Dash.
Phase 5 – Forecasting Module
Goals: Predict financials (revenue, EBITDA, cash flow) using time-series models.
Steps:
Create analytics/forecasting.py:
Implement ARIMA, SARIMA, or Prophet models.
Store forecasts in forecast table in JSON format.
Implement versioning of forecasts for audit purposes.
Deliverable: Forecast module ready to produce future projections.
Phase 6 – Dash Dashboard Skeleton
Goals: Visualize financials, ratios, technicals, and forecasts.
Steps:
Create dashboard/app.py skeleton.
Add:
Ticker selection dropdown
Revenue trend chart
Ratios overview panel
Technical analysis chart
Forecast chart
Make layout modular:
layouts.py and callbacks.py for extensibility.
Connect dashboard to SQLite using Pandas queries.
Deliverable: Interactive dashboard showing trends and metrics.
Phase 7 – Automation & Incremental Updates
Goals: Regularly fetch new data and update database.
Steps:
Schedule jobs (e.g., using cron, Windows Task Scheduler, or APScheduler).
Ensure:
Deduplication
Logging of added/skipped records
Versioning of forecasts
Create scripts/update_all.py to:
Fetch all tickers
Update financial statements, ratios, metrics, prices
Run audit and validation
Deliverable: Automated weekly/monthly update pipeline.
Phase 8 – Testing & Audit
Goals: Ensure institutional-grade data quality.
Steps:
Unit tests for:
Data ingestion
Ratio computation
Deduplication
Forecasting
Integration tests for:
SQLite updates
Dashboard rendering
Audit:
Verify computed ratios vs reported
Check consistency of historical data
Log any discrepancies
Deliverable: Verified, auditable financial database and dashboard.
Phase 9 – Future Enhancements
Ideas:
Multi-ticker portfolio analysis
DCF / valuation models
Scenario & sensitivity analysis
Export dashboard/report to PDF
Cloud DB support for scalability
✅ Milestones Summary
Phase	Milestone
0	Project setup, environment, folders
1	FMP client tested and CSV storage ready
2	SQLite DB design, upsert module working
3	Computed & validated ratios in DB
4	Technical analysis implemented
5	Forecasting module producing predictions
6	Dash dashboard skeleton displaying data
7	Automated updates & deduplication
8	Testing, audit, and quality assurance
9	Advanced analytics & cloud-ready enhancements

Phase 0 – Project Setup
Initialize Git repository
"Create a new Git repository for the project MyCFATool with a standard .gitignore for Python."
Create project structure
"Create the following folder structure for MyCFATool: data/, database/, ingestion/, analytics/, dashboard/, config/, tests/. Include a placeholder README.md."
Setup virtual environment and dependencies
"Create a Python virtual environment and install requests, pandas, dash, plotly, sqlalchemy, python-dotenv."
Create configuration files
"Create config/settings.yaml and .env to store API keys, ticker list, and update frequency."
Phase 1 – FMP Client
Implement FMP API client class
"Write fmp_client.py with a class FMPClient that retrieves income statements, balance sheets, cash flow, ratios, and historical prices using the FMP API. Include annual and quarterly support."
Add API error handling
"Add robust error handling for HTTP errors, missing fields, and rate limits in FMPClient."
Test API client
"Fetch sample data for ticker AAPL and save as CSV to data/raw/."
Phase 2 – Database Design & Updater
Create SQLite schema
"Generate SQLite database AAPL_sqlite.db with tables: income_statement, balance_sheet, cash_flow, financial_ratio_reported, financial_ratio_computed, historical_price, key_metrics, forecast, audit_ratio_validation, and update_log using flexible JSON columns for data fields."
Implement DataUpdater module
"Write data_updater.py with a class DataUpdater that can upsert Pandas DataFrames into SQLite tables while avoiding duplicates."
Test DataUpdater
"Insert sample CSV data for income_statement into SQLite and verify that duplicates are ignored."
Phase 3 – Financial Ratio Computation & Validation
Implement ratio calculations
"Create analytics/ratios.py to compute profitability, liquidity, leverage, efficiency, and valuation ratios from raw financial statements."
Compare computed vs reported ratios
"Add a function to validate computed ratios against reported ratios and log discrepancies in audit_ratio_validation table."
Add unit tests for ratio calculations
"Write unit tests to check correctness of computed ratios for sample tickers."
Phase 4 – Technical Analysis
Compute technical indicators
"Create analytics/technicals.py to compute moving averages, RSI, MACD, and Bollinger Bands from historical price data."
Store technical indicators in SQLite
"Add optional JSON column extra_data in historical_price to store computed technical indicators."
Test technical analysis module
"Visualize indicators for AAPL using Matplotlib or Plotly to verify correctness."
Phase 5 – Forecasting Module
Implement time-series forecasting
"Create analytics/forecasting.py using ARIMA or Prophet to forecast revenue, EBITDA, and cash flow."
Store forecasts in SQLite
"Save forecast results as JSON in forecast table with model_name, target_variable, forecast_start_date, forecast_end_date."
Test forecasting module
"Generate sample forecast for AAPL revenue and visualize predictions vs historical data."
Phase 6 – Dash Dashboard Skeleton
Setup Dash app
"Create dashboard/app.py with a basic layout including ticker dropdown and content div."
Connect dashboard to SQLite
"Load income_statement data from SQLite and display revenue trend chart using Plotly."
Add dynamic callbacks
"Implement Dash callback to update charts when a different ticker is selected."
Modularize layout and callbacks
"Create dashboard/layouts.py and dashboard/callbacks.py to separate UI components from logic."
Phase 7 – Automation & Incremental Updates
Schedule periodic updates
"Write a script scripts/update_all.py to fetch new data from FMP and update SQLite weekly or monthly."
Implement deduplication and logging
"Ensure only new records are inserted and update update_log table with counts of added/skipped records."
Test automated pipeline
"Run full update script for multiple tickers and verify database consistency."
Phase 8 – Testing & Audit
Write unit tests
"Test ingestion, ratio calculation, deduplication, and forecasting modules."
Write integration tests
"Verify end-to-end pipeline: API fetch → SQLite update → dashboard rendering."
Perform audit
"Compare computed ratios to reported ratios, log discrepancies, and ensure historical data integrity."
Phase 9 – Future Enhancements (Optional Tasks)
Add multi-ticker portfolio analysis
Implement DCF valuation module
Add scenario & sensitivity analysis
Enable PDF report export from Dash
Upgrade to cloud database support

**End of Project Brief**
