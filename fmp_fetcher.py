"""
fmp_fetcher.py

A command-line interface (CLI) tool for fetching financial data from the Financial Modeling Prep (FMP) API.

This script serves as the entry point for the MyCFATool project, providing automated retrieval of financial statements, ratios, metrics, and historical prices for specified stock tickers. Data can be output in CSV or JSON formats and optionally stored in SQLite databases for further analysis.

Key Features:
- Supports both annual and quarterly financial data.
- Handles API authentication via environment variables.
- Provides basic error handling for API responses.
- Extensible structure for adding more data types and processing logic.

Usage:
    python fmp_fetcher.py --ticker AAPL --output ./output --period annual

Design Decisions:
- Modular imports for clarity and maintainability.
- Use of argparse for flexible CLI options with validation and help generation.
- Environment variable loading for secure API key management.
- ENDPOINTS dictionary organizes API URL templates for maintainability and extensibility.
- main() function now implements CLI argument parsing for ticker, output directory, and period.
- Separation of concerns: imports grouped by standard library vs third-party.
- Future extensions planned for API integration and data processing.

Author: Auto-generated
Date: 2026-01-02

"""

# Standard library imports for core functionality
import argparse  # Command-line argument parsing for user inputs
import os  # Operating system interfaces for environment and file operations
import requests  # HTTP library for API requests to FMP
import csv  # CSV file handling for data export
import json  # JSON parsing for API responses and data manipulation

# Third-party libraries
from dotenv import load_dotenv  # Loading environment variables from .env files for secure configuration

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
        'wma': 'https://financialmodelingprep.com/api/v3/technical_indicator/daily/{ticker}?type=wma&period=26&apikey={apikey}', 
        'dema': 'https://financialmodelingprep.com/api/v3/technical_indicator/daily/{ticker}?type=dema&period=26&apikey={apikey}',
        'tema': 'https://financialmodelingprep.com/api/v3/technical_indicator/daily/{ticker}?type=tema&period=26&apikey={apikey}',
        'williams': 'https://financialmodelingprep.com/api/v3/technical_indicator/daily/{ticker}?type=williams&period=26&apikey={apikey}', 
        'adx': 'https://financialmodelingprep.com/api/v3/technical_indicator/daily/{ticker}?type=adx&period=26&apikey={apikey}',
        'standarddeviation': 'https://financialmodelingprep.com/api/v3/technical_indicator/daily/{ticker}?type=standarddeviation&period=26&apikey={apikey}'
    }
}

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

    Design Decisions:
    - Uses argparse for standardized CLI argument handling, providing automatic help generation and error messages.
    - Includes short and long option names (-t/--ticker) for user convenience.
    - Sets sensible defaults (AAPL ticker, ./output directory, annual period) to allow minimal argument usage.
    - Enforces period validation through choices parameter to prevent invalid API requests.
    - Separates argument parsing from API logic for maintainability.
    - Follows single-responsibility principle: main() focuses on setup and orchestration.

    Future Extensions:
    - Will integrate with API request logic using parsed arguments.
    - May add additional arguments for data types, limits, and output formats.
    - Error handling will be expanded for API responses and file operations.

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

if __name__ == "__main__":
    # Script execution guard to ensure main() is only run when script is executed directly
    # This prevents unintended execution if the module is imported elsewhere
    main()