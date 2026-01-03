# Proposal Plan for Fundamental Ratios Calculator CLI Script

## Overview

This proposal outlines the design and implementation plan for a Python script that serves as a command-line interface (CLI) tool to compute fundamental financial ratios. The script will include a `ratios` class with methods to calculate various ratios based on provided financial inputs. The CLI will allow users to specify the ratio to compute and pass the required input values as arguments.

## Requirements

- **Class Design**: A `ratios` class with:
  - `__init__()` method that accepts required parameters.
  - Methods named `compute_{ratio}_metric(self, required_input1, ..., required_inputn)` that perform the calculation, validate inputs, inform users of missing inputs, and return the result.

- **CLI Interface**: The script can be invoked as `python3 command -m {ratio_name} {input1} {input2} ...` where inputs are the values needed for the ratio.

- **Ratios to Implement**: A comprehensive list of fundamental ratios covering liquidity, profitability, solvency, efficiency, valuation, and per-share metrics, based on the provided FUNDAMENTAL RATIOS lists.

## List of Ratios

The following is a categorized list of ratios with their formulas and required inputs. This covers the unique ratios from both provided lists, with standard financial formulas used.

### Liquidity Ratios

- **Current Ratio**: current_assets / current_liabilities
  - Inputs: current_assets, current_liabilities

- **Quick Ratio**: (current_assets - inventory) / current_liabilities
  - Inputs: current_assets, inventory, current_liabilities

- **Cash Ratio**: cash_and_cash_equivalents / current_liabilities
  - Inputs: cash_and_cash_equivalents, current_liabilities

### Efficiency Ratios

- **Days of Sales Outstanding (DSO)**: (accounts_receivable / total_revenue) * 365
  - Inputs: accounts_receivable, total_revenue

- **Days of Inventory Outstanding (DIO)**: (inventory / cost_of_goods_sold) * 365
  - Inputs: inventory, cost_of_goods_sold

- **Operating Cycle**: DSO + DIO
  - Inputs: accounts_receivable, total_revenue, inventory, cost_of_goods_sold

- **Days of Payables Outstanding (DPO)**: (accounts_payable / cost_of_goods_sold) * 365
  - Inputs: accounts_payable, cost_of_goods_sold

- **Cash Conversion Cycle**: Operating Cycle - DPO
  - Inputs: accounts_receivable, total_revenue, inventory, cost_of_goods_sold, accounts_payable

- **Receivables Turnover**: total_revenue / accounts_receivable
  - Inputs: total_revenue, accounts_receivable

- **Payables Turnover**: cost_of_goods_sold / accounts_payable
  - Inputs: cost_of_goods_sold, accounts_payable

- **Inventory Turnover**: cost_of_goods_sold / inventory
  - Inputs: cost_of_goods_sold, inventory

- **Fixed Asset Turnover**: total_revenue / fixed_assets
  - Inputs: total_revenue, fixed_assets

- **Asset Turnover**: total_revenue / total_assets
  - Inputs: total_revenue, total_assets

### Profitability Ratios

- **Gross Profit Margin**: (gross_profit / total_revenue) * 100
  - Inputs: gross_profit, total_revenue

- **Operating Profit Margin**: (operating_income / total_revenue) * 100
  - Inputs: operating_income, total_revenue

- **Pretax Profit Margin**: (pretax_income / total_revenue) * 100
  - Inputs: pretax_income, total_revenue

- **Net Profit Margin**: (net_income / total_revenue) * 100
  - Inputs: net_income, total_revenue

- **Return on Assets (ROA)**: (net_income / total_assets) * 100
  - Inputs: net_income, total_assets

- **Return on Equity (ROE)**: (net_income / shareholders_equity) * 100
  - Inputs: net_income, shareholders_equity

- **Return on Capital Employed (ROCE)**: (ebit / capital_employed) * 100
  - Inputs: ebit, capital_employed

- **Effective Tax Rate**: (income_tax_expense / pretax_income) * 100
  - Inputs: income_tax_expense, pretax_income

- **Net Income Per EBT**: net_income / ebt
  - Inputs: net_income, ebt

- **EBT Per EBIT**: ebt / ebit
  - Inputs: ebt, ebit

- **EBIT Per Revenue**: ebit / total_revenue
  - Inputs: ebit, total_revenue

### Solvency Ratios

- **Debt Ratio**: total_debt / total_assets
  - Inputs: total_debt, total_assets

- **Debt Equity Ratio**: total_debt / shareholders_equity
  - Inputs: total_debt, shareholders_equity

- **Long Term Debt to Capitalization**: long_term_debt / (long_term_debt + shareholders_equity)
  - Inputs: long_term_debt, shareholders_equity

- **Total Debt to Capitalization**: total_debt / (total_debt + shareholders_equity)
  - Inputs: total_debt, shareholders_equity

- **Interest Coverage**: ebit / interest_expense
  - Inputs: ebit, interest_expense

- **Cash Flow to Debt Ratio**: operating_cash_flow / total_debt
  - Inputs: operating_cash_flow, total_debt

- **Company Equity Multiplier**: total_assets / shareholders_equity
  - Inputs: total_assets, shareholders_equity

### Valuation Ratios

- **Price Book Value Ratio**: market_price_per_share / book_value_per_share
  - Inputs: market_price_per_share, book_value_per_share

- **Price to Sales Ratio**: market_cap / total_revenue
  - Inputs: market_cap, total_revenue

- **Price Earnings Ratio**: market_price_per_share / earnings_per_share
  - Inputs: market_price_per_share, earnings_per_share

- **Price to Free Cash Flows Ratio**: market_price_per_share / free_cash_flow_per_share
  - Inputs: market_price_per_share, free_cash_flow_per_share

- **Dividend Yield**: dividends_per_share / market_price_per_share
  - Inputs: dividends_per_share, market_price_per_share

- **Dividend Payout Ratio**: dividends_per_share / earnings_per_share
  - Inputs: dividends_per_share, earnings_per_share

- **Enterprise Value Multiple**: enterprise_value / ebitda
  - Inputs: enterprise_value, ebitda

- **Price Cash Flow Ratio**: market_cap / operating_cash_flow
  - Inputs: market_cap, operating_cash_flow

### Per-Share Metrics

- **Revenue Per Share**: total_revenue / number_of_shares_outstanding
  - Inputs: total_revenue, number_of_shares_outstanding

- **Net Income Per Share**: net_income / number_of_shares_outstanding
  - Inputs: net_income, number_of_shares_outstanding

- **Operating Cash Flow Per Share**: operating_cash_flow / number_of_shares_outstanding
  - Inputs: operating_cash_flow, number_of_shares_outstanding

- **Free Cash Flow Per Share**: free_cash_flow / number_of_shares_outstanding
  - Inputs: free_cash_flow, number_of_shares_outstanding

- **Cash Per Share**: cash_and_cash_equivalents / number_of_shares_outstanding
  - Inputs: cash_and_cash_equivalents, number_of_shares_outstanding

- **Book Value Per Share**: shareholders_equity / number_of_shares_outstanding
  - Inputs: shareholders_equity, number_of_shares_outstanding

- **Tangible Book Value Per Share**: (shareholders_equity - intangible_assets) / number_of_shares_outstanding
  - Inputs: shareholders_equity, intangible_assets, number_of_shares_outstanding

- **Shareholders Equity Per Share**: shareholders_equity / number_of_shares_outstanding
  - Inputs: shareholders_equity, number_of_shares_outstanding

- **Interest Debt Per Share**: interest_bearing_debt / number_of_shares_outstanding
  - Inputs: interest_bearing_debt, number_of_shares_outstanding

- **Capex Per Share**: capital_expenditures / number_of_shares_outstanding
  - Inputs: capital_expenditures, number_of_shares_outstanding

(Note: This is a subset for illustration. The full implementation will include all ratios from the provided lists, with formulas derived from standard financial practices. Additional ratios like grahamNumber, roic, etc., will have their respective formulas and inputs defined.)

## Script Architecture

- **Class `ratios`**:
  - `__init__(self)`: No required parameters, as inputs are provided per method call.

- **Compute Methods**:
  - Each method named `compute_{ratio_name}_metric(self, *args)` where args are the required inputs in order.
  - Validate that all inputs are provided and not None.
  - Handle division by zero and print appropriate error messages.
  - If inputs missing, print "Missing required input: {input_name}".
  - Calculate the ratio and return it, perhaps with print for CLI output.

- **CLI**:
  - Use `argparse` for parsing.
  - Argument: `-m` or `--metric` for the ratio name (e.g., current_ratio).
  - Positional arguments: the input values in the order defined for the ratio.
  - Map the metric name to the method, instantiate the class, call the method with args, print the result.

- **Script Name**: `command.py` (as referred in the example).

## Implementation Plan

### Atomic Subtasks (To-Do List)

- [ ] Compile full list of unique ratios from both provided FUNDAMENTAL RATIOS lists.
- [ ] Research and define standard formulas and required inputs for each ratio.
- [ ] Group ratios into categories for organized implementation.
- [ ] Design the `ratios` class structure and decide on __init__ parameters (none required).
- [ ] Create the Python script file `command.py`.
- [ ] Implement CLI argument parsing with argparse (metric flag and positional inputs).
- [ ] Implement the `ratios` class __init__ method.
- [ ] Implement compute methods for all Liquidity ratios.
- [ ] Implement compute methods for all Efficiency ratios.
- [ ] Implement compute methods for all Profitability ratios.
- [ ] Implement compute methods for all Solvency ratios.
- [ ] Implement compute methods for all Valuation ratios.
- [ ] Implement compute methods for all Per-Share metrics.
- [ ] Add input validation (check for None, handle zero divisions, validate numeric types).
- [ ] Add informative error messages for missing or invalid inputs.
- [ ] Test individual methods with sample inputs to ensure correct calculations.
- [ ] Test the CLI interface with example commands like the provided current_ratio example.
- [ ] Handle edge cases (negative values, very small/large numbers).
- [ ] Add docstrings and comments to the code for maintainability.
- [ ] Perform integration testing for the full script with various ratios.
- [ ] Document usage instructions in a README or script comments.

## Tools and Technologies

- **Python**: Core language for scripting.
- **Argparse**: For command-line argument parsing.
- **Math**: Standard library for calculations.

## Expected Outcomes

- A robust CLI script that accurately computes any specified fundamental ratio.
- User-friendly error handling and feedback.
- Extensible code structure for adding more ratios in the future.
- Clean, modular implementation following the specified design.

## Timeline and Resources

- Estimated completion: 2-4 weeks, depending on the number of ratios and testing thoroughness.
- Resources: Python 3 environment, access to financial ratio definitions for verification.

This plan provides an atomic, checkable breakdown for implementing the fundamental ratios calculator CLI script as per the specified design and requirements.