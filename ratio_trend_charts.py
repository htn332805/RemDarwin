#!/usr/bin/env python3
"""
ratio_trend_charts.py

A command-line interface (CLI) tool for generating financial ratio trend charts.

This script calculates and visualizes liquidity, solvency, and profitability ratios
from financial statement CSV files (balance sheet, income statement, cash flow statement).
Charts can be rendered as line or bar charts and saved as PNG files.

Key Features:
- Calculates 11 financial ratios across 3 categories
- Supports both annual and quarterly financial data
- Generates professional-grade PNG chart outputs
- Flexible CLI with customizable input/output directories

Usage:
    python ratio_trend_charts.py -t CSCO                    # Basic usage (annual data)
    python ratio_trend_charts.py -t CSCO -q                 # Quarterly data
    python ratio_trend_charts.py -t CSCO -d ./my_data       # Custom directory
    python ratio_trend_charts.py -t CSCO -c bar             # Bar charts instead of line

Ratios Calculated:
    Liquidity:    Current Ratio, Quick Ratio, Cash Ratio
    Solvency:     Debt-to-Equity, Debt-to-Assets, Interest Coverage
    Profitability: ROE, ROA, Gross Margin, Operating Margin, Net Margin

Author: MyCFATool Project
Date: 2026-01-02
"""

# Standard library imports
import argparse
import os
import sys
from pathlib import Path

# Third-party imports
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

# =============================================================================
# CONSTANTS
# =============================================================================

# Default values
DEFAULT_DIRECTORY = "data"
DEFAULT_CHART_TYPE = "line"
DEFAULT_PERIOD = "annual"

# Chart styling
CHART_STYLE = {
    'figure_size': (12, 6),
    'dpi': 150,
    'grid_alpha': 0.3,
    'line_width': 2,
    'marker_size': 6,
    'legend_loc': 'upper left',
    'title_fontsize': 14,
    'label_fontsize': 12,
    'tick_fontsize': 10
}

# Color palettes for each category
COLORS = {
    'liquidity': ['#2196F3', '#4CAF50', '#FF9800'],  # Blue, Green, Orange
    'solvency': ['#9C27B0', '#E91E63', '#00BCD4'],   # Purple, Pink, Cyan
    'profitability': ['#F44336', '#3F51B5', '#8BC34A', '#FF5722', '#607D8B']  # Red, Indigo, Light Green, Deep Orange, Blue Grey
}

# Ratio definitions
LIQUIDITY_RATIOS = ['Current Ratio', 'Quick Ratio', 'Cash Ratio']
SOLVENCY_RATIOS = ['Debt-to-Equity', 'Debt-to-Assets', 'Interest Coverage']
PROFITABILITY_RATIOS = ['ROE (%)', 'ROA (%)', 'Gross Margin (%)', 'Operating Margin (%)', 'Net Margin (%)']


# =============================================================================
# CLI ARGUMENT PARSER
# =============================================================================

def create_argument_parser():
    """
    Create and configure the argument parser for the CLI.
    
    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        prog='ratio_trend_charts.py',
        description='Generate financial ratio trend charts from CSV financial statements.',
        epilog='''
Examples:
  python ratio_trend_charts.py -t CSCO                    # Annual data from ./data/
  python ratio_trend_charts.py -t CSCO -q                 # Quarterly data
  python ratio_trend_charts.py -t AAPL -d ./financials    # Custom directory
  python ratio_trend_charts.py -t MSFT -c bar -q          # Bar charts, quarterly
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '-t', '--ticker',
        type=str,
        required=True,
        help='Stock ticker symbol (e.g., CSCO, AAPL, MSFT)'
    )
    
    parser.add_argument(
        '-d', '--directory',
        type=str,
        default=DEFAULT_DIRECTORY,
        help=f'Input/output directory for CSV files and charts (default: {DEFAULT_DIRECTORY})'
    )
    
    parser.add_argument(
        '-q', '--quarterly',
        action='store_true',
        help='Use quarterly data instead of annual (default: annual)'
    )
    
    parser.add_argument(
        '-c', '--chart-type',
        type=str,
        choices=['line', 'bar'],
        default=DEFAULT_CHART_TYPE,
        help=f'Chart type: line or bar (default: {DEFAULT_CHART_TYPE})'
    )
    
    return parser


def parse_arguments(args=None):
    """
    Parse command-line arguments.
    
    Args:
        args: Optional list of arguments (for testing). If None, uses sys.argv.
        
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = create_argument_parser()
    return parser.parse_args(args)


# =============================================================================
# DATA LOADING
# =============================================================================

def build_file_paths(ticker, directory, period):
    """
    Build file paths for the three financial statement CSV files.
    
    Args:
        ticker: Stock ticker symbol
        directory: Base directory for CSV files
        period: 'annual' or 'quarterly'
        
    Returns:
        dict: Dictionary with keys 'balance_sheet', 'income_statement', 'cash_flow'
              and values as Path objects
    """
    base_path = Path(directory)
    
    return {
        'balance_sheet': base_path / f'{ticker}_balance_sheet_{period}.csv',
        'income_statement': base_path / f'{ticker}_income_statement_{period}.csv',
        'cash_flow': base_path / f'{ticker}_cash_flow_statement_{period}.csv'
    }


def load_csv(file_path):
    """
    Load a CSV file into a pandas DataFrame.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        pd.DataFrame: Loaded data
        
    Raises:
        FileNotFoundError: If the file does not exist
        pd.errors.EmptyDataError: If the file is empty
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    
    if df.empty:
        raise ValueError(f"CSV file is empty: {file_path}")
    
    return df


def load_financial_data(ticker, directory, period):
    """
    Load all three financial statement CSV files.
    
    Args:
        ticker: Stock ticker symbol
        directory: Base directory for CSV files
        period: 'annual' or 'quarterly'
        
    Returns:
        dict: Dictionary with DataFrames for each statement type
    """
    file_paths = build_file_paths(ticker, directory, period)
    
    data = {}
    for statement_type, path in file_paths.items():
        try:
            df = load_csv(path)
            # Parse date column and sort by date ascending
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date', ascending=True).reset_index(drop=True)
            data[statement_type] = df
            print(f"  Loaded {statement_type}: {len(df)} records from {path}")
        except FileNotFoundError as e:
            print(f"  Warning: {e}")
            data[statement_type] = pd.DataFrame()
        except Exception as e:
            print(f"  Error loading {statement_type}: {e}")
            data[statement_type] = pd.DataFrame()
    
    return data


def get_column_value(df, column_name, default=np.nan):
    """
    Safely get a column from a DataFrame, returning default if not found.
    
    Args:
        df: pandas DataFrame
        column_name: Name of the column to retrieve
        default: Default value if column not found
        
    Returns:
        pd.Series or default value
    """
    if column_name in df.columns:
        return df[column_name]
    return pd.Series([default] * len(df), index=df.index)


# =============================================================================
# LIQUIDITY RATIO CALCULATIONS
# =============================================================================

def calculate_current_ratio(balance_sheet):
    """
    Calculate Current Ratio = Current Assets / Current Liabilities
    
    Args:
        balance_sheet: DataFrame with balance sheet data
        
    Returns:
        pd.Series: Current ratio values
    """
    current_assets = get_column_value(balance_sheet, 'totalCurrentAssets')
    current_liabilities = get_column_value(balance_sheet, 'totalCurrentLiabilities')
    
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio = current_assets / current_liabilities
        ratio = ratio.replace([np.inf, -np.inf], np.nan)
    
    return ratio


def calculate_quick_ratio(balance_sheet):
    """
    Calculate Quick Ratio = (Current Assets - Inventory) / Current Liabilities
    
    Args:
        balance_sheet: DataFrame with balance sheet data
        
    Returns:
        pd.Series: Quick ratio values
    """
    current_assets = get_column_value(balance_sheet, 'totalCurrentAssets')
    inventory = get_column_value(balance_sheet, 'inventory', default=0)
    current_liabilities = get_column_value(balance_sheet, 'totalCurrentLiabilities')
    
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio = (current_assets - inventory) / current_liabilities
        ratio = ratio.replace([np.inf, -np.inf], np.nan)
    
    return ratio


def calculate_cash_ratio(balance_sheet):
    """
    Calculate Cash Ratio = Cash & Equivalents / Current Liabilities
    
    Args:
        balance_sheet: DataFrame with balance sheet data
        
    Returns:
        pd.Series: Cash ratio values
    """
    cash = get_column_value(balance_sheet, 'cashAndCashEquivalents')
    current_liabilities = get_column_value(balance_sheet, 'totalCurrentLiabilities')
    
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio = cash / current_liabilities
        ratio = ratio.replace([np.inf, -np.inf], np.nan)
    
    return ratio


def calculate_liquidity_ratios(balance_sheet):
    """
    Calculate all liquidity ratios.
    
    Args:
        balance_sheet: DataFrame with balance sheet data
        
    Returns:
        pd.DataFrame: DataFrame with date and all liquidity ratios
    """
    if balance_sheet.empty:
        return pd.DataFrame()
    
    result = pd.DataFrame()
    
    if 'date' in balance_sheet.columns:
        result['date'] = balance_sheet['date']
    
    result['Current Ratio'] = calculate_current_ratio(balance_sheet)
    result['Quick Ratio'] = calculate_quick_ratio(balance_sheet)
    result['Cash Ratio'] = calculate_cash_ratio(balance_sheet)
    
    return result


# =============================================================================
# SOLVENCY RATIO CALCULATIONS
# =============================================================================

def calculate_debt_to_equity(balance_sheet):
    """
    Calculate Debt-to-Equity Ratio = Total Debt / Total Stockholders' Equity
    
    Args:
        balance_sheet: DataFrame with balance sheet data
        
    Returns:
        pd.Series: Debt-to-equity ratio values
    """
    total_debt = get_column_value(balance_sheet, 'totalDebt')
    total_equity = get_column_value(balance_sheet, 'totalStockholdersEquity')
    
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio = total_debt / total_equity
        ratio = ratio.replace([np.inf, -np.inf], np.nan)
    
    return ratio


def calculate_debt_to_assets(balance_sheet):
    """
    Calculate Debt-to-Assets Ratio = Total Debt / Total Assets
    
    Args:
        balance_sheet: DataFrame with balance sheet data
        
    Returns:
        pd.Series: Debt-to-assets ratio values
    """
    total_debt = get_column_value(balance_sheet, 'totalDebt')
    total_assets = get_column_value(balance_sheet, 'totalAssets')
    
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio = total_debt / total_assets
        ratio = ratio.replace([np.inf, -np.inf], np.nan)
    
    return ratio


def calculate_interest_coverage(income_statement):
    """
    Calculate Interest Coverage Ratio = Operating Income (EBIT) / Interest Expense
    
    Args:
        income_statement: DataFrame with income statement data
        
    Returns:
        pd.Series: Interest coverage ratio values
    """
    operating_income = get_column_value(income_statement, 'operatingIncome')
    interest_expense = get_column_value(income_statement, 'interestExpense')
    
    # Interest expense is often reported as negative, take absolute value
    interest_expense = interest_expense.abs()
    
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio = operating_income / interest_expense
        ratio = ratio.replace([np.inf, -np.inf], np.nan)
    
    return ratio


def calculate_solvency_ratios(balance_sheet, income_statement):
    """
    Calculate all solvency ratios.
    
    Args:
        balance_sheet: DataFrame with balance sheet data
        income_statement: DataFrame with income statement data
        
    Returns:
        pd.DataFrame: DataFrame with date and all solvency ratios
    """
    if balance_sheet.empty:
        return pd.DataFrame()
    
    result = pd.DataFrame()
    
    if 'date' in balance_sheet.columns:
        result['date'] = balance_sheet['date']
    
    result['Debt-to-Equity'] = calculate_debt_to_equity(balance_sheet)
    result['Debt-to-Assets'] = calculate_debt_to_assets(balance_sheet)
    
    # Interest coverage requires income statement data
    if not income_statement.empty and len(income_statement) == len(balance_sheet):
        result['Interest Coverage'] = calculate_interest_coverage(income_statement)
    else:
        result['Interest Coverage'] = np.nan
    
    return result


# =============================================================================
# PROFITABILITY RATIO CALCULATIONS
# =============================================================================

def calculate_roe(income_statement, balance_sheet):
    """
    Calculate Return on Equity (ROE) = Net Income / Shareholders' Equity
    
    Args:
        income_statement: DataFrame with income statement data
        balance_sheet: DataFrame with balance sheet data
        
    Returns:
        pd.Series: ROE values (as percentage)
    """
    net_income = get_column_value(income_statement, 'netIncome')
    total_equity = get_column_value(balance_sheet, 'totalStockholdersEquity')
    
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio = (net_income / total_equity) * 100
        ratio = ratio.replace([np.inf, -np.inf], np.nan)
    
    return ratio


def calculate_roa(income_statement, balance_sheet):
    """
    Calculate Return on Assets (ROA) = Net Income / Total Assets
    
    Args:
        income_statement: DataFrame with income statement data
        balance_sheet: DataFrame with balance sheet data
        
    Returns:
        pd.Series: ROA values (as percentage)
    """
    net_income = get_column_value(income_statement, 'netIncome')
    total_assets = get_column_value(balance_sheet, 'totalAssets')
    
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio = (net_income / total_assets) * 100
        ratio = ratio.replace([np.inf, -np.inf], np.nan)
    
    return ratio


def calculate_gross_margin(income_statement):
    """
    Calculate Gross Margin = Gross Profit / Revenue
    
    Args:
        income_statement: DataFrame with income statement data
        
    Returns:
        pd.Series: Gross margin values (as percentage)
    """
    gross_profit = get_column_value(income_statement, 'grossProfit')
    revenue = get_column_value(income_statement, 'revenue')
    
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio = (gross_profit / revenue) * 100
        ratio = ratio.replace([np.inf, -np.inf], np.nan)
    
    return ratio


def calculate_operating_margin(income_statement):
    """
    Calculate Operating Margin = Operating Income / Revenue
    
    Args:
        income_statement: DataFrame with income statement data
        
    Returns:
        pd.Series: Operating margin values (as percentage)
    """
    operating_income = get_column_value(income_statement, 'operatingIncome')
    revenue = get_column_value(income_statement, 'revenue')
    
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio = (operating_income / revenue) * 100
        ratio = ratio.replace([np.inf, -np.inf], np.nan)
    
    return ratio


def calculate_net_margin(income_statement):
    """
    Calculate Net Margin = Net Income / Revenue
    
    Args:
        income_statement: DataFrame with income statement data
        
    Returns:
        pd.Series: Net margin values (as percentage)
    """
    net_income = get_column_value(income_statement, 'netIncome')
    revenue = get_column_value(income_statement, 'revenue')
    
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio = (net_income / revenue) * 100
        ratio = ratio.replace([np.inf, -np.inf], np.nan)
    
    return ratio


def calculate_profitability_ratios(income_statement, balance_sheet):
    """
    Calculate all profitability ratios.
    
    Args:
        income_statement: DataFrame with income statement data
        balance_sheet: DataFrame with balance sheet data
        
    Returns:
        pd.DataFrame: DataFrame with date and all profitability ratios
    """
    if income_statement.empty:
        return pd.DataFrame()
    
    result = pd.DataFrame()
    
    if 'date' in income_statement.columns:
        result['date'] = income_statement['date']
    
    # Ratios requiring both income statement and balance sheet
    if not balance_sheet.empty and len(balance_sheet) == len(income_statement):
        result['ROE (%)'] = calculate_roe(income_statement, balance_sheet)
        result['ROA (%)'] = calculate_roa(income_statement, balance_sheet)
    else:
        result['ROE (%)'] = np.nan
        result['ROA (%)'] = np.nan
    
    # Ratios from income statement only
    result['Gross Margin (%)'] = calculate_gross_margin(income_statement)
    result['Operating Margin (%)'] = calculate_operating_margin(income_statement)
    result['Net Margin (%)'] = calculate_net_margin(income_statement)
    
    return result


# =============================================================================
# CHART GENERATION
# =============================================================================

def setup_chart_style():
    """
    Configure matplotlib style for professional-looking charts.
    """
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams['figure.facecolor'] = 'white'
    plt.rcParams['axes.facecolor'] = 'white'
    plt.rcParams['axes.edgecolor'] = '#333333'
    plt.rcParams['axes.labelcolor'] = '#333333'
    plt.rcParams['text.color'] = '#333333'
    plt.rcParams['xtick.color'] = '#333333'
    plt.rcParams['ytick.color'] = '#333333'


def format_date_labels(ax, dates, period):
    """
    Format x-axis date labels based on the data period.
    
    Args:
        ax: Matplotlib axes object
        dates: Series of date values
        period: 'annual' or 'quarterly'
    """
    if period == 'annual':
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    else:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-Q%q'))
    
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')


def generate_line_chart(df, ratio_columns, title, colors, output_path, period):
    """
    Generate a line chart with multiple series.
    
    Args:
        df: DataFrame with date and ratio columns
        ratio_columns: List of column names to plot
        title: Chart title
        colors: List of colors for each line
        output_path: Path to save the PNG file
        period: 'annual' or 'quarterly' (for date formatting)
    """
    setup_chart_style()
    
    fig, ax = plt.subplots(figsize=CHART_STYLE['figure_size'])
    
    if 'date' not in df.columns or df.empty:
        ax.text(0.5, 0.5, 'No data available', ha='center', va='center',
                transform=ax.transAxes, fontsize=14)
        plt.title(title, fontsize=CHART_STYLE['title_fontsize'], fontweight='bold')
        plt.tight_layout()
        plt.savefig(output_path, dpi=CHART_STYLE['dpi'], bbox_inches='tight')
        plt.close()
        return
    
    dates = df['date']
    
    for i, col in enumerate(ratio_columns):
        if col in df.columns:
            color = colors[i % len(colors)]
            ax.plot(dates, df[col], 
                   label=col,
                   color=color,
                   linewidth=CHART_STYLE['line_width'],
                   marker='o',
                   markersize=CHART_STYLE['marker_size'])
    
    ax.set_xlabel('Date', fontsize=CHART_STYLE['label_fontsize'])
    ax.set_ylabel('Ratio Value', fontsize=CHART_STYLE['label_fontsize'])
    ax.set_title(title, fontsize=CHART_STYLE['title_fontsize'], fontweight='bold')
    
    ax.legend(loc=CHART_STYLE['legend_loc'], framealpha=0.9)
    ax.grid(True, alpha=CHART_STYLE['grid_alpha'])
    ax.tick_params(axis='both', labelsize=CHART_STYLE['tick_fontsize'])
    
    # Format x-axis dates
    format_date_labels(ax, dates, period)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=CHART_STYLE['dpi'], bbox_inches='tight')
    plt.close()
    
    print(f"  Saved: {output_path}")


def generate_bar_chart(df, ratio_columns, title, colors, output_path, period):
    """
    Generate a grouped bar chart with multiple series.
    
    Args:
        df: DataFrame with date and ratio columns
        ratio_columns: List of column names to plot
        title: Chart title
        colors: List of colors for each bar group
        output_path: Path to save the PNG file
        period: 'annual' or 'quarterly' (for date formatting)
    """
    setup_chart_style()
    
    fig, ax = plt.subplots(figsize=CHART_STYLE['figure_size'])
    
    if 'date' not in df.columns or df.empty:
        ax.text(0.5, 0.5, 'No data available', ha='center', va='center',
                transform=ax.transAxes, fontsize=14)
        plt.title(title, fontsize=CHART_STYLE['title_fontsize'], fontweight='bold')
        plt.tight_layout()
        plt.savefig(output_path, dpi=CHART_STYLE['dpi'], bbox_inches='tight')
        plt.close()
        return
    
    # Prepare data for grouped bars
    valid_columns = [col for col in ratio_columns if col in df.columns]
    n_groups = len(df)
    n_bars = len(valid_columns)
    
    if n_bars == 0:
        ax.text(0.5, 0.5, 'No data available', ha='center', va='center',
                transform=ax.transAxes, fontsize=14)
        plt.title(title, fontsize=CHART_STYLE['title_fontsize'], fontweight='bold')
        plt.tight_layout()
        plt.savefig(output_path, dpi=CHART_STYLE['dpi'], bbox_inches='tight')
        plt.close()
        return
    
    bar_width = 0.8 / n_bars
    x = np.arange(n_groups)
    
    for i, col in enumerate(valid_columns):
        offset = (i - n_bars/2 + 0.5) * bar_width
        color = colors[i % len(colors)]
        ax.bar(x + offset, df[col], bar_width, label=col, color=color)
    
    ax.set_xlabel('Date', fontsize=CHART_STYLE['label_fontsize'])
    ax.set_ylabel('Ratio Value', fontsize=CHART_STYLE['label_fontsize'])
    ax.set_title(title, fontsize=CHART_STYLE['title_fontsize'], fontweight='bold')
    
    # Format x-axis with dates
    if period == 'annual':
        date_labels = df['date'].dt.strftime('%Y').tolist()
    else:
        date_labels = df['date'].dt.strftime('%Y-Q%q').tolist()
    
    ax.set_xticks(x)
    ax.set_xticklabels(date_labels, rotation=45, ha='right')
    
    ax.legend(loc=CHART_STYLE['legend_loc'], framealpha=0.9)
    ax.grid(True, alpha=CHART_STYLE['grid_alpha'], axis='y')
    ax.tick_params(axis='both', labelsize=CHART_STYLE['tick_fontsize'])
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=CHART_STYLE['dpi'], bbox_inches='tight')
    plt.close()
    
    print(f"  Saved: {output_path}")


def generate_ratio_chart(df, ratio_columns, title, colors, output_path, period, chart_type):
    """
    Generate a chart based on the specified type.
    
    Args:
        df: DataFrame with date and ratio columns
        ratio_columns: List of column names to plot
        title: Chart title
        colors: List of colors for each series
        output_path: Path to save the PNG file
        period: 'annual' or 'quarterly'
        chart_type: 'line' or 'bar'
    """
    if chart_type == 'bar':
        generate_bar_chart(df, ratio_columns, title, colors, output_path, period)
    else:
        generate_line_chart(df, ratio_columns, title, colors, output_path, period)


# =============================================================================
# MAIN ORCHESTRATION
# =============================================================================

def validate_directory(directory):
    """
    Validate that the directory exists, create if necessary.
    
    Args:
        directory: Path to validate
        
    Returns:
        Path: Validated path object
    """
    path = Path(directory)
    
    if not path.exists():
        print(f"Warning: Directory '{directory}' does not exist.")
        print(f"  Creating directory: {directory}")
        path.mkdir(parents=True, exist_ok=True)
    
    return path


def build_output_path(directory, ticker, category, period):
    """
    Build the output file path for a chart.
    
    Args:
        directory: Output directory
        ticker: Stock ticker symbol
        category: Ratio category (liquidity, solvency, profitability)
        period: 'annual' or 'quarterly'
        
    Returns:
        Path: Full output file path
    """
    filename = f"{ticker}_{category}_ratios_{period}.png"
    return Path(directory) / filename


def main(args=None):
    """
    Main entry point for the ratio trend charts CLI tool.
    
    Args:
        args: Optional list of CLI arguments (for testing)
    """
    # Parse arguments
    parsed_args = parse_arguments(args)
    
    ticker = parsed_args.ticker.upper()
    directory = parsed_args.directory
    period = 'quarterly' if parsed_args.quarterly else 'annual'
    chart_type = parsed_args.chart_type
    
    print(f"\n{'='*60}")
    print(f"Ratio Trend Charts Generator")
    print(f"{'='*60}")
    print(f"Ticker:      {ticker}")
    print(f"Directory:   {directory}")
    print(f"Period:      {period}")
    print(f"Chart Type:  {chart_type}")
    print(f"{'='*60}\n")
    
    # Validate directory
    validate_directory(directory)
    
    # Load financial data
    print("Loading financial data...")
    data = load_financial_data(ticker, directory, period)
    
    balance_sheet = data.get('balance_sheet', pd.DataFrame())
    income_statement = data.get('income_statement', pd.DataFrame())
    cash_flow = data.get('cash_flow', pd.DataFrame())
    
    # Check if we have any data
    if balance_sheet.empty and income_statement.empty:
        print("\nError: No financial data found. Cannot generate charts.")
        print(f"Expected files in '{directory}':")
        file_paths = build_file_paths(ticker, directory, period)
        for name, path in file_paths.items():
            print(f"  - {path}")
        sys.exit(1)
    
    # Calculate ratios
    print("\nCalculating financial ratios...")
    
    liquidity_df = calculate_liquidity_ratios(balance_sheet)
    print(f"  Liquidity ratios: {len(liquidity_df)} periods")
    
    solvency_df = calculate_solvency_ratios(balance_sheet, income_statement)
    print(f"  Solvency ratios: {len(solvency_df)} periods")
    
    profitability_df = calculate_profitability_ratios(income_statement, balance_sheet)
    print(f"  Profitability ratios: {len(profitability_df)} periods")
    
    # Generate charts
    print(f"\nGenerating {chart_type} charts...")
    
    # Liquidity chart
    if not liquidity_df.empty:
        output_path = build_output_path(directory, ticker, 'liquidity', period)
        generate_ratio_chart(
            liquidity_df,
            LIQUIDITY_RATIOS,
            f"{ticker} Liquidity Ratios ({period.title()})",
            COLORS['liquidity'],
            output_path,
            period,
            chart_type
        )
    else:
        print("  Skipping liquidity chart (no data)")
    
    # Solvency chart
    if not solvency_df.empty:
        output_path = build_output_path(directory, ticker, 'solvency', period)
        generate_ratio_chart(
            solvency_df,
            SOLVENCY_RATIOS,
            f"{ticker} Solvency Ratios ({period.title()})",
            COLORS['solvency'],
            output_path,
            period,
            chart_type
        )
    else:
        print("  Skipping solvency chart (no data)")
    
    # Profitability chart
    if not profitability_df.empty:
        output_path = build_output_path(directory, ticker, 'profitability', period)
        generate_ratio_chart(
            profitability_df,
            PROFITABILITY_RATIOS,
            f"{ticker} Profitability Ratios ({period.title()})",
            COLORS['profitability'],
            output_path,
            period,
            chart_type
        )
    else:
        print("  Skipping profitability chart (no data)")
    
    # Summary
    print(f"\n{'='*60}")
    print("Chart generation complete!")
    print(f"Output directory: {directory}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
