#!/usr/bin/env python3
"""
CLI script to fetch financial-statement-full-as-reported data for a given ticker.
Usage: python script.py -t TICKER [-d DESTINATION]
"""

import argparse
import os
import csv
import requests
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd
import json

def fetch_data(url):
    """
    Fetches data from the given URL.
    """
    print(f"Fetching data from: {url}")
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API request failed with status code {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def save_to_csv(data, filename, output_dir):
    """
    Saves the provided data to a CSV file in the specified output directory.
    Sorts data by date ascending (oldest first) if 'date' key exists.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        print(f"Error creating output directory '{output_dir}': {e}")
        return
    def data_to_dataframe(data):
        """
        Converts a list of dictionaries to a pandas DataFrame.
        Each dictionary becomes a row in the DataFrame.
        """
        if not isinstance(data, list):
            raise ValueError("Input data must be a list of dictionaries.")
        if not all(isinstance(d, dict) for d in data):
            raise ValueError("All elements of data must be dictionaries.")
        return pd.DataFrame(data)
    df=data_to_dataframe(data)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.sort_values(by='date', ascending=True)
    df.to_csv(os.path.join(output_dir, filename), index=False)    
    

def main():
    parser = argparse.ArgumentParser(description="Fetch financial-statement-full-as-reported data and save to CSV.")
    parser.add_argument("-t", "--ticker", required=True, help="Stock ticker symbol")
    parser.add_argument("-d", "--destination", default="data", help="Output destination directory (default: data)")

    args = parser.parse_args()

    # Load environment variables
    load_dotenv()
    api_key = os.environ.get('FMP_API_KEY')
    if not api_key:
        print("Error: FMP_API_KEY not found in .env file")
        return

    # Construct URL
    url = f"https://financialmodelingprep.com/api/v3/financial-statement-full-as-reported/{args.ticker}?period=quarter&apikey={api_key}"

    # Fetch data
    data = fetch_data(url)
    if data is None:
        print("Failed to fetch data")
        return



    # Save to CSV
    filename = f"{args.ticker}_financial_statement_full_as_reported"
    save_to_csv(data, filename, args.destination)

if __name__ == "__main__":
    main()
