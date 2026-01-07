"""
fmp_fetcher.py

A command-line interface (CLI) tool for fetching financial data from the Financial Modeling Prep (FMP) API.

This script serves as the entry point for the MyCFATool project, providing automated retrieval of financial statements, ratios, metrics, and historical prices for specified stock tickers. Data can be output in CSV or JSON formats and optionally stored in SQLite databases for further analysis.

Key Features:
- Supports both annual and quarterly financial data.
- Handles API authentication via environment variables.
- Implements logging to file for detailed operation tracking and error recording.
- Provides comprehensive error handling for API responses and file operations, ensuring graceful failure management and continued processing.
- Extensible structure for adding more data types and processing logic.
- Includes save_to_csv function for exporting fetched data to CSV format.
- Provides specialized fetch functions for period-dependent financial data categories including income statements, balance sheets, cash flow statements, ratios, enterprise values, financial growth metrics, and analyst estimates, as well as non-period financial data categories including owner earnings, scores, key metrics TTM, ratios TTM, discounted cash flow valuations, ratings, historical data, market capitalization, employee counts, institutional holdings, insider trading data, analyst recommendations, and technical indicators.

Usage:
    python fmp_fetcher.py --ticker AAPL --output ./output --period annual

Design Decisions:
- Modular imports for clarity and maintainability.
- Use of argparse for flexible CLI options with validation and help generation.
- Environment variable loading for secure API key management.
- ENDPOINTS dictionary organizes API URL templates for maintainability and extensibility.
- main() function implements complete CLI argument parsing and orchestrates comprehensive data fetching from all FMP API endpoints, with progress reporting and automated CSV export.
- Separation of concerns: imports grouped by standard library vs third-party.
- save_to_csv function implements CSV export functionality with automatic directory creation and data validation.
- Specific fetch functions for annual/quarterly endpoints, building on the base fetch functionality and ENDPOINTS dictionary.
- Future extensions planned for JSON export, SQLite integration, and advanced data processing.

Author: Auto-generated
Date: 2026-01-02

"""

# Standard library imports for core functionality
import argparse  # Command-line argument parsing for user inputs
import os  # Operating system interfaces for environment and file operations
import requests  # HTTP library for API requests to FMP
import csv  # CSV file handling for data export
import json  # JSON parsing for API responses and data manipulation
import time
# Third-party libraries
from dotenv import load_dotenv  # Loading environment variables from .env files for secure configuration

# Logging import
import logging  # Standard logging module for recording application events and errors

# Suppress urllib3 OpenSSL compatibility warning
import warnings
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL 1.1.1+", category=UserWarning)

"""
ENDPOINTS Dictionary Documentation

This dictionary serves as a centralized repository for all Financial Modeling Prep (FMP) API URL templates.
It organizes API endpoints by category to ensure maintainability, consistency, and ease of extension.

Structure:
- Top-level keys: Endpoint categories (e.g., 'income_statement', 'balance_sheet')
- Second-level keys: Periods or types ('annual', 'quarterly', 'no_period', or specific types like 'all', 'purchases')
- Values: URL template strings with placeholders for dynamic substitution

Organization:
- Financial statements and metrics are organized by period (annual/quarterly) where applicable.
- Endpoints without period distinction use 'no_period' as the key.
- Special cases like 'insider_trading' include transaction types ('all', 'purchases', 'sales') for granular data access.
- 'technical_indicators' category contains sub-types for different technical analysis indicators (SMA, EMA, RSI, etc.).

Placeholders:
- {ticker}: Replaced with the stock symbol (e.g., 'AAPL')
- {apikey}: Replaced with the FMP API key for authentication

Special Cases:
- insider_trading: Provides URLs for all insider transactions, purchases only, or sales only.
- technical_indicators: Includes common technical indicators with default periods (e.g., SMA uses 252 periods).

Usage for URL Construction:
- Select the appropriate template: ENDPOINTS['category']['period_or_type']
- Format with actual values: template.format(ticker='AAPL', apikey='your_key')
- Example: ENDPOINTS['income_statement']['annual'].format(ticker='AAPL', apikey='your_key')

This design promotes DRY principles by avoiding hardcoded URLs and enables easy addition of new endpoints.
"""
ENDPOINTS = {
    'income_statement': {
        'annual': 'https://financialmodelingprep.com/api/v3/income-statement/{ticker}?period=annual&apikey={apikey}',
        'quarterly': 'https://financialmodelingprep.com/api/v3/income-statement/{ticker}?period=quarterly&apikey={apikey}'
    },
    'balance_sheet': {
        'annual': 'https://financialmodelingprep.com/api/v3/balance-sheet-statement/{ticker}?period=annual&apikey={apikey}',
        'quarterly': 'https://financialmodelingprep.com/api/v3/balance-sheet-statement/{ticker}?period=quarterly&apikey={apikey}'
    },
    'cash_flow_statement': {
        'annual': 'https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker}?period=annual&apikey={apikey}',
        'quarterly': 'https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker}?period=quarterly&apikey={apikey}'
    },
    'ratios': {
        'annual': 'https://financialmodelingprep.com/api/v3/ratios/{ticker}?period=annual&apikey={apikey}',
        'quarterly': 'https://financialmodelingprep.com/api/v3/ratios/{ticker}?period=quarterly&apikey={apikey}'
    },
    'enterprise_values': {
        'annual': 'https://financialmodelingprep.com/api/v3/enterprise-values/{ticker}?period=annual&apikey={apikey}',
        'quarterly': 'https://financialmodelingprep.com/api/v3/enterprise-values/{ticker}?period=quarterly&apikey={apikey}'
    },
    'financial_growth': {
        'annual': 'https://financialmodelingprep.com/api/v3/financial-growth/{ticker}?period=annual&apikey={apikey}',
        'quarterly': 'https://financialmodelingprep.com/api/v3/financial-growth/{ticker}?period=quarterly&apikey={apikey}'
    },
    'balance_sheet_growth': {
        'annual': 'https://financialmodelingprep.com/api/v3/balance-sheet-statement-growth/{ticker}?period=annual&apikey={apikey}',
        'quarterly': 'https://financialmodelingprep.com/api/v3/balance-sheet-statement-growth/{ticker}?period=quarterly&apikey={apikey}'
    },
    'income_statement_growth': {
        'annual': 'https://financialmodelingprep.com/api/v3/income-statement-growth/{ticker}?period=annual&apikey={apikey}',
        'quarterly': 'https://financialmodelingprep.com/api/v3/income-statement-growth/{ticker}?period=quarterly&apikey={apikey}'
    },
    'cash_flow_statement_growth': {
        'annual': 'https://financialmodelingprep.com/api/v3/cash-flow-statement-growth/{ticker}?period=annual&apikey={apikey}',
        'quarterly': 'https://financialmodelingprep.com/api/v3/cash-flow-statement-growth/{ticker}?period=quarterly&apikey={apikey}'
    },
    'key_metrics': {
        'annual': 'https://financialmodelingprep.com/api/v3/key-metrics/{ticker}?period=annual&apikey={apikey}',
        'quarterly': 'https://financialmodelingprep.com/api/v3/key-metrics/{ticker}?period=quarterly&apikey={apikey}'
    },
    'analyst_estimates': {
        'annual': 'https://financialmodelingprep.com/api/v3/analyst-estimates/{ticker}?period=annual&apikey={apikey}',
        'quarterly': 'https://financialmodelingprep.com/api/v3/analyst-estimates/{ticker}?period=quarterly&apikey={apikey}'
    },
    'owner_earnings': {
        'no_period': 'https://financialmodelingprep.com/api/v3/owner-earnings/{ticker}?apikey={apikey}'
    },
    'score': {
        'no_period': 'https://financialmodelingprep.com/api/v3/score/{ticker}?apikey={apikey}'
    },
    'key_metrics_ttm': {
        'no_period': 'https://financialmodelingprep.com/api/v3/key-metrics-ttm/{ticker}?apikey={apikey}'
    },
    'ratios_ttm': {
        'no_period': 'https://financialmodelingprep.com/api/v3/ratios-ttm/{ticker}?apikey={apikey}'
    },
    'discounted_cash_flow': {
        'no_period': 'https://financialmodelingprep.com/api/v3/discounted-cash-flow/{ticker}?apikey={apikey}'
    },
    'advanced_dcf': {
        'no_period': 'https://financialmodelingprep.com/api/v3/advanced_discounted_cash_flow/{ticker}?apikey={apikey}'
    },
    'advanced_levered_dcf': {
        'no_period': 'https://financialmodelingprep.com/api/v3/advanced_levered_discounted_cash_flow/{ticker}?apikey={apikey}'
    },
    'rating': {
        'no_period': 'https://financialmodelingprep.com/api/v3/rating/{ticker}?apikey={apikey}'
    },
    'historical_rating': {
        'no_period': 'https://financialmodelingprep.com/api/v3/historical-rating/{ticker}?apikey={apikey}'
    },
    'historical_price_dividend': {
        'no_period': 'https://financialmodelingprep.com/api/v3/historical-price-full/stock_dividend/{ticker}?apikey={apikey}'
    },
    'historical_price_full': {
        'no_period': 'https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?apikey={apikey}'
    },
    'historical_sectors_performance': {
        'no_period': 'https://financialmodelingprep.com/api/v3/historical-sectors-performance?apikey={apikey}'
    },
    'employee_count': {
        'no_period': 'https://financialmodelingprep.com/api/v3/historical/employee_count?symbol={ticker}&apikey={apikey}'
    },
    'shares_float': {
        'no_period': 'https://financialmodelingprep.com/api/v3/shares_float?symbol={ticker}&apikey={apikey}'
    },
    'analyst_recommendations': {
        'no_period': 'https://financialmodelingprep.com/api/v3/analyst-stock-recommendations/{ticker}?apikey={apikey}'
    },
    'historical_market_cap': {
        'no_period': 'https://financialmodelingprep.com/api/v3/historical-market-capitalization/{ticker}?apikey={apikey}'
    },
    'earning_calendar': {
        'no_period': 'https://financialmodelingprep.com/api/v3/earning_calendar/{ticker}?apikey={apikey}'
    },
    'institutional_holder': {
        'no_period': 'https://financialmodelingprep.com/api/v3/institutional-holder/{ticker}?apikey={apikey}'
    },
    'etf_sector_weightings': {
        'no_period': 'https://financialmodelingprep.com/api/v3/etf-sector-weightings/{ticker}?apikey={apikey}'
    },
    'historical_price_eod': {
        'no_period': 'https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?apikey={apikey}'
    },
    'stock_price_change': {
        'no_period': 'https://financialmodelingprep.com/api/v3/stock-price-change/{ticker}?apikey={apikey}'
    },
    'insider_trading': {
        'all': 'https://financialmodelingprep.com/api/v3/insider-trading?symbol={ticker}&apikey={apikey}',
        'purchases': 'https://financialmodelingprep.com/api/v3/insider-trading?symbol={ticker}&transactionType=purchase&apikey={apikey}',
        'sales': 'https://financialmodelingprep.com/api/v3/insider-trading?symbol={ticker}&transactionType=sale&apikey={apikey}'
    },
    'technical_indicators': {
        'sma': 'https://financialmodelingprep.com/api/v3/technical_indicator/daily/{ticker}?type=sma&period=252&apikey={apikey}',
        'ema': 'https://financialmodelingprep.com/api/v3/technical_indicator/daily/{ticker}?type=ema&period=50&apikey={apikey}',
        'rsi': 'https://financialmodelingprep.com/api/v3/technical_indicator/daily/{ticker}?type=rsi&period=14&apikey={apikey}',
        'macd': 'https://financialmodelingprep.com/api/v3/technical_indicator/daily/{ticker}?type=macd&period=26&apikey={apikey}',
        'wma': 'https://financialmodelingprep.com/api/v3/technical_indicator/daily/{ticker}?type=wma&period=20&apikey={apikey}',
        'dema': 'https://financialmodelingprep.com/api/v3/technical_indicator/daily/{ticker}?type=dema&period=30&apikey={apikey}',
        'tema': 'https://financialmodelingprep.com/api/v3/technical_indicator/daily/{ticker}?type=tema&period=200&apikey={apikey}',
        'williams': 'https://financialmodelingprep.com/api/v3/technical_indicator/daily/{ticker}?type=williams&period=26&apikey={apikey}',
        'adx': 'https://financialmodelingprep.com/api/v3/technical_indicator/daily/{ticker}?type=adx&period=26&apikey={apikey}',
        'standarddeviation': 'https://financialmodelingprep.com/api/v3/technical_indicator/daily/{ticker}?type=standarddeviation&period=20&apikey={apikey}'
    }
}

def fetch_data(url):
    """
    Fetches data from the given URL using a GET request.

    This function performs an HTTP GET request to the specified URL, displays the URL for user verification,
    and returns the JSON response if successful. It handles errors by returning None for any issues.

    Args:
        url (str): The full URL to fetch data from.

    Returns:
        dict or list or None: The parsed JSON data if the request is successful (status code 200),
                              otherwise None.
    """
    print(f"Fetching data from: {url}")
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def fetch_income_statement(ticker, api_key, period):
    """
    Fetches comprehensive income statement data for the specified stock ticker from the Financial Modeling Prep API.

    This function retrieves detailed income statement information, including revenue, cost of goods sold, operating expenses,
    net income, earnings per share, and other key financial performance metrics. The data covers historical periods
    based on the specified timeframe (annual or quarterly) and is essential for fundamental analysis of a company's profitability.

    The function constructs the API URL using the centralized ENDPOINTS dictionary and delegates the actual HTTP request
    to the fetch_data function, ensuring consistent error handling and response processing across all fetch operations.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'AAPL' for Apple Inc.). Must be a valid symbol recognized by FMP API.
        api_key (str): The Financial Modeling Prep API key for authentication. Retrieved from environment variables.
        period (str): The reporting period for data retrieval. Must be either 'annual' or 'quarterly'.

    Returns:
        list[dict] or None: A list of dictionaries containing income statement data for each historical period,
        where each dictionary represents one period's financial metrics. Returns None if the API request fails
        or encounters an error.

    Raises:
        ValueError: If the period parameter is not 'annual' or 'quarterly'.
        KeyError: If the ticker or period key is not found in the ENDPOINTS dictionary.

    Usage:
        # Fetch annual income statement for Apple
        income_data = fetch_income_statement('AAPL', 'your_api_key', 'annual')
        if income_data:
            for period in income_data:
                print(f"Year: {period.get('calendarYear')}, Revenue: {period.get('revenue')}")

    Integration:
        This function integrates with the overall fmp_fetcher system by utilizing the ENDPOINTS['income_statement']
        URL template and the fetch_data helper function, promoting code reusability and maintainability.
    """
    
    url = ENDPOINTS['income_statement'][period].format(ticker=ticker, apikey=api_key)
    return fetch_data(url)

def fetch_balance_sheet(ticker, api_key, period):
    """
    Fetches comprehensive balance sheet data for the specified stock ticker from the Financial Modeling Prep API.

    This function retrieves detailed balance sheet information, including total assets, current assets, liabilities,
    shareholder equity, cash equivalents, and other key financial position metrics. The data provides a snapshot
    of the company's financial health at specific points in time based on the selected period (annual or quarterly).

    The function leverages the centralized ENDPOINTS dictionary for URL construction and relies on the fetch_data
    function for HTTP request handling, maintaining consistency with other fetch operations in the system.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'MSFT' for Microsoft Corporation). Must be valid for FMP API.
        api_key (str): The Financial Modeling Prep API key for secure authentication.
        period (str): The reporting period for data retrieval. Accepts 'annual' or 'quarterly' only.

    Returns:
        list[dict] or None: A list of dictionaries with balance sheet data for each historical period,
        each dictionary containing financial position metrics. Returns None on API failure or error.

    Raises:
        ValueError: If period is not 'annual' or 'quarterly'.
        KeyError: If ticker or period is invalid in ENDPOINTS.

    Usage:
        # Get quarterly balance sheet data for Microsoft
        balance_data = fetch_balance_sheet('MSFT', 'your_api_key', 'quarterly')
        if balance_data:
            for entry in balance_data:
                total_assets = entry.get('totalAssets', 0)
                total_liabilities = entry.get('totalLiabilities', 0)
                equity = total_assets - total_liabilities

    Integration:
        Part of the fmp_fetcher module's fetch functions, using ENDPOINTS['balance_sheet'] and fetch_data
        for modular, maintainable API interactions.
    """
    
    url = ENDPOINTS['balance_sheet'][period].format(ticker=ticker, apikey=api_key)
    return fetch_data(url)

def fetch_cash_flow_statement(ticker, api_key, period):
    """
    Fetches detailed cash flow statement data for the specified stock ticker from the Financial Modeling Prep API.

    This function retrieves comprehensive cash flow information, including operating cash flows, investing activities,
    financing activities, net cash changes, and other liquidity-related metrics. The data is crucial for analyzing
    a company's cash generation, investment patterns, and financing decisions over the selected time periods.

    Utilizes the ENDPOINTS dictionary for consistent URL formatting and delegates to fetch_data for error-resilient
    HTTP requests, aligning with the module's design for standardized API interactions.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'GOOGL' for Alphabet Inc.). Valid FMP API symbol required.
        api_key (str): The Financial Modeling Prep API key for authentication.
        period (str): The reporting period. Restricted to 'annual' or 'quarterly'.

    Returns:
        list[dict] or None: A list of dictionaries containing cash flow metrics for each period,
        or None if the request fails.

    Raises:
        ValueError: For invalid period values.
        KeyError: If endpoint keys are not found.

    Usage:
        # Retrieve annual cash flow data for Alphabet
        cashflow_data = fetch_cash_flow_statement('GOOGL', 'your_api_key', 'annual')
        if cashflow_data:
            for period in cashflow_data:
                operating_cash = period.get('netCashProvidedByOperatingActivities', 0)

    Integration:
        Integrates with the fmp_fetcher system via ENDPOINTS['cash_flow_statement'] and fetch_data,
        supporting modular financial data retrieval.
    """
    
    url = ENDPOINTS['cash_flow_statement'][period].format(ticker=ticker, apikey=api_key)
    return fetch_data(url)

def fetch_ratios(ticker, api_key, period):
    """
    Fetches key financial ratios data for the specified stock ticker from the Financial Modeling Prep API.

    This function retrieves important valuation and performance ratios including price-to-earnings (P/E), price-to-book (P/B),
    debt-to-equity, return on equity (ROE), gross margins, and other analytical metrics. These ratios are essential
    for comparative analysis and valuation assessments across different periods.

    Builds on the ENDPOINTS['ratios'] template and fetch_data function to ensure uniform API handling
    within the fmp_fetcher module.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'TSLA' for Tesla Inc.). Must be valid for FMP API.
        api_key (str): The Financial Modeling Prep API key.
        period (str): The period for ratio calculation. 'annual' or 'quarterly' only.

    Returns:
        list[dict] or None: A list of dictionaries with ratio data per period, or None on failure.

    Raises:
        ValueError: If period is invalid.
        KeyError: For missing endpoint keys.

    Usage:
        # Get annual ratios for Tesla
        ratios_data = fetch_ratios('TSLA', 'your_api_key', 'annual')
        if ratios_data:
            pe_ratio = ratios_data[0].get('priceEarningsRatio', 'N/A')

    Integration:
        Part of the period-dependent fetch functions, using ENDPOINTS and fetch_data for consistency.
    """
    
    url = ENDPOINTS['ratios'][period].format(ticker=ticker, apikey=api_key)
    return fetch_data(url)

def fetch_enterprise_values(ticker, api_key, period):
    """
    Fetches enterprise value metrics for the specified stock ticker from the Financial Modeling Prep API.

    This function retrieves enterprise value-related data including market capitalization, enterprise value,
    EV/EBITDA ratios, and other comprehensive valuation metrics that incorporate debt and cash positions
    for a more complete picture of company value.

    Relies on ENDPOINTS['enterprise_values'] and the fetch_data utility for standardized API access.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'NVDA' for NVIDIA Corporation).
        api_key (str): The FMP API key for authentication.
        period (str): The reporting period. 'annual' or 'quarterly'.

    Returns:
        list[dict] or None: Enterprise value data per period, or None if error.

    Raises:
        ValueError: For invalid period.
        KeyError: If endpoint not found.

    Usage:
        # Fetch enterprise values for NVIDIA
        ev_data = fetch_enterprise_values('NVDA', 'your_api_key', 'annual')

    Integration:
        Contributes to the suite of fetch functions, maintaining system consistency.
    """
    
    url = ENDPOINTS['enterprise_values'][period].format(ticker=ticker, apikey=api_key)
    return fetch_data(url)

def fetch_financial_growth(ticker, api_key, period):
    """
    Fetches financial growth metrics for the specified stock ticker from the Financial Modeling Prep API.

    This function retrieves year-over-year growth rates for key financial metrics including revenue growth,
    earnings growth, asset growth, and other performance indicators. Growth data is vital for trend analysis
    and forecasting company performance.

    Uses ENDPOINTS['financial_growth'] and fetch_data for consistent implementation.

    Parameters:
        ticker (str): The stock ticker symbol.
        api_key (str): The FMP API key.
        period (str): 'annual' or 'quarterly'.

    Returns:
        list[dict] or None: Growth data per period.

    Raises:
        ValueError: Invalid period.
        KeyError: Endpoint error.

    Usage:
        growth_data = fetch_financial_growth('AMZN', 'your_api_key', 'annual')

    Integration:
        Part of the fetch functions suite.
    """
    
    url = ENDPOINTS['financial_growth'][period].format(ticker=ticker, apikey=api_key)
    return fetch_data(url)

def fetch_balance_sheet_growth(ticker, api_key, period):
    """
    Fetches balance sheet-specific growth rates for the specified stock ticker from the Financial Modeling Prep API.

    This function provides growth percentages for balance sheet components such as asset growth, liability changes,
    equity increases, and other balance sheet item variations. Useful for analyzing capital structure evolution.

    Leverages ENDPOINTS['balance_sheet_growth'] and fetch_data.

    Parameters:
        ticker (str): Stock ticker symbol.
        api_key (str): FMP API key.
        period (str): 'annual' or 'quarterly'.

    Returns:
        list[dict] or None: Balance sheet growth data.

    Raises:
        ValueError: Invalid period.
        KeyError: Endpoint issue.

    Usage:
        bs_growth = fetch_balance_sheet_growth('JPM', 'your_api_key', 'annual')

    Integration:
        Consistent with other period-dependent fetch functions.
    """
    url = ENDPOINTS['balance_sheet_growth'][period].format(ticker=ticker, apikey=api_key)
    return fetch_data(url)

def fetch_income_statement_growth(ticker, api_key, period):
    """
    Fetches income statement growth rates for the specified stock ticker from the Financial Modeling Prep API.

    Provides growth percentages for income statement items like revenue growth, expense changes, and profit margins.
    Essential for profitability trend analysis.

    Uses ENDPOINTS['income_statement_growth'] and fetch_data.

    Parameters:
        ticker (str): Stock ticker.
        api_key (str): FMP API key.
        period (str): 'annual' or 'quarterly'.

    Returns:
        list[dict] or None: Income statement growth data.

    Raises:
        ValueError: Invalid period.
        KeyError: Endpoint error.

    Usage:
        is_growth = fetch_income_statement_growth('WMT', 'your_api_key', 'annual')

    Integration:
        Aligns with the fetch functions design.
    """
    url = ENDPOINTS['income_statement_growth'][period].format(ticker=ticker, apikey=api_key)
    return fetch_data(url)

def fetch_cash_flow_statement_growth(ticker, api_key, period):
    """
    Fetches cash flow statement growth rates for the specified stock ticker from the Financial Modeling Prep API.

    Retrieves growth percentages for cash flow components such as operating cash flow growth, investing activity changes,
    and financing cash flow trends. Critical for liquidity and cash management analysis.

    Utilizes ENDPOINTS['cash_flow_statement_growth'] and fetch_data.

    Parameters:
        ticker (str): Stock ticker symbol.
        api_key (str): FMP API key.
        period (str): 'annual' or 'quarterly'.

    Returns:
        list[dict] or None: Cash flow growth data.

    Raises:
        ValueError: Invalid period.
        KeyError: Endpoint not found.

    Usage:
        cf_growth = fetch_cash_flow_statement_growth('BAC', 'your_api_key', 'annual')

    Integration:
        Maintains consistency within the fetch functions.
    """
    url = ENDPOINTS['cash_flow_statement_growth'][period].format(ticker=ticker, apikey=api_key)
    return fetch_data(url)

def fetch_key_metrics(ticker, api_key, period):
    """
    Fetches key financial metrics for the specified stock ticker from the Financial Modeling Prep API.

    Provides essential valuation and performance metrics such as market capitalization, P/E ratio, dividend yield,
    ROE, ROA, and other critical indicators for comprehensive company evaluation.

    Employs ENDPOINTS['key_metrics'] and fetch_data for reliable data retrieval.

    Parameters:
        ticker (str): Stock ticker symbol.
        api_key (str): FMP API key.
        period (str): 'annual' or 'quarterly'.

    Returns:
        list[dict] or None: Key metrics data per period.

    Raises:
        ValueError: Invalid period.
        KeyError: Endpoint error.

    Usage:
        metrics = fetch_key_metrics('META', 'your_api_key', 'annual')

    Integration:
        Part of the period-based fetch functions suite.
    """
    url = ENDPOINTS['key_metrics'][period].format(ticker=ticker, apikey=api_key)
    return fetch_data(url)

def fetch_analyst_estimates(ticker, api_key, period):
    """
    Fetches analyst estimates and forecasts for the specified stock ticker from the Financial Modeling Prep API.

    Retrieves consensus analyst estimates for revenue, earnings, EPS, and other forward-looking metrics,
    providing insights into market expectations and future performance projections.

    Leverages ENDPOINTS['analyst_estimates'] and fetch_data for consistent API interaction.

    Parameters:
        ticker (str): Stock ticker symbol.
        api_key (str): FMP API key.
        period (str): 'annual' or 'quarterly'.

    Returns:
        list[dict] or None: Analyst estimates data.

    Raises:
        ValueError: Invalid period.
        KeyError: Endpoint not found.

    Usage:
        estimates = fetch_analyst_estimates('NFLX', 'your_api_key', 'annual')

    Integration:
        Completes the set of period-dependent fetch functions in the fmp_fetcher module.
    """
    url = ENDPOINTS['analyst_estimates'][period].format(ticker=ticker, apikey=api_key)
    return fetch_data(url)

def fetch_owner_earnings(ticker, api_key):
    """
    Fetches owner earnings data for the specified stock ticker from the Financial Modeling Prep API.

    Owner earnings, a concept popularized by Warren Buffett, represent the cash flow available to shareholders
    after accounting for capital expenditures required to maintain the company's current level of operations.
    This metric provides insight into the sustainable cash generation capacity of the business.

    The function constructs the API URL using the centralized ENDPOINTS dictionary and delegates the actual HTTP request
    to the fetch_data function, ensuring consistent error handling and response processing across all fetch operations.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'AAPL' for Apple Inc.). Must be a valid symbol recognized by FMP API.
        api_key (str): The Financial Modeling Prep API key for authentication. Retrieved from environment variables.

    Returns:
        dict or None: A dictionary containing owner earnings and related cash flow metrics if the request is successful,
        otherwise None. The dictionary typically includes keys like 'ownerEarnings', 'freeCashFlow', and calculation components.

    Raises:
        KeyError: If the ticker or endpoint key is not found in the ENDPOINTS dictionary.

    Usage:
        # Fetch owner earnings for Apple
        owner_data = fetch_owner_earnings('AAPL', 'your_api_key')
        if owner_data:
            earnings = owner_data.get('ownerEarnings', 0)
            print(f"Owner earnings for AAPL: {earnings}")

    Integration:
        This function integrates with the overall fmp_fetcher system by utilizing the ENDPOINTS['owner_earnings']
        URL template and the fetch_data helper function, promoting code reusability and maintainability.
    """
    url = ENDPOINTS['owner_earnings']['no_period'].format(ticker=ticker, apikey=api_key)
    return fetch_data(url)

def fetch_score(ticker, api_key):
    """
    Fetches financial score data for the specified stock ticker from the Financial Modeling Prep API.

    The score represents a composite financial health metric calculated by FMP, incorporating various
    fundamental indicators to provide an overall assessment of the company's financial strength and stability.
    This metric is useful for quick evaluations and comparative analysis across different stocks.

    The function constructs the API URL using the centralized ENDPOINTS dictionary and delegates the actual HTTP request
    to the fetch_data function, ensuring consistent error handling and response processing across all fetch operations.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'MSFT' for Microsoft Corporation). Must be a valid symbol recognized by FMP API.
        api_key (str): The Financial Modeling Prep API key for authentication. Retrieved from environment variables.

    Returns:
        dict or None: A dictionary containing the financial score and related metrics if the request is successful,
        otherwise None. The dictionary typically includes keys like 'score', 'rating', and component factors.

    Raises:
        KeyError: If the ticker or endpoint key is not found in the ENDPOINTS dictionary.

    Usage:
        # Fetch financial score for Microsoft
        score_data = fetch_score('MSFT', 'your_api_key')
        if score_data:
            company_score = score_data.get('score', 0)
            print(f"Financial score for MSFT: {company_score}")

    Integration:
        This function integrates with the overall fmp_fetcher system by utilizing the ENDPOINTS['score']
        URL template and the fetch_data helper function, promoting code reusability and maintainability.
    """
    url = ENDPOINTS['score']['no_period'].format(ticker=ticker, apikey=api_key)
    return fetch_data(url)

def fetch_key_metrics_ttm(ticker, api_key):
    """
    Fetches key financial metrics on a trailing twelve months (TTM) basis for the specified stock ticker from the Financial Modeling Prep API.

    TTM metrics provide the most recent twelve months of financial performance data, offering a current snapshot
    of the company's valuation and operational metrics without waiting for quarterly or annual reports.
    This includes metrics like P/E ratio, ROE, ROA, dividend yield, and market capitalization calculated on a TTM basis.

    The function constructs the API URL using the centralized ENDPOINTS dictionary and delegates the actual HTTP request
    to the fetch_data function, ensuring consistent error handling and response processing across all fetch operations.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'TSLA' for Tesla Inc.). Must be a valid symbol recognized by FMP API.
        api_key (str): The Financial Modeling Prep API key for authentication. Retrieved from environment variables.

    Returns:
        dict or None: A dictionary containing TTM key metrics if the request is successful,
        otherwise None. The dictionary includes various valuation and performance indicators.

    Raises:
        KeyError: If the ticker or endpoint key is not found in the ENDPOINTS dictionary.

    Usage:
        # Fetch TTM key metrics for Tesla
        ttm_metrics = fetch_key_metrics_ttm('TSLA', 'your_api_key')
        if ttm_metrics:
            pe_ttm = ttm_metrics.get('peRatioTTM', 0)
            print(f"P/E TTM for TSLA: {pe_ttm}")

    Integration:
        This function integrates with the overall fmp_fetcher system by utilizing the ENDPOINTS['key_metrics_ttm']
        URL template and the fetch_data helper function, promoting code reusability and maintainability.
    """
    url = ENDPOINTS['key_metrics_ttm']['no_period'].format(ticker=ticker, apikey=api_key)
    return fetch_data(url)

def fetch_ratios_ttm(ticker, api_key):
    """
    Fetches key financial ratios on a trailing twelve months (TTM) basis for the specified stock ticker from the Financial Modeling Prep API.

    TTM ratios provide the most current financial ratios calculated over the last twelve months, offering
    up-to-date valuation and performance metrics like P/E, P/B, debt-to-equity, and margins without seasonal distortions.
    These ratios are essential for real-time comparative analysis and investment decision-making.

    The function constructs the API URL using the centralized ENDPOINTS dictionary and delegates the actual HTTP request
    to the fetch_data function, ensuring consistent error handling and response processing across all fetch operations.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'NVDA' for NVIDIA Corporation). Must be a valid symbol recognized by FMP API.
        api_key (str): The Financial Modeling Prep API key for authentication. Retrieved from environment variables.

    Returns:
        dict or None: A dictionary containing TTM financial ratios if the request is successful,
        otherwise None. The dictionary includes various ratio metrics for valuation and performance analysis.

    Raises:
        KeyError: If the ticker or endpoint key is not found in the ENDPOINTS dictionary.

    Usage:
        # Fetch TTM ratios for NVIDIA
        ttm_ratios = fetch_ratios_ttm('NVDA', 'your_api_key')
        if ttm_ratios:
            pe_ttm = ttm_ratios.get('priceEarningsRatioTTM', 0)
            print(f"P/E TTM for NVDA: {pe_ttm}")

    Integration:
        This function integrates with the overall fmp_fetcher system by utilizing the ENDPOINTS['ratios_ttm']
        URL template and the fetch_data helper function, promoting code reusability and maintainability.
    """
    url = ENDPOINTS['ratios_ttm']['no_period'].format(ticker=ticker, apikey=api_key)
    return fetch_data(url)

def fetch_discounted_cash_flow(ticker, api_key):
    """
    Fetches discounted cash flow (DCF) valuation data for the specified stock ticker from the Financial Modeling Prep API.

    DCF analysis estimates the intrinsic value of a company by projecting its future free cash flows and discounting them
    back to their present value. This method provides an estimate of what the stock should be worth based on fundamental
    cash flow generation rather than market sentiment. The data includes DCF value, current stock price, and valuation metrics.

    The function constructs the API URL using the centralized ENDPOINTS dictionary and delegates the actual HTTP request
    to the fetch_data function, ensuring consistent error handling and response processing across all fetch operations.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'META' for Meta Platforms Inc.). Must be a valid symbol recognized by FMP API.
        api_key (str): The Financial Modeling Prep API key for authentication. Retrieved from environment variables.

    Returns:
        dict or None: A dictionary containing DCF valuation metrics if the request is successful,
        otherwise None. The dictionary typically includes 'dcf', 'stockPrice', and 'valuation' keys.

    Raises:
        KeyError: If the ticker or endpoint key is not found in the ENDPOINTS dictionary.

    Usage:
        # Fetch DCF valuation for Meta
        dcf_data = fetch_discounted_cash_flow('META', 'your_api_key')
        if dcf_data:
            intrinsic_value = dcf_data.get('dcf', 0)
            current_price = dcf_data.get('stockPrice', 0)
            print(f"DCF value for META: {intrinsic_value}, Current price: {current_price}")

    Integration:
        This function integrates with the overall fmp_fetcher system by utilizing the ENDPOINTS['discounted_cash_flow']
        URL template and the fetch_data helper function, promoting code reusability and maintainability.
    """
    url = ENDPOINTS['discounted_cash_flow']['no_period'].format(ticker=ticker, apikey=api_key)
    return fetch_data(url)

def fetch_advanced_dcf(ticker, api_key):
    """
    Fetches advanced discounted cash flow (DCF) valuation data for the specified stock ticker from the Financial Modeling Prep API.

    The advanced DCF model incorporates more sophisticated assumptions and methodologies compared to the standard DCF,
    potentially including variable growth rates, different discount rates, or more detailed cash flow projections.
    This provides a comprehensive intrinsic valuation estimate for more accurate investment analysis.

    The function constructs the API URL using the centralized ENDPOINTS dictionary and delegates the actual HTTP request
    to the fetch_data function, ensuring consistent error handling and response processing across all fetch operations.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'AMZN' for Amazon.com Inc.). Must be a valid symbol recognized by FMP API.
        api_key (str): The Financial Modeling Prep API key for authentication. Retrieved from environment variables.

    Returns:
        dict or None: A dictionary containing advanced DCF valuation metrics if the request is successful,
        otherwise None. The dictionary includes detailed valuation components and assumptions.

    Raises:
        KeyError: If the ticker or endpoint key is not found in the ENDPOINTS dictionary.

    Usage:
        # Fetch advanced DCF for Amazon
        adv_dcf = fetch_advanced_dcf('AMZN', 'your_api_key')
        if adv_dcf:
            advanced_value = adv_dcf.get('dcf', 0)
            print(f"Advanced DCF value for AMZN: {advanced_value}")

    Integration:
        This function integrates with the overall fmp_fetcher system by utilizing the ENDPOINTS['advanced_dcf']
        URL template and the fetch_data helper function, promoting code reusability and maintainability.
    """
    url = ENDPOINTS['advanced_dcf']['no_period'].format(ticker=ticker, apikey=api_key)
    return fetch_data(url)

def fetch_advanced_levered_dcf(ticker, api_key):
    """
    Fetches advanced levered discounted cash flow (DCF) valuation data for the specified stock ticker from the Financial Modeling Prep API.

    The levered DCF model accounts for the company's capital structure by using levered free cash flow (FCF to equity)
    and incorporates tax shields from debt. This advanced model provides a more accurate valuation for leveraged companies
    by considering the benefits and costs of debt financing in the cash flow projections.

    The function constructs the API URL using the centralized ENDPOINTS dictionary and delegates the actual HTTP request
    to the fetch_data function, ensuring consistent error handling and response processing across all fetch operations.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'JPM' for JPMorgan Chase & Co.). Must be a valid symbol recognized by FMP API.
        api_key (str): The Financial Modeling Prep API key for authentication. Retrieved from environment variables.

    Returns:
        dict or None: A dictionary containing advanced levered DCF valuation metrics if the request is successful,
        otherwise None. The dictionary includes equity valuation and capital structure considerations.

    Raises:
        KeyError: If the ticker or endpoint key is not found in the ENDPOINTS dictionary.

    Usage:
        # Fetch advanced levered DCF for JPMorgan
        levered_dcf = fetch_advanced_levered_dcf('JPM', 'your_api_key')
        if levered_dcf:
            levered_value = levered_dcf.get('dcf', 0)
            print(f"Advanced levered DCF value for JPM: {levered_value}")

    Integration:
        This function integrates with the overall fmp_fetcher system by utilizing the ENDPOINTS['advanced_levered_dcf']
        URL template and the fetch_data helper function, promoting code reusability and maintainability.
    """
    url = ENDPOINTS['advanced_levered_dcf']['no_period'].format(ticker=ticker, apikey=api_key)
    return fetch_data(url)

def fetch_rating(ticker, api_key):
    """
    Fetches current rating and recommendation data for the specified stock ticker from the Financial Modeling Prep API.

    This endpoint provides the latest analyst consensus rating and recommendation for the stock, including
    buy/hold/sell ratings, target prices, and rating distributions. This information is crucial for understanding
    market sentiment and analyst expectations for the company's stock performance.

    The function constructs the API URL using the centralized ENDPOINTS dictionary and delegates the actual HTTP request
    to the fetch_data function, ensuring consistent error handling and response processing across all fetch operations.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'NFLX' for Netflix Inc.). Must be a valid symbol recognized by FMP API.
        api_key (str): The Financial Modeling Prep API key for authentication. Retrieved from environment variables.

    Returns:
        dict or None: A dictionary containing rating and recommendation data if the request is successful,
        otherwise None. The dictionary typically includes 'rating', 'ratingScore', 'recommendation', and target price information.

    Raises:
        KeyError: If the ticker or endpoint key is not found in the ENDPOINTS dictionary.

    Usage:
        # Fetch rating for Netflix
        rating_data = fetch_rating('NFLX', 'your_api_key')
        if rating_data:
            recommendation = rating_data.get('recommendation', 'N/A')
            rating_score = rating_data.get('ratingScore', 0)
            print(f"Recommendation for NFLX: {recommendation}, Score: {rating_score}")

    Integration:
        This function integrates with the overall fmp_fetcher system by utilizing the ENDPOINTS['rating']
        URL template and the fetch_data helper function, promoting code reusability and maintainability.
    """
    url = ENDPOINTS['rating']['no_period'].format(ticker=ticker, apikey=api_key)
    return fetch_data(url)

def fetch_historical_rating(ticker, api_key):
    """
    Fetches historical rating and recommendation data for the specified stock ticker from the Financial Modeling Prep API.

    This endpoint provides a time series of analyst ratings and recommendations for the stock, showing how
    sentiment and analyst opinions have evolved over time. This historical perspective is valuable for
    understanding rating trends and analyst consensus changes.

    The function constructs the API URL using the centralized ENDPOINTS dictionary and delegates the actual HTTP request
    to the fetch_data function, ensuring consistent error handling and response processing across all fetch operations.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'GOOGL' for Alphabet Inc.). Must be a valid symbol recognized by FMP API.
        api_key (str): The Financial Modeling Prep API key for authentication. Retrieved from environment variables.

    Returns:
        list[dict] or None: A list of dictionaries containing historical rating data for each period if the request is successful,
        otherwise None. Each dictionary represents a historical rating with date, rating, and recommendation information.

    Raises:
        KeyError: If the ticker or endpoint key is not found in the ENDPOINTS dictionary.

    Usage:
        # Fetch historical ratings for Alphabet
        hist_ratings = fetch_historical_rating('GOOGL', 'your_api_key')
        if hist_ratings:
            for rating in hist_ratings[:5]:  # Show first 5
                date = rating.get('date', 'N/A')
                rec = rating.get('recommendation', 'N/A')
                print(f"{date}: {rec}")

    Integration:
        This function integrates with the overall fmp_fetcher system by utilizing the ENDPOINTS['historical_rating']
        URL template and the fetch_data helper function, promoting code reusability and maintainability.
    """
    url = ENDPOINTS['historical_rating']['no_period'].format(ticker=ticker, apikey=api_key)
    return fetch_data(url)

def fetch_historical_price_dividend(ticker, api_key):
    """
    Fetches historical price data including dividend information for the specified stock ticker from the Financial Modeling Prep API.

    This endpoint provides a comprehensive historical record of stock prices along with dividend payments and dates.
    This data is essential for calculating total returns (price appreciation + dividends) and analyzing dividend history,
    which is crucial for income-focused investment strategies.

    The function constructs the API URL using the centralized ENDPOINTS dictionary and delegates the actual HTTP request
    to the fetch_data function, ensuring consistent error handling and response processing across all fetch operations.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'JNJ' for Johnson & Johnson). Must be a valid symbol recognized by FMP API.
        api_key (str): The Financial Modeling Prep API key for authentication. Retrieved from environment variables.

    Returns:
        list[dict] or None: A list of dictionaries containing historical price and dividend data for each trading day if the request is successful,
        otherwise None. Each dictionary includes date, price, and dividend information.

    Raises:
        KeyError: If the ticker or endpoint key is not found in the ENDPOINTS dictionary.

    Usage:
        # Fetch historical price and dividend data for Johnson & Johnson
        hist_price_div = fetch_historical_price_dividend('JNJ', 'your_api_key')
        if hist_price_div:
            total_dividends = sum(item.get('dividend', 0) for item in hist_price_div if item.get('dividend', 0) > 0)
            print(f"Total dividends paid by JNJ: {total_dividends}")

    Integration:
        This function integrates with the overall fmp_fetcher system by utilizing the ENDPOINTS['historical_price_dividend']
        URL template and the fetch_data helper function, promoting code reusability and maintainability.
    """
    url = ENDPOINTS['historical_price_dividend']['no_period'].format(ticker=ticker, apikey=api_key)
    data = fetch_data(url)
    if data and isinstance(data, dict) and 'historical' in data:
        return data['historical']
    return data

def fetch_historical_price_full(ticker, api_key):
    """
    Fetches comprehensive historical price data for the specified stock ticker from the Financial Modeling Prep API.

    This endpoint provides complete historical daily price information including open, high, low, close prices,
    volume, and adjusted prices. This data is fundamental for technical analysis, backtesting trading strategies,
    and understanding long-term price movements and volatility patterns.

    The function constructs the API URL using the centralized ENDPOINTS dictionary and delegates the actual HTTP request
    to the fetch_data function, ensuring consistent error handling and response processing across all fetch operations.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'SPY' for SPDR S&P 500 ETF Trust). Must be a valid symbol recognized by FMP API.
        api_key (str): The Financial Modeling Prep API key for authentication. Retrieved from environment variables.

    Returns:
        list[dict] or None: A list of dictionaries containing daily historical price data if the request is successful,
        otherwise None. Each dictionary includes date, open, high, low, close, volume, and adjusted prices.

    Raises:
        KeyError: If the ticker or endpoint key is not found in the ENDPOINTS dictionary.

    Usage:
        # Fetch full historical prices for SPY
        hist_prices = fetch_historical_price_full('SPY', 'your_api_key')
        if hist_prices:
            latest = hist_prices[0]  # Most recent first
            close_price = latest.get('close', 0)
            volume = latest.get('volume', 0)
            print(f"Latest SPY close: {close_price}, Volume: {volume}")

    Integration:
        This function integrates with the overall fmp_fetcher system by utilizing the ENDPOINTS['historical_price_full']
        URL template and the fetch_data helper function, promoting code reusability and maintainability.
    """
    url = ENDPOINTS['historical_price_full']['no_period'].format(ticker=ticker, apikey=api_key)
    data = fetch_data(url)
    if data and isinstance(data, dict) and 'historical' in data:
        return data['historical']
    return data

def fetch_historical_sectors_performance(api_key):
    """
    Fetches historical performance data for all market sectors from the Financial Modeling Prep API.

    This endpoint provides time series data showing how different market sectors (e.g., Technology, Healthcare, Financials)
    have performed over time. This information is valuable for sector rotation strategies, portfolio diversification,
    and understanding which sectors are leading or lagging the market.

    The function constructs the API URL using the centralized ENDPOINTS dictionary and delegates the actual HTTP request
    to the fetch_data function, ensuring consistent error handling and response processing across all fetch operations.

    Parameters:
        api_key (str): The Financial Modeling Prep API key for authentication. Retrieved from environment variables.

    Returns:
        list[dict] or None: A list of dictionaries containing sector performance data for each historical period if the request is successful,
        otherwise None. Each dictionary includes sector names and their performance metrics over time.

    Raises:
        KeyError: If the endpoint key is not found in the ENDPOINTS dictionary.

    Usage:
        # Fetch historical sector performance
        sector_perf = fetch_historical_sectors_performance('your_api_key')
        if sector_perf:
            for period in sector_perf[:5]:  # Show first 5 periods
                date = period.get('date', 'N/A')
                tech_perf = period.get('Technology', 'N/A')
                print(f"{date}: Technology sector performance: {tech_perf}")

    Integration:
        This function integrates with the overall fmp_fetcher system by utilizing the ENDPOINTS['historical_sectors_performance']
        URL template and the fetch_data helper function, promoting code reusability and maintainability.
    """
    url = ENDPOINTS['historical_sectors_performance']['no_period'].format(apikey=api_key)
    return fetch_data(url)

def fetch_employee_count(ticker, api_key):
    """
    Fetches historical employee count data for the specified stock ticker from the Financial Modeling Prep API.

    This endpoint provides time series data of the company's workforce size over time, which is important for
    analyzing growth patterns, operational efficiency, and scalability. Changes in employee count can indicate
    business expansion, contraction, or restructuring.

    The function constructs the API URL using the centralized ENDPOINTS dictionary and delegates the actual HTTP request
    to the fetch_data function, ensuring consistent error handling and response processing across all fetch operations.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'WMT' for Walmart Inc.). Must be a valid symbol recognized by FMP API.
        api_key (str): The Financial Modeling Prep API key for authentication. Retrieved from environment variables.

    Returns:
        list[dict] or None: A list of dictionaries containing historical employee count data if the request is successful,
        otherwise None. Each dictionary includes date and employee count information.

    Raises:
        KeyError: If the ticker or endpoint key is not found in the ENDPOINTS dictionary.

    Usage:
        # Fetch employee count history for Walmart
        emp_count = fetch_employee_count('WMT', 'your_api_key')
        if emp_count:
            latest = emp_count[0]  # Most recent first
            count = latest.get('employeeCount', 0)
            date = latest.get('date', 'N/A')
            print(f"WMT employee count as of {date}: {count}")

    Integration:
        This function integrates with the overall fmp_fetcher system by utilizing the ENDPOINTS['employee_count']
        URL template and the fetch_data helper function, promoting code reusability and maintainability.
    """
    url = ENDPOINTS['employee_count']['no_period'].format(ticker=ticker, apikey=api_key)
    return fetch_data(url)

def fetch_shares_float(ticker, api_key):
    """
    Fetches shares float data for the specified stock ticker from the Financial Modeling Prep API.

    The float represents the number of shares available for trading by the public, excluding shares held by
    insiders, major shareholders, and restricted stock. This metric is important for understanding liquidity,
    short squeeze potential, and institutional ownership analysis.

    The function constructs the API URL using the centralized ENDPOINTS dictionary and delegates the actual HTTP request
    to the fetch_data function, ensuring consistent error handling and response processing across all fetch operations.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'GME' for GameStop Corp.). Must be a valid symbol recognized by FMP API.
        api_key (str): The Financial Modeling Prep API key for authentication. Retrieved from environment variables.

    Returns:
        dict or None: A dictionary containing shares float information if the request is successful,
        otherwise None. The dictionary typically includes 'floatShares' and related float metrics.

    Raises:
        KeyError: If the ticker or endpoint key is not found in the ENDPOINTS dictionary.

    Usage:
        # Fetch shares float for GameStop
        float_data = fetch_shares_float('GME', 'your_api_key')
        if float_data:
            float_shares = float_data.get('floatShares', 0)
            print(f"GME float shares: {float_shares}")

    Integration:
        This function integrates with the overall fmp_fetcher system by utilizing the ENDPOINTS['shares_float']
        URL template and the fetch_data helper function, promoting code reusability and maintainability.
    """
    url = ENDPOINTS['shares_float']['no_period'].format(ticker=ticker, apikey=api_key)
    return fetch_data(url)

def fetch_analyst_recommendations(ticker, api_key):
    """
    Fetches detailed analyst stock recommendations data for the specified stock ticker from the Financial Modeling Prep API.

    This endpoint provides comprehensive analyst recommendations including buy/sell/hold ratings from multiple
    analysts, target prices, and consensus information. This data is essential for understanding market sentiment
    and making informed investment decisions based on professional analysis.

    The function constructs the API URL using the centralized ENDPOINTS dictionary and delegates the actual HTTP request
    to the fetch_data function, ensuring consistent error handling and response processing across all fetch operations.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'DIS' for The Walt Disney Company). Must be a valid symbol recognized by FMP API.
        api_key (str): The Financial Modeling Prep API key for authentication. Retrieved from environment variables.

    Returns:
        list[dict] or None: A list of dictionaries containing analyst recommendation data if the request is successful,
        otherwise None. Each dictionary includes analyst details, ratings, target prices, and dates.

    Raises:
        KeyError: If the ticker or endpoint key is not found in the ENDPOINTS dictionary.

    Usage:
        # Fetch analyst recommendations for Disney
        recs = fetch_analyst_recommendations('DIS', 'your_api_key')
        if recs:
            buy_count = sum(1 for rec in recs if rec.get('recommendation') == 'Buy')
            total_analysts = len(recs)
            print(f"DIS: {buy_count}/{total_analysts} analysts recommend Buy")

    Integration:
        This function integrates with the overall fmp_fetcher system by utilizing the ENDPOINTS['analyst_recommendations']
        URL template and the fetch_data helper function, promoting code reusability and maintainability.
    """
    url = ENDPOINTS['analyst_recommendations']['no_period'].format(ticker=ticker, apikey=api_key)
    return fetch_data(url)

def fetch_historical_market_cap(ticker, api_key):
    """
    Fetches historical market capitalization data for the specified stock ticker from the Financial Modeling Prep API.

    This endpoint provides time series data of the company's market value (share price × shares outstanding)
    over time. Market cap history is crucial for analyzing company growth, valuation trends, and market positioning
    relative to peers and indices.

    The function constructs the API URL using the centralized ENDPOINTS dictionary and delegates the actual HTTP request
    to the fetch_data function, ensuring consistent error handling and response processing across all fetch operations.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'MSFT' for Microsoft Corporation). Must be a valid symbol recognized by FMP API.
        api_key (str): The Financial Modeling Prep API key for authentication. Retrieved from environment variables.

    Returns:
        list[dict] or None: A list of dictionaries containing historical market cap data if the request is successful,
        otherwise None. Each dictionary includes date and market capitalization values.

    Raises:
        KeyError: If the ticker or endpoint key is not found in the ENDPOINTS dictionary.

    Usage:
        # Fetch historical market cap for Microsoft
        hist_mcap = fetch_historical_market_cap('MSFT', 'your_api_key')
        if hist_mcap:
            current_mcap = hist_mcap[0].get('marketCap', 0)  # Most recent first
            print(f"Current MSFT market cap: {current_mcap}")

    Integration:
        This function integrates with the overall fmp_fetcher system by utilizing the ENDPOINTS['historical_market_cap']
        URL template and the fetch_data helper function, promoting code reusability and maintainability.
    """
    url = ENDPOINTS['historical_market_cap']['no_period'].format(ticker=ticker, apikey=api_key)
    return fetch_data(url)

def fetch_earning_calendar(ticker, api_key):
    """
    Fetches earnings calendar data for the specified stock ticker from the Financial Modeling Prep API.

    This endpoint provides upcoming and historical earnings announcement dates, expected vs actual results,
    and related earnings information. Earnings calendars are essential for event-driven trading strategies
    and understanding when companies report their financial performance.

    The function constructs the API URL using the centralized ENDPOINTS dictionary and delegates the actual HTTP request
    to the fetch_data function, ensuring consistent error handling and response processing across all fetch operations.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'AAPL' for Apple Inc.). Must be a valid symbol recognized by FMP API.
        api_key (str): The Financial Modeling Prep API key for authentication. Retrieved from environment variables.

    Returns:
        list[dict] or None: A list of dictionaries containing earnings calendar data if the request is successful,
        otherwise None. Each dictionary includes earnings dates, expected/actual EPS, and revenue figures.

    Raises:
        KeyError: If the ticker or endpoint key is not found in the ENDPOINTS dictionary.

    Usage:
        # Fetch earnings calendar for Apple
        earnings = fetch_earning_calendar('AAPL', 'your_api_key')
        if earnings:
            next_earnings = earnings[0]  # Next upcoming
            date = next_earnings.get('date', 'N/A')
            eps_est = next_earnings.get('epsEstimated', 'N/A')
            print(f"AAPL next earnings: {date}, EPS estimate: {eps_est}")

    Integration:
        This function integrates with the overall fmp_fetcher system by utilizing the ENDPOINTS['earning_calendar']
        URL template and the fetch_data helper function, promoting code reusability and maintainability.
    """
    url = ENDPOINTS['earning_calendar']['no_period'].format(ticker=ticker, apikey=api_key)
    return fetch_data(url)

def fetch_institutional_holder(ticker, api_key):
    """
    Fetches institutional holder data for the specified stock ticker from the Financial Modeling Prep API.

    This endpoint provides information about institutional investors who hold significant positions in the company,
    including their names, share holdings, and ownership percentages. This data is valuable for understanding
    smart money positioning and potential institutional buying/selling pressure.

    The function constructs the API URL using the centralized ENDPOINTS dictionary and delegates the actual HTTP request
    to the fetch_data function, ensuring consistent error handling and response processing across all fetch operations.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'KO' for The Coca-Cola Company). Must be a valid symbol recognized by FMP API.
        api_key (str): The Financial Modeling Prep API key for authentication. Retrieved from environment variables.

    Returns:
        list[dict] or None: A list of dictionaries containing institutional holder data if the request is successful,
        otherwise None. Each dictionary includes institution name, shares held, value, and ownership percentage.

    Raises:
        KeyError: If the ticker or endpoint key is not found in the ENDPOINTS dictionary.

    Usage:
        # Fetch institutional holders for Coca-Cola
        holders = fetch_institutional_holder('KO', 'your_api_key')
        if holders:
            top_holder = holders[0]  # Largest holder
            name = top_holder.get('holder', 'N/A')
            shares = top_holder.get('shares', 0)
            pct = top_holder.get('weightPercent', 0)
            print(f"Top KO holder: {name}, {shares} shares ({pct}%)")

    Integration:
        This function integrates with the overall fmp_fetcher system by utilizing the ENDPOINTS['institutional_holder']
        URL template and the fetch_data helper function, promoting code reusability and maintainability.
    """
    url = ENDPOINTS['institutional_holder']['no_period'].format(ticker=ticker, apikey=api_key)
    return fetch_data(url)

def fetch_etf_sector_weightings(ticker, api_key):
    """
    Fetches ETF sector weightings data for the specified ETF ticker from the Financial Modeling Prep API.

    This endpoint provides the sector allocation breakdown for an ETF, showing what percentage of the fund's
    assets are invested in different market sectors. This information is crucial for understanding an ETF's
    exposure to various industries and for portfolio diversification analysis.

    The function constructs the API URL using the centralized ENDPOINTS dictionary and delegates the actual HTTP request
    to the fetch_data function, ensuring consistent error handling and response processing across all fetch operations.

    Parameters:
        ticker (str): The ETF ticker symbol (e.g., 'SPY' for SPDR S&P 500 ETF Trust). Must be a valid ETF symbol recognized by FMP API.
        api_key (str): The Financial Modeling Prep API key for authentication. Retrieved from environment variables.

    Returns:
        list[dict] or None: A list of dictionaries containing sector weighting data if the request is successful,
        otherwise None. Each dictionary includes sector name and percentage weighting.

    Raises:
        KeyError: If the ticker or endpoint key is not found in the ENDPOINTS dictionary.

    Usage:
        # Fetch sector weightings for SPY ETF
        sectors = fetch_etf_sector_weightings('SPY', 'your_api_key')
        if sectors:
            tech_weight = next((s.get('weightPercentage', 0) for s in sectors if s.get('sector') == 'Technology'), 0)
            print(f"SPY Technology sector weighting: {tech_weight}%")

    Integration:
        This function integrates with the overall fmp_fetcher system by utilizing the ENDPOINTS['etf_sector_weightings']
        URL template and the fetch_data helper function, promoting code reusability and maintainability.
    """
    url = ENDPOINTS['etf_sector_weightings']['no_period'].format(ticker=ticker, apikey=api_key)
    return fetch_data(url)

def fetch_historical_price_eod(ticker, api_key):
    """
    Fetches historical end-of-day price data for the specified stock ticker from the Financial Modeling Prep API.

    This endpoint provides comprehensive daily price information including open, high, low, close prices,
    volume, and adjusted prices at the end of each trading day. This data forms the foundation for technical
    analysis, chart pattern recognition, and historical performance evaluation.

    The function constructs the API URL using the centralized ENDPOINTS dictionary and delegates the actual HTTP request
    to the fetch_data function, ensuring consistent error handling and response processing across all fetch operations.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'QQQ' for Invesco QQQ Trust). Must be a valid symbol recognized by FMP API.
        api_key (str): The Financial Modeling Prep API key for authentication. Retrieved from environment variables.

    Returns:
        list[dict] or None: A list of dictionaries containing daily historical price data if the request is successful,
        otherwise None. Each dictionary includes date, open, high, low, close, volume, and adjusted prices.

    Raises:
        KeyError: If the ticker or endpoint key is not found in the ENDPOINTS dictionary.

    Usage:
        # Fetch EOD prices for QQQ
        eod_prices = fetch_historical_price_eod('QQQ', 'your_api_key')
        if eod_prices:
            yesterday = eod_prices[1]  # Yesterday's data (index 0 is latest)
            close = yesterday.get('close', 0)
            volume = yesterday.get('volume', 0)
            print(f"QQQ yesterday close: {close}, Volume: {volume}")

    Integration:
        This function integrates with the overall fmp_fetcher system by utilizing the ENDPOINTS['historical_price_eod']
        URL template and the fetch_data helper function, promoting code reusability and maintainability.
    """
    url = ENDPOINTS['historical_price_eod']['no_period'].format(ticker=ticker, apikey=api_key)
    data = fetch_data(url)
    if data and isinstance(data, dict) and 'historical' in data:
        return data['historical']
    return data

def fetch_stock_price_change(ticker, api_key):
    """
    Fetches stock price change data for the specified stock ticker from the Financial Modeling Prep API.

    This endpoint provides information about recent price movements, including percentage changes over various
    time periods (1D, 5D, 1M, 3M, 6M, 1Y, etc.). This data is useful for understanding short-term momentum,
    volatility, and recent performance trends.

    The function constructs the API URL using the centralized ENDPOINTS dictionary and delegates the actual HTTP request
    to the fetch_data function, ensuring consistent error handling and response processing across all fetch operations.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'TSLA' for Tesla Inc.). Must be a valid symbol recognized by FMP API.
        api_key (str): The Financial Modeling Prep API key for authentication. Retrieved from environment variables.

    Returns:
        dict or None: A dictionary containing price change data across different time periods if the request is successful,
        otherwise None. The dictionary includes percentage changes and price movements for various intervals.

    Raises:
        KeyError: If the ticker or endpoint key is not found in the ENDPOINTS dictionary.

    Usage:
        # Fetch price changes for Tesla
        price_change = fetch_stock_price_change('TSLA', 'your_api_key')
        if price_change:
            day_change = price_change.get('1D', 0)
            month_change = price_change.get('1M', 0)
            print(f"TSLA: 1D change {day_change}%, 1M change {month_change}%")

    Integration:
        This function integrates with the overall fmp_fetcher system by utilizing the ENDPOINTS['stock_price_change']
        URL template and the fetch_data helper function, promoting code reusability and maintainability.
    """
    url = ENDPOINTS['stock_price_change']['no_period'].format(ticker=ticker, apikey=api_key)
    return fetch_data(url)

def fetch_insider_trading_all(ticker, api_key):
    """
    Fetches all insider trading data for the specified stock ticker from the Financial Modeling Prep API.

    This endpoint provides comprehensive insider transaction information including purchases, sales, and other
    insider activities for the company. This data is crucial for monitoring insider sentiment and potential
    signals about company performance expectations from those with privileged information.

    The function constructs the API URL using the centralized ENDPOINTS dictionary and delegates the actual HTTP request
    to the fetch_data function, ensuring consistent error handling and response processing across all fetch operations.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'AAPL' for Apple Inc.). Must be a valid symbol recognized by FMP API.
        api_key (str): The Financial Modeling Prep API key for authentication. Retrieved from environment variables.

    Returns:
        list[dict] or None: A list of dictionaries containing all insider trading transactions if the request is successful,
        otherwise None. Each dictionary includes transaction details like date, insider name, transaction type, shares, and values.

    Raises:
        KeyError: If the ticker or endpoint key is not found in the ENDPOINTS dictionary.

    Usage:
        # Fetch all insider trading for Apple
        insider_data = fetch_insider_trading_all('AAPL', 'your_api_key')
        if insider_data:
            total_transactions = len(insider_data)
            print(f"AAPL: {total_transactions} insider transactions found")

    Integration:
        This function integrates with the overall fmp_fetcher system by utilizing the ENDPOINTS['insider_trading']
        URL template and the fetch_data helper function, promoting code reusability and maintainability.
    """
    url = ENDPOINTS['insider_trading']['all'].format(ticker=ticker, apikey=api_key)
    return fetch_data(url)

def fetch_insider_trading_purchases(ticker, api_key):
    """
    Fetches insider purchase transactions for the specified stock ticker from the Financial Modeling Prep API.

    This endpoint provides information about insider buying activities, which can be a positive signal as insiders
    may purchase shares when they believe the stock is undervalued or when they have confidence in the company's future.
    Purchase data is often analyzed for bullish sentiment indicators.

    The function constructs the API URL using the centralized ENDPOINTS dictionary and delegates the actual HTTP request
    to the fetch_data function, ensuring consistent error handling and response processing across all fetch operations.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'TSLA' for Tesla Inc.). Must be a valid symbol recognized by FMP API.
        api_key (str): The Financial Modeling Prep API key for authentication. Retrieved from environment variables.

    Returns:
        list[dict] or None: A list of dictionaries containing insider purchase transactions if the request is successful,
        otherwise None. Each dictionary includes purchase details like date, insider name, shares purchased, and values.

    Raises:
        KeyError: If the ticker or endpoint key is not found in the ENDPOINTS dictionary.

    Usage:
        # Fetch insider purchases for Tesla
        purchases = fetch_insider_trading_purchases('TSLA', 'your_api_key')
        if purchases:
            recent_purchase = purchases[0]  # Most recent
            shares = recent_purchase.get('securitiesTransacted', 0)
            print(f"TSLA recent insider purchase: {shares} shares")

    Integration:
        This function integrates with the overall fmp_fetcher system by utilizing the ENDPOINTS['insider_trading']
        URL template and the fetch_data helper function, promoting code reusability and maintainability.
    """
    url = ENDPOINTS['insider_trading']['purchases'].format(ticker=ticker, apikey=api_key)
    return fetch_data(url)

def fetch_insider_trading_sales(ticker, api_key):
    """
    Fetches insider sale transactions for the specified stock ticker from the Financial Modeling Prep API.

    This endpoint provides information about insider selling activities, which may indicate various scenarios
    from portfolio diversification to lack of confidence. Sale data is analyzed for potential bearish signals,
    though sales can also be routine or for legitimate financial planning reasons.

    The function constructs the API URL using the centralized ENDPOINTS dictionary and delegates the actual HTTP request
    to the fetch_data function, ensuring consistent error handling and response processing across all fetch operations.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'AMZN' for Amazon.com Inc.). Must be a valid symbol recognized by FMP API.
        api_key (str): The Financial Modeling Prep API key for authentication. Retrieved from environment variables.

    Returns:
        list[dict] or None: A list of dictionaries containing insider sale transactions if the request is successful,
        otherwise None. Each dictionary includes sale details like date, insider name, shares sold, and values.

    Raises:
        KeyError: If the ticker or endpoint key is not found in the ENDPOINTS dictionary.

    Usage:
        # Fetch insider sales for Amazon
        sales = fetch_insider_trading_sales('AMZN', 'your_api_key')
        if sales:
            total_sales = sum(s.get('securitiesTransacted', 0) for s in sales)
            print(f"AMZN total insider shares sold: {total_sales}")

    Integration:
        This function integrates with the overall fmp_fetcher system by utilizing the ENDPOINTS['insider_trading']
        URL template and the fetch_data helper function, promoting code reusability and maintainability.
    """
    url = ENDPOINTS['insider_trading']['sales'].format(ticker=ticker, apikey=api_key)
    return fetch_data(url)

def fetch_technical_indicators(ticker, api_key):
    """
    Fetches technical indicators data for the specified stock ticker from the Financial Modeling Prep API.

    This function retrieves various technical analysis indicators including Simple Moving Average (SMA),
    Exponential Moving Average (EMA), Relative Strength Index (RSI), Moving Average Convergence Divergence (MACD),
    and others. These indicators are essential for technical analysis and trading strategy development.

    The function loops through all available technical indicator types in the ENDPOINTS dictionary,
    constructs the appropriate URL for each indicator, and fetches the data. Results are aggregated
    into a dictionary with indicator types as keys and the fetched data as values.

    Parameters:
        ticker (str): The stock ticker symbol (e.g., 'AAPL' for Apple Inc.). Must be a valid symbol recognized by FMP API.
        api_key (str): The Financial Modeling Prep API key for authentication. Retrieved from environment variables.

    Returns:
        dict: A dictionary with technical indicator types as keys ('sma', 'ema', 'rsi', etc.) and
        the corresponding fetched data (typically list[dict] or None) as values. Each indicator's data
        contains the calculated indicator values over time.

    Raises:
        KeyError: If the ticker or endpoint key is not found in the ENDPOINTS dictionary.

    Usage:
        # Fetch all technical indicators for Apple
        indicators = fetch_technical_indicators('AAPL', 'your_api_key')
        if indicators and indicators['rsi']:
            latest_rsi = indicators['rsi'][0].get('rsi', 0)  # Most recent RSI value
            print(f"AAPL latest RSI: {latest_rsi}")

    Integration:
        This function integrates with the overall fmp_fetcher system by utilizing the ENDPOINTS['technical_indicators']
        URL templates and the fetch_data helper function, ensuring consistent error handling and response processing.
    """
    result = {}
    for indicator_type in ENDPOINTS['technical_indicators']:
        url = ENDPOINTS['technical_indicators'][indicator_type].format(ticker=ticker, apikey=api_key)
        data = fetch_data(url)
        result[indicator_type] = data
    return result

def save_to_csv(data, filename, output_dir):
    """
    Saves the provided data to a CSV file in the specified output directory.

    This function handles the export of financial data fetched from the FMP API to CSV format.
    It supports both a single dictionary and a list of dictionaries as input data. The CSV file
    will use the keys from the first dictionary as column headers, ensuring consistent structure
    for tabular data like financial statements.

    Parameters:
        data (dict or list[dict]): The data to be saved. Can be a single dictionary or a list of
            dictionaries. Each dictionary represents a row in the CSV, with keys as column headers.
            For example, [{'symbol': 'AAPL', 'revenue': 100}, {'symbol': 'MSFT', 'revenue': 200}].
            If a single dict is passed, it is automatically converted to a list.
        filename (str): The base name of the CSV file to create, without the '.csv' extension.
            The function will append '.csv' to this name.
        output_dir (str): The directory path where the CSV file will be saved. If the directory
            does not exist, it will be created automatically. Relative or absolute paths are supported.

    Behavior:
        - Directory Creation: The output directory and any necessary parent directories are created
          if they do not exist.
        - Data Handling:
            - If data is a single dict, it is wrapped in a list.
            - If data is empty or contains non-dict elements, no file is created.
            - Field names are derived from the keys of the first dictionary.
        - CSV Format: Standard CSV with comma-separated values, with the first row as headers.
          Uses the csv.DictWriter with default quoting.
        - Error Handling: Raises exceptions for directory creation or file writing failures.

    Usage:
        # Save a list of financial metrics
        data = [{'ticker': 'AAPL', 'pe_ratio': 25.5}, {'ticker': 'GOOGL', 'pe_ratio': 30.2}]
        save_to_csv(data, 'pe_ratios', './output')
        This creates './output/pe_ratios.csv' with columns 'ticker' and 'pe_ratio'.
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        raise Exception(f"Error creating output directory '{output_dir}': {e}")

    # Ensure data is a list of dicts
    if isinstance(data, dict):
        data = [data]

    if not data or not all(isinstance(d, dict) for d in data):
        return  # Empty or invalid data, don't create file

    # Get fieldnames from first dict
    fieldnames = list(data[0].keys())

    # File path
    file_path = os.path.join(output_dir, f"{filename}.csv")

    try:
        # Write to CSV
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
    except Exception as e:
        raise Exception(f"Error writing to CSV file '{file_path}': {e}")

def main():
    """
    Main entry point for the fmp_fetcher script.

    This function orchestrates the CLI tool's functionality by:
    - Parsing command-line arguments using argparse for ticker, output directory, and period.
    - Loading API configuration from environment variables.
    - Preparing arguments for future API interaction logic.
    - Ensuring robust error handling through argparse's built-in validation.

    Current Implementation:
    - Implements argparse-based argument parsing with support for ticker, output directory, and period.
    - Provides user-friendly help text and default values for all arguments.
    - Validates period choices to ensure only 'annual' or 'quarterly' are accepted.
    - Stores parsed arguments in local variables for further processing.
    - Loads and validates the FMP API key from the .env file using python-dotenv, ensuring secure and configurable API authentication.
    - Configures file-based logging with INFO level, timestamped entries, and structured messages for operational tracking and troubleshooting.
    - Logs process initialization, individual fetch operations, success/failure status, and completion metrics to a dedicated log file.
    - Maintains console output for essential user feedback including real-time progress and final execution summary.
    - Orchestrates comprehensive data fetching from all 26+ FMP API endpoints, including:
      - 12 period-dependent categories (income_statement, balance_sheet, etc.) fetched with the selected period.
      - 19 non-period categories (owner_earnings, score, etc.) fetched without period specification.
      - Historical sectors performance data.
      - Insider trading data in three variants (all, purchases, sales).
      - Technical indicators data with multiple indicator types saved separately.
    - Provides progress reporting via console output for each fetch and save operation.
    - Automatically saves all fetched data to CSV files in the specified output directory, creating the directory if needed.
    - Implements comprehensive error handling with try-except blocks around all fetch function calls, preventing script crashes and allowing continued processing on individual failures.
    - Tracks and reports on fetch operations with counters for total attempted, successful, and failed fetches across all data categories.
    - Handles potential errors in directory creation and CSV saving operations, logging specific error messages for troubleshooting.
    - Generates a final summary report providing an overview of all fetch attempts and outcomes for user awareness.

    Design Decisions:
    - Uses argparse for standardized CLI argument handling, providing automatic help generation and error messages.
    - Includes short and long option names (-t/--ticker) for user convenience.
    - Sets sensible defaults (AAPL ticker, ./output directory, annual period) to allow minimal argument usage.
    - Enforces period validation through choices parameter to prevent invalid API requests.
    - Separates argument parsing from API logic for maintainability.
    - Follows single-responsibility principle: main() focuses on setup and orchestration.
    - Uses dynamic function lookup via globals() to call appropriate fetch functions based on category names, promoting code maintainability.
    - Groups data fetching into logical categories (period-dependent, non-period, special cases) for organized execution.
    - Implements real-time progress reporting through print statements to inform users of current operations.
    - Leverages the save_to_csv function for consistent CSV export across all data types with automatic directory creation.

    Future Extensions:
    - May add additional arguments for data types, limits, and output formats.
    - Error handling has been implemented for API responses and file operations, ensuring robust operation and graceful failure recovery.
    - Potential for JSON export, SQLite database integration, and web-based data visualization.

    Returns:
        None

    Raises:
        SystemExit: Automatically raised by argparse for invalid arguments or --help flag usage.
    """
    # Initialize argparse for CLI argument parsing
    # ArgumentParser provides the framework for defining command-line arguments,
    # automatically generating help messages, and handling user input validation.
    # The description explains the script's purpose, and prog sets the program name for help text.
    parser = argparse.ArgumentParser(
        description="Fetch financial data from Financial Modeling Prep API and save to CSV.",
        prog="fmp_fetcher.py"
    )
    timeout_var=3
    # Define ticker argument: required stock symbol for data fetching
    # Type is string, default AAPL for demonstration, help text explains usage
    # This allows users to specify which company's data to retrieve
    parser.add_argument(
        "-t", "--ticker",
        type=str,
        default="AAPL",
        help="Stock ticker symbol to fetch data for (default: AAPL)"
    )

    # Define output directory argument: where to save fetched data files
    # Type is string, default is ./output directory (relative to current working directory)
    # Help text clarifies the purpose and default behavior
    # Future implementation will create the directory if it doesn't exist
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="./output",
        help="Output directory to save CSV files (default: ./output)"
    )

    # Define period argument: financial data timeframe selection
    # Type is string with restricted choices for validation
    # Choices ensure only 'annual' or 'quarterly' are accepted, preventing invalid API calls
    # Default is 'annual' as it's commonly used for financial analysis
    # Help text lists available options and default
    parser.add_argument(
        "-p", "--period",
        type=str,
        choices=["annual", "quarterly"],
        default="annual",
        help="Period for financial data: 'annual' or 'quarterly' (default: annual)"
    )

    # Parse the command-line arguments
    # parse_args() processes sys.argv and validates against defined arguments
    # If invalid arguments are provided, argparse will display error messages and exit
    # On success, returns a Namespace object with argument values
    args = parser.parse_args()

    # Extract parsed arguments into local variables for clarity and future use
    # This separates argument parsing from business logic
    # Variables will be used in subsequent API calls and file operations
    ticker = args.ticker
    output_dir = args.output
    period = args.period

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Set up logging to file
    logging.basicConfig(
        filename=os.path.join(output_dir, 'fmp_fetcher.log'),
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filemode='w'
    )

    # Log start of process
    logging.info("Starting data fetching process for ticker: %s, period: %s, output directory: %s", ticker, period, output_dir)

    # Load environment variables from .env file
    # The dotenv library (python-dotenv) is used to load environment variables from a .env file in the project root.
    # This allows sensitive information like API keys to be stored securely outside of the source code.
    # load_dotenv() reads the .env file and sets the variables in os.environ if they are not already set.
    # This ensures that configuration remains local to the development environment and is not committed to version control.
    load_dotenv()

    # Retrieve and validate FMP_API_KEY
    # os.environ.get('FMP_API_KEY') retrieves the 'FMP_API_KEY' environment variable from the loaded environment.
    # get() returns the value if set, or None if not present.
    # Validation: Check if api_key is truthy (not None and not empty). If falsy, the API key is missing.
    # This ensures the script cannot proceed without a valid API key, preventing unauthorized API requests.
    api_key = os.environ.get('FMP_API_KEY')
    # Error handling for missing API key
    # If api_key is falsy (None or empty), the environment variable is not set or invalid.
    # Print a user-friendly error message explaining the issue and how to fix it.
    # exit(1) terminates the program with exit code 1, signaling failure to the calling process or shell.
    # This approach prevents proceeding with API calls that would fail due to lack of authentication.
    if not api_key:
        print("Error: FMP_API_KEY environment variable not found. Please set it in your .env file.")
        exit(1)

    # Why .env is used for API keys:
    # - Security: Prevents sensitive data from being committed to version control systems like Git.
    # - Flexibility: Allows different team members and environments to use their own API keys without modifying shared code.
    # - Environment-specific: Supports separate configurations for development, testing, and production.
    # - Best Practices: Follows industry standards for handling secrets in software development projects.

    # Store the valid API key for later use

    # Initialize counters for error handling summary
    total_attempted = 0
    successful = 0
    failed = 0

    # Main execution logic: fetch all data and save to CSV

    # Period-dependent categories
    period_categories = [
        'income_statement',
        'balance_sheet',
        'cash_flow_statement',
        'ratios',
        'enterprise_values',
        'financial_growth',
        'balance_sheet_growth',
        'income_statement_growth',
        'cash_flow_statement_growth',
        'key_metrics',
        'analyst_estimates'
    ]

    for category in period_categories:
        logging.info("Fetching %s data for period %s...", category, period)
        time.sleep(timeout_var)
        try:
            fetch_func = globals()[f'fetch_{category}']
            data = fetch_func(ticker, api_key, period)
            total_attempted += 1
            if data is not None:
                try:
                    filename = f"{ticker}_{category}_{period}"
                    save_to_csv(data, filename, output_dir)
                    logging.info("Successfully saved %s.csv", filename)
                    successful += 1
                except Exception as e:
                    logging.error("Error saving %s.csv: %s", filename, e)
                    failed += 1
            else:
                logging.warning("No data fetched for %s", category)
                failed += 1
        except Exception as e:
            logging.error("Error fetching %s: %s", category, e)
            total_attempted += 1
            failed += 1

    # Non-period categories
    non_period_categories = [
        'owner_earnings',
        'score',
        'key_metrics_ttm',
        'ratios_ttm',
        'discounted_cash_flow',
        'advanced_dcf',
        'advanced_levered_dcf',
        'rating',
        'historical_rating',
        'employee_count',
        'shares_float',
        'analyst_recommendations',
        'historical_market_cap',
        'earning_calendar',
        'institutional_holder',
        'etf_sector_weightings',
        'stock_price_change'
    ]

    for category in non_period_categories:
        logging.info("Fetching %s data...", category)
        time.sleep(timeout_var)
        try:
            fetch_func = globals()[f'fetch_{category}']
            data = fetch_func(ticker, api_key)
            total_attempted += 1
            if data is not None:
                try:
                    filename = f"{ticker}_{category}"
                    save_to_csv(data, filename, output_dir)
                    logging.info("Successfully saved %s.csv", filename)
                    successful += 1
                except Exception as e:
                    logging.error("Error saving %s.csv: %s", filename, e)
                    failed += 1
            else:
                logging.warning("No data fetched for %s", category)
                failed += 1
        except Exception as e:
            logging.error("Error fetching %s: %s", category, e)
            total_attempted += 1
            failed += 1

    # Historical sectors performance (no ticker)
    logging.info("Fetching historical sectors performance data...")
    try:
        data = fetch_historical_sectors_performance(api_key)
        total_attempted += 1
        if data is not None:
            try:
                filename = "historical_sectors_performance"
                save_to_csv(data, filename, output_dir)
                logging.info("Successfully saved %s.csv", filename)
                successful += 1
            except Exception as e:
                logging.error("Error saving %s.csv: %s", filename, e)
                failed += 1
        else:
            logging.warning("No data fetched for historical_sectors_performance")
            failed += 1
    except Exception as e:
        logging.error("Error fetching historical_sectors_performance: %s", e)
        total_attempted += 1
        failed += 1

    # Combined historical price data
    logging.info("Fetching combined historical price data...")
    try:
        dividend_data = fetch_historical_price_dividend(ticker, api_key) or []
        full_data = fetch_historical_price_full(ticker, api_key) or []
        eod_data = fetch_historical_price_eod(ticker, api_key) or []

        # Create combined data dict keyed by date
        combined_price_data = {}
        all_keys = set()
        for record in dividend_data + full_data + eod_data:
            date = record.get('date')
            if date:
                if date not in combined_price_data:
                    combined_price_data[date] = {'date': date}
                combined_price_data[date].update(record)
            all_keys.update(record.keys())

        # Ensure all records have all keys, fill missing with None
        for date, record in combined_price_data.items():
            for key in all_keys:
                if key not in record:
                    record[key] = None

        # Convert to list sorted by date (newest first)
        combined_data = sorted(combined_price_data.values(), key=lambda x: x['date'], reverse=True)

        if combined_data:
            filename = f"{ticker}_historical_prices"
            save_to_csv(combined_data, filename, output_dir)
            logging.info("Successfully saved %s.csv with %d records", filename, len(combined_data))
            total_attempted += 1
            successful += 1
        else:
            logging.warning("No historical price data fetched")
            total_attempted += 1
            failed += 1
    except Exception as e:
        logging.error("Error fetching/saving combined historical price data: %s", e)
        total_attempted += 1
        failed += 1

    # Insider trading variants
    insider_variants = ['all', 'purchases', 'sales']
    for variant in insider_variants:
        logging.info("Fetching insider trading %s data...", variant)
        time.sleep(timeout_var)
        try:
            fetch_func = globals()[f'fetch_insider_trading_{variant}']
            data = fetch_func(ticker, api_key)
            total_attempted += 1
            if data is not None:
                try:
                    filename = f"{ticker}_insider_trading_{variant}"
                    save_to_csv(data, filename, output_dir)
                    logging.info("Successfully saved %s.csv", filename)
                    successful += 1
                except Exception as e:
                    logging.error("Error saving %s.csv: %s", filename, e)
                    failed += 1
            else:
                logging.warning("No data fetched for insider_trading_%s", variant)
                failed += 1
        except Exception as e:
            logging.error("Error fetching insider_trading_%s: %s", variant, e)
            total_attempted += 1
            failed += 1

    # Technical indicators
    logging.info("Fetching technical indicators data...")
    try:
        indicators = fetch_technical_indicators(ticker, api_key)
        if indicators:
            # Field name mapping for indicators that don't match their key
            field_mapping = {
                'standarddeviation': 'standardDeviation'
            }

            # Use first indicator as base
            first_ind = next(iter(indicators))
            base_data = indicators[first_ind]
            if base_data:
                merged_data = []
                for entry in base_data:
                    merged_entry = dict(entry)
                    # Add other indicators
                    for ind_type, data in indicators.items():
                        if ind_type != first_ind and data:
                            # Find matching date
                            date = entry['date']
                            matching = next((e for e in data if e['date'] == date), None)
                            if matching:
                                # Use mapped field name if exists, otherwise use ind_type
                                field_name = field_mapping.get(ind_type, ind_type)
                                merged_entry[ind_type] = matching.get(field_name, None)
                    merged_data.append(merged_entry)
                # Save merged data
                filename = f"{ticker}_technical_indicators"
                save_to_csv(merged_data, filename, output_dir)
                logging.info("Successfully saved %s.csv", filename)
                total_attempted += 1
                successful += 1
            else:
                logging.warning("No data for base indicator")
                total_attempted += 1
                failed += 1
        else:
            logging.warning("No indicators fetched")
            total_attempted += 1
            failed += 1
    except Exception as e:
        logging.error("Error fetching/saving technical_indicators: %s", e)
        total_attempted += 1
        failed += 1

    # Log completion
    logging.info("Data fetching process completed.")

    # Final summary
    print("\nSummary:")
    print(f"Total fetches attempted: {total_attempted}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

if __name__ == "__main__":
    # Script execution guard to ensure main() is only run when script is executed directly
    # This prevents unintended execution if the module is imported elsewhere
    main()