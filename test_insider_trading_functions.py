#!/usr/bin/env python3

import fmp_fetcher

# Mock fetch_data to return the URL instead of fetching
original_fetch_data = fmp_fetcher.fetch_data

def mock_fetch_data(url):
    print(f"Mock fetching URL: {url}")
    return url  # Return the URL for verification

fmp_fetcher.fetch_data = mock_fetch_data

# Test parameters
ticker = 'AAPL'
api_key = 'test'

# Test functions
functions = [
    ('fetch_insider_trading_all', 'all'),
    ('fetch_insider_trading_purchases', 'purchases'),
    ('fetch_insider_trading_sales', 'sales')
]

print("Testing insider trading fetch functions:")
results = {}
for func_name, transaction_type in functions:
    func = getattr(fmp_fetcher, func_name)
    url = func(ticker, api_key)
    results[func_name] = url
    print(f"{func_name}: URL = {url}")

# Verify URL formatting
print("\nVerifying URL formatting:")
all_passed = True
for func_name, transaction_type in functions:
    url = results[func_name]
    expected_url = fmp_fetcher.ENDPOINTS['insider_trading'][transaction_type].format(ticker=ticker, apikey=api_key)
    if url == expected_url:
        print(f"{func_name}: PASS")
    else:
        print(f"{func_name}: FAIL - Expected {expected_url}, got {url}")
        all_passed = False

# Additional verification: check transaction types in URLs
print("\nVerifying transaction types in URLs:")
for func_name, transaction_type in functions:
    url = results[func_name]
    if transaction_type == 'all':
        if 'transactionType=' not in url:
            print(f"{func_name}: PASS - No transactionType parameter for 'all'")
        else:
            print(f"{func_name}: FAIL - Unexpected transactionType in 'all' URL")
            all_passed = False
    elif transaction_type == 'purchases':
        if 'transactionType=purchase' in url:
            print(f"{func_name}: PASS - Correct transactionType=purchase")
        else:
            print(f"{func_name}: FAIL - Missing or incorrect transactionType for purchases")
            all_passed = False
    elif transaction_type == 'sales':
        if 'transactionType=sale' in url:
            print(f"{func_name}: PASS - Correct transactionType=sale")
        else:
            print(f"{func_name}: FAIL - Missing or incorrect transactionType for sales")
            all_passed = False

# Restore original fetch_data
fmp_fetcher.fetch_data = original_fetch_data

if all_passed:
    print("\nAll tests passed!")
else:
    print("\nSome tests failed!")