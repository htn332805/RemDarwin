import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import yaml
import pandas as pd
import time
import requests
from MyCFATool.ingestion.fmp_client import FMPClient
from MyCFATool.core.validation import ValidationError

class TestFMPClient(unittest.TestCase):
    def setUp(self):
        self.mock_config = {
            "api": {
                "fmp": {
                    "base_url": "https://financialmodelingprep.com/api/v3/",
                    "limit": 120
                }
            }
        }
        self.config_path = "config/settings.yaml"
        self.api_key = "test_api_key"
        os.environ["FMP_API_KEY"] = self.api_key

    def tearDown(self):
        if "FMP_API_KEY" in os.environ:
            del os.environ["FMP_API_KEY"]

    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_init_success(self, mock_yaml, mock_file):
        mock_yaml.return_value = self.mock_config
        client = FMPClient(self.config_path)
        self.assertEqual(client.config, self.mock_config)
        self.assertEqual(client.api_key, self.api_key)
        self.assertEqual(client.base_url, "https://financialmodelingprep.com/api/v3/")
        self.assertEqual(client.request_limit, 120)
        self.assertEqual(client.requests, [])

    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_init_no_api_key(self, mock_yaml, mock_file):
        mock_yaml.return_value = self.mock_config
        del os.environ["FMP_API_KEY"]
        with self.assertRaises(ValueError) as cm:
            FMPClient(self.config_path)
        self.assertIn("FMP_API_KEY environment variable not set", str(cm.exception))

    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_load_config(self, mock_yaml, mock_file):
        mock_yaml.return_value = self.mock_config
        client = FMPClient.__new__(FMPClient)
        result = client._load_config(self.config_path)
        self.assertEqual(result, self.mock_config)
        self.assertEqual(mock_file.call_count, 1)
        self.assertEqual(mock_file.call_args, ((self.config_path, "r"),))
        mock_yaml.assert_called_once()

    @patch("time.sleep")
    @patch("time.time")
    def test_rate_limit_no_sleep(self, mock_time, mock_sleep):
        mock_time.return_value = 1000
        client = FMPClient.__new__(FMPClient)  # Create without __init__
        client.requests = []
        client.request_limit = 120
        client.logger = MagicMock()
        client._rate_limit()
        mock_sleep.assert_not_called()
        self.assertEqual(len(client.requests), 1)

    @patch("time.sleep")
    @patch("time.time")
    def test_rate_limit_with_sleep(self, mock_time, mock_sleep):
        client = FMPClient.__new__(FMPClient)
        client.requests = [900] * 120  # 120 requests at time 900
        client.request_limit = 120
        client.logger = MagicMock()
        mock_time.side_effect = [950, 950, 980]  # First call 950, sleep 10s, then 980
        client._rate_limit()
        mock_sleep.assert_called_once_with(10.0)
        self.assertEqual(len(client.requests), 121)

    @patch("requests.get")
    def test_get_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": "test"}
        mock_get.return_value = mock_response
        client = FMPClient.__new__(FMPClient)
        client.api_key = self.api_key
        client.base_url = "https://financialmodelingprep.com/api/v3/"
        client.requests = []
        client.request_limit = 120
        client.logger = MagicMock()
        client._rate_limit = MagicMock()
        result = client._get("test_endpoint")
        self.assertEqual(result, {"data": "test"})
        mock_get.assert_called_once_with("https://financialmodelingprep.com/api/v3/test_endpoint", params={"apikey": self.api_key})

    @patch("requests.get")
    def test_get_api_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "API error"}
        mock_get.return_value = mock_response
        client = FMPClient.__new__(FMPClient)
        client.api_key = self.api_key
        client.base_url = "https://financialmodelingprep.com/api/v3/"
        client.requests = []
        client.request_limit = 120
        client.logger = MagicMock()
        client._rate_limit = MagicMock()
        with self.assertRaises(ValueError) as cm:
            client._get("test_endpoint")
        self.assertIn("API error", str(cm.exception))

    @patch("time.sleep")
    @patch("requests.get")
    def test_get_rate_limit_429_retry(self, mock_get, mock_sleep):
        mock_resp1 = MagicMock()
        mock_resp1.status_code = 429
        mock_resp1.raise_for_status.side_effect = requests.HTTPError("429")
        mock_resp2 = MagicMock()
        mock_resp2.json.return_value = {"data": "test"}
        mock_get.side_effect = [mock_resp1, mock_resp2]
        client = FMPClient.__new__(FMPClient)
        client.api_key = self.api_key
        client.base_url = "https://financialmodelingprep.com/api/v3/"
        client.requests = []
        client.request_limit = 120
        client.logger = MagicMock()
        client._rate_limit = MagicMock()
        result = client._get("test_endpoint")
        self.assertEqual(result, {"data": "test"})
        self.assertEqual(mock_sleep.call_count, 1)
        self.assertEqual(mock_get.call_count, 2)

    @patch("time.sleep")
    @patch("requests.get")
    def test_get_http_error_no_retry(self, mock_get, mock_sleep):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError("404")
        mock_get.return_value = mock_response
        client = FMPClient.__new__(FMPClient)
        client.api_key = self.api_key
        client.base_url = "https://financialmodelingprep.com/api/v3/"
        client.requests = []
        client.request_limit = 120
        client.logger = MagicMock()
        client._rate_limit = MagicMock()
        with self.assertRaises(requests.HTTPError):
            client._get("test_endpoint")

    def test_validate_response_data_valid(self):
        client = FMPClient.__new__(FMPClient)
        client.logger = MagicMock()
        data = [{"date": "2023-01-01", "symbol": "AAPL"}]
        client._validate_response_data(data)  # Should not raise

    def test_validate_response_data_not_list(self):
        client = FMPClient.__new__(FMPClient)
        client.logger = MagicMock()
        data = {"error": "not list"}
        with self.assertRaises(ValidationError) as cm:
            client._validate_response_data(data)
        self.assertIn("Invalid response: data must be a list", str(cm.exception))

    def test_validate_response_data_empty(self):
        client = FMPClient.__new__(FMPClient)
        client.logger = MagicMock()
        data = []
        with self.assertRaises(ValidationError) as cm:
            client._validate_response_data(data)
        self.assertIn("Invalid response: data is empty", str(cm.exception))

    def test_validate_response_data_non_dict_item(self):
        client = FMPClient.__new__(FMPClient)
        client.logger = MagicMock()
        data = ["not dict", {"date": "2023-01-01", "symbol": "AAPL"}]
        with self.assertRaises(ValidationError) as cm:
            client._validate_response_data(data)
        self.assertIn("Invalid response: each item must be a dictionary", str(cm.exception))

    def test_validate_response_data_missing_fields(self):
        client = FMPClient.__new__(FMPClient)
        client.logger = MagicMock()
        data = [{"symbol": "AAPL"}]  # missing date
        with self.assertRaises(ValidationError) as cm:
            client._validate_response_data(data)
        self.assertIn("Invalid response: missing required fields", str(cm.exception))

    def test_validate_response_data_invalid_date_format(self):
        """Test _validate_response_data with invalid date format."""
        client = FMPClient.__new__(FMPClient)
        client.logger = MagicMock()
        data = [{"date": "2023/01/01", "symbol": "AAPL"}]  # invalid date format
        with self.assertRaises(ValidationError) as cm:
            client._validate_response_data(data)
        self.assertIn("does not match format", str(cm.exception))

    def test_validate_response_data_non_numeric_field(self):
        """Test _validate_response_data with non-numeric value in numeric field."""
        client = FMPClient.__new__(FMPClient)
        client.logger = MagicMock()
        data = [{"date": "2023-01-01", "symbol": "AAPL", "totalAssets": "not_a_number"}]
        with self.assertRaises(ValidationError) as cm:
            client._validate_response_data(data)
        self.assertIn("is not numeric", str(cm.exception))

    def test_validate_response_data_negative_asset(self):
        """Test _validate_response_data with negative asset value."""
        client = FMPClient.__new__(FMPClient)
        client.logger = MagicMock()
        data = [{"date": "2023-01-01", "symbol": "AAPL", "totalAssets": -100.0}]
        with self.assertRaises(ValidationError) as cm:
            client._validate_response_data(data)
        self.assertIn("is below minimum 0", str(cm.exception))

    def test_validate_response_data_balance_sheet_inconsistency(self):
        """Test _validate_response_data with balance sheet inconsistency."""
        client = FMPClient.__new__(FMPClient)
        client.logger = MagicMock()
        data = [{"date": "2023-01-01", "symbol": "AAPL",
                "totalAssets": 1000.0, "totalLiabilities": 400.0, "totalStockholdersEquity": 500.0}]
        # 1000 != 400 + 500
        with self.assertRaises(ValidationError) as cm:
            client._validate_response_data(data)
        self.assertIn("Balance sheet inconsistency", str(cm.exception))

    def test_validate_response_data_valid_balance_sheet(self):
        """Test _validate_response_data with valid balance sheet."""
        client = FMPClient.__new__(FMPClient)
        client.logger = MagicMock()
        data = [{"date": "2023-01-01", "symbol": "AAPL",
                "totalAssets": 1000.0, "totalLiabilities": 500.0, "totalStockholdersEquity": 500.0}]
        # Should not raise
        client._validate_response_data(data)

    @patch("pandas.DataFrame")
    def test_get_annual_income_statement_success(self, mock_df):
        client = FMPClient.__new__(FMPClient)
        client._get = MagicMock(return_value=[{"date": "2023-01-01", "symbol": "AAPL"}])
        client._validate_response_data = MagicMock()
        client.get_annual_income_statement("AAPL")
        client._get.assert_called_once_with("income-statement/AAPL", {"period": "annual"})
        client._validate_response_data.assert_called_once()
        mock_df.assert_called_once()

    @patch("pandas.DataFrame")
    def test_get_annual_income_statement_validation_error(self, mock_df):
        client = FMPClient.__new__(FMPClient)
        client._get = MagicMock(return_value=[{"date": "2023-01-01", "symbol": "AAPL"}])
        client._validate_response_data = MagicMock(side_effect=ValidationError("Validation failed"))
        with self.assertRaises(ValidationError):
            client.get_annual_income_statement("AAPL")

    @patch("pandas.DataFrame")
    def test_get_quarterly_income_statement_success(self, mock_df):
        client = FMPClient.__new__(FMPClient)
        client._get = MagicMock(return_value=[{"date": "2023-01-01", "symbol": "AAPL"}])
        client._validate_response_data = MagicMock()
        client.get_quarterly_income_statement("AAPL")
        client._get.assert_called_once_with("income-statement/AAPL", {"period": "quarter"})
        client._validate_response_data.assert_called_once()
        mock_df.assert_called_once()

    @patch("pandas.DataFrame")
    def test_get_annual_balance_sheet_success(self, mock_df):
        client = FMPClient.__new__(FMPClient)
        client._get = MagicMock(return_value=[{"date": "2023-01-01", "symbol": "AAPL"}])
        client._validate_response_data = MagicMock()
        client.get_annual_balance_sheet("AAPL")
        client._get.assert_called_once_with("balance-sheet-statement/AAPL", {"period": "annual"})
        client._validate_response_data.assert_called_once()
        mock_df.assert_called_once()

    @patch("pandas.DataFrame")
    def test_get_quarterly_balance_sheet_success(self, mock_df):
        client = FMPClient.__new__(FMPClient)
        client._get = MagicMock(return_value=[{"date": "2023-01-01", "symbol": "AAPL"}])
        client._validate_response_data = MagicMock()
        client.get_quarterly_balance_sheet("AAPL")
        client._get.assert_called_once_with("balance-sheet-statement/AAPL", {"period": "quarter"})
        client._validate_response_data.assert_called_once()
        mock_df.assert_called_once()

    @patch("pandas.DataFrame")
    def test_get_annual_cash_flow_success(self, mock_df):
        client = FMPClient.__new__(FMPClient)
        client._get = MagicMock(return_value=[{"date": "2023-01-01", "symbol": "AAPL"}])
        client._validate_response_data = MagicMock()
        client.get_annual_cash_flow("AAPL")
        client._get.assert_called_once_with("cash-flow-statement/AAPL", {"period": "annual"})
        client._validate_response_data.assert_called_once()
        mock_df.assert_called_once()

    @patch("pandas.DataFrame")
    def test_get_quarterly_cash_flow_success(self, mock_df):
        client = FMPClient.__new__(FMPClient)
        client._get = MagicMock(return_value=[{"date": "2023-01-01", "symbol": "AAPL"}])
        client._validate_response_data = MagicMock()
        client.get_quarterly_cash_flow("AAPL")
        client._get.assert_called_once_with("cash-flow-statement/AAPL", {"period": "quarter"})
        client._validate_response_data.assert_called_once()
        mock_df.assert_called_once()

if __name__ == "__main__":
    unittest.main()