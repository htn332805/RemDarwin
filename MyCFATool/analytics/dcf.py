import sqlite3
import json
import numpy as np
import pandas as pd
from scipy.optimize import newton
from datetime import datetime

class DCFValuation:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)

    def load_financial_data(self, ticker_symbol, period_type, fiscal_date):
        """
        Load financial data from income_statement, balance_sheet, cash_flow for DCF calculations.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            period_type (str): 'annual' or 'quarterly'.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format.

        Returns:
            dict: {'income': dict, 'balance': dict, 'cash_flow': dict} or None if not found.
        """
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        data = {}
        tables = ['income_statement', 'balance_sheet', 'cash_flow']
        keys = ['income', 'balance', 'cash_flow']
        for table, key in zip(tables, keys):
            stmt = self.conn.execute(f"SELECT statement_data FROM {table} WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?", (ticker_id, period_type, fiscal_date)).fetchone()
            if stmt:
                data[key] = json.loads(stmt[0])
            else:
                data[key] = {}
        return data if any(data.values()) else None

    def compute_free_cash_flow(self, income_data, cash_flow_data):
        """
        Compute Free Cash Flow (FCF) = CFO - Capex.

        Args:
            income_data (dict): Income statement data.
            cash_flow_data (dict): Cash flow data.

        Returns:
            float or None: FCF value.
        """
        cfo = cash_flow_data.get('operatingCashFlow', 0) or 0
        capex = cash_flow_data.get('capitalExpenditures', 0) or 0
        if capex > 0:
            capex = -capex  # Capex is usually positive in statements but outflow
        fcf = cfo + capex  # Capex is negative, so add
        return fcf

    def project_free_cash_flows(self, ticker_symbol, period_type, fiscal_date, projection_years=5, growth_rate=0.03):
        """
        Project FCF for future years using historical growth.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            period_type (str): 'annual'.
            fiscal_date (str): Latest fiscal date.
            projection_years (int): Number of years to project.
            growth_rate (float): Assumed long-term growth rate.

        Returns:
            list: Projected FCFs [year1, year2, ..., yearN].
        """
        # Load historical FCF
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return []
        ticker_id = ticker_id[0]

        # Get last 3 years FCF
        rows = self.conn.execute("""
            SELECT fiscal_date, statement_data FROM cash_flow
            WHERE ticker_id = ? AND period_type = ?
            ORDER BY fiscal_date DESC LIMIT 3
        """, (ticker_id, period_type)).fetchall()

        fcf_history = []
        for row in rows:
            cf_data = json.loads(row[1])
            inc_data = self.conn.execute("SELECT statement_data FROM income_statement WHERE ticker_id = ? AND period_type = ? AND fiscal_date = ?", (ticker_id, period_type, row[0])).fetchone()
            if inc_data:
                inc = json.loads(inc_data[0])
                fcf = self.compute_free_cash_flow(inc, cf_data)
                if fcf:
                    fcf_history.append(fcf)

        if not fcf_history:
            return []

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
        latest_data = self.load_financial_data(ticker_symbol, period_type, fiscal_date)
        if not latest_data:
            return []
        latest_fcf = self.compute_free_cash_flow(latest_data['income'], latest_data['cash_flow'])
        if not latest_fcf:
            return []

        projections = []
        current_fcf = latest_fcf
        for year in range(1, projection_years + 1):
            current_fcf *= (1 + avg_growth)
            projections.append(current_fcf)

        return projections

    def compute_wacc(self, ticker_symbol, period_type, fiscal_date, risk_free_rate=0.05, market_risk_premium=0.06, beta=1.0):
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
        data = self.load_financial_data(ticker_symbol, period_type, fiscal_date)
        if not data or not data['balance']:
            return None

        balance = data['balance']
        total_debt = balance.get('totalDebt', 0) or 0
        total_equity = balance.get('totalStockholdersEquity', 0) or 0
        total_capital = total_debt + total_equity
        if total_capital == 0:
            return None

        # Cost of equity = risk_free + beta * market_premium
        cost_equity = risk_free_rate + beta * market_risk_premium

        # Cost of debt: assume interest expense / total debt, or default
        interest_expense = data['income'].get('interestExpense', 0) or 0
        cost_debt = interest_expense / total_debt if total_debt > 0 else 0.04  # Default 4%

        # Tax rate
        pre_tax_income = data['income'].get('incomeBeforeTax', 0) or 0
        tax_expense = data['income'].get('incomeTaxExpense', 0) or 0
        tax_rate = tax_expense / pre_tax_income if pre_tax_income > 0 else 0.21  # Default 21%

        # WACC = (E/V)*Re + (D/V)*Rd*(1-T)
        wacc = (total_equity / total_capital) * cost_equity + (total_debt / total_capital) * cost_debt * (1 - tax_rate)
        return wacc

    def compute_terminal_value(self, terminal_fcf, growth_rate=0.03, wacc=0.1, method='perpetuity'):
        """
        Compute Terminal Value.

        Args:
            terminal_fcf (float): FCF at end of projection.
            growth_rate (float): Perpetual growth rate.
            wacc (float): Discount rate.
            method (str): 'perpetuity' or 'multiple' (placeholder for exit multiple).

        Returns:
            float: Terminal value.
        """
        if method == 'perpetuity':
            if wacc <= growth_rate:
                return None  # Invalid
            tv = terminal_fcf * (1 + growth_rate) / (wacc - growth_rate)
        else:
            # Placeholder for exit multiple, e.g., 10x FCF
            tv = terminal_fcf * 10
        return tv

    def compute_intrinsic_value(self, projected_fcfs, terminal_value, wacc):
        """
        Compute intrinsic value by discounting FCFs and TV.

        Args:
            projected_fcfs (list): List of projected FCFs.
            terminal_value (float): Terminal value.
            wacc (float): Discount rate.

        Returns:
            float: Intrinsic value (per share if adjusted).
        """
        pv_fcfs = 0
        for i, fcf in enumerate(projected_fcfs, 1):
            pv_fcfs += fcf / ((1 + wacc) ** i)

        pv_tv = terminal_value / ((1 + wacc) ** len(projected_fcfs))
        enterprise_value = pv_fcfs + pv_tv

        # To get equity value, subtract net debt, but for simplicity, assume EV ≈ Equity Value
        # In real DCF, EV = Equity Value + Net Debt
        return enterprise_value

    def compute_dcf_valuation(self, ticker_symbol, period_type, fiscal_date, projection_years=5, growth_rate=0.03, risk_free_rate=0.05, market_risk_premium=0.06, beta=1.0):
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
            dict: {'intrinsic_value': float, 'wacc': float, 'projected_fcfs': list, 'terminal_value': float, 'signal': str, 'interpretation': str} or None.
        """
        # Get WACC
        wacc = self.compute_wacc(ticker_symbol, period_type, fiscal_date, risk_free_rate, market_risk_premium, beta)
        if not wacc:
            return None

        # Project FCFs
        projected_fcfs = self.project_free_cash_flows(ticker_symbol, period_type, fiscal_date, projection_years, growth_rate)
        if not projected_fcfs:
            return None

        # Terminal value
        terminal_fcf = projected_fcfs[-1]
        terminal_value = self.compute_terminal_value(terminal_fcf, growth_rate, wacc)
        if not terminal_value:
            return None

        # Intrinsic value
        intrinsic_value = self.compute_intrinsic_value(projected_fcfs, terminal_value, wacc)

        # Get share count for per share value
        data = self.load_financial_data(ticker_symbol, period_type, fiscal_date)
        shares = data['balance'].get('commonStockSharesOutstanding', 0) or 0
        if shares:
            per_share_value = intrinsic_value / shares
        else:
            per_share_value = intrinsic_value  # Assume EV

        # Get current price for comparison
        latest_price = self.conn.execute("SELECT close FROM historical_price WHERE ticker_id = (SELECT ticker_id FROM ticker WHERE symbol = ?) ORDER BY trade_date DESC LIMIT 1", (ticker_symbol,)).fetchone()
        current_price = latest_price[0] if latest_price else None

        if current_price and per_share_value:
            if per_share_value > current_price * 1.1:
                signal = 'undervalued'
            elif per_share_value < current_price * 0.9:
                signal = 'overvalued'
            else:
                signal = 'fairly valued'
        else:
            signal = 'neutral'

        interpretation = f"DCF suggests intrinsic value of ${per_share_value:.2f} per share. Market price: ${current_price:.2f} if available."

        return {
            'intrinsic_value': per_share_value,
            'wacc': wacc,
            'projected_fcfs': projected_fcfs,
            'terminal_value': terminal_value,
            'signal': signal,
            'interpretation': interpretation
        }

    def perform_sensitivity_analysis(self, base_valuation, growth_rates=None, discount_rates=None):
        """
        Perform sensitivity analysis on growth rates and discount rates.

        Args:
            base_valuation (dict): Base DCF result.
            growth_rates (list): List of growth rates to test.
            discount_rates (list): List of discount rates to test.

        Returns:
            dict: Sensitivity table.
        """
        if growth_rates is None:
            growth_rates = [0.01, 0.02, 0.03, 0.04, 0.05]
        if discount_rates is None:
            discount_rates = [0.08, 0.10, 0.12, 0.14, 0.16]

        sensitivity = {}
        for gr in growth_rates:
            for dr in discount_rates:
                # Recalculate assuming same projections but different params
                # This is simplified; in reality, projections depend on growth
                projected_fcfs = [fcf * ((1 + gr) / (1 + 0.03))**i for i, fcf in enumerate(base_valuation['projected_fcfs'], 1)]
                terminal_value = self.compute_terminal_value(projected_fcfs[-1], gr, dr)
                if terminal_value:
                    intrinsic_value = self.compute_intrinsic_value(projected_fcfs, terminal_value, dr)
                    sensitivity[(gr, dr)] = intrinsic_value
                else:
                    sensitivity[(gr, dr)] = None

        return sensitivity