#!/usr/bin/env python3

import fmp_fetcher

# Mock fetch_data to capture calls and return mock data
original_fetch_data = fmp_fetcher.fetch_data
fetch_calls = []

def mock_fetch_data(url):
    print(f"Mock fetching URL: {url}")
    fetch_calls.append(url)
    # Return a mock list of data for each indicator
    return [{'date': '2023-01-01', 'value': 100.0}]

fmp_fetcher.fetch_data = mock_fetch_data

# Test the function
ticker = 'AAPL'
api_key = 'test'

print("Testing fetch_technical_indicators...")
result = fmp_fetcher.fetch_technical_indicators(ticker, api_key)

# Verify results
print("\nVerifying results...")

# Check that all 10 indicator types are processed
expected_types = ['sma', 'ema', 'rsi', 'macd', 'wma', 'dema', 'tema', 'williams', 'adx', 'standarddeviation']
print(f"Expected indicator types: {expected_types}")
print(f"Actual result keys: {list(result.keys())}")

if set(result.keys()) == set(expected_types):
    print("PASS: All 10 indicator types present in result")
else:
    print("FAIL: Mismatch in indicator types")

# Check number of fetch_data calls
print(f"Number of fetch_data calls: {len(fetch_calls)}")
if len(fetch_calls) == 10:
    print("PASS: fetch_data called 10 times")
else:
    print("FAIL: Incorrect number of fetch_data calls")

# Check URL formatting for first few types
expected_base = 'https://financialmodelingprep.com/api/v3/technical_indicator/daily/AAPL?type='
expected_urls = [
    f"{expected_base}sma&period=252&apikey=test",
    f"{expected_base}ema&period=50&apikey=test",
    f"{expected_base}rsi&period=14&apikey=test"
]

print("\nChecking URL formatting for first 3 types:")
for i, expected_url in enumerate(expected_urls):
    actual_url = fetch_calls[i]
    if actual_url == expected_url:
        print(f"URL {i+1}: PASS")
    else:
        print(f"URL {i+1}: FAIL - Expected {expected_url}, got {actual_url}")

# Check return structure
print("\nChecking return structure:")
if isinstance(result, dict):
    print("PASS: Result is a dictionary")
    all_values_lists = all(isinstance(v, list) for v in result.values() if v is not None)
    if all_values_lists:
        print("PASS: All values are lists (or None)")
    else:
        print("FAIL: Some values are not lists")
else:
    print("FAIL: Result is not a dictionary")

# Restore original fetch_data
fmp_fetcher.fetch_data = original_fetch_data

print("\nTest completed.")