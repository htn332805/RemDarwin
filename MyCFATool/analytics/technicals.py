from MyCFATool.domain.services.technical_analysis_service import TechnicalAnalysisService

class TechnicalAnalyzer:
    def __init__(self):
        self.service = TechnicalAnalysisService()

    def compute_moving_averages(self, ticker_symbol, fiscal_date):
        """
        Compute Simple Moving Average (SMA) and Exponential Moving Average (EMA) for 20-day period.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format (optional for indicators).

        Returns:
            dict or None: {'sma_20': float, 'ema_20': float, 'signal': str, 'interpretation': str} or None if insufficient data.
        """
        return self.service.compute_moving_averages(ticker_symbol, fiscal_date)

    def compute_stochastic_oscillator(self, ticker_symbol, fiscal_date):
        """
        Compute Stochastic Oscillator (%K and %D, 14-day).

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format (optional for indicators).

        Returns:
            dict or None: {'k_percent': float, 'd_percent': float, 'signal': str, 'interpretation': str} or None if insufficient data.
        """
        return self.service.compute_stochastic_oscillator(ticker_symbol, fiscal_date)

    def compute_williams_r(self, ticker_symbol, fiscal_date):
        """
        Compute Williams %R (14-day).

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format (optional for indicators).

        Returns:
            dict or None: {'williams_r': float, 'signal': str, 'interpretation': str} or None if insufficient data.
        """
        return self.service.compute_williams_r(ticker_symbol, fiscal_date)

    def compute_ichimoku_cloud(self, ticker_symbol, fiscal_date):
        """
        Compute Ichimoku Cloud components (Tenkan-sen, Kijun-sen, Senkou Span A, Senkou Span B).

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format (optional for indicators).

        Returns:
            dict or None: {'tenkan_sen': float, 'kijun_sen': float, 'senkou_a': float, 'senkou_b': float, 'signal': str, 'interpretation': str} or None if insufficient data.
        """
        return self.service.compute_ichimoku_cloud(ticker_symbol, fiscal_date)

    def compute_rsi(self, ticker_symbol, fiscal_date):
        """
        Compute Relative Strength Index (RSI, 14-day).

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format (optional for indicators).

        Returns:
            dict or None: {'rsi': float, 'signal': str, 'interpretation': str} or None if insufficient data.
        """
        return self.service.compute_rsi(ticker_symbol, fiscal_date)

    def compute_macd(self, ticker_symbol, fiscal_date):
        """
        Compute MACD (Moving Average Convergence Divergence).

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format (optional for indicators).

        Returns:
            dict or None: {'macd': float, 'signal': float, 'histogram': float, 'trend_signal': str, 'interpretation': str} or None if insufficient data.
        """
        return self.service.compute_macd(ticker_symbol, fiscal_date)

    def compute_bollinger_bands(self, ticker_symbol, fiscal_date):
        """
        Compute Bollinger Bands (20-day, 2 std dev).

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format (optional for indicators).

        Returns:
            dict or None: {'middle': float, 'upper': float, 'lower': float, 'signal': str, 'interpretation': str} or None if insufficient data.
        """
        return self.service.compute_bollinger_bands(ticker_symbol, fiscal_date)

    def compute_roc(self, ticker_symbol, fiscal_date):
        """
        Compute Rate of Change (ROC, 10-day).

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format (optional for indicators).

        Returns:
            dict or None: {'roc': float, 'signal': str, 'interpretation': str} or None if insufficient data.
        """
        return self.service.compute_roc(ticker_symbol, fiscal_date)

    def compute_obv(self, ticker_symbol, fiscal_date):
        """
        Compute On-Balance Volume (OBV).

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format (optional for indicators).

        Returns:
            dict or None: {'obv': float, 'signal': str, 'interpretation': str} or None if insufficient data.
        """
        return self.service.compute_obv(ticker_symbol, fiscal_date)

    def compute_vroc(self, ticker_symbol, fiscal_date):
        """
        Compute Volume Rate of Change (VROC, 10-day).

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format (optional for indicators).

        Returns:
            dict or None: {'vroc': float, 'signal': str, 'interpretation': str} or None if insufficient data.
        """
        return self.service.compute_vroc(ticker_symbol, fiscal_date)

    def compute_atr(self, ticker_symbol, fiscal_date):
        """
        Compute Average True Range (ATR, 14-day).

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format (optional for indicators).

        Returns:
            dict or None: {'atr': float, 'signal': str, 'interpretation': str} or None if insufficient data.
        """
        return self.service.compute_atr(ticker_symbol, fiscal_date)

    def compute_adx(self, ticker_symbol, fiscal_date):
        """
        Compute Average Directional Index (ADX, 14-day).

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format (optional for indicators).

        Returns:
            dict or None: {'adx': float, 'plus_di': float, 'minus_di': float, 'signal': str, 'interpretation': str} or None if insufficient data.
        """
        return self.service.compute_adx(ticker_symbol, fiscal_date)

    def detect_doji(self, ticker_symbol, fiscal_date):
        """
        Detect Doji candlestick pattern.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format.

        Returns:
            dict or None: {'pattern_detected': bool, 'signal': str, 'strength': float, 'interpretation': str} or None if insufficient data.
        """
        return self.service.detect_doji(ticker_symbol, fiscal_date)

    def detect_engulfing(self, ticker_symbol, fiscal_date):
        """
        Detect Bullish or Bearish Engulfing candlestick pattern.

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format.

        Returns:
            dict or None: {'pattern_detected': bool, 'signal': str, 'strength': float, 'interpretation': str} or None if insufficient data.
        """
        return self.service.detect_engulfing(ticker_symbol, fiscal_date)

    def detect_hammer(self, ticker_symbol, fiscal_date):
        """
        Detect Hammer candlestick pattern (bullish reversal).

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format.

        Returns:
            dict or None: {'pattern_detected': bool, 'signal': str, 'strength': float, 'interpretation': str} or None if insufficient data.
        """
        return self.service.detect_hammer(ticker_symbol, fiscal_date)

    def detect_shooting_star(self, ticker_symbol, fiscal_date):
        """
        Detect Shooting Star candlestick pattern (bearish reversal).

        Args:
            ticker_symbol (str): The stock ticker symbol.
            fiscal_date (str): Fiscal date in 'YYYY-MM-DD' format.

        Returns:
            dict or None: {'pattern_detected': bool, 'signal': str, 'strength': float, 'interpretation': str} or None if insufficient data.
        """
        return self.service.detect_shooting_star(ticker_symbol, fiscal_date)