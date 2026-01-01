import time
from MyCFATool.core.database import db_manager
from MyCFATool.domain.repositories.financial_data_repository import FinancialDataRepository
from MyCFATool.analytics.technicals import TechnicalAnalyzer
from MyCFATool.analytics.forecasting import Forecasting

def benchmark_queries():
    repo = FinancialDataRepository()
    analyzer = TechnicalAnalyzer()
    forecaster = Forecasting('MyCFATool/database/database.db')

    # Benchmark historical prices query
    start = time.time()
    prices = repo.get_historical_prices('AAPL', limit=1000)
    end = time.time()
    print(f"Historical prices query: {end - start:.4f} seconds, records: {len(prices)}")

    # Benchmark technical indicator calculation
    start = time.time()
    ma = analyzer.compute_moving_averages('AAPL', None)
    end = time.time()
    print(f"Moving averages calc: {end - start:.4f} seconds")

    # Benchmark forecast
    start = time.time()
    forecast = forecaster.arima_forecast('AAPL', target='price', forecast_periods=12)
    end = time.time()
    print(f"ARIMA forecast: {end - start:.4f} seconds")

    # Benchmark batch insert simulation (if data available)
    # Since no new data, skip

    print("Performance test completed")

if __name__ == "__main__":
    benchmark_queries()