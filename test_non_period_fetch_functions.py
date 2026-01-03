#!/usr/bin/env python3

import fmp_fetcher

# Mock fetch_data to return the URL instead of fetching
original_fetch_data = fmp_fetcher.fetch_data

def mock_fetch_data(url):
    print(f"Mock fetching URL: {url}")
    return url  # Return the URL for verification

fmp_fetcher.fetch_data = mock_fetch_data

# List of non-period function names
functions = [
    'fetch_owner_earnings',
    'fetch_score',
    'fetch_key_metrics_ttm',
    'fetch_ratios_ttm',
    'fetch_discounted_cash_flow',
    'fetch_advanced_dcf',
    'fetch_advanced_levered_dcf',
    'fetch_rating',
    'fetch_historical_rating',
    'fetch_historical_price_dividend',
    'fetch_historical_price_full',
    'fetch_historical_sectors_performance',  # Special: no ticker
    'fetch_employee_count',
    'fetch_shares_float',
    'fetch_analyst_recommendations',
    'fetch_historical_market_cap',
    'fetch_earning_calendar',
    'fetch_institutional_holder',
    'fetch_etf_sector_weightings',
    'fetch_historical_price_eod',
    'fetch_stock_price_change'
]

ticker = 'AAPL'
api_key = 'test'

print("Testing non-period fetch functions:")
results = {}
for func_name in functions:
    func = getattr(fmp_fetcher, func_name)
    if func_name == 'fetch_historical_sectors_performance':
        url = func(api_key)
    else:
        url = func(ticker, api_key)
    results[func_name] = url
    print(f"{func_name}: URL = {url}")

# Verify URL formatting
print("\nVerifying URL formatting:")
for func_name, url in results.items():
    category = func_name.replace('fetch_', '')
    if category == 'historical_sectors_performance':
        expected_url = fmp_fetcher.ENDPOINTS[category]['no_period'].format(apikey=api_key)
    else:
        expected_url = fmp_fetcher.ENDPOINTS[category]['no_period'].format(ticker=ticker, apikey=api_key)
    if url == expected_url:
        print(f"{func_name}: PASS")
    else:
        print(f"{func_name}: FAIL - Expected {expected_url}, got {url}")

# Restore original fetch_data
fmp_fetcher.fetch_data = original_fetch_data