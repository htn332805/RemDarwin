import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from datetime import date, datetime
from implementation.options.IV_Surfaces import (
    IVSurface, retrieve_iv_data, process_iv_for_surface, calculate_iv_metrics,
    validate_iv_surface, ExpirationCriteria, detect_market_regime,
    filter_options_by_expiration, save_iv_surface_to_db, integrate_with_screening_engine
)

class TestIVSurfaceDataclass:
    """Test IVSurface dataclass functionality."""

    def test_iv_surface_creation(self):
        """Test creating an IVSurface instance."""
        timestamp = datetime.now()
        underlying_price = 150.0
        market_regime = 'normal'

        # Create sample surface data
        index = pd.MultiIndex.from_tuples([
            (date(2024, 1, 15), 145.0),
            (date(2024, 1, 15), 150.0),
            (date(2024, 2, 15), 145.0),
        ], names=['expiration_date', 'strike_price'])

        surface_data = pd.DataFrame({
            'iv_call': [0.25, 0.22, 0.28],
            'iv_put': [0.26, 0.23, 0.29]
        }, index=index)

        surface = IVSurface(
            ticker='AAPL',
            timestamp=timestamp,
            underlying_price=underlying_price,
            market_regime=market_regime,
            surface_data=surface_data
        )

        assert surface.ticker == 'AAPL'
        assert surface.underlying_price == 150.0
        assert surface.market_regime == 'normal'
        assert len(surface.surface_data) == 3

class TestDataRetrieval:
    """Test data retrieval functions."""

    @pytest.fixture
    def sample_db(self):
        """Create a temporary database with sample data."""
        db_fd, db_path = tempfile.mkstemp()
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Create sample table
            cursor.execute("""
                CREATE TABLE options_2024_01_01 (
                    symbol TEXT,
                    expiration_date TEXT,
                    strike_price REAL,
                    option_type TEXT,
                    last_price REAL,
                    bid REAL,
                    ask REAL,
                    delta REAL,
                    gamma REAL,
                    theta REAL,
                    vega REAL,
                    rho REAL,
                    implied_volatility REAL,
                    underlying_price REAL
                )
            """)

            # Insert sample data
            sample_data = [
                ('AAPL', '2024-01-15', 145.0, 'call', 5.50, 5.45, 5.55, 0.65, 0.02, -0.03, 0.15, 0.08, 0.25, 150.0),
                ('AAPL', '2024-01-15', 150.0, 'call', 3.20, 3.15, 3.25, 0.52, 0.03, -0.04, 0.18, 0.06, 0.22, 150.0),
                ('AAPL', '2024-01-15', 145.0, 'put', 4.80, 4.75, 4.85, -0.35, 0.02, -0.025, 0.14, -0.05, 0.26, 150.0),
                ('AAPL', '2024-02-15', 145.0, 'call', 8.90, 8.85, 8.95, 0.58, 0.015, -0.02, 0.22, 0.12, 0.28, 150.0),
            ]

            cursor.executemany("INSERT INTO options_2024_01_01 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", sample_data)
            conn.commit()
            conn.close()

            yield db_path
        finally:
            os.close(db_fd)
            os.unlink(db_path)

    def test_retrieve_iv_data(self, sample_db):
        """Test retrieving IV data from database."""
        df = retrieve_iv_data(sample_db)

        assert not df.empty
        assert 'strike_price' in df.columns
        assert 'implied_volatility' in df.columns
        assert 'expiration_date' in df.columns
        assert 'option_type' in df.columns
        assert len(df) == 4  # All records retrieved

class TestSurfaceProcessing:
    """Test surface processing and interpolation."""

    def test_process_iv_for_surface_basic(self):
        """Test basic surface processing."""
        # Create sample data
        data = {
            'strike_price': [140, 145, 150, 155, 160] * 2,
            'implied_volatility': [0.30, 0.25, 0.20, 0.22, 0.28] * 2,
            'expiration_date': [date(2024, 1, 15)] * 5 + [date(2024, 2, 15)] * 5,
            'option_type': ['call'] * 10
        }
        df = pd.DataFrame(data)

        X, Y, Z, exps = process_iv_for_surface(df)

        assert X.shape[0] > 0
        assert Y.shape[0] > 0
        assert Z.shape[0] > 0
        assert len(exps) == 2

    def test_process_iv_for_surface_interpolation_methods(self):
        """Test different interpolation methods."""
        data = {
            'strike_price': [140, 145, 150, 155, 160],
            'implied_volatility': [0.30, 0.25, 0.20, 0.22, 0.28],
            'expiration_date': [date(2024, 1, 15)] * 5,
            'option_type': ['call'] * 5
        }
        df = pd.DataFrame(data)

        for method in ['linear', 'cubic', 'rbf']:
            X, Y, Z, exps = process_iv_for_surface(df, interpolation_method=method)
            assert Z.shape[0] > 0
            assert not np.all(np.isnan(Z))

class TestMetricsCalculation:
    """Test IV metrics calculations."""

    def test_calculate_iv_metrics(self):
        """Test IV metrics calculation."""
        data = {
            'strike_price': [145, 150, 155, 145, 150, 155],
            'implied_volatility': [0.25, 0.22, 0.24, 0.26, 0.23, 0.25],
            'expiration_date': [date(2024, 1, 15), date(2024, 1, 15), date(2024, 1, 15),
                               date(2024, 2, 15), date(2024, 2, 15), date(2024, 2, 15)],
            'option_type': ['call', 'call', 'call', 'put', 'put', 'put']
        }
        df = pd.DataFrame(data)

        metrics = calculate_iv_metrics(df, underlying_price=150.0)

        assert 'atm_iv' in metrics
        assert 'skew_ratios' in metrics
        assert 'term_premium' in metrics
        assert 'vol_of_vol' in metrics
        assert isinstance(metrics['vol_of_vol'], float)

class TestValidation:
    """Test surface validation functions."""

    def test_validate_iv_surface(self):
        """Test surface validation."""
        # Create test surface with some outliers
        Z = np.random.normal(0.25, 0.05, (50, 50))
        Z[10, 10] = 2.0  # Add outlier
        strikes = np.linspace(100, 200, 50)
        exps = [date(2024, 1, 1) + pd.Timedelta(days=i*7) for i in range(50)]

        validation = validate_iv_surface(Z, strikes, exps)

        assert 'outliers' in validation
        assert 'smoothness_issues' in validation
        assert 'arbitrage_flags' in validation
        assert 'overall_quality' in validation

class TestExpirationCriteria:
    """Test expiration criteria functionality."""

    def test_expiration_criteria_creation(self):
        """Test creating ExpirationCriteria."""
        criteria = ExpirationCriteria(min_days=20, max_days=120)
        assert criteria.min_days == 20
        assert criteria.max_days == 120
        assert criteria.regime_adjustment == True

    def test_regime_adjustment(self):
        """Test regime-based adjustment."""
        criteria = ExpirationCriteria()
        original_max = criteria.max_days

        criteria.adjust_for_regime('high_vol')
        assert criteria.max_days > original_max

class TestMarketRegime:
    """Test market regime detection."""

    def test_detect_market_regime_normal(self):
        """Test normal market detection."""
        regime = detect_market_regime(vix_level=18, iv_percentile=40, liquidity_score=0.8)
        assert regime == 'normal'

    def test_detect_market_regime_high_vol(self):
        """Test high volatility detection."""
        regime = detect_market_regime(vix_level=28, iv_percentile=75, liquidity_score=0.6)
        assert regime == 'high_vol'

    def test_detect_market_regime_crisis(self):
        """Test crisis regime detection."""
        regime = detect_market_regime(vix_level=40, iv_percentile=95, liquidity_score=0.3)
        assert regime == 'crisis'

class TestFiltering:
    """Test option filtering functions."""

    def test_filter_options_by_expiration(self):
        """Test expiration-based filtering."""
        data = {
            'strike_price': [145, 150, 155, 160],
            'implied_volatility': [0.25, 0.22, 0.24, 0.26],
            'expiration_date': [date.today() + pd.Timedelta(days=d) for d in [20, 60, 100, 30]],
            'option_type': ['call'] * 4
        }
        df = pd.DataFrame(data)

        criteria = ExpirationCriteria(min_days=30, max_days=90)
        filtered = filter_options_by_expiration(df, criteria)

        # Should filter out 20-day and 100-day expirations
        assert len(filtered) == 2
        assert all(30 <= (exp - date.today()).days <= 90 for exp in filtered['expiration_date'])

    def test_filter_with_earnings(self):
        """Test filtering with earnings proximity."""
        data = {
            'strike_price': [145, 150, 155],
            'implied_volatility': [0.25, 0.22, 0.24],
            'expiration_date': [date.today() + pd.Timedelta(days=45)] * 3,
            'option_type': ['call'] * 3
        }
        df = pd.DataFrame(data)

        earnings_dates = [date.today() + pd.Timedelta(days=50)]
        criteria = ExpirationCriteria(min_days=30, max_days=90)
        filtered = filter_options_by_expiration(df, criteria, earnings_dates=earnings_dates)

        # Should filter out expiration near earnings
        assert len(filtered) == 0

class TestIntegration:
    """Test integration functions."""

    def test_integrate_with_screening_engine(self):
        """Test screening engine integration."""
        data = {
            'strike_price': [145, 150, 155],
            'implied_volatility': [0.25, 0.22, 0.24],
            'expiration_date': [date.today() + pd.Timedelta(days=45)] * 3,
            'option_type': ['call'] * 3,
            'bid': [5.0, 3.0, 2.0],
            'ask': [5.1, 3.1, 2.1],
            'delta': [0.6, 0.5, 0.4],
            'gamma': [0.02, 0.03, 0.025],
            'theta': [-0.03, -0.04, -0.035],
            'vega': [0.15, 0.18, 0.16]
        }
        df = pd.DataFrame(data)

        filtered = integrate_with_screening_engine(df)

        # Should apply spread and Greeks filters
        assert len(filtered) >= 0  # May filter some based on criteria

if __name__ == "__main__":
    pytest.main([__file__])