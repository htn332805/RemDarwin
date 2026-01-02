#!/usr/bin/env python3
"""
test_ratio_calculations.py

Unit tests for the ratio_trend_charts.py ratio calculation functions.

These tests verify that:
1. Liquidity ratios (Current, Quick, Cash) are calculated correctly
2. Solvency ratios (Debt-to-Equity, Debt-to-Assets, Interest Coverage) are calculated correctly
3. Profitability ratios (ROE, ROA, Gross Margin, Operating Margin, Net Margin) are calculated correctly
4. Edge cases (zero denominators, missing data) are handled gracefully

Run tests with:
    python -m pytest tests/test_ratio_calculations.py -v

Author: MyCFATool Project
Date: 2026-01-02
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ratio_trend_charts import (
    # Liquidity ratios
    calculate_current_ratio,
    calculate_quick_ratio,
    calculate_cash_ratio,
    calculate_liquidity_ratios,
    # Solvency ratios
    calculate_debt_to_equity,
    calculate_debt_to_assets,
    calculate_interest_coverage,
    calculate_solvency_ratios,
    # Profitability ratios
    calculate_roe,
    calculate_roa,
    calculate_gross_margin,
    calculate_operating_margin,
    calculate_net_margin,
    calculate_profitability_ratios,
    # Utilities
    get_column_value,
    build_file_paths,
    parse_arguments
)


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def sample_balance_sheet():
    """Create a sample balance sheet DataFrame for testing."""
    return pd.DataFrame({
        'date': pd.to_datetime(['2024-01-01', '2023-01-01', '2022-01-01']),
        'totalCurrentAssets': [100000, 90000, 80000],
        'totalCurrentLiabilities': [50000, 45000, 40000],
        'inventory': [10000, 9000, 8000],
        'cashAndCashEquivalents': [20000, 18000, 16000],
        'totalDebt': [60000, 55000, 50000],
        'totalStockholdersEquity': [80000, 75000, 70000],
        'totalAssets': [200000, 180000, 160000]
    })


@pytest.fixture
def sample_income_statement():
    """Create a sample income statement DataFrame for testing."""
    return pd.DataFrame({
        'date': pd.to_datetime(['2024-01-01', '2023-01-01', '2022-01-01']),
        'revenue': [500000, 450000, 400000],
        'grossProfit': [200000, 180000, 160000],
        'operatingIncome': [100000, 90000, 80000],
        'netIncome': [60000, 54000, 48000],
        'interestExpense': [5000, 4500, 4000]
    })


@pytest.fixture
def empty_dataframe():
    """Create an empty DataFrame for testing edge cases."""
    return pd.DataFrame()


@pytest.fixture
def balance_sheet_with_zeros():
    """Create a balance sheet with zero values for edge case testing."""
    return pd.DataFrame({
        'date': pd.to_datetime(['2024-01-01']),
        'totalCurrentAssets': [100000],
        'totalCurrentLiabilities': [0],  # Zero denominator
        'inventory': [10000],
        'cashAndCashEquivalents': [20000],
        'totalDebt': [60000],
        'totalStockholdersEquity': [0],  # Zero denominator
        'totalAssets': [0]  # Zero denominator
    })


# =============================================================================
# LIQUIDITY RATIO TESTS
# =============================================================================

class TestCurrentRatio:
    """Tests for Current Ratio calculation."""

    def test_current_ratio_basic(self, sample_balance_sheet):
        """Test basic current ratio calculation."""
        result = calculate_current_ratio(sample_balance_sheet)
        # Current Ratio = Current Assets / Current Liabilities
        # 100000 / 50000 = 2.0
        assert pytest.approx(result.iloc[0], rel=0.001) == 2.0
        # 90000 / 45000 = 2.0
        assert pytest.approx(result.iloc[1], rel=0.001) == 2.0
        # 80000 / 40000 = 2.0
        assert pytest.approx(result.iloc[2], rel=0.001) == 2.0

    def test_current_ratio_zero_denominator(self, balance_sheet_with_zeros):
        """Test current ratio with zero current liabilities."""
        result = calculate_current_ratio(balance_sheet_with_zeros)
        assert pd.isna(result.iloc[0])


class TestQuickRatio:
    """Tests for Quick Ratio calculation."""

    def test_quick_ratio_basic(self, sample_balance_sheet):
        """Test basic quick ratio calculation."""
        result = calculate_quick_ratio(sample_balance_sheet)
        # Quick Ratio = (Current Assets - Inventory) / Current Liabilities
        # (100000 - 10000) / 50000 = 1.8
        assert pytest.approx(result.iloc[0], rel=0.001) == 1.8
        # (90000 - 9000) / 45000 = 1.8
        assert pytest.approx(result.iloc[1], rel=0.001) == 1.8

    def test_quick_ratio_zero_denominator(self, balance_sheet_with_zeros):
        """Test quick ratio with zero current liabilities."""
        result = calculate_quick_ratio(balance_sheet_with_zeros)
        assert pd.isna(result.iloc[0])


class TestCashRatio:
    """Tests for Cash Ratio calculation."""

    def test_cash_ratio_basic(self, sample_balance_sheet):
        """Test basic cash ratio calculation."""
        result = calculate_cash_ratio(sample_balance_sheet)
        # Cash Ratio = Cash / Current Liabilities
        # 20000 / 50000 = 0.4
        assert pytest.approx(result.iloc[0], rel=0.001) == 0.4
        # 18000 / 45000 = 0.4
        assert pytest.approx(result.iloc[1], rel=0.001) == 0.4


class TestLiquidityRatiosWrapper:
    """Tests for the liquidity ratios wrapper function."""

    def test_liquidity_ratios_returns_dataframe(self, sample_balance_sheet):
        """Test that liquidity ratios returns a DataFrame with all ratios."""
        result = calculate_liquidity_ratios(sample_balance_sheet)
        assert isinstance(result, pd.DataFrame)
        assert 'Current Ratio' in result.columns
        assert 'Quick Ratio' in result.columns
        assert 'Cash Ratio' in result.columns
        assert 'date' in result.columns

    def test_liquidity_ratios_empty_input(self, empty_dataframe):
        """Test liquidity ratios with empty input."""
        result = calculate_liquidity_ratios(empty_dataframe)
        assert result.empty


# =============================================================================
# SOLVENCY RATIO TESTS
# =============================================================================

class TestDebtToEquity:
    """Tests for Debt-to-Equity ratio calculation."""

    def test_debt_to_equity_basic(self, sample_balance_sheet):
        """Test basic debt-to-equity calculation."""
        result = calculate_debt_to_equity(sample_balance_sheet)
        # Debt-to-Equity = Total Debt / Total Equity
        # 60000 / 80000 = 0.75
        assert pytest.approx(result.iloc[0], rel=0.001) == 0.75

    def test_debt_to_equity_zero_denominator(self, balance_sheet_with_zeros):
        """Test debt-to-equity with zero equity."""
        result = calculate_debt_to_equity(balance_sheet_with_zeros)
        assert pd.isna(result.iloc[0])


class TestDebtToAssets:
    """Tests for Debt-to-Assets ratio calculation."""

    def test_debt_to_assets_basic(self, sample_balance_sheet):
        """Test basic debt-to-assets calculation."""
        result = calculate_debt_to_assets(sample_balance_sheet)
        # Debt-to-Assets = Total Debt / Total Assets
        # 60000 / 200000 = 0.3
        assert pytest.approx(result.iloc[0], rel=0.001) == 0.3


class TestInterestCoverage:
    """Tests for Interest Coverage ratio calculation."""

    def test_interest_coverage_basic(self, sample_income_statement):
        """Test basic interest coverage calculation."""
        result = calculate_interest_coverage(sample_income_statement)
        # Interest Coverage = Operating Income / Interest Expense
        # 100000 / 5000 = 20.0
        assert pytest.approx(result.iloc[0], rel=0.001) == 20.0


class TestSolvencyRatiosWrapper:
    """Tests for the solvency ratios wrapper function."""

    def test_solvency_ratios_returns_dataframe(self, sample_balance_sheet, sample_income_statement):
        """Test that solvency ratios returns a DataFrame with all ratios."""
        result = calculate_solvency_ratios(sample_balance_sheet, sample_income_statement)
        assert isinstance(result, pd.DataFrame)
        assert 'Debt-to-Equity' in result.columns
        assert 'Debt-to-Assets' in result.columns
        assert 'Interest Coverage' in result.columns


# =============================================================================
# PROFITABILITY RATIO TESTS
# =============================================================================

class TestROE:
    """Tests for Return on Equity calculation."""

    def test_roe_basic(self, sample_income_statement, sample_balance_sheet):
        """Test basic ROE calculation."""
        result = calculate_roe(sample_income_statement, sample_balance_sheet)
        # ROE = (Net Income / Equity) * 100
        # (60000 / 80000) * 100 = 75.0%
        assert pytest.approx(result.iloc[0], rel=0.001) == 75.0


class TestROA:
    """Tests for Return on Assets calculation."""

    def test_roa_basic(self, sample_income_statement, sample_balance_sheet):
        """Test basic ROA calculation."""
        result = calculate_roa(sample_income_statement, sample_balance_sheet)
        # ROA = (Net Income / Total Assets) * 100
        # (60000 / 200000) * 100 = 30.0%
        assert pytest.approx(result.iloc[0], rel=0.001) == 30.0


class TestGrossMargin:
    """Tests for Gross Margin calculation."""

    def test_gross_margin_basic(self, sample_income_statement):
        """Test basic gross margin calculation."""
        result = calculate_gross_margin(sample_income_statement)
        # Gross Margin = (Gross Profit / Revenue) * 100
        # (200000 / 500000) * 100 = 40.0%
        assert pytest.approx(result.iloc[0], rel=0.001) == 40.0


class TestOperatingMargin:
    """Tests for Operating Margin calculation."""

    def test_operating_margin_basic(self, sample_income_statement):
        """Test basic operating margin calculation."""
        result = calculate_operating_margin(sample_income_statement)
        # Operating Margin = (Operating Income / Revenue) * 100
        # (100000 / 500000) * 100 = 20.0%
        assert pytest.approx(result.iloc[0], rel=0.001) == 20.0


class TestNetMargin:
    """Tests for Net Margin calculation."""

    def test_net_margin_basic(self, sample_income_statement):
        """Test basic net margin calculation."""
        result = calculate_net_margin(sample_income_statement)
        # Net Margin = (Net Income / Revenue) * 100
        # (60000 / 500000) * 100 = 12.0%
        assert pytest.approx(result.iloc[0], rel=0.001) == 12.0


class TestProfitabilityRatiosWrapper:
    """Tests for the profitability ratios wrapper function."""

    def test_profitability_ratios_returns_dataframe(self, sample_income_statement, sample_balance_sheet):
        """Test that profitability ratios returns a DataFrame with all ratios."""
        result = calculate_profitability_ratios(sample_income_statement, sample_balance_sheet)
        assert isinstance(result, pd.DataFrame)
        assert 'ROE (%)' in result.columns
        assert 'ROA (%)' in result.columns
        assert 'Gross Margin (%)' in result.columns
        assert 'Operating Margin (%)' in result.columns
        assert 'Net Margin (%)' in result.columns


# =============================================================================
# UTILITY FUNCTION TESTS
# =============================================================================

class TestGetColumnValue:
    """Tests for the get_column_value utility function."""

    def test_get_existing_column(self, sample_balance_sheet):
        """Test getting an existing column."""
        result = get_column_value(sample_balance_sheet, 'totalAssets')
        assert len(result) == 3
        assert result.iloc[0] == 200000

    def test_get_missing_column(self, sample_balance_sheet):
        """Test getting a missing column returns NaN series."""
        result = get_column_value(sample_balance_sheet, 'nonExistentColumn')
        assert len(result) == 3
        assert all(pd.isna(result))

    def test_get_missing_column_with_default(self, sample_balance_sheet):
        """Test getting a missing column with custom default."""
        result = get_column_value(sample_balance_sheet, 'nonExistentColumn', default=0)
        assert len(result) == 3
        assert all(result == 0)


class TestBuildFilePaths:
    """Tests for the build_file_paths utility function."""

    def test_build_annual_paths(self):
        """Test building file paths for annual data."""
        result = build_file_paths('CSCO', 'data', 'annual')
        assert 'balance_sheet' in result
        assert 'income_statement' in result
        assert 'cash_flow' in result
        assert 'CSCO_balance_sheet_annual.csv' in str(result['balance_sheet'])

    def test_build_quarterly_paths(self):
        """Test building file paths for quarterly data."""
        result = build_file_paths('AAPL', 'custom_dir', 'quarterly')
        assert 'AAPL_balance_sheet_quarterly.csv' in str(result['balance_sheet'])
        assert 'custom_dir' in str(result['balance_sheet'])


class TestParseArguments:
    """Tests for CLI argument parsing."""

    def test_parse_required_ticker(self):
        """Test parsing with required ticker argument."""
        args = parse_arguments(['-t', 'CSCO'])
        assert args.ticker == 'CSCO'
        assert args.directory == 'data'
        assert args.quarterly is False
        assert args.chart_type == 'line'

    def test_parse_all_arguments(self):
        """Test parsing with all arguments."""
        args = parse_arguments(['-t', 'AAPL', '-d', 'custom', '-q', '-c', 'bar'])
        assert args.ticker == 'AAPL'
        assert args.directory == 'custom'
        assert args.quarterly is True
        assert args.chart_type == 'bar'

    def test_parse_long_arguments(self):
        """Test parsing with long argument names."""
        args = parse_arguments(['--ticker', 'MSFT', '--directory', 'output', '--quarterly', '--chart-type', 'line'])
        assert args.ticker == 'MSFT'
        assert args.directory == 'output'
        assert args.quarterly is True
        assert args.chart_type == 'line'


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for the ratio calculation workflow."""

    def test_full_liquidity_workflow(self, sample_balance_sheet):
        """Test the full liquidity ratio calculation workflow."""
        result = calculate_liquidity_ratios(sample_balance_sheet)
        
        # Verify all ratios are calculated
        assert not result['Current Ratio'].isna().all()
        assert not result['Quick Ratio'].isna().all()
        assert not result['Cash Ratio'].isna().all()
        
        # Verify relationships between ratios
        # Current Ratio should always be >= Quick Ratio (inventory is non-negative)
        assert all(result['Current Ratio'] >= result['Quick Ratio'])
        # Quick Ratio should always be >= Cash Ratio (other current assets exist)
        assert all(result['Quick Ratio'] >= result['Cash Ratio'])

    def test_full_profitability_workflow(self, sample_income_statement, sample_balance_sheet):
        """Test the full profitability ratio calculation workflow."""
        result = calculate_profitability_ratios(sample_income_statement, sample_balance_sheet)
        
        # Verify all ratios are calculated
        assert not result['Gross Margin (%)'].isna().all()
        assert not result['Operating Margin (%)'].isna().all()
        assert not result['Net Margin (%)'].isna().all()
        
        # Verify margin relationships (assuming no extraordinary items)
        # Gross Margin >= Operating Margin >= Net Margin (typically)
        assert all(result['Gross Margin (%)'] >= result['Operating Margin (%)'])
        assert all(result['Operating Margin (%)'] >= result['Net Margin (%)'])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
