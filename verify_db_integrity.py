#!/usr/bin/env python3
"""Database integrity verification script for batch ingestion test."""

import sys
import os
from pathlib import Path

# Add the MyCFATool package to the path
sys.path.insert(0, str(Path(__file__).parent / 'MyCFATool'))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from MyCFATool.ingestion.models import (
    Base, Ticker, IncomeStatement, BalanceSheet, CashFlow,
    FinancialRatioReported, FinancialRatioComputed, HistoricalPrice
)

# Database URL
DATABASE_URL = 'sqlite:///database/database.db'

def get_session():
    engine = create_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()

def verify_ticker_presence(session, tickers):
    """Verify that all tickers are present in the database."""
    print("=== TICKER PRESENCE VERIFICATION ===")
    for ticker_symbol in tickers:
        ticker = session.query(Ticker).filter(Ticker.symbol == ticker_symbol).first()
        if ticker:
            print(f"✓ {ticker_symbol}: Present (ID: {ticker.ticker_id})")
        else:
            print(f"✗ {ticker_symbol}: MISSING")
    print()

def count_records(session, tickers):
    """Count records for each data type."""
    print("=== RECORD COUNTS ===")

    tables = [
        ('Income Statement', IncomeStatement),
        ('Balance Sheet', BalanceSheet),
        ('Cash Flow', CashFlow),
        ('Financial Ratios (Reported)', FinancialRatioReported),
        ('Financial Ratios (Computed)', FinancialRatioComputed),
        ('Historical Price', HistoricalPrice)
    ]

    ticker_ids = {t.symbol: t.ticker_id for t in session.query(Ticker).filter(Ticker.symbol.in_(tickers)).all()}

    for table_name, model in tables:
        print(f"\n{table_name}:")

        if model == HistoricalPrice:
            # Historical price has no period_type
            counts = session.query(model.ticker_id, func.count(model.price_id)).\
                filter(model.ticker_id.in_(ticker_ids.values())).\
                group_by(model.ticker_id).all()

            for ticker_id, count in counts:
                symbol = next((s for s, tid in ticker_ids.items() if tid == ticker_id), 'UNKNOWN')
                print(f"  {symbol}: {count} records")
        else:
            # Other tables have period_type
            counts = session.query(model.ticker_id, model.period_type, func.count(model.statement_id if hasattr(model, 'statement_id') else model.ratio_id)).\
                filter(model.ticker_id.in_(ticker_ids.values())).\
                group_by(model.ticker_id, model.period_type).all()

            for ticker_id, period_type, count in counts:
                symbol = next((s for s, tid in ticker_ids.items() if tid == ticker_id), 'UNKNOWN')
                print(f"  {symbol} ({period_type}): {count} records")

def validate_data_quality(session, tickers):
    """Validate data quality: no null fiscal dates, valid period types."""
    print("\n\n=== DATA QUALITY VALIDATION ===")

    ticker_ids = {t.symbol: t.ticker_id for t in session.query(Ticker).filter(Ticker.symbol.in_(tickers)).all()}

    tables = [
        ('Income Statement', IncomeStatement, 'statement_id'),
        ('Balance Sheet', BalanceSheet, 'statement_id'),
        ('Cash Flow', CashFlow, 'statement_id'),
        ('Financial Ratios (Reported)', FinancialRatioReported, 'ratio_id'),
        ('Financial Ratios (Computed)', FinancialRatioComputed, 'ratio_id')
    ]

    for table_name, model, id_field in tables:
        print(f"\n{table_name}:")

        # Check for null fiscal_date
        null_dates = session.query(func.count(getattr(model, id_field))).\
            filter(model.ticker_id.in_(ticker_ids.values())).\
            filter(model.fiscal_date.is_(None)).scalar()

        if null_dates > 0:
            print(f"  ✗ {null_dates} records with NULL fiscal_date")
        else:
            print("  ✓ No NULL fiscal_date")

        # Check for invalid period_type
        query = session.query(func.count(getattr(model, id_field)))
        query = query.filter(model.ticker_id.in_(ticker_ids.values()))
        query = query.filter(~model.period_type.in_(['annual', 'quarterly']))
        invalid_periods = query.scalar()

        if invalid_periods > 0:
            print(f"  ✗ {invalid_periods} records with invalid period_type")
        else:
            print("  ✓ All period_type values are valid")

def read_batch_ingestion_log():
    """Read and summarize the batch ingestion log."""
    print("\n\n=== BATCH INGESTION LOG SUMMARY ===")

    log_file = Path('logs/batch_ingestion_test.log')
    if not log_file.exists():
        print("✗ Log file not found")
        return

    try:
        with open(log_file, 'r') as f:
            log_content = f.read()

        print("Log file contents:")
        print("-" * 50)
        print(log_content)
        print("-" * 50)

    except Exception as e:
        print(f"Error reading log file: {e}")

def main():
    tickers = ['CRH', 'CVNA', 'FIX', 'ARES', 'SNDK', 'Q', 'APP', 'EME', 'HOOD', 'IBKR']

    session = get_session()
    try:
        verify_ticker_presence(session, tickers)
        count_records(session, tickers)
        validate_data_quality(session, tickers)
        read_batch_ingestion_log()

        print("\n\n=== SUMMARY ===")
        print("Database integrity verification completed.")
        print("Review the above output for any issues.")

    finally:
        session.close()

if __name__ == '__main__':
    main()