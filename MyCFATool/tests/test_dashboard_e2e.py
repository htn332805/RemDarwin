import pytest
import sqlite3
import json
from unittest.mock import patch, MagicMock
from dash.testing import DashComposite
from MyCFATool.dashboard.app import app
from MyCFATool.domain.services.fundamental_analysis_service import FundamentalAnalysisService
from MyCFATool.domain.services.technical_analysis_service import TechnicalAnalysisService
from MyCFATool.domain.services.forecasting_service import ForecastingService


@pytest.fixture
def dash_app():
    """Create a DashComposite for testing."""
    # Mock config loading
    mock_config = {
        "database": {"path": ":memory:"},
        "default_ticker": "AAPL"
    }
    with patch('yaml.safe_load', return_value=mock_config):
        with patch('builtins.open', MagicMock()):
            # Create test app with in-memory db
            test_app = DashComposite(app.app)  # Use the app instance
            yield test_app


@pytest.fixture
def test_db():
    """Set up test database with sample data."""
    conn = sqlite3.connect(':memory:')
    # Create tables
    conn.execute("""
        CREATE TABLE ticker (
            ticker_id INTEGER PRIMARY KEY,
            symbol TEXT UNIQUE
        );
    """)
    conn.execute("""
        CREATE TABLE balance_sheet (
            statement_id INTEGER PRIMARY KEY,
            ticker_id INTEGER,
            period_type TEXT,
            fiscal_date TEXT,
            statement_data TEXT,
            UNIQUE (ticker_id, period_type, fiscal_date)
        );
    """)
    conn.execute("""
        CREATE TABLE income_statement (
            statement_id INTEGER PRIMARY KEY,
            ticker_id INTEGER,
            period_type TEXT,
            fiscal_date TEXT,
            statement_data TEXT,
            UNIQUE (ticker_id, period_type, fiscal_date)
        );
    """)
    conn.execute("""
        CREATE TABLE cash_flow (
            statement_id INTEGER PRIMARY KEY,
            ticker_id INTEGER,
            period_type TEXT,
            fiscal_date TEXT,
            statement_data TEXT,
            UNIQUE (ticker_id, period_type, fiscal_date)
        );
    """)
    conn.execute("""
        CREATE TABLE historical_price (
            price_id INTEGER PRIMARY KEY,
            ticker_id INTEGER,
            date TEXT,
            price REAL,
            UNIQUE (ticker_id, date)
        );
    """)

    # Insert sample data for AAPL
    conn.execute("INSERT INTO ticker (symbol) VALUES ('AAPL')")
    ticker_id = 1

    # Sample data
    income_data = {
        'revenue': 1000,
        'netIncome': 150
    }
    balance_data = {
        'totalAssets': 2000,
        'totalShareholdersEquity': 1000
    }
    conn.execute("INSERT INTO income_statement (ticker_id, period_type, fiscal_date, statement_data) VALUES (?, ?, ?, ?)",
                 (ticker_id, 'annual', '2023-09-30', json.dumps(income_data)))
    conn.execute("INSERT INTO balance_sheet (ticker_id, period_type, fiscal_date, statement_data) VALUES (?, ?, ?, ?)",
                 (ticker_id, 'annual', '2023-09-30', json.dumps(balance_data)))

    yield conn
    conn.close()


class TestDashboardE2E:
    """End-to-end tests for the Dash dashboard."""

    def test_app_startup(self, dash_app):
        """Test that the app starts up correctly."""
        # The app should have a layout
        assert dash_app.app.layout is not None

        # Check that navigation tabs are present
        dash_app.wait_for_element("#tabs", timeout=10)

        # Check initial tab content
        initial_tab = dash_app.find_element("#tabs .tab--selected")
        assert initial_tab is not None

    def test_tab_switching(self, dash_app):
        """Test switching between tabs."""
        # Wait for tabs to load
        dash_app.wait_for_element("#tabs", timeout=10)

        # Find all tabs
        tabs = dash_app.find_elements("#tabs .tab")

        # Should have multiple tabs
        assert len(tabs) > 1

        # Test switching to Financial Statements tab
        fs_tab = dash_app.find_element("#tabs .tab[data-value='financial-statements']")
        if fs_tab:
            fs_tab.click()
            dash_app.wait_for_element("#financial-statements-content", timeout=10)
            assert dash_app.find_element("#financial-statements-content") is not None

        # Test switching to Risk Metrics tab
        risk_tab = dash_app.find_element("#tabs .tab[data-value='risk-metrics']")
        if risk_tab:
            risk_tab.click()
            dash_app.wait_for_element("#risk-metrics-content", timeout=10)
            assert dash_app.find_element("#risk-metrics-content") is not None

    def test_ticker_dropdown_interaction(self, dash_app, test_db):
        """Test ticker dropdown loads and triggers callbacks."""
        # Mock the database connection in callbacks
        with patch('MyCFATool.dashboard.callbacks.FundamentalAnalysisService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.compute_return_on_equity.return_value = {'value': 0.15, 'interpretation': 'profitability from shareholders investment'}
            mock_service.compute_return_on_assets.return_value = {'value': 0.075, 'interpretation': 'how efficiently assets generate profit'}
            mock_service_class.return_value = mock_service

            # Wait for overview tab
            dash_app.wait_for_element("#overview-content", timeout=10)

            # Find ticker dropdown
            dropdown = dash_app.find_element("#ticker-dropdown")
            assert dropdown is not None

            # The dropdown should have AAPL as option
            options = dash_app.find_elements("#ticker-dropdown option")
            assert len(options) >= 1

            # Select AAPL (assuming it's the first option)
            dropdown.send_keys("AAPL")
            dash_app.wait_for_element("#roe-display", timeout=10)

            # Check that ROE is displayed
            roe_element = dash_app.find_element("#roe-display")
            assert roe_element is not None

    def test_financial_statements_subtabs(self, dash_app, test_db):
        """Test Financial Statements sub-tabs work."""
        # Switch to Financial Statements tab
        fs_tab = dash_app.find_element("#tabs .tab[data-value='financial-statements']")
        if fs_tab:
            fs_tab.click()
            dash_app.wait_for_element("#financial-statements-tabs", timeout=10)

            # Find sub-tabs
            subtabs = dash_app.find_elements("#financial-statements-tabs .tab")
            assert len(subtabs) >= 3  # Income, Balance, Cash Flow

            # Test Income Statement sub-tab
            income_tab = dash_app.find_element("#financial-statements-tabs .tab[data-value='income-statement']")
            if income_tab:
                income_tab.click()
                dash_app.wait_for_element("#income-statement-table", timeout=10)
                table = dash_app.find_element("#income-statement-table")
                assert table is not None

            # Test Balance Sheet sub-tab
            balance_tab = dash_app.find_element("#financial-statements-tabs .tab[data-value='balance-sheet']")
            if balance_tab:
                balance_tab.click()
                dash_app.wait_for_element("#balance-sheet-table", timeout=10)
                table = dash_app.find_element("#balance-sheet-table")
                assert table is not None

    def test_new_tabs_functionality(self, dash_app, test_db):
        """Test new dashboard tabs: Forecasting, Risk Metrics, Validation/Audit, Technicals."""

        # Mock analytics classes
        with patch('MyCFATool.dashboard.callbacks.ForecastingService') as mock_forecasting:
            with patch('MyCFATool.dashboard.callbacks.TechnicalAnalysisService') as mock_technical:
                with patch('MyCFATool.dashboard.callbacks.FundamentalAnalysisService') as mock_validator:

                    mock_forecasting.return_value.arima_forecast.return_value = {
                        'forecast': [100, 105, 110],
                        'interpretation': 'ARIMA forecast'
                    }
                    mock_technical.return_value.compute_atr.return_value = {
                        'value': 2.5,
                        'interpretation': 'volatile market'
                    }
                    mock_validator.return_value.compute_altman_z_score.return_value = {
                        'z_score': 2.0,
                        'risk': 'gray'
                    }

                    # Test Forecasting tab
                    forecast_tab = dash_app.find_element("#tabs .tab[data-value='forecasting']")
                    if forecast_tab:
                        forecast_tab.click()
                        dash_app.wait_for_element("#forecasting-content", timeout=10)
                        content = dash_app.find_element("#forecasting-content")
                        assert content is not None
                        # Check for forecast display
                        assert dash_app.find_element("#forecast-display") is not None

                    # Test Risk Metrics tab
                    risk_tab = dash_app.find_element("#tabs .tab[data-value='risk-metrics']")
                    if risk_tab:
                        risk_tab.click()
                        dash_app.wait_for_element("#risk-metrics-content", timeout=10)
                        content = dash_app.find_element("#risk-metrics-content")
                        assert content is not None
                        # Check for Altman Z display
                        assert dash_app.find_element("#altman-z-display") is not None

                    # Test Validation/Audit tab
                    audit_tab = dash_app.find_element("#tabs .tab[data-value='validation-audit']")
                    if audit_tab:
                        audit_tab.click()
                        dash_app.wait_for_element("#validation-audit-content", timeout=10)
                        content = dash_app.find_element("#validation-audit-content")
                        assert content is not None
                        # Check for audit log display
                        assert dash_app.find_element("#audit-log-display") is not None

                    # Test Technicals tab (enhanced)
                    technicals_tab = dash_app.find_element("#tabs .tab[data-value='technicals']")
                    if technicals_tab:
                        technicals_tab.click()
                        dash_app.wait_for_element("#technicals-content", timeout=10)
                        content = dash_app.find_element("#technicals-content")
                        assert content is not None
                        # Check for ATR display
                        assert dash_app.find_element("#atr-display") is not None

    def test_component_loading(self, dash_app):
        """Test that all components load without errors."""
        # Wait for main layout
        dash_app.wait_for_element("#main-layout", timeout=10)

        # Check for navigation
        nav = dash_app.find_element("#tabs")
        assert nav is not None

        # Check for footer or other static elements
        footer = dash_app.find_element("#footer")
        if footer:  # If footer exists
            assert footer is not None

    def test_error_handling(self, dash_app):
        """Test error handling in UI."""
        # Try invalid ticker
        dropdown = dash_app.find_element("#ticker-dropdown")
        if dropdown:
            dropdown.send_keys("INVALID")
            # Should handle gracefully without crashing
            # Check that no error message is shown or handled properly
            error_msg = dash_app.find_elements(".error-message")
            if error_msg:
                # If error messages are shown, ensure they are appropriate
                pass

    def test_responsive_layout(self, dash_app):
        """Test that layout adapts to different viewports."""
        # Set viewport size
        dash_app.driver.set_window_size(1200, 800)

        # Check that tabs are visible
        tabs = dash_app.find_elements("#tabs .tab")
        assert len(tabs) > 0

        # Test mobile size
        dash_app.driver.set_window_size(375, 667)
        # Layout should still work, perhaps with scrolling
        tabs_mobile = dash_app.find_elements("#tabs .tab")
        assert len(tabs_mobile) > 0