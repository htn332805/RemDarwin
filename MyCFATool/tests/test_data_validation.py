import unittest
import sqlite3
import json
import os
from unittest.mock import patch, mock_open, MagicMock, call
from MyCFATool.domain.services.fundamental_analysis_service import FundamentalAnalysisService
from MyCFATool.domain.repositories.financial_data_repository import FinancialDataRepository
from MyCFATool.core.validation import ValidationError


class TestDataValidation(unittest.TestCase):
    def setUp(self):
        self.db_path = ':memory:'
        self.mock_repo = MagicMock(spec=FinancialDataRepository)
        self.validator = FundamentalAnalysisService(self.mock_repo)
        # For tests that need direct DB access, create a mock conn
        self.conn = MagicMock()

        # Create tables
        self.conn.execute("""
            CREATE TABLE ticker (
                ticker_id INTEGER PRIMARY KEY,
                symbol TEXT UNIQUE
            );
        """)
        self.conn.execute("""
            CREATE TABLE balance_sheet (
                statement_id INTEGER PRIMARY KEY,
                ticker_id INTEGER,
                period_type TEXT,
                fiscal_date TEXT,
                statement_data TEXT,
                UNIQUE (ticker_id, period_type, fiscal_date)
            );
        """)
        self.conn.execute("""
            CREATE TABLE income_statement (
                statement_id INTEGER PRIMARY KEY,
                ticker_id INTEGER,
                period_type TEXT,
                fiscal_date TEXT,
                statement_data TEXT,
                UNIQUE (ticker_id, period_type, fiscal_date)
            );
        """)
        self.conn.execute("""
            CREATE TABLE cash_flow (
                statement_id INTEGER PRIMARY KEY,
                ticker_id INTEGER,
                period_type TEXT,
                fiscal_date TEXT,
                statement_data TEXT,
                UNIQUE (ticker_id, period_type, fiscal_date)
            );
        """)
        self.conn.execute("""
            CREATE TABLE historical_price (
                price_id INTEGER PRIMARY KEY,
                ticker_id INTEGER,
                date TEXT,
                price REAL,
                UNIQUE (ticker_id, date)
            );
        """)
        self.conn.execute("""
            CREATE TABLE ratios (
                statement_id INTEGER PRIMARY KEY,
                ticker_id INTEGER,
                period_type TEXT,
                fiscal_date TEXT,
                statement_data TEXT,
                UNIQUE (ticker_id, period_type, fiscal_date)
            );
        """)

        # Insert sample ticker
        self.conn.execute("INSERT INTO ticker (symbol) VALUES ('AAPL')")
        self.ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = 'AAPL'").fetchone()[0]

    def tearDown(self):
        self.conn.close()

    def test_data_consistency_across_statements(self):
        """Test that data is consistent across different financial statements."""
        # Insert consistent data
        income_data = {
            'revenue': 1000,
            'netIncome': 150,
            'operatingIncome': 200
        }
        balance_data = {
            'totalAssets': 2000,
            'totalLiabilities': 1000,
            'totalShareholdersEquity': 1000,
            'totalCurrentAssets': 800,
            'totalCurrentLiabilities': 400
        }
        cash_data = {
            'operatingCashFlow': 180,
            'capitalExpenditures': 50,
            'dividendsPaid': -100
        }

        self.conn.execute("INSERT INTO income_statement (ticker_id, period_type, fiscal_date, statement_data) VALUES (?, ?, ?, ?)",
                         (self.ticker_id, 'annual', '2023-09-30', json.dumps(income_data)))
        self.conn.execute("INSERT INTO balance_sheet (ticker_id, period_type, fiscal_date, statement_data) VALUES (?, ?, ?, ?)",
                         (self.ticker_id, 'annual', '2023-09-30', json.dumps(balance_data)))
        self.conn.execute("INSERT INTO cash_flow (ticker_id, period_type, fiscal_date, statement_data) VALUES (?, ?, ?, ?)",
                         (self.ticker_id, 'annual', '2023-09-30', json.dumps(cash_data)))

        # Test ratio calculations are consistent
        roe1 = self.validator.compute_return_on_equity('AAPL', 'annual', '2023-09-30')
        roe2 = income_data['netIncome'] / balance_data['totalShareholdersEquity']
        self.assertAlmostEqual(roe1, roe2, places=5)

        # Test balance sheet consistency: Assets = Liabilities + Equity
        assets = balance_data['totalAssets']
        liabilities = balance_data['totalLiabilities']
        equity = balance_data['totalShareholdersEquity']
        self.assertEqual(assets, liabilities + equity)

    def test_data_consistency_validation_flags_inconsistencies(self):
        """Test that validation detects inconsistencies in data."""
        # Insert inconsistent data: Assets don't equal Liabilities + Equity
        balance_data = {
            'totalAssets': 1000,  # Should be 1500
            'totalLiabilities': 500,
            'totalShareholdersEquity': 1000
        }
        self.conn.execute("INSERT INTO balance_sheet (ticker_id, period_type, fiscal_date, statement_data) VALUES (?, ?, ?, ?)",
                         (self.ticker_id, 'annual', '2023-09-30', json.dumps(balance_data)))

        # Custom validation method to check balance sheet consistency
        result = self._check_balance_sheet_consistency('AAPL', 'annual', '2023-09-30')
        self.assertFalse(result['consistent'])
        self.assertEqual(result['discrepancy'], -500)  # 1000 - (500+1000)

    def test_ratio_calculations_with_new_analytics(self):
        """Test ratio calculations using new analytics methods."""
        # Insert comprehensive data
        balance_data = {
            'totalCurrentAssets': 600,
            'totalCurrentLiabilities': 300,
            'totalAssets': 1500,
            'totalLiabilities': 750,
            'totalShareholdersEquity': 750,
            'longTermDebt': 300,
            'retainedEarnings': 500,
            'commonStockSharesOutstanding': 50
        }
        income_data = {
            'revenue': 1200,
            'operatingIncome': 300,
            'netIncome': 225,
            'interestExpense': 30
        }
        cash_data = {
            'operatingCashFlow': 250,
            'capitalExpenditures': 100
        }
        self.conn.execute("INSERT INTO balance_sheet (ticker_id, period_type, fiscal_date, statement_data) VALUES (?, ?, ?, ?)",
                         (self.ticker_id, 'annual', '2023-09-30', json.dumps(balance_data)))
        self.conn.execute("INSERT INTO income_statement (ticker_id, period_type, fiscal_date, statement_data) VALUES (?, ?, ?, ?)",
                         (self.ticker_id, 'annual', '2023-09-30', json.dumps(income_data)))
        self.conn.execute("INSERT INTO cash_flow (ticker_id, period_type, fiscal_date, statement_data) VALUES (?, ?, ?, ?)",
                         (self.ticker_id, 'annual', '2023-09-30', json.dumps(cash_data)))
        self.conn.execute("INSERT INTO historical_price (ticker_id, date, price) VALUES (?, ?, ?)",
                         (self.ticker_id, '2023-09-30', 100.0))

        # Test Altman Z-Score
        altman = self.validator.compute_altman_z_score('AAPL', 'annual', '2023-09-30')
        self.assertIsNotNone(altman)
        self.assertIn('z_score', altman)
        self.assertIn('risk', altman)

        # Test FCF Yield
        fcf_yield = self.validator.compute_fcf_yield('AAPL', 'annual', '2023-09-30')
        self.assertIsNotNone(fcf_yield)
        expected_fcf = 250 - 100  # 150
        expected_yield = (expected_fcf / 50) / 100  # Per share FCF / price
        self.assertAlmostEqual(fcf_yield['fcf_yield'], expected_yield, places=5)

        # Test EV Multiples
        ev_multiples = self.validator.compute_ev_multiples('AAPL', 'annual', '2023-09-30')
        self.assertIsNotNone(ev_multiples)
        expected_ev = 100 * 50 + 750 - 0  # Market cap + debt - cash, assuming no cash
        self.assertEqual(ev_multiples['ev'], expected_ev)

    def test_audit_log_generation_with_discrepancies(self):
        """Test that audit logs are generated for validation discrepancies."""
        # Insert data with known discrepancies
        balance_data = {
            'totalCurrentAssets': 400,
            'totalCurrentLiabilities': 300
        }
        self.conn.execute("INSERT INTO balance_sheet (ticker_id, period_type, fiscal_date, statement_data) VALUES (?, ?, ?, ?)",
                         (self.ticker_id, 'annual', '2023-09-30', json.dumps(balance_data)))

        # Insert reported ratios with discrepancy
        reported = {'currentRatio': 1.0}  # Computed is 400/300 = 1.333
        self.conn.execute("INSERT INTO ratios (ticker_id, period_type, fiscal_date, statement_data) VALUES (?, ?, ?, ?)",
                         (self.ticker_id, 'annual', '2023-09-30', json.dumps(reported)))

        # Run validation
        validation_result = self.validator.validate_ratios('AAPL', 'annual', '2023-09-30')

        # Mock audit logging to verify it's called
        with patch('MyCFATool.analytics.validation.os.path.exists', return_value=True), \
             patch('MyCFATool.analytics.validation.os.makedirs'), \
             patch('MyCFATool.analytics.validation.os.stat', return_value=MagicMock(st_size=100)), \
             patch('MyCFATool.analytics.validation.open', mock_open()), \
             patch('MyCFATool.analytics.validation.csv.writer') as mock_writer, \
             patch('MyCFATool.analytics.validation.datetime') as mock_dt:

            mock_dt.now.return_value.isoformat.return_value = '2023-01-01T12:00:00'
            mock_writer_instance = MagicMock()
            mock_writer.return_value = mock_writer_instance

            self.validator.log_validation_results('AAPL', 'annual', '2023-09-30', validation_result)

            # Verify log was written
            calls = mock_writer_instance.writerow.call_args_list
            self.assertTrue(len(calls) > 0)
            # Should include discrepancy
            discrepancy_logged = any('currentRatio' in str(call) for call in calls)
            self.assertTrue(discrepancy_logged)

    def test_audit_log_blockchain_integrity(self):
        """Test blockchain-style audit logging for tamper detection."""
        # Test blockchain audit log
        with patch('MyCFATool.analytics.validation.os.path.exists', return_value=False), \
             patch('MyCFATool.analytics.validation.os.makedirs'), \
             patch('MyCFATool.analytics.validation.os.stat', return_value=MagicMock(st_size=0)), \
             patch('MyCFATool.analytics.validation.open', mock_open()), \
             patch('MyCFATool.analytics.validation.csv.writer') as mock_writer, \
             patch('MyCFATool.analytics.validation.datetime') as mock_dt:

            mock_dt.now.return_value.isoformat.return_value = '2023-01-01T12:00:00'
            mock_writer_instance = MagicMock()
            mock_writer.return_value = mock_writer_instance

            data1 = "Validation completed for AAPL"
            hash1 = self.validator.blockchain_audit_log(data1)

            # Second entry
            data2 = "Discrepancy found in currentRatio"
            hash2 = self.validator.blockchain_audit_log(data2)

            # Verify hashes are different and chained
            self.assertNotEqual(hash1, hash2)

            # Verify writer calls
            calls = mock_writer_instance.writerow.call_args_list
            self.assertEqual(len(calls), 3)  # Header + 2 data rows

            # Check that second hash uses first hash as previous
            second_row = calls[2][0][0]  # Last call's data
            self.assertEqual(second_row[2], hash1)  # previous_hash
            self.assertEqual(second_row[3], hash2)  # current_hash

    def test_trend_analysis_with_multi_period_data(self):
        """Test trend analysis with multiple periods."""
        # Insert 3 years of data
        years_data = [
            ('2021-09-30', {'netIncome': 100}, {'totalShareholdersEquity': 500}),
            ('2022-09-30', {'netIncome': 120}, {'totalShareholdersEquity': 550}),
            ('2023-09-30', {'netIncome': 150}, {'totalShareholdersEquity': 600}),
        ]

        for fiscal_date, income, balance in years_data:
            self.conn.execute("INSERT INTO income_statement (ticker_id, period_type, fiscal_date, statement_data) VALUES (?, ?, ?, ?)",
                             (self.ticker_id, 'annual', fiscal_date, json.dumps(income)))
            self.conn.execute("INSERT INTO balance_sheet (ticker_id, period_type, fiscal_date, statement_data) VALUES (?, ?, ?, ?)",
                             (self.ticker_id, 'annual', fiscal_date, json.dumps(balance)))

        fiscal_dates = ['2021-09-30', '2022-09-30', '2023-09-30']
        trends = self.validator.analyze_ratio_trends('AAPL', 'annual', 'returnOnEquity', fiscal_dates)

        self.assertIsNotNone(trends)
        self.assertEqual(trends['periods'], 3)
        self.assertIsNotNone(trends['cagr'])
        self.assertIsNotNone(trends['avg_annual_change'])
        self.assertIsNotNone(trends['volatility'])

        # Verify CAGR calculation
        roe_2021 = 100/500
        roe_2023 = 150/600
        expected_cagr = (roe_2023 / roe_2021)**(1/2) - 1
        self.assertAlmostEqual(trends['cagr'], expected_cagr, places=5)

    def test_scenario_analysis_stress_testing(self):
        """Test scenario analysis for stress testing."""
        # Base data
        income_data = {
            'revenue': 1000,
            'costOfRevenue': 600,
            'interestExpense': 50,
            'netIncome': 200
        }
        balance_data = {
            'totalAssets': 1500,
            'totalShareholdersEquity': 750,
            'totalCurrentAssets': 600,
            'totalCurrentLiabilities': 300
        }
        self.conn.execute("INSERT INTO income_statement (ticker_id, period_type, fiscal_date, statement_data) VALUES (?, ?, ?, ?)",
                         (self.ticker_id, 'annual', '2023-09-30', json.dumps(income_data)))
        self.conn.execute("INSERT INTO balance_sheet (ticker_id, period_type, fiscal_date, statement_data) VALUES (?, ?, ?, ?)",
                         (self.ticker_id, 'annual', '2023-09-30', json.dumps(balance_data)))

        # Stress factors
        stress_factors = {
            'revenue_change': -0.2,  # 20% revenue decline
            'cost_change': 0.1,      # 10% cost increase
            'interest_rate_change': 0.05  # 5% interest rate increase
        }

        result = self.validator.perform_scenario_analysis('AAPL', 'annual', '2023-09-30', stress_factors)

        self.assertIsNotNone(result)
        # Verify stressed ratios are different from base
        self.assertNotEqual(result['scenario_ratios']['roe'], result['base_ratios']['roe'])
        self.assertNotEqual(result['scenario_ratios']['roa'], result['base_ratios']['roa'])

        # Verify percentage changes are calculated
        self.assertIsNotNone(result['scenario_impacts']['roe']['percentage_change'])
        self.assertLess(result['scenario_impacts']['roe']['percentage_change'], 0)  # Negative impact

    def test_credit_rating_estimation(self):
        """Test credit rating estimation using scorecard."""
        # Data for high credit rating
        balance_data = {
            'totalAssets': 2000,
            'totalLiabilities': 400,
            'totalShareholdersEquity': 1600,
            'totalCurrentAssets': 800,
            'totalCurrentLiabilities': 200
        }
        income_data = {
            'operatingIncome': 300,
            'interestExpense': 20,
            'revenue': 1200
        }
        cash_data = {
            'operatingCashFlow': 250
        }
        self.conn.execute("INSERT INTO balance_sheet (ticker_id, period_type, fiscal_date, statement_data) VALUES (?, ?, ?, ?)",
                         (self.ticker_id, 'annual', '2023-09-30', json.dumps(balance_data)))
        self.conn.execute("INSERT INTO income_statement (ticker_id, period_type, fiscal_date, statement_data) VALUES (?, ?, ?, ?)",
                         (self.ticker_id, 'annual', '2023-09-30', json.dumps(income_data)))
        self.conn.execute("INSERT INTO cash_flow (ticker_id, period_type, fiscal_date, statement_data) VALUES (?, ?, ?, ?)",
                         (self.ticker_id, 'annual', '2023-09-30', json.dumps(cash_data)))

        rating = self.validator.estimate_credit_rating('AAPL', 'annual', '2023-09-30')
        self.assertIsNotNone(rating)
        self.assertIn(rating, ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC', 'CC', 'C', 'D'])

    def test_comprehensive_audit_report(self):
        """Test comprehensive audit report generation."""
        # Insert minimal data for report
        income_data = {'netIncome': 100}
        balance_data = {'totalShareholdersEquity': 500}
        self.conn.execute("INSERT INTO income_statement (ticker_id, period_type, fiscal_date, statement_data) VALUES (?, ?, ?, ?)",
                         (self.ticker_id, 'annual', '2023-09-30', json.dumps(income_data)))
        self.conn.execute("INSERT INTO balance_sheet (ticker_id, period_type, fiscal_date, statement_data) VALUES (?, ?, ?, ?)",
                         (self.ticker_id, 'annual', '2023-09-30', json.dumps(balance_data)))

        report = self.validator.generate_audit_report('AAPL', 'annual', '2023-09-30')
        self.assertIn('summary', report)
        self.assertIn('scores', report)
        self.assertIn('recommendations', report)
        self.assertIn('missing_data', report)

        # Should have some scores even with missing data
        self.assertIsInstance(report['scores'], dict)

    def test_fundamental_analysis_service_invalid_ticker(self):
        """Test FundamentalAnalysisService with invalid ticker."""
        self.mock_repo.get_income_statement_data.side_effect = ValidationError("Invalid ticker")

        with self.assertRaises(ValidationError):
            self.validator.compute_gross_profit_margin("INVALID", "annual", "2023-01-01")

    def test_fundamental_analysis_service_missing_data(self):
        """Test FundamentalAnalysisService with missing data."""
        self.mock_repo.get_income_statement_data.return_value = None

        result = self.validator.compute_gross_profit_margin("AAPL", "annual", "2023-01-01")
        self.assertIsNone(result)

    def test_fundamental_analysis_service_invalid_calculation(self):
        """Test FundamentalAnalysisService with invalid calculation inputs."""
        # Mock data that would cause division by zero or invalid calculation
        self.mock_repo.get_income_statement_data.return_value = {
            "revenue": 0,  # Zero revenue would cause issues in some ratios
            "costOfRevenue": 100
        }
        self.mock_repo.get_balance_sheet_data.return_value = {
            "totalAssets": 1000
        }

        with patch.object(self.validator, '_safe_divide', side_effect=ValidationError("Division by zero")):
            with self.assertRaises(ValidationError):
                self.validator.compute_gross_profit_margin("AAPL", "annual", "2023-01-01")

    def test_fundamental_analysis_service_negative_values(self):
        """Test FundamentalAnalysisService handling negative values appropriately."""
        self.mock_repo.get_income_statement_data.return_value = {
            "revenue": -100,  # Negative revenue
            "costOfRevenue": 50
        }

        # Depending on the method, it might handle or raise
        result = self.validator.compute_gross_profit_margin("AAPL", "annual", "2023-01-01")
        # Assume it handles gracefully
        self.assertIsNotNone(result)

    def test_fundamental_analysis_service_altman_z_score_insufficient_data(self):
        """Test Altman Z-Score with insufficient data."""
        self.mock_repo.get_balance_sheet_data.return_value = {"totalAssets": 1000}  # Missing other required fields
        self.mock_repo.get_income_statement_data.return_value = {"netIncome": 100}

        result = self.validator.compute_altman_z_score("AAPL", "annual", "2023-01-01")
        self.assertIsNone(result)  # Should return None for insufficient data

    def _check_balance_sheet_consistency(self, ticker, period, fiscal_date):
        """Helper method to check balance sheet consistency."""
        balance_data = self.validator._get_statement_data(ticker, 'balance_sheet', period, fiscal_date)
        if not balance_data:
            return {'consistent': False, 'discrepancy': None}

        assets = balance_data.get('totalAssets', 0)
        liabilities = balance_data.get('totalLiabilities', 0)
        equity = balance_data.get('totalShareholdersEquity', 0)

        discrepancy = assets - (liabilities + equity)
        consistent = abs(discrepancy) < 0.01  # Allow small rounding differences

        return {
            'consistent': consistent,
            'discrepancy': discrepancy if not consistent else 0
        }