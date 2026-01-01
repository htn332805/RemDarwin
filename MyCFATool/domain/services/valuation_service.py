import json
import numpy as np
import pandas as pd
from scipy.optimize import newton
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging

from ..repositories.financial_data_repository import FinancialDataRepository


class ValuationService:
    """Service for valuation computations using FinancialDataRepository."""

    def __init__(self):
        self.repo = FinancialDataRepository()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.operation_count = 0
        self.failure_count = 0

    def compute_free_cash_flow(self, ticker_symbol: str, period_type: str, fiscal_date: str) -> Optional[float]:
        """
        Compute Free Cash Flow (FCF) = CFO - Capex.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            period_type (str): 'annual' or 'quarterly'.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format.

        Returns:
            float or None: FCF value.
        """
        try:
            cash_flow = self.repo.get_cash_flow(ticker_symbol, period_type, fiscal_date)
            if not cash_flow:
                self.logger.warning(f"[{ticker_symbol}] compute_free_cash_flow: No cash flow data for {period_type} {fiscal_date}")
                return None

            data = cash_flow['statement_data']
            cfo = data.get('operatingCashFlow', 0) or 0
            capex = data.get('capitalExpenditures', 0) or 0
            if capex > 0:
                capex = -capex  # Capex is usually positive in statements but outflow
            fcf = cfo + capex  # Capex is negative, so add
            self.operation_count += 1
            self.logger.info(f"[{ticker_symbol}] compute_free_cash_flow succeeded: fcf={fcf:.2f}, period_type={period_type}, fiscal_date={fiscal_date}")
            return fcf
        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"[{ticker_symbol}] compute_free_cash_flow failed: {str(e)}. Inputs: ticker={ticker_symbol}, period_type={period_type}, fiscal_date={fiscal_date}")
            return None

    def project_free_cash_flows(self, ticker_symbol: str, period_type: str, fiscal_date: str, projection_years: int = 5, growth_rate: float = 0.03) -> Optional[List[float]]:
        """
        Project FCF for future years using historical growth.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            period_type (str): 'annual'.
            fiscal_date (str): Latest fiscal date.
            projection_years (int): Number of years to project.
            growth_rate (float): Assumed long-term growth rate.

        Returns:
            list or None: Projected FCFs [year1, year2, ..., yearN].
        """
        # Get historical FCF from last 3 years
        # Since repo doesn't have direct historical statements, we need to get multiple dates
        # Assume annual, get previous years
        try:
            current_dt = datetime.fromisoformat(fiscal_date)
            fcf_history = []
            for i in range(4):  # current + 3 previous
                dt = current_dt.replace(year=current_dt.year - i)
                f_date = dt.isoformat()[:10]
                fcf = self.compute_free_cash_flow(ticker_symbol, period_type, f_date)
                if fcf is not None:
                    fcf_history.append(fcf)
        except ValueError:
            return None

        if not fcf_history:
            return None

        # Calculate average growth
        if len(fcf_history) > 1:
            growths = []
            for i in range(1, len(fcf_history)):
                if fcf_history[i-1] != 0:
                    growths.append((fcf_history[i-1] - fcf_history[i]) / abs(fcf_history[i]))
            avg_growth = np.mean(growths) if growths else growth_rate
        else:
            avg_growth = growth_rate

        # Start from latest FCF
        latest_fcf = fcf_history[0] if fcf_history else None
        if latest_fcf is None:
            return None

        projections = []
        current_fcf = latest_fcf
        for year in range(1, projection_years + 1):
            current_fcf *= (1 + avg_growth)
            projections.append(current_fcf)

        return projections

    def compute_wacc(self, ticker_symbol: str, period_type: str, fiscal_date: str, risk_free_rate: float = 0.05, market_risk_premium: float = 0.06, beta: float = 1.0) -> Optional[float]:
        """
        Compute Weighted Average Cost of Capital (WACC).

        Args:
            ticker_symbol (str): The stock ticker symbol.
            period_type (str): 'annual'.
            fiscal_date (str): Fiscal date.
            risk_free_rate (float): Risk-free rate.
            market_risk_premium (float): Market risk premium.
            beta (float): Beta of the stock.

        Returns:
            float or None: WACC.
        """
        balance = self.repo.get_balance_sheet(ticker_symbol, period_type, fiscal_date)
        income = self.repo.get_income_statement(ticker_symbol, period_type, fiscal_date)
        if not balance or not income:
            return None

        bal_data = balance['statement_data']
        inc_data = income['statement_data']
        total_debt = bal_data.get('totalDebt', 0) or 0
        total_equity = bal_data.get('totalStockholdersEquity', 0) or 0
        total_capital = total_debt + total_equity
        if total_capital == 0:
            return None

        # Cost of equity = risk_free + beta * market_premium
        cost_equity = risk_free_rate + beta * market_risk_premium

        # Cost of debt: assume interest expense / total debt, or default
        interest_expense = inc_data.get('interestExpense', 0) or 0
        cost_debt = interest_expense / total_debt if total_debt > 0 else 0.04  # Default 4%

        # Tax rate
        pre_tax_income = inc_data.get('incomeBeforeTax', 0) or 0
        tax_expense = inc_data.get('incomeTaxExpense', 0) or 0
        tax_rate = tax_expense / pre_tax_income if pre_tax_income > 0 else 0.21  # Default 21%

        # WACC = (E/V)*Re + (D/V)*Rd*(1-T)
        wacc = (total_equity / total_capital) * cost_equity + (total_debt / total_capital) * cost_debt * (1 - tax_rate)
        return wacc

    def compute_terminal_value(self, terminal_fcf: float, growth_rate: float = 0.03, wacc: float = 0.1, method: str = 'perpetuity') -> Optional[float]:
        """
        Compute Terminal Value.

        Args:
            terminal_fcf (float): FCF at end of projection.
            growth_rate (float): Perpetual growth rate.
            wacc (float): Discount rate.
            method (str): 'perpetuity' or 'multiple' (placeholder for exit multiple).

        Returns:
            float or None: Terminal value.
        """
        if method == 'perpetuity':
            if wacc <= growth_rate:
                return None  # Invalid
            tv = terminal_fcf * (1 + growth_rate) / (wacc - growth_rate)
        else:
            # Placeholder for exit multiple, e.g., 10x FCF
            tv = terminal_fcf * 10
        return tv

    def compute_intrinsic_value(self, projected_fcfs: List[float], terminal_value: float, wacc: float) -> float:
        """
        Compute intrinsic value by discounting FCFs and TV.

        Args:
            projected_fcfs (list): List of projected FCFs.
            terminal_value (float): Terminal value.
            wacc (float): Discount rate.

        Returns:
            float: Intrinsic value (enterprise value).
        """
        pv_fcfs = 0
        for i, fcf in enumerate(projected_fcfs, 1):
            pv_fcfs += fcf / ((1 + wacc) ** i)

        pv_tv = terminal_value / ((1 + wacc) ** len(projected_fcfs))
        enterprise_value = pv_fcfs + pv_tv
        return enterprise_value

    def compute_dcf_valuation(self, ticker_symbol: str, period_type: str, fiscal_date: str, projection_years: int = 5, growth_rate: float = 0.03, risk_free_rate: float = 0.05, market_risk_premium: float = 0.06, beta: float = 1.0) -> Optional[Dict[str, Any]]:
        """
        Full DCF valuation.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            period_type (str): 'annual'.
            fiscal_date (str): Fiscal date.
            projection_years (int): Years to project.
            growth_rate (float): Long-term growth.
            risk_free_rate (float): Risk-free rate.
            market_risk_premium (float): Market premium.
            beta (float): Beta.

        Returns:
            dict or None: {'intrinsic_value_per_share': float, 'wacc': float, 'projected_fcfs': list, 'terminal_value': float, 'signal': str, 'interpretation': str}.
        """
        try:
            # Get WACC
            wacc = self.compute_wacc(ticker_symbol, period_type, fiscal_date, risk_free_rate, market_risk_premium, beta)
            if not wacc:
                self.logger.warning(f"[{ticker_symbol}] compute_dcf_valuation: Unable to compute WACC")
                return None

            # Project FCFs
            projected_fcfs = self.project_free_cash_flows(ticker_symbol, period_type, fiscal_date, projection_years, growth_rate)
            if not projected_fcfs:
                self.logger.warning(f"[{ticker_symbol}] compute_dcf_valuation: Unable to project FCFs")
                return None

            # Terminal value
            terminal_fcf = projected_fcfs[-1]
            terminal_value = self.compute_terminal_value(terminal_fcf, growth_rate, wacc)
            if not terminal_value:
                self.logger.warning(f"[{ticker_symbol}] compute_dcf_valuation: Unable to compute terminal value")
                return None

            # Intrinsic value
            enterprise_value = self.compute_intrinsic_value(projected_fcfs, terminal_value, wacc)

            # Get share count for per share value
            balance = self.repo.get_balance_sheet(ticker_symbol, period_type, fiscal_date)
            if balance:
                shares = balance['statement_data'].get('commonStockSharesOutstanding', 0) or 0
            else:
                shares = 0
            if shares:
                per_share_value = enterprise_value / shares
            else:
                per_share_value = enterprise_value  # Assume EV

            # Get current price for comparison
            latest_prices = self.repo.get_historical_prices_ordered(ticker_symbol, order='desc', limit=1)
            current_price = latest_prices[0]['close'] if latest_prices else None

            if current_price and per_share_value:
                if per_share_value > current_price * 1.1:
                    signal = 'undervalued'
                elif per_share_value < current_price * 0.9:
                    signal = 'overvalued'
                else:
                    signal = 'fairly valued'
            else:
                signal = 'neutral'

            interpretation = f"DCF suggests intrinsic value of ${per_share_value:.2f} per share. Market price: ${current_price:.2f} if available. Signal: {signal}."

            self.operation_count += 1
            self.logger.info(f"[{ticker_symbol}] compute_dcf_valuation succeeded: intrinsic_value_per_share={per_share_value:.2f}, signal={signal}, period_type={period_type}, fiscal_date={fiscal_date}")
            return {
                'intrinsic_value_per_share': per_share_value,
                'enterprise_value': enterprise_value,
                'wacc': wacc,
                'projected_fcfs': projected_fcfs,
                'terminal_value': terminal_value,
                'signal': signal,
                'interpretation': interpretation
            }
        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"[{ticker_symbol}] compute_dcf_valuation failed: {str(e)}. Inputs: ticker={ticker_symbol}, period_type={period_type}, fiscal_date={fiscal_date}")
            return None

    def perform_sensitivity_analysis(self, ticker_symbol: str, period_type: str, fiscal_date: str, base_valuation: Dict[str, Any], growth_rates: List[float] = None, discount_rates: List[float] = None) -> Optional[Dict[str, Any]]:
        """
        Perform sensitivity analysis on growth rates and discount rates.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            period_type (str): Period type.
            fiscal_date (str): Fiscal date.
            base_valuation (dict): Base DCF result.
            growth_rates (list): List of growth rates to test.
            discount_rates (list): List of discount rates to test.

        Returns:
            dict or None: Sensitivity table as dict of (growth, discount): value.
        """
        if growth_rates is None:
            growth_rates = [0.01, 0.02, 0.03, 0.04, 0.05]
        if discount_rates is None:
            discount_rates = [0.08, 0.10, 0.12, 0.14, 0.16]

        sensitivity = {}
        base_fcfs = base_valuation.get('projected_fcfs', [])
        base_growth = 0.03  # Assume base growth
        for gr in growth_rates:
            for dr in discount_rates:
                # Recalculate assuming same projections but different params
                # Simplified: adjust FCFs with new growth
                adjusted_fcfs = [fcf * ((1 + gr) / (1 + base_growth))**i for i, fcf in enumerate(base_fcfs, 1)]
                terminal_value = self.compute_terminal_value(adjusted_fcfs[-1], gr, dr)
                if terminal_value:
                    intrinsic_value = self.compute_intrinsic_value(adjusted_fcfs, terminal_value, dr)
                    # Get per share
                    balance = self.repo.get_balance_sheet(ticker_symbol, period_type, fiscal_date)
                    shares = balance['statement_data'].get('commonStockSharesOutstanding', 0) if balance else 0
                    if shares:
                        val = intrinsic_value / shares
                    else:
                        val = intrinsic_value
                    sensitivity[(gr, dr)] = val
                else:
                    sensitivity[(gr, dr)] = None

        return sensitivity