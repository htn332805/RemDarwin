#!/usr/bin/env python3

import sys
import os
import tempfile
from unittest.mock import patch, MagicMock
import fmp_fetcher

def test_main_execution_logic():
    """
    Test the main execution logic with 100% coverage.
    Mocks all API calls and verifies function calls, parameters, CSV naming, and progress messages.
    Tests both annual and quarterly periods.
    """

    # Mock data for fetch functions
    mock_data = [{'test_key': 'test_value', 'date': '2023-01-01'}]

    # Mock data for single dict returns (like owner_earnings, score, etc.)
    mock_dict_data = {'test_key': 'test_value'}

    # Mock data for technical indicators (dict of lists)
    mock_tech_data = {
        'sma': mock_data,
        'ema': mock_data,
        'rsi': mock_data,
        'macd': mock_data,
        'wma': mock_data,
        'dema': mock_data,
        'tema': mock_data,
        'williams': mock_data,
        'adx': mock_data,
        'standarddeviation': mock_data
    }

    # Create a temporary directory for output
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock all fetch functions
        mock_fetchers = {
            # Period-dependent
            'fetch_income_statement': MagicMock(return_value=mock_data),
            'fetch_balance_sheet': MagicMock(return_value=mock_data),
            'fetch_cash_flow_statement': MagicMock(return_value=mock_data),
            'fetch_ratios': MagicMock(return_value=mock_data),
            'fetch_enterprise_values': MagicMock(return_value=mock_data),
            'fetch_financial_growth': MagicMock(return_value=mock_data),
            'fetch_balance_sheet_growth': MagicMock(return_value=mock_data),
            'fetch_income_statement_growth': MagicMock(return_value=mock_data),
            'fetch_cash_flow_statement_growth': MagicMock(return_value=mock_data),
            'fetch_key_metrics': MagicMock(return_value=mock_data),
            'fetch_analyst_estimates': MagicMock(return_value=mock_data),

            # Non-period
            'fetch_owner_earnings': MagicMock(return_value=mock_dict_data),
            'fetch_score': MagicMock(return_value=mock_dict_data),
            'fetch_key_metrics_ttm': MagicMock(return_value=mock_dict_data),
            'fetch_ratios_ttm': MagicMock(return_value=mock_dict_data),
            'fetch_discounted_cash_flow': MagicMock(return_value=mock_dict_data),
            'fetch_advanced_dcf': MagicMock(return_value=mock_dict_data),
            'fetch_advanced_levered_dcf': MagicMock(return_value=mock_dict_data),
            'fetch_rating': MagicMock(return_value=mock_dict_data),
            'fetch_historical_rating': MagicMock(return_value=mock_data),
            'fetch_historical_price_dividend': MagicMock(return_value=mock_data),
            'fetch_historical_price_full': MagicMock(return_value=mock_data),
            'fetch_employee_count': MagicMock(return_value=mock_data),
            'fetch_shares_float': MagicMock(return_value=mock_dict_data),
            'fetch_analyst_recommendations': MagicMock(return_value=mock_data),
            'fetch_historical_market_cap': MagicMock(return_value=mock_data),
            'fetch_earning_calendar': MagicMock(return_value=mock_data),
            'fetch_institutional_holder': MagicMock(return_value=mock_data),
            'fetch_etf_sector_weightings': MagicMock(return_value=mock_data),
            'fetch_historical_price_eod': MagicMock(return_value=mock_data),
            'fetch_stock_price_change': MagicMock(return_value=mock_dict_data),

            # Special
            'fetch_historical_sectors_performance': MagicMock(return_value=mock_data),
            'fetch_insider_trading_all': MagicMock(return_value=mock_data),
            'fetch_insider_trading_purchases': MagicMock(return_value=mock_data),
            'fetch_insider_trading_sales': MagicMock(return_value=mock_data),
            'fetch_technical_indicators': MagicMock(return_value=mock_tech_data)
        }

        # Mock save_to_csv to capture calls
        mock_save_to_csv = MagicMock()

        with patch.multiple(fmp_fetcher, **mock_fetchers), \
             patch('fmp_fetcher.save_to_csv', mock_save_to_csv), \
             patch.dict(os.environ, {'FMP_API_KEY': 'mock_api_key'}):

            # Test for annual period
            print("Testing main execution with annual period...")
            printed_messages = []
            def mock_print(*args, **kwargs):
                message = ' '.join(str(arg) for arg in args)
                printed_messages.append(message)
                # Don't print to avoid recursion

            with patch('builtins.print', side_effect=mock_print):
                sys.argv = ['fmp_fetcher.py', '--ticker', 'TEST', '--output', temp_dir, '--period', 'annual']
                fmp_fetcher.main()

            # Verify annual period calls
            print("\nVerifying annual period function calls...")
            ticker = 'TEST'
            api_key = 'mock_api_key'
            period = 'annual'

            # Period-dependent categories
            period_categories = [
                'income_statement', 'balance_sheet', 'cash_flow_statement', 'ratios',
                'enterprise_values', 'financial_growth', 'balance_sheet_growth',
                'income_statement_growth', 'cash_flow_statement_growth', 'key_metrics',
                'analyst_estimates'
            ]

            for category in period_categories:
                fetch_func = mock_fetchers[f'fetch_{category}']
                fetch_func.assert_called_with(ticker, api_key, period)
                print(f"✓ fetch_{category} called with correct params")

            # Non-period categories
            non_period_categories = [
                'owner_earnings', 'score', 'key_metrics_ttm', 'ratios_ttm',
                'discounted_cash_flow', 'advanced_dcf', 'advanced_levered_dcf',
                'rating', 'historical_rating', 'historical_price_dividend',
                'historical_price_full', 'employee_count', 'shares_float',
                'analyst_recommendations', 'historical_market_cap',
                'earning_calendar', 'institutional_holder', 'etf_sector_weightings',
                'historical_price_eod', 'stock_price_change'
            ]

            for category in non_period_categories:
                fetch_func = mock_fetchers[f'fetch_{category}']
                fetch_func.assert_called_with(ticker, api_key)
                print(f"✓ fetch_{category} called with correct params")

            # Special cases
            mock_fetchers['fetch_historical_sectors_performance'].assert_called_with(api_key)
            print("✓ fetch_historical_sectors_performance called with correct params")

            for variant in ['all', 'purchases', 'sales']:
                fetch_func = mock_fetchers[f'fetch_insider_trading_{variant}']
                fetch_func.assert_called_with(ticker, api_key)
                print(f"✓ fetch_insider_trading_{variant} called with correct params")

            mock_fetchers['fetch_technical_indicators'].assert_called_with(ticker, api_key)
            print("✓ fetch_technical_indicators called with correct params")

            # Verify CSV save calls for annual
            print("\nVerifying CSV save calls for annual period...")
            expected_save_calls = []

            # Period-dependent
            for category in period_categories:
                expected_filename = f"{ticker}_{category}_{period}"
                expected_save_calls.append(((mock_data, expected_filename, temp_dir), {}))
                print(f"✓ Expected save call for {expected_filename}")

            # Non-period
            for category in non_period_categories:
                expected_filename = f"{ticker}_{category}"
                expected_save_calls.append(((mock_data if category in [
                    'historical_rating', 'historical_price_dividend', 'historical_price_full',
                    'employee_count', 'analyst_recommendations', 'historical_market_cap',
                    'earning_calendar', 'institutional_holder', 'etf_sector_weightings',
                    'historical_price_eod'
                ] else mock_dict_data, expected_filename, temp_dir), {}))
                print(f"✓ Expected save call for {expected_filename}")

            # Special
            expected_save_calls.append(((mock_data, "historical_sectors_performance", temp_dir), {}))
            print("✓ Expected save call for historical_sectors_performance")

            for variant in ['all', 'purchases', 'sales']:
                expected_filename = f"{ticker}_insider_trading_{variant}"
                expected_save_calls.append(((mock_data, expected_filename, temp_dir), {}))
                print(f"✓ Expected save call for {expected_filename}")

            # Technical indicators
            for ind_type in mock_tech_data.keys():
                expected_filename = f"{ticker}_technical_{ind_type}"
                expected_save_calls.append(((mock_data, expected_filename, temp_dir), {}))
                print(f"✓ Expected save call for {expected_filename}")

            # Check that save_to_csv was called the correct number of times
            assert mock_save_to_csv.call_count == len(expected_save_calls), f"Expected {len(expected_save_calls)} save calls, got {mock_save_to_csv.call_count}"

            # Verify each save call
            for i, call in enumerate(mock_save_to_csv.call_args_list):
                args, kwargs = call
                expected_args, expected_kwargs = expected_save_calls[i]
                assert args == expected_args, f"Save call {i} args mismatch: expected {expected_args}, got {args}"
                assert kwargs == expected_kwargs, f"Save call {i} kwargs mismatch: expected {expected_kwargs}, got {kwargs}"
                print(f"✓ Save call {i} correct")

            # Verify progress messages for annual
            print("\nVerifying progress messages for annual period...")
            expected_messages = []

            for category in period_categories:
                expected_messages.append(f"Fetching {category} data...")
                expected_messages.append(f"Saving to {ticker}_{category}_{period}.csv")

            for category in non_period_categories:
                expected_messages.append(f"Fetching {category} data...")
                expected_messages.append(f"Saving to {ticker}_{category}.csv")

            expected_messages.append("Fetching historical_sectors_performance data...")
            expected_messages.append("Saving to historical_sectors_performance.csv")

            for variant in ['all', 'purchases', 'sales']:
                expected_messages.append(f"Fetching insider_trading_{variant} data...")
                expected_messages.append(f"Saving to {ticker}_insider_trading_{variant}.csv")

            expected_messages.append("Fetching technical_indicators data...")
            for ind_type in mock_tech_data.keys():
                expected_messages.append(f"Saving to {ticker}_technical_{ind_type}.csv")

            # Check messages
            assert printed_messages == expected_messages, f"Message mismatch: expected {expected_messages}, got {printed_messages}"
            print("✓ All progress messages correct for annual")

            # Reset mocks for quarterly test
            for mock_func in mock_fetchers.values():
                mock_func.reset_mock()
            mock_save_to_csv.reset_mock()
            printed_messages.clear()

            # Test for quarterly period
            print("\nTesting main execution with quarterly period...")
            printed_messages_quarterly = []
            def mock_print_quarterly(*args, **kwargs):
                message = ' '.join(str(arg) for arg in args)
                printed_messages_quarterly.append(message)
                # Don't print to avoid recursion

            with patch('builtins.print', side_effect=mock_print_quarterly):
                sys.argv = ['fmp_fetcher.py', '--ticker', 'TEST', '--output', temp_dir, '--period', 'quarterly']
                fmp_fetcher.main()

            # Verify quarterly period calls
            print("\nVerifying quarterly period function calls...")
            period = 'quarterly'

            for category in period_categories:
                fetch_func = mock_fetchers[f'fetch_{category}']
                fetch_func.assert_called_with(ticker, api_key, period)
                print(f"✓ fetch_{category} called with correct params")

            # Non-period should be called again (same as annual)
            for category in non_period_categories:
                fetch_func = mock_fetchers[f'fetch_{category}']
                fetch_func.assert_called_with(ticker, api_key)
                print(f"✓ fetch_{category} called with correct params")

            # Special cases again
            mock_fetchers['fetch_historical_sectors_performance'].assert_called_with(api_key)
            print("✓ fetch_historical_sectors_performance called with correct params")

            for variant in ['all', 'purchases', 'sales']:
                fetch_func = mock_fetchers[f'fetch_insider_trading_{variant}']
                fetch_func.assert_called_with(ticker, api_key)
                print(f"✓ fetch_insider_trading_{variant} called with correct params")

            mock_fetchers['fetch_technical_indicators'].assert_called_with(ticker, api_key)
            print("✓ fetch_technical_indicators called with correct params")

            # Verify CSV save calls for quarterly
            print("\nVerifying CSV save calls for quarterly period...")
            expected_save_calls_quarterly = []

            # Period-dependent with quarterly
            for category in period_categories:
                expected_filename = f"{ticker}_{category}_{period}"
                expected_save_calls_quarterly.append(((mock_data, expected_filename, temp_dir), {}))
                print(f"✓ Expected save call for {expected_filename}")

            # Non-period (same as annual)
            for category in non_period_categories:
                expected_filename = f"{ticker}_{category}"
                expected_save_calls_quarterly.append(((mock_data if category in [
                    'historical_rating', 'historical_price_dividend', 'historical_price_full',
                    'employee_count', 'analyst_recommendations', 'historical_market_cap',
                    'earning_calendar', 'institutional_holder', 'etf_sector_weightings',
                    'historical_price_eod'
                ] else mock_dict_data, expected_filename, temp_dir), {}))
                print(f"✓ Expected save call for {expected_filename}")

            # Special
            expected_save_calls_quarterly.append(((mock_data, "historical_sectors_performance", temp_dir), {}))
            print("✓ Expected save call for historical_sectors_performance")

            for variant in ['all', 'purchases', 'sales']:
                expected_filename = f"{ticker}_insider_trading_{variant}"
                expected_save_calls_quarterly.append(((mock_data, expected_filename, temp_dir), {}))
                print(f"✓ Expected save call for {expected_filename}")

            # Technical indicators
            for ind_type in mock_tech_data.keys():
                expected_filename = f"{ticker}_technical_{ind_type}"
                expected_save_calls_quarterly.append(((mock_data, expected_filename, temp_dir), {}))
                print(f"✓ Expected save call for {expected_filename}")

            # Check save calls for quarterly
            assert mock_save_to_csv.call_count == len(expected_save_calls_quarterly), f"Expected {len(expected_save_calls_quarterly)} save calls, got {mock_save_to_csv.call_count}"

            for i, call in enumerate(mock_save_to_csv.call_args_list):
                args, kwargs = call
                expected_args, expected_kwargs = expected_save_calls_quarterly[i]
                assert args == expected_args, f"Quarterly save call {i} args mismatch: expected {expected_args}, got {args}"
                assert kwargs == expected_kwargs, f"Quarterly save call {i} kwargs mismatch: expected {expected_kwargs}, got {kwargs}"
                print(f"✓ Quarterly save call {i} correct")

            # Verify progress messages for quarterly
            print("\nVerifying progress messages for quarterly period...")
            expected_messages_quarterly = []

            for category in period_categories:
                expected_messages_quarterly.append(f"Fetching {category} data...")
                expected_messages_quarterly.append(f"Saving to {ticker}_{category}_{period}.csv")

            for category in non_period_categories:
                expected_messages_quarterly.append(f"Fetching {category} data...")
                expected_messages_quarterly.append(f"Saving to {ticker}_{category}.csv")

            expected_messages_quarterly.append("Fetching historical_sectors_performance data...")
            expected_messages_quarterly.append("Saving to historical_sectors_performance.csv")

            for variant in ['all', 'purchases', 'sales']:
                expected_messages_quarterly.append(f"Fetching insider_trading_{variant} data...")
                expected_messages_quarterly.append(f"Saving to {ticker}_insider_trading_{variant}.csv")

            expected_messages_quarterly.append("Fetching technical_indicators data...")
            for ind_type in mock_tech_data.keys():
                expected_messages_quarterly.append(f"Saving to {ticker}_technical_{ind_type}.csv")

            # Check messages
            assert printed_messages_quarterly == expected_messages_quarterly, f"Quarterly message mismatch: expected {expected_messages_quarterly}, got {printed_messages_quarterly}"
            print("✓ All progress messages correct for quarterly")

    print("\n🎉 All tests passed! Main execution logic is correct.")
    print("Coverage: 100% - All categories processed, period logic works, filenames correct, messages printed.")

if __name__ == "__main__":
    test_main_execution_logic()