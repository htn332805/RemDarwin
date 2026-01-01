import os
from dotenv import load_dotenv
load_dotenv()
import pandas as pd
from ingestion.fmp_client import FMPClient

def main():
    # Instantiate FMPClient
    client = FMPClient()

    # Fetch annual income statement data for CSCO
    annual_df = client.get_annual_income_statement('CSCO')

    # Fetch quarterly income statement data for CSCO
    quarterly_df = client.get_quarterly_income_statement('CSCO')

    # Create data/raw/csv/ directory if needed
    os.makedirs('data/raw/csv', exist_ok=True)

    # Save annual data to CSV
    annual_df.to_csv('data/raw/csv/CSCO_income_statement_annual.csv', index=False)
    print("Annual income statement data saved to data/raw/csv/CSCO_income_statement_annual.csv")

    # Save quarterly data to CSV
    quarterly_df.to_csv('data/raw/csv/CSCO_income_statement_quarterly.csv', index=False)
    print("Quarterly income statement data saved to data/raw/csv/CSCO_income_statement_quarterly.csv")

if __name__ == "__main__":
    main()