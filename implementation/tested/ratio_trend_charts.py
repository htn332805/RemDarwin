import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys
import logging
import yaml
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='ratio_trend_charts.log',
    filemode='w'
)

# Liquidity Ratios

def calculate_current_ratio(bs_df):
    """Calculate current ratio from balance sheet data.

    Args:
        bs_df (pd.DataFrame): Balance sheet DataFrame with columns 'totalCurrentAssets' and 'totalCurrentLiabilities'.

    Returns:
        pd.Series: Current ratio series (totalCurrentAssets / totalCurrentLiabilities), NaN for invalid calculations.
    """
    if 'totalCurrentAssets' not in bs_df.columns or 'totalCurrentLiabilities' not in bs_df.columns:
        logging.warning("Ratio: current_ratio, Missing: totalCurrentAssets or totalCurrentLiabilities, Period: all")
        return pd.Series([np.nan] * len(bs_df), index=bs_df.index)
    try:
        denom = bs_df['totalCurrentLiabilities']
        ratio = np.where((denom != 0) & (~denom.isna()), bs_df['totalCurrentAssets'] / denom, np.nan)
        invalid = denom == 0
        for idx in bs_df.index[invalid]:
            logging.warning(f"Ratio: current_ratio, Missing: totalCurrentLiabilities == 0, Period: {idx}")
        return pd.Series(ratio, index=bs_df.index)
    except Exception as e:
        logging.error(f"Error calculating Current Ratio: {e}")
        return pd.Series([np.nan] * len(bs_df), index=bs_df.index)

def calculate_quick_ratio(bs_df):
    """Calculate quick ratio from balance sheet data.

    Args:
        bs_df (pd.DataFrame): Balance sheet DataFrame with columns 'totalCurrentAssets', 'inventory', and 'totalCurrentLiabilities'.

    Returns:
        pd.Series: Quick ratio series ((totalCurrentAssets - inventory) / totalCurrentLiabilities), NaN for invalid calculations.
    """
    if 'totalCurrentAssets' not in bs_df.columns or 'inventory' not in bs_df.columns or 'totalCurrentLiabilities' not in bs_df.columns:
        logging.warning("Ratio: quick_ratio, Missing: totalCurrentAssets or inventory or totalCurrentLiabilities, Period: all")
        return pd.Series([np.nan] * len(bs_df), index=bs_df.index)
    try:
        denom = bs_df['totalCurrentLiabilities']
        ratio = np.where((denom != 0) & (~denom.isna()), (bs_df['totalCurrentAssets'] - bs_df['inventory']) / denom, np.nan)
        invalid = denom == 0
        for idx in bs_df.index[invalid]:
            logging.warning(f"Ratio: quick_ratio, Missing: totalCurrentLiabilities == 0, Period: {idx}")
        return pd.Series(ratio, index=bs_df.index)
    except Exception as e:
        logging.error(f"Error calculating Quick Ratio: {e}")
        return pd.Series([np.nan] * len(bs_df), index=bs_df.index)

def calculate_cash_ratio(bs_df):
    """Calculate cash ratio from balance sheet data.

    Args:
        bs_df (pd.DataFrame): Balance sheet DataFrame with columns 'cashAndCashEquivalents' and 'totalCurrentLiabilities'.

    Returns:
        pd.Series: Cash ratio series (cashAndCashEquivalents / totalCurrentLiabilities), NaN for invalid calculations.
    """
    if 'cashAndCashEquivalents' not in bs_df.columns or 'totalCurrentLiabilities' not in bs_df.columns:
        logging.warning("Ratio: cash_ratio, Missing: cashAndCashEquivalents or totalCurrentLiabilities, Period: all")
        return pd.Series([np.nan] * len(bs_df), index=bs_df.index)
    try:
        denom = bs_df['totalCurrentLiabilities']
        ratio = np.where((denom != 0) & (~denom.isna()), bs_df['cashAndCashEquivalents'] / denom, np.nan)
        invalid = denom == 0
        for idx in bs_df.index[invalid]:
            logging.warning(f"Ratio: cash_ratio, Missing: totalCurrentLiabilities == 0, Period: {idx}")
        return pd.Series(ratio, index=bs_df.index)
    except Exception as e:
        logging.error(f"Error calculating Cash Ratio: {e}")
        return pd.Series([np.nan] * len(bs_df), index=bs_df.index)

# Solvency Ratios

def calculate_debt_to_equity(bs_df):
    """Calculate debt-to-equity ratio from balance sheet data.

    Args:
        bs_df (pd.DataFrame): Balance sheet DataFrame with columns 'totalDebt' and 'totalEquity'.

    Returns:
        pd.Series: Debt-to-equity ratio series (totalDebt / totalEquity), NaN for invalid calculations.
    """
    if 'totalDebt' not in bs_df.columns or 'totalEquity' not in bs_df.columns:
        logging.warning("Ratio: debt_to_equity, Missing: totalDebt or totalEquity, Period: all")
        return pd.Series([np.nan] * len(bs_df), index=bs_df.index)
    try:
        denom = bs_df['totalEquity']
        ratio = np.where((denom != 0) & (~denom.isna()), bs_df['totalDebt'] / denom, np.nan)
        invalid = denom == 0
        for idx in bs_df.index[invalid]:
            logging.warning(f"Ratio: debt_to_equity, Missing: totalEquity == 0, Period: {idx}")
        return pd.Series(ratio, index=bs_df.index)
    except Exception as e:
        logging.error(f"Error calculating Debt-to-Equity: {e}")
        return pd.Series([np.nan] * len(bs_df), index=bs_df.index)

def calculate_debt_to_assets(bs_df):
    """Calculate debt-to-assets ratio from balance sheet data.

    Args:
        bs_df (pd.DataFrame): Balance sheet DataFrame with columns 'totalDebt' and 'totalAssets'.

    Returns:
        pd.Series: Debt-to-assets ratio series (totalDebt / totalAssets), NaN for invalid calculations.
    """
    if 'totalDebt' not in bs_df.columns or 'totalAssets' not in bs_df.columns:
        logging.warning("Ratio: debt_to_assets, Missing: totalDebt or totalAssets, Period: all")
        return pd.Series([np.nan] * len(bs_df), index=bs_df.index)
    try:
        denom = bs_df['totalAssets']
        ratio = np.where((denom != 0) & (~denom.isna()), bs_df['totalDebt'] / denom, np.nan)
        invalid = denom == 0
        for idx in bs_df.index[invalid]:
            logging.warning(f"Ratio: debt_to_assets, Missing: totalAssets == 0, Period: {idx}")
        return pd.Series(ratio, index=bs_df.index)
    except Exception as e:
        logging.error(f"Error calculating Debt-to-Assets: {e}")
        return pd.Series([np.nan] * len(bs_df), index=bs_df.index)

def calculate_interest_coverage(is_df):
    """Calculate interest coverage ratio from income statement data.

    Args:
        is_df (pd.DataFrame): Income statement DataFrame with columns 'ebit' and 'interestExpense'.

    Returns:
        pd.Series: Interest coverage ratio series (ebit / interestExpense), NaN for invalid calculations.
    """
    if 'ebit' not in is_df.columns or 'interestExpense' not in is_df.columns:
        logging.warning("Ratio: interest_coverage, Missing: ebit or interestExpense, Period: all")
        return pd.Series([np.nan] * len(is_df), index=is_df.index)
    try:
        denom = is_df['interestExpense']
        ratio = np.where((denom != 0) & (~denom.isna()), is_df['ebit'] / denom, np.nan)
        invalid = denom == 0
        for idx in is_df.index[invalid]:
            logging.warning(f"Ratio: interest_coverage, Missing: interestExpense == 0, Period: {idx}")
        return pd.Series(ratio, index=is_df.index)
    except Exception as e:
        logging.error(f"Error calculating Interest Coverage: {e}")
        return pd.Series([np.nan] * len(is_df), index=is_df.index)

# Profitability Ratios

def calculate_roe(is_df, bs_df):
    """Calculate return on equity (ROE) from income statement and balance sheet data.

    Args:
        is_df (pd.DataFrame): Income statement DataFrame with column 'netIncome'.
        bs_df (pd.DataFrame): Balance sheet DataFrame with column 'totalEquity'.

    Returns:
        pd.Series: ROE series (netIncome / totalEquity), NaN for invalid calculations.
    """
    if 'netIncome' not in is_df.columns or 'totalEquity' not in bs_df.columns:
        logging.warning("Ratio: roe, Missing: netIncome or totalEquity, Period: all")
        return pd.Series([np.nan] * len(is_df), index=is_df.index)
    try:
        denom = bs_df['totalEquity']
        ratio = np.where((denom != 0) & (~denom.isna()), is_df['netIncome'] / denom, np.nan)
        invalid = denom == 0
        for idx in bs_df.index[invalid]:
            logging.warning(f"Ratio: roe, Missing: totalEquity == 0, Period: {idx}")
        return pd.Series(ratio, index=is_df.index)
    except Exception as e:
        logging.error(f"Error calculating ROE: {e}")
        return pd.Series([np.nan] * len(is_df), index=is_df.index)

def calculate_roa(is_df, bs_df):
    """Calculate return on assets (ROA) from income statement and balance sheet data.

    Args:
        is_df (pd.DataFrame): Income statement DataFrame with column 'netIncome'.
        bs_df (pd.DataFrame): Balance sheet DataFrame with column 'totalAssets'.

    Returns:
        pd.Series: ROA series (netIncome / totalAssets), NaN for invalid calculations.
    """
    if 'netIncome' not in is_df.columns or 'totalAssets' not in bs_df.columns:
        logging.warning("Ratio: roa, Missing: netIncome or totalAssets, Period: all")
        return pd.Series([np.nan] * len(is_df), index=is_df.index)
    try:
        denom = bs_df['totalAssets']
        ratio = np.where((denom != 0) & (~denom.isna()), is_df['netIncome'] / denom, np.nan)
        invalid = denom == 0
        for idx in bs_df.index[invalid]:
            logging.warning(f"Ratio: roa, Missing: totalAssets == 0, Period: {idx}")
        return pd.Series(ratio, index=is_df.index)
    except Exception as e:
        logging.error(f"Error calculating ROA: {e}")
        return pd.Series([np.nan] * len(is_df), index=is_df.index)

def calculate_gross_margin(is_df):
    """Calculate gross margin from income statement data.

    Args:
        is_df (pd.DataFrame): Income statement DataFrame with columns 'grossProfit' and 'revenue'.

    Returns:
        pd.Series: Gross margin series (grossProfit / revenue), NaN for invalid calculations.
    """
    if 'grossProfit' not in is_df.columns or 'revenue' not in is_df.columns:
        logging.warning("Ratio: gross_margin, Missing: grossProfit or revenue, Period: all")
        return pd.Series([np.nan] * len(is_df), index=is_df.index)
    try:
        denom = is_df['revenue']
        ratio = np.where((denom != 0) & (~denom.isna()), is_df['grossProfit'] / denom, np.nan)
        invalid = denom == 0
        for idx in is_df.index[invalid]:
            logging.warning(f"Ratio: gross_margin, Missing: revenue == 0, Period: {idx}")
        return pd.Series(ratio, index=is_df.index)
    except Exception as e:
        logging.error(f"Error calculating Gross Margin: {e}")
        return pd.Series([np.nan] * len(is_df), index=is_df.index)

def calculate_operating_margin(is_df):
    """Calculate operating margin from income statement data.

    Args:
        is_df (pd.DataFrame): Income statement DataFrame with columns 'operatingIncome' and 'revenue'.

    Returns:
        pd.Series: Operating margin series (operatingIncome / revenue), NaN for invalid calculations.
    """
    if 'operatingIncome' not in is_df.columns or 'revenue' not in is_df.columns:
        logging.warning("Ratio: operating_margin, Missing: operatingIncome or revenue, Period: all")
        return pd.Series([np.nan] * len(is_df), index=is_df.index)
    try:
        denom = is_df['revenue']
        ratio = np.where((denom != 0) & (~denom.isna()), is_df['operatingIncome'] / denom, np.nan)
        invalid = denom == 0
        for idx in is_df.index[invalid]:
            logging.warning(f"Ratio: operating_margin, Missing: revenue == 0, Period: {idx}")
        return pd.Series(ratio, index=is_df.index)
    except Exception as e:
        logging.error(f"Error calculating Operating Margin: {e}")
        return pd.Series([np.nan] * len(is_df), index=is_df.index)

def calculate_net_margin(is_df):
    """Calculate net margin from income statement data.

    Args:
        is_df (pd.DataFrame): Income statement DataFrame with columns 'netIncome' and 'revenue'.

    Returns:
        pd.Series: Net margin series (netIncome / revenue), NaN for invalid calculations.
    """
    if 'netIncome' not in is_df.columns or 'revenue' not in is_df.columns:
        logging.warning("Ratio: net_margin, Missing: netIncome or revenue, Period: all")
        return pd.Series([np.nan] * len(is_df), index=is_df.index)
    try:
        denom = is_df['revenue']
        ratio = np.where((denom != 0) & (~denom.isna()), is_df['netIncome'] / denom, np.nan)
        invalid = denom == 0
        for idx in is_df.index[invalid]:
            logging.warning(f"Ratio: net_margin, Missing: revenue == 0, Period: {idx}")
        return pd.Series(ratio, index=is_df.index)
    except Exception as e:
        logging.error(f"Error calculating Net Margin: {e}")
        return pd.Series([np.nan] * len(is_df), index=is_df.index)

# Efficiency Ratios

def calculate_asset_turnover(bs_df, is_df):
    """Calculate asset turnover from balance sheet and income statement data.

    Args:
        bs_df (pd.DataFrame): Balance sheet DataFrame with column 'totalAssets'.
        is_df (pd.DataFrame): Income statement DataFrame with column 'revenue'.

    Returns:
        pd.Series: Asset turnover series (revenue / totalAssets), NaN for invalid calculations.
    """
    if 'totalAssets' not in bs_df.columns or 'revenue' not in is_df.columns:
        logging.warning("Ratio: asset_turnover, Missing: totalAssets or revenue, Period: all")
        return pd.Series([np.nan] * len(is_df), index=is_df.index)
    try:
        denom = bs_df['totalAssets']
        ratio = np.where((denom != 0) & (~denom.isna()), is_df['revenue'] / denom, np.nan)
        invalid = denom == 0
        for idx in bs_df.index[invalid]:
            logging.warning(f"Ratio: asset_turnover, Missing: totalAssets == 0, Period: {idx}")
        return pd.Series(ratio, index=is_df.index)
    except Exception as e:
        logging.error(f"Error calculating Asset Turnover: {e}")
        return pd.Series([np.nan] * len(is_df), index=is_df.index)

def calculate_inventory_turnover(bs_df, is_df):
    """Calculate inventory turnover from balance sheet and income statement data.

    Args:
        bs_df (pd.DataFrame): Balance sheet DataFrame with column 'inventory'.
        is_df (pd.DataFrame): Income statement DataFrame with column 'costOfRevenue'.

    Returns:
        pd.Series: Inventory turnover series (costOfRevenue / inventory), NaN for invalid calculations.
    """
    if 'inventory' not in bs_df.columns or 'costOfRevenue' not in is_df.columns:
        logging.warning("Ratio: inventory_turnover, Missing: inventory or costOfRevenue, Period: all")
        return pd.Series([np.nan] * len(is_df), index=is_df.index)
    try:
        denom = bs_df['inventory']
        ratio = np.where((denom != 0) & (~denom.isna()), is_df['costOfRevenue'] / denom, np.nan)
        invalid = denom == 0
        for idx in bs_df.index[invalid]:
            logging.warning(f"Ratio: inventory_turnover, Missing: inventory == 0, Period: {idx}")
        return pd.Series(ratio, index=is_df.index)
    except Exception as e:
        logging.error(f"Error calculating Inventory Turnover: {e}")
        return pd.Series([np.nan] * len(is_df), index=is_df.index)

# Market Ratios

def calculate_pe_ratio(prices_df, is_df):
    """Calculate P/E ratio from prices and income statement data.

    Args:
        prices_df (pd.DataFrame): Prices DataFrame with column 'close'.
        is_df (pd.DataFrame): Income statement DataFrame with column 'eps'.

    Returns:
        pd.Series: P/E ratio series (close / eps), NaN for invalid calculations.
    """
    if 'close' not in prices_df.columns or 'eps' not in is_df.columns:
        logging.warning("Ratio: pe_ratio, Missing: close or eps, Period: all")
        return pd.Series([np.nan] * len(is_df), index=is_df.index)
    try:
        eps = is_df['eps']
        ratio = np.where((eps != 0) & (~eps.isna()), prices_df['close'] / eps, np.nan)
        invalid = eps == 0
        for idx in is_df.index[invalid]:
            logging.warning(f"Ratio: pe_ratio, Missing: eps == 0, Period: {idx}")
        return pd.Series(ratio, index=is_df.index)
    except Exception as e:
        logging.error(f"Error calculating P/E Ratio: {e}")
        return pd.Series([np.nan] * len(is_df), index=is_df.index)

def calculate_ev_ebitda(bs_df, is_df, market_df):
    """Calculate EV/EBITDA from balance sheet, income statement, and market cap data.

    Args:
        bs_df (pd.DataFrame): Balance sheet DataFrame with columns 'totalDebt', 'cashAndCashEquivalents'.
        is_df (pd.DataFrame): Income statement DataFrame with column 'ebitda'.
        market_df (pd.DataFrame): Market cap DataFrame with column 'marketCap'.

    Returns:
        pd.Series: EV/EBITDA series ((marketCap + totalDebt - cashAndCashEquivalents) / ebitda), NaN for invalid calculations.
    """
    if 'totalDebt' not in bs_df.columns or 'cashAndCashEquivalents' not in bs_df.columns or 'ebitda' not in is_df.columns or 'marketCap' not in market_df.columns:
        logging.warning("Ratio: ev_ebitda, Missing: required columns, Period: all")
        return pd.Series([np.nan] * len(is_df), index=is_df.index)
    try:
        ev = market_df['marketCap'] + bs_df['totalDebt'] - bs_df['cashAndCashEquivalents']
        ebitda = is_df['ebitda']
        ratio = np.where((ebitda != 0) & (~ebitda.isna()), ev / ebitda, np.nan)
        invalid = ebitda == 0
        for idx in is_df.index[invalid]:
            logging.warning(f"Ratio: ev_ebitda, Missing: ebitda == 0, Period: {idx}")
        return pd.Series(ratio, index=is_df.index)
    except Exception as e:
        logging.error(f"Error calculating EV/EBITDA: {e}")
        return pd.Series([np.nan] * len(is_df), index=is_df.index)

def calculate_trend_line(series):
    """Calculate linear trend line statistics for a series.

    Args:
        series (pd.Series): Time series data.

    Returns:
        dict: Dictionary with 'slope', 'intercept', and 'r_squared'.
    """
    series = series.dropna()
    if len(series) < 2:
        return {'slope': np.nan, 'intercept': np.nan, 'r_squared': np.nan}
    x = np.arange(len(series))
    y = series.values
    slope, intercept = np.polyfit(x, y, 1)
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred)**2)
    ss_tot = np.sum((y - np.mean(y))**2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else np.nan
    return {'slope': slope, 'intercept': intercept, 'r_squared': r_squared}

def calculate_moving_average(series, window=12):
    """Calculate simple moving average for a series.

    Args:
        series (pd.Series): Time series data.
        window (int): Window size for the moving average.

    Returns:
        pd.Series: Moving average series.
    """
    return series.rolling(window=window).mean()

def calculate_volatility(series):
    """Calculate volatility metrics for a series.

    Args:
        series (pd.Series): Time series data.

    Returns:
        dict: Dictionary with 'std_dev' and 'coefficient_of_variation'.
    """
    series = series.dropna()
    if len(series) < 2:
        return {'std_dev': np.nan, 'coefficient_of_variation': np.nan}
    std_dev = series.std()
    mean_val = series.mean()
    coeff_var = std_dev / mean_val if mean_val != 0 else np.nan
    return {'std_dev': std_dev, 'coefficient_of_variation': coeff_var}

def calculate_ratio_volatility(ratios_df):
    """Compute volatility for each ratio column in the DataFrame.

    Args:
        ratios_df (pd.DataFrame): DataFrame containing ratio columns.

    Returns:
        dict: Dictionary with ratio names as keys and volatility dicts as values.
    """
    volatility_dict = {}
    for col in ratios_df.columns:
        series = ratios_df[col]
        volatility_dict[col] = calculate_volatility(series)
    return volatility_dict

def calculate_correlation_matrix(ratios_df):
    """Calculate correlation matrix for ratios DataFrame.

    Args:
        ratios_df (pd.DataFrame): DataFrame containing ratio columns.

    Returns:
        pd.DataFrame: Correlation matrix.
    """
    return ratios_df.corr()

def plot_correlation_matrix(corr_matrix, ticker, period, output_dir):
    """Plot correlation matrix using seaborn heatmap.

    Args:
        corr_matrix (pd.DataFrame): Correlation matrix.
        ticker (str): Stock ticker.
        period (str): 'annual' or 'quarterly'.
        output_dir (str): Directory to save the plot.

    Returns:
        bool: True if saved, False otherwise.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        plt.figure(figsize=(12, 10))
        sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap='coolwarm', square=True, cbar=True)
        plt.title(f"{ticker} Correlation Matrix ({period})")
        filename = f"{ticker}_correlation_matrix_{period}.png"
        filepath = os.path.join(output_dir, filename)
        plt.savefig(filepath)
        plt.close()
        logging.info(f"Correlation matrix plot saved to {filepath}")
        return True
    except Exception as e:
        logging.error(f"Failed to plot correlation matrix: {e}")
        return False

def load_financial_data(ticker, period, directory):
    """
    Load financial data from CSV files.

    Args:
        ticker (str): Stock ticker symbol.
        period (str): 'annual' or 'quarterly'.
        directory (str): Directory containing the CSV files.

    Returns:
        dict or None: Dictionary with 'balance_sheet', 'income_statement', 'cash_flow' DataFrames if successful, None if any file is missing or error.
    """
    file_paths = {
        'balance_sheet': os.path.join(directory, f"{ticker}_balance_sheet_{period}.csv"),
        'income_statement': os.path.join(directory, f"{ticker}_income_statement_{period}.csv"),
        'cash_flow': os.path.join(directory, f"{ticker}_cash_flow_statement_{period}.csv")
    }
    data = {}
    for key, path in file_paths.items():
        try:
            df = pd.read_csv(path, parse_dates=['date'])
            if 'date' in df.columns:
                df.set_index('date', inplace=True)
            df.sort_index(inplace=True)
            data[key] = df
        except FileNotFoundError:
            logging.error(f"File not found: {path}")
            return None
        except Exception as e:
            logging.error(f"Error reading {path}: {e}")
            return None
    # Optional market data
    optional_files = {
        'prices': os.path.join(directory, f"{ticker}_historical_prices_{period}.csv"),
        'market_cap': os.path.join(directory, f"{ticker}_historical_market_cap_{period}.csv")
    }
    for key, path in optional_files.items():
        try:
            df = pd.read_csv(path, parse_dates=['date'])
            if 'date' in df.columns:
                df.set_index('date', inplace=True)
            df.sort_index(inplace=True)
            data[key] = df
        except Exception as e:
            logging.warning(f"Optional market data file not found or error: {path}: {e}")
    return data

def plot_ratio_trend(ratios_series, ratio_name, ticker, category, period, chart_type, output_dir):
    """Plot ratio trend chart.

    Args:
        ratios_series (pd.Series): Ratio values indexed by date.
        ratio_name (str): Name of the ratio.
        ticker (str): Stock ticker.
        category (str): Category of the ratio (e.g., 'liquidity').
        period (str): 'annual' or 'quarterly'.
        chart_type (str): 'line' or 'bar'.
        output_dir (str): Directory to save the plot.

    Returns:
        bool: True if plot was saved, False if no data or error.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        ratios_series = ratios_series.dropna()
        if ratios_series.empty:
            logging.warning(f"No valid data for {ratio_name} to plot.")
            return False
        plt.figure(figsize=(10, 6))
        if chart_type == 'line':
            plt.plot(ratios_series.index, ratios_series.values, marker='o', label='Ratio')
            # Add trend line if available
            trend = calculate_trend_line(ratios_series)
            if not np.isnan(trend['slope']):
                x = np.arange(len(ratios_series))
                y_trend = trend['slope'] * x + trend['intercept']
                plt.plot(ratios_series.index, y_trend, 'r--', label='Trend Line')
                plt.legend()
                # Add annotation for stats
                slope_text = f"Slope: {trend['slope']:.4f}"
                r2_text = f"R²: {trend['r_squared']:.4f}"
                plt.annotate(f"{slope_text}\n{r2_text}", xy=(0.02, 0.98), xycoords='axes fraction', 
                             verticalalignment='top', fontsize=10, 
                             bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        elif chart_type == 'bar':
            plt.bar(ratios_series.index, ratios_series.values)
        plt.xlabel('Date')
        plt.ylabel(ratio_name)
        plt.title(f"{ticker} {ratio_name} Trend ({period})")
        plt.grid(True)
        filename = f"{ticker}_{category}_{ratio_name}_{period}.png"
        filepath = os.path.join(output_dir, filename)
        plt.savefig(filepath)
        plt.close()
        logging.info(f"Plot saved to {filepath}")
        return True
    except Exception as e:
        logging.error(f"Failed to plot {ratio_name}: {e}")
        return False

def plot_ratio_heatmap(ratios_df, ticker, period, output_dir):
    """Plot ratio heatmaps using seaborn with subplots for each category.

    Args:
        ratios_df (pd.DataFrame): DataFrame containing ratio columns.
        ticker (str): Stock ticker.
        period (str): 'annual' or 'quarterly'.
        output_dir (str): Directory to save the plot.

    Returns:
        bool: True if saved, False otherwise.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        # Define categories
        categories = {
            'liquidity': ['current_ratio', 'quick_ratio', 'cash_ratio'],
            'solvency': ['debt_to_equity', 'debt_to_assets', 'interest_coverage'],
            'profitability': ['roe', 'roa', 'gross_margin', 'operating_margin', 'net_margin'],
            'efficiency': ['asset_turnover', 'inventory_turnover'],
            'market': ['pe_ratio', 'ev_ebitda']
        }
        # Filter categories that have data
        valid_categories = {}
        for cat, cols in categories.items():
            cat_cols = [c for c in cols if c in ratios_df.columns]
            if cat_cols:
                valid_categories[cat] = cat_cols
        num_cats = len(valid_categories)
        if num_cats == 0:
            logging.warning("No valid categories for heatmap.")
            return False
        # Determine subplot layout
        if num_cats <= 3:
            nrows = 1
            ncols = num_cats
        else:
            nrows = 2
            ncols = (num_cats + 1) // 2
        fig, axes = plt.subplots(nrows, ncols, figsize=(12 * ncols, 8 * nrows))
        if nrows > 1:
            axes = axes.flatten()
        elif num_cats == 1:
            axes = [axes]
        for i, (cat, cols) in enumerate(valid_categories.items()):
            cat_df = ratios_df[cols]
            # Normalize per category
            normalized_cat = (cat_df.T - cat_df.T.mean(axis=1, skipna=True)[:, None]) / cat_df.T.std(axis=1, skipna=True)[:, None]
            sns.heatmap(normalized_cat, annot=False, cmap='RdYlBu_r', center=0, cbar=True, ax=axes[i])
            axes[i].set_title(f"{cat.title()} Ratios")
            axes[i].set_xlabel('Date')
            axes[i].set_ylabel('Ratio')
        # Hide unused axes
        for j in range(i + 1, nrows * ncols):
            axes[j].set_visible(False)
        plt.tight_layout()
        plt.suptitle(f"{ticker} Ratios Heatmaps by Category ({period})", fontsize=16)
        filename = f"{ticker}_ratios_heatmap_{period}.png"
        filepath = os.path.join(output_dir, filename)
        plt.savefig(filepath)
        plt.close()
        logging.info(f"Ratios heatmaps saved to {filepath}")
        return True
    except Exception as e:
        logging.error(f"Failed to plot ratios heatmaps: {e}")
        return False

def plot_pairwise_scatter(ratios_df, output_dir):
    """Generate scatter plots for key ratio pairs based on top correlations.

    Args:
        ratios_df (pd.DataFrame): DataFrame containing ratio columns.
        output_dir (str): Directory to save the plots.

    Returns:
        int: Number of plots saved.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        corr_matrix = ratios_df.corr()
        # Get upper triangle of correlation matrix
        corr_upper = corr_matrix.where(np.triu(np.ones_like(corr_matrix), k=1).astype(bool))
        # Stack to get pairs
        pairs = corr_upper.stack().reset_index()
        pairs.columns = ['ratio1', 'ratio2', 'correlation']
        # Sort by absolute correlation descending
        pairs['abs_corr'] = pairs['correlation'].abs()
        pairs = pairs.sort_values('abs_corr', ascending=False)
        # Select top 10 pairs, or fewer if not available
        top_pairs = pairs.head(10)
        plots_saved = 0
        for _, row in top_pairs.iterrows():
            ratio1 = row['ratio1']
            ratio2 = row['ratio2']
            corr_val = row['correlation']
            # Get data, drop NaNs
            data = ratios_df[[ratio1, ratio2]].dropna()
            if len(data) < 2:
                continue
            plt.figure(figsize=(8, 6))
            plt.scatter(data[ratio1], data[ratio2], alpha=0.7)
            plt.xlabel(ratio1.replace('_', ' ').title())
            plt.ylabel(ratio2.replace('_', ' ').title())
            plt.title(f"{ratio1.replace('_', ' ').title()} vs {ratio2.replace('_', ' ').title()} (Corr: {corr_val:.2f})")
            plt.grid(True)
            filename = f"{ratio1}_vs_{ratio2}.png"
            filepath = os.path.join(output_dir, filename)
            plt.savefig(filepath)
            plt.close()
            logging.info(f"Scatter plot saved to {filepath}")
            plots_saved += 1
        return plots_saved
    except Exception as e:
        logging.error(f"Failed to plot pairwise scatters: {e}")
        return 0

def export_ratios_csv(ratios_df, ticker, period, output_dir):
    """Export ratios DataFrame to CSV file.

    Args:
        ratios_df (pd.DataFrame): DataFrame containing calculated ratios.
        ticker (str): Stock ticker symbol.
        period (str): 'annual' or 'quarterly'.
        output_dir (str): Directory to save the CSV file.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{ticker}_calculated_ratios_{period}.csv"
        filepath = os.path.join(output_dir, filename)
        ratios_df.to_csv(filepath, index=True)
        logging.info(f"Ratios exported to {filepath}")
    except Exception as e:
        logging.error(f"Error exporting ratios to CSV: {e}")

def load_custom_ratios(config_file, data):
    """
    Load custom ratios from a YAML config file.

    Args:
        config_file (str): Path to the YAML config file.
        data (dict): Dictionary of loaded financial data DataFrames.

    Returns:
        list: List of tuples (category, name, func, *dfs) for custom ratios.
    """
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Error loading config file {config_file}: {e}")
        return []

    custom_ratios = []
    for item in config.get('ratios', []):
        name = item['name']
        category = item.get('category', 'custom')
        formula = item['formula']
        data_sources = item.get('data_sources', ['balance_sheet'])
        dfs = []
        for source in data_sources:
            if source in data:
                dfs.append(data[source])
            else:
                logging.warning(f"Data source {source} not available for custom ratio {name}")
                dfs.append(pd.DataFrame())  # dummy DataFrame to avoid errors

        def create_func(formula, data_sources):
            def func(*dfs):
                if not dfs or any(df.empty for df in dfs):
                    return pd.Series([np.nan], index=[pd.Timestamp.now()])  # dummy
                locals_dict = {source: df for source, df in zip(data_sources, dfs)}
                try:
                    # Evaluate the formula with np and pd available
                    result = eval(formula, {"np": np, "pd": pd}, locals_dict)
                    # Ensure result is a Series
                    if isinstance(result, pd.Series):
                        return result
                    else:
                        # If scalar, repeat for each index
                        return pd.Series([result] * len(dfs[0]), index=dfs[0].index)
                except Exception as e:
                    logging.error(f"Error evaluating formula for {name}: {e}")
                    return pd.Series([np.nan] * len(dfs[0]), index=dfs[0].index)
            return func

        func = create_func(formula, data_sources)
        custom_ratios.append((category, name, func, *dfs))
    return custom_ratios

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='ratio_trend_charts.py',
        description='Generate ratio trend charts for stock tickers.',
        epilog='Use --help for more information.'
    )
    parser.add_argument('-t', '--ticker', required=True, type=str, help='Stock ticker symbol (required)')
    parser.add_argument('-d', '--directory', type=str, default='data', help='Directory containing data files (default: data)')
    parser.add_argument('-q', '--quarterly', action='store_true', help='Use quarterly data instead of annual')
    parser.add_argument('-c', '--chart-type', choices=['line', 'bar'], default='line', help='Type of chart to generate (default: line)')
    parser.add_argument('-o', '--output-dir', type=str, default='charts', help='Output directory for charts (default: charts)')
    parser.add_argument('--config', type=str, help='Path to YAML config file for custom ratios')
    parser.add_argument('--heatmaps', action='store_true', help='Generate ratio heatmaps')
    parser.add_argument('--correlation', action='store_true', help='Generate correlation matrix plot')
    parser.add_argument('--stats', action='store_true', help='Compute and save ratio statistics to JSON')

    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        logging.error(f"Directory '{args.directory}' does not exist.")
        sys.exit(1)

    period = 'quarterly' if args.quarterly else 'annual'
    logging.info(f"Starting ratio trend chart generation for {args.ticker} ({period})")

    data = load_financial_data(args.ticker, period, args.directory)
    if data is None:
        logging.error("Failed to load financial data. Exiting.")
        sys.exit(1)

    bs_df = data['balance_sheet']
    is_df = data['income_statement']
    cf_df = data['cash_flow']
    prices_df = data.get('prices')
    market_df = data.get('market_cap')

    ratios = [
        ('liquidity', 'current_ratio', calculate_current_ratio, bs_df),
        ('liquidity', 'quick_ratio', calculate_quick_ratio, bs_df),
        ('liquidity', 'cash_ratio', calculate_cash_ratio, bs_df),
        ('solvency', 'debt_to_equity', calculate_debt_to_equity, bs_df),
        ('solvency', 'debt_to_assets', calculate_debt_to_assets, bs_df),
        ('solvency', 'interest_coverage', calculate_interest_coverage, is_df),
        ('profitability', 'roe', calculate_roe, is_df, bs_df),
        ('profitability', 'roa', calculate_roa, is_df, bs_df),
        ('profitability', 'gross_margin', calculate_gross_margin, is_df),
        ('profitability', 'operating_margin', calculate_operating_margin, is_df),
        ('profitability', 'net_margin', calculate_net_margin, is_df),
        ('efficiency', 'asset_turnover', calculate_asset_turnover, bs_df, is_df),
        ('efficiency', 'inventory_turnover', calculate_inventory_turnover, bs_df, is_df),
    ]

    if prices_df is not None and market_df is not None:
        ratios.extend([
            ('market', 'pe_ratio', calculate_pe_ratio, prices_df, is_df),
            ('market', 'ev_ebitda', calculate_ev_ebitda, bs_df, is_df, market_df),
        ])

    if args.config:
        custom_ratios = load_custom_ratios(args.config, data)
        ratios.extend(custom_ratios)

    ratios_data = {}
    successful_plots = 0
    total_ratios = len(ratios)

    for category, ratio_name, func, *dfs in ratios:
        try:
            logging.info(f"Calculating and plotting {ratio_name}")
            series = func(*dfs)
            ratios_data[ratio_name] = series
            if plot_ratio_trend(series, ratio_name, args.ticker, category, period, args.chart_type, args.output_dir):
                successful_plots += 1
        except Exception as e:
            logging.error(f"Error processing {ratio_name}: {e}")

    ratios_df = pd.DataFrame(ratios_data)

    if args.heatmaps:
        plot_ratio_heatmap(ratios_df, args.ticker, period, args.output_dir)

    if args.correlation:
        corr_matrix = calculate_correlation_matrix(ratios_df)
        plot_correlation_matrix(corr_matrix, args.ticker, period, args.output_dir)

    pairwise_plots = plot_pairwise_scatter(ratios_df, args.output_dir)
    logging.info(f"Generated {pairwise_plots} pairwise scatter plots.")

    if args.stats:
        stats = {}
        for col in ratios_df.columns:
            series = ratios_df[col]
            trend = calculate_trend_line(series)
            vol = calculate_volatility(series)
            stats[col] = {'trend': trend, 'volatility': vol}
        os.makedirs(args.output_dir, exist_ok=True)
        stats_file = os.path.join(args.output_dir, f"{args.ticker}_stats_{period}.json")
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=4)
        logging.info(f"Ratio statistics saved to {stats_file}")

    try:
        export_ratios_csv(ratios_df, args.ticker, period, args.directory)
    except Exception as e:
        logging.error(f"Error exporting ratios: {e}")

    logging.info(f"Generation complete. Plotted {successful_plots} out of {total_ratios} ratios.")
    print(f"Generated {successful_plots} ratio trend charts for {args.ticker} ({period}).")


