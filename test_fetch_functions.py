#!/usr/bin/env python3

import fmp_fetcher

# Mock fetch_data to return the URL instead of fetching
original_fetch_data = fmp_fetcher.fetch_data

def mock_fetch_data(url):
    print(f"Mock fetching URL: {url}")
    return url  # Return the URL for verification

fmp_fetcher.fetch_data = mock_fetch_data

# List of function names
functions = [
    'fetch_income_statement',
    'fetch_balance_sheet',
    'fetch_cash_flow_statement',
    'fetch_ratios',
    'fetch_enterprise_values',
    'fetch_financial_growth',
    'fetch_balance_sheet_growth',
    'fetch_income_statement_growth',
    'fetch_cash_flow_statement_growth',
    'fetch_key_metrics',
    'fetch_analyst_estimates'
]

ticker = 'AAPL'
api_key = 'test'
period = 'annual'

print("Testing annual period for all functions:")
results = {}
for func_name in functions:
    func = getattr(fmp_fetcher, func_name)
    url = func(ticker, api_key, period)
    results[func_name] = url
    print(f"{func_name}: URL = {url}")

# Test one function for both periods: fetch_income_statement
print("\nTesting both periods for fetch_income_statement:")
for p in ['annual', 'quarterly']:
    url = fmp_fetcher.fetch_income_statement(ticker, api_key, p)
    print(f"Period {p}: URL = {url}")

# Verify URL formatting
print("\nVerifying URL formatting:")
expected_base = 'https://financialmodelingprep.com/api/v3/'
for func_name, url in results.items():
    category = func_name.replace('fetch_', '')
    if category == 'balance_sheet':
        category = 'balance-sheet-statement'
    elif category == 'cash_flow_statement':
        category = 'cash-flow-statement'
    elif category == 'income_statement':
        category = 'income-statement'
    elif category == 'analyst_estimates':
        category = 'analyst-estimates'
    elif category == 'key_metrics':
        category = 'key-metrics'
    elif category == 'enterprise_values':
        category = 'enterprise-values'
    elif category == 'financial_growth':
        category = 'financial-growth'
    elif category == 'balance_sheet_growth':
        category = 'balance-sheet-statement-growth'
    elif category == 'income_statement_growth':
        category = 'income-statement-growth'
    elif category == 'cash_flow_statement_growth':
        category = 'cash-flow-statement-growth'

    expected_url = f"{expected_base}{category}/{ticker}?period={period}&apikey={api_key}"
    if url == expected_url:
        print(f"{func_name}: PASS")
    else:
        print(f"{func_name}: FAIL - Expected {expected_url}, got {url}")

# Restore original fetch_data
fmp_fetcher.fetch_data = original_fetch_data