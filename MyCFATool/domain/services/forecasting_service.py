import pandas as pd
import sqlite3  # Wait, no, remove sqlite3
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging
import signal

def _timeout_handler(signum, frame):
    raise TimeoutError("Forecasting operation timed out")

from ..repositories.financial_data_repository import FinancialDataRepository


class ForecastingService:
    """Service for time-series forecasting using FinancialDataRepository."""

    def __init__(self):
        self.repo = FinancialDataRepository()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.operation_count = 0
        self.failure_count = 0

    def _load_price_data(self, ticker_symbol: str, periods: int = 100) -> Optional[pd.DataFrame]:
        """
        Load historical price data for the given ticker.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            periods (int): Number of historical periods to load.

        Returns:
            pd.DataFrame or None: DataFrame with 'date' and 'price' columns, or None if insufficient data.
        """
        prices = self.repo.get_historical_prices_ordered(ticker_symbol, order='desc', limit=periods)
        if len(prices) < 10:
            return None

        df = pd.DataFrame(prices)
        df['date'] = pd.to_datetime(df['trade_date'])
        df['price'] = df['close']
        df = df.sort_values('date').reset_index(drop=True)
        # Enhanced data imputation: first try rolling mean, then linear interpolation, then forward/backward fill
        df['price'] = df['price'].fillna(df['price'].rolling(window=3, min_periods=1).mean())
        df['price'] = df['price'].interpolate(method='linear').fillna(method='bfill').fillna(method='ffill')
        return df

    def _load_ratio_data(self, ticker_symbol: str, ratio_method: str, period_type: str = 'annual', periods: int = 20) -> Optional[pd.DataFrame]:
        """
        Load historical ratio data by computing ratios for multiple fiscal dates.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            ratio_method (str): Method name from FundamentalAnalysisService (e.g., 'compute_return_on_equity').
            period_type (str): 'annual' or 'quarterly'.
            periods (int): Number of historical periods to load.

        Returns:
            pd.DataFrame or None: DataFrame with 'date' and 'ratio' columns, or None if insufficient data.
        """
        from .fundamental_analysis_service import FundamentalAnalysisService
        analyzer = FundamentalAnalysisService()

        # Get fiscal dates from balance_sheet
        # Since repo doesn't provide bulk dates, get last periods dates
        try:
            # Get latest balance sheet date
            latest_balance = None
            for i in range(periods):
                dt = datetime.now() - timedelta(days=i*365) if period_type == 'annual' else datetime.now() - timedelta(days=i*90)
                f_date = dt.isoformat()[:10]
                bal = self.repo.get_balance_sheet(ticker_symbol, period_type, f_date)
                if bal:
                    latest_balance = bal
                    break
            if not latest_balance:
                return None
            current_dt = datetime.fromisoformat(latest_balance['fiscal_date'])

            data = []
            for i in range(periods):
                dt = current_dt.replace(year=current_dt.year - i) if period_type == 'annual' else current_dt - timedelta(days=i*90)
                f_date = dt.isoformat()[:10]
                ratio = getattr(analyzer, ratio_method)(ticker_symbol, period_type, f_date)
                if ratio is not None and 'value' in ratio:
                    data.append({'date': pd.to_datetime(f_date), 'ratio': ratio['value']})

            if len(data) < 5:
                return None

            df = pd.DataFrame(data).sort_values('date').reset_index(drop=True)
            # Enhanced data imputation: first try rolling mean, then linear interpolation, then forward/backward fill
            df['ratio'] = df['ratio'].fillna(df['ratio'].rolling(window=3, min_periods=1).mean())
            df['ratio'] = df['ratio'].interpolate(method='linear').fillna(method='bfill').fillna(method='ffill')
            return df
        except ValueError:
            return None

    def arima_forecast(self, ticker_symbol: str, target: str = 'price', ratio_method: str = None, period_type: str = 'annual', forecast_periods: int = 12) -> Optional[Dict[str, Any]]:
        """
        Perform ARIMA forecasting on price data or key ratios.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            target (str): 'price' or 'ratio'.
            ratio_method (str): Ratio method if target='ratio'.
            period_type (str): 'annual' or 'quarterly'.
            forecast_periods (int): Number of periods to forecast.

        Returns:
            dict or None: {
                'forecasted_values': list,
                'confidence_intervals': list of [lower, upper],
                'interpretation': str
            } or None if insufficient data.
        """
        # Load data
        if target == 'price':
            df = self._load_price_data(ticker_symbol)
            series = df['price']
        elif target == 'ratio' and ratio_method:
            df = self._load_ratio_data(ticker_symbol, ratio_method, period_type)
            series = df['ratio']
        else:
            self.logger.warning(f"[{ticker_symbol}] arima_forecast: Invalid target or missing ratio_method")
            return None

        if df is None or len(series) < 10:
            self.logger.warning(f"[{ticker_symbol}] arima_forecast: Insufficient data for {target}")
            return None

        # Try ARIMA with timeout
        try:
            signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(30)  # 30 seconds timeout
            model = ARIMA(series, order=(5,1,0))
            model_fit = model.fit()
            signal.alarm(0)  # Cancel alarm
            forecast = model_fit.forecast(steps=forecast_periods)
            conf_int = model_fit.get_forecast(steps=forecast_periods).conf_int()
            conf_int = conf_int.values.tolist()

            interpretation = f"ARIMA forecast for {target}: Next {forecast_periods} periods show {'increasing' if forecast.mean() > series.iloc[-1] else 'decreasing'} trend with confidence intervals."

            self.operation_count += 1
            self.logger.info(f"[{ticker_symbol}] arima_forecast succeeded with ARIMA: target={target}, forecast_periods={forecast_periods}")
            return {
                'forecasted_values': forecast.tolist(),
                'confidence_intervals': conf_int,
                'interpretation': interpretation
            }
        except (Exception, TimeoutError) as e:
            signal.alarm(0)
            self.logger.warning(f"[{ticker_symbol}] ARIMA failed, trying Linear Regression: {str(e)}")
            # Fallback to Linear Regression
            try:
                result = self.linear_regression_forecast(ticker_symbol, target, ratio_method, period_type, forecast_periods)
                if result:
                    self.operation_count += 1
                    self.logger.info(f"[{ticker_symbol}] arima_forecast succeeded with Linear Regression fallback: target={target}, forecast_periods={forecast_periods}")
                    return result
            except Exception as e2:
                self.logger.warning(f"[{ticker_symbol}] Linear Regression failed, trying Moving Average: {str(e2)}")
                # Fallback to Moving Average
                try:
                    result = self.moving_average_forecast(ticker_symbol, target, ratio_method, period_type, forecast_periods)
                    if result:
                        self.operation_count += 1
                        self.logger.info(f"[{ticker_symbol}] arima_forecast succeeded with Moving Average fallback: target={target}, forecast_periods={forecast_periods}")
                        return result
                except Exception as e3:
                    self.failure_count += 1
                    self.logger.error(f"[{ticker_symbol}] All forecasting methods failed: ARIMA {str(e)}, Linear Regression {str(e2)}, Moving Average {str(e3)}")
                    return None

    def exponential_smoothing_forecast(self, ticker_symbol: str, target: str = 'price', ratio_method: str = None, period_type: str = 'annual', forecast_periods: int = 12) -> Optional[Dict[str, Any]]:
        """
        Perform Exponential Smoothing forecasting on price data or key ratios.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            target (str): 'price' or 'ratio'.
            ratio_method (str): Ratio method if target='ratio'.
            period_type (str): 'annual' or 'quarterly'.
            forecast_periods (int): Number of periods to forecast.

        Returns:
            dict or None: {
                'forecasted_values': list,
                'interpretation': str
            } or None if insufficient data.
        """
        if target == 'price':
            df = self._load_price_data(ticker_symbol)
            series = df['price']
        elif target == 'ratio' and ratio_method:
            df = self._load_ratio_data(ticker_symbol, ratio_method, period_type)
            series = df['ratio']
        else:
            return None

        if df is None or len(series) < 10:
            return None

        try:
            model = ExponentialSmoothing(series, seasonal='add', seasonal_periods=4)
            model_fit = model.fit()
            forecast = model_fit.forecast(steps=forecast_periods)

            interpretation = f"Exponential Smoothing forecast for {target}: Next {forecast_periods} periods show {'increasing' if forecast.mean() > series.iloc[-1] else 'decreasing'} trend."

            return {
                'forecasted_values': forecast.tolist(),
                'interpretation': interpretation
            }
        except Exception as e:
            return None

    def linear_regression_forecast(self, ticker_symbol: str, target: str = 'price', ratio_method: str = None, period_type: str = 'annual', forecast_periods: int = 12) -> Optional[Dict[str, Any]]:
        """
        Perform Linear Regression forecasting on price data or key ratios.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            target (str): 'price' or 'ratio'.
            ratio_method (str): Ratio method if target='ratio'.
            period_type (str): 'annual' or 'quarterly'.
            forecast_periods (int): Number of periods to forecast.

        Returns:
            dict or None: {
                'forecasted_values': list,
                'interpretation': str
            } or None if insufficient data.
        """
        if target == 'price':
            df = self._load_price_data(ticker_symbol)
        elif target == 'ratio' and ratio_method:
            df = self._load_ratio_data(ticker_symbol, ratio_method, period_type)
        else:
            return None

        if df is None or len(df) < 10:
            return None

        df['time_index'] = np.arange(len(df))
        X = df[['time_index']]
        y = df['price'] if target == 'price' else df['ratio']

        model = LinearRegression()
        model.fit(X, y)

        future_indices = np.arange(len(df), len(df) + forecast_periods)
        forecast = model.predict(future_indices.reshape(-1, 1))

        interpretation = f"Linear Regression forecast for {target}: Trend slope is {model.coef_[0]:.4f}, next {forecast_periods} periods projected."

        return {
            'forecasted_values': forecast.tolist(),
            'interpretation': interpretation
        }

    def moving_average_forecast(self, ticker_symbol: str, target: str = 'price', ratio_method: str = None, period_type: str = 'annual', forecast_periods: int = 12, window_size: int = 5) -> Optional[Dict[str, Any]]:
        """
        Perform Moving Average forecasting on price data or key ratios.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            target (str): 'price' or 'ratio'.
            ratio_method (str): Ratio method if target='ratio'.
            period_type (str): 'annual' or 'quarterly'.
            forecast_periods (int): Number of periods to forecast.
            window_size (int): Window size for moving average.

        Returns:
            dict or None: {
                'forecasted_values': list,
                'interpretation': str
            } or None if insufficient data.
        """
        try:
            if target == 'price':
                df = self._load_price_data(ticker_symbol)
                series = df['price']
            elif target == 'ratio' and ratio_method:
                df = self._load_ratio_data(ticker_symbol, ratio_method, period_type)
                series = df['ratio']
            else:
                self.logger.warning(f"[{ticker_symbol}] moving_average_forecast: Invalid target or missing ratio_method")
                return None

            if df is None or len(series) < window_size:
                self.logger.warning(f"[{ticker_symbol}] moving_average_forecast: Insufficient data for {target}")
                return None

            # Forecast using the moving average of the last window_size values
            last_ma = series[-window_size:].mean()
            forecast = [last_ma] * forecast_periods

            interpretation = f"Moving Average ({window_size}) forecast for {target}: Next {forecast_periods} periods at {last_ma:.4f}"

            self.operation_count += 1
            self.logger.info(f"[{ticker_symbol}] moving_average_forecast succeeded: target={target}, forecast_periods={forecast_periods}, window_size={window_size}")
            return {
                'forecasted_values': forecast,
                'interpretation': interpretation
            }
        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"[{ticker_symbol}] moving_average_forecast failed: {str(e)}. Inputs: ticker={ticker_symbol}, target={target}, ratio_method={ratio_method}, period_type={period_type}, forecast_periods={forecast_periods}, window_size={window_size}")
            return None