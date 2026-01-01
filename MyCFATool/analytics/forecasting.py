import pandas as pd
import sqlite3
import json
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
import numpy as np
from datetime import datetime, timedelta
from functools import lru_cache

class Forecasting:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)

    def _load_price_data(self, ticker_symbol, periods=100):
        """
        Load historical price data for the given ticker.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            periods (int): Number of historical periods to load.

        Returns:
            pd.DataFrame or None: DataFrame with 'date' and 'price' columns, or None if insufficient data.
        """
        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        prices = self.conn.execute("""
            SELECT trade_date, close FROM historical_price
            WHERE ticker_id = ?
            ORDER BY trade_date DESC
            LIMIT ?
        """, (ticker_id, periods)).fetchall()

        if len(prices) < 10:  # Minimum data required
            return None

        df = pd.DataFrame(prices, columns=['date', 'price'])
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        df['price'] = df['price'].interpolate(method='linear').fillna(method='bfill').fillna(method='ffill')
        return df

    def _load_ratio_data(self, ticker_symbol, ratio_method, period_type='annual', periods=20):
        """
        Load historical ratio data by computing ratios for multiple fiscal dates.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            ratio_method (str): Method name from RatioValidator (e.g., 'compute_return_on_equity').
            period_type (str): 'annual' or 'quarterly'.
            periods (int): Number of historical periods to load.

        Returns:
            pd.DataFrame or None: DataFrame with 'date' and 'ratio' columns, or None if insufficient data.
        """
        from .validation import RatioValidator  # Import here to avoid circular import
        validator = RatioValidator(self.db_path)

        ticker_id = self.conn.execute("SELECT ticker_id FROM ticker WHERE symbol = ?", (ticker_symbol,)).fetchone()
        if not ticker_id:
            return None
        ticker_id = ticker_id[0]

        # Get fiscal dates
        fiscal_dates = self.conn.execute("""
            SELECT fiscal_date FROM balance_sheet
            WHERE ticker_id = ? AND period_type = ?
            ORDER BY fiscal_date DESC
            LIMIT ?
        """, (ticker_id, period_type, periods)).fetchall()

        if len(fiscal_dates) < 5:  # Minimum data required
            return None

        data = []
        for (fiscal_date,) in fiscal_dates:
            ratio = getattr(validator, ratio_method)(ticker_symbol, period_type, fiscal_date)
            if ratio is not None:
                data.append({'date': pd.to_datetime(fiscal_date), 'ratio': ratio})

        if len(data) < 5:
            return None

        df = pd.DataFrame(data).sort_values('date').reset_index(drop=True)
        df['ratio'] = df['ratio'].interpolate(method='linear').fillna(method='bfill').fillna(method='ffill')
        return df

    @lru_cache(maxsize=None)
    def arima_forecast(self, ticker_symbol, target='price', ratio_method=None, period_type='annual', forecast_periods=12):
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
            model = ARIMA(series, order=(5,1,0))
            model_fit = model.fit()
            forecast = model_fit.forecast(steps=forecast_periods)
            conf_int = model_fit.get_forecast(steps=forecast_periods).conf_int()
            conf_int = conf_int.values.tolist()

            interpretation = f"ARIMA forecast for {target}: Next {forecast_periods} periods show {'increasing' if forecast.mean() > series.iloc[-1] else 'decreasing'} trend with confidence intervals."

            return {
                'forecasted_values': forecast.tolist(),
                'confidence_intervals': conf_int,
                'interpretation': interpretation
            }
        except Exception as e:
            return None

    @lru_cache(maxsize=None)
    def exponential_smoothing_forecast(self, ticker_symbol, target='price', ratio_method=None, period_type='annual', forecast_periods=12):
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

    @lru_cache(maxsize=None)
    def linear_regression_forecast(self, ticker_symbol, target='price', ratio_method=None, period_type='annual', forecast_periods=12):
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