#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt

import logging
import argparse
import os

# File paths for the CSV files (set dynamically)
BALANCE_SHEET_FILE = None
INCOME_STATEMENT_FILE = None
CASH_FLOW_FILE = None


def load_and_preprocess_dataframes():
    """
    Load and preprocess the dataframes from the defined CSV file paths.
    Converts 'date' column to datetime, sorts by date, and selects necessary columns.
    Handles data type issues and ensures dataframes are ready for merging.
    """
    # Load income statement
    try:
        df_income = pd.read_csv(INCOME_STATEMENT_FILE)
        df_income['date'] = pd.to_datetime(df_income['date'])
        df_income = df_income.sort_values('date')
        df_income = df_income[['date', 'revenue', 'netIncome']]
        # Ensure numeric types
        df_income['revenue'] = pd.to_numeric(df_income['revenue'], errors='coerce')
        df_income['netIncome'] = pd.to_numeric(df_income['netIncome'], errors='coerce')
        logging.info("Successfully loaded and preprocessed income statement")
    except Exception as e:
        logging.error("Error loading income statement: %s", e)
        df_income = pd.DataFrame(columns=['date', 'revenue', 'netIncome'])

    # Load cash flow statement
    try:
        df_cash_flow = pd.read_csv(CASH_FLOW_FILE)
        df_cash_flow['date'] = pd.to_datetime(df_cash_flow['date'])
        df_cash_flow = df_cash_flow.sort_values('date')
        df_cash_flow = df_cash_flow[['date', 'freeCashFlow']]
        # Ensure numeric type
        df_cash_flow['freeCashFlow'] = pd.to_numeric(df_cash_flow['freeCashFlow'], errors='coerce')
        logging.info("Successfully loaded and preprocessed cash flow statement")
    except Exception as e:
        logging.error("Error loading cash flow statement: %s", e)
        df_cash_flow = pd.DataFrame(columns=['date', 'freeCashFlow'])

    # Load balance sheet (only keep 'date' for merging)
    try:
        df_balance = pd.read_csv(BALANCE_SHEET_FILE)
        df_balance['date'] = pd.to_datetime(df_balance['date'])
        df_balance = df_balance.sort_values('date')
        df_balance = df_balance[['date']]
        logging.info("Successfully loaded and preprocessed balance sheet")
    except Exception as e:
        logging.error("Error loading balance sheet: %s", e)
        df_balance = pd.DataFrame(columns=['date'])

    return {
        'income_statement': df_income,
        'cash_flow_statement': df_cash_flow,
        'balance_sheet': df_balance
    }


def merge_dataframes(dataframes):
    """
    Merge the preprocessed dataframes on the 'date' column using outer joins.
    Starts with income statement, merges cash flow, and optionally balance sheet for date alignment.
    Returns a dataframe with 'date', 'revenue', 'netIncome', and 'freeCashFlow' columns.
    """
    # Start with income statement
    merged_df = dataframes['income_statement']

    # Merge cash flow statement on 'date' with outer join
    merged_df = pd.merge(merged_df, dataframes['cash_flow_statement'], on='date', how='outer')

    # Optionally merge balance sheet for date alignment (only 'date' column)
    merged_df = pd.merge(merged_df, dataframes['balance_sheet'], on='date', how='outer')

    # Ensure the resulting dataframe contains the required columns
    merged_df = merged_df[['date', 'revenue', 'netIncome', 'freeCashFlow']]

    return merged_df


def plot_time_series(merged_df):
    """
    Create a combined time series line chart for revenue, net income, and free cash flow.
    Uses secondary y-axis for revenue, primary for net income and free cash flow.
    Plots all metrics over 'date', saves as 'combined_time_series.png' with professional styling.
    Handles missing values by skipping them (matplotlib's plot skips NaN by default).
    """
    try:
        plt.style.use('seaborn-v0_8')  # Professional style
    except:
        logging.warning("Seaborn style not available, using default style")

    fig, ax1 = plt.subplots(figsize=(12, 8))

    # Primary axis for netIncome and freeCashFlow
    ax1.plot(merged_df['date'], merged_df['netIncome'], marker='o', linestyle='-', color='blue', label='Net Income')
    ax1.plot(merged_df['date'], merged_df['freeCashFlow'], marker='s', linestyle='-', color='green', label='Free Cash Flow')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Net Income / Free Cash Flow')
    ax1.grid(True)

    # Secondary axis for revenue
    ax2 = ax1.twinx()
    ax2.plot(merged_df['date'], merged_df['revenue'], marker='^', linestyle='-', color='red', label='Revenue')
    ax2.set_ylabel('Revenue')

    # Legend combining both axes
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    plt.title('Combined Time Series: Revenue, Net Income, and Free Cash Flow')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'{ticker}_combined_time_series.png'))
    plt.close()
    logging.info("Successfully created combined time series plot")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Plot time series for financial data.")
    parser.add_argument('--ticker', default='CSCO', help='Ticker symbol for the company (default: CSCO)')
    parser.add_argument('-q', '--quarterly', action='store_true', help='Use quarterly data instead of annual')
    parser.add_argument('-d', '--output-dir', default='data/', help='Output directory for files (default: data/)')
    args = parser.parse_args()
    ticker = args.ticker.upper()
    period = 'quarterly' if args.quarterly else 'annual'
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    logging.basicConfig(
        filename=os.path.join(output_dir, 'time_series_plot.log'),
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filemode='w'
    )
    
    # Set file paths dynamically
    globals()['BALANCE_SHEET_FILE'] = os.path.join(output_dir, f"{ticker}_balance_sheet_{period}.csv")
    globals()['INCOME_STATEMENT_FILE'] = os.path.join(output_dir, f"{ticker}_income_statement_{period}.csv")
    globals()['CASH_FLOW_FILE'] = os.path.join(output_dir, f"{ticker}_cash_flow_statement_{period}.csv")
    
    print("Starting time series plotting script.")
    dataframes = load_and_preprocess_dataframes()
    try:
        merged_df = merge_dataframes(dataframes)
        logging.info("Dataframes merged successfully")
        print("Data merged successfully.")
        merged_df.to_csv(os.path.join(output_dir, f"{ticker}_combined_time_series.csv"), index=False)
        logging.info("Successfully exported merged dataframe to combined_time_series.csv")
        plot_time_series(merged_df)
    except Exception as e:
        logging.error("Error in merging or plotting: %s", e)
        print("Error in processing data.")
    print("Script execution completed.")