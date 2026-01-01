import json
import pandas as pd
import numpy as np
from scipy.stats import norm
from sklearn.linear_model import LinearRegression
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging

from ..repositories.financial_data_repository import FinancialDataRepository


class FundamentalAnalysisService:
    """Service for fundamental analysis computations using FinancialDataRepository."""

    def __init__(self):
        self.repo = FinancialDataRepository()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.operation_count = 0
        self.failure_count = 0

    # Liquidity Ratios
    def compute_current_ratio(self, ticker_symbol: str, period_type: str, fiscal_date: str) -> Optional[Dict[str, Any]]:
        try:
            balance = self.repo.get_balance_sheet(ticker_symbol, period_type, fiscal_date)
            if not balance:
                self.logger.warning(f"[{ticker_symbol}] compute_current_ratio: No balance sheet data for {period_type} {fiscal_date}")
                return None

            data = balance['statement_data']
            total_current_assets = data.get('totalCurrentAssets')
            total_current_liabilities = data.get('totalCurrentLiabilities')

            if total_current_assets is None or total_current_liabilities is None or total_current_liabilities == 0:
                self.logger.warning(f"[{ticker_symbol}] compute_current_ratio: Missing required data in balance sheet")
                return None

            ratio = total_current_assets / total_current_liabilities
            self.operation_count += 1
            self.logger.info(f"[{ticker_symbol}] compute_current_ratio succeeded: ratio={ratio:.4f}, period_type={period_type}, fiscal_date={fiscal_date}")
            return {
                'value': ratio,
                'interpretation': 'higher than 1 indicates good short-term liquidity' if ratio > 1 else 'below 1 indicates potential liquidity issues'
            }
        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"[{ticker_symbol}] compute_current_ratio failed: {str(e)}. Inputs: ticker={ticker_symbol}, period_type={period_type}, fiscal_date={fiscal_date}")
            return None

    def compute_quick_ratio(self, ticker_symbol: str, period_type: str, fiscal_date: str) -> Optional[Dict[str, Any]]:
        try:
            balance = self.repo.get_balance_sheet(ticker_symbol, period_type, fiscal_date)
            if not balance:
                self.logger.warning(f"[{ticker_symbol}] compute_quick_ratio: No balance sheet data for {period_type} {fiscal_date}")
                return None

            data = balance['statement_data']
            total_current_assets = data.get('totalCurrentAssets')
            inventory = data.get('inventory')
            total_current_liabilities = data.get('totalCurrentLiabilities')

            if total_current_assets is None or total_current_liabilities is None or total_current_liabilities == 0:
                self.logger.warning(f"[{ticker_symbol}] compute_quick_ratio: Missing required data in balance sheet")
                return None

            quick_assets = total_current_assets - inventory if inventory is not None else total_current_assets
            ratio = quick_assets / total_current_liabilities
            self.operation_count += 1
            self.logger.info(f"[{ticker_symbol}] compute_quick_ratio succeeded: ratio={ratio:.4f}, period_type={period_type}, fiscal_date={fiscal_date}")
            return {
                'value': ratio,
                'interpretation': 'higher than 1 indicates strong liquidity excluding inventory' if ratio > 1 else 'below 1 suggests dependence on inventory for liquidity'
            }
        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"[{ticker_symbol}] compute_quick_ratio failed: {str(e)}. Inputs: ticker={ticker_symbol}, period_type={period_type}, fiscal_date={fiscal_date}")
            return None

    def compute_cash_ratio(self, ticker_symbol: str, period_type: str, fiscal_date: str) -> Optional[Dict[str, Any]]:
        try:
            balance = self.repo.get_balance_sheet(ticker_symbol, period_type, fiscal_date)
            if not balance:
                self.logger.warning(f"[{ticker_symbol}] compute_cash_ratio: No balance sheet data for {period_type} {fiscal_date}")
                return None

            data = balance['statement_data']
            cash_and_equivalents = data.get('cashAndCashEquivalents')
            total_current_liabilities = data.get('totalCurrentLiabilities')

            if cash_and_equivalents is None or total_current_liabilities is None or total_current_liabilities == 0:
                self.logger.warning(f"[{ticker_symbol}] compute_cash_ratio: Missing required data in balance sheet")
                return None

            ratio = cash_and_equivalents / total_current_liabilities
            self.operation_count += 1
            self.logger.info(f"[{ticker_symbol}] compute_cash_ratio succeeded: ratio={ratio:.4f}, period_type={period_type}, fiscal_date={fiscal_date}")
            return {
                'value': ratio,
                'interpretation': 'measures cash available to cover immediate liabilities' if ratio > 0.2 else 'low cash ratio indicates limited immediate liquidity'
            }
        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"[{ticker_symbol}] compute_cash_ratio failed: {str(e)}. Inputs: ticker={ticker_symbol}, period_type={period_type}, fiscal_date={fiscal_date}")
            return None

    # Profitability Ratios
    def compute_gross_profit_margin(self, ticker_symbol: str, period_type: str, fiscal_date: str) -> Optional[Dict[str, Any]]:
        try:
            income = self.repo.get_income_statement(ticker_symbol, period_type, fiscal_date)
            if not income:
                self.logger.warning(f"[{ticker_symbol}] compute_gross_profit_margin: No income statement data for {period_type} {fiscal_date}")
                return None

            data = income['statement_data']
            revenue = data.get('revenue')
            cost_of_revenue = data.get('costOfRevenue')

            if revenue is None or revenue == 0:
                self.logger.warning(f"[{ticker_symbol}] compute_gross_profit_margin: Missing or zero revenue in income statement")
                return None

            gross_profit = revenue - cost_of_revenue if cost_of_revenue is not None else revenue
            margin = gross_profit / revenue
            self.operation_count += 1
            self.logger.info(f"[{ticker_symbol}] compute_gross_profit_margin succeeded: margin={margin:.4f}, period_type={period_type}, fiscal_date={fiscal_date}")
            return {
                'value': margin,
                'interpretation': 'percentage of revenue retained after cost of goods sold' if margin > 0.2 else 'low margin indicates high production costs'
            }
        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"[{ticker_symbol}] compute_gross_profit_margin failed: {str(e)}. Inputs: ticker={ticker_symbol}, period_type={period_type}, fiscal_date={fiscal_date}")
            return None

    def compute_operating_profit_margin(self, ticker_symbol: str, period_type: str, fiscal_date: str) -> Optional[Dict[str, Any]]:
        try:
            income = self.repo.get_income_statement(ticker_symbol, period_type, fiscal_date)
            if not income:
                self.logger.warning(f"[{ticker_symbol}] compute_operating_profit_margin: No income statement data for {period_type} {fiscal_date}")
                return None

            data = income['statement_data']
            revenue = data.get('revenue')
            operating_income = data.get('operatingIncome')

            if revenue is None or operating_income is None or revenue == 0:
                self.logger.warning(f"[{ticker_symbol}] compute_operating_profit_margin: Missing required data in income statement")
                return None

            margin = operating_income / revenue
            self.operation_count += 1
            self.logger.info(f"[{ticker_symbol}] compute_operating_profit_margin succeeded: margin={margin:.4f}, period_type={period_type}, fiscal_date={fiscal_date}")
            return {
                'value': margin,
                'interpretation': 'measures efficiency in managing operating expenses' if margin > 0.1 else 'low margin suggests high operating costs'
            }
        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"[{ticker_symbol}] compute_operating_profit_margin failed: {str(e)}. Inputs: ticker={ticker_symbol}, period_type={period_type}, fiscal_date={fiscal_date}")
            return None

    def compute_net_profit_margin(self, ticker_symbol: str, period_type: str, fiscal_date: str) -> Optional[Dict[str, Any]]:
        try:
            income = self.repo.get_income_statement(ticker_symbol, period_type, fiscal_date)
            if not income:
                self.logger.warning(f"[{ticker_symbol}] compute_net_profit_margin: No income statement data for {period_type} {fiscal_date}")
                return None

            data = income['statement_data']
            revenue = data.get('revenue')
            net_income = data.get('netIncome')

            if revenue is None or net_income is None or revenue == 0:
                self.logger.warning(f"[{ticker_symbol}] compute_net_profit_margin: Missing required data in income statement")
                return None

            margin = net_income / revenue
            self.operation_count += 1
            self.logger.info(f"[{ticker_symbol}] compute_net_profit_margin succeeded: margin={margin:.4f}, period_type={period_type}, fiscal_date={fiscal_date}")
            return {
                'value': margin,
                'interpretation': 'overall profitability after all expenses' if margin > 0.05 else 'low margin indicates poor overall profitability'
            }
        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"[{ticker_symbol}] compute_net_profit_margin failed: {str(e)}. Inputs: ticker={ticker_symbol}, period_type={period_type}, fiscal_date={fiscal_date}")
            return None

    def compute_return_on_assets(self, ticker_symbol: str, period_type: str, fiscal_date: str) -> Optional[Dict[str, Any]]:
        try:
            income = self.repo.get_income_statement(ticker_symbol, period_type, fiscal_date)
            balance = self.repo.get_balance_sheet(ticker_symbol, period_type, fiscal_date)
            if not income or not balance:
                self.logger.warning(f"[{ticker_symbol}] compute_return_on_assets: Missing income or balance sheet data for {period_type} {fiscal_date}")
                return None

            income_data = income['statement_data']
            balance_data = balance['statement_data']
            net_income = income_data.get('netIncome')
            total_assets = balance_data.get('totalAssets')

            if net_income is None or total_assets is None or total_assets == 0:
                self.logger.warning(f"[{ticker_symbol}] compute_return_on_assets: Missing required data in statements")
                return None

            roa = net_income / total_assets
            self.operation_count += 1
            self.logger.info(f"[{ticker_symbol}] compute_return_on_assets succeeded: roa={roa:.4f}, period_type={period_type}, fiscal_date={fiscal_date}")
            return {
                'value': roa,
                'interpretation': 'how efficiently assets generate profit' if roa > 0.05 else 'low ROA indicates inefficient asset use'
            }
        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"[{ticker_symbol}] compute_return_on_assets failed: {str(e)}. Inputs: ticker={ticker_symbol}, period_type={period_type}, fiscal_date={fiscal_date}")
            return None

    def compute_return_on_equity(self, ticker_symbol: str, period_type: str, fiscal_date: str) -> Optional[Dict[str, Any]]:
        try:
            income = self.repo.get_income_statement(ticker_symbol, period_type, fiscal_date)
            balance = self.repo.get_balance_sheet(ticker_symbol, period_type, fiscal_date)
            if not income or not balance:
                self.logger.warning(f"[{ticker_symbol}] compute_return_on_equity: Missing income or balance sheet data for {period_type} {fiscal_date}")
                return None

            income_data = income['statement_data']
            balance_data = balance['statement_data']
            net_income = income_data.get('netIncome')
            total_shareholders_equity = balance_data.get('totalShareholdersEquity')

            if net_income is None or total_shareholders_equity is None or total_shareholders_equity == 0:
                self.logger.warning(f"[{ticker_symbol}] compute_return_on_equity: Missing required data in statements")
                return None

            roe = net_income / total_shareholders_equity
            self.operation_count += 1
            self.logger.info(f"[{ticker_symbol}] compute_return_on_equity succeeded: roe={roe:.4f}, period_type={period_type}, fiscal_date={fiscal_date}")
            return {
                'value': roe,
                'interpretation': 'profitability from shareholders investment' if roe > 0.1 else 'low ROE suggests poor returns to shareholders'
            }
        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"[{ticker_symbol}] compute_return_on_equity failed: {str(e)}. Inputs: ticker={ticker_symbol}, period_type={period_type}, fiscal_date={fiscal_date}")
            return None

    # DuPont Analysis
    def compute_dupont_analysis(self, ticker_symbol: str, period_type: str, fiscal_date: str) -> Optional[Dict[str, Any]]:
        try:
            net_profit_margin = self.compute_net_profit_margin(ticker_symbol, period_type, fiscal_date)
            asset_turnover = self.compute_asset_turnover(ticker_symbol, period_type, fiscal_date)
            debt_to_equity = self.compute_debt_to_equity_ratio(ticker_symbol, period_type, fiscal_date)

            if not net_profit_margin or not asset_turnover or not debt_to_equity:
                self.logger.warning(f"[{ticker_symbol}] compute_dupont_analysis: Missing component ratios for {period_type} {fiscal_date}")
                return None

            equity_multiplier = 1 + debt_to_equity['value'] if debt_to_equity['value'] is not None else None

            if net_profit_margin['value'] is None or asset_turnover['value'] is None or equity_multiplier is None:
                self.logger.warning(f"[{ticker_symbol}] compute_dupont_analysis: Invalid values in component ratios")
                return None

            calculated_roe = net_profit_margin['value'] * asset_turnover['value'] * equity_multiplier
            phase3_roe = self.compute_return_on_equity(ticker_symbol, period_type, fiscal_date)

            match = None
            if calculated_roe is not None and phase3_roe and phase3_roe['value'] is not None:
                match = abs(calculated_roe - phase3_roe['value']) < 1e-6

            self.operation_count += 1
            self.logger.info(f"[{ticker_symbol}] compute_dupont_analysis succeeded: calculated_roe={calculated_roe:.4f}, match={match}, period_type={period_type}, fiscal_date={fiscal_date}")
            return {
                'calculated_roe': calculated_roe,
                'phase3_roe': phase3_roe['value'] if phase3_roe else None,
                'match': match,
                'decomposition': {
                    'net_profit_margin': net_profit_margin['value'],
                    'asset_turnover': asset_turnover['value'],
                    'equity_multiplier': equity_multiplier
                }
            }
        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"[{ticker_symbol}] compute_dupont_analysis failed: {str(e)}. Inputs: ticker={ticker_symbol}, period_type={period_type}, fiscal_date={fiscal_date}")
            return None

    # Efficiency Ratios
    def compute_asset_turnover(self, ticker_symbol: str, period_type: str, fiscal_date: str) -> Optional[Dict[str, Any]]:
        try:
            income = self.repo.get_income_statement(ticker_symbol, period_type, fiscal_date)
            balance = self.repo.get_balance_sheet(ticker_symbol, period_type, fiscal_date)
            if not income or not balance:
                self.logger.warning(f"[{ticker_symbol}] compute_asset_turnover: Missing income or balance sheet data for {period_type} {fiscal_date}")
                return None

            income_data = income['statement_data']
            balance_data = balance['statement_data']
            revenue = income_data.get('revenue')
            total_assets = balance_data.get('totalAssets')

            if revenue is None or total_assets is None or total_assets == 0:
                self.logger.warning(f"[{ticker_symbol}] compute_asset_turnover: Missing required data in statements")
                return None

            turnover = revenue / total_assets
            self.operation_count += 1
            self.logger.info(f"[{ticker_symbol}] compute_asset_turnover succeeded: turnover={turnover:.4f}, period_type={period_type}, fiscal_date={fiscal_date}")
            return {
                'value': turnover,
                'interpretation': 'how efficiently assets generate sales' if turnover > 1 else 'low turnover indicates underutilized assets'
            }
        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"[{ticker_symbol}] compute_asset_turnover failed: {str(e)}. Inputs: ticker={ticker_symbol}, period_type={period_type}, fiscal_date={fiscal_date}")
            return None

    # Leverage Ratios
    def compute_debt_ratio(self, ticker_symbol: str, period_type: str, fiscal_date: str) -> Optional[Dict[str, Any]]:
        try:
            balance = self.repo.get_balance_sheet(ticker_symbol, period_type, fiscal_date)
            if not balance:
                self.logger.warning(f"[{ticker_symbol}] compute_debt_ratio: No balance sheet data for {period_type} {fiscal_date}")
                return None

            data = balance['statement_data']
            total_liabilities = data.get('totalLiabilities')
            total_assets = data.get('totalAssets')

            if total_liabilities is None or total_assets is None or total_assets == 0:
                self.logger.warning(f"[{ticker_symbol}] compute_debt_ratio: Missing required data in balance sheet")
                return None

            ratio = total_liabilities / total_assets
            self.operation_count += 1
            self.logger.info(f"[{ticker_symbol}] compute_debt_ratio succeeded: ratio={ratio:.4f}, period_type={period_type}, fiscal_date={fiscal_date}")
            return {
                'value': ratio,
                'interpretation': 'proportion of assets financed by debt' if ratio < 0.5 else 'high debt ratio indicates financial risk'
            }
        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"[{ticker_symbol}] compute_debt_ratio failed: {str(e)}. Inputs: ticker={ticker_symbol}, period_type={period_type}, fiscal_date={fiscal_date}")
            return None

    def compute_debt_to_equity_ratio(self, ticker_symbol: str, period_type: str, fiscal_date: str) -> Optional[Dict[str, Any]]:
        try:
            balance = self.repo.get_balance_sheet(ticker_symbol, period_type, fiscal_date)
            if not balance:
                self.logger.warning(f"[{ticker_symbol}] compute_debt_to_equity_ratio: No balance sheet data for {period_type} {fiscal_date}")
                return None

            data = balance['statement_data']
            total_liabilities = data.get('totalLiabilities')
            total_shareholders_equity = data.get('totalShareholdersEquity')

            if total_liabilities is None or total_shareholders_equity is None or total_shareholders_equity == 0:
                self.logger.warning(f"[{ticker_symbol}] compute_debt_to_equity_ratio: Missing required data in balance sheet")
                return None

            ratio = total_liabilities / total_shareholders_equity
            self.operation_count += 1
            self.logger.info(f"[{ticker_symbol}] compute_debt_to_equity_ratio succeeded: ratio={ratio:.4f}, period_type={period_type}, fiscal_date={fiscal_date}")
            return {
                'value': ratio,
                'interpretation': 'debt relative to equity' if ratio < 1 else 'high leverage increases risk'
            }
        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"[{ticker_symbol}] compute_debt_to_equity_ratio failed: {str(e)}. Inputs: ticker={ticker_symbol}, period_type={period_type}, fiscal_date={fiscal_date}")
            return None

    # Valuation Ratios
    def compute_price_earnings_ratio(self, ticker_symbol: str, period_type: str, fiscal_date: str) -> Optional[Dict[str, Any]]:
        try:
            income = self.repo.get_income_statement(ticker_symbol, period_type, fiscal_date)
            balance = self.repo.get_balance_sheet(ticker_symbol, period_type, fiscal_date)
            price = self.repo.get_historical_price_at_date(ticker_symbol, fiscal_date)
            if not income or not balance or not price:
                self.logger.warning(f"[{ticker_symbol}] compute_price_earnings_ratio: Missing data for {period_type} {fiscal_date}")
                return None

            income_data = income['statement_data']
            balance_data = balance['statement_data']
            net_income = income_data.get('netIncome')
            shares_outstanding = balance_data.get('commonStockSharesOutstanding')
            current_price = price['close']

            if net_income is None or shares_outstanding is None or shares_outstanding == 0 or current_price is None:
                self.logger.warning(f"[{ticker_symbol}] compute_price_earnings_ratio: Missing required data in statements or price")
                return None

            eps = net_income / shares_outstanding
            if eps == 0:
                self.logger.warning(f"[{ticker_symbol}] compute_price_earnings_ratio: EPS is zero")
                return None

            pe = current_price / eps
            self.operation_count += 1
            self.logger.info(f"[{ticker_symbol}] compute_price_earnings_ratio succeeded: pe={pe:.4f}, period_type={period_type}, fiscal_date={fiscal_date}")
            return {
                'value': pe,
                'interpretation': 'valuation multiple' if pe > 15 else 'potentially undervalued'
            }
        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"[{ticker_symbol}] compute_price_earnings_ratio failed: {str(e)}. Inputs: ticker={ticker_symbol}, period_type={period_type}, fiscal_date={fiscal_date}")
            return None

    def compute_price_book_value_ratio(self, ticker_symbol: str, period_type: str, fiscal_date: str) -> Optional[Dict[str, Any]]:
        try:
            balance = self.repo.get_balance_sheet(ticker_symbol, period_type, fiscal_date)
            price = self.repo.get_historical_price_at_date(ticker_symbol, fiscal_date)
            if not balance or not price:
                self.logger.warning(f"[{ticker_symbol}] compute_price_book_value_ratio: Missing balance sheet or price data for {fiscal_date}")
                return None

            data = balance['statement_data']
            total_shareholders_equity = data.get('totalShareholdersEquity')
            shares_outstanding = data.get('commonStockSharesOutstanding')
            current_price = price['close']

            if total_shareholders_equity is None or shares_outstanding is None or shares_outstanding == 0 or current_price is None:
                self.logger.warning(f"[{ticker_symbol}] compute_price_book_value_ratio: Missing required data in statements or price")
                return None

            book_value_per_share = total_shareholders_equity / shares_outstanding
            if book_value_per_share == 0:
                self.logger.warning(f"[{ticker_symbol}] compute_price_book_value_ratio: Book value per share is zero")
                return None

            pb = current_price / book_value_per_share
            self.operation_count += 1
            self.logger.info(f"[{ticker_symbol}] compute_price_book_value_ratio succeeded: pb={pb:.4f}, period_type={period_type}, fiscal_date={fiscal_date}")
            return {
                'value': pb,
                'interpretation': 'price relative to book value' if pb > 1 else 'trading below book value'
            }
        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"[{ticker_symbol}] compute_price_book_value_ratio failed: {str(e)}. Inputs: ticker={ticker_symbol}, period_type={period_type}, fiscal_date={fiscal_date}")
            return None

    # Bankruptcy Scores
    def compute_altman_z_score(self, ticker_symbol: str, period_type: str, fiscal_date: str) -> Optional[Dict[str, Any]]:
        balance = self.repo.get_balance_sheet(ticker_symbol, period_type, fiscal_date)
        income = self.repo.get_income_statement(ticker_symbol, period_type, fiscal_date)
        price = self.repo.get_historical_price_at_date(ticker_symbol, fiscal_date)
        if not balance or not income or not price:
            return None

        balance_data = balance['statement_data']
        income_data = income['statement_data']
        current_price = price['close']

        total_current_assets = balance_data.get('totalCurrentAssets')
        total_current_liabilities = balance_data.get('totalCurrentLiabilities')
        retained_earnings = balance_data.get('retainedEarnings')
        total_assets = balance_data.get('totalAssets')
        total_liabilities = balance_data.get('totalLiabilities')
        shares_outstanding = balance_data.get('commonStockSharesOutstanding')

        operating_income = income_data.get('operatingIncome')
        revenue = income_data.get('revenue')

        if any(x is None for x in [total_current_assets, total_current_liabilities, retained_earnings, total_assets, total_liabilities, shares_outstanding, operating_income, revenue, current_price]):
            return None
        if total_assets == 0 or total_liabilities == 0:
            return None

        working_capital = total_current_assets - total_current_liabilities
        market_value_equity = current_price * shares_outstanding

        z = (1.2 * (working_capital / total_assets) +
             1.4 * (retained_earnings / total_assets) +
             3.3 * (operating_income / total_assets) +
             0.6 * (market_value_equity / total_liabilities) +
             0.999 * (revenue / total_assets))

        if z > 3:
            risk = 'safe'
        elif 1.8 <= z <= 3:
            risk = 'gray'
        else:
            risk = 'distress'

        return {
            'z_score': z,
            'risk': risk
        }

    # Validation
    def validate_ratios(self, ticker_symbol: str, period_type: str, fiscal_date: str) -> Dict[str, Any]:
        try:
            ratios = self.repo.get_ratios(ticker_symbol, period_type, fiscal_date)
            if not ratios:
                self.logger.warning(f"[{ticker_symbol}] validate_ratios: No ratios data for {period_type} {fiscal_date}")
                return {}

            reported_data = ratios['ratio_data']
            results = {}

            ratio_mappings = {
                'currentRatio': 'compute_current_ratio',
                'quickRatio': 'compute_quick_ratio',
                'cashRatio': 'compute_cash_ratio',
                'grossProfitMargin': 'compute_gross_profit_margin',
                'operatingProfitMargin': 'compute_operating_profit_margin',
                'netProfitMargin': 'compute_net_profit_margin',
                'returnOnAssets': 'compute_return_on_assets',
                'returnOnEquity': 'compute_return_on_equity',
                'debtRatio': 'compute_debt_ratio',
                'debtEquityRatio': 'compute_debt_to_equity_ratio',
                'priceEarningsRatio': 'compute_price_earnings_ratio',
                'priceBookValueRatio': 'compute_price_book_value_ratio',
                'assetTurnover': 'compute_asset_turnover'
            }

            for ratio_name, reported_val in reported_data.items():
                method_name = ratio_mappings.get(ratio_name)
                if method_name:
                    compute_method = getattr(self, method_name)
                    computed = compute_method(ticker_symbol, period_type, fiscal_date)
                    computed_val = computed['value'] if computed else None

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

            self.operation_count += 1
            self.logger.info(f"[{ticker_symbol}] validate_ratios succeeded: validated {len(results)} ratios, period_type={period_type}, fiscal_date={fiscal_date}")
            return results
        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"[{ticker_symbol}] validate_ratios failed: {str(e)}. Inputs: ticker={ticker_symbol}, period_type={period_type}, fiscal_date={fiscal_date}")
            return {}

    # Bankruptcy Scores
    def compute_beneish_m_score(self, ticker_symbol: str, period_type: str, fiscal_date: str) -> Optional[Dict[str, Any]]:
        try:
            # Compute previous fiscal_date (assuming annual)
            try:
                current_dt = datetime.fromisoformat(fiscal_date)
                previous_dt = current_dt.replace(year=current_dt.year - 1)
                previous_fiscal_date = previous_dt.isoformat()[:10]
            except ValueError:
                self.logger.warning(f"[{ticker_symbol}] compute_beneish_m_score: Invalid fiscal_date format")
                return None

            # Get current period data
            income_curr = self.repo.get_income_statement(ticker_symbol, period_type, fiscal_date)
            balance_curr = self.repo.get_balance_sheet(ticker_symbol, period_type, fiscal_date)
            cash_curr = self.repo.get_cash_flow(ticker_symbol, period_type, fiscal_date)

            income_prev = self.repo.get_income_statement(ticker_symbol, period_type, previous_fiscal_date)
            balance_prev = self.repo.get_balance_sheet(ticker_symbol, period_type, previous_fiscal_date)
            cash_prev = self.repo.get_cash_flow(ticker_symbol, period_type, previous_fiscal_date)

            if not all([income_curr, balance_curr, cash_curr, income_prev, balance_prev, cash_prev]):
                return None

            inc_curr = income_curr['statement_data']
            bal_curr = balance_curr['statement_data']
            cas_curr = cash_curr['statement_data']

            inc_prev = income_prev['statement_data']
            bal_prev = balance_prev['statement_data']
            cas_prev = cash_prev['statement_data']

            # Extract variables
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

            # Compute ratios
            dsri = (receivables_t / sales_t) / (receivables_tm1 / sales_tm1)
            gm_t = (sales_t - cogs_t) / sales_t
            gm_tm1 = (sales_tm1 - cogs_tm1) / sales_tm1
            if gm_t == 0:
                return None
            gmi = gm_tm1 / gm_t
            aqi_t = 1 - (curr_assets_t + ppe_t) / total_assets_t
            aqi_tm1 = 1 - (curr_assets_tm1 + ppe_tm1) / total_assets_tm1
            if aqi_tm1 == 0:
                return None
            aqi = aqi_t / aqi_tm1
            sgi = sales_t / sales_tm1
            depi_t = dep_t / (ppe_t + dep_t)
            depi_tm1 = dep_tm1 / (ppe_tm1 + dep_tm1)
            if depi_t == 0:
                return None
            depi = depi_tm1 / depi_t
            sgai = (sga_t / sales_t) / (sga_tm1 / sales_tm1)
            tata = (net_income_t - cfo_t) / total_assets_t
            lvgi_t = (curr_liab_t + total_debt_t) / total_assets_t
            lvgi_tm1 = (curr_liab_tm1 + total_debt_tm1) / total_assets_tm1
            lvgi = lvgi_t / lvgi_tm1

            # Compute M-Score
            m_score = (-4.84 + 0.92 * dsri + 0.528 * gmi + 0.404 * aqi + 0.892 * sgi +
                       0.115 * depi - 0.172 * sgai + 4.679 * tata - 0.327 * lvgi)

            risk = 'high' if m_score > -2.22 else 'low'

            return {'m_score': m_score, 'risk': risk}
        except Exception as e:
            self.logger.error(f"[{ticker_symbol}] compute_beneish_m_score failed: {str(e)}")
            return None

    def compute_ohlson_o_score(self, ticker_symbol: str, period_type: str, fiscal_date: str) -> Optional[Dict[str, Any]]:
        # Compute previous dates
        try:
            current_dt = datetime.fromisoformat(fiscal_date)
            previous_dt = current_dt.replace(year=current_dt.year - 1)
            previous_fiscal_date = previous_dt.isoformat()[:10]
            tm2_dt = current_dt.replace(year=current_dt.year - 2)
            tm2_fiscal_date = tm2_dt.isoformat()[:10]
        except ValueError:
            return None

        # Get data
        balance_t = self.repo.get_balance_sheet(ticker_symbol, period_type, fiscal_date)
        income_t = self.repo.get_income_statement(ticker_symbol, period_type, fiscal_date)
        cash_t = self.repo.get_cash_flow(ticker_symbol, period_type, fiscal_date)
        income_tm1 = self.repo.get_income_statement(ticker_symbol, period_type, previous_fiscal_date)
        income_tm2 = self.repo.get_income_statement(ticker_symbol, period_type, tm2_fiscal_date)

        if not all([balance_t, income_t, cash_t, income_tm1, income_tm2]):
            return None

        bal = balance_t['statement_data']
        inc_t = income_t['statement_data']
        cas_t = cash_t['statement_data']
        inc_tm1 = income_tm1['statement_data']
        inc_tm2 = income_tm2['statement_data']

        # Extract
        TA = bal.get('totalAssets')
        TL = bal.get('totalLiabilities')
        WC = bal.get('totalCurrentAssets') - bal.get('totalCurrentLiabilities') if bal.get('totalCurrentAssets') and bal.get('totalCurrentLiabilities') else None
        CA = bal.get('totalCurrentAssets')
        CL = bal.get('totalCurrentLiabilities')
        EBIT = inc_t.get('operatingIncome')
        NI_t = inc_t.get('netIncome')
        NI_tm1 = inc_tm1.get('netIncome')
        NI_tm2 = inc_tm2.get('netIncome')
        FFO = cas_t.get('operatingCashFlow')

        if (TA is None or TL is None or WC is None or CA is None or CL is None or EBIT is None or
            NI_t is None or NI_tm1 is None or NI_tm2 is None or FFO is None or TA == 0 or CL == 0):
            return None

        # Ratios
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

        # O-Score
        o_score = (-1.32 - 0.407 * log_TA + 6.03 * TL_TA - 1.43 * WC_TA + 0.076 * CL_CA -
                   1.72 * EBIT_TA - 2.37 * NI_tm1_NI_t - 1.83 * FFO_TA + 0.285 * NI_t_NI_tm1 -
                   0.521 * NI_tm1_NI_tm2)

        risk = 'high' if o_score > 0.5 else 'low'

        return {'o_score': o_score, 'risk': risk}

    # This covers the main migrated methods. Further methods can be added as needed.