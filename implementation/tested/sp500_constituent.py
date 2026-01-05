import requests
import pandas as pd
import json
import subprocess
import time

def get_sp500_constituents(api_key: str) -> pd.DataFrame:
    """
    Fetches S&P 500 constituents from Financial Modeling Prep API and returns a pandas DataFrame.

    Args:
        api_key (str): Your API key for Financial Modeling Prep.

    Returns:
        pd.DataFrame: DataFrame containing S&P 500 constituents.
    """
    url = f"https://financialmodelingprep.com/api/v3/sp500_constituent?apikey={api_key}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return pd.DataFrame(data)

def process_tickers_with_subprocess(ticker_list):
    """
    Iteratively runs 'python fmp_fetcher.py --ticker <ticker> --output ./output --period annual'
    for each ticker in ticker_list. Appends tickers to 'processed.txt' on success,
    or to 'processed_failed.txt' on failure.
    """
    for ticker in ticker_list:
        time.sleep(5)
        cmd = [
            "python", "./implementation/tested/fmp_fetcher.py",
            "--ticker", ticker,
            "--output", "./output",
            "--period", "annual"
        ]
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            with open("processed.txt", "a") as f:
                f.write(f"{ticker}\n")
        except subprocess.CalledProcessError:
            with open("processed_failed.txt", "a") as f:
                f.write(f"{ticker}\n")

# Only run this if the script is executed directly
if __name__ == "__main__":
    df = get_sp500_constituents('927d9dc4b031112483b155d52401c4a2')
    df.to_csv("ticker_list.txt", index=False)
    process_tickers_with_subprocess(df['symbol'].tolist())
    print(df.head())