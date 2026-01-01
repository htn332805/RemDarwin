import os
import sys
import logging
from dotenv import load_dotenv
load_dotenv()
import pandas as pd

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ingestion.fmp_client import FMPClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    """
    Fetch all financial statements for AAPL and export to CSV files.
    Handles errors and logs the process.
    """
    ticker = 'AAPL'
    logging.info(f"Starting data fetch for {ticker}")

    try:
        # Instantiate FMPClient
        client = FMPClient()
        logging.info("FMPClient initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize FMPClient: {e}")
        return

    # Create directory if needed
    output_dir = 'data/raw/csv'
    os.makedirs(output_dir, exist_ok=True)
    logging.info(f"Output directory ensured: {output_dir}")

    # List of statements to fetch: (method_name, filename_suffix)
    statements = [
        ('get_annual_income_statement', 'income_statement_annual'),
        ('get_quarterly_income_statement', 'income_statement_quarterly'),
        ('get_annual_balance_sheet', 'balance_sheet_annual'),
        ('get_quarterly_balance_sheet', 'balance_sheet_quarterly'),
        ('get_annual_cash_flow', 'cash_flow_annual'),
        ('get_quarterly_cash_flow', 'cash_flow_quarterly')
    ]

    for method_name, suffix in statements:
        try:
            logging.info(f"Fetching {suffix} for {ticker}")
            method = getattr(client, method_name)
            df = method(ticker)
            filename = f"{ticker}_{suffix}.csv"
            filepath = os.path.join(output_dir, filename)
            df.to_csv(filepath, index=False)
            logging.info(f"Successfully saved {filename}")
        except Exception as e:
            logging.error(f"Failed to fetch and save {suffix} for {ticker}: {e}")

    logging.info(f"Data fetch process completed for {ticker}")

if __name__ == "__main__":
    main()