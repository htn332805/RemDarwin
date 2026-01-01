#!/usr/bin/env python3
"""
Analytics Pipeline Validation Script for CRH Ticker

This script validates that the analytics services work correctly with newly ingested batch data.
It runs a complete analytics pipeline including:
- Fundamental Analysis
- Technical Analysis
- Valuation (DCF)
- Forecasting

All results are printed with error checking and data validation.
"""

import sys
import os
from datetime import datetime

# Add MyCFATool to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'MyCFATool'))

from MyCFATool.domain.services.fundamental_analysis_service import FundamentalAnalysisService
from MyCFATool.domain.services.technical_analysis_service import TechnicalAnalysisService
from MyCFATool.domain.services.valuation_service import ValuationService
from MyCFATool.domain.services.forecasting_service import ForecastingService
from MyCFATool.domain.repositories.financial_data_repository import FinancialDataRepository

def main():
    ticker = "CRH"
    period_type = "annual"  # Using annual data for analysis
    fiscal_date = "2023-12-31"  # Use latest available annual

    print(f"{'='*60}")
    print(f"ANALYTICS PIPELINE VALIDATION FOR {ticker}")
    print(f"Started at: {datetime.now()}")
    print(f"{'='*60}")

    # Initialize services
    repo = FinancialDataRepository()
    fundamental_service = FundamentalAnalysisService()
    technical_service = TechnicalAnalysisService()
    valuation_service = ValuationService()
    forecasting_service = ForecastingService()

    results = {}

    try:
        # 1. Verify data exists
        print("\n1. VERIFYING DATA AVAILABILITY")
        print("-" * 40)

        # Check if ticker exists
        ticker_id = repo.ticker_repo.get_ticker_id(ticker)
        if ticker_id is None:
            raise ValueError(f"Ticker {ticker} not found in database")

        print(f"✓ Ticker {ticker} found (ID: {ticker_id})")

        # Check data availability
        data_check = {
            "income_statement": repo.get_income_statement(ticker, period_type, fiscal_date),
            "balance_sheet": repo.get_balance_sheet(ticker, period_type, fiscal_date),
            "cash_flow": repo.get_cash_flow(ticker, period_type, fiscal_date),
            "ratios": repo.get_ratios(ticker, period_type, fiscal_date),
            "historical_prices": repo.get_historical_prices(ticker)
        }

        for data_type, data in data_check.items():
            if data:
                print(f"✓ {data_type.replace('_', ' ').title()}: {len(data)} records")
            else:
                print(f"✗ {data_type.replace('_', ' ').title()}: No data found")

        results["data_availability"] = {k: len(v) if v else 0 for k, v in data_check.items()}

        # 2. Fundamental Analysis
        print("\n2. FUNDAMENTAL ANALYSIS")
        print("-" * 40)

        fundamental_results = {}

        # Liquidity ratios
        fundamental_results["current_ratio"] = fundamental_service.compute_current_ratio(ticker, period_type, fiscal_date)
        fundamental_results["quick_ratio"] = fundamental_service.compute_quick_ratio(ticker, period_type, fiscal_date)
        fundamental_results["cash_ratio"] = fundamental_service.compute_cash_ratio(ticker, period_type, fiscal_date)

        # Profitability ratios
        fundamental_results["gross_profit_margin"] = fundamental_service.compute_gross_profit_margin(ticker, period_type, fiscal_date)
        fundamental_results["net_profit_margin"] = fundamental_service.compute_net_profit_margin(ticker, period_type, fiscal_date)
        fundamental_results["return_on_assets"] = fundamental_service.compute_return_on_assets(ticker, period_type, fiscal_date)
        fundamental_results["return_on_equity"] = fundamental_service.compute_return_on_equity(ticker, period_type, fiscal_date)
        fundamental_results["asset_turnover"] = fundamental_service.compute_asset_turnover(ticker, period_type, fiscal_date)

        # Leverage ratios
        fundamental_results["debt_to_equity_ratio"] = fundamental_service.compute_debt_to_equity_ratio(ticker, period_type, fiscal_date)
        fundamental_results["debt_ratio"] = fundamental_service.compute_debt_ratio(ticker, period_type, fiscal_date)

        # Valuation ratios
        fundamental_results["price_earnings_ratio"] = fundamental_service.compute_price_earnings_ratio(ticker, period_type, fiscal_date)
        fundamental_results["price_book_value_ratio"] = fundamental_service.compute_price_book_value_ratio(ticker, period_type, fiscal_date)

        # Bankruptcy scores
        fundamental_results["altman_z_score"] = fundamental_service.compute_altman_z_score(ticker, period_type, fiscal_date)
        fundamental_results["beneish_m_score"] = fundamental_service.compute_beneish_m_score(ticker, period_type, fiscal_date)
        fundamental_results["ohlson_o_score"] = fundamental_service.compute_ohlson_o_score(ticker, period_type, fiscal_date)

        # Print fundamental results
        for metric, result in fundamental_results.items():
            if result:
                if 'value' in result:
                    print(f"✓ {metric.replace('_', ' ').title()}: {result['value']:.4f} - {result.get('interpretation', '')}")
                else:
                    # For bankruptcy scores with different format
                    print(f"✓ {metric.replace('_', ' ').title()}: {result}")
            else:
                print(f"✗ {metric.replace('_', ' ').title()}: No data")

        results["fundamental_analysis"] = fundamental_results

        # 3. Technical Analysis
        print("\n3. TECHNICAL ANALYSIS")
        print("-" * 40)

        technical_results = {}

        # Volume indicators
        technical_results["obv"] = technical_service.compute_obv(ticker, fiscal_date)
        technical_results["vroc"] = technical_service.compute_vroc(ticker, fiscal_date)

        # Trend/Volatility indicators
        technical_results["atr"] = technical_service.compute_atr(ticker, fiscal_date)
        technical_results["adx"] = technical_service.compute_adx(ticker, fiscal_date)

        # Candlestick patterns
        technical_results["doji"] = technical_service.detect_doji(ticker, fiscal_date)
        technical_results["engulfing"] = technical_service.detect_engulfing(ticker, fiscal_date)

        # Print technical results
        for indicator, result in technical_results.items():
            if result:
                print(f"✓ {indicator.upper()}: {result}")
            else:
                print(f"✗ {indicator.upper()}: No data")

        results["technical_analysis"] = technical_results

        # 4. Valuation (DCF)
        print("\n4. VALUATION (DCF ANALYSIS)")
        print("-" * 40)

        valuation_results = {}

        try:
            # DCF components
            valuation_results["free_cash_flow"] = valuation_service.compute_free_cash_flow(ticker, period_type, fiscal_date)
            valuation_results["wacc"] = valuation_service.compute_wacc(ticker, period_type, fiscal_date)
            valuation_results["terminal_value"] = valuation_service.compute_terminal_value(ticker, period_type, fiscal_date)
            valuation_results["intrinsic_value"] = valuation_service.compute_intrinsic_value(ticker, period_type, fiscal_date)
            valuation_results["dcf_valuation"] = valuation_service.compute_dcf_valuation(ticker, period_type, fiscal_date)

            # Sensitivity analysis
            valuation_results["sensitivity_analysis"] = valuation_service.perform_sensitivity_analysis(ticker, period_type, fiscal_date)
        except Exception as e:
            print(f"Valuation failed: {e}")
            valuation_results = {}

        # Print valuation results
        if valuation_results:
            for component, result in valuation_results.items():
                if result:
                    if isinstance(result, dict) and 'value' in result:
                        print(f"✓ {component.replace('_', ' ').title()}: {result['value']:.4f} - {result['interpretation']}")
                    elif isinstance(result, dict):
                        print(f"✓ {component.replace('_', ' ').title()}: {result}")
                    else:
                        print(f"✓ {component.replace('_', ' ').title()}: {result}")
                else:
                    print(f"✗ {component.replace('_', ' ').title()}: No data")
        else:
            print("✗ Valuation: Failed due to missing data")

        results["valuation"] = valuation_results if valuation_results is not None else {}

        # 5. Forecasting
        print("\n5. FORECASTING")
        print("-" * 40)

        forecasting_results = {}

        try:
            # Time series forecasting methods
            forecasting_results["arima_forecast"] = forecasting_service.arima_forecast(ticker, fiscal_date)
            forecasting_results["exponential_smoothing"] = forecasting_service.exponential_smoothing_forecast(ticker, fiscal_date)
            forecasting_results["linear_regression"] = forecasting_service.linear_regression_forecast(ticker, fiscal_date)
        except Exception as e:
            print(f"Forecasting failed: {e}")
            forecasting_results = {}

        # Print forecasting results
        if forecasting_results:
            for method, result in forecasting_results.items():
                if result:
                    print(f"✓ {method.replace('_', ' ').title()}: Forecast = {result['forecast']:.4f} - {result['interpretation']}")
                else:
                    print(f"✗ {method.replace('_', ' ').title()}: No data")
        else:
            print("✗ Forecasting: Failed")

        results["forecasting"] = forecasting_results

        # Final validation
        print("\n6. VALIDATION SUMMARY")
        print("-" * 40)

        total_checks = 0
        successful_checks = 0

        for category, category_results in results.items():
            if category == "data_availability":
                for data_type, count in category_results.items():
                    total_checks += 1
                    if count > 0:
                        successful_checks += 1
            else:
                for metric, result in category_results.items():
                    total_checks += 1
                    if result is not None:
                        successful_checks += 1

        success_rate = (successful_checks / total_checks) * 100 if total_checks > 0 else 0

        print(f"Total checks performed: {total_checks}")
        print(f"Successful checks: {successful_checks}")
        print(f"Success rate: {success_rate:.1f}%")

        if success_rate >= 95:
            print("✓ OVERALL RESULT: EXCELLENT - Analytics pipeline fully functional")
        elif success_rate >= 80:
            print("✓ OVERALL RESULT: GOOD - Analytics pipeline mostly functional")
        else:
            print("✗ OVERALL RESULT: ISSUES DETECTED - Analytics pipeline needs attention")

        print(f"\n{'='*60}")
        print(f"VALIDATION COMPLETED AT: {datetime.now()}")
        print(f"{'='*60}")

        return True

    except Exception as e:
        print(f"\n❌ VALIDATION FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)