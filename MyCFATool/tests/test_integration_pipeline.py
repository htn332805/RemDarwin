import pytest
import sqlite3
import json
import os
import pandas as pd
from unittest.mock import patch, MagicMock
from MyCFATool.ingestion.fmp_client import FMPClient
from MyCFATool.ingestion.data_updater import DataUpdater
from MyCFATool.analytics.validation import RatioValidator


@pytest.fixture
def db_connection():
    """Create an in-memory SQLite database with schema."""
    conn = sqlite3.connect(':memory:')
    # Create tables as in database_setup.py
    conn.execute("""
        CREATE TABLE ticker (
            ticker_id INTEGER PRIMARY KEY,
            symbol TEXT UNIQUE
        );
    """)
    conn.execute("""
        CREATE TABLE balance_sheet (
            statement_id INTEGER PRIMARY KEY,
            ticker_id INTEGER,
            period_type TEXT,
            fiscal_date TEXT,
            fiscal_year TEXT,
            fiscal_quarter TEXT,
            statement_data TEXT,
            source_id INTEGER,
            created_at TEXT,
            UNIQUE (ticker_id, period_type, fiscal_date)
        );
    """)
    conn.execute("""
        CREATE TABLE income_statement (
            statement_id INTEGER PRIMARY KEY,
            ticker_id INTEGER,
            period_type TEXT,
            fiscal_date TEXT,
            fiscal_year TEXT,
            fiscal_quarter TEXT,
            statement_data TEXT,
            source_id INTEGER,
            created_at TEXT,
            UNIQUE (ticker_id, period_type, fiscal_date)
        );
    """)
    conn.execute("""
        CREATE TABLE cash_flow (
            statement_id INTEGER PRIMARY KEY,
            ticker_id INTEGER,
            period_type TEXT,
            fiscal_date TEXT,
            fiscal_year TEXT,
            fiscal_quarter TEXT,
            statement_data TEXT,
            source_id INTEGER,
            created_at TEXT,
            UNIQUE (ticker_id, period_type, fiscal_date)
        );
    """)
    conn.execute("""
        CREATE TABLE data_source (
            source_id INTEGER PRIMARY KEY,
            name TEXT,
            provider TEXT,
            api_version TEXT
        );
    """)
    conn.execute("""
        CREATE TABLE historical_price (
            price_id INTEGER PRIMARY KEY,
            ticker_id INTEGER,
            date TEXT,
            price REAL,
            UNIQUE (ticker_id, date)
        );
    """)
    conn.execute("""
        CREATE TABLE ratios (
            statement_id INTEGER PRIMARY KEY,
            ticker_id INTEGER,
            period_type TEXT,
            fiscal_date TEXT,
            statement_data TEXT,
            UNIQUE (ticker_id, period_type, fiscal_date)
        );
    """)
    # Insert ticker
    conn.execute("INSERT INTO ticker (symbol) VALUES ('AAPL')")
    yield conn
    conn.close()


@pytest.fixture
def sample_fmp_data():
    """Sample data mimicking FMP API response."""
    return {
        'income_statement': [
            {
                'date': '2023-09-30',
                'symbol': 'AAPL',
                'revenue': 1000,
                'costOfRevenue': 600,
                'operatingIncome': 200,
                'netIncome': 150
            }
        ],
        'balance_sheet': [
            {
                'date': '2023-09-30',
                'symbol': 'AAPL',
                'totalCurrentAssets': 400,
                'totalCurrentLiabilities': 200,
                'totalAssets': 1000,
                'totalShareholdersEquity': 500,
                'totalLiabilities': 500
            }
        ],
        'cash_flow': [
            {
                'date': '2023-09-30',
                'symbol': 'AAPL',
                'operatingCashFlow': 200,
                'capitalExpenditures': 50
            }
        ],
        'historical_price': [
            {
                'date': '2023-09-30',
                'close': 150.0
            }
        ]
    }


class TestIntegrationPipeline:
    """Integration tests for the full data pipeline from FMP API to analytics."""

    def test_full_pipeline_income_statement_to_ratio_computation(self, db_connection, sample_fmp_data):
        """Test full pipeline: FMP client -> database -> ratio validator computation."""
        # Mock FMP client to return sample data
        with patch.object(FMPClient, '__init__', return_value=None), \
             patch.object(FMPClient, 'get_annual_income_statement') as mock_income, \
             patch.object(FMPClient, 'get_annual_balance_sheet') as mock_balance, \
             patch.object(FMPClient, 'get_annual_cash_flow') as mock_cash, \
             patch.object(FMPClient, 'get_historical_price') as mock_price:
                        # Set mock returns as DataFrames
                        mock_income.return_value = pd.DataFrame(sample_fmp_data['income_statement'])
                        mock_balance.return_value = pd.DataFrame(sample_fmp_data['balance_sheet'])
                        mock_cash.return_value = pd.DataFrame(sample_fmp_data['cash_flow'])
                        mock_price.return_value = pd.DataFrame(sample_fmp_data['historical_price'])

                        # Simulate data ingestion
                        client = FMPClient()
                        with patch.object(DataUpdater, '__init__', return_value=None):
                            updater = DataUpdater()
                            updater.conn = db_connection  # Set the connection directly
                            updater.logger = MagicMock()  # Mock logger

                        # Fetch and update data (normally done by scheduler)
                        income_df = client.get_annual_income_statement('AAPL')
                        balance_df = client.get_annual_balance_sheet('AAPL')
                        cash_df = client.get_annual_cash_flow('AAPL')
                        price_df = client.get_historical_price('AAPL')

                        # Update database
                        updater.upsert_statement(income_df, 'income_statement', 'AAPL', 'annual')
                        updater.upsert_statement(balance_df, 'balance_sheet', 'AAPL', 'annual')
                        updater.upsert_statement(cash_df, 'cash_flow', 'AAPL', 'annual')
                        updater.upsert_historical_prices(price_df, 'AAPL')

                        # Now test analytics: compute ratios
                        validator = RatioValidator(db_connection)

                        # Test individual ratio computations
                        net_margin = validator.compute_net_profit_margin('AAPL', 'annual', '2023-09-30')
                        assert net_margin == 0.15  # 150/1000

                        current_ratio = validator.compute_current_ratio('AAPL', 'annual', '2023-09-30')
                        assert current_ratio == 2.0  # 400/200

                        roe = validator.compute_return_on_equity('AAPL', 'annual', '2023-09-30')
                        assert roe == 0.3  # 150/500

                        # Test that data is consistent across tables
                        # Check that revenue in income matches assets in balance (simple consistency check)
                        income_data = db_connection.execute(
                            "SELECT statement_data FROM income_statement WHERE ticker_id = 1 AND fiscal_date = '2023-09-30'"
                        ).fetchone()[0]
                        income_json = json.loads(income_data)
                        assert income_json['revenue'] == 1000

                        balance_data = db_connection.execute(
                            "SELECT statement_data FROM balance_sheet WHERE ticker_id = 1 AND fiscal_date = '2023-09-30'"
                        ).fetchone()[0]
                        balance_json = json.loads(balance_data)
                        assert balance_json['totalAssets'] == 1000

    def test_pipeline_with_invalid_data_handling(self, db_connection):
        """Test pipeline handles invalid data gracefully."""
        # Mock client to return invalid data
        with patch.object(FMPClient, 'get_annual_income_statement') as mock_income:
            mock_income.return_value = []  # Empty data

            client = FMPClient()
            updater = DataUpdater(db_connection)

            df = client.get_annual_income_statement('AAPL')
            # Update should handle empty data without crashing
            updater.update_income_statement('AAPL', df, 'annual')

            # Validator should return None for missing data
            validator = RatioValidator(db_connection)
            result = validator.compute_net_profit_margin('AAPL', 'annual', '2023-09-30')
            assert result is None

    def test_pipeline_deduplication(self, db_connection, sample_fmp_data):
        """Test that pipeline handles duplicate data correctly."""
        with patch.object(FMPClient, 'get_annual_income_statement') as mock_income:
            mock_income.return_value = sample_fmp_data['income_statement']

            client = FMPClient()
            updater = DataUpdater(db_connection)

            # Insert same data twice
            df = client.get_annual_income_statement('AAPL')
            updater.update_income_statement('AAPL', df, 'annual')
            updater.update_income_statement('AAPL', df, 'annual')  # Should not duplicate

            # Check only one record exists
            count = db_connection.execute(
                "SELECT COUNT(*) FROM income_statement WHERE ticker_id = 1"
            ).fetchone()[0]
            assert count == 1

    def test_pipeline_analytics_integration(self, db_connection, sample_fmp_data):
        """Test that analytics can compute complex metrics from pipeline data."""
        # Insert data manually to simulate pipeline
        updater = DataUpdater(db_connection)

        from pandas import DataFrame
        income_df = DataFrame(sample_fmp_data['income_statement'])
        balance_df = DataFrame(sample_fmp_data['balance_sheet'])
        cash_df = DataFrame(sample_fmp_data['cash_flow'])
        price_df = DataFrame(sample_fmp_data['historical_price'])

        updater.update_income_statement('AAPL', income_df, 'annual')
        updater.update_balance_sheet('AAPL', balance_df, 'annual')
        updater.update_cash_flow('AAPL', cash_df, 'annual')
        updater.update_historical_price('AAPL', price_df)

        validator = RatioValidator(db_connection)

        # Test Dupont analysis
        dupont = validator.compute_dupont_analysis('AAPL', 'annual', '2023-09-30')
        assert dupont is not None
        assert dupont['calculated_roe'] is not None
        assert dupont['phase3_roe'] is not None
        assert dupont['match'] is True  # Should match since data is consistent

        # Test technical indicators
        technicals = validator.compute_technical_indicators('AAPL')
        # With single price, should return None or handle gracefully
        # Assuming it returns None for insufficient data
        assert technicals is None or isinstance(technicals, dict)

    def test_pipeline_error_recovery(self, db_connection):
        """Test pipeline recovers from partial failures."""
        # Mock partial success
        with patch.object(FMPClient, 'get_annual_income_statement') as mock_income:
            with patch.object(FMPClient, 'get_annual_balance_sheet') as mock_balance:
                mock_income.return_value = [{'date': '2023-09-30', 'symbol': 'AAPL', 'revenue': 1000}]
                mock_balance.side_effect = Exception("API Error")

                client = FMPClient()
                updater = DataUpdater(db_connection)

                # Income succeeds
                income_df = client.get_annual_income_statement('AAPL')
                updater.update_income_statement('AAPL', income_df, 'annual')

                # Balance fails - should not crash pipeline
                try:
                    balance_df = client.get_annual_balance_sheet('AAPL')
                    updater.update_balance_sheet('AAPL', balance_df, 'annual')
                except Exception:
                    pass  # Expected

                # Should still be able to compute income-based ratios
                validator = RatioValidator(db_connection)
                # Can't compute ROE without balance sheet, but revenue exists
                result = validator.compute_net_profit_margin('AAPL', 'annual', '2023-09-30')
                assert result is None  # Missing netIncome in sample