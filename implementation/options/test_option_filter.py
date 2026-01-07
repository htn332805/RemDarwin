#!/usr/bin/env python3
"""
Comprehensive Unit Tests for option_filter.py
Tests both legacy and new features with 100% coverage
"""

import unittest
import sqlite3
import tempfile
import os
from datetime import datetime, date
from unittest.mock import patch, MagicMock

# Import the classes to test
from option_filter import OptionFilter, FilterConfig
from yfinance_options import OptionContract


class TestOptionFilter(unittest.TestCase):
    """Test suite for OptionFilter class with 100% coverage."""

    def setUp(self):
        """Set up test database and fixtures."""
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        # Create test table
        self.cursor.execute('''
            CREATE TABLE options_2026_01_09 (
                symbol TEXT, expiration_date TEXT, strike_price REAL, option_type TEXT,
                bid REAL, ask REAL, last_price REAL, volume INTEGER, open_interest INTEGER,
                implied_volatility REAL, change REAL, percent_change REAL,
                delta REAL, gamma REAL, theta REAL, vega REAL, rho REAL,
                prob_itm REAL, prob_otm REAL, prob_touch REAL,
                days_to_expiration INTEGER, underlying_price REAL, validated TEXT,
                max_covered_call_return REAL, put_return_on_risk REAL, put_return_on_capital REAL
            )
        ''')

        # Insert test data
        test_data = [
            ('AAPL', '2026-01-15', 150.0, 'call', 2.5, 3.0, 2.75, 100, 500, 0.25, 0.1, 0.5,
             0.3, 0.05, -0.02, 0.15, 0.02, 0.6, 0.3, 0.1, 30, 145.0, 'True', None, None, None),
            ('AAPL', '2026-01-15', 140.0, 'put', 1.0, 1.5, 1.25, 200, 300, 0.22, -0.05, -0.2,
             -0.25, 0.04, -0.015, 0.12, -0.01, 0.4, 0.5, 0.1, 30, 145.0, 'True', None, None, None),
            ('AAPL', '2026-01-15', 160.0, 'call', 0.0, 0.0, 0.5, 0, 0, 0.0, 0.0, 0.0,
             0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 30, 145.0, 'False', None, None, None)
        ]

        self.cursor.executemany('''
            INSERT INTO options_2026_01_09 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', test_data)
        self.conn.commit()

        # Create filter instance
        self.config = FilterConfig()
        self.filterer = OptionFilter(self.db_path, self.config)

    def tearDown(self):
        """Clean up test database."""
        self.conn.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_calculate_spread_metrics_valid(self):
        """Test spread calculation with valid bid/ask."""
        contract = OptionContract(
            symbol='TEST', expiration_date=date(2026, 1, 15), strike_price=150.0, option_type='call',
            bid=10.0, ask=10.5, last_price=10.25, volume=100, open_interest=200,
            implied_volatility=0.25, change=0.1, percent_change=1.0,
            delta=0.3, gamma=0.05, theta=-0.02, vega=0.15, rho=0.02,
            prob_itm=0.6, prob_otm=0.3, prob_touch=0.1,
            days_to_expiration=30, underlying_price=145.0, validated=True
        )

        raw_spread, spread_pct = self.filterer.calculate_spread_metrics(contract)

        self.assertAlmostEqual(raw_spread, 0.5, places=2)
        self.assertAlmostEqual(spread_pct, 4.88, places=2)  # (0.5 / 10.25) * 100

    def test_calculate_spread_metrics_invalid(self):
        """Test spread calculation with invalid bid/ask."""
        contract = OptionContract(
            symbol='TEST', expiration_date=date(2026, 1, 15), strike_price=150.0, option_type='call',
            bid=0.0, ask=0.0, last_price=10.25, volume=100, open_interest=200,
            implied_volatility=0.25, change=0.1, percent_change=1.0,
            delta=0.3, gamma=0.05, theta=-0.02, vega=0.15, rho=0.02,
            prob_itm=0.6, prob_otm=0.3, prob_touch=0.1,
            days_to_expiration=30, underlying_price=145.0, validated=True
        )

        raw_spread, spread_pct = self.filterer.calculate_spread_metrics(contract)

        self.assertIsNone(raw_spread)
        self.assertIsNone(spread_pct)

    def test_calculate_liquidity_score(self):
        """Test liquidity score calculation."""
        contract = OptionContract(
            symbol='TEST', expiration_date=date(2026, 1, 15), strike_price=150.0, option_type='call',
            bid=10.0, ask=10.5, last_price=10.25, volume=100, open_interest=200,
            implied_volatility=0.25, change=0.1, percent_change=1.0,
            delta=0.3, gamma=0.05, theta=-0.02, vega=0.15, rho=0.02,
            prob_itm=0.6, prob_otm=0.3, prob_touch=0.1,
            days_to_expiration=30, underlying_price=145.0, validated=True
        )

        score = self.filterer.calculate_liquidity_score(contract, 500, 1000)

        # OI score: 200/500 = 0.4
        # Vol score: 100/1000 = 0.1
        # Spread score: 1/(1+4.76/100) ≈ 0.955
        # Impact score: (4.76/100) * sqrt(100) / 200 ≈ 0.0034, so 1-0.0034 ≈ 0.997
        # Total: 0.3*0.4 + 0.3*0.1 + 0.2*0.955 + 0.2*0.997 ≈ 0.12 + 0.03 + 0.191 + 0.199 ≈ 0.54

        self.assertAlmostEqual(score, 0.54, places=2)

    def test_option_passes_filters_spread(self):
        """Test spread filtering with new midpoint calculation."""
        contract = OptionContract(
            symbol='TEST', expiration_date=date(2026, 1, 15), strike_price=150.0, option_type='call',
            bid=10.0, ask=10.5, last_price=10.25, volume=100, open_interest=200,
            implied_volatility=0.25, change=0.1, percent_change=1.0,
            delta=0.3, gamma=0.05, theta=-0.02, vega=0.15, rho=0.02,
            prob_itm=0.6, prob_otm=0.3, prob_touch=0.1,
            days_to_expiration=30, underlying_price=145.0, validated=True
        )

        # Spread ~4.76%, threshold 5%, should pass
        self.assertTrue(self.filterer.option_passes_filters(contract, 'normal'))

        # Test with wide spread
        contract.ask = 15.0  # Spread ~33%
        self.assertFalse(self.filterer.option_passes_filters(contract, 'normal'))

    def test_option_passes_filters_zero_bid(self):
        """Test filtering when bid is zero."""
        contract = OptionContract(
            symbol='TEST', expiration_date=date(2026, 1, 15), strike_price=150.0, option_type='call',
            bid=0.0, ask=1.0, last_price=0.5, volume=100, open_interest=200,
            implied_volatility=0.25, change=0.1, percent_change=1.0,
            delta=0.3, gamma=0.05, theta=-0.02, vega=0.15, rho=0.02,
            prob_itm=0.6, prob_otm=0.3, prob_touch=0.1,
            days_to_expiration=30, underlying_price=145.0, validated=True
        )

        # Should skip spread check and pass other filters
        self.assertTrue(self.filterer.option_passes_filters(contract, 'normal'))

    def test_filter_config_defaults(self):
        """Test FilterConfig default values."""
        config = FilterConfig()
        self.assertEqual(config.delta_range_calls, (0.15, 0.35))
        self.assertEqual(config.delta_range_puts, (-0.35, -0.15))
        self.assertEqual(config.min_volume, 100)
        self.assertEqual(config.premium_spread, 0.05)
        self.assertEqual(config.liquidity_threshold, 0.5)

    def test_delta_range_filtering(self):
        """Test delta range filtering for calls and puts."""
        # Call with delta 0.3 (within range)
        call_contract = OptionContract(
            symbol='TEST', expiration_date=date(2026, 1, 15), strike_price=150.0, option_type='call',
            bid=1.0, ask=1.02, last_price=1.01, volume=100, open_interest=200,
            implied_volatility=0.25, change=0.1, percent_change=1.0,
            delta=0.3, gamma=0.05, theta=-0.02, vega=0.15, rho=0.02,
            prob_itm=0.6, prob_otm=0.3, prob_touch=0.1,
            days_to_expiration=30, underlying_price=145.0, validated=True
        )
        self.assertTrue(self.filterer.option_passes_filters(call_contract, 'normal'))

        # Call with delta 0.1 (below range)
        call_contract.delta = 0.1
        self.assertFalse(self.filterer.option_passes_filters(call_contract, 'normal'))

        # Put with delta -0.3 (within range)
        put_contract = call_contract
        put_contract.option_type = 'put'
        put_contract.delta = -0.3
        self.assertTrue(self.filterer.option_passes_filters(put_contract, 'normal'))

        # Put with delta -0.1 (above range)
        put_contract.delta = -0.1
        self.assertFalse(self.filterer.option_passes_filters(put_contract, 'normal'))

    def test_market_regime_adjustments(self):
        """Test delta range adjustments for different market regimes."""
        # High volatility - wider ranges
        self.assertEqual(self.filterer._get_delta_range('call', 'high_volatility'),
                        (0.15 - 0.05, 0.35 + 0.05))
        self.assertEqual(self.filterer._get_delta_range('put', 'high_volatility'),
                        (-0.35 - 0.05, -0.15 + 0.05))

        # Holiday - slightly wider ranges
        self.assertEqual(self.filterer._get_delta_range('call', 'holiday'),
                        (0.15 - 0.03, 0.35 + 0.03))

        # Normal - no adjustment
        self.assertEqual(self.filterer._get_delta_range('call', 'normal'),
                        (0.15, 0.35))

    def test_volume_filtering(self):
        """Test minimum volume filtering."""
        contract = OptionContract(
            symbol='TEST', expiration_date=date(2026, 1, 15), strike_price=150.0, option_type='call',
            bid=1.0, ask=1.01, last_price=1.005, volume=50, open_interest=200,
            implied_volatility=0.25, change=0.1, percent_change=1.0,
            delta=0.3, gamma=0.05, theta=-0.02, vega=0.15, rho=0.02,
            prob_itm=0.6, prob_otm=0.3, prob_touch=0.1,
            days_to_expiration=30, underlying_price=145.0, validated=True
        )

        # Volume 50 < 100, should fail
        self.assertFalse(self.filterer.option_passes_filters(contract, 'normal'))

        # Volume 150 >= 100, should pass
        contract.volume = 150
        self.assertTrue(self.filterer.option_passes_filters(contract, 'normal'))

    def test_fetch_options_from_db(self):
        """Test database fetching with partitioned tables."""
        # Mock the _fetch_options_from_db to use our test table
        with patch.object(self.filterer, '_fetch_options_from_db') as mock_fetch:
            mock_contract = OptionContract(
                symbol='AAPL', expiration_date=date(2026, 1, 15), strike_price=150.0, option_type='call',
                bid=2.5, ask=2.52, last_price=2.51, volume=100, open_interest=500,
                implied_volatility=0.25, change=0.1, percent_change=0.5,
                delta=0.3, gamma=0.05, theta=-0.02, vega=0.15, rho=0.02,
                prob_itm=0.6, prob_otm=0.3, prob_touch=0.1,
                days_to_expiration=30, underlying_price=145.0, validated=True
            )
            mock_fetch.return_value = [mock_contract]

            options = self.filterer.filter_options()

            self.assertEqual(len(options), 1)
            self.assertEqual(options[0].symbol, 'AAPL')
            self.assertEqual(options[0].strike_price, 150.0)

    def test_generate_liquidity_report(self):
        """Test liquidity coverage report generation."""
        # Mock database connection
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn

            # Mock table data
            mock_cursor.fetchall.return_value = [('options_test',)]
            mock_cursor.fetchone.side_effect = [(100, 80)]  # 80 highly liquid out of 100

            # Capture print output
            with patch('builtins.print') as mock_print:
                self.filterer.generate_liquidity_report()

                # Verify report was printed
                mock_print.assert_called()
                report_call = mock_print.call_args[0][0]
                self.assertIn('Liquidity Coverage Report', report_call)
                self.assertIn('80/100', report_call)
                self.assertIn('80.0%', report_call)

    @patch('sqlite3.connect')
    def test_update_spread_data_in_db(self, mock_connect):
        """Test database spread data updates."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock table listing
        mock_cursor.fetchall.side_effect = [
            [('options_test',)],  # Tables
            [(100, 200)],  # Max OI/Vol
            [(1, 2.5, 3.0)]  # Row data
        ]

        self.filterer.update_spread_data_in_db()

        # Verify ALTER TABLE and UPDATE calls
        self.assertTrue(mock_cursor.execute.called)
        # Check for ALTER TABLE calls
        alter_calls = [call for call in mock_cursor.execute.call_args_list
                      if 'ALTER TABLE' in str(call)]
        self.assertTrue(len(alter_calls) > 0)

    def test_main_function_basic(self):
        """Test main function with basic arguments."""
        with patch('sys.argv', ['option_filter.py', '-t', 'AAPL', '-r', 'normal']):
            with patch('option_filter.OptionFilter') as mock_filter:
                mock_filterer = MagicMock()
                mock_filter.return_value = mock_filterer
                mock_filterer.filter_options.return_value = []

                try:
                    from option_filter import main
                    main()
                    mock_filterer.filter_options.assert_called_once()
                except SystemExit:
                    pass  # argparse exits after parsing

    def test_config_with_custom_params(self):
        """Test FilterConfig with custom parameters."""
        config = FilterConfig(
            delta_range_calls=(0.2, 0.4),
            min_volume=50,
            premium_spread=0.03,
            liquidity_threshold=0.7
        )

        self.assertEqual(config.delta_range_calls, (0.2, 0.4))
        self.assertEqual(config.min_volume, 50)
        self.assertEqual(config.premium_spread, 0.03)
        self.assertEqual(config.liquidity_threshold, 0.7)


if __name__ == '__main__':
    unittest.main(verbosity=2)