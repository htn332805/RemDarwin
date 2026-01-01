import os
import requests
import yaml
import pandas as pd
import logging
import time
from typing import Dict, Any, Optional
import redis
from .rate_limiter import RedisRateLimiter
from MyCFATool.core.validation import ValidationMixin, ValidationError


class FMPClient(ValidationMixin):
    """
    Financial Modeling Prep API Client for retrieving financial data.

    This class provides methods to fetch annual and quarterly financial statements
    including income statements, balance sheets, and cash flow statements.
    """

    def __init__(self, config_path: str = "config/settings.yaml"):
        """
        Initialize the FMP API client.

        Args:
            config_path: Path to the configuration file
        """
        self.config = self._load_config(config_path)
        self.api_key = os.getenv("FMP_API_KEY")
        if not self.api_key:
            raise ValueError("FMP_API_KEY environment variable not set")
        self.base_url = self.config["api"]["fmp"]["base_url"]
        self.request_limit = self.config["api"]["fmp"]["limit"]
        self.logger = logging.getLogger(__name__)

        # Initialize Redis for distributed rate limiting
        redis_config = self.config.get("redis", {})
        redis_client = redis.Redis(
            host=redis_config.get("host", "localhost"),
            port=redis_config.get("port", 6379),
            db=redis_config.get("db", 0),
            password=os.getenv("REDIS_PASSWORD") or redis_config.get("password"),
            decode_responses=True
        )

        # Initialize rate limiter
        self.rate_limiter = RedisRateLimiter(
            redis_client=redis_client,
            limit=self.request_limit,
            window=60  # 60 seconds for per-minute limit
        )

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to the config file

        Returns:
            Configuration dictionary
        """
        with open(config_path, "r") as file:
            return yaml.safe_load(file)

    def _rate_limit(self):
        """
        Enforce distributed rate limiting using Redis.
        Blocks until a request slot becomes available.
        """
        # Wait for a slot to become available (with a reasonable timeout)
        if not self.rate_limiter.wait_for_slot(identifier=self.api_key, timeout=300):  # 5 minute timeout
            raise RuntimeError("Rate limit timeout: Unable to acquire request slot within 5 minutes")
        self.logger.debug("Rate limit check passed")

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a GET request to the FMP API with error handling, rate limiting, and retries.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            JSON response as dictionary

        Raises:
            requests.HTTPError: For HTTP errors
            ValueError: For API-specific errors
        """
        url = f"{self.base_url}{endpoint}"
        if params is None:
            params = {}
        params["apikey"] = self.api_key

        max_retries = 3
        for attempt in range(max_retries):
            try:
                self._rate_limit()
                self.logger.info(f"Making request to {url} with params {params}")
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                # Check for API-specific errors
                if isinstance(data, dict) and 'error' in data:
                    self.logger.error(f"API error: {data['error']}")
                    raise ValueError(f"API error: {data['error']}")
                self.logger.info(f"Request successful for {endpoint}")
                return data
            except requests.HTTPError as e:
                if response.status_code == 429:
                    # Rate limit exceeded from API, retry with exponential backoff
                    wait_time = 2 ** attempt
                    self.logger.warning(f"API rate limit hit (429), retrying in {wait_time} seconds (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    self.logger.error(f"HTTP error for {endpoint}: {e}")
                    raise
            except RuntimeError as e:
                if "Rate limit" in str(e):
                    # Our rate limiter timeout
                    self.logger.error(f"Distributed rate limiter timeout: {e}")
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        self.logger.info(f"Retrying after rate limiter timeout in {wait_time} seconds")
                        time.sleep(wait_time)
                        continue
                    raise
                else:
                    raise
            except requests.RequestException as e:
                self.logger.error(f"Request exception for {endpoint}: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    self.logger.info(f"Retrying in {wait_time} seconds")
                    time.sleep(wait_time)
                    continue
                raise
        raise RuntimeError(f"Failed to get data from {endpoint} after {max_retries} attempts")

    def _validate_response_data(self, data: Any, required_fields: Optional[list] = None) -> None:
        """
        Validate the API response data.

        Args:
            data: The response data to validate
            required_fields: List of required fields in each dict

        Raises:
            ValidationError: If validation fails
        """
        if required_fields is None:
            required_fields = ['date', 'symbol']

        if not isinstance(data, list):
            self.logger.error("Response data is not a list")
            raise ValidationError("Invalid response: data must be a list")

        if not data:
            self.logger.warning("Response data is empty")
            raise ValidationError("Invalid response: data is empty")

        # Define financial fields that should be numeric
        non_negative_fields = [
            'totalAssets', 'totalLiabilities', 'totalStockholdersEquity',
            'totalCurrentAssets', 'totalCurrentLiabilities', 'cashAndCashEquivalents',
            'shortTermInvestments', 'netReceivables', 'inventory',
            'propertyPlantAndEquipmentNet', 'goodwill', 'intangibleAssets',
            'longTermDebt', 'accountsPayable', 'deferredRevenue', 'totalDebt',
            'retainedEarnings', 'commonStock', 'treasuryStock'
        ]

        numeric_fields = [
            'revenue', 'costOfRevenue', 'grossProfit', 'operatingExpenses',
            'operatingIncome', 'interestExpense', 'incomeBeforeTax',
            'incomeTaxExpense', 'netIncome', 'eps', 'epsdiluted', 'ebitda',
            'depreciationAndAmortization', 'changesInReceivables',
            'changesInInventories', 'cashflowFromInvestment',
            'cashflowFromFinancing', 'dividendsPaid', 'freeCashFlow'
        ]

        for item in data:
            if not isinstance(item, dict):
                self.logger.error("Response data contains non-dict item")
                raise ValidationError("Invalid response: each item must be a dictionary")

            missing_fields = [field for field in required_fields if field not in item]
            if missing_fields:
                self.logger.error(f"Response data item missing required fields: {missing_fields}")
                raise ValidationError(f"Invalid response: missing required fields {missing_fields}")

            # Validate date format
            if 'date' in item:
                self.validate_date_format(item['date'])

            # Validate financial field data types and ranges
            for field, value in item.items():
                if field in non_negative_fields + numeric_fields and value is not None:
                    min_val = 0.0 if field in non_negative_fields else None
                    self.validate_numeric(value, min_val=min_val)

            # Balance sheet consistency check
            if all(field in item and item[field] is not None for field in ['totalAssets', 'totalLiabilities', 'totalStockholdersEquity']):
                assets = item['totalAssets']
                liabilities = item['totalLiabilities']
                equity = item['totalStockholdersEquity']
                if assets > 0:  # Avoid division by zero
                    diff = abs(assets - (liabilities + equity))
                    if diff / assets > 0.01:  # 1% tolerance
                        raise ValidationError(
                            f"Balance sheet inconsistency: assets ({assets}) != liabilities ({liabilities}) + equity ({equity})"
                        )

    def get_annual_income_statement(self, ticker: str) -> pd.DataFrame:
        """
        Retrieve annual income statement data for a given ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Pandas DataFrame containing annual income statement data
        """
        endpoint = f"income-statement/{ticker}"
        params = {"period": "annual"}
        data = self._get(endpoint, params)
        self._validate_response_data(data)
        return pd.DataFrame(data)

    def get_quarterly_income_statement(self, ticker: str) -> pd.DataFrame:
        """
        Retrieve quarterly income statement data for a given ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Pandas DataFrame containing quarterly income statement data
        """
        endpoint = f"income-statement/{ticker}"
        params = {"period": "quarter"}
        data = self._get(endpoint, params)
        self._validate_response_data(data)
        return pd.DataFrame(data)

    def get_annual_balance_sheet(self, ticker: str) -> pd.DataFrame:
        """
        Retrieve annual balance sheet data for a given ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Pandas DataFrame containing annual balance sheet data
        """
        endpoint = f"balance-sheet-statement/{ticker}"
        params = {"period": "annual"}
        data = self._get(endpoint, params)
        self._validate_response_data(data)
        return pd.DataFrame(data)

    def get_quarterly_balance_sheet(self, ticker: str) -> pd.DataFrame:
        """
        Retrieve quarterly balance sheet data for a given ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Pandas DataFrame containing quarterly balance sheet data
        """
        endpoint = f"balance-sheet-statement/{ticker}"
        params = {"period": "quarter"}
        data = self._get(endpoint, params)
        self._validate_response_data(data)
        return pd.DataFrame(data)

    def get_annual_cash_flow(self, ticker: str) -> pd.DataFrame:
        """
        Retrieve annual cash flow statement data for a given ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Pandas DataFrame containing annual cash flow statement data
        """
        endpoint = f"cash-flow-statement/{ticker}"
        params = {"period": "annual"}
        data = self._get(endpoint, params)
        self._validate_response_data(data)
        return pd.DataFrame(data)

    def get_quarterly_cash_flow(self, ticker: str) -> pd.DataFrame:
        """
        Retrieve quarterly cash flow statement data for a given ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Pandas DataFrame containing quarterly cash flow statement data
        """
        endpoint = f"cash-flow-statement/{ticker}"
        params = {"period": "quarter"}
        data = self._get(endpoint, params)
        self._validate_response_data(data)
        return pd.DataFrame(data)

    def get_annual_ratios(self, ticker: str) -> pd.DataFrame:
        """
        Retrieve annual financial ratios data for a given ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Pandas DataFrame containing annual financial ratios data
        """
        endpoint = f"ratios/{ticker}"
        params = {"period": "annual"}
        data = self._get(endpoint, params)
        self._validate_response_data(data)
        return pd.DataFrame(data)

    def get_quarterly_ratios(self, ticker: str) -> pd.DataFrame:
        """
        Retrieve quarterly financial ratios data for a given ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Pandas DataFrame containing quarterly financial ratios data
        """
        endpoint = f"ratios/{ticker}"
        params = {"period": "quarter"}
        data = self._get(endpoint, params)
        self._validate_response_data(data)
        return pd.DataFrame(data)

    def get_historical_price(self, ticker: str, timeseries: int = 365) -> pd.DataFrame:
        """
        Retrieve historical price data for a given ticker, including OHLCV.

        Args:
            ticker: Stock ticker symbol
            timeseries: Number of days of historical data to retrieve

        Returns:
            Pandas DataFrame containing historical price data with OHLCV
        """
        endpoint = f"historical-price-full/{ticker}"
        params = {"timeseries": timeseries}
        data = self._get(endpoint, params)
        # Historical data is in data['historical']
        historical_data = data.get("historical", [])
        if not isinstance(historical_data, list):
            self.logger.error("Historical data is not a list")
            raise ValueError("Invalid historical data response")
        # Validate each item has 'date'
        for item in historical_data:
            if not isinstance(item, dict) or 'date' not in item:
                self.logger.error("Historical data item missing 'date'")
                raise ValueError("Invalid historical data item")
        return pd.DataFrame(historical_data)

    def get_sp500_tickers(self) -> list[str]:
        """
        Retrieve the list of S&P 500 constituent tickers.

        Returns:
            List of ticker symbols
        """
        endpoint = "sp500_constituent"
        data = self._get(endpoint)
        if not isinstance(data, list):
            self.logger.error("S&P 500 data is not a list")
            raise ValueError("Invalid S&P 500 response")
        tickers = []
        for item in data:
            if isinstance(item, dict) and 'symbol' in item:
                tickers.append(item['symbol'])
        if not tickers:
            self.logger.warning("No tickers found in S&P 500 response")
        return tickers

    def get_available_tickers(self, limit: int = 1000) -> list[str]:
        """
        Retrieve a list of available tickers from the stock list API.

        Args:
            limit: Maximum number of tickers to retrieve

        Returns:
            List of ticker symbols
        """
        endpoint = "stock/list"
        params = {"limit": limit}
        data = self._get(endpoint, params)
        if not isinstance(data, list):
            self.logger.error("Stock list data is not a list")
            raise ValueError("Invalid stock list response")
        tickers = []
        for item in data:
            if isinstance(item, dict) and 'symbol' in item:
                tickers.append(item['symbol'])
        return tickers