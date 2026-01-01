import pandas as pd
import json
import os
import csv
import logging
from datetime import datetime
import numpy as np
from scipy.stats import norm
from sklearn.linear_model import LinearRegression
import hashlib

from ..domain.repositories.financial_data_repository import FinancialDataRepository
from ..domain.services.fundamental_analysis_service import FundamentalAnalysisService

class RatioValidator:
    def __init__(self, conn=None):
        self.conn = conn  # For backward compatibility in tests
        self.repo = FinancialDataRepository()
        self.service = FundamentalAnalysisService()

    def compute_current_ratio(self, ticker_symbol, period_type, fiscal_date):
        return self.service.compute_current_ratio(ticker_symbol, period_type, fiscal_date)

    def compute_quick_ratio(self, ticker_symbol, period_type, fiscal_date):
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get balance sheet statement
        statement = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not statement:
            return None

        data = json.loads(statement[0])

        total_current_assets = data.get('totalCurrentAssets')
        inventory = data.get('inventory')
        total_current_liabilities = data.get('totalCurrentLiabilities')

        if total_current_assets is None or total_current_liabilities is None:
            return None

        quick_assets = total_current_assets - inventory if inventory is not None else total_current_assets

        if total_current_liabilities == 0:
            return None  # Division by zero

        return quick_assets / total_current_liabilities

    def compute_cash_ratio(self, ticker_symbol, period_type, fiscal_date):
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get balance sheet statement
        statement = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not statement:
            return None

        data = json.loads(statement[0])

        cash_and_equivalents = data.get('cashAndCashEquivalents')
        total_current_liabilities = data.get('totalCurrentLiabilities')

        if cash_and_equivalents is None or total_current_liabilities is None:
            return None

        if total_current_liabilities == 0:
            return None  # Division by zero

        return cash_and_equivalents / total_current_liabilities

    def compute_days_of_sales_outstanding(self):
        pass

    def compute_days_of_inventory_outstanding(self):
        pass

    def compute_operating_cycle(self):
        pass

    def compute_days_of_payables_outstanding(self):
        pass

    def compute_cash_conversion_cycle(self):
        pass

    def compute_gross_profit_margin(self, ticker_symbol, period_type, fiscal_date):
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get income statement
        statement = self.conn.execute("""
            SELECT statement_data FROM income_statement
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not statement:
            return None

        data = json.loads(statement[0])

        revenue = data.get('revenue')
        cost_of_revenue = data.get('costOfRevenue')

        if revenue is None:
            return None

        if revenue == 0:
            return None  # Division by zero

        gross_profit = revenue - cost_of_revenue if cost_of_revenue is not None else revenue

        return gross_profit / revenue

    def compute_operating_profit_margin(self, ticker_symbol, period_type, fiscal_date):
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get income statement
        statement = self.conn.execute("""
            SELECT statement_data FROM income_statement
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not statement:
            return None

        data = json.loads(statement[0])

        revenue = data.get('revenue')
        operating_income = data.get('operatingIncome')

        if revenue is None or operating_income is None:
            return None

        if revenue == 0:
            return None  # Division by zero

        return operating_income / revenue

    def compute_pretax_profit_margin(self):
        pass

    def compute_net_profit_margin(self, ticker_symbol, period_type, fiscal_date):
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get income statement
        statement = self.conn.execute("""
            SELECT statement_data FROM income_statement
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not statement:
            return None

        data = json.loads(statement[0])

        revenue = data.get('revenue')
        net_income = data.get('netIncome')

        if revenue is None or net_income is None:
            return None

        if revenue == 0:
            return None  # Division by zero

        return net_income / revenue

    def compute_effective_tax_rate(self):
        pass

    def compute_return_on_assets(self, ticker_symbol, period_type, fiscal_date):
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get income statement for net income
        income_statement = self.conn.execute("""
            SELECT statement_data FROM income_statement
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        # Get balance sheet for total assets
        balance_statement = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not income_statement or not balance_statement:
            return None

        income_data = json.loads(income_statement[0])
        balance_data = json.loads(balance_statement[0])

        net_income = income_data.get('netIncome')
        total_assets = balance_data.get('totalAssets')

        if net_income is None or total_assets is None:
            return None

        if total_assets == 0:
            return None  # Division by zero

        return net_income / total_assets

    def compute_return_on_equity(self, ticker_symbol, period_type, fiscal_date):
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get income statement for net income
        income_statement = self.conn.execute("""
            SELECT statement_data FROM income_statement
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        # Get balance sheet for total shareholders' equity
        balance_statement = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not income_statement or not balance_statement:
            return None

        income_data = json.loads(income_statement[0])
        balance_data = json.loads(balance_statement[0])

        net_income = income_data.get('netIncome')
        total_shareholders_equity = balance_data.get('totalShareholdersEquity')

        if net_income is None or total_shareholders_equity is None:
            return None

        if total_shareholders_equity == 0:
            return None  # Division by zero

        return net_income / total_shareholders_equity

    def compute_dupont_analysis(self, ticker_symbol, period_type, fiscal_date):
        """
        Compute ROE using the DuPont formula and compare with Phase 3 ROE.

        The DuPont formula decomposes ROE as: ROE = Net Profit Margin * Asset Turnover * Equity Multiplier
        Where Equity Multiplier = 1 + Debt-to-Equity Ratio.

        This method retrieves necessary financial ratios, calculates the DuPont ROE, and compares it
        to the ROE computed from Phase 3 (direct calculation from net income and equity).
        Handles missing data by returning None for unavailable components and flags incompleteness.
        Logs warnings for missing data and calculation steps for robustness.

        Args:
            ticker_symbol (str): The stock ticker symbol (e.g., 'AAPL').
            period_type (str): The period type ('annual' or 'quarterly').
            fiscal_date (str): The fiscal date in 'YYYY-MM-DD' format.

        Returns:
            dict: A dictionary containing:
                - 'calculated_roe' (float or None): ROE calculated via DuPont formula.
                - 'phase3_roe' (float or None): ROE from Phase 3 computation.
                - 'match' (bool or None): True if both ROEs are equal (within floating point precision), False otherwise, None if either is None.
                - 'decomposition' (dict): Dictionary with 'net_profit_margin', 'asset_turnover', 'equity_multiplier'.
                - 'percentage_difference' (float or None): Percentage difference between calculated and Phase 3 ROE if both available and Phase 3 ROE != 0.
                - 'missing_components' (list): List of component names that could not be computed.
                - 'incomplete' (bool): True if any component is missing, False otherwise.

        Raises:
            ValueError: If input parameters are not strings.
        """
        # Input validation
        if not isinstance(ticker_symbol, str) or not isinstance(period_type, str) or not isinstance(fiscal_date, str):
            raise ValueError("ticker_symbol, period_type, and fiscal_date must be strings.")

        logging.info(f"Starting DuPont analysis for {ticker_symbol} ({period_type}, {fiscal_date}).")

        # Compute individual components
        net_profit_margin = self.compute_net_profit_margin(ticker_symbol, period_type, fiscal_date)
        asset_turnover = self.compute_asset_turnover(ticker_symbol, period_type, fiscal_date)
        debt_to_equity = self.compute_debt_to_equity_ratio(ticker_symbol, period_type, fiscal_date)

        # Calculate equity multiplier
        equity_multiplier = None
        if debt_to_equity is not None:
            equity_multiplier = 1 + debt_to_equity
            logging.info(".6f")
        else:
            logging.warning(f"Debt-to-equity ratio is missing for {ticker_symbol} ({period_type}, {fiscal_date}). Equity multiplier set to None.")

        # Calculate DuPont ROE
        calculated_roe = None
        if net_profit_margin is not None and asset_turnover is not None and equity_multiplier is not None:
            calculated_roe = net_profit_margin * asset_turnover * equity_multiplier
            logging.info(".6f")

        # Compute Phase 3 ROE for comparison
        phase3_roe = self.compute_return_on_equity(ticker_symbol, period_type, fiscal_date)

        # Determine match
        match = None
        if calculated_roe is not None and phase3_roe is not None:
            match = abs(calculated_roe - phase3_roe) < 1e-6  # Account for floating point precision
            if not match:
                logging.warning(".6f")

        # Calculate percentage difference if both available and phase3_roe != 0
        percentage_difference = None
        if calculated_roe is not None and phase3_roe is not None and phase3_roe != 0:
            percentage_difference = ((calculated_roe - phase3_roe) / phase3_roe) * 100

        # Decomposition dictionary
        decomposition = {
            'net_profit_margin': net_profit_margin,
            'asset_turnover': asset_turnover,
            'equity_multiplier': equity_multiplier
        }

        # Missing components
        missing_components = [k for k, v in decomposition.items() if v is None]
        if 'debt_to_equity' in locals() and debt_to_equity is None:
            missing_components.append('debt_to_equity')  # Though not in decomposition

        # Flag for incompleteness
        incomplete = len(missing_components) > 0

        if incomplete:
            logging.warning(f"DuPont analysis incomplete for {ticker_symbol} ({period_type}, {fiscal_date}). Missing: {missing_components}")

        logging.info(f"DuPont analysis completed for {ticker_symbol} ({period_type}, {fiscal_date}).")

        return {
            'calculated_roe': calculated_roe,
            'phase3_roe': phase3_roe,
            'match': match,
            'decomposition': decomposition,
            'percentage_difference': percentage_difference,
            'missing_components': missing_components,
            'incomplete': incomplete
        }

    def compute_extended_dupont(self, ticker_symbol, period_type, fiscal_date):
        """
        Compute the Extended DuPont Analysis for ROE decomposition.

        Decomposes ROE into:
        - Profit Margin, Asset Turnover, Equity Multiplier
        - Further breaks Profit Margin into Operating Margin, Tax Burden, Interest Burden

        Handles missing data by returning None for unavailable components.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            period_type (str): 'annual' or 'quarterly'.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format.

        Returns:
            dict or None: {
                'roe': float or None,
                'calculated_roe': float or None,
                'match': bool or None,
                'decomposition': dict with components,
                'missing_components': list,
                'incomplete': bool
            } or None if ticker not found.
        """
        # Input validation
        if not isinstance(ticker_symbol, str) or not isinstance(period_type, str) or not isinstance(fiscal_date, str):
            raise ValueError("ticker_symbol, period_type, and fiscal_date must be strings.")

        income_statement = self.repo.get_income_statement(ticker_symbol, period_type, fiscal_date)
        balance_statement = self.repo.get_balance_sheet(ticker_symbol, period_type, fiscal_date)

        if not income_statement or not balance_statement:
            return None

        income_data = income_statement['statement_data']
        balance_data = balance_statement['statement_data']

        revenue = income_data.get('revenue')
        net_income = income_data.get('netIncome')
        operating_income = income_data.get('operatingIncome')
        interest_expense = income_data.get('interestExpense')
        total_assets = balance_data.get('totalAssets')
        total_shareholders_equity = balance_data.get('totalShareholdersEquity')

        # Compute ROE
        roe = None
        if net_income is not None and total_shareholders_equity is not None and total_shareholders_equity != 0:
            roe = net_income / total_shareholders_equity

        # Basic DuPont components
        net_profit_margin = None
        if revenue is not None and revenue != 0 and net_income is not None:
            net_profit_margin = net_income / revenue

        asset_turnover = None
        if revenue is not None and total_assets is not None and total_assets != 0:
            asset_turnover = revenue / total_assets

        equity_multiplier = None
        if total_assets is not None and total_shareholders_equity is not None and total_shareholders_equity != 0:
            equity_multiplier = total_assets / total_shareholders_equity

        # Extended components
        operating_margin = None
        if revenue is not None and revenue != 0 and operating_income is not None:
            operating_margin = operating_income / revenue

        # EBT approximation: EBIT - interest
        ebt = operating_income
        if interest_expense is not None and operating_income is not None:
            ebt = operating_income - interest_expense

        tax_burden = None
        if ebt is not None and ebt != 0 and net_income is not None:
            tax_burden = net_income / ebt

        interest_burden = None
        if operating_income is not None and operating_income != 0 and ebt is not None:
            interest_burden = ebt / operating_income

        # Calculated ROE
        calculated_roe = None
        if net_profit_margin is not None and asset_turnover is not None and equity_multiplier is not None:
            calculated_roe = net_profit_margin * asset_turnover * equity_multiplier

        # Match
        match = None
        if roe is not None and calculated_roe is not None:
            match = abs(roe - calculated_roe) < 1e-6

        # Decomposition
        decomposition = {
            'net_profit_margin': net_profit_margin,
            'asset_turnover': asset_turnover,
            'equity_multiplier': equity_multiplier,
            'operating_margin': operating_margin,
            'tax_burden': tax_burden,
            'interest_burden': interest_burden
        }

        # Missing components
        missing_components = [k for k, v in decomposition.items() if v is None]
        incomplete = len(missing_components) > 0

        return {
            'roe': roe,
            'calculated_roe': calculated_roe,
            'match': match,
            'decomposition': decomposition,
            'missing_components': missing_components,
            'incomplete': incomplete
        }

    def perform_scenario_analysis(self, ticker_symbol, period_type, fiscal_date, scenario_factors):
        """
        Perform scenario analysis by applying scenario factors to financials and recalculating key ratios.

        Scenario factors: dict with keys like 'revenue_change', 'cost_change', 'interest_rate_change', 'debt_change'
        Values are multipliers (e.g., 0.1 for 10% increase).

        Modifies financial data, adjusts netIncome proportionally, and recomputes ratios.

        Returns dict with baseline and scenario values for ratios, and percentage changes.

        Ratios: roe, roa, debt_ratio, current_ratio, gross_profit_margin, net_profit_margin
        """
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get statements
        income_stmt = self.conn.execute("""
            SELECT statement_data FROM income_statement
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        balance_stmt = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not income_stmt or not balance_stmt:
            return None

        income_data = json.loads(income_stmt[0])
        balance_data = json.loads(balance_stmt[0])

        # Baseline values
        revenue = income_data.get('revenue')
        cost_of_revenue = income_data.get('costOfRevenue')
        interest_expense = income_data.get('interestExpense')
        net_income = income_data.get('netIncome')
        total_assets = balance_data.get('totalAssets')
        total_liabilities = balance_data.get('totalLiabilities')
        total_shareholders_equity = balance_data.get('totalShareholdersEquity')
        total_current_assets = balance_data.get('totalCurrentAssets')
        total_current_liabilities = balance_data.get('totalCurrentLiabilities')

        if not all([revenue, net_income, total_assets, total_liabilities, total_shareholders_equity]):
            return None  # Missing key data

        # Apply scenario factors
        revenue_new = revenue * (1 + scenario_factors.get('revenue_change', 0))
        cost_of_revenue_new = (cost_of_revenue or 0) * (1 + scenario_factors.get('cost_change', 0))
        interest_expense_new = (interest_expense or 0) * (1 + scenario_factors.get('interest_rate_change', 0))
        total_liabilities_new = total_liabilities * (1 + scenario_factors.get('debt_change', 0))

        # Adjust netIncome: assume netIncome = revenue - cost_of_revenue - interest_expense - other_expenses
        # So delta_net_income = delta_revenue - delta_cost - delta_interest
        delta_revenue = revenue_new - revenue
        delta_cost = cost_of_revenue_new - (cost_of_revenue or 0)
        delta_interest = interest_expense_new - (interest_expense or 0)
        net_income_new = net_income + delta_revenue - delta_cost - delta_interest

        # For balance sheet, adjust total_assets if liabilities change (assuming assets change accordingly, equity fixed)
        total_assets_new = total_assets - total_liabilities + total_liabilities_new
        # total_current_assets, total_current_liabilities assume no change for simplicity

        # Compute baseline ratios
        baseline_roe = net_income / total_shareholders_equity if total_shareholders_equity else None
        baseline_roa = net_income / total_assets if total_assets else None
        baseline_debt_ratio = total_liabilities / total_assets if total_assets else None
        baseline_current_ratio = total_current_assets / total_current_liabilities if total_current_liabilities else None
        baseline_gross_margin = (revenue - (cost_of_revenue or 0)) / revenue if revenue else None
        baseline_net_margin = net_income / revenue if revenue else None

        # Compute scenario ratios
        scenario_roe = net_income_new / total_shareholders_equity if total_shareholders_equity else None
        scenario_roa = net_income_new / total_assets_new if total_assets_new else None
        scenario_debt_ratio = total_liabilities_new / total_assets_new if total_assets_new else None
        scenario_current_ratio = baseline_current_ratio  # No change
        scenario_gross_margin = (revenue_new - cost_of_revenue_new) / revenue_new if revenue_new else None
        scenario_net_margin = net_income_new / revenue_new if revenue_new else None

        # Impacts: dict with baseline, scenario, change
        impacts = {}
        for ratio in ['roe', 'roa', 'debt_ratio', 'current_ratio', 'gross_profit_margin', 'net_profit_margin']:
            baseline = locals()[f'baseline_{ratio}']
            scenario = locals()[f'scenario_{ratio}']
            change = None
            if baseline and scenario and baseline != 0:
                change = ((scenario - baseline) / baseline) * 100
            impacts[ratio] = {
                'baseline': baseline,
                'scenario': scenario,
                'percentage_change': change
            }

        return impacts

    def compute_return_on_capital_employed(self, ticker_symbol, period_type, fiscal_date):
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get income statement for operatingIncome
        income_statement = self.conn.execute("""
            SELECT statement_data FROM income_statement
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        # Get balance sheet for totalAssets and totalCurrentLiabilities
        balance_statement = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not income_statement or not balance_statement:
            return None

        income_data = json.loads(income_statement[0])
        balance_data = json.loads(balance_statement[0])

        operating_income = income_data.get('operatingIncome')
        total_assets = balance_data.get('totalAssets')
        total_current_liabilities = balance_data.get('totalCurrentLiabilities')

        if operating_income is None or total_assets is None or total_current_liabilities is None:
            return None

        capital_employed = total_assets - total_current_liabilities

        if capital_employed <= 0:
            return None  # Division by zero or negative capital employed

        return operating_income / capital_employed

    def compute_eva(self, ticker_symbol, period_type, fiscal_date, wacc=0.10, tax_rate=0.21):
        """
        Compute Economic Value Added (EVA) as NOPAT - (Capital * WACC).

        NOPAT = EBIT * (1 - tax_rate), where EBIT is operating income.
        Capital = Total Assets - Current Liabilities.
        WACC is weighted average cost of capital, default 10%.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            period_type (str): 'annual' or 'quarterly'.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format.
            wacc (float): WACC as decimal, default 0.10.
            tax_rate (float): Effective tax rate as decimal, default 0.21.

        Returns:
            dict or None: {'eva': float, 'interpretation': str} or None if missing data.
        """
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get income statement for operatingIncome (EBIT)
        income_statement = self.conn.execute("""
            SELECT statement_data FROM income_statement
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        # Get balance sheet for totalAssets and totalCurrentLiabilities
        balance_statement = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not income_statement or not balance_statement:
            return None

        income_data = json.loads(income_statement[0])
        balance_data = json.loads(balance_statement[0])

        ebit = income_data.get('operatingIncome')
        total_assets = balance_data.get('totalAssets')
        total_current_liabilities = balance_data.get('totalCurrentLiabilities')

        if ebit is None or total_assets is None or total_current_liabilities is None:
            return None

        nopat = ebit * (1 - tax_rate)
        capital = total_assets - total_current_liabilities

        eva = nopat - (capital * wacc)

        if eva > 0:
            interpretation = "Positive EVA indicates value creation for shareholders."
        elif eva < 0:
            interpretation = "Negative EVA indicates value destruction for shareholders."
        else:
            interpretation = "EVA at zero indicates break-even; no value creation or destruction."

        return {'eva': eva, 'interpretation': interpretation}

    def compute_net_income_per_ebt(self):
        pass

    def compute_ebt_per_ebit(self):
        pass

    def compute_ebit_per_revenue(self):
        pass

    def compute_debt_ratio(self, ticker_symbol, period_type, fiscal_date):
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get balance sheet for total debt and total assets
        balance_statement = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not balance_statement:
            return None

        balance_data = json.loads(balance_statement[0])

        total_debt = balance_data.get('totalLiabilities')
        total_assets = balance_data.get('totalAssets')

        if total_debt is None or total_assets is None:
            return None

        if total_assets == 0:
            return None  # Division by zero

        return total_debt / total_assets

    def compute_debt_to_equity_ratio(self, ticker_symbol, period_type, fiscal_date):
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get balance sheet for total debt and total shareholders' equity
        balance_statement = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not balance_statement:
            return None

        balance_data = json.loads(balance_statement[0])

        total_debt = balance_data.get('totalLiabilities')  # Assuming totalLiabilities represents total debt
        total_shareholders_equity = balance_data.get('totalShareholdersEquity')

        if total_debt is None or total_shareholders_equity is None:
            return None

        if total_shareholders_equity == 0:
            return None  # Division by zero

        return total_debt / total_shareholders_equity

    def compute_long_term_debt_to_capitalization(self, ticker_symbol, period_type, fiscal_date):
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get balance sheet
        statement = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not statement:
            return None

        data = json.loads(statement[0])

        long_term_debt = data.get('longTermDebt')
        total_shareholders_equity = data.get('totalShareholdersEquity')

        if long_term_debt is None or total_shareholders_equity is None:
            return None

        denominator = long_term_debt + total_shareholders_equity
        if denominator == 0:
            return None  # Division by zero

        return long_term_debt / denominator

    def compute_total_debt_to_capitalization(self):
        pass

    def compute_interest_coverage(self, ticker_symbol, period_type, fiscal_date):
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get income statement
        statement = self.conn.execute("""
            SELECT statement_data FROM income_statement
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not statement:
            return None

        data = json.loads(statement[0])

        operating_income = data.get('operatingIncome')
        interest_expense = data.get('interestExpense')

        if operating_income is None or interest_expense is None:
            return None

        if interest_expense == 0:
            return None  # Division by zero

        return operating_income / interest_expense

    def compute_cash_flow_to_debt_ratio(self, ticker_symbol, period_type, fiscal_date):
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get cash flow statement
        cash_statement = self.conn.execute("""
            SELECT statement_data FROM cash_flow
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        # Get balance sheet statement
        balance_statement = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not cash_statement or not balance_statement:
            return None

        cash_data = json.loads(cash_statement[0])
        balance_data = json.loads(balance_statement[0])

        operating_cash_flow = cash_data.get('operatingCashFlow')
        total_debt = balance_data.get('totalLiabilities')

        if operating_cash_flow is None or total_debt is None:
            return None

        if total_debt == 0:
            return None  # Division by zero

        return operating_cash_flow / total_debt

    def compute_company_equity_multiplier(self):
        pass

    def compute_receivables_turnover(self, ticker_symbol, period_type, fiscal_date):
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get income statement for revenue
        income_statement = self.conn.execute("""
            SELECT statement_data FROM income_statement
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        # Get balance sheet for accountReceivables
        balance_statement = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not income_statement or not balance_statement:
            return None

        income_data = json.loads(income_statement[0])
        balance_data = json.loads(balance_statement[0])

        revenue = income_data.get('revenue')
        account_receivables = balance_data.get('accountReceivables')

        if revenue is None or account_receivables is None:
            return None

        if account_receivables == 0:
            return None  # Division by zero

        return revenue / account_receivables

    def compute_payables_turnover(self, ticker_symbol, period_type, fiscal_date):
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get income statement for costOfRevenue
        income_statement = self.conn.execute("""
            SELECT statement_data FROM income_statement
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        # Get balance sheet for accountPayables
        balance_statement = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not income_statement or not balance_statement:
            return None

        income_data = json.loads(income_statement[0])
        balance_data = json.loads(balance_statement[0])

        cost_of_revenue = income_data.get('costOfRevenue')
        account_payables = balance_data.get('accountPayables')

        if cost_of_revenue is None or account_payables is None:
            return None

        if account_payables == 0:
            return None  # Division by zero

        return cost_of_revenue / account_payables

    def compute_inventory_turnover(self, ticker_symbol, period_type, fiscal_date):
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get income statement for costOfRevenue
        income_statement = self.conn.execute("""
            SELECT statement_data FROM income_statement
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        # Get balance sheet for inventory
        balance_statement = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not income_statement or not balance_statement:
            return None

        income_data = json.loads(income_statement[0])
        balance_data = json.loads(balance_statement[0])

        cost_of_revenue = income_data.get('costOfRevenue')
        inventory = balance_data.get('inventory')

        if cost_of_revenue is None or inventory is None:
            return None

        if inventory == 0:
            return None  # Division by zero

        return cost_of_revenue / inventory

    def compute_fixed_asset_turnover(self, ticker_symbol, period_type, fiscal_date):
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get income statement for revenue
        income_statement = self.conn.execute("""
            SELECT statement_data FROM income_statement
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        # Get balance sheet for fixed assets
        balance_statement = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not income_statement or not balance_statement:
            return None

        income_data = json.loads(income_statement[0])
        balance_data = json.loads(balance_statement[0])

        revenue = income_data.get('revenue')
        fixed_assets = balance_data.get('propertyPlantEquipmentNet')

        if revenue is None or fixed_assets is None:
            return None

        if fixed_assets == 0:
            return None  # Division by zero

        return revenue / fixed_assets

    def compute_asset_turnover(self, ticker_symbol, period_type, fiscal_date):
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get income statement for revenue
        income_statement = self.conn.execute("""
            SELECT statement_data FROM income_statement
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        # Get balance sheet for total assets
        balance_statement = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not income_statement or not balance_statement:
            return None

        income_data = json.loads(income_statement[0])
        balance_data = json.loads(balance_statement[0])

        revenue = income_data.get('revenue')
        total_assets = balance_data.get('totalAssets')

        if revenue is None or total_assets is None:
            return None

        if total_assets == 0:
            return None  # Division by zero

        return revenue / total_assets

    def compute_operating_cash_flow_per_share(self, ticker_symbol, period_type, fiscal_date):
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get cash flow statement
        cash_statement = self.conn.execute("""
            SELECT statement_data FROM cash_flow
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        # Get balance sheet for shares outstanding
        balance_statement = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not cash_statement or not balance_statement:
            return None

        cash_data = json.loads(cash_statement[0])
        balance_data = json.loads(balance_statement[0])

        operating_cash_flow = cash_data.get('operatingCashFlow')
        shares_outstanding = balance_data.get('commonStockSharesOutstanding')

        if operating_cash_flow is None or shares_outstanding is None:
            return None

        if shares_outstanding == 0:
            return None  # Division by zero

        return operating_cash_flow / shares_outstanding

    def compute_free_cash_flow_per_share(self, ticker_symbol, period_type, fiscal_date):
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get cash flow statement
        cash_statement = self.conn.execute("""
            SELECT statement_data FROM cash_flow
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        # Get balance sheet for shares outstanding
        balance_statement = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not cash_statement or not balance_statement:
            return None

        cash_data = json.loads(cash_statement[0])
        balance_data = json.loads(balance_statement[0])

        operating_cash_flow = cash_data.get('operatingCashFlow')
        capital_expenditures = cash_data.get('capitalExpenditures')

        if operating_cash_flow is None or capital_expenditures is None:
            return None

        free_cash_flow = operating_cash_flow - capital_expenditures

        shares_outstanding = balance_data.get('commonStockSharesOutstanding')

        if shares_outstanding is None:
            return None

        if shares_outstanding == 0:
            return None  # Division by zero

        return free_cash_flow / shares_outstanding

    def compute_fcf_yield(self, ticker_symbol, period_type, fiscal_date):
        """
        Compute Free Cash Flow Yield.

        FCF Yield = Free Cash Flow / Market Cap, where Market Cap = Price * Shares Outstanding.
        Free Cash Flow = Operating Cash Flow - Capital Expenditures.

        Assesses yield: 'high' if >5%, 'low' if <2%, else 'moderate'.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            period_type (str): 'annual' or 'quarterly'.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format.

        Returns:
            dict or None: {'fcf_yield': float, 'assessment': str} or None if missing data.
        """
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get cash flow statement for free cash flow
        cash_statement = self.conn.execute("""
            SELECT statement_data FROM cash_flow
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        # Get balance sheet for shares outstanding
        balance_statement = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        # Get historical price
        price_record = self.conn.execute("""
            SELECT price FROM historical_price
            WHERE ticker_id = ? AND date = ?
        """, (ticker_id, fiscal_date)).fetchone()

        if not cash_statement or not balance_statement or not price_record:
            return None

        cash_data = json.loads(cash_statement[0])
        balance_data = json.loads(balance_statement[0])
        price = price_record[0]

        operating_cash_flow = cash_data.get('operatingCashFlow')
        capital_expenditures = cash_data.get('capitalExpenditures')
        shares_outstanding = balance_data.get('commonStockSharesOutstanding')

        if operating_cash_flow is None or capital_expenditures is None or shares_outstanding is None or price is None:
            return None

        free_cash_flow = operating_cash_flow - capital_expenditures
        market_cap = price * shares_outstanding

        if market_cap == 0:
            return None  # Division by zero

        fcf_yield = free_cash_flow / market_cap

        if fcf_yield > 0.05:
            assessment = 'high'
        elif fcf_yield < 0.02:
            assessment = 'low'
        else:
            assessment = 'moderate'

        return {'fcf_yield': fcf_yield, 'assessment': assessment}

    def compute_cash_per_share(self):
        pass

    def compute_payout_ratio(self, ticker_symbol, period_type, fiscal_date):
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get income statement for netIncome
        income_statement = self.conn.execute("""
            SELECT statement_data FROM income_statement
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        # Get cash flow statement for dividendsPaid
        cash_statement = self.conn.execute("""
            SELECT statement_data FROM cash_flow
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not income_statement or not cash_statement:
            return None

        income_data = json.loads(income_statement[0])
        cash_data = json.loads(cash_statement[0])

        net_income = income_data.get('netIncome')
        dividends_paid = cash_data.get('dividendsPaid')

        if net_income is None or dividends_paid is None:
            return None

        if net_income == 0:
            return None  # Division by zero

        # Dividends should be positive; if dividendsPaid is negative (outflow), take absolute value
        dividends = abs(dividends_paid) if dividends_paid != 0 else 0

        return dividends / net_income

    def compute_operating_cash_flow_sales_ratio(self, ticker_symbol, period_type, fiscal_date):
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get cash flow statement
        cash_statement = self.conn.execute("""
            SELECT statement_data FROM cash_flow
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        # Get income statement
        income_statement = self.conn.execute("""
            SELECT statement_data FROM income_statement
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not cash_statement or not income_statement:
            return None

        cash_data = json.loads(cash_statement[0])
        income_data = json.loads(income_statement[0])

        operating_cash_flow = cash_data.get('operatingCashFlow')
        revenue = income_data.get('revenue')

        if operating_cash_flow is None or revenue is None:
            return None

        if revenue == 0:
            return None  # Division by zero

        return operating_cash_flow / revenue

    def compute_free_cash_flow_operating_cash_flow_ratio(self, ticker_symbol, period_type, fiscal_date):
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get cash flow statement
        statement = self.conn.execute("""
            SELECT statement_data FROM cash_flow
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not statement:
            return None

        data = json.loads(statement[0])

        operating_cash_flow = data.get('operatingCashFlow')
        capital_expenditures = data.get('capitalExpenditures')

        if operating_cash_flow is None or capital_expenditures is None:
            return None

        free_cash_flow = operating_cash_flow - capital_expenditures

        if operating_cash_flow == 0:
            return None  # Division by zero

        return free_cash_flow / operating_cash_flow

    def compute_cash_flow_coverage_ratios(self):
        pass

    def compute_short_term_coverage_ratios(self):
        pass

    def compute_capital_expenditure_coverage_ratio(self):
        pass

    def compute_dividend_paid_and_capex_coverage_ratio(self):
        pass

    def compute_dividend_payout_ratio(self):
        pass

    def compute_price_book_value_ratio(self, ticker_symbol, period_type, fiscal_date):
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get balance sheet statement
        statement = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not statement:
            return None

        data = json.loads(statement[0])

        total_shareholders_equity = data.get('totalShareholdersEquity')
        shares_outstanding = data.get('commonStockSharesOutstanding')

        if total_shareholders_equity is None or shares_outstanding is None:
            return None

        if shares_outstanding == 0:
            return None  # Division by zero

        book_value_per_share = total_shareholders_equity / shares_outstanding

        if book_value_per_share == 0:
            return None  # Division by zero

        # Get historical price for the fiscal_date
        price_record = self.conn.execute("""
            SELECT price FROM historical_price
            WHERE ticker_id = ? AND date = ?
        """, (ticker_id, fiscal_date)).fetchone()

        if not price_record:
            return None

        price = price_record[0]

        if price == 0:
            return None  # Division by zero for P/B

        return price / book_value_per_share

    def compute_price_to_book_ratio(self):
        pass

    def compute_price_to_sales_ratio(self, ticker_symbol, period_type, fiscal_date):
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get income statement for revenue
        income_statement = self.conn.execute("""
            SELECT statement_data FROM income_statement
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        # Get balance sheet for shares outstanding
        balance_statement = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not income_statement or not balance_statement:
            return None

        income_data = json.loads(income_statement[0])
        balance_data = json.loads(balance_statement[0])

        revenue = income_data.get('revenue')
        shares_outstanding = balance_data.get('commonStockSharesOutstanding')

        if revenue is None or shares_outstanding is None:
            return None

        if revenue == 0 or shares_outstanding == 0:
            return None  # Division by zero

        sales_per_share = revenue / shares_outstanding

        if sales_per_share == 0:
            return None  # Avoid division by zero in ratio

        # Get historical price for the fiscal_date
        price_record = self.conn.execute("""
            SELECT price FROM historical_price
            WHERE ticker_id = ? AND date = ?
        """, (ticker_id, fiscal_date)).fetchone()

        if not price_record:
            return None

        price = price_record[0]

        if price == 0:
            return None  # Division by zero for P/S

        return price / sales_per_share

    def compute_price_earnings_ratio(self, ticker_symbol, period_type, fiscal_date):
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get income statement for netIncome
        income_statement = self.conn.execute("""
            SELECT statement_data FROM income_statement
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        # Get balance sheet for sharesOutstanding
        balance_statement = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not income_statement or not balance_statement:
            return None

        income_data = json.loads(income_statement[0])
        balance_data = json.loads(balance_statement[0])

        net_income = income_data.get('netIncome')
        shares_outstanding = balance_data.get('commonStockSharesOutstanding')

        if net_income is None or shares_outstanding is None:
            return None

        if shares_outstanding == 0:
            return None  # Division by zero

        eps = net_income / shares_outstanding

        # Get historical price for the fiscal_date
        price_record = self.conn.execute("""
            SELECT price FROM historical_price
            WHERE ticker_id = ? AND date = ?
        """, (ticker_id, fiscal_date)).fetchone()

        if not price_record:
            return None

        price = price_record[0]

        if price == 0:
            return None  # Division by zero for P/E

        return price / eps

    def compute_price_to_free_cash_flows_ratio(self):
        pass

    def compute_price_to_operating_cash_flows_ratio(self):
        pass

    def compute_price_cash_flow_ratio(self):
        pass

    def compute_price_earnings_to_growth_ratio(self):
        pass

    def compute_price_sales_ratio(self):
        pass

    def compute_dividend_yield(self, ticker_symbol, period_type, fiscal_date):
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get cash flow statement
        cash_statement = self.conn.execute("""
            SELECT statement_data FROM cash_flow
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        # Get balance sheet statement
        balance_statement = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not cash_statement or not balance_statement:
            return None

        cash_data = json.loads(cash_statement[0])
        balance_data = json.loads(balance_statement[0])

        dividends_paid = cash_data.get('dividendsPaid')
        shares_outstanding = balance_data.get('commonStockSharesOutstanding')

        if dividends_paid is None or shares_outstanding is None:
            return None

        if shares_outstanding == 0:
            return None  # Division by zero

        # Use absolute value for dividends (as outflow is negative)
        dividends = abs(dividends_paid) if dividends_paid != 0 else 0
        dps = dividends / shares_outstanding

        # Get historical price for the fiscal_date
        price_record = self.conn.execute("""
            SELECT price FROM historical_price
            WHERE ticker_id = ? AND date = ?
        """, (ticker_id, fiscal_date)).fetchone()

        if not price_record:
            return None

        price = price_record[0]

        if price == 0:
            return None  # Division by zero for yield

        return dps / price

    def compute_altman_z_score(self, ticker_symbol, period_type, fiscal_date):
        balance_statement = self.repo.get_balance_sheet(ticker_symbol, period_type, fiscal_date)
        income_statement = self.repo.get_income_statement(ticker_symbol, period_type, fiscal_date)
        price_record = self.repo.get_historical_price_at_date(ticker_symbol, fiscal_date)

        if not balance_statement or not income_statement or not price_record:
            return None

        balance_data = balance_statement['statement_data']
        income_data = income_statement['statement_data']
        price = price_record['close']

        # Extract values
        total_current_assets = balance_data.get('totalCurrentAssets')
        total_current_liabilities = balance_data.get('totalCurrentLiabilities')
        retained_earnings = balance_data.get('retainedEarnings')
        total_assets = balance_data.get('totalAssets')
        total_liabilities = balance_data.get('totalLiabilities')
        shares_outstanding = balance_data.get('commonStockSharesOutstanding')

        operating_income = income_data.get('operatingIncome')
        revenue = income_data.get('revenue')

        # Check for missing values
        if (total_current_assets is None or total_current_liabilities is None or
            retained_earnings is None or total_assets is None or total_liabilities is None or
            shares_outstanding is None or operating_income is None or revenue is None or
            price is None or total_assets == 0 or total_liabilities == 0):
            return None

        # Calculate components
        working_capital = total_current_assets - total_current_liabilities
        market_value_equity = price * shares_outstanding

        # Altman Z-Score formula
        z = (1.2 * (working_capital / total_assets) +
             1.4 * (retained_earnings / total_assets) +
             3.3 * (operating_income / total_assets) +
             0.6 * (market_value_equity / total_liabilities) +
             0.999 * (revenue / total_assets))

        # Risk interpretation
        if z > 3:
            risk = 'safe'
        elif 1.8 <= z <= 3:
            risk = 'gray'
        else:
            risk = 'distress'

        return {'z_score': z, 'risk': risk}

    def compute_beneish_m_score(self, ticker_symbol, period_type, fiscal_date):
        """
        Compute the Beneish M-Score for earnings manipulation detection.

        The M-Score is based on 8 financial ratios over two consecutive periods.
        A score > -2.22 suggests potential earnings manipulation risk.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            period_type (str): 'annual' or 'quarterly'.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format for the current period.

        Returns:
            dict or None: {'m_score': float, 'risk': 'low' or 'high'} or None if insufficient/missing data.
        """
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Parse fiscal_date and compute previous
        try:
            current_dt = datetime.fromisoformat(fiscal_date)
            previous_dt = current_dt.replace(year=current_dt.year - 1)
            previous_fiscal_date = previous_dt.isoformat()[:10]
        except ValueError:
            return None

        # Get current period data: income, balance, cash
        income_current = self.conn.execute("""
            SELECT statement_data FROM income_statement
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        balance_current = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        cash_current = self.conn.execute("""
            SELECT statement_data FROM cash_flow
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not income_current or not balance_current or not cash_current:
            return None

        inc_curr = json.loads(income_current[0])
        bal_curr = json.loads(balance_current[0])
        cas_curr = json.loads(cash_current[0])

        # Get previous period data
        income_prev = self.conn.execute("""
            SELECT statement_data FROM income_statement
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, previous_fiscal_date)).fetchone()

        balance_prev = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, previous_fiscal_date)).fetchone()

        cash_prev = self.conn.execute("""
            SELECT statement_data FROM cash_flow
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, previous_fiscal_date)).fetchone()

        if not income_prev or not balance_prev or not cash_prev:
            return None

        inc_prev = json.loads(income_prev[0])
        bal_prev = json.loads(balance_prev[0])
        cas_prev = json.loads(cash_prev[0])

        # Extract required fields
        receivables_t = bal_curr.get('accountReceivables')
        sales_t = inc_curr.get('revenue')
        receivables_tm1 = bal_prev.get('accountReceivables')
        sales_tm1 = inc_prev.get('revenue')
        cogs_t = inc_curr.get('costOfRevenue')
        cogs_tm1 = inc_prev.get('costOfRevenue')
        curr_assets_t = bal_curr.get('totalCurrentAssets')
        ppe_t = bal_curr.get('propertyPlantEquipmentNet')
        total_assets_t = bal_curr.get('totalAssets')
        curr_assets_tm1 = bal_prev.get('totalCurrentAssets')
        ppe_tm1 = bal_prev.get('propertyPlantEquipmentNet')
        total_assets_tm1 = bal_prev.get('totalAssets')
        dep_t = inc_curr.get('depreciationAndAmortization')
        dep_tm1 = inc_prev.get('depreciationAndAmortization')
        sga_t = inc_curr.get('sellingGeneralAndAdministrativeExpenses')
        sga_tm1 = inc_prev.get('sellingGeneralAndAdministrativeExpenses')
        net_income_t = inc_curr.get('netIncome')
        cfo_t = cas_curr.get('operatingCashFlow')
        curr_liab_t = bal_curr.get('totalCurrentLiabilities')
        total_debt_t = bal_curr.get('totalLiabilities')
        curr_liab_tm1 = bal_prev.get('totalCurrentLiabilities')
        total_debt_tm1 = bal_prev.get('totalLiabilities')

        # Check for missing or zero values
        if (receivables_t is None or sales_t is None or sales_t == 0 or
            receivables_tm1 is None or sales_tm1 is None or sales_tm1 == 0 or
            cogs_t is None or cogs_tm1 is None or
            curr_assets_t is None or ppe_t is None or total_assets_t is None or total_assets_t == 0 or
            curr_assets_tm1 is None or ppe_tm1 is None or total_assets_tm1 is None or total_assets_tm1 == 0 or
            dep_t is None or dep_tm1 is None or
            sga_t is None or sga_tm1 is None or
            net_income_t is None or cfo_t is None or
            curr_liab_t is None or total_debt_t is None or
            curr_liab_tm1 is None or total_debt_tm1 is None):
            return None

        # Compute DSRI
        dsri = (receivables_t / sales_t) / (receivables_tm1 / sales_tm1)

        # Compute GMI
        gm_t = (sales_t - cogs_t) / sales_t
        gm_tm1 = (sales_tm1 - cogs_tm1) / sales_tm1
        if gm_t == 0:
            return None
        gmi = gm_tm1 / gm_t

        # Compute AQI
        aqi_t = 1 - (curr_assets_t + ppe_t) / total_assets_t
        aqi_tm1 = 1 - (curr_assets_tm1 + ppe_tm1) / total_assets_tm1
        if aqi_tm1 == 0:
            return None
        aqi = aqi_t / aqi_tm1

        # Compute SGI
        sgi = sales_t / sales_tm1

        # Compute DEPI
        depi_t = dep_t / (ppe_t + dep_t)
        depi_tm1 = dep_tm1 / (ppe_tm1 + dep_tm1)
        if depi_t == 0:
            return None
        depi = depi_tm1 / depi_t

        # Compute SGAI
        sgai = (sga_t / sales_t) / (sga_tm1 / sales_tm1)

        # Compute TATA
        tata = (net_income_t - cfo_t) / total_assets_t

        # Compute LVGI
        lvgi_t = (curr_liab_t + total_debt_t) / total_assets_t
        lvgi_tm1 = (curr_liab_tm1 + total_debt_tm1) / total_assets_tm1
        lvgi = lvgi_t / lvgi_tm1

        # Compute M-Score
        m_score = (-4.84 + 0.92 * dsri + 0.528 * gmi + 0.404 * aqi + 0.892 * sgi +
                   0.115 * depi - 0.172 * sgai + 4.679 * tata - 0.327 * lvgi)

        # Determine risk
        risk = 'high' if m_score > -2.22 else 'low'

        return {'m_score': m_score, 'risk': risk}

    def compute_var(self, ticker_symbol, period_type, fiscal_date):
        """
        Compute Value at Risk (VaR) at 95% confidence using parametric, historical, and Monte Carlo methods.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            period_type (str): 'annual' or 'quarterly'.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format.

        Returns:
            dict or None: {
                'parametric_var': float,
                'historical_var': float,
                'monte_carlo_var': float
            } or None if insufficient data or ticker not found.
        """
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get historical prices, ordered by date
        prices = self.conn.execute("""
            SELECT date, price FROM historical_price
            WHERE ticker_id = ? ORDER BY date
        """, (ticker_id,)).fetchall()

        if len(prices) < 2:
            return None  # Need at least 2 prices for returns

        # Compute returns
        returns = []
        for i in range(1, len(prices)):
            prev_price = prices[i-1][1]
            curr_price = prices[i][1]
            if prev_price != 0:
                ret = (curr_price - prev_price) / prev_price
            else:
                ret = 0  # Avoid division by zero
            returns.append(ret)

        returns = np.array(returns)

        if len(returns) < 30:  # Minimum data for reliable VaR
            return None

        # Parametric VaR
        mean_ret = np.mean(returns)
        std_ret = np.std(returns, ddof=1)  # Sample standard deviation
        z = norm.ppf(0.05)  # 5% tail for 95% confidence
        parametric_var = - (mean_ret + z * std_ret)

        # Historical VaR
        sorted_returns = np.sort(returns)
        index = int(0.05 * len(sorted_returns))
        historical_var = -sorted_returns[index]

        # Monte Carlo VaR
        num_simulations = 10000
        simulated_returns = np.random.normal(mean_ret, std_ret, num_simulations)
        simulated_sorted = np.sort(simulated_returns)
        mc_index = int(0.05 * num_simulations)
        monte_carlo_var = -simulated_sorted[mc_index]

        return {
            'parametric_var': parametric_var,
            'historical_var': historical_var,
            'monte_carlo_var': monte_carlo_var
        }

    def compute_piotroski_f_score(self, ticker_symbol, period_type, fiscal_date):
        """
        Compute the Piotroski F-Score, a 9-point score based on fundamental signals.

        The score evaluates profitability, leverage, liquidity, source of funds, and asset efficiency.
        Each criterion is worth 1 point if satisfied, 0 otherwise. Missing data for a criterion results in 0.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            period_type (str): 'annual' or 'quarterly'.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format.

        Returns:
            int or None: The F-Score (0-9) or None if ticker not found.
        """
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Parse fiscal_date and compute previous
        try:
            current_dt = datetime.fromisoformat(fiscal_date)
            previous_dt = current_dt.replace(year=current_dt.year - 1)
            previous_fiscal_date = previous_dt.isoformat()[:10]  # YYYY-MM-DD
        except ValueError:
            return None

        score = 0

        # Criterion 1: Positive net income
        income_stmt = self.conn.execute("""
            SELECT statement_data FROM income_statement
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()
        if income_stmt:
            income_data = json.loads(income_stmt[0])
            net_income = income_data.get('netIncome')
            if net_income is not None and net_income > 0:
                score += 1

        # Criterion 2: Positive ROA
        roa = self.compute_return_on_assets(ticker_symbol, period_type, fiscal_date)
        if roa is not None and roa > 0:
            score += 1

        # Criterion 3: Positive operating cash flow
        cash_stmt = self.conn.execute("""
            SELECT statement_data FROM cash_flow
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()
        operating_cash_flow = None
        if cash_stmt:
            cash_data = json.loads(cash_stmt[0])
            operating_cash_flow = cash_data.get('operatingCashFlow')

        if operating_cash_flow is not None and operating_cash_flow > 0:
            score += 1

        # Criterion 4: Operating cash flow > net income
        if operating_cash_flow is not None and income_stmt:
            income_data = json.loads(income_stmt[0])
            net_income = income_data.get('netIncome')
            if net_income is not None and operating_cash_flow > net_income:
                score += 1

        # Criterion 5: Lower long-term debt to assets ratio year over year
        balance_stmt_current = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()
        balance_stmt_previous = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, previous_fiscal_date)).fetchone()

        if balance_stmt_current and balance_stmt_previous:
            balance_current = json.loads(balance_stmt_current[0])
            balance_previous = json.loads(balance_stmt_previous[0])
            long_term_debt_current = balance_current.get('longTermDebt')
            long_term_debt_previous = balance_previous.get('longTermDebt')
            total_assets_current = balance_current.get('totalAssets')
            total_assets_previous = balance_previous.get('totalAssets')
            if (long_term_debt_current is not None and total_assets_current is not None and total_assets_current > 0 and
                long_term_debt_previous is not None and total_assets_previous is not None and total_assets_previous > 0):
                ratio_current = long_term_debt_current / total_assets_current
                ratio_previous = long_term_debt_previous / total_assets_previous
                if ratio_current < ratio_previous:
                    score += 1

        # Criterion 6: Higher current ratio year over year
        if balance_stmt_current and balance_stmt_previous:
            balance_current = json.loads(balance_stmt_current[0])
            balance_previous = json.loads(balance_stmt_previous[0])
            current_assets_current = balance_current.get('totalCurrentAssets')
            current_liab_current = balance_current.get('totalCurrentLiabilities')
            current_assets_previous = balance_previous.get('totalCurrentAssets')
            current_liab_previous = balance_previous.get('totalCurrentLiabilities')
            if (current_assets_current is not None and current_liab_current is not None and current_liab_current > 0 and
                current_assets_previous is not None and current_liab_previous is not None and current_liab_previous > 0):
                ratio_current = current_assets_current / current_liab_current
                ratio_previous = current_assets_previous / current_liab_previous
                if ratio_current > ratio_previous:
                    score += 1

        # Criterion 7: No new shares issued
        if balance_stmt_current and balance_stmt_previous:
            balance_current = json.loads(balance_stmt_current[0])
            balance_previous = json.loads(balance_stmt_previous[0])
            shares_current = balance_current.get('commonStockSharesOutstanding')
            shares_previous = balance_previous.get('commonStockSharesOutstanding')
            if shares_current is not None and shares_previous is not None and shares_current <= shares_previous:
                score += 1

        # Criterion 8: Higher gross margin year over year
        income_stmt_previous = self.conn.execute("""
            SELECT statement_data FROM income_statement
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, previous_fiscal_date)).fetchone()

        if income_stmt and income_stmt_previous:
            income_current = json.loads(income_stmt[0])
            income_previous = json.loads(income_stmt_previous[0])
            revenue_current = income_current.get('revenue')
            cost_current = income_current.get('costOfRevenue')
            revenue_previous = income_previous.get('revenue')
            cost_previous = income_previous.get('costOfRevenue')
            if (revenue_current is not None and cost_current is not None and revenue_current > 0 and
                revenue_previous is not None and cost_previous is not None and revenue_previous > 0):
                margin_current = (revenue_current - cost_current) / revenue_current
                margin_previous = (revenue_previous - cost_previous) / revenue_previous
                if margin_current > margin_previous:
                    score += 1

        # Criterion 9: Higher asset turnover year over year
        if balance_stmt_current and balance_stmt_previous and income_stmt and income_stmt_previous:
            balance_current = json.loads(balance_stmt_current[0])
            balance_previous = json.loads(balance_stmt_previous[0])
            income_current = json.loads(income_stmt[0])
            income_previous = json.loads(income_stmt_previous[0])
            revenue_current = income_current.get('revenue')
            revenue_previous = income_previous.get('revenue')
            total_assets_current = balance_current.get('totalAssets')
            total_assets_previous = balance_previous.get('totalAssets')
            if (revenue_current is not None and total_assets_current is not None and total_assets_current > 0 and
                revenue_previous is not None and total_assets_previous is not None and total_assets_previous > 0):
                turnover_current = revenue_current / total_assets_current
                turnover_previous = revenue_previous / total_assets_previous
                if turnover_current > turnover_previous:
                    score += 1

        return score

    def compute_custom_ratio(self, ticker_symbol, period_type, fiscal_date, numerator_field, denominator_field):
        """
        Compute a custom ratio given numerator and denominator field names.

        Fetches the values from the financial statements (balance_sheet, income_statement, cash_flow)
        for the specified ticker, period, and date. Computes numerator / denominator if both present and denominator != 0.
        Handles missing data by returning None.

        Args:
            ticker_symbol (str): The stock ticker symbol (e.g., 'AAPL').
            period_type (str): 'annual' or 'quarterly'.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format.
            numerator_field (str): Field name for numerator (e.g., 'totalAssets').
            denominator_field (str): Field name for denominator (e.g., 'totalLiabilities').

        Returns:
            float or None: The computed ratio or None if missing data or invalid.
        """
        if not isinstance(ticker_symbol, str) or not isinstance(period_type, str) or not isinstance(fiscal_date, str) or not isinstance(numerator_field, str) or not isinstance(denominator_field, str):
            raise ValueError("All arguments must be strings.")

        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get statements
        balance_stmt = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        income_stmt = self.conn.execute("""
            SELECT statement_data FROM income_statement
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        cash_stmt = self.conn.execute("""
            SELECT statement_data FROM cash_flow
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        # Load data
        balance_data = json.loads(balance_stmt[0]) if balance_stmt else {}
        income_data = json.loads(income_stmt[0]) if income_stmt else {}
        cash_data = json.loads(cash_stmt[0]) if cash_stmt else {}

        # Combine all data
        all_data = {**balance_data, **income_data, **cash_data}

        numerator = all_data.get(numerator_field)
        denominator = all_data.get(denominator_field)

        if numerator is None or denominator is None:
            return None

        if denominator == 0:
            return None

        return numerator / denominator

    def compute_esg_score(self, ticker_symbol, period_type, fiscal_date):
        """
        Compute a proxy ESG score based on financial ratios.

        Uses debt ratio for governance (lower debt better), ROA for social, net profit margin for environmental.
        Returns average score and breakdown.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            period_type (str): 'annual' or 'quarterly'.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format.

        Returns:
            dict or None: {'score': float, 'breakdown': {'governance': float, 'social': float, 'environmental': float}} or None if missing data.
        """
        governance = self.compute_debt_ratio(ticker_symbol, period_type, fiscal_date)
        if governance is not None:
            governance = 1 - governance  # Lower debt better
        social = self.compute_return_on_assets(ticker_symbol, period_type, fiscal_date)
        environmental = self.compute_net_profit_margin(ticker_symbol, period_type, fiscal_date)

        if governance is None or social is None or environmental is None:
            return None

        score = (governance + social + environmental) / 3
        breakdown = {'governance': governance, 'social': social, 'environmental': environmental}

        return {'score': score, 'breakdown': breakdown}

    def validate_ratios(self, ticker_symbol, period_type, fiscal_date):
        ratios = self.repo.get_ratios(ticker_symbol, period_type, fiscal_date)
        if not ratios:
            return {}

        reported_data = ratios['ratio_data']

        # Mapping from ratio name to compute method
        ratio_mappings = {
            'currentRatio': 'compute_current_ratio',
            'quickRatio': 'compute_quick_ratio',
            'cashRatio': 'compute_cash_ratio',
            'grossProfitMargin': 'compute_gross_profit_margin',
            'operatingProfitMargin': 'compute_operating_profit_margin',
            'netProfitMargin': 'compute_net_profit_margin',
            'returnOnAssets': 'compute_return_on_assets',
            'returnOnEquity': 'compute_return_on_equity',
            'returnOnCapitalEmployed': 'compute_return_on_capital_employed',
            'debtRatio': 'compute_debt_ratio',
            'debtEquityRatio': 'compute_debt_to_equity_ratio',
            'longTermDebtToCapitalization': 'compute_long_term_debt_to_capitalization',
            'interestCoverage': 'compute_interest_coverage',
            'cashFlowToDebtRatio': 'compute_cash_flow_to_debt_ratio',
            'receivablesTurnover': 'compute_receivables_turnover',
            'payablesTurnover': 'compute_payables_turnover',
            'inventoryTurnover': 'compute_inventory_turnover',
            'fixedAssetTurnover': 'compute_fixed_asset_turnover',
            'assetTurnover': 'compute_asset_turnover',
            'operatingCashFlowPerShare': 'compute_operating_cash_flow_per_share',
            'freeCashFlowPerShare': 'compute_free_cash_flow_per_share',
            'payoutRatio': 'compute_payout_ratio',
            'operatingCashFlowSalesRatio': 'compute_operating_cash_flow_sales_ratio',
            'freeCashFlowOperatingCashFlowRatio': 'compute_free_cash_flow_operating_cash_flow_ratio',
            'priceEarningsRatio': 'compute_price_earnings_ratio',
            'priceBookValueRatio': 'compute_price_book_value_ratio',
            'dividendYield': 'compute_dividend_yield',
            'priceToSalesRatio': 'compute_price_to_sales_ratio'
        }

        results = {}
        for ratio_name, reported_val in reported_data.items():
            method_name = ratio_mappings.get(ratio_name)
            if method_name:
                compute_method = getattr(self, method_name)
                computed_val = compute_method(ticker_symbol, period_type, fiscal_date)

                if computed_val is not None and reported_val is not None:
                    if reported_val == 0:
                        percentage_difference = None
                        discrepancy_flag = None
                    else:
                        percentage_difference = ((computed_val - reported_val) / reported_val) * 100
                        discrepancy_flag = abs(percentage_difference) > 1.0
                    results[ratio_name] = {
                        'computed': computed_val,
                        'reported': reported_val,
                        'percentage_difference': percentage_difference,
                        'discrepancy_flag': discrepancy_flag
                    }
                else:
                    results[ratio_name] = {
                        'computed': computed_val,
                        'reported': reported_val,
                        'percentage_difference': None,
                        'discrepancy_flag': None
                    }
            else:
                results[ratio_name] = {
                    'computed': None,
                    'reported': reported_val,
                    'percentage_difference': None,
                    'discrepancy_flag': None
                }

        return results

    def compare_to_peers(self, ticker_symbol, period_type, fiscal_date, peer_ratios):
        """
        Compare the company's computed ratios to peer average ratios.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            period_type (str): 'annual' or 'quarterly'.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format.
            peer_ratios (dict): Dict of peer average ratios, e.g., {'currentRatio': {'average': 2.0, 'std_dev': 0.5}, ...}

        Returns:
            dict: Comparison results for each ratio in peer_ratios where comparison is possible.
                 Format: {'ratio_name': {'company': float or None, 'peer_average': float, 'difference': float or None, 'z_score': float or None}}
                 If company ratio cannot be computed, difference and z_score are None.
                 If std_dev not provided or 0, z_score is None.
        """
        if not isinstance(peer_ratios, dict):
            raise ValueError("peer_ratios must be a dict")

        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return {}
        ticker_id = ticker_id[0]

        # Mapping from ratio name to compute method
        ratio_mappings = {
            'currentRatio': 'compute_current_ratio',
            'quickRatio': 'compute_quick_ratio',
            'cashRatio': 'compute_cash_ratio',
            'grossProfitMargin': 'compute_gross_profit_margin',
            'operatingProfitMargin': 'compute_operating_profit_margin',
            'netProfitMargin': 'compute_net_profit_margin',
            'returnOnAssets': 'compute_return_on_assets',
            'returnOnEquity': 'compute_return_on_equity',
            'returnOnCapitalEmployed': 'compute_return_on_capital_employed',
            'debtRatio': 'compute_debt_ratio',
            'debtEquityRatio': 'compute_debt_to_equity_ratio',
            'longTermDebtToCapitalization': 'compute_long_term_debt_to_capitalization',
            'interestCoverage': 'compute_interest_coverage',
            'cashFlowToDebtRatio': 'compute_cash_flow_to_debt_ratio',
            'receivablesTurnover': 'compute_receivables_turnover',
            'payablesTurnover': 'compute_payables_turnover',
            'inventoryTurnover': 'compute_inventory_turnover',
            'fixedAssetTurnover': 'compute_fixed_asset_turnover',
            'assetTurnover': 'compute_asset_turnover',
            'operatingCashFlowPerShare': 'compute_operating_cash_flow_per_share',
            'freeCashFlowPerShare': 'compute_free_cash_flow_per_share',
            'payoutRatio': 'compute_payout_ratio',
            'operatingCashFlowSalesRatio': 'compute_operating_cash_flow_sales_ratio',
            'freeCashFlowOperatingCashFlowRatio': 'compute_free_cash_flow_operating_cash_flow_ratio',
            'priceEarningsRatio': 'compute_price_earnings_ratio',
            'priceBookValueRatio': 'compute_price_book_value_ratio',
            'dividendYield': 'compute_dividend_yield',
            'priceToSalesRatio': 'compute_price_to_sales_ratio'
        }

        results = {}
        for ratio_name, peer_data in peer_ratios.items():
            if not isinstance(peer_data, dict) or 'average' not in peer_data:
                continue  # Skip invalid peer data
            peer_avg = peer_data['average']
            std_dev = peer_data.get('std_dev')

            method_name = ratio_mappings.get(ratio_name)
            if method_name:
                compute_method = getattr(self, method_name)
                company_value = compute_method(ticker_symbol, period_type, fiscal_date)

                difference = None
                z_score = None
                if company_value is not None:
                    difference = company_value - peer_avg
                    if std_dev is not None and std_dev != 0:
                        z_score = difference / std_dev

                results[ratio_name] = {
                    'company': company_value,
                    'peer_average': peer_avg,
                    'difference': difference,
                    'z_score': z_score
                }

        return results

    def analyze_ratio_trends(self, ticker_symbol, period_type, ratio_name, fiscal_dates):
        """
        Analyzes trends for a specified ratio over multiple periods.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            period_type (str): 'annual' or 'quarterly'.
            ratio_name (str): Name of the ratio (e.g., 'returnOnEquity').
            fiscal_dates (list): List of fiscal dates (str, YYYY-MM-DD).

        Returns:
            dict: {
                'ratio_values': {date: value or None},
                'cagr': float or None,
                'avg_annual_change': float or None,
                'volatility': float or None,
                'periods': int
            } or None if invalid inputs.
        """
        if not isinstance(ticker_symbol, str) or not isinstance(period_type, str) or not isinstance(ratio_name, str) or not isinstance(fiscal_dates, list):
            raise ValueError("ticker_symbol, period_type, ratio_name must be strings, fiscal_dates list.")

        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        ratio_mappings = {
            'currentRatio': 'compute_current_ratio',
            'quickRatio': 'compute_quick_ratio',
            'cashRatio': 'compute_cash_ratio',
            'grossProfitMargin': 'compute_gross_profit_margin',
            'operatingProfitMargin': 'compute_operating_profit_margin',
            'netProfitMargin': 'compute_net_profit_margin',
            'returnOnAssets': 'compute_return_on_assets',
            'returnOnEquity': 'compute_return_on_equity',
            'returnOnCapitalEmployed': 'compute_return_on_capital_employed',
            'debtRatio': 'compute_debt_ratio',
            'debtEquityRatio': 'compute_debt_to_equity_ratio',
            'longTermDebtToCapitalization': 'compute_long_term_debt_to_capitalization',
            'interestCoverage': 'compute_interest_coverage',
            'cashFlowToDebtRatio': 'compute_cash_flow_to_debt_ratio',
            'receivablesTurnover': 'compute_receivables_turnover',
            'payablesTurnover': 'compute_payables_turnover',
            'inventoryTurnover': 'compute_inventory_turnover',
            'fixedAssetTurnover': 'compute_fixed_asset_turnover',
            'assetTurnover': 'compute_asset_turnover',
            'operatingCashFlowPerShare': 'compute_operating_cash_flow_per_share',
            'freeCashFlowPerShare': 'compute_free_cash_flow_per_share',
            'payoutRatio': 'compute_payout_ratio',
            'operatingCashFlowSalesRatio': 'compute_operating_cash_flow_sales_ratio',
            'freeCashFlowOperatingCashFlowRatio': 'compute_free_cash_flow_operating_cash_flow_ratio',
            'priceEarningsRatio': 'compute_price_earnings_ratio',
            'priceBookValueRatio': 'compute_price_book_value_ratio',
            'dividendYield': 'compute_dividend_yield',
            'priceToSalesRatio': 'compute_price_to_sales_ratio'
        }

        method_name = ratio_mappings.get(ratio_name)
        if not method_name:
            return None
        compute_method = getattr(self, method_name)

        fiscal_dates = sorted(fiscal_dates)
        ratio_values = {}
        for date in fiscal_dates:
            value = compute_method(ticker_symbol, period_type, date)
            ratio_values[date] = value

        valid_values = [(date, val) for date, val in ratio_values.items() if val is not None]
        if len(valid_values) < 2:
            return {
                'ratio_values': ratio_values,
                'cagr': None,
                'avg_annual_change': None,
                'volatility': None,
                'periods': len(valid_values)
            }

        dates, values = zip(*valid_values)
        changes = []
        for i in range(1, len(values)):
            if values[i-1] != 0:
                change = (values[i] - values[i-1]) / values[i-1]
                changes.append(change)

        start = values[0]
        end = values[-1]
        n = len(valid_values) - 1
        cagr = None
        if start > 0 and end > 0:
            try:
                cagr = (end / start) ** (1 / n) - 1
            except ZeroDivisionError:
                cagr = None

        avg_annual_change = np.mean(changes) if changes else None
        volatility = np.std(changes) if len(changes) > 1 else None

        return {
            'ratio_values': ratio_values,
            'cagr': cagr,
            'avg_annual_change': avg_annual_change,
            'volatility': volatility,
            'periods': len(valid_values)
        }

    def log_validation_results(self, ticker_symbol, period_type, fiscal_date, validation_result):
        directory = os.path.join('MyCFATool', 'data', 'audit_logs')
        if not os.path.exists(directory):
            os.makedirs(directory)
        file_path = os.path.join(directory, 'audit_logs.csv')
        write_header = not os.path.exists(file_path) or os.stat(file_path).st_size == 0
        with open(file_path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if write_header:
                writer.writerow(['timestamp', 'ticker', 'period', 'ratio_name', 'computed_value', 'reported_value', 'percentage_difference', 'is_discrepancy'])
            for ratio_name, res in validation_result.items():
                if res['discrepancy_flag']:
                    row = [
                        datetime.now().isoformat(),
                        ticker_symbol,
                        period_type,
                        ratio_name,
                        res['computed'],
                        res['reported'],
                        res['percentage_difference'],
                        res['discrepancy_flag']
                    ]
                    writer.writerow(row)

    def blockchain_audit_log(self, data):
        if not isinstance(data, str):
            raise ValueError("data must be a string")

        directory = os.path.join('MyCFATool', 'data', 'audit_logs')
        if not os.path.exists(directory):
            os.makedirs(directory)

        csv_file = os.path.join(directory, 'blockchain_audit.csv')

        previous_hash = '0'
        if os.path.exists(csv_file) and os.path.getsize(csv_file) > 0:
            with open(csv_file, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
                if rows:
                    previous_hash = rows[-1][3]  # current_hash column

        current_hash = hashlib.sha256((previous_hash + data).encode()).hexdigest()

        write_header = not os.path.exists(csv_file) or os.path.getsize(csv_file) == 0

        with open(csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(['timestamp', 'data', 'previous_hash', 'current_hash'])

            writer.writerow([datetime.now().isoformat(), data, previous_hash, current_hash])

        return current_hash

    def compute_enterprise_value_multiple(self):
        pass

    def compute_price_fair_value(self):
        pass

    def assess_risk_metrics(self, ticker_symbol, period_type, fiscal_date):
        """
        Assess risk metrics: volatility and beta from historical price data.

        Volatility is the standard deviation of price returns.
        Beta is not computed as market data is not available.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            period_type (str): 'annual' or 'quarterly'.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format.

        Returns:
            dict: {'volatility': float or None, 'beta': None}
        """
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get historical prices ordered by date
        prices = self.conn.execute("SELECT date, price FROM historical_price WHERE ticker_id = ? ORDER BY date", (ticker_id,)).fetchall()

        if not prices or len(prices) < 2:
            return {'volatility': None, 'beta': None}

        # Compute returns
        returns = []
        for i in range(1, len(prices)):
            prev_price = prices[i-1][1]
            curr_price = prices[i][1]
            if prev_price == 0:
                continue  # Skip division by zero
            ret = (curr_price / prev_price) - 1
            returns.append(ret)

        if not returns:
            return {'volatility': None, 'beta': None}

        volatility = np.std(returns)

        # Beta not available
        beta = None

        return {'volatility': volatility, 'beta': beta}

    def generate_audit_report(self, ticker_symbol, period_type, fiscal_date, trend_dates=None):
        """
        Generate a comprehensive audit report aggregating results from various validation and analysis methods.

        The report includes summary, scores, trends, and recommendations based on institutional-level financial metrics.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            period_type (str): 'annual' or 'quarterly'.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format.
            trend_dates (list of str, optional): List of fiscal dates for trend analysis. If None, uses [fiscal_date].

        Returns:
            dict: Comprehensive report with keys:
                - 'summary' (str): High-level assessment.
                - 'scores' (dict): Altman Z-score, Piotroski F-score, ROE scores.
                - 'trends' (dict or None): Trend analysis for returnOnEquity.
                - 'recommendations' (list): List of recommended actions.
                - 'discrepancies_logged' (bool): Whether discrepancies were logged.
                - 'missing_data' (list): List of methods with missing data.
        """
        # Input validation
        if not isinstance(ticker_symbol, str) or not isinstance(period_type, str) or not isinstance(fiscal_date, str):
            raise ValueError("ticker_symbol, period_type, and fiscal_date must be strings.")

        report = {
            'summary': '',
            'scores': {},
            'trends': None,
            'recommendations': [],
            'discrepancies_logged': False,
            'missing_data': []
        }

        # Validate ratios and log discrepancies
        validation_result = self.validate_ratios(ticker_symbol, period_type, fiscal_date)
        discrepancies = [k for k, v in validation_result.items() if v['discrepancy_flag']]
        if discrepancies:
            self.log_validation_results(ticker_symbol, period_type, fiscal_date, validation_result)
            report['discrepancies_logged'] = True
            report['recommendations'].append("Review reported ratios for discrepancies in: {}".format(', '.join(discrepancies)))

        # DuPont Analysis
        dupont = self.compute_dupont_analysis(ticker_symbol, period_type, fiscal_date)
        if dupont:
            report['scores']['dupont_roe'] = dupont['calculated_roe']
            report['scores']['phase3_roe'] = dupont['phase3_roe']
            if not dupont['match']:
                report['recommendations'].append("DuPont ROE does not match Phase 3 ROE; investigate decomposition.")
            if dupont['incomplete']:
                report['missing_data'].append('dupont_analysis')
        else:
            report['missing_data'].append('dupont_analysis')

        # Altman Z-Score
        altman = self.compute_altman_z_score(ticker_symbol, period_type, fiscal_date)
        if altman:
            report['scores']['altman_z'] = altman['z_score']
            report['scores']['altman_risk'] = altman['risk']
            if altman['risk'] == 'distress':
                report['recommendations'].append("High bankruptcy risk; consider financial restructuring.")
            elif altman['risk'] == 'gray':
                report['recommendations'].append("Moderate bankruptcy risk; monitor financial health.")
        else:
            report['missing_data'].append('altman_z_score')

        # Piotroski F-Score
        piotroski = self.compute_piotroski_f_score(ticker_symbol, period_type, fiscal_date)
        if piotroski is not None:
            report['scores']['piotroski_f'] = piotroski
            if piotroski < 4:
                report['recommendations'].append("Low F-score indicates weak fundamentals; review financial statements.")
        else:
            report['missing_data'].append('piotroski_f_score')

        # Risk Metrics
        risk = self.assess_risk_metrics(ticker_symbol, period_type, fiscal_date)
        if risk:
            report['scores']['volatility'] = risk['volatility']
            if risk['volatility'] and risk['volatility'] > 0.3:  # Arbitrary threshold
                report['recommendations'].append("High price volatility; consider diversification.")
        else:
            report['missing_data'].append('risk_metrics')

        # Trends
        if trend_dates:
            trends = self.analyze_ratio_trends(ticker_symbol, period_type, 'returnOnEquity', trend_dates)
            if trends:
                report['trends'] = trends
                if trends['cagr'] and trends['cagr'] < 0:
                    report['recommendations'].append("Declining ROE trend; investigate profitability.")
                if trends['volatility'] and trends['volatility'] > 0.2:
                    report['recommendations'].append("High ROE volatility; assess stability.")
            else:
                report['missing_data'].append('ratio_trends')

        # Summary
        score_parts = []
        if 'altman_risk' in report['scores']:
            score_parts.append(f"Bankruptcy risk: {report['scores']['altman_risk']}")
        if 'piotroski_f' in report['scores']:
            score_parts.append(f"F-score: {report['scores']['piotroski_f']}/9")
        if 'dupont_roe' in report['scores'] and report['scores']['dupont_roe'] is not None:
            score_parts.append(f"DuPont ROE: {report['scores']['dupont_roe']:.3f}")
        if score_parts:
            report['summary'] = f"Financial audit summary: {'; '.join(score_parts)}. {len(report['missing_data'])} missing analyses."
        else:
            report['summary'] = "Unable to generate summary due to missing data."

        return report

    def monte_carlo_risk_simulation(self, ticker_symbol, period_type, fiscal_date, ratio_name, num_periods=5, num_simulations=1000):
        """
        Perform Monte Carlo simulation for risk assessment of a financial ratio.

        Simulates future values of the specified ratio over num_periods using historical mean and volatility.
        Calculates VaR at 95% confidence and other risk metrics.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            period_type (str): 'annual' or 'quarterly'.
            fiscal_date (str): Current fiscal date in 'YYYY-MM-DD' format.
            ratio_name (str): Name of the ratio (e.g., 'returnOnEquity').
            num_periods (int): Number of periods to simulate (default 5).
            num_simulations (int): Number of simulations (default 1000).

        Returns:
            dict or None: Risk metrics or None if insufficient data.
                Keys: 'current_ratio', 'historical_mean', 'historical_volatility', 'simulated_mean', 'simulated_std', 'var_95', 'probability_below_zero'
        """
        ratio_mappings = {
            'currentRatio': 'compute_current_ratio',
            'quickRatio': 'compute_quick_ratio',
            'cashRatio': 'compute_cash_ratio',
            'grossProfitMargin': 'compute_gross_profit_margin',
            'operatingProfitMargin': 'compute_operating_profit_margin',
            'netProfitMargin': 'compute_net_profit_margin',
            'returnOnAssets': 'compute_return_on_assets',
            'returnOnEquity': 'compute_return_on_equity',
            'returnOnCapitalEmployed': 'compute_return_on_capital_employed',
            'debtRatio': 'compute_debt_ratio',
            'debtEquityRatio': 'compute_debt_to_equity_ratio',
            'longTermDebtToCapitalization': 'compute_long_term_debt_to_capitalization',
            'interestCoverage': 'compute_interest_coverage',
            'cashFlowToDebtRatio': 'compute_cash_flow_to_debt_ratio',
            'receivablesTurnover': 'compute_receivables_turnover',
            'payablesTurnover': 'compute_payables_turnover',
            'inventoryTurnover': 'compute_inventory_turnover',
            'fixedAssetTurnover': 'compute_fixed_asset_turnover',
            'assetTurnover': 'compute_asset_turnover',
            'operatingCashFlowPerShare': 'compute_operating_cash_flow_per_share',
            'freeCashFlowPerShare': 'compute_free_cash_flow_per_share',
            'payoutRatio': 'compute_payout_ratio',
            'operatingCashFlowSalesRatio': 'compute_operating_cash_flow_sales_ratio',
            'freeCashFlowOperatingCashFlowRatio': 'compute_free_cash_flow_operating_cash_flow_ratio',
            'priceEarningsRatio': 'compute_price_earnings_ratio',
            'priceBookValueRatio': 'compute_price_book_value_ratio',
            'dividendYield': 'compute_dividend_yield',
            'priceToSalesRatio': 'compute_price_to_sales_ratio'
        }

        method_name = ratio_mappings.get(ratio_name)
        if not method_name:
            return None

        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get historical fiscal_dates
        cursor = self.conn.execute("""
            SELECT DISTINCT fiscal_date FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ?
            ORDER BY fiscal_date DESC
        """, (ticker_id, period_type))
        dates = [row[0] for row in cursor.fetchall()]

        historical_dates = [d for d in dates if d != fiscal_date][:10]  # Up to 10 past dates

        # Compute historical ratios
        historical_ratios = []
        compute_method = getattr(self, method_name)
        for date in historical_dates:
            ratio = compute_method(ticker_symbol, period_type, date)
            if ratio is not None:
                historical_ratios.append(ratio)

        if len(historical_ratios) < 3:
            return None  # Insufficient data

        historical_mean = np.mean(historical_ratios)
        historical_vol = np.std(historical_ratios)

        # Get current ratio
        current_ratio = compute_method(ticker_symbol, period_type, fiscal_date)
        if current_ratio is None:
            return None

        # Simulate
        np.random.seed(42)  # For reproducibility
        simulated_final = []
        for _ in range(num_simulations):
            # Simple random walk: final = current + normal(0, vol * sqrt(periods))
            shock = np.random.normal(0, historical_vol * np.sqrt(num_periods))
            final = current_ratio + shock
            simulated_final.append(final)

        simulated_final = np.array(simulated_final)

        # VaR at 95%: 5th percentile (value below which 5% of outcomes fall)
        var_95 = np.percentile(simulated_final, 5)

        # Probability below zero (for ratios like ROE, negative might be risk)
        prob_below_zero = np.mean(simulated_final < 0)

        return {
            'current_ratio': current_ratio,
            'historical_mean': historical_mean,
            'historical_volatility': historical_vol,
            'simulated_mean': np.mean(simulated_final),
            'simulated_std': np.std(simulated_final),
            'var_95': var_95,
            'probability_below_zero': prob_below_zero
        }

    def compute_graham_number(self, ticker_symbol, period_type, fiscal_date):
        """
        Compute the Graham Number (intrinsic value) and compare to current price.

        The Graham Number is calculated as sqrt(22.5 * EPS * BVPS), where EPS is earnings per share
        and BVPS is book value per share. Compares to current price to assess valuation.

        Args:
            ticker_symbol (str): The stock ticker symbol (e.g., 'AAPL').
            period_type (str): 'annual' or 'quarterly'.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format.

        Returns:
            dict or None: {'graham_number': float, 'current_price': float, 'assessment': str} or None if missing data.
        """
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get income statement for netIncome
        income_statement = self.conn.execute("""
            SELECT statement_data FROM income_statement
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        # Get balance sheet for totalShareholdersEquity and commonStockSharesOutstanding
        balance_statement = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        # Get historical price
        price_record = self.conn.execute("""
            SELECT price FROM historical_price
            WHERE ticker_id = ? AND date = ?
        """, (ticker_id, fiscal_date)).fetchone()

        if not income_statement or not balance_statement or not price_record:
            return None

        income_data = json.loads(income_statement[0])
        balance_data = json.loads(balance_statement[0])
        price = price_record[0]

        net_income = income_data.get('netIncome')
        shares_outstanding = balance_data.get('commonStockSharesOutstanding')
        equity = balance_data.get('totalShareholdersEquity')

        if net_income is None or shares_outstanding is None or shares_outstanding == 0 or equity is None or price is None:
            return None

        eps = net_income / shares_outstanding
        bvps = equity / shares_outstanding
        graham_number = (22.5 * eps * bvps) ** 0.5

        if graham_number > price:
            assessment = 'undervalued'
        elif graham_number < price:
            assessment = 'overvalued'
        else:
            assessment = 'fair'

        return {'graham_number': graham_number, 'current_price': price, 'assessment': assessment}

    def compute_dcf_valuation(self, ticker_symbol, period_type, fiscal_date, growth_rate, terminal_growth, wacc, periods):
        """
        Compute DCF Valuation: estimates intrinsic value using discounted free cash flows over N years, terminal value (perpetuity growth), and WACC.
        Compares to market price for assessment.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            period_type (str): 'annual' or 'quarterly'.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format.
            growth_rate (float): Growth rate for FCF projections.
            terminal_growth (float): Terminal growth rate.
            wacc (float): Weighted average cost of capital.
            periods (int): Number of years to project.

        Returns:
            dict or None: {'intrinsic_value': float, 'market_price': float or None, 'assessment': str or None} or None if missing FCF data.
        """
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get cash flow statement
        cash_statement = self.conn.execute("""
            SELECT statement_data FROM cash_flow
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not cash_statement:
            return None

        data = json.loads(cash_statement[0])

        operating_cash_flow = data.get('operatingCashFlow')
        capital_expenditures = data.get('capitalExpenditures')

        if operating_cash_flow is None or capital_expenditures is None:
            return None

        fcf = operating_cash_flow - capital_expenditures

        # Project and discount FCF over periods
        discounted_fcf_sum = 0.0
        for t in range(1, periods + 1):
            projected_fcf = fcf * ((1 + growth_rate) ** t)
            discount_factor = (1 + wacc) ** t
            discounted_fcf_sum += projected_fcf / discount_factor

        # Terminal value
        if wacc <= terminal_growth:
            return None  # Invalid, WACC must be > terminal growth
        terminal_fcf = fcf * ((1 + growth_rate) ** periods) * (1 + terminal_growth) / (wacc - terminal_growth)
        discounted_terminal = terminal_fcf / ((1 + wacc) ** periods)

        intrinsic_value = discounted_fcf_sum + discounted_terminal

        # Get market price
        price_record = self.conn.execute("""
            SELECT price FROM historical_price
            WHERE ticker_id = ? AND date = ?
        """, (ticker_id, fiscal_date)).fetchone()

        market_price = None
        assessment = None
        if price_record:
            market_price = price_record[0]
            if intrinsic_value > market_price:
                assessment = 'undervalued'
            elif intrinsic_value < market_price:
                assessment = 'overvalued'
            else:
                assessment = 'fair'

        return {'intrinsic_value': intrinsic_value, 'market_price': market_price, 'assessment': assessment}

    def compute_merton_dd(self, ticker_symbol, period_type, fiscal_date, rf, T):
        """
        Compute Merton's Distance to Default (DD) and default probability.

        DD = [ln(MV_Equity / Debt) + (rf - 0.5*sigma^2)*T] / (sigma * sqrt(T))
        where sigma is the volatility of equity returns, MV_Equity = price * shares_outstanding, Debt = total_liabilities.

        Default probability is calculated as norm.cdf(-DD), assuming DD ~ N(0,1).

        Args:
            ticker_symbol (str): The stock ticker symbol.
            period_type (str): 'annual' or 'quarterly'.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format.
            rf (float): Risk-free rate (decimal, e.g., 0.05 for 5%).
            T (float): Time horizon in years (e.g., 1.0 for 1 year).

        Returns:
            dict or None: {'dd': float, 'default_probability': float, 'interpretation': str} or None if missing data.
        """
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get balance sheet for debt and shares outstanding
        balance_statement = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not balance_statement:
            return None

        balance_data = json.loads(balance_statement[0])

        debt = balance_data.get('totalLiabilities')
        shares_outstanding = balance_data.get('commonStockSharesOutstanding')

        # Get historical price for MV_Equity
        price_record = self.conn.execute("""
            SELECT price FROM historical_price
            WHERE ticker_id = ? AND date = ?
        """, (ticker_id, fiscal_date)).fetchone()

        if not price_record:
            return None

        price = price_record[0]

        if debt is None or shares_outstanding is None or shares_outstanding == 0 or price is None or debt == 0:
            return None

        mv_equity = price * shares_outstanding

        # Compute sigma from historical price returns
        prices = self.conn.execute("SELECT date, price FROM historical_price WHERE ticker_id = ? ORDER BY date", (ticker_id,)).fetchall()

        if not prices or len(prices) < 2:
            return None

        returns = []
        for i in range(1, len(prices)):
            prev_price = prices[i-1][1]
            curr_price = prices[i][1]
            if prev_price == 0:
                continue
            ret = (curr_price / prev_price) - 1
            returns.append(ret)

        if not returns:
            return None

        sigma = np.std(returns)

        if sigma == 0 or T <= 0:
            return None

        # Compute DD
        ln_ratio = np.log(mv_equity / debt)
        term1 = ln_ratio + (rf - 0.5 * sigma**2) * T
        term2 = sigma * np.sqrt(T)

        dd = term1 / term2

        # Default probability
        default_probability = norm.cdf(-dd)

        # Interpretation
        if default_probability < 0.01:
            interpretation = "Very low default risk."
        elif default_probability < 0.05:
            interpretation = "Low default risk."
        elif default_probability < 0.10:
            interpretation = "Moderate default risk."
        else:
            interpretation = "High default risk."

        return {
            'dd': dd,
            'default_probability': default_probability,
            'interpretation': interpretation
        }

    def compute_ohlson_o_score(self, ticker_symbol, period_type, fiscal_date):
        """
        Compute Ohlson O-Score for bankruptcy prediction.

        The O-Score uses 9 variables from current and previous periods.
        Score > 0.5 suggests high distress risk.
        Requires 3 periods for NI changes.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            period_type (str): 'annual' or 'quarterly'.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format for the current period.

        Returns:
            dict or None: {'o_score': float, 'risk': 'low' or 'high'} or None if insufficient data.
        """
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Compute previous dates (assuming annual, t-1 = fiscal_date -1 year, t-2 = -2 years)
        try:
            current_dt = datetime.fromisoformat(fiscal_date)
            previous_dt = current_dt.replace(year=current_dt.year - 1)
            previous_fiscal_date = previous_dt.isoformat()[:10]
            tm2_dt = current_dt.replace(year=current_dt.year - 2)
            tm2_fiscal_date = tm2_dt.isoformat()[:10]
        except ValueError:
            return None

        # Get data for t, t-1, t-2
        balance_t = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        income_t = self.conn.execute("""
            SELECT statement_data FROM income_statement
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        cash_t = self.conn.execute("""
            SELECT statement_data FROM cash_flow
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        income_tm1 = self.conn.execute("""
            SELECT statement_data FROM income_statement
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, previous_fiscal_date)).fetchone()

        income_tm2 = self.conn.execute("""
            SELECT statement_data FROM income_statement
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, tm2_fiscal_date)).fetchone()

        if not balance_t or not income_t or not cash_t or not income_tm1 or not income_tm2:
            return None

        bal = json.loads(balance_t[0])
        inc_t = json.loads(income_t[0])
        cas_t = json.loads(cash_t[0])
        inc_tm1 = json.loads(income_tm1[0])
        inc_tm2 = json.loads(income_tm2[0])

        # Extract variables
        TA = bal.get('totalAssets')
        TL = bal.get('totalLiabilities')
        WC = bal.get('totalCurrentAssets') - bal.get('totalCurrentLiabilities') if bal.get('totalCurrentAssets') and bal.get('totalCurrentLiabilities') else None
        CA = bal.get('totalCurrentAssets')
        CL = bal.get('totalCurrentLiabilities')
        EBIT = inc_t.get('operatingIncome')
        NI_t = inc_t.get('netIncome')
        NI_tm1 = inc_tm1.get('netIncome')
        NI_tm2 = inc_tm2.get('netIncome')
        FFO = cas_t.get('operatingCashFlow')  # Assuming FFO is operatingCashFlow

        if (TA is None or TL is None or WC is None or CA is None or CL is None or EBIT is None or
            NI_t is None or NI_tm1 is None or NI_tm2 is None or FFO is None or
            TA == 0 or CL == 0):
            return None

        # Compute ratios
        log_TA = np.log(TA)
        TL_TA = TL / TA
        WC_TA = WC / TA
        CL_CA = CL / CA
        EBIT_TA = EBIT / TA
        NI_tm1_NI_t = NI_tm1 / NI_t if NI_t != 0 else None
        FFO_TA = FFO / TA
        NI_t_NI_tm1 = NI_t / NI_tm1 if NI_tm1 != 0 else None
        NI_tm1_NI_tm2 = NI_tm1 / NI_tm2 if NI_tm2 != 0 else None

        if NI_tm1_NI_t is None or NI_t_NI_tm1 is None or NI_tm1_NI_tm2 is None:
            return None

        # O-Score formula
        o_score = (-1.32 - 0.407 * log_TA + 6.03 * TL_TA - 1.43 * WC_TA + 0.076 * CL_CA -
                   1.72 * EBIT_TA - 2.37 * NI_tm1_NI_t - 1.83 * FFO_TA + 0.285 * NI_t_NI_tm1 -
                   0.521 * NI_tm1_NI_tm2)

        risk = 'high' if o_score > 0.5 else 'low'

        return {'o_score': o_score, 'risk': risk}

    def compute_ev_multiples(self, ticker_symbol, period_type, fiscal_date):
        """
        Compute Enterprise Value Multiples: EV/EBITDA and EV/Sales.

        EV = Market Cap + Debt - Cash

        Market Cap = Price * Shares Outstanding

        Provides assessment for EV/EBITDA: low <10 attractive, high >20 expensive, else moderate.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            period_type (str): 'annual' or 'quarterly'.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format.

        Returns:
            dict or None: {'ev': float, 'ev_ebitda': float or None, 'ev_sales': float, 'ev_ebitda_assessment': str or None} or None if missing data.
        """
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get balance sheet for debt, cash, shares
        balance_statement = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        # Get income statement for revenue, operatingIncome, depreciation
        income_statement = self.conn.execute("""
            SELECT statement_data FROM income_statement
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        # Get price
        price_record = self.conn.execute("""
            SELECT price FROM historical_price
            WHERE ticker_id = ? AND date = ?
        """, (ticker_id, fiscal_date)).fetchone()

        if not balance_statement or not income_statement or not price_record:
            return None

        balance_data = json.loads(balance_statement[0])
        income_data = json.loads(income_statement[0])
        price = price_record[0]

        debt = balance_data.get('totalLiabilities')
        cash = balance_data.get('cashAndCashEquivalents')
        shares = balance_data.get('commonStockSharesOutstanding')
        revenue = income_data.get('revenue')
        operating_income = income_data.get('operatingIncome')
        depreciation = income_data.get('depreciationAndAmortization')

        if debt is None or shares is None or price is None or revenue is None or operating_income is None:
            return None

        if shares == 0 or revenue == 0:
            return None

        market_cap = price * shares
        ev = market_cap + debt - (cash if cash is not None else 0)

        ebitda = operating_income + (depreciation if depreciation is not None else 0)

        if ebitda == 0:
            ev_ebitda = None
        else:
            ev_ebitda = ev / ebitda

        ev_sales = ev / revenue

        assessment = None
        if ev_ebitda is not None:
            if ev_ebitda < 10:
                assessment = "attractive"
            elif ev_ebitda > 20:
                assessment = "expensive"
            else:
                assessment = "moderate"

        return {
            'ev': ev,
            'ev_ebitda': ev_ebitda,
            'ev_sales': ev_sales,
            'ev_ebitda_assessment': assessment
        }

    def perform_stress_test(self, ticker_symbol, period_type, fiscal_date, stress_factors):
        """
        Perform stress testing by applying stress factors to base financials and recalculating key ratios.

        Stress factors: dict with 'revenue_change', 'cost_change', 'interest_rate_change' (decimals, e.g., 0.1 for 10% increase)

        Returns dict: {'stressed_ratios': {'roe': float, 'roa': float, 'current_ratio': float, 'debt_ratio': float},
                       'impact_analysis': {'ratio_name': {'base': float, 'stressed': float, 'difference': float}}}
        or None if missing data.

        """
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get statements
        balance_stmt = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        income_stmt = self.conn.execute("""
            SELECT statement_data FROM income_statement
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not balance_stmt or not income_stmt:
            return None

        balance_data = json.loads(balance_stmt[0])
        income_data = json.loads(income_stmt[0])

        # Extract base values
        revenue = income_data.get('revenue')
        cost_of_revenue = income_data.get('costOfRevenue')
        interest_expense = income_data.get('interestExpense')
        net_income = income_data.get('netIncome')
        total_assets = balance_data.get('totalAssets')
        total_shareholders_equity = balance_data.get('totalShareholdersEquity')
        total_liabilities = balance_data.get('totalLiabilities')
        total_current_assets = balance_data.get('totalCurrentAssets')
        total_current_liabilities = balance_data.get('totalCurrentLiabilities')

        # Check required
        if (revenue is None or cost_of_revenue is None or interest_expense is None or net_income is None or
            total_assets is None or total_shareholders_equity is None or total_liabilities is None or
            total_current_assets is None or total_current_liabilities is None or
            total_assets == 0 or total_shareholders_equity == 0 or total_current_liabilities == 0):
            return None

        # Get stress factors
        revenue_change = stress_factors.get('revenue_change', 0)
        cost_change = stress_factors.get('cost_change', 0)
        interest_rate_change = stress_factors.get('interest_rate_change', 0)

        # Calculate delta net_income
        delta_net_income = (revenue_change * revenue) - (cost_change * cost_of_revenue) - (interest_rate_change * interest_expense)

        # Stressed net_income
        stressed_net_income = net_income + delta_net_income

        # Compute base ratios
        base_roe = net_income / total_shareholders_equity
        base_roa = net_income / total_assets
        base_current_ratio = total_current_assets / total_current_liabilities
        base_debt_ratio = total_liabilities / total_assets

        # Stressed ratios (current and debt unchanged)
        stressed_roe = stressed_net_income / total_shareholders_equity
        stressed_roa = stressed_net_income / total_assets
        stressed_current_ratio = base_current_ratio  # unchanged
        stressed_debt_ratio = base_debt_ratio  # unchanged

        # Impact analysis
        impact_analysis = {
            'roe': {
                'base': base_roe,
                'stressed': stressed_roe,
                'difference': stressed_roe - base_roe
            },
            'roa': {
                'base': base_roa,
                'stressed': stressed_roa,
                'difference': stressed_roa - base_roa
            },
            'current_ratio': {
                'base': base_current_ratio,
                'stressed': stressed_current_ratio,
                'difference': 0
            },
            'debt_ratio': {
                'base': base_debt_ratio,
                'stressed': stressed_debt_ratio,
                'difference': 0
            }
        }

        return {
            'stressed_ratios': {
                'roe': stressed_roe,
                'roa': stressed_roa,
                'current_ratio': stressed_current_ratio,
                'debt_ratio': stressed_debt_ratio
            },
            'impact_analysis': impact_analysis
        }

    def perform_scenario_analysis(self, ticker_symbol, period_type, fiscal_date, scenario_factors):
        """
        Perform scenario analysis by applying scenario factors to financials and recalculating key ratios.

        Scenario factors: dict with 'revenue_change', 'cost_change', 'interest_rate_change', etc. (decimals, e.g., 0.1 for 10% increase)

        Recalculates ROE, ROA, debt ratio, etc., and returns scenario impacts.

        Returns dict: {'base_ratios': {'roe': float, 'roa': float, 'debt_ratio': float, ...},
                       'scenario_ratios': {'roe': float, 'roa': float, 'debt_ratio': float, ...},
                       'scenario_impacts': {'ratio_name': {'base': float, 'scenario': float, 'difference': float, 'percentage_change': float or None}}}
        or None if missing data.
        """
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get statements
        balance_stmt = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        income_stmt = self.conn.execute("""
            SELECT statement_data FROM income_statement
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not balance_stmt or not income_stmt:
            return None

        balance_data = json.loads(balance_stmt[0])
        income_data = json.loads(income_stmt[0])

        # Extract base values
        revenue = income_data.get('revenue')
        cost_of_revenue = income_data.get('costOfRevenue')
        interest_expense = income_data.get('interestExpense')
        net_income = income_data.get('netIncome')
        total_assets = balance_data.get('totalAssets')
        total_shareholders_equity = balance_data.get('totalShareholdersEquity')
        total_liabilities = balance_data.get('totalLiabilities')
        total_current_assets = balance_data.get('totalCurrentAssets')
        total_current_liabilities = balance_data.get('totalCurrentLiabilities')

        # Check required
        if (revenue is None or cost_of_revenue is None or interest_expense is None or net_income is None or
            total_assets is None or total_shareholders_equity is None or total_liabilities is None or
            total_current_assets is None or total_current_liabilities is None or
            total_assets == 0 or total_shareholders_equity == 0 or total_current_liabilities == 0):
            return None

        # Get scenario factors (default to 0 if not provided)
        revenue_change = scenario_factors.get('revenue_change', 0)
        cost_change = scenario_factors.get('cost_change', 0)
        interest_rate_change = scenario_factors.get('interest_rate_change', 0)

        # Calculate delta net_income
        delta_net_income = (revenue_change * revenue) - (cost_change * cost_of_revenue) - (interest_rate_change * interest_expense)

        # Scenario net_income
        scenario_net_income = net_income + delta_net_income

        # Compute base ratios
        base_roe = net_income / total_shareholders_equity
        base_roa = net_income / total_assets
        base_debt_ratio = total_liabilities / total_assets
        base_current_ratio = total_current_assets / total_current_liabilities

        # Scenario ratios (current ratio unchanged, debt ratio can be adjusted if debt_change, but for now unchanged like stress)
        scenario_roe = scenario_net_income / total_shareholders_equity
        scenario_roa = scenario_net_income / total_assets
        scenario_debt_ratio = base_debt_ratio  # unchanged
        scenario_current_ratio = base_current_ratio  # unchanged

        # Scenario impacts
        scenario_impacts = {}
        ratios = ['roe', 'roa', 'debt_ratio', 'current_ratio']
        base_dict = {'roe': base_roe, 'roa': base_roa, 'debt_ratio': base_debt_ratio, 'current_ratio': base_current_ratio}
        scenario_dict = {'roe': scenario_roe, 'roa': scenario_roa, 'debt_ratio': scenario_debt_ratio, 'current_ratio': scenario_current_ratio}
        for ratio in ratios:
            base_val = base_dict[ratio]
            scenario_val = scenario_dict[ratio]
            difference = scenario_val - base_val
            percentage_change = (difference / base_val * 100) if base_val != 0 else None
            scenario_impacts[ratio] = {
                'base': base_val,
                'scenario': scenario_val,
                'difference': difference,
                'percentage_change': percentage_change
            }

        return {
            'base_ratios': base_dict,
            'scenario_ratios': scenario_dict,
            'scenario_impacts': scenario_impacts
        }

    def compute_var(self, ticker_symbol, confidence=0.95):
        """
        Compute Value at Risk (VaR) using parametric, historical, and Monte Carlo methods at specified confidence level from historical price returns.

        VaR represents the maximum potential loss over a specific time period at the given confidence level.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            confidence (float): Confidence level (e.g., 0.95 for 95% confidence). Default is 0.95.

        Returns:
            dict or None: Dictionary containing 'parametric', 'historical', and 'monte_carlo' VaR values as floats, or None if insufficient data (less than 11 prices).
        """
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get historical prices ordered by date
        prices = self.conn.execute("SELECT price FROM historical_price WHERE ticker_id = ? ORDER BY date", (ticker_id,)).fetchall()
        if len(prices) < 11:  # Need at least 10 returns (11 prices)
            return None

        # Extract price values
        prices = [row[0] for row in prices]

        # Compute daily returns
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] == 0:
                continue  # Skip division by zero
            ret = (prices[i] / prices[i-1]) - 1
            returns.append(ret)

        if len(returns) < 10:
            return None  # Insufficient data

        returns = np.array(returns)
        mean = np.mean(returns)
        std = np.std(returns)

        # Parametric VaR: Assume normal distribution
        z = norm.ppf(confidence)
        parametric_var = - (mean - z * std)  # VaR as positive loss

        # Historical VaR: Empirical 5th percentile
        historical_var = - np.percentile(returns, (1 - confidence) * 100)

        # Monte Carlo VaR: Simulate 1000 returns and find percentile
        np.random.seed(42)  # For reproducibility
        simulated_returns = np.random.normal(mean, std, 1000)
        mc_var = - np.percentile(simulated_returns, (1 - confidence) * 100)

        return {
            'parametric': parametric_var,
            'historical': historical_var,
            'monte_carlo': mc_var
        }

    def compute_ddm_valuation(self, ticker_symbol, period_type, fiscal_date, required_return, growth_rate):
        """
        Compute Dividend Discount Model (DDM) valuation using Gordon Growth Model.

        Intrinsic value = Dividend per Share / (required_return - growth_rate)

        Compares intrinsic value to market price for assessment.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            period_type (str): 'annual' or 'quarterly'.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format.
            required_return (float): Required rate of return (decimal, e.g., 0.10).
            growth_rate (float): Dividend growth rate (decimal, e.g., 0.05).

        Returns:
            dict or None: {'intrinsic_value': float, 'market_price': float or None, 'assessment': str or None} or None if missing data or invalid.
        """
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get cash flow for dividendsPaid
        cash_statement = self.conn.execute("""
            SELECT statement_data FROM cash_flow
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not cash_statement:
            return None

        cash_data = json.loads(cash_statement[0])
        dividends_paid = cash_data.get('dividendsPaid')
        if dividends_paid is None:
            return None

        # Get balance sheet for shares outstanding
        balance_statement = self.conn.execute("""
            SELECT statement_data FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?
        """, (ticker_id, period_type, fiscal_date)).fetchone()

        if not balance_statement:
            return None

        balance_data = json.loads(balance_statement[0])
        shares_outstanding = balance_data.get('commonStockSharesOutstanding')
        if shares_outstanding is None or shares_outstanding == 0:
            return None

        # Calculate DPS
        dps = abs(dividends_paid) / shares_outstanding

        # Check validity
        if required_return <= growth_rate:
            return None

        intrinsic_value = dps / (required_return - growth_rate)

        # Get market price
        price_record = self.conn.execute("""
            SELECT price FROM historical_price
            WHERE ticker_id = ? AND date = ?
        """, (ticker_id, fiscal_date)).fetchone()

        market_price = None
        assessment = None
        if price_record:
            market_price = price_record[0]
            if intrinsic_value > market_price:
                assessment = 'undervalued'
            elif intrinsic_value < market_price:
                assessment = 'overvalued'
            else:
                assessment = 'fair'

        return {
            'intrinsic_value': intrinsic_value,
            'market_price': market_price,
            'assessment': assessment
        }

    def estimate_credit_rating(self, ticker_symbol, period_type, fiscal_date):
        """
        Estimate credit rating using a scorecard approach based on financial ratios.

        Assigns points for ROA, debt ratio, interest coverage, ROE, current ratio, and cash flow to debt ratio.
        Total score maps to S&P ratings: AAA (35+), AA (30-34), A (25-29), BBB (20-24), BB (15-19), B (10-14), CCC (5-9), CC (0-4), C (-5 to -1), D (-inf to -6).

        Args:
            ticker_symbol (str): The stock ticker symbol.
            period_type (str): 'annual' or 'quarterly'.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format.

        Returns:
            str or None: Estimated rating or None if insufficient data.
        """
        # Get ratios
        roa = self.compute_return_on_assets(ticker_symbol, period_type, fiscal_date)
        debt_ratio = self.compute_debt_ratio(ticker_symbol, period_type, fiscal_date)
        interest_coverage = self.compute_interest_coverage(ticker_symbol, period_type, fiscal_date)
        roe = self.compute_return_on_equity(ticker_symbol, period_type, fiscal_date)
        current_ratio = self.compute_current_ratio(ticker_symbol, period_type, fiscal_date)
        cf_to_debt = self.compute_cash_flow_to_debt_ratio(ticker_symbol, period_type, fiscal_date)

        score = 0

        # ROA points: higher better
        if roa is not None:
            if roa > 0.15: score += 7
            elif roa > 0.10: score += 5
            elif roa > 0.05: score += 3
            elif roa > 0.02: score += 1
            elif roa > 0: score += 0
            else: score -= 2

        # Debt ratio points: lower better
        if debt_ratio is not None:
            if debt_ratio < 0.20: score += 7
            elif debt_ratio < 0.30: score += 5
            elif debt_ratio < 0.40: score += 3
            elif debt_ratio < 0.50: score += 1
            elif debt_ratio < 0.60: score += 0
            else: score -= 3

        # Interest coverage points: higher better
        if interest_coverage is not None:
            if interest_coverage > 20: score += 7
            elif interest_coverage > 10: score += 5
            elif interest_coverage > 5: score += 3
            elif interest_coverage > 2: score += 1
            elif interest_coverage > 0: score += 0
            else: score -= 2

        # ROE points: higher better
        if roe is not None:
            if roe > 0.25: score += 6
            elif roe > 0.15: score += 4
            elif roe > 0.10: score += 2
            elif roe > 0.05: score += 0
            else: score -= 1

        # Current ratio points: higher better
        if current_ratio is not None:
            if current_ratio > 3: score += 5
            elif current_ratio > 2: score += 3
            elif current_ratio > 1.5: score += 1
            elif current_ratio > 1: score += 0
            else: score -= 2

        # Cash flow to debt ratio points: higher better
        if cf_to_debt is not None:
            if cf_to_debt > 1: score += 3
            elif cf_to_debt > 0.5: score += 2
            elif cf_to_debt > 0.25: score += 1
            elif cf_to_debt > 0: score += 0
            else: score -= 1

        # Map score to rating
        if score >= 35: return 'AAA'
        elif score >= 30: return 'AA'
        elif score >= 25: return 'A'
        elif score >= 20: return 'BBB'
        elif score >= 15: return 'BB'
        elif score >= 10: return 'B'
        elif score >= 5: return 'CCC'
        elif score >= 0: return 'CC'
        elif score >= -5: return 'C'
        else: return 'D'

    def compute_risk_adjusted_metrics(self, ticker_symbol, risk_free_rate=0.02):
        """
        Compute risk-adjusted performance metrics from historical price data.

        Calculates Sharpe Ratio, Sortino Ratio, and Maximum Drawdown.

        Sharpe Ratio = (mean(return) - risk_free_rate) / std(return)
        Sortino Ratio = (mean(return) - risk_free_rate) / std(downside returns)
        Maximum Drawdown = max((peak - trough) / peak)

        Args:
            ticker_symbol (str): The stock ticker symbol.
            risk_free_rate (float): Risk-free rate as decimal (default 0.02).

        Returns:
            dict or None: {'sharpe_ratio': float, 'sortino_ratio': float, 'maximum_drawdown': float} or None if insufficient data.
        """
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get historical prices ordered by date
        prices = self.conn.execute("SELECT price FROM historical_price WHERE ticker_id = ? ORDER BY date", (ticker_id,)).fetchall()
        if not prices or len(prices) < 2:
            return None

        # Extract prices
        price_list = [row[0] for row in prices]

        # Compute returns
        returns = []
        for i in range(1, len(price_list)):
            if price_list[i-1] == 0:
                continue  # Skip division by zero
            ret = (price_list[i] - price_list[i-1]) / price_list[i-1]
            returns.append(ret)

        if not returns:
            return None

        # Sharpe Ratio
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        sharpe_ratio = (mean_return - risk_free_rate) / std_return if std_return != 0 else None

        # Sortino Ratio
        downside_returns = [r for r in returns if r < 0]
        downside_std = np.std(downside_returns) if downside_returns else None
        sortino_ratio = (mean_return - risk_free_rate) / downside_std if downside_std and downside_std != 0 else None

        # Maximum Drawdown
        peak = price_list[0]
        max_drawdown = 0
        for price in price_list:
            if price > peak:
                peak = price
            drawdown = (peak - price) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        return {
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'maximum_drawdown': max_drawdown
        }

    def compute_technical_indicators(self, ticker_symbol):
        """
        Compute Technical Indicators: RSI (14), MACD (12,26,9), Bollinger Bands (20,2) from historical price data.

        Returns latest values and signals. Handles insufficient data.

        Args:
            ticker_symbol (str): The stock ticker symbol.

        Returns:
            dict or None: {
                'rsi': float, 'rsi_signal': str ('overbought', 'oversold', 'neutral'),
                'macd': float, 'macd_signal': float, 'macd_signal_type': str ('bullish', 'bearish'),
                'bollinger_upper': float, 'bollinger_lower': float, 'bollinger_signal': str ('overbought', 'oversold', 'neutral'),
                'current_price': float
            } or None if insufficient data (less than 26 prices) or ticker not found.
        """
        # Get ticker_id
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get historical prices ordered by date
        prices = self.conn.execute("SELECT date, price FROM historical_price WHERE ticker_id = ? ORDER BY date", (ticker_id,)).fetchall()

        if len(prices) < 26:
            return None  # Insufficient data

        prices_list = [p[1] for p in prices]
        price_series = pd.Series(prices_list)

        # RSI 14
        delta = price_series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        latest_rsi = rsi.iloc[-1]
        rsi_signal = 'overbought' if latest_rsi > 70 else 'oversold' if latest_rsi < 30 else 'neutral'

        # MACD
        short_ema = price_series.ewm(span=12).mean()
        long_ema = price_series.ewm(span=26).mean()
        macd = short_ema - long_ema
        signal = macd.ewm(span=9).mean()
        latest_macd = macd.iloc[-1]
        latest_signal = signal.iloc[-1]
        macd_signal = 'bullish' if latest_macd > latest_signal else 'bearish'

        # Bollinger Bands
        sma = price_series.rolling(window=20).mean()
        std = price_series.rolling(window=20).std()
        upper = sma + 2 * std
        lower = sma - 2 * std
        latest_price = price_series.iloc[-1]
        latest_upper = upper.iloc[-1]
        latest_lower = lower.iloc[-1]
        bb_signal = 'overbought' if latest_price > latest_upper else 'oversold' if latest_price < latest_lower else 'neutral'

        return {
            'rsi': latest_rsi,
            'rsi_signal': rsi_signal,
            'macd': latest_macd,
            'macd_signal': latest_signal,
            'macd_signal_type': macd_signal,
            'bollinger_upper': latest_upper,
            'bollinger_lower': latest_lower,
            'bollinger_signal': bb_signal,
            'current_price': latest_price
        }

    def value_real_options(self, current_value, strike, time, volatility, risk_free_rate):
        """
        Value a real option using the Black-Scholes model for a European call option as a proxy.

        Args:
            current_value (float): Current value of the underlying asset.
            strike (float): Strike price.
            time (float): Time to expiration in years.
            volatility (float): Volatility of the underlying asset (decimal).
            risk_free_rate (float): Risk-free rate (decimal).

        Returns:
            float or None: The option value or None if invalid inputs.
        """
        import math
        if not all(isinstance(arg, (int, float)) for arg in [current_value, strike, time, volatility, risk_free_rate]):
            return None
        if current_value <= 0 or strike <= 0 or time <= 0 or volatility < 0 or risk_free_rate < 0:
            return None

        if volatility == 0:
            # Intrinsic value for zero volatility
            discounted_strike = strike * math.exp(-risk_free_rate * time)
            return max(current_value - discounted_strike, 0)

        d1 = (math.log(current_value / strike) + (risk_free_rate + 0.5 * volatility**2) * time) / (volatility * math.sqrt(time))
        d2 = d1 - volatility * math.sqrt(time)
        call_value = current_value * norm.cdf(d1) - strike * math.exp(-risk_free_rate * time) * norm.cdf(d2)
        return call_value

    def analyze_sentiment(self, text):
        """
        Analyze the sentiment of the given text based on positive and negative word counts.

        Computes a sentiment score as the difference between positive and negative word counts.
        Returns the score and a label ('positive', 'negative', 'neutral').

        Args:
            text (str): The text to analyze.

        Returns:
            dict: {'score': int, 'label': str} or None if text is empty or invalid.
        """
        if not isinstance(text, str) or not text.strip():
            return None

        # Define positive and negative words
        positive_words = {
            'good', 'great', 'excellent', 'positive', 'happy', 'love', 'like', 'best', 'awesome', 'fantastic',
            'amazing', 'wonderful', 'brilliant', 'superb', 'outstanding', 'perfect', 'delightful', 'pleasing'
        }
        negative_words = {
            'bad', 'poor', 'terrible', 'negative', 'sad', 'hate', 'worst', 'awful', 'horrible', 'dislike',
            'ugly', 'awful', 'dreadful', 'abhorrent', 'appalling', 'atrocious', 'abominable', 'execrable'
        }

        # Preprocess text: lowercase and split into words
        words = text.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)

        score = positive_count - negative_count

        if score > 0:
            label = 'positive'
        elif score < 0:
            label = 'negative'
        else:
            label = 'neutral'

        return {'score': score, 'label': label}