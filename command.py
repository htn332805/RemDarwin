#!/usr/bin/env python3
"""
Fundamental Ratios Calculator CLI Scripts

This script provides a command-line interface to compute fundamental financial ratios.
Usage: python3 command.py -m {ratio_name} {input1} {input2} ...
"""

import argparse
import sys
import math

class Ratios:
    """
    A class to compute fundamental financial ratios.
    """

    def __init__(self):
        self.accounts_receivable = None
        self.total_revenue = None
        self.inventory = None
        self.cost_of_goods_sold = None
        self.account_payables = None
        self.net_income = None
        self.shareholders_equity = None
        self.number_of_shares_outstanding = None
        self.free_cash_flow = None
        self.market_price_per_share = None
        self.operating_cash_flow = None
        self.capital_expenditures = None
        self.total_assets = None
        self.total_current_liabilities = None
        self.total_current_assets = None
        self.current_assets = self.total_current_assets 
        self.goodwill_and_intangible_assets = None
        self.cash_and_cash_equivalents = None
        self.total_liabilities = None
        self.depreciation_and_amortization = None
        self.total_revenue = None
        self.research_and_development_expenses = None
        self.general_and_administrative_expenses = None
        self.earnings_per_share = None
        self.price_per_share = None
        self.price_earnings_ratio = None
        self.growth_rate = None
        self.enterprise_value = None
        self.dividends_per_share = None
        self.earnings_per_share = None
        self.operating_income = None
        self.income_before_tax = None
        self.ebitda = None
        self.market_cap = None
        self.total_debt = None
        self.long_term_debt = None
        self.interest_expense = None
        self.income_tax_expense = None
        self.property_plant_equipment_net = None
        self.gross_profit = None

        
        
    def compute_current_ratio_metric(self, current_assets, current_liabilities):
        """
        Compute Current Ratio: current_assets / current_liabilities
        """
        self.total_current_assets = current_assets
        self.total_current_liabilities = current_liabilities
        #python3 command.py -m current_ratio 34986000000 35064000000
        #return 0.997767535

        if self.total_current_assets is None or self.total_current_liabilities is None:
            raise ValueError("Missing required input: current_assets or current_liabilities")
        if not isinstance(self.total_current_assets, (int, float)) or not isinstance(self.total_current_liabilities, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.total_current_liabilities == 0:
            raise ValueError("Division by zero: current_liabilities cannot be zero")
        return self.total_current_assets / self.total_current_liabilities

    def compute_working_capital_metric(self, current_assets, current_liabilities):
        """
        Compute Working Capital: current_assets - current_liabilities
        """
        self.total_current_assets = current_assets
        self.total_current_liabilities = current_liabilities
        if self.total_current_assets is None or self.total_current_liabilities is None:
            raise ValueError("Missing required input: current_assets or current_liabilities")
        if not isinstance(self.total_current_assets, (int, float)) or not isinstance(self.total_current_liabilities, (int, float)):
            raise ValueError("Inputs must be numeric")
        return self.total_current_assets - self.total_current_liabilities

    def compute_quick_ratio_metric(self, current_assets, inventory, current_liabilities):
        """
        Compute Quick Ratio: (current_assets - inventory) / current_liabilities

        """
        self.total_current_assets = current_assets
        self.inventory = inventory
        self.total_current_liabilities = current_liabilities
        #python3 command.py -m quick_ratio 34986000000 3164000000 35064000000
        #return 0.9075404973762263
        if self.total_current_assets is None or self.inventory is None or self.total_current_liabilities is None:
            raise ValueError("Missing required input: current_assets, inventory, or current_liabilities")
        if not isinstance(self.total_current_assets, (int, float)) or not isinstance(self.inventory, (int, float)) or not isinstance(self.total_current_liabilities, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.total_current_liabilities == 0:
            raise ValueError("Division by zero: current_liabilities cannot be zero")
        return (self.total_current_assets - self.inventory) / self.total_current_liabilities    

    def compute_cash_ratio_metric(self, cash_and_cash_equivalents, current_liabilities):
        """
        Compute Cash Ratio: cash_and_cash_equivalents / current_liabilities
        """
        self.cash_and_cash_equivalents = cash_and_cash_equivalents
        self.total_current_liabilities = current_liabilities
        #python3 command.py -m cash_ratio 9473000000 35064000000
    
        if self.cash_and_cash_equivalents is None or self.total_current_liabilities is None:
            raise ValueError("Missing required input: cash_and_cash_equivalents or current_liabilities")
        if not isinstance(self.cash_and_cash_equivalents, (int, float)) or not isinstance(self.total_current_liabilities, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.total_current_liabilities == 0:
            raise ValueError("Division by zero: current_liabilities cannot be zero")
        return self.cash_and_cash_equivalents / self.total_current_liabilities  

    def compute_gross_profit_margin_metric(self, gross_profit, total_revenue):
        """
        Compute Gross Profit Margin: (gross_profit / total_revenue) * 100
        """
        self.gross_profit = gross_profit
        self.total_revenue = total_revenue
        #python3 command.py -m gross_profit_margin 36790000000 56654000000
        #result 64.93804497475907 in %
        if self.gross_profit is None or self.total_revenue is None:
            raise ValueError("Missing required input: gross_profit or total_revenue")
        if not isinstance(self.gross_profit, (int, float)) or not isinstance(self.total_revenue, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.total_revenue == 0:
            raise ValueError("Division by zero: total_revenue cannot be zero")
        return (self.gross_profit / self.total_revenue) * 100

    def compute_operating_profit_margin_metric(self, operating_income, total_revenue):
        """
        Compute Operating Profit Margin: (operating_income / total_revenue) * 100
        """
        self.operating_income = operating_income
        self.total_revenue = total_revenue
        #python3 command.py -m operating_profit_margin 11760000000 56654000000
        #result 20.76220920662668 in %
        if self.operating_income is None or self.total_revenue is None:
            raise ValueError("Missing required input: operating_income or total_revenue")
        if not isinstance(self.operating_income, (int, float)) or not isinstance(self.total_revenue, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.total_revenue == 0:
            raise ValueError("Division by zero: total_revenue cannot be zero")
        return (self.operating_income / self.total_revenue) * 100

    def compute_net_profit_margin_metric(self, net_income, total_revenue):
        """
        Compute Net Profit Margin: (net_income / total_revenue) * 100
        """
        self.net_income = net_income
        self.total_revenue = total_revenue
        #python3 command.py -m net_profit_margin 10180000000 56654000000
        #result 17.967263763263763 in %
        if self.net_income is None or self.total_revenue is None:
            raise ValueError("Missing required input: net_income or total_revenue")
        if not isinstance(self.net_income, (int, float)) or not isinstance(self.total_revenue, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.total_revenue == 0:
            raise ValueError("Division by zero: total_revenue cannot be zero")
        return (self.net_income / self.total_revenue) * 100

    def compute_return_on_assets_metric(self, net_income, total_assets):
        """
        Compute Return on Assets: (net_income / total_assets) * 100
        """
        self.net_income = net_income
        self.total_assets = total_assets
        #python3 command.py -m return_on_assets 10180000000 122291000000
        #result 8.32062620520928 in %
        if self.net_income is None or self.total_assets is None:
            raise ValueError("Missing required input: net_income or total_assets")
        if not isinstance(self.net_income, (int, float)) or not isinstance(self.total_assets, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.total_assets == 0:
            raise ValueError("Division by zero: total_assets cannot be zero")
        return (self.net_income / self.total_assets) * 100

    def compute_return_on_equity_metric(self, net_income, shareholders_equity):
        """
        Compute Return on Equity: (net_income / shareholders_equity) * 100
        """
        self.net_income = net_income
        self.shareholders_equity = shareholders_equity
        #python3 command.py -m return_on_equity 10180000000 46843000000
        #result 21.73320521416156 in %
        if self.net_income is None or self.shareholders_equity is None:
            raise ValueError("Missing required input: net_income or shareholders_equity")
        if not isinstance(self.net_income, (int, float)) or not isinstance(self.shareholders_equity, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.shareholders_equity == 0:
            raise ValueError("Division by zero: shareholders_equity cannot be zero")
        return (self.net_income / self.shareholders_equity) * 100

    def compute_debt_ratio_metric(self, total_debt, total_assets):
        """
        Compute Debt Ratio: total_debt / total_assets
        """
        self.total_debt = total_debt
        self.total_assets = total_assets
        #python3 command.py -m debt_ratio 29643000000 122291000000
        #result 0.2423136359936592
        if self.total_debt is None or self.total_assets is None:
            raise ValueError("Missing required input: total_debt or total_assets")
        if not isinstance(self.total_debt, (int, float)) or not isinstance(self.total_assets, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.total_assets == 0:
            raise ValueError("Division by zero: total_assets cannot be zero")
        return self.total_debt / self.total_assets

    def compute_debt_equity_ratio_metric(self, total_debt, shareholders_equity):
        """
        Compute Debt Equity Ratio: total_debt / shareholders_equity
        """
        self.total_debt = total_debt
        self.shareholders_equity = shareholders_equity
        #python3 command.py -m debt_equity_ratio 29643000000 46843000000
        #result 0.6329968992875924
        if self.total_debt is None or self.shareholders_equity is None:
            raise ValueError("Missing required input: total_debt or shareholders_equity")
        if not isinstance(self.total_debt, (int, float)) or not isinstance(self.shareholders_equity, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.shareholders_equity == 0:
            raise ValueError("Division by zero: shareholders_equity cannot be zero")
        return self.total_debt / self.shareholders_equity

    def compute_price_to_sales_ratio_metric(self, market_cap, total_revenue):
        """
        Compute Price to Sales Ratio: market_cap / total_revenue
        """
        self.market_cap = market_cap
        self.total_revenue = total_revenue
        if self.market_cap is None or self.total_revenue is None:
            raise ValueError("Missing required input: market_cap or total_revenue")
        if not isinstance(self.market_cap, (int, float)) or not isinstance(self.total_revenue, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.total_revenue == 0:
            raise ValueError("Division by zero: total_revenue cannot be zero")
        return self.market_cap / self.total_revenue

    def compute_earnings_per_share_metric(self, net_income, number_of_shares_outstanding):
        """
        Compute Earnings Per Share (EPS): net_income / number_of_shares_outstanding
        """
        self.net_income = net_income
        self.number_of_shares_outstanding = number_of_shares_outstanding
        if self.net_income is None or self.number_of_shares_outstanding is None:
            raise ValueError("Missing required input: net_income or number_of_shares_outstanding")
        if not isinstance(self.net_income, (int, float)) or not isinstance(self.number_of_shares_outstanding, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.number_of_shares_outstanding == 0:
            raise ValueError("Division by zero: number_of_shares_outstanding cannot be zero")
        return self.net_income / self.number_of_shares_outstanding

    def compute_price_earnings_ratio_metric(self, market_price_per_share, net_income, number_of_shares_outstanding):
        """
        Compute Price Earnings Ratio: market_price_per_share / earnings_per_share
        """
        self.market_price_per_share = market_price_per_share
        self.net_income = net_income
        self.number_of_shares_outstanding = number_of_shares_outstanding
        if self.market_price_per_share is None or self.net_income is None or self.number_of_shares_outstanding is None:
            raise ValueError("Missing required input: market_price_per_share, net_income, or number_of_shares_outstanding")
        if not isinstance(self.market_price_per_share, (int, float)) or not isinstance(self.net_income, (int, float)) or not isinstance(self.number_of_shares_outstanding, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.number_of_shares_outstanding == 0:
            raise ValueError("Division by zero: number_of_shares_outstanding cannot be zero")
        return self.market_price_per_share / self.compute_earnings_per_share_metric(net_income, number_of_shares_outstanding)

    def compute_dividend_yield_metric(self, dividends_per_share, market_price_per_share):
        """
        Compute Dividend Yield: dividends_per_share / market_price_per_share
        """
        self.dividends_per_share = dividends_per_share
        self.market_price_per_share = market_price_per_share
        if self.dividends_per_share is None or self.market_price_per_share is None:
            raise ValueError("Missing required input: dividends_per_share or market_price_per_share")
        if not isinstance(self.dividends_per_share, (int, float)) or not isinstance(self.market_price_per_share, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.market_price_per_share == 0:
            raise ValueError("Division by zero: market_price_per_share cannot be zero")
        return self.dividends_per_share / self.market_price_per_share

    def compute_days_of_sales_outstanding_metric(self, accounts_receivable, total_revenue):
        """
        Compute Days of Sales Outstanding: (accounts_receivable / total_revenue) * 365
        """
        self.accounts_receivable = accounts_receivable
        self.total_revenue = total_revenue
        if self.accounts_receivable is None or self.total_revenue is None:
            raise ValueError("Missing required input: accounts_receivable or total_revenue")
        if not isinstance(self.accounts_receivable, (int, float)) or not isinstance(self.total_revenue, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.total_revenue == 0:
            raise ValueError("Division by zero: total_revenue cannot be zero")
        return (self.accounts_receivable / self.total_revenue) * 365

    def compute_days_of_inventory_outstanding_metric(self, inventory, cost_of_goods_sold):
        """
        Compute Days of Inventory Outstanding: (inventory / cost_of_goods_sold) * 365
        """
        self.inventory = inventory
        self.cost_of_goods_sold = cost_of_goods_sold
        if self.inventory is None or self.cost_of_goods_sold is None:
            raise ValueError("Missing required input: inventory or cost_of_goods_sold")
        if not isinstance(self.inventory, (int, float)) or not isinstance(self.cost_of_goods_sold, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.cost_of_goods_sold == 0:
            raise ValueError("Division by zero: cost_of_goods_sold cannot be zero")
        return (self.inventory / self.cost_of_goods_sold) * 365

    def compute_days_of_inventory_outstanding_alt_metric(self, inventory, total_revenue, gross_profit):
        """
        Compute Days of Inventory Outstanding: (inventory / (total_revenue - gross_profit)) * 365
        """
        self.inventory = inventory
        self.total_revenue = total_revenue
        self.gross_profit = gross_profit
        if self.inventory is None or self.total_revenue is None or self.gross_profit is None:
            raise ValueError("Missing required input: inventory, total_revenue, or gross_profit")
        if not isinstance(self.inventory, (int, float)) or not isinstance(self.total_revenue, (int, float)) or not isinstance(self.gross_profit, (int, float)):
            raise ValueError("Inputs must be numeric")
        cost_of_goods_sold = self.total_revenue - self.gross_profit
        if cost_of_goods_sold == 0:
            raise ValueError("Division by zero: cost_of_goods_sold cannot be zero")
        return (self.inventory / cost_of_goods_sold) * 365

    def compute_days_of_payables_outstanding_metric(self, account_payables, cost_of_goods_sold):
        """
        Compute Days of Payables Outstanding: (account_payables / cost_of_goods_sold) * 365
        """
        self.account_payables = account_payables
        self.cost_of_goods_sold = cost_of_goods_sold
        if self.account_payables is None or self.cost_of_goods_sold is None:
            raise ValueError("Missing required input: account_payables or cost_of_goods_sold")
        if not isinstance(self.account_payables, (int, float)) or not isinstance(self.cost_of_goods_sold, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.cost_of_goods_sold == 0:
            raise ValueError("Division by zero: cost_of_goods_sold cannot be zero")
        return (self.account_payables / self.cost_of_goods_sold) * 365

    def compute_receivables_turnover_metric(self, total_revenue, accounts_receivable):
        """
        Compute Receivables Turnover: total_revenue / accounts_receivable
        """
        self.total_revenue = total_revenue
        self.accounts_receivable = accounts_receivable
        if self.total_revenue is None or self.accounts_receivable is None:
            raise ValueError("Missing required input: total_revenue or accounts_receivable")
        if not isinstance(self.total_revenue, (int, float)) or not isinstance(self.accounts_receivable, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.accounts_receivable == 0:
            raise ValueError("Division by zero: accounts_receivable cannot be zero")
        return self.total_revenue / self.accounts_receivable

    def compute_payables_turnover_metric(self, cost_of_goods_sold, account_payables):
        """
        Compute Payables Turnover: cost_of_goods_sold / account_payables
        """
        self.cost_of_goods_sold = cost_of_goods_sold
        self.account_payables = account_payables
        if self.cost_of_goods_sold is None or self.account_payables is None:
            raise ValueError("Missing required input: cost_of_goods_sold or account_payables")
        if not isinstance(self.cost_of_goods_sold, (int, float)) or not isinstance(self.account_payables, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.account_payables == 0:
            raise ValueError("Division by zero: account_payables cannot be zero")
        return self.cost_of_goods_sold / self.account_payables

    def compute_inventory_turnover_metric(self, cost_of_goods_sold, inventory):
        """
        Compute Inventory Turnover: cost_of_goods_sold / inventory
        """
        self.cost_of_goods_sold = cost_of_goods_sold
        self.inventory = inventory
        if self.cost_of_goods_sold is None or self.inventory is None:
            raise ValueError("Missing required input: cost_of_goods_sold or inventory")
        if not isinstance(self.cost_of_goods_sold, (int, float)) or not isinstance(self.inventory, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.inventory == 0:
            raise ValueError("Division by zero: inventory cannot be zero")
        return self.cost_of_goods_sold / self.inventory

    def compute_asset_turnover_metric(self, total_revenue, total_assets):
        """
        Compute Asset Turnover: total_revenue / total_assets
        """
        self.total_revenue = total_revenue
        self.total_assets = total_assets
        if self.total_revenue is None or self.total_assets is None:
            raise ValueError("Missing required input: total_revenue or total_assets")
        if not isinstance(self.total_revenue, (int, float)) or not isinstance(self.total_assets, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.total_assets == 0:
            raise ValueError("Division by zero: total_assets cannot be zero")
        return self.total_revenue / self.total_assets

    def compute_fixed_asset_turnover_metric(self, total_revenue, property_plant_equipment_net):
        """
        Compute Fixed Asset Turnover: total_revenue / property_plant_equipment_net
        """
        self.total_revenue = total_revenue
        self.property_plant_equipment_net = property_plant_equipment_net
        if self.total_revenue is None or self.property_plant_equipment_net is None:
            raise ValueError("Missing required input: total_revenue or property_plant_equipment_net")
        if not isinstance(self.total_revenue, (int, float)) or not isinstance(self.property_plant_equipment_net, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.property_plant_equipment_net == 0:
            raise ValueError("Division by zero: property_plant_equipment_net cannot be zero")
        return self.total_revenue / self.property_plant_equipment_net

    def compute_effective_tax_rate_metric(self, income_tax_expense, income_before_tax):
        """
        Compute Effective Tax Rate: income_tax_expense / income_before_tax
        """
        self.income_tax_expense = income_tax_expense
        self.income_before_tax = income_before_tax
        if self.income_tax_expense is None or self.income_before_tax is None:
            raise ValueError("Missing required input: income_tax_expense or income_before_tax")
        if not isinstance(self.income_tax_expense, (int, float)) or not isinstance(self.income_before_tax, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.income_before_tax == 0:
            raise ValueError("Division by zero: income_before_tax cannot be zero")
        return self.income_tax_expense / self.income_before_tax

    def compute_interest_coverage_metric(self, operating_income, interest_expense):
        """
        Compute Interest Coverage: operating_income / interest_expense
        """
        self.operating_income = operating_income
        self.interest_expense = interest_expense
        if self.operating_income is None or self.interest_expense is None:
            raise ValueError("Missing required input: operating_income or interest_expense")
        if not isinstance(self.operating_income, (int, float)) or not isinstance(self.interest_expense, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.interest_expense == 0:
            raise ValueError("Division by zero: interest_expense cannot be zero")
        return self.operating_income / self.interest_expense

    def compute_long_term_debt_to_capitalization_metric(self, long_term_debt, total_stockholders_equity):
        """
        Compute Long Term Debt to Capitalization: long_term_debt / (long_term_debt + total_stockholders_equity)
        """
        self.long_term_debt = long_term_debt
        self.shareholders_equity = total_stockholders_equity
        if self.long_term_debt is None or self.shareholders_equity is None:
            raise ValueError("Missing required input: long_term_debt or total_stockholders_equity")
        if not isinstance(self.long_term_debt, (int, float)) or not isinstance(self.shareholders_equity, (int, float)):
            raise ValueError("Inputs must be numeric")
        denominator = self.long_term_debt + self.shareholders_equity
        if denominator == 0:
            raise ValueError("Division by zero: long_term_debt + total_stockholders_equity cannot be zero")
        return self.long_term_debt / denominator

    def compute_total_debt_to_capitalization_metric(self, total_debt, total_stockholders_equity):
        """
        Compute Total Debt to Capitalization: total_debt / (total_debt + total_stockholders_equity)
        """
        self.total_debt = total_debt
        self.shareholders_equity = total_stockholders_equity
        if self.total_debt is None or self.shareholders_equity is None:
            raise ValueError("Missing required input: total_debt or total_stockholders_equity")
        if not isinstance(self.total_debt, (int, float)) or not isinstance(self.shareholders_equity, (int, float)):
            raise ValueError("Inputs must be numeric")
        denominator = self.total_debt + self.shareholders_equity
        if denominator == 0:
            raise ValueError("Division by zero: total_debt + total_stockholders_equity cannot be zero")
        return self.total_debt / denominator

    def compute_cash_flow_to_debt_ratio_metric(self, operating_cash_flow, total_debt):
        """
        Compute Cash Flow to Debt Ratio: operating_cash_flow / total_debt
        """
        self.operating_cash_flow = operating_cash_flow
        self.total_debt = total_debt
        if self.operating_cash_flow is None or self.total_debt is None:
            raise ValueError("Missing required input: operating_cash_flow or total_debt")
        if not isinstance(self.operating_cash_flow, (int, float)) or not isinstance(self.total_debt, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.total_debt == 0:
            raise ValueError("Division by zero: total_debt cannot be zero")
        return self.operating_cash_flow / self.total_debt

    def compute_company_equity_multiplier_metric(self, total_assets, total_stockholders_equity):
        """
        Compute Company Equity Multiplier: total_assets / total_stockholders_equity
        """
        self.total_assets = total_assets
        self.shareholders_equity = total_stockholders_equity
        if self.total_assets is None or self.shareholders_equity is None:
            raise ValueError("Missing required input: total_assets or total_stockholders_equity")
        if not isinstance(self.total_assets, (int, float)) or not isinstance(self.shareholders_equity, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.shareholders_equity == 0:
            raise ValueError("Division by zero: total_stockholders_equity cannot be zero")
        return self.total_assets / self.shareholders_equity

    def compute_price_cash_flow_ratio_metric(self, market_cap, operating_cash_flow):
        """
        Compute Price Cash Flow Ratio: market_cap / operating_cash_flow
        """
        self.market_cap = market_cap
        self.operating_cash_flow = operating_cash_flow
        if self.market_cap is None or self.operating_cash_flow is None:
            raise ValueError("Missing required input: market_cap or operating_cash_flow")
        if not isinstance(self.market_cap, (int, float)) or not isinstance(self.operating_cash_flow, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.operating_cash_flow == 0:
            raise ValueError("Division by zero: operating_cash_flow cannot be zero")
        return self.market_cap / self.operating_cash_flow

    def compute_enterprise_value_multiple_metric(self, enterprise_value, ebitda):
        """
        Compute Enterprise Value Multiple: enterprise_value / ebitda
        """
        self.enterprise_value = enterprise_value
        self.ebitda = ebitda
        if self.enterprise_value is None or self.ebitda is None:
            raise ValueError("Missing required input: enterprise_value or ebitda")
        if not isinstance(self.enterprise_value, (int, float)) or not isinstance(self.ebitda, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.ebitda == 0:
            raise ValueError("Division by zero: ebitda cannot be zero")
        return self.enterprise_value / self.ebitda

    def compute_revenue_per_share_metric(self, total_revenue, weighted_average_shares_outstanding):
        """
        Compute Revenue Per Share: total_revenue / weighted_average_shares_outstanding
        """
        self.total_revenue = total_revenue
        self.number_of_shares_outstanding = weighted_average_shares_outstanding
        if self.total_revenue is None or self.number_of_shares_outstanding is None:
            raise ValueError("Missing required input: total_revenue or weighted_average_shares_outstanding")
        if not isinstance(self.total_revenue, (int, float)) or not isinstance(self.number_of_shares_outstanding, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.number_of_shares_outstanding == 0:
            raise ValueError("Division by zero: number_of_shares_outstanding cannot be zero")
        return self.total_revenue / self.number_of_shares_outstanding

    def compute_net_income_per_share_metric(self, net_income, weighted_average_shares_outstanding):
        """
        Compute Net Income Per Share: net_income / weighted_average_shares_outstanding
        """
        self.net_income = net_income
        self.number_of_shares_outstanding = weighted_average_shares_outstanding
        if self.net_income is None or self.number_of_shares_outstanding is None:
            raise ValueError("Missing required input: net_income or weighted_average_shares_outstanding")
        if not isinstance(self.net_income, (int, float)) or not isinstance(self.number_of_shares_outstanding, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.number_of_shares_outstanding == 0:
            raise ValueError("Division by zero: number_of_shares_outstanding cannot be zero")
        return self.net_income / self.number_of_shares_outstanding

    def compute_operating_cash_flow_per_share_metric(self, operating_cash_flow, weighted_average_shares_outstanding):
        """
        Compute Operating Cash Flow Per Share: operating_cash_flow / weighted_average_shares_outstanding
        """
        self.operating_cash_flow = operating_cash_flow
        self.number_of_shares_outstanding = weighted_average_shares_outstanding
        if self.operating_cash_flow is None or self.number_of_shares_outstanding is None:
            raise ValueError("Missing required input: operating_cash_flow or weighted_average_shares_outstanding")
        if not isinstance(self.operating_cash_flow, (int, float)) or not isinstance(self.number_of_shares_outstanding, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.number_of_shares_outstanding == 0:
            raise ValueError("Division by zero: number_of_shares_outstanding cannot be zero")
        return self.operating_cash_flow / self.number_of_shares_outstanding

    def compute_free_cash_flow_per_share_metric(self, free_cash_flow, weighted_average_shares_outstanding):
        """
        Compute Free Cash Flow Per Share: free_cash_flow / weighted_average_shares_outstanding
        """
        self.free_cash_flow = free_cash_flow
        self.number_of_shares_outstanding = weighted_average_shares_outstanding
        if self.free_cash_flow is None or self.number_of_shares_outstanding is None:
            raise ValueError("Missing required input: free_cash_flow or weighted_average_shares_outstanding")
        if not isinstance(self.free_cash_flow, (int, float)) or not isinstance(self.number_of_shares_outstanding, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.number_of_shares_outstanding == 0:
            raise ValueError("Division by zero: weighted_average_shares_outstanding cannot be zero")
        return self.free_cash_flow / self.number_of_shares_outstanding

    def compute_cash_per_share_metric(self, cash_and_short_term_investments, weighted_average_shares_outstanding):
        """
        Compute Cash Per Share: cash_and_short_term_investments / weighted_average_shares_outstanding
        """
        self.cash_and_cash_equivalents = cash_and_short_term_investments
        self.number_of_shares_outstanding = weighted_average_shares_outstanding
        if self.cash_and_cash_equivalents is None or self.number_of_shares_outstanding is None:
            raise ValueError("Missing required input: cash_and_short_term_investments or weighted_average_shares_outstanding")
        if not isinstance(self.cash_and_cash_equivalents, (int, float)) or not isinstance(self.number_of_shares_outstanding, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.number_of_shares_outstanding == 0:
            raise ValueError("Division by zero: weighted_average_shares_outstanding cannot be zero")
        return self.cash_and_cash_equivalents / self.number_of_shares_outstanding

    def compute_book_value_per_share_metric(self, total_stockholders_equity, weighted_average_shares_outstanding):
        """
        Compute Book Value Per Share: total_stockholders_equity / weighted_average_shares_outstanding
        """
        self.shareholders_equity = total_stockholders_equity
        self.number_of_shares_outstanding = weighted_average_shares_outstanding
        if self.shareholders_equity is None or self.number_of_shares_outstanding is None:
            raise ValueError("Missing required input: total_stockholders_equity or weighted_average_shares_outstanding")
        if not isinstance(self.shareholders_equity, (int, float)) or not isinstance(self.number_of_shares_outstanding, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.number_of_shares_outstanding == 0:
            raise ValueError("Division by zero: weighted_average_shares_outstanding cannot be zero")
        return self.shareholders_equity / self.number_of_shares_outstanding
        
    def compute_return_on_capital_employed_metric(self, operating_income, total_assets, total_current_liabilities):
        """
        Compute Return on Capital Employed: operating_income / (total_assets - total_current_liabilities)
        """
        self.operating_income = operating_income
        self.total_assets = total_assets
        self.totalCurrentLiabilities = total_current_liabilities
        if self.operating_income is None or self.total_assets is None or self.totalCurrentLiabilities is None:
            raise ValueError("Missing required input: operating_income, total_assets, or total_current_liabilities")
        if not isinstance(self.operating_income, (int, float)) or not isinstance(self.total_assets, (int, float)) or not isinstance(self.totalCurrentLiabilities, (int, float)):
            raise ValueError("Inputs must be numeric")
        capital_employed = self.total_assets - self.totalCurrentLiabilities
        if capital_employed == 0:
            raise ValueError("Division by zero: capital employed cannot be zero")
        return self.operating_income / capital_employed

    def compute_pretax_profit_margin_metric(self, income_before_tax, total_revenue):
        """
        Compute Pretax Profit Margin: income_before_tax / total_revenue
        """
        self.income_before_tax = income_before_tax
        self.total_revenue = total_revenue
        if self.income_before_tax is None or self.total_revenue is None:
            raise ValueError("Missing required input: income_before_tax or total_revenue")
        if not isinstance(self.income_before_tax, (int, float)) or not isinstance(self.total_revenue, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.total_revenue == 0:
            raise ValueError("Division by zero: total_revenue cannot be zero")
        return self.income_before_tax / self.total_revenue

    def compute_net_income_per_ebt_metric(self, net_income, income_before_tax):
        """
        Compute Net Income per EBT: net_income / income_before_tax
        """
        self.net_income = net_income
        self.income_before_tax = income_before_tax
        if self.net_income is None or self.income_before_tax is None:
            raise ValueError("Missing required input: net_income or income_before_tax")
        if not isinstance(self.net_income, (int, float)) or not isinstance(self.income_before_tax, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.income_before_tax == 0:
            raise ValueError("Division by zero: income_before_tax cannot be zero")
        return self.net_income / self.income_before_tax

    def compute_ebt_per_ebit_metric(self, income_before_tax, operating_income):
        """
        Compute EBT per EBIT: income_before_tax / operating_income
        """
        self.income_before_tax = income_before_tax
        self.operating_income = operating_income
        if self.income_before_tax is None or self.operating_income is None:
            raise ValueError("Missing required input: income_before_tax or operating_income")
        if not isinstance(self.income_before_tax, (int, float)) or not isinstance(self.operating_income, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.operating_income == 0:
            raise ValueError("Division by zero: operating_income cannot be zero")
        return self.income_before_tax / self.operating_income

    def compute_ebit_per_revenue_metric(self, operating_income, total_revenue):
        """
        Compute EBIT per Revenue: operating_income / total_revenue
        """
        self.operating_income = operating_income
        self.total_revenue = total_revenue
        if self.operating_income is None or self.total_revenue is None:
            raise ValueError("Missing required input: operating_income or total_revenue")
        if not isinstance(self.operating_income, (int, float)) or not isinstance(self.total_revenue, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.total_revenue == 0:
            raise ValueError("Division by zero: total_revenue cannot be zero")
        return self.operating_income / self.total_revenue

    def compute_payout_ratio_metric(self, dividends_per_share, earnings_per_share):
        """
        Compute Payout Ratio: dividends_per_share / earnings_per_share
        """
        self.dividends_per_share = dividends_per_share
        self.earnings_per_share = earnings_per_share
        if self.dividends_per_share is None or self.earnings_per_share is None:
            raise ValueError("Missing required input: dividends_per_share or earnings_per_share")
        if not isinstance(self.dividends_per_share, (int, float)) or not isinstance(self.earnings_per_share, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.earnings_per_share == 0:
            raise ValueError("Division by zero: earnings_per_share cannot be zero")
        return self.dividends_per_share / self.earnings_per_share

    def compute_operating_cash_flow_sales_ratio_metric(self, operating_cash_flow, total_revenue):
        """
        Compute Operating Cash Flow Sales Ratio: operating_cash_flow / total_revenue
        """
        self.operating_cash_flow = operating_cash_flow
        self.total_revenue = total_revenue
        if self.operating_cash_flow is None or self.total_revenue is None:
            raise ValueError("Missing required input: operating_cash_flow or total_revenue")
        if not isinstance(self.operating_cash_flow, (int, float)) or not isinstance(self.total_revenue, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.total_revenue == 0:
            raise ValueError("Division by zero: total_revenue cannot be zero")
        return self.operating_cash_flow / self.total_revenue

    def compute_free_cash_flow_operating_cash_flow_ratio_metric(self, free_cash_flow, operating_cash_flow):
        """
        Compute Free Cash Flow Operating Cash Flow Ratio: free_cash_flow / operating_cash_flow
        """
        self.free_cash_flow = free_cash_flow
        self.operating_cash_flow = operating_cash_flow
        if self.free_cash_flow is None or self.operating_cash_flow is None:
            raise ValueError("Missing required input: free_cash_flow or operating_cash_flow")
        if not isinstance(self.free_cash_flow, (int, float)) or not isinstance(self.operating_cash_flow, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.operating_cash_flow == 0:
            raise ValueError("Division by zero: operating_cash_flow cannot be zero")
        return self.free_cash_flow / self.operating_cash_flow

    def compute_capital_expenditure_coverage_ratio_metric(self, operating_cash_flow, capital_expenditures):
        """
        Compute Capital Expenditure Coverage Ratio: operating_cash_flow / capital_expenditures
        """
        self.operating_cash_flow = operating_cash_flow
        self.capital_expenditures = capital_expenditures
        if self.operating_cash_flow is None or self.capital_expenditures is None:
            raise ValueError("Missing required input: operating_cash_flow or capital_expenditures")
        if not isinstance(self.operating_cash_flow, (int, float)) or not isinstance(self.capital_expenditures, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.capital_expenditures == 0:
            raise ValueError("Division by zero: capital_expenditures cannot be zero")
        return self.operating_cash_flow / self.capital_expenditures

    def compute_ev_to_sales_metric(self, enterprise_value, total_revenue):
        """
        Compute EV to Sales: enterprise_value / total_revenue
        """
        self.enterprise_value = enterprise_value
        self.total_revenue = total_revenue
        if self.enterprise_value is None or self.total_revenue is None:
            raise ValueError("Missing required input: enterprise_value or total_revenue")
        if not isinstance(self.enterprise_value, (int, float)) or not isinstance(self.total_revenue, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.total_revenue == 0:
            raise ValueError("Division by zero: total_revenue cannot be zero")
        return self.enterprise_value / self.total_revenue

    def compute_ev_to_operating_cash_flow_metric(self, enterprise_value, operating_cash_flow):
        """
        Compute EV to Operating Cash Flow: enterprise_value / operating_cash_flow
        """
        self.enterprise_value = enterprise_value
        self.operating_cash_flow = operating_cash_flow
        if self.enterprise_value is None or self.operating_cash_flow is None:
            raise ValueError("Missing required input: enterprise_value or operating_cash_flow")
        if not isinstance(self.enterprise_value, (int, float)) or not isinstance(self.operating_cash_flow, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.operating_cash_flow == 0:
            raise ValueError("Division by zero: operating_cash_flow cannot be zero")
        return self.enterprise_value / self.operating_cash_flow

    def compute_ev_to_free_cash_flow_metric(self, enterprise_value, free_cash_flow):
        """
        Compute EV to Free Cash Flow: enterprise_value / free_cash_flow
        """
        self.enterprise_value = enterprise_value
        self.free_cash_flow = free_cash_flow
        if self.enterprise_value is None or self.free_cash_flow is None:
            raise ValueError("Missing required input: enterprise_value or free_cash_flow")
        if not isinstance(self.enterprise_value, (int, float)) or not isinstance(self.free_cash_flow, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.free_cash_flow == 0:
            raise ValueError("Division by zero: free_cash_flow cannot be zero")
        return self.enterprise_value / self.free_cash_flow

    def compute_price_earnings_to_growth_ratio_metric(self, price_earnings_ratio, growth_rate):
        """
        Compute Price Earnings to Growth Ratio: price_earnings_ratio / growth_rate
        """
        self.price_earnings_ratio = price_earnings_ratio
        self.growth_rate = growth_rate
        if self.price_earnings_ratio is None or self.growth_rate is None:
            raise ValueError("Missing required input: price_earnings_ratio or growth_rate")
        if not isinstance(self.price_earnings_ratio, (int, float)) or not isinstance(self.growth_rate, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.growth_rate == 0:
            raise ValueError("Division by zero: growth_rate cannot be zero")
        return self.price_earnings_ratio / self.growth_rate

    def compute_earning_yield_metric(self, earnings_per_share, price_per_share):
        """
        Compute Earning Yield: earnings_per_share / price_per_share
        """
        self.earnings_per_share = earnings_per_share
        self.price_per_share = price_per_share
        if self.earnings_per_share is None or self.price_per_share is None:
            raise ValueError("Missing required input: earnings_per_share or price_per_share")
        if not isinstance(self.earnings_per_share, (int, float)) or not isinstance(self.price_per_share, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.price_per_share == 0:
            raise ValueError("Division by zero: price_per_share cannot be zero")
        return self.earnings_per_share / self.price_per_share

    def compute_income_quality_metric(self, operating_cash_flow, net_income):
        """
        Compute Income Quality: operating_cash_flow / net_income
        """
        self.operating_cash_flow = operating_cash_flow
        self.net_income = net_income
        if self.operating_cash_flow is None or self.net_income is None:
            raise ValueError("Missing required input: operating_cash_flow or net_income")
        if not isinstance(self.operating_cash_flow, (int, float)) or not isinstance(self.net_income, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.net_income == 0:
            raise ValueError("Division by zero: net_income cannot be zero")
        return self.operating_cash_flow / self.net_income

    def compute_sales_general_and_administrative_to_revenue_metric(self, general_and_administrative_expenses, total_revenue):
        """
        Compute Sales General and Administrative to Revenue: general_and_administrative_expenses / total_revenue
        """
        self.general_and_administrative_expenses = general_and_administrative_expenses
        self.total_revenue = total_revenue
        if self.general_and_administrative_expenses is None or self.total_revenue is None:
            raise ValueError("Missing required input: general_and_administrative_expenses or total_revenue")
        if not isinstance(self.general_and_administrative_expenses, (int, float)) or not isinstance(self.total_revenue, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.total_revenue == 0:
            raise ValueError("Division by zero: total_revenue cannot be zero")
        return self.general_and_administrative_expenses / self.total_revenue

    def compute_research_and_development_to_revenue_metric(self, research_and_development_expenses, total_revenue):
        """
        Compute Research and Development to Revenue: research_and_development_expenses / total_revenue
        """
        self.research_and_development_expenses = research_and_development_expenses
        self.total_revenue = total_revenue
        if self.research_and_development_expenses is None or self.total_revenue is None:
            raise ValueError("Missing required input: research_and_development_expenses or total_revenue")
        if not isinstance(self.research_and_development_expenses, (int, float)) or not isinstance(self.total_revenue, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.total_revenue == 0:
            raise ValueError("Division by zero: total_revenue cannot be zero")
        return self.research_and_development_expenses / self.total_revenue

    def compute_intangibles_to_total_assets_metric(self, goodwill_and_intangible_assets, total_assets):
        """
        Compute Intangibles to Total Assets: goodwill_and_intangible_assets / total_assets
        """
        self.goodwill_and_intangible_assets = goodwill_and_intangible_assets
        self.total_assets = total_assets
        if self.goodwill_and_intangible_assets is None or self.total_assets is None:
            raise ValueError("Missing required input: goodwill_and_intangible_assets or total_assets")
        if not isinstance(self.goodwill_and_intangible_assets, (int, float)) or not isinstance(self.total_assets, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.total_assets == 0:
            raise ValueError("Division by zero: total_assets cannot be zero")
        return self.goodwill_and_intangible_assets / self.total_assets

    def compute_capex_to_operating_cash_flow_metric(self, capital_expenditures, operating_cash_flow):
        """
        Compute Capex to Operating Cash Flow: capital_expenditures / operating_cash_flow
        """
        self.capital_expenditures = capital_expenditures
        self.operating_cash_flow = operating_cash_flow
        if self.capital_expenditures is None or self.operating_cash_flow is None:
            raise ValueError("Missing required input: capital_expenditures or operating_cash_flow")
        if not isinstance(self.capital_expenditures, (int, float)) or not isinstance(self.operating_cash_flow, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.operating_cash_flow == 0:
            raise ValueError("Division by zero: operating_cash_flow cannot be zero")
        return self.capital_expenditures / self.operating_cash_flow

    def compute_capex_to_revenue_metric(self, capital_expenditures, total_revenue):
        """
        Compute Capex to Revenue: capital_expenditures / total_revenue
        """
        self.capital_expenditures = capital_expenditures
        self.total_revenue = total_revenue
        if self.capital_expenditures is None or self.total_revenue is None:
            raise ValueError("Missing required input: capital_expenditures or total_revenue")
        if not isinstance(self.capital_expenditures, (int, float)) or not isinstance(self.total_revenue, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.total_revenue == 0:
            raise ValueError("Division by zero: total_revenue cannot be zero")
        return self.capital_expenditures / self.total_revenue

    def compute_capex_to_depreciation_metric(self, capital_expenditures, depreciation_and_amortization):
        """
        Compute Capex to Depreciation: capital_expenditures / depreciation_and_amortization
        """
        self.capital_expenditures = capital_expenditures
        self.depreciation_and_amortization = depreciation_and_amortization
        if self.capital_expenditures is None or self.depreciation_and_amortization is None:
            raise ValueError("Missing required input: capital_expenditures or depreciation_and_amortization")
        if not isinstance(self.capital_expenditures, (int, float)) or not isinstance(self.depreciation_and_amortization, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.depreciation_and_amortization == 0:
            raise ValueError("Division by zero: depreciation_and_amortization cannot be zero")
        return self.capital_expenditures / self.depreciation_and_amortization

    def compute_stock_based_compensation_to_revenue_metric(self, stock_based_compensation, total_revenue):
        """
        Compute Stock Based Compensation to Revenue: stock_based_compensation / total_revenue
        """
        self.stock_based_compensation = stock_based_compensation
        self.total_revenue = total_revenue
        if self.stock_based_compensation is None or self.total_revenue is None:
            raise ValueError("Missing required input: stock_based_compensation or total_revenue")
        if not isinstance(self.stock_based_compensation, (int, float)) or not isinstance(self.total_revenue, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.total_revenue == 0:
            raise ValueError("Division by zero: total_revenue cannot be zero")
        return self.stock_based_compensation / self.total_revenue

    def compute_roic_metric(self, net_income, total_assets, total_current_liabilities):
        """
        Compute ROIC: net_income / (total_assets - total_current_liabilities)
        """
        self.net_income = net_income
        self.total_assets = total_assets
        self.total_current_liabilities = total_current_liabilities
        if self.net_income is None or self.total_assets is None or self.total_current_liabilities is None:
            raise ValueError("Missing required input: net_income, total_assets, or total_current_liabilities")
        if not isinstance(self.net_income, (int, float)) or not isinstance(self.total_assets, (int, float)) or not isinstance(self.total_current_liabilities, (int, float)):
            raise ValueError("Inputs must be numeric")
        invested_capital = self.total_assets - self.total_current_liabilities
        if invested_capital == 0:
            raise ValueError("Division by zero: invested capital cannot be zero")
        return self.net_income / invested_capital

    def compute_return_on_tangible_assets_metric(self, net_income, total_assets, goodwill_and_intangible_assets):
        """
        Compute Return on Tangible Assets: net_income / (total_assets - goodwill_and_intangible_assets)
        """
        self.net_income = net_income
        self.total_assets = total_assets
        self.goodwill_and_intangible_assets = goodwill_and_intangible_assets
        if self.net_income is None or self.total_assets is None or self.goodwill_and_intangible_assets is None:
            raise ValueError("Missing required input: net_income, total_assets, or goodwill_and_intangible_assets")
        if not isinstance(self.net_income, (int, float)) or not isinstance(self.total_assets, (int, float)) or not isinstance(self.goodwill_and_intangible_assets, (int, float)):
            raise ValueError("Inputs must be numeric")
        tangible_assets = self.total_assets - self.goodwill_and_intangible_assets
        if tangible_assets == 0:
            raise ValueError("Division by zero: tangible assets cannot be zero")
        return self.net_income / tangible_assets

    def compute_graham_net_net_per_share_metric(self, cash_and_cash_equivalents, accounts_receivable, inventory, total_liabilities, number_of_shares_outstanding):
        """
        Compute Graham Net-Net per share: (cash_and_cash_equivalents + 0.75 * accounts_receivable + 0.5 * inventory - total_liabilities) / number_of_shares_outstanding
        """
        self.cash_and_cash_equivalents = cash_and_cash_equivalents
        self.accounts_receivable = accounts_receivable
        self.inventory = inventory
        self.total_liabilities = total_liabilities
        self.number_of_shares_outstanding = number_of_shares_outstanding
        if self.cash_and_cash_equivalents is None or self.accounts_receivable is None or self.inventory is None or self.total_liabilities is None or self.number_of_shares_outstanding is None:
            raise ValueError("Missing required input: cash_and_cash_equivalents, accounts_receivable, inventory, total_liabilities, or number_of_shares_outstanding")
        if not isinstance(self.cash_and_cash_equivalents, (int, float)) or not isinstance(self.accounts_receivable, (int, float)) or not isinstance(self.inventory, (int, float)) or not isinstance(self.total_liabilities, (int, float)) or not isinstance(self.number_of_shares_outstanding, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.number_of_shares_outstanding == 0:
            raise ValueError("Division by zero: number_of_shares_outstanding cannot be zero")
        return (self.cash_and_cash_equivalents + 0.75 * self.accounts_receivable + 0.5 * self.inventory - self.total_liabilities) / self.number_of_shares_outstanding

    def compute_tangible_asset_value_metric(self, total_assets, goodwill_and_intangible_assets):
        """
        Compute Tangible Asset Value: total_assets - goodwill_and_intangible_assets
        """
        self.total_assets = total_assets
        self.goodwill_and_intangible_assets = goodwill_and_intangible_assets
        if self.total_assets is None or self.goodwill_and_intangible_assets is None:
            raise ValueError("Missing required input: total_assets or goodwill_and_intangible_assets")
        if not isinstance(self.total_assets, (int, float)) or not isinstance(self.goodwill_and_intangible_assets, (int, float)):
            raise ValueError("Inputs must be numeric")
        return self.total_assets - self.goodwill_and_intangible_assets

    def compute_net_current_asset_value_metric(self, current_assets, current_liabilities):
        """
        Compute Net Current Asset Value: current_assets - current_liabilities
        """
        self.total_current_assets = current_assets
        self.total_current_liabilities = current_liabilities
        if self.total_current_assets is None or self.total_current_liabilities is None:
            raise ValueError("Missing required input: current_assets or current_liabilities")
        if not isinstance(self.total_current_assets, (int, float)) or not isinstance(self.total_current_liabilities, (int, float)):
            raise ValueError("Inputs must be numeric")
        return self.total_current_assets - self.total_current_liabilities

    def compute_invested_capital_metric(self, total_assets, total_current_liabilities):
        """
        Compute Invested Capital: total_assets - total_current_liabilities
        """
        self.total_assets = total_assets
        self.total_current_liabilities = total_current_liabilities
        if self.total_assets is None or self.total_current_liabilities is None:
            raise ValueError("Missing required input: total_assets or total_current_liabilities")
        if not isinstance(self.total_assets, (int, float)) or not isinstance(self.total_current_liabilities, (int, float)):
            raise ValueError("Inputs must be numeric")
        return self.total_assets - self.total_current_liabilities

    def compute_capex_per_share_metric(self, capital_expenditures, weighted_average_shares_outstanding):
        """
        Compute Capex Per Share: capital_expenditures / weighted_average_shares_outstanding
        """
        self.capital_expenditures = capital_expenditures
        self.number_of_shares_outstanding = weighted_average_shares_outstanding
        if self.capital_expenditures is None or self.number_of_shares_outstanding is None:
            raise ValueError("Missing required input: capital_expenditures or weighted_average_shares_outstanding")
        if not isinstance(self.capital_expenditures, (int, float)) or not isinstance(self.number_of_shares_outstanding, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.number_of_shares_outstanding == 0:
            raise ValueError("Division by zero: weighted_average_shares_outstanding cannot be zero")
        return self.capital_expenditures / self.number_of_shares_outstanding

    def compute_price_to_book_ratio_metric(self, market_price_per_share, total_stockholders_equity, weighted_average_shares_outstanding):
        """
        Compute Price to Book Ratio: market_price_per_share / (total_stockholders_equity / weighted_average_shares_outstanding)
        """
        self.market_price_per_share = market_price_per_share
        self.shareholders_equity = total_stockholders_equity
        self.number_of_shares_outstanding = weighted_average_shares_outstanding
        if self.market_price_per_share is None or self.shareholders_equity is None or self.number_of_shares_outstanding is None:
            raise ValueError("Missing required input: market_price_per_share, total_stockholders_equity, or weighted_average_shares_outstanding")
        if not isinstance(self.market_price_per_share, (int, float)) or not isinstance(self.shareholders_equity, (int, float)) or not isinstance(self.number_of_shares_outstanding, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.number_of_shares_outstanding == 0:
            raise ValueError("Division by zero: weighted_average_shares_outstanding cannot be zero")
        if self.shareholders_equity == 0:
            raise ValueError("Division by zero: total_stockholders_equity cannot be zero")
        book_value_per_share = self.shareholders_equity / self.number_of_shares_outstanding
        return self.market_price_per_share / book_value_per_share

    def compute_price_to_free_cash_flow_ratio_metric(self, market_price_per_share, free_cash_flow, weighted_average_shares_outstanding):
        """
        Compute Price to Free Cash Flow Ratio: market_price_per_share / (free_cash_flow / weighted_average_shares_outstanding)
        """
        self.market_price_per_share = market_price_per_share
        self.free_cash_flow = free_cash_flow
        self.number_of_shares_outstanding = weighted_average_shares_outstanding
        if self.market_price_per_share is None or self.free_cash_flow is None or self.number_of_shares_outstanding is None:
            raise ValueError("Missing required input: market_price_per_share, free_cash_flow, or weighted_average_shares_outstanding")
        if not isinstance(self.market_price_per_share, (int, float)) or not isinstance(self.free_cash_flow, (int, float)) or not isinstance(self.number_of_shares_outstanding, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.number_of_shares_outstanding == 0:
            raise ValueError("Division by zero: weighted_average_shares_outstanding cannot be zero")
        if self.free_cash_flow == 0:
            raise ValueError("Division by zero: free_cash_flow cannot be zero")
        free_cash_flow_per_share = self.free_cash_flow / self.number_of_shares_outstanding
        return self.market_price_per_share / free_cash_flow_per_share

    def compute_price_to_operating_cash_flow_ratio_metric(self, market_price_per_share, operating_cash_flow, weighted_average_shares_outstanding):
        """
        Compute Price to Operating Cash Flow Ratio: market_price_per_share / (operating_cash_flow / weighted_average_shares_outstanding)
        """
        self.market_price_per_share = market_price_per_share
        self.operating_cash_flow = operating_cash_flow
        self.number_of_shares_outstanding = weighted_average_shares_outstanding
        if self.market_price_per_share is None or self.operating_cash_flow is None or self.number_of_shares_outstanding is None:
            raise ValueError("Missing required input: market_price_per_share, operating_cash_flow, or weighted_average_shares_outstanding")
        if not isinstance(self.market_price_per_share, (int, float)) or not isinstance(self.operating_cash_flow, (int, float)) or not isinstance(self.number_of_shares_outstanding, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.number_of_shares_outstanding == 0:
            raise ValueError("Division by zero: weighted_average_shares_outstanding cannot be zero")
        if self.operating_cash_flow == 0:
            raise ValueError("Division by zero: operating_cash_flow cannot be zero")
        operating_cash_flow_per_share = self.operating_cash_flow / self.number_of_shares_outstanding
        return self.market_price_per_share / operating_cash_flow_per_share

    def compute_free_cash_flow_yield_metric(self, free_cash_flow, weighted_average_shares_outstanding, market_price_per_share):
        """
        Compute Free Cash Flow Yield: (free_cash_flow / weighted_average_shares_outstanding) / market_price_per_share
        """
        self.free_cash_flow = free_cash_flow
        self.number_of_shares_outstanding = weighted_average_shares_outstanding
        self.market_price_per_share = market_price_per_share
        if self.free_cash_flow is None or self.number_of_shares_outstanding is None or self.market_price_per_share is None:
            raise ValueError("Missing required input: free_cash_flow, weighted_average_shares_outstanding, or market_price_per_share")
        if not isinstance(self.free_cash_flow, (int, float)) or not isinstance(self.number_of_shares_outstanding, (int, float)) or not isinstance(self.market_price_per_share, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.number_of_shares_outstanding == 0:
            raise ValueError("Division by zero: weighted_average_shares_outstanding cannot be zero")
        if self.market_price_per_share == 0:
            raise ValueError("Division by zero: market_price_per_share cannot be zero")
        free_cash_flow_per_share = self.free_cash_flow / self.number_of_shares_outstanding
        return free_cash_flow_per_share / self.market_price_per_share

    def compute_graham_number_metric(self, net_income, total_stockholders_equity, weighted_average_shares_outstanding):
        """
        Compute Graham Number: sqrt(22.5 * (net_income / weighted_average_shares_outstanding) * (total_stockholders_equity / weighted_average_shares_outstanding))
        """
        self.net_income = net_income
        self.shareholders_equity = total_stockholders_equity
        self.number_of_shares_outstanding = weighted_average_shares_outstanding
        if self.net_income is None or self.shareholders_equity is None or self.number_of_shares_outstanding is None:
            raise ValueError("Missing required input: net_income, total_stockholders_equity, or weighted_average_shares_outstanding")
        if not isinstance(self.net_income, (int, float)) or not isinstance(self.shareholders_equity, (int, float)) or not isinstance(self.number_of_shares_outstanding, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.number_of_shares_outstanding == 0:
            raise ValueError("Division by zero: weighted_average_shares_outstanding cannot be zero")
        eps = self.net_income / self.number_of_shares_outstanding
        bvps = self.shareholders_equity / self.number_of_shares_outstanding
        return math.sqrt(22.5 * eps * bvps)

    def compute_operating_cycle_metric(self, accounts_receivable, total_revenue, inventory, cost_of_goods_sold):
        """
        Compute Operating Cycle: (accounts_receivable / total_revenue * 365) + (inventory / cost_of_goods_sold * 365)
        """
        self.accounts_receivable = accounts_receivable
        self.total_revenue = total_revenue
        self.inventory = inventory
        self.cost_of_goods_sold = cost_of_goods_sold
        if self.accounts_receivable is None or self.total_revenue is None or self.inventory is None or self.cost_of_goods_sold is None:
            raise ValueError("Missing required input: accounts_receivable, total_revenue, inventory, or cost_of_goods_sold")
        if not isinstance(self.accounts_receivable, (int, float)) or not isinstance(self.total_revenue, (int, float)) or not isinstance(self.inventory, (int, float)) or not isinstance(self.cost_of_goods_sold, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.total_revenue == 0:
            raise ValueError("Division by zero: total_revenue cannot be zero")
        if self.cost_of_goods_sold == 0:
            raise ValueError("Division by zero: cost_of_goods_sold cannot be zero")
        dso = (self.accounts_receivable / self.total_revenue) * 365
        dio = (self.inventory / self.cost_of_goods_sold) * 365
        return dso + dio

    def compute_cash_conversion_cycle_metric(self, accounts_receivable, total_revenue, inventory, cost_of_goods_sold, account_payables):
        """
        Compute Cash Conversion Cycle: (accounts_receivable / total_revenue * 365) + (inventory / cost_of_goods_sold * 365) - (account_payables / cost_of_goods_sold * 365)
        """
        self.accounts_receivable = accounts_receivable
        self.total_revenue = total_revenue
        self.inventory = inventory
        self.cost_of_goods_sold = cost_of_goods_sold
        self.account_payables = account_payables
        if self.accounts_receivable is None or self.total_revenue is None or self.inventory is None or self.cost_of_goods_sold is None or self.account_payables is None:
            raise ValueError("Missing required input: accounts_receivable, total_revenue, inventory, cost_of_goods_sold, or account_payables")
        if not isinstance(self.accounts_receivable, (int, float)) or not isinstance(self.total_revenue, (int, float)) or not isinstance(self.inventory, (int, float)) or not isinstance(self.cost_of_goods_sold, (int, float)) or not isinstance(self.account_payables, (int, float)):
            raise ValueError("Inputs must be numeric")
        if self.total_revenue == 0:
            raise ValueError("Division by zero: total_revenue cannot be zero")
        if self.cost_of_goods_sold == 0:
            raise ValueError("Division by zero: cost_of_goods_sold cannot be zero")
        dso = (self.accounts_receivable / self.total_revenue) * 365
        dio = (self.inventory / self.cost_of_goods_sold) * 365
        dpo = (self.account_payables / self.cost_of_goods_sold) * 365
        return dso + dio - dpo

    # Add more methods here...

def main():
    parser = argparse.ArgumentParser(description='Compute fundamental financial ratios.')
    parser.add_argument('-m', '--metric', required=True, help='The ratio to compute (e.g., current_ratio)')
    parser.add_argument('inputs', nargs='*', type=float, help='Input values for the ratio')

    args = parser.parse_args()

    ratio_calculator = Ratios()

    metric = args.metric.replace('_', '_')

    method_name = f'compute_{metric}_metric'

    if not hasattr(ratio_calculator, method_name):
        print(f"Error: Ratio '{metric}' not implemented.")
        sys.exit(1)

    method = getattr(ratio_calculator, method_name)

    try:
        result = method(*args.inputs)
        print(f"{result}")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except TypeError as e:
        print(f"Error: Incorrect number of inputs for {metric}. {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()