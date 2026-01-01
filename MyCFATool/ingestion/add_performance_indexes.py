#!/usr/bin/env python3
"""
Database migration script to add performance indexes for production optimization.
Run this script after deploying to production to add the new indexes.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine, text
from core.config import config

def add_performance_indexes():
    """Add strategic indexes for production performance."""

    db_url = config.get_database_url()
    engine = create_engine(db_url, echo=True)

    with engine.connect() as conn:
        print("Adding performance indexes...")

        try:
            # Ticker indexes
            print("Adding ticker indexes...")
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ticker_symbol ON ticker (symbol);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ticker_exchange ON ticker (exchange);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ticker_sector ON ticker (sector);"))

            # Historical Price indexes
            print("Adding historical price indexes...")
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_historical_price_lookup ON historical_price (ticker_id, trade_date);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_historical_price_date ON historical_price (trade_date);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_historical_price_ticker_date_desc ON historical_price (ticker_id, trade_date DESC);"))

            # Income Statement indexes
            print("Adding income statement indexes...")
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_income_statement_lookup ON income_statement (ticker_id, period_type, fiscal_date);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_income_statement_date ON income_statement (fiscal_date);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_income_statement_ticker_date ON income_statement (ticker_id, fiscal_date);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_income_statement_year ON income_statement (ticker_id, fiscal_year);"))

            # Balance Sheet indexes
            print("Adding balance sheet indexes...")
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_balance_sheet_lookup ON balance_sheet (ticker_id, period_type, fiscal_date);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_balance_sheet_date ON balance_sheet (fiscal_date);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_balance_sheet_ticker_date ON balance_sheet (ticker_id, fiscal_date);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_balance_sheet_year ON balance_sheet (ticker_id, fiscal_year);"))

            # Cash Flow indexes
            print("Adding cash flow indexes...")
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_cash_flow_lookup ON cash_flow (ticker_id, period_type, fiscal_date);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_cash_flow_date ON cash_flow (fiscal_date);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_cash_flow_ticker_date ON cash_flow (ticker_id, fiscal_date);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_cash_flow_year ON cash_flow (ticker_id, fiscal_year);"))

            # Financial Ratios Reported indexes
            print("Adding financial ratios reported indexes...")
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_financial_ratio_reported_lookup ON financial_ratio_reported (ticker_id, period_type, fiscal_date);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_financial_ratio_reported_date ON financial_ratio_reported (fiscal_date);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_financial_ratio_reported_ticker_date ON financial_ratio_reported (ticker_id, fiscal_date);"))

            # Financial Ratios Computed indexes
            print("Adding financial ratios computed indexes...")
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_financial_ratio_computed_lookup ON financial_ratio_computed (ticker_id, period_type, fiscal_date);"))

            # Key Metrics indexes
            print("Adding key metrics indexes...")
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_key_metrics_lookup ON key_metrics (ticker_id, period_type, fiscal_date);"))

            # Forecast indexes
            print("Adding forecast indexes...")
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_forecast_lookup ON forecast (ticker_id, model_name, target_variable);"))

            # Audit Ratio Validation indexes
            print("Adding audit ratio validation indexes...")
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_ratio_validation_lookup ON audit_ratio_validation (ticker_id, fiscal_date, ratio_name);"))

            conn.commit()
            print("All performance indexes added successfully!")
        except Exception as e:
            print(f"Error adding indexes: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    add_performance_indexes()