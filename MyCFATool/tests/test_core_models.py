import unittest
from pydantic import ValidationError
from MyCFATool.core.models import (
    FinancialStatement, IncomeStatementData, BalanceSheetData,
    CashFlowData, RatioData, ForecastInput, PriceData, TechnicalIndicatorInput
)


class TestCoreModels(unittest.TestCase):
    """Test cases for Pydantic models validation errors."""

    def test_financial_statement_valid(self):
        """Test FinancialStatement with valid data."""
        data = FinancialStatement(
            ticker="AAPL",
            period_type="annual",
            fiscal_date="2023-01-01",
            data={"key": "value"}
        )
        self.assertEqual(data.ticker, "AAPL")

    def test_financial_statement_ticker_too_short(self):
        """Test FinancialStatement with ticker too short."""
        with self.assertRaises(ValidationError) as cm:
            FinancialStatement(
                ticker="A",  # min_length=1 but test edge
                period_type="annual",
                fiscal_date="2023-01-01",
                data={"key": "value"}
            )
        self.assertIn("min_length", str(cm.exception))

    def test_financial_statement_ticker_too_long(self):
        """Test FinancialStatement with ticker too long."""
        with self.assertRaises(ValidationError) as cm:
            FinancialStatement(
                ticker="AAPLTOOLONG",  # max_length=10
                period_type="annual",
                fiscal_date="2023-01-01",
                data={"key": "value"}
            )
        self.assertIn("max_length", str(cm.exception))

    def test_financial_statement_invalid_period_type(self):
        """Test FinancialStatement with invalid period_type."""
        with self.assertRaises(ValidationError) as cm:
            FinancialStatement(
                ticker="AAPL",
                period_type="monthly",  # regex doesn't match
                fiscal_date="2023-01-01",
                data={"key": "value"}
            )
        self.assertIn("regex", str(cm.exception))

    def test_financial_statement_invalid_fiscal_date_format(self):
        """Test FinancialStatement with invalid fiscal_date format."""
        with self.assertRaises(ValidationError) as cm:
            FinancialStatement(
                ticker="AAPL",
                period_type="annual",
                fiscal_date="2023/01/01",  # doesn't match regex
                data={"key": "value"}
            )
        self.assertIn("regex", str(cm.exception))

    def test_income_statement_data_valid(self):
        """Test IncomeStatementData with valid data."""
        data = IncomeStatementData(
            revenue=1000.0,
            netIncome=100.0,
            weightedAverageSharesOutstanding=50.0
        )
        self.assertEqual(data.revenue, 1000.0)

    def test_income_statement_data_negative_revenue(self):
        """Test IncomeStatementData with negative revenue (invalid)."""
        with self.assertRaises(ValidationError) as cm:
            IncomeStatementData(
                revenue=-100.0  # ge=0
            )
        self.assertIn("revenue", str(cm.exception))

    def test_income_statement_data_negative_shares(self):
        """Test IncomeStatementData with negative shares."""
        with self.assertRaises(ValidationError) as cm:
            IncomeStatementData(
                weightedAverageSharesOutstanding=-10.0  # gt=0
            )
        self.assertIn("weightedAverageSharesOutstanding", str(cm.exception))

    def test_balance_sheet_data_valid(self):
        """Test BalanceSheetData with valid data."""
        data = BalanceSheetData(
            totalAssets=1000.0,
            totalLiabilities=500.0,
            totalEquity=500.0,
            commonStock=100.0
        )
        self.assertEqual(data.totalAssets, 1000.0)

    def test_balance_sheet_data_negative_assets(self):
        """Test BalanceSheetData with negative assets."""
        with self.assertRaises(ValidationError) as cm:
            BalanceSheetData(
                totalAssets=-100.0  # ge=0
            )
        self.assertIn("totalAssets", str(cm.exception))

    def test_balance_sheet_data_negative_equity(self):
        """Test BalanceSheetData with negative equity."""
        with self.assertRaises(ValidationError) as cm:
            BalanceSheetData(
                totalEquity=-100.0  # no constraint, should allow
            )
        # This should not raise, as totalEquity has no ge constraint
        data = BalanceSheetData(totalEquity=-100.0)
        self.assertEqual(data.totalEquity, -100.0)

    def test_cash_flow_data_valid(self):
        """Test CashFlowData with valid data."""
        data = CashFlowData(
            netIncome=100.0,
            operatingCashFlow=150.0,
            cashAtBeginningOfPeriod=200.0
        )
        self.assertEqual(data.netIncome, 100.0)

    def test_cash_flow_data_negative_capex(self):
        """Test CashFlowData with positive capex (should be <=0)."""
        with self.assertRaises(ValidationError) as cm:
            CashFlowData(
                capitalExpenditure=100.0  # le=0
            )
        self.assertIn("capitalExpenditure", str(cm.exception))

    def test_cash_flow_data_valid_negative_capex(self):
        """Test CashFlowData with valid negative capex."""
        data = CashFlowData(capitalExpenditure=-100.0)
        self.assertEqual(data.capitalExpenditure, -100.0)

    def test_ratio_data_valid(self):
        """Test RatioData with valid data."""
        data = RatioData(
            peRatio=15.0,
            currentRatio=2.0,
            debtToAssets=0.5
        )
        self.assertEqual(data.peRatio, 15.0)

    def test_ratio_data_negative_pe_ratio(self):
        """Test RatioData with negative peRatio."""
        with self.assertRaises(ValidationError) as cm:
            RatioData(
                peRatio=-5.0  # gt=0
            )
        self.assertIn("peRatio", str(cm.exception))

    def test_ratio_data_debt_ratio_too_high(self):
        """Test RatioData with debtToAssets > 1."""
        with self.assertRaises(ValidationError) as cm:
            RatioData(
                debtToAssets=1.5  # le=1
            )
        self.assertIn("debtToAssets", str(cm.exception))

    def test_forecast_input_valid(self):
        """Test ForecastInput with valid data."""
        data = ForecastInput(
            ticker="AAPL",
            variable="revenue",
            historical_data=[100, 110, 120],
            periods_ahead=3,
            model_type="linear"
        )
        self.assertEqual(data.ticker, "AAPL")

    def test_forecast_input_too_few_data_points(self):
        """Test ForecastInput with too few historical_data points."""
        with self.assertRaises(ValidationError) as cm:
            ForecastInput(
                ticker="AAPL",
                variable="revenue",
                historical_data=[100],  # min_items=2
                periods_ahead=3
            )
        self.assertIn("min_items", str(cm.exception))

    def test_forecast_input_periods_ahead_too_high(self):
        """Test ForecastInput with periods_ahead > 10."""
        with self.assertRaises(ValidationError) as cm:
            ForecastInput(
                ticker="AAPL",
                variable="revenue",
                historical_data=[100, 110],
                periods_ahead=15  # le=10
            )
        self.assertIn("periods_ahead", str(cm.exception))

    def test_forecast_input_invalid_model_type(self):
        """Test ForecastInput with invalid model_type."""
        with self.assertRaises(ValidationError) as cm:
            ForecastInput(
                ticker="AAPL",
                variable="revenue",
                historical_data=[100, 110],
                periods_ahead=3,
                model_type="invalid"  # regex doesn't match
            )
        self.assertIn("regex", str(cm.exception))

    def test_price_data_valid(self):
        """Test PriceData with valid data."""
        data = PriceData(
            date="2023-01-01",
            close=100.0
        )
        self.assertEqual(data.close, 100.0)

    def test_price_data_invalid_date_format(self):
        """Test PriceData with invalid date format."""
        with self.assertRaises(ValidationError) as cm:
            PriceData(
                date="01/01/2023",  # doesn't match regex
                close=100.0
            )
        self.assertIn("regex", str(cm.exception))

    def test_price_data_negative_close(self):
        """Test PriceData with negative close price."""
        with self.assertRaises(ValidationError) as cm:
            PriceData(
                date="2023-01-01",
                close=-100.0  # gt=0
            )
        self.assertIn("close", str(cm.exception))

    def test_technical_indicator_input_valid(self):
        """Test TechnicalIndicatorInput with valid data."""
        price_data = [
            PriceData(date="2023-01-01", close=100.0),
            PriceData(date="2023-01-02", close=101.0)
        ]
        data = TechnicalIndicatorInput(
            ticker="AAPL",
            price_data=price_data,
            indicators=["SMA"]
        )
        self.assertEqual(data.ticker, "AAPL")
        # Should sort price_data by date
        self.assertEqual(data.price_data[0].date, "2023-01-01")

    def test_technical_indicator_input_empty_price_data(self):
        """Test TechnicalIndicatorInput with empty price_data."""
        with self.assertRaises(ValidationError) as cm:
            TechnicalIndicatorInput(
                ticker="AAPL",
                price_data=[],  # min_items=1
                indicators=["SMA"]
            )
        self.assertIn("min_items", str(cm.exception))

    def test_technical_indicator_input_unsorted_price_data(self):
        """Test TechnicalIndicatorInput sorts price_data by date."""
        price_data = [
            PriceData(date="2023-01-02", close=101.0),
            PriceData(date="2023-01-01", close=100.0)
        ]
        data = TechnicalIndicatorInput(
            ticker="AAPL",
            price_data=price_data,
            indicators=["SMA"]
        )
        # Should be sorted
        self.assertEqual(data.price_data[0].date, "2023-01-01")
        self.assertEqual(data.price_data[1].date, "2023-01-02")


if __name__ == "__main__":
    unittest.main()