import os
import sys
import logging
import pandas as pd
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ingestion.data_updater import DataUpdater
from domain.repositories.financial_data_repository import FinancialDataRepository
from domain.services.data_ingestion_service import DataIngestionService
from core.validation import ValidationError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class TestRepositoryValidation(unittest.TestCase):
    """Test cases for repository validation errors."""

    def setUp(self):
        self.mock_config = {
            "database": {
                "type": "sqlite",
                "path": ":memory:"
            }
        }
        self.mock_repo = MagicMock(spec=FinancialDataRepository)
        self.service = DataIngestionService(self.mock_config, self.mock_repo)

    def test_ingest_statement_invalid_data_type(self):
        """Test ingest_statement with invalid data type."""
        # Mock invalid data that should cause validation error
        invalid_data = {
            "date": "2023-01-01",
            "symbol": "AAPL",
            "totalAssets": "not_a_number"  # Should be numeric
        }
        df = pd.DataFrame([invalid_data])

        with patch.object(self.service, '_validate_financial_data', side_effect=ValidationError("Invalid data")):
            with self.assertRaises(ValidationError):
                self.service.ingest_statement(df, "balance_sheet", "AAPL", "annual")

    def test_ingest_statement_missing_required_fields(self):
        """Test ingest_statement with missing required fields."""
        # Data missing required fields
        invalid_data = {
            "symbol": "AAPL",
            "totalAssets": 1000.0
            # Missing date
        }
        df = pd.DataFrame([invalid_data])

        with patch.object(self.service, '_validate_financial_data', side_effect=ValidationError("Missing required fields")):
            with self.assertRaises(ValidationError):
                self.service.ingest_statement(df, "balance_sheet", "AAPL", "annual")

    def test_ingest_ratios_invalid_ratio_value(self):
        """Test ingest_ratios with invalid ratio value."""
        invalid_data = {
            "date": "2023-01-01",
            "symbol": "AAPL",
            "peRatio": -5.0  # Invalid negative P/E ratio
        }
        df = pd.DataFrame([invalid_data])

        with patch.object(self.service, '_validate_ratio_data', side_effect=ValidationError("Invalid ratio value")):
            with self.assertRaises(ValidationError):
                self.service.ingest_ratios(df, "AAPL", "annual")

    def test_ingest_historical_prices_invalid_date(self):
        """Test ingest_historical_prices with invalid date format."""
        invalid_data = {
            "date": "2023/01/01",  # Invalid format
            "open": 100.0,
            "close": 101.0
        }
        df = pd.DataFrame([invalid_data])

        with patch.object(self.service, '_validate_price_data', side_effect=ValidationError("Invalid date format")):
            with self.assertRaises(ValidationError):
                self.service.ingest_historical_prices(df, "AAPL")

    def test_ingest_historical_prices_negative_price(self):
        """Test ingest_historical_prices with negative price."""
        invalid_data = {
            "date": "2023-01-01",
            "open": -100.0,  # Invalid negative price
            "close": 101.0
        }
        df = pd.DataFrame([invalid_data])

        with patch.object(self.service, '_validate_price_data', side_effect=ValidationError("Negative price")):
            with self.assertRaises(ValidationError):
                self.service.ingest_historical_prices(df, "AAPL")

    def test_repository_save_statement_validation_error(self):
        """Test repository save_statement with validation error."""
        self.mock_repo.save_statement.side_effect = ValidationError("Repository validation failed")

        valid_data = {
            "date": "2023-01-01",
            "symbol": "AAPL",
            "totalAssets": 1000.0
        }
        df = pd.DataFrame([valid_data])

        with self.assertRaises(ValidationError):
            self.service.ingest_statement(df, "balance_sheet", "AAPL", "annual")

def main():
    """
    Test inserting CSV data into SQLite database for AAPL.
    """
    ticker = 'AAPL'
    db_path = f"database/{ticker}_sqlite.db"
    csv_dir = 'data/raw/csv'

    logging.info(f"Starting data insertion for {ticker}")

    # Check if DB exists
    if not os.path.exists(db_path):
        logging.error(f"Database {db_path} does not exist. Run database_setup.py first.")
        return

    updater = DataUpdater(db_path)

    try:
        # Insert statements
        statements = [
            ('income_statement_annual', 'annual'),
            ('income_statement_quarterly', 'quarterly'),
            ('balance_sheet_annual', 'annual'),
            ('balance_sheet_quarterly', 'quarterly'),
            ('cash_flow_annual', 'annual'),
            ('cash_flow_quarterly', 'quarterly')
        ]

        for csv_suffix, period in statements:
            csv_file = f"{ticker}_{csv_suffix}.csv"
            csv_path = os.path.join(csv_dir, csv_file)
            if not os.path.exists(csv_path):
                logging.warning(f"CSV file {csv_file} not found, skipping.")
                continue

            logging.info(f"Loading and inserting {csv_file}")
            df = pd.read_csv(csv_path)
            if 'income' in csv_suffix:
                table = 'income_statement'
            elif 'balance' in csv_suffix:
                table = 'balance_sheet'
            elif 'cash' in csv_suffix:
                table = 'cash_flow'
            else:
                continue
            records_added, records_skipped = updater.upsert_statement(df, table, ticker, period)
            logging.info(f"Inserted {records_added} records, skipped {records_skipped} for {table}")
            updater.log_update(updater.get_ticker_id(ticker), table, records_added, records_skipped)

        # Insert ratios
        ratios = [
            ('ratios_annual', 'financial_ratio_reported', 'annual'),
            ('ratios_quarterly', 'financial_ratio_reported', 'quarterly')
        ]

        for csv_suffix, table, period in ratios:
            csv_file = f"{ticker}_{csv_suffix}.csv"
            csv_path = os.path.join(csv_dir, csv_file)
            if not os.path.exists(csv_path):
                logging.warning(f"CSV file {csv_file} not found, skipping.")
                continue

            logging.info(f"Loading and inserting {csv_file}")
            df = pd.read_csv(csv_path)
            records_added, records_skipped = updater.upsert_ratios(df, table, ticker, period)
            logging.info(f"Inserted {records_added} records, skipped {records_skipped} for {table}")
            updater.log_update(updater.get_ticker_id(ticker), table, records_added, records_skipped)

        # Insert historical prices
        csv_file = f"{ticker}_historical_price.csv"
        csv_path = os.path.join(csv_dir, csv_file)
        if os.path.exists(csv_path):
            logging.info(f"Loading and inserting {csv_file}")
            df = pd.read_csv(csv_path)
            records_added, records_skipped = updater.upsert_historical_prices(df, ticker)
            logging.info(f"Inserted {records_added} records, skipped {records_skipped} for historical_price")
            updater.log_update(updater.get_ticker_id(ticker), 'historical_price', records_added, records_skipped)
        else:
            logging.warning(f"CSV file {csv_file} not found, skipping.")

    finally:
        updater.close()

    logging.info(f"Data insertion completed for {ticker}")

if __name__ == "__main__":
    # Run tests if called directly
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        unittest.main()
    else:
        main()