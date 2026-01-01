import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
from functools import lru_cache
import logging

from ..repositories.financial_data_repository import FinancialDataRepository


class TechnicalAnalysisService:
    """Service for technical analysis computations using FinancialDataRepository."""

    def __init__(self):
        self.repo = FinancialDataRepository()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.operation_count = 0
        self.failure_count = 0

    @lru_cache(maxsize=None)
    def compute_moving_averages(self, ticker_symbol: str, fiscal_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Compute Simple Moving Average (SMA) and Exponential Moving Average (EMA) for 20-day period.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str, optional): Fiscal date in 'YYYY-MM-DD' format. If None, use all available data.

        Returns:
            dict or None: {'sma_20': float, 'ema_20': float, 'signal': str, 'interpretation': str} or None if insufficient data.
        """
        try:
            prices = self.repo.get_historical_prices_ordered(ticker_symbol, order='asc')
            if len(prices) < 20:
                self.logger.warning(f"[{ticker_symbol}] compute_moving_averages: Insufficient price data (less than 20)")
                return None

            prices_df = pd.DataFrame(prices)
            prices_df['trade_date'] = pd.to_datetime(prices_df['trade_date'])

            # Compute SMA and EMA
            sma_20 = prices_df['close'].rolling(window=20).mean().iloc[-1]
            ema_20 = prices_df['close'].ewm(span=20).mean().iloc[-1]

            current_price = prices_df['close'].iloc[-1]

            # Signal
            if current_price > sma_20 and current_price > ema_20:
                signal = 'bullish'
            elif current_price < sma_20 and current_price < ema_20:
                signal = 'bearish'
            else:
                signal = 'neutral'

            interpretation = f"Price is {signal} relative to moving averages."

            self.operation_count += 1
            self.logger.info(f"[{ticker_symbol}] compute_moving_averages succeeded: sma_20={sma_20:.2f}, ema_20={ema_20:.2f}, signal={signal}")
            return {
                'sma_20': sma_20,
                'ema_20': ema_20,
                'signal': signal,
                'interpretation': interpretation
            }
        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"[{ticker_symbol}] compute_moving_averages failed: {str(e)}. Inputs: ticker={ticker_symbol}, fiscal_date={fiscal_date}")
            return None

    def compute_stochastic_oscillator(self, ticker_symbol: str, fiscal_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Compute Stochastic Oscillator (%K and %D, 14-day).

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str, optional): Fiscal date in 'YYYY-MM-DD' format. If None, use all available data.

        Returns:
            dict or None: {'k_percent': float, 'd_percent': float, 'signal': str, 'interpretation': str} or None if insufficient data.
        """
        prices = self.repo.get_historical_prices_ordered(ticker_symbol, order='asc')
        if len(prices) < 14:
            return None

        prices_df = pd.DataFrame(prices)
        prices_df['trade_date'] = pd.to_datetime(prices_df['trade_date'])

        # High and Low for 14 days
        high_14 = prices_df['high'].rolling(window=14).max()
        low_14 = prices_df['low'].rolling(window=14).min()

        k_percent = 100 * (prices_df['close'] - low_14) / (high_14 - low_14)
        d_percent = k_percent.rolling(window=3).mean()

        latest_k = k_percent.iloc[-1]
        latest_d = d_percent.iloc[-1]

        if latest_k > 80 and latest_d > 80:
            signal = 'overbought'
        elif latest_k < 20 and latest_d < 20:
            signal = 'oversold'
        else:
            signal = 'neutral'

        interpretation = f"Stochastic oscillator indicates {signal} conditions."

        return {
            'k_percent': latest_k,
            'd_percent': latest_d,
            'signal': signal,
            'interpretation': interpretation
        }

    def compute_williams_r(self, ticker_symbol: str, fiscal_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Compute Williams %R (14-day).

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str, optional): Fiscal date in 'YYYY-MM-DD' format. If None, use all available data.

        Returns:
            dict or None: {'williams_r': float, 'signal': str, 'interpretation': str} or None if insufficient data.
        """
        prices = self.repo.get_historical_prices_ordered(ticker_symbol, order='asc')
        if len(prices) < 14:
            return None

        prices_df = pd.DataFrame(prices)
        prices_df['trade_date'] = pd.to_datetime(prices_df['trade_date'])

        high_14 = prices_df['high'].rolling(window=14).max()
        low_14 = prices_df['low'].rolling(window=14).min()

        williams_r = -100 * (high_14 - prices_df['close']) / (high_14 - low_14)

        latest_r = williams_r.iloc[-1]

        if latest_r > -20:
            signal = 'overbought'
        elif latest_r < -80:
            signal = 'oversold'
        else:
            signal = 'neutral'

        interpretation = f"Williams %R indicates {signal} conditions."

        return {
            'williams_r': latest_r,
            'signal': signal,
            'interpretation': interpretation
        }

    def compute_ichimoku_cloud(self, ticker_symbol: str, fiscal_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Compute Ichimoku Cloud components (Tenkan-sen, Kijun-sen, Senkou Span A, Senkou Span B).

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str, optional): Fiscal date in 'YYYY-MM-DD' format. If None, use all available data.

        Returns:
            dict or None: {'tenkan_sen': float, 'kijun_sen': float, 'senkou_a': float, 'senkou_b': float, 'signal': str, 'interpretation': str} or None if insufficient data.
        """
        prices = self.repo.get_historical_prices_ordered(ticker_symbol, order='asc')
        if len(prices) < 52:
            return None

        prices_df = pd.DataFrame(prices)
        prices_df['trade_date'] = pd.to_datetime(prices_df['trade_date'])

        # Tenkan-sen (Conversion Line): (9-period high + 9-period low) / 2
        tenkan_high = prices_df['high'].rolling(window=9).max()
        tenkan_low = prices_df['low'].rolling(window=9).min()
        tenkan_sen = (tenkan_high + tenkan_low) / 2

        # Kijun-sen (Base Line): (26-period high + 26-period low) / 2
        kijun_high = prices_df['high'].rolling(window=26).max()
        kijun_low = prices_df['low'].rolling(window=26).min()
        kijun_sen = (kijun_high + kijun_low) / 2

        # Senkou Span A (Leading Span A): (Tenkan-sen + Kijun-sen) / 2, plotted 26 periods ahead
        senkou_a = (tenkan_sen + kijun_sen) / 2

        # Senkou Span B (Leading Span B): (52-period high + 52-period low) / 2, plotted 26 periods ahead
        senkou_high = prices_df['high'].rolling(window=52).max()
        senkou_low = prices_df['low'].rolling(window=52).min()
        senkou_b = (senkou_high + senkou_low) / 2

        # Shift Senkou spans 26 periods ahead
        senkou_a_shifted = senkou_a.shift(-26)
        senkou_b_shifted = senkou_b.shift(-26)

        # Latest values
        latest_tenkan = tenkan_sen.iloc[-1]
        latest_kijun = kijun_sen.iloc[-1]
        latest_senkou_a = senkou_a_shifted.iloc[-1] if not np.isnan(senkou_a_shifted.iloc[-1]) else None
        latest_senkou_b = senkou_b_shifted.iloc[-1] if not np.isnan(senkou_b_shifted.iloc[-1]) else None

        current_price = prices_df['close'].iloc[-1]

        signal = 'neutral'
        if latest_senkou_a and latest_senkou_b:
            if current_price > max(latest_senkou_a, latest_senkou_b):
                signal = 'bullish'
            elif current_price < min(latest_senkou_a, latest_senkou_b):
                signal = 'bearish'

        interpretation = f"Ichimoku Cloud indicates {signal} momentum."

        return {
            'tenkan_sen': latest_tenkan,
            'kijun_sen': latest_kijun,
            'senkou_a': latest_senkou_a,
            'senkou_b': latest_senkou_b,
            'signal': signal,
            'interpretation': interpretation
        }

    def compute_rsi(self, ticker_symbol: str, fiscal_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Compute Relative Strength Index (RSI, 14-day).

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str, optional): Fiscal date in 'YYYY-MM-DD' format. If None, use all available data.

        Returns:
            dict or None: {'rsi': float, 'signal': str, 'interpretation': str} or None if insufficient data.
        """
        prices = self.repo.get_historical_prices_ordered(ticker_symbol, order='asc')
        if len(prices) < 15:
            return None

        prices_df = pd.DataFrame(prices)
        prices_df['trade_date'] = pd.to_datetime(prices_df['trade_date'])

        # Calculate daily returns
        prices_df['change'] = prices_df['close'].diff()

        # Calculate gains and losses
        prices_df['gain'] = prices_df['change'].where(prices_df['change'] > 0, 0)
        prices_df['loss'] = -prices_df['change'].where(prices_df['change'] < 0, 0)

        # Calculate average gain and loss over 14 periods
        avg_gain = prices_df['gain'].rolling(window=14).mean()
        avg_loss = prices_df['loss'].rolling(window=14).mean()

        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        latest_rsi = rsi.iloc[-1]

        if latest_rsi > 70:
            signal = 'overbought'
        elif latest_rsi < 30:
            signal = 'oversold'
        else:
            signal = 'neutral'

        interpretation = f"RSI indicates {signal} conditions."

        return {
            'rsi': latest_rsi,
            'signal': signal,
            'interpretation': interpretation
        }

    def compute_macd(self, ticker_symbol: str, fiscal_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Compute MACD (Moving Average Convergence Divergence).

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str, optional): Fiscal date in 'YYYY-MM-DD' format. If None, use all available data.

        Returns:
            dict or None: {'macd': float, 'signal': float, 'histogram': float, 'trend_signal': str, 'interpretation': str} or None if insufficient data.
        """
        prices = self.repo.get_historical_prices_ordered(ticker_symbol, order='asc')
        if len(prices) < 26:
            return None

        prices_df = pd.DataFrame(prices)
        prices_df['trade_date'] = pd.to_datetime(prices_df['trade_date'])

        # Calculate EMAs
        ema12 = prices_df['close'].ewm(span=12).mean()
        ema26 = prices_df['close'].ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()
        histogram = macd - signal

        latest_macd = macd.iloc[-1]
        latest_signal = signal.iloc[-1]
        latest_histogram = histogram.iloc[-1]

        # Signal: if MACD > Signal, bullish; else bearish
        trend_signal = 'bullish' if latest_macd > latest_signal else 'bearish'

        interpretation = f"MACD indicates {trend_signal} momentum."

        return {
            'macd': latest_macd,
            'signal': latest_signal,
            'histogram': latest_histogram,
            'trend_signal': trend_signal,
            'interpretation': interpretation
        }

    def compute_bollinger_bands(self, ticker_symbol: str, fiscal_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Compute Bollinger Bands (20-day, 2 std dev).

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str, optional): Fiscal date in 'YYYY-MM-DD' format. If None, use all available data.

        Returns:
            dict or None: {'middle': float, 'upper': float, 'lower': float, 'signal': str, 'interpretation': str} or None if insufficient data.
        """
        prices = self.repo.get_historical_prices_ordered(ticker_symbol, order='asc')
        if len(prices) < 20:
            return None

        prices_df = pd.DataFrame(prices)
        prices_df['trade_date'] = pd.to_datetime(prices_df['trade_date'])

        # Calculate SMA and std
        sma = prices_df['close'].rolling(window=20).mean()
        std = prices_df['close'].rolling(window=20).std()

        upper = sma + (std * 2)
        lower = sma - (std * 2)

        latest_middle = sma.iloc[-1]
        latest_upper = upper.iloc[-1]
        latest_lower = lower.iloc[-1]
        current_price = prices_df['close'].iloc[-1]

        if current_price > latest_upper:
            signal = 'overbought'
        elif current_price < latest_lower:
            signal = 'oversold'
        else:
            signal = 'neutral'

        interpretation = f"Bollinger Bands indicate {signal} price action."

        return {
            'middle': latest_middle,
            'upper': latest_upper,
            'lower': latest_lower,
            'signal': signal,
            'interpretation': interpretation
        }

    def compute_roc(self, ticker_symbol: str, fiscal_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Compute Rate of Change (ROC, 10-day).

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str, optional): Fiscal date in 'YYYY-MM-DD' format. If None, use all available data.

        Returns:
            dict or None: {'roc': float, 'signal': str, 'interpretation': str} or None if insufficient data.
        """
        prices = self.repo.get_historical_prices_ordered(ticker_symbol, order='asc')
        if len(prices) < 11:
            return None

        prices_df = pd.DataFrame(prices)
        prices_df['trade_date'] = pd.to_datetime(prices_df['trade_date'])

        # Calculate ROC: (current - price_10_ago) / price_10_ago * 100
        roc = (prices_df['close'] - prices_df['close'].shift(10)) / prices_df['close'].shift(10) * 100

        latest_roc = roc.iloc[-1]

        if latest_roc > 0:
            signal = 'positive momentum'
        else:
            signal = 'negative momentum'

        interpretation = f"ROC indicates {signal}."

        return {
            'roc': latest_roc,
            'signal': signal,
            'interpretation': interpretation
        }

    def compute_obv(self, ticker_symbol: str, fiscal_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Compute On-Balance Volume (OBV).

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str, optional): Fiscal date in 'YYYY-MM-DD' format. If None, use all available data.

        Returns:
            dict or None: {'obv': float, 'signal': str, 'interpretation': str} or None if insufficient data.
        """
        prices = self.repo.get_historical_prices_ordered(ticker_symbol, order='asc')
        if len(prices) < 2:
            return None

        prices_df = pd.DataFrame(prices)
        prices_df['trade_date'] = pd.to_datetime(prices_df['trade_date'])

        # Calculate OBV
        obv = [0]  # Start with 0
        for i in range(1, len(prices_df)):
            volume = prices_df['volume'].iloc[i] if prices_df['volume'].iloc[i] is not None else 0
            if prices_df['close'].iloc[i] > prices_df['close'].iloc[i-1]:
                obv.append(obv[-1] + volume)
            elif prices_df['close'].iloc[i] < prices_df['close'].iloc[i-1]:
                obv.append(obv[-1] - volume)
            else:
                obv.append(obv[-1])

        prices_df['obv'] = obv

        latest_obv = obv[-1]

        # Signal based on trend (simple: if OBV > OBV 10 days ago, bullish)
        if len(prices_df) >= 11:
            prev_obv = prices_df['obv'].iloc[-11]
            if latest_obv > prev_obv:
                signal = 'bullish'
            elif latest_obv < prev_obv:
                signal = 'bearish'
            else:
                signal = 'neutral'
        else:
            signal = 'neutral'

        interpretation = f"OBV indicates {signal} volume flow."

        return {
            'obv': latest_obv,
            'signal': signal,
            'interpretation': interpretation
        }

    def compute_vroc(self, ticker_symbol: str, fiscal_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Compute Volume Rate of Change (VROC, 10-day).

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str, optional): Fiscal date in 'YYYY-MM-DD' format. If None, use all available data.

        Returns:
            dict or None: {'vroc': float, 'signal': str, 'interpretation': str} or None if insufficient data.
        """
        prices = self.repo.get_historical_prices_ordered(ticker_symbol, order='asc')
        if len(prices) < 11:
            return None

        prices_df = pd.DataFrame(prices)
        prices_df['trade_date'] = pd.to_datetime(prices_df['trade_date'])

        # Calculate VROC: (current_volume - volume_10_ago) / volume_10_ago * 100
        vroc = (prices_df['volume'] - prices_df['volume'].shift(10)) / prices_df['volume'].shift(10) * 100

        latest_vroc = vroc.iloc[-1]

        if latest_vroc > 0:
            signal = 'increasing volume'
        elif latest_vroc < 0:
            signal = 'decreasing volume'
        else:
            signal = 'neutral'

        interpretation = f"VROC indicates {signal}."

        return {
            'vroc': latest_vroc,
            'signal': signal,
            'interpretation': interpretation
        }

    def compute_atr(self, ticker_symbol: str, fiscal_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Compute Average True Range (ATR, 14-day).

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str, optional): Fiscal date in 'YYYY-MM-DD' format. If None, use all available data.

        Returns:
            dict or None: {'atr': float, 'signal': str, 'interpretation': str} or None if insufficient data.
        """
        prices = self.repo.get_historical_prices_ordered(ticker_symbol, order='asc')
        if len(prices) < 15:
            return None

        prices_df = pd.DataFrame(prices)
        prices_df['trade_date'] = pd.to_datetime(prices_df['trade_date'])

        # Calculate True Range
        prices_df['prev_close'] = prices_df['close'].shift(1)
        prices_df['tr'] = np.maximum(
            prices_df['high'] - prices_df['low'],
            np.maximum(
                np.abs(prices_df['high'] - prices_df['prev_close']),
                np.abs(prices_df['low'] - prices_df['prev_close'])
            )
        )

        # ATR as 14-day average of TR
        atr = prices_df['tr'].rolling(window=14).mean()

        latest_atr = atr.iloc[-1]

        # Signal based on volatility: if ATR > average ATR, high volatility
        avg_atr = atr.mean()
        if latest_atr > avg_atr:
            signal = 'high volatility'
        elif latest_atr < avg_atr:
            signal = 'low volatility'
        else:
            signal = 'normal volatility'

        interpretation = f"ATR indicates {signal}."

        return {
            'atr': latest_atr,
            'signal': signal,
            'interpretation': interpretation
        }

    def compute_adx(self, ticker_symbol: str, fiscal_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Compute Average Directional Index (ADX, 14-day).

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str, optional): Fiscal date in 'YYYY-MM-DD' format. If None, use all available data.

        Returns:
            dict or None: {'adx': float, 'plus_di': float, 'minus_di': float, 'signal': str, 'interpretation': str} or None if insufficient data.
        """
        prices = self.repo.get_historical_prices_ordered(ticker_symbol, order='asc')
        if len(prices) < 29:
            return None

        prices_df = pd.DataFrame(prices)
        prices_df['trade_date'] = pd.to_datetime(prices_df['trade_date'])

        # Calculate True Range
        prices_df['prev_close'] = prices_df['close'].shift(1)
        prices_df['tr'] = np.maximum(
            prices_df['high'] - prices_df['low'],
            np.maximum(
                np.abs(prices_df['high'] - prices_df['prev_close']),
                np.abs(prices_df['low'] - prices_df['prev_close'])
            )
        )

        # Directional Movement
        prices_df['prev_high'] = prices_df['high'].shift(1)
        prices_df['prev_low'] = prices_df['low'].shift(1)
        prices_df['plus_dm'] = np.where(
            (prices_df['high'] - prices_df['prev_high']) > (prices_df['prev_low'] - prices_df['low']),
            np.maximum(prices_df['high'] - prices_df['prev_high'], 0),
            0
        )
        prices_df['minus_dm'] = np.where(
            (prices_df['prev_low'] - prices_df['low']) > (prices_df['high'] - prices_df['prev_high']),
            np.maximum(prices_df['prev_low'] - prices_df['low'], 0),
            0
        )

        # Smoothed averages (Wilder's smoothing)
        window = 14
        prices_df['atr'] = prices_df['tr'].ewm(alpha=1/window).mean()
        prices_df['plus_di'] = (prices_df['plus_dm'].ewm(alpha=1/window).mean() / prices_df['atr']) * 100
        prices_df['minus_di'] = (prices_df['minus_dm'].ewm(alpha=1/window).mean() / prices_df['atr']) * 100

        # DX
        prices_df['dx'] = (np.abs(prices_df['plus_di'] - prices_df['minus_di']) / (prices_df['plus_di'] + prices_df['minus_di'])) * 100

        # ADX
        prices_df['adx'] = prices_df['dx'].ewm(alpha=1/window).mean()

        latest_adx = prices_df['adx'].iloc[-1]
        latest_plus_di = prices_df['plus_di'].iloc[-1]
        latest_minus_di = prices_df['minus_di'].iloc[-1]

        # Signal
        if latest_adx > 25:
            trend_strength = 'strong trend'
        elif latest_adx < 20:
            trend_strength = 'weak trend'
        else:
            trend_strength = 'moderate trend'

        if latest_plus_di > latest_minus_di:
            direction = 'upward'
        elif latest_minus_di > latest_plus_di:
            direction = 'downward'
        else:
            direction = 'sideways'

        signal = f"{trend_strength}, {direction}"

        interpretation = f"ADX indicates {signal}."

        return {
            'adx': latest_adx,
            'plus_di': latest_plus_di,
            'minus_di': latest_minus_di,
            'signal': signal,
            'interpretation': interpretation
        }

    def detect_doji(self, ticker_symbol: str, fiscal_date: str) -> Optional[Dict[str, Any]]:
        """
        Detect Doji candlestick pattern.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format.

        Returns:
            dict or None: {'pattern_detected': bool, 'signal': str, 'strength': float, 'interpretation': str} or None if insufficient data.
        """
        prices = self.repo.get_historical_prices_ordered(ticker_symbol, order='desc', up_to_date=fiscal_date, limit=1)
        if len(prices) < 1:
            return None

        price = prices[0]
        open_price = price['open']
        high = price['high']
        low = price['low']
        close = price['close']

        if open_price is None or high is None or low is None or close is None:
            return None

        body = abs(close - open_price)
        range_size = high - low

        if range_size == 0:
            pattern_detected = False
            strength = 0
        else:
            body_ratio = body / range_size
            pattern_detected = body_ratio < 0.05  # Threshold for Doji
            strength = 1 - body_ratio if pattern_detected else 0

        if pattern_detected:
            signal = 'indecision'
            interpretation = f"Doji pattern detected with strength {strength:.2f}, indicating market indecision."
        else:
            signal = 'neutral'
            interpretation = "No Doji pattern detected."

        return {
            'pattern_detected': pattern_detected,
            'signal': signal,
            'strength': strength,
            'interpretation': interpretation
        }

    def detect_engulfing(self, ticker_symbol: str, fiscal_date: str) -> Optional[Dict[str, Any]]:
        """
        Detect Bullish or Bearish Engulfing candlestick pattern.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format.

        Returns:
            dict or None: {'pattern_detected': bool, 'signal': str, 'strength': float, 'interpretation': str} or None if insufficient data.
        """
        prices = self.repo.get_historical_prices_ordered(ticker_symbol, order='desc', up_to_date=fiscal_date, limit=2)
        if len(prices) < 2:
            return None

        current = prices[0]
        previous = prices[1]

        curr_open = current['open']
        curr_high = current['high']
        curr_low = current['low']
        curr_close = current['close']

        prev_open = previous['open']
        prev_high = previous['high']
        prev_low = previous['low']
        prev_close = previous['close']

        if (curr_open is None or curr_high is None or curr_low is None or curr_close is None or
            prev_open is None or prev_high is None or prev_low is None or prev_close is None):
            return None

        curr_body = abs(curr_close - curr_open)
        prev_body = abs(prev_close - prev_open)

        pattern_detected = False
        signal = 'neutral'
        strength = 0

        if prev_body > 0:
            if curr_open <= prev_close and curr_close >= prev_open and curr_close > prev_close:
                # Bullish engulfing
                pattern_detected = True
                signal = 'bullish'
                strength = curr_body / prev_body
            elif curr_open >= prev_close and curr_close <= prev_open and curr_close < prev_close:
                # Bearish engulfing
                pattern_detected = True
                signal = 'bearish'
                strength = curr_body / prev_body

        if pattern_detected:
            interpretation = f"{signal.capitalize()} engulfing pattern detected with strength {strength:.2f}."
        else:
            interpretation = "No engulfing pattern detected."

        return {
            'pattern_detected': pattern_detected,
            'signal': signal,
            'strength': strength,
            'interpretation': interpretation
        }

    def detect_hammer(self, ticker_symbol: str, fiscal_date: str) -> Optional[Dict[str, Any]]:
        """
        Detect Hammer candlestick pattern (bullish reversal).

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format.

        Returns:
            dict or None: {'pattern_detected': bool, 'signal': str, 'strength': float, 'interpretation': str} or None if insufficient data.
        """
        prices = self.repo.get_historical_prices_ordered(ticker_symbol, order='desc', up_to_date=fiscal_date, limit=1)
        if len(prices) < 1:
            return None

        price = prices[0]
        open_price = price['open']
        high = price['high']
        low = price['low']
        close = price['close']

        if open_price is None or high is None or low is None or close is None:
            return None

        body = abs(close - open_price)
        range_size = high - low

        if range_size == 0 or body == 0:
            pattern_detected = False
            strength = 0
        else:
            upper_wick = high - max(open_price, close)
            lower_wick = min(open_price, close) - low
            body_ratio = body / range_size
            lower_wick_ratio = lower_wick / range_size

            # Hammer: small body, long lower wick (at least 2x body), small upper wick (less than body)
            pattern_detected = body_ratio < 0.3 and lower_wick_ratio > 0.5 and upper_wick < body
            strength = lower_wick_ratio if pattern_detected else 0

        if pattern_detected:
            signal = 'bullish reversal'
            interpretation = f"Hammer pattern detected with strength {strength:.2f}, indicating potential bullish reversal."
        else:
            signal = 'neutral'
            interpretation = "No Hammer pattern detected."

        return {
            'pattern_detected': pattern_detected,
            'signal': signal,
            'strength': strength,
            'interpretation': interpretation
        }

    def detect_shooting_star(self, ticker_symbol: str, fiscal_date: str) -> Optional[Dict[str, Any]]:
        """
        Detect Shooting Star candlestick pattern (bearish reversal).

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format.

        Returns:
            dict or None: {'pattern_detected': bool, 'signal': str, 'strength': float, 'interpretation': str} or None if insufficient data.
        """
        prices = self.repo.get_historical_prices_ordered(ticker_symbol, order='desc', up_to_date=fiscal_date, limit=1)
        if len(prices) < 1:
            return None

        price = prices[0]
        open_price = price['open']
        high = price['high']
        low = price['low']
        close = price['close']

        if open_price is None or high is None or low is None or close is None:
            return None

        body = abs(close - open_price)
        range_size = high - low

        if range_size == 0 or body == 0:
            pattern_detected = False
            strength = 0
        else:
            upper_wick = high - max(open_price, close)
            lower_wick = min(open_price, close) - low
            body_ratio = body / range_size
            upper_wick_ratio = upper_wick / range_size

            # Shooting Star: small body, long upper wick (at least 2x body), small lower wick (less than body)
            pattern_detected = body_ratio < 0.3 and upper_wick_ratio > 0.5 and lower_wick < body
            strength = upper_wick_ratio if pattern_detected else 0

        if pattern_detected:
            signal = 'bearish reversal'
            interpretation = f"Shooting Star pattern detected with strength {strength:.2f}, indicating potential bearish reversal."
        else:
            signal = 'neutral'
            interpretation = "No Shooting Star pattern detected."

        return {
            'pattern_detected': pattern_detected,
            'signal': signal,
            'strength': strength,
            'interpretation': interpretation
        }