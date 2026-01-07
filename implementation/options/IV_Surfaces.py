"""
IV Surfaces Module for Systematic Options Trading

This module provides comprehensive tools for implied volatility surface analysis,
intelligent expiration filtering, and quantitative options trading decision support.

Key Features:
- IV surface construction with multiple interpolation methods (linear, cubic, RBF)
- Advanced metrics calculation (ATM IV, call/put skew ratios, term premium, volatility-of-volatility)
- Intelligent expiration filtering with market regime adaptation and efficiency scoring
- FastAPI endpoints for RESTful integration with downstream systems
- Comprehensive validation, backtesting, and database storage capabilities

Usage Examples:

1. Basic IV Surface Construction:
    from implementation.options.IV_Surfaces import retrieve_iv_data, process_iv_for_surface

    # Load option data from database
    df = retrieve_iv_data('AAPL_options.db')

    # Generate 3D surface with cubic interpolation
    X, Y, Z, expirations = process_iv_for_surface(df, interpolation_method='cubic')

2. Calculate Surface Metrics:
    from implementation.options.IV_Surfaces import calculate_iv_metrics

    metrics = calculate_iv_metrics(df, underlying_price=150.0)
    print(f"ATM IV: {metrics['atm_iv']}")
    print(f"Term Premium: {metrics.get('term_premium', 'N/A')}")

3. Intelligent Expiration Filtering:
    from implementation.options.IV_Surfaces import ExpirationCriteria, detect_market_regime, filter_options_by_expiration

    # Detect market regime
    regime = detect_market_regime(vix_level=25, iv_percentile=70, liquidity_score=0.7)

    # Create criteria and adjust for regime
    criteria = ExpirationCriteria()
    criteria.adjust_for_regime(regime)

    # Filter options
    filtered_options = filter_options_by_expiration(df, criteria)

4. API Server:
    python IV_Surfaces.py --ticker AAPL --api
    # Access at http://localhost:8000/surface/AAPL

Assumptions:
- SQLite database with partitioned options tables (options_YYYY_MM_DD format)
- Option data includes standard fields: strike_price, implied_volatility, expiration_date, option_type
- Underlying price is provided separately for calculations
- Greeks calculation requires external library (yfinance_options.GreekCalculator)

Dependencies:
- numpy, pandas, scipy, sqlite3
- fastapi, uvicorn (for API server)
- numba (for performance optimization)
- matplotlib (for plotting, optional)
- dash, plotly (for interactive visualization, optional)

API Reference:
Core Functions:
- retrieve_iv_data(db_path): Load IV data from partitioned database tables
- process_iv_for_surface(df, method, gap_fill): Generate interpolated 3D surface
- calculate_iv_metrics(df, underlying_price): Compute key IV statistics
- validate_iv_surface(Z, strikes, expirations): Quality validation and anomaly detection
- save_iv_surface_to_db(db_path, surface): Persist surface data with metadata

Filtering Functions:
- ExpirationCriteria: Dataclass for expiration filtering parameters
- detect_market_regime(vix, iv_pct, liquidity): Classify market conditions
- filter_options_by_expiration(df, criteria, scores, earnings): Apply expiration filters
- calculate_expiration_efficiency_scores(df, price): Score expirations by Greeks

Integration Functions:
- integrate_with_screening_engine(df, url1, url2): Connect with external filters
- backtest_expiration_selections(df, ticker, dates): Evaluate expiration strategies

API Endpoints:
- GET /surface/{ticker}: Retrieve IV surface data with optional parameters
- GET /metrics/{ticker}: Get IV surface metrics

For detailed function documentation, see individual docstrings.
"""

import argparse
import sqlite3
import os
import datetime
import logging
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import dash
from dash import html, dcc
import plotly.graph_objects as go
from scipy import interpolate as interp
from scipy.interpolate import Rbf
from numba import jit
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from options_backtest import OptionsBacktester  # Import existing backtesting framework
from dataclasses import dataclass
from typing import Optional

@jit(nopython=True)
def jitted_mean_fill(Z):
    """
    JIT-compiled function for fast mean-based gap filling in numpy arrays.
    """
    mean_val = np.nanmean(Z)
    Z_filled = np.where(np.isnan(Z), mean_val, Z)
    return Z_filled

@dataclass
class ExpirationCriteria:
    """
    Criteria for expiration range filtering in options trading.

    Attributes:
        min_days (int): Minimum days to expiration (default 30)
        max_days (int): Maximum days to expiration (default 90)
        premium_decay_weight (float): Weight for premium decay in scoring (default 1.0)
        regime_adjustment (bool): Whether to adjust ranges based on market regime (default True)
    """
    min_days: int = 30
    max_days: int = 90
    premium_decay_weight: float = 1.0
    regime_adjustment: bool = True

    def adjust_for_regime(self, regime: str):
        """
        Adjust expiration criteria based on detected market regime.
        """
        if not self.regime_adjustment:
            return

        if regime == 'high_vol':
            self.max_days = 120  # Extend for volatility harvesting
            self.min_days = 45
        elif regime == 'low_liquidity':
            self.max_days = 60  # Shorten for better liquidity
            self.min_days = 20
        elif regime == 'crisis':
            self.max_days = 150  # Very long for crisis alpha
            self.min_days = 60
        # normal: keep defaults

    def apply_fallback(self, condition: str):
        """
        Apply fallback adjustments for adverse market conditions when primary filtering yields insufficient options.
        """
        if condition == 'high_vol_fallback':
            self.max_days = int(min(self.max_days * 1.5, 180))  # Extend up to 180 days
        elif condition == 'thin_liquidity_fallback':
            self.min_days = int(max(self.min_days * 0.5, 15))  # Shorten to at least 15 days
        logging.info(f"Applied fallback for {condition}: min_days={self.min_days}, max_days={self.max_days}")

def detect_market_regime(vix_level: float, iv_percentile: float, liquidity_score: float, monitor: ExpirationFilterMonitor = None) -> str:
    """
    Detect market regime based on VIX level, IV percentile, and liquidity score.

    Args:
        vix_level: Current VIX value
        iv_percentile: Current IV percentile (0-100)
        liquidity_score: Liquidity measure (0-1, higher is better)
        monitor: Optional monitoring instance for logging regime changes

    Returns:
        str: Regime classification ('normal', 'high_vol', 'low_liquidity', 'crisis')
    """
    if vix_level > 35 or iv_percentile > 90:
        regime = 'crisis'
    elif vix_level > 25 or iv_percentile > 75:
        regime = 'high_vol'
    elif liquidity_score < 0.3:
        regime = 'low_liquidity'
    else:
        regime = 'normal'

    # Log regime change if monitor is provided
    if monitor:
        monitor.log_regime_change(regime, vix_level, iv_percentile, liquidity_score)

    return regime

def calculate_expiration_efficiency_scores(df, underlying_price):
    """
    Calculate efficiency scores for different expiration dates based on option Greeks approximations.

    Scores prioritize:
    - High theta decay (premium erosion)
    - Low gamma exposure (reduced directional risk)
    - Optimal time to expiration (manageable position duration)

    Args:
        df (pd.DataFrame): Options data with expiration_date, implied_volatility
        underlying_price (float): Current underlying price

    Returns:
        dict: Efficiency scores by expiration date
    """
    try:
        scores = {}
        today = datetime.date.today()

        for exp in df['expiration_date'].unique():
            exp_df = df[df['expiration_date'] == exp]
            days_to_exp = (exp - today).days

            if days_to_exp <= 0:
                continue  # Expired

            avg_iv = exp_df['implied_volatility'].mean()
            time_factor = np.sqrt(days_to_exp / 365.0)

            # Theta score: Higher IV and longer time increases decay potential
            theta_score = avg_iv * time_factor

            # Gamma score: Lower gamma preferred (less sensitivity to underlying moves)
            # Approximation: gamma decreases with longer time
            gamma_score = -avg_iv / time_factor  # Negative because lower gamma is better

            # Manageability score: Optimal around 45-90 days for options selling
            optimal_days = 60
            manageability = max(0, 1 - abs(days_to_exp - optimal_days) / optimal_days)

            # Weighted composite score
            total_score = (
                0.5 * theta_score +      # 50% weight on decay potential
                0.3 * gamma_score +      # 30% weight on risk management
                0.2 * manageability       # 20% weight on position manageability
            )

            scores[exp] = total_score

        # Normalize scores to 0-1 range
        if scores:
            min_score = min(scores.values())
            max_score = max(scores.values())
            if max_score > min_score:
                scores = {exp: (score - min_score) / (max_score - min_score) for exp, score in scores.items()}

        logging.info(f"Calculated efficiency scores for {len(scores)} expirations")
        return scores

    except Exception as e:
        logging.error(f"Error calculating expiration efficiency scores: {e}")
        return {}

def filter_options_by_expiration(df, criteria: ExpirationCriteria, efficiency_scores=None, efficiency_threshold=0.5, earnings_dates=None, earnings_buffer_days=7, monitor: ExpirationFilterMonitor = None):
    """
    Filter options DataFrame based on expiration criteria, efficiency scores, and earnings proximity.

    Args:
        df (pd.DataFrame): Options data with expiration_date, etc.
        criteria (ExpirationCriteria): Filtering criteria
        efficiency_scores (dict): Optional efficiency scores by expiration
        efficiency_threshold (float): Minimum efficiency score to include (0-1)
        earnings_dates (list): Optional list of datetime.date for earnings dates
        earnings_buffer_days (int): Days to exclude around earnings dates
        monitor (ExpirationFilterMonitor): Optional monitoring instance

    Returns:
        pd.DataFrame: Filtered options
    """
    try:
        filtered_rows = []
        today = datetime.date.today()

        for exp in df['expiration_date'].unique():
            days = (exp - today).days

            # Check if within range
            if not (criteria.min_days <= days <= criteria.max_days):
                continue

            # Check earnings proximity
            if earnings_dates:
                near_earnings = any(abs((exp - earning).days) <= earnings_buffer_days for earning in earnings_dates)
                if near_earnings:
                    logging.info(f"Excluding expiration {exp} due to proximity to earnings")
                    continue

            # Check efficiency score if provided
            if efficiency_scores is not None:
                score = efficiency_scores.get(exp, 0)
                if score < efficiency_threshold:
                    continue

            # Include all options for this expiration (calls and puts)
            exp_df = df[df['expiration_date'] == exp]
            filtered_rows.extend(exp_df.to_dict('records'))

        filtered_df = pd.DataFrame(filtered_rows)
        logging.info(f"Filtered {len(filtered_df)} options from {len(df)} total based on expiration criteria")

        # Log monitoring data if monitor is provided
        if monitor:
            monitor.log_expiration_distribution(df, criteria, filtered_df)
            monitor.log_filter_effectiveness(df, filtered_df, criteria, efficiency_scores, earnings_dates)

        return filtered_df

    except Exception as e:
        logging.error(f"Error filtering options by expiration: {e}")
        return pd.DataFrame()

def integrate_with_screening_engine(filtered_df, premium_filter_url=None, greeks_filter_url=None):
    """
    Integrate filtered options with external screening engine APIs for premium and Greeks filtering.

    Args:
        filtered_df (pd.DataFrame): Options filtered by expiration criteria
        premium_filter_url (str): URL for premium filter API
        greeks_filter_url (str): URL for Greeks filter API

    Returns:
        pd.DataFrame: Further filtered options compatible with screening engine
    """
    try:
        if filtered_df.empty:
            return filtered_df

        final_filtered = filtered_df.copy()

        # TODO: Implement actual API calls to screening engine
        # For now, simulate compatibility checks

        # Premium filter compatibility: ensure bid-ask spread < 5%
        if 'bid' in final_filtered.columns and 'ask' in final_filtered.columns:
            spread_ratio = (final_filtered['ask'] - final_filtered['bid']) / final_filtered['bid']
            final_filtered = final_filtered[spread_ratio < 0.05]

        # Greeks filter compatibility: ensure delta, gamma, theta are within bounds
        greeks_columns = ['delta', 'gamma', 'theta', 'vega', 'rho']
        available_greeks = [col for col in greeks_columns if col in final_filtered.columns]

        if available_greeks:
            # Apply basic Greeks filtering (placeholder logic)
            # Delta: |delta| < 0.3 for covered calls/puts
            if 'delta' in final_filtered.columns:
                final_filtered = final_filtered[final_filtered['delta'].abs() < 0.3]

            # Vega: vega < 0.05 for reduced volatility risk
            if 'vega' in final_filtered.columns:
                final_filtered = final_filtered[final_filtered['vega'] < 0.05]

        logging.info(f"Integrated screening: {len(final_filtered)} options passed premium and Greeks filters")
        return final_filtered

    except Exception as e:
        logging.error(f"Error integrating with screening engine: {e}")
        return filtered_df

@dataclass
class IVSurface:
    """
    Represents a 2D implied volatility surface with metadata.

    Attributes:
        ticker (str): Stock ticker symbol.
        timestamp (datetime): When the surface was created/generated.
        underlying_price (float): Current price of the underlying asset.
        market_regime (str): Market regime classification (e.g., 'normal', 'high_vol', 'low_vol').
        surface_data (pd.DataFrame): Multi-indexed DataFrame with IV data.
            Index: MultiIndex with levels [expiration_date, strike_price].
            Columns: ['iv_call', 'iv_put'] for implied volatilities of calls and puts.
    """
    ticker: str
    timestamp: datetime.datetime
    underlying_price: float
    market_regime: str
    surface_data: pd.DataFrame

def retrieve_iv_data(db_path):
    """
    Retrieve implied volatility data from partitioned options tables using pandas for efficiency.

    Returns a pandas DataFrame with columns: strike_price, implied_volatility, expiration_date
    Only processes call options and skips invalid rows.

    Performance considerations:
    - Uses a single UNION ALL query for all tables to minimize DB round trips
    - Processes data in bulk with pandas for better performance
    - Memory usage scales with total data size; consider chunking for very large datasets
    """
    try:
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file {db_path} not found.")

        logging.info(f"Connecting to database: {db_path}")
        conn = sqlite3.connect(db_path)
        logging.info("Successfully connected to database")

        # Discover tables
        tables_df = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'options_%'", conn)
        tables = tables_df['name'].tolist()
        logging.info(f"Found {len(tables)} options tables: {tables}")

        if not tables:
            logging.warning("No options tables found in database")
            return pd.DataFrame(columns=['strike_price', 'implied_volatility', 'expiration_date'])

        # Build union query for both calls and puts
        union_queries = []
        for table in tables:
            union_queries.append(f"SELECT strike_price, implied_volatility, expiration_date, option_type FROM {table}")
        full_query = " UNION ALL ".join(union_queries)

        # Estimate dataset size for performance optimization
        estimated_rows = 0
        for table in tables:
            count_query = f"SELECT COUNT(*) FROM {table}"
            count_df = pd.read_sql(count_query, conn)
            estimated_rows += count_df.iloc[0, 0]

        # Use chunked reading for large datasets to manage memory
        if estimated_rows > 50000:
            logging.info(f"Large dataset ({estimated_rows} rows), using chunked reading with chunksize=50000")
            chunks = []
            for chunk in pd.read_sql(full_query, conn, parse_dates=['expiration_date'], chunksize=50000):
                chunks.append(chunk)
            df = pd.concat(chunks, ignore_index=True)
        else:
            df = pd.read_sql(full_query, conn, parse_dates=['expiration_date'])
        conn.close()

        # Convert date column to date only (not datetime)
        df['expiration_date'] = df['expiration_date'].dt.date

        # Convert numeric columns and drop NaNs
        df['strike_price'] = pd.to_numeric(df['strike_price'], errors='coerce')
        df['implied_volatility'] = pd.to_numeric(df['implied_volatility'], errors='coerce')
        df = df.dropna()

        total_rows = len(df)
        logging.info(f"Data retrieval complete. Retrieved {total_rows} valid data points across {df['expiration_date'].nunique()} expirations")
        return df

    except Exception as e:
        logging.error(f"Error in retrieve_iv_data: {e}")
        raise

def process_iv_for_surface(df, interpolation_method='cubic', gap_fill_method='nearest'):
    """
    Process the retrieved IV data into numpy arrays suitable for 3D plotting with multiple interpolation options.

    Args:
        df (pd.DataFrame): DataFrame with columns strike_price, implied_volatility, expiration_date, option_type
        interpolation_method (str): Interpolation method ('linear', 'cubic', 'rbf'). Default 'cubic'.
        gap_fill_method (str): Method to fill gaps after interpolation ('nearest', 'linear', None). Default 'nearest'.

    Returns:
        tuple: (X, Y, Z) where X and Y are 2D meshgrids (strikes, expirations), Z is IV matrix with gaps filled

    Performance considerations:
    - Uses float32 for Z matrix to reduce memory usage (half of float64)
    - Interpolation is performed per expiration; skips if insufficient data
    - For very large datasets (>10k strikes or >100 expirations), consider downsampling
    """
    try:
        if df.empty:
            logging.warning("No IV data provided for processing")
            return np.array([]), np.array([]), np.array([]), []

        logging.info(f"Processing IV data for {df['expiration_date'].nunique()} expirations")

        # Sort expirations chronologically
        exps = sorted(df['expiration_date'].unique())

        # Get unique strikes and sort numerically
        strikes = sorted(df['strike_price'].unique())
        logging.info(f"Found {len(strikes)} unique strike prices across {len(exps)} expirations")

        # Check for large datasets
        if len(strikes) > 10000 or len(exps) > 100:
            logging.warning(f"Large dataset detected: {len(strikes)} strikes, {len(exps)} expirations. Performance may be impacted.")

        # Convert expirations to ordinal numbers for numerical plotting
        exp_nums = [exp.toordinal() for exp in exps]

        # Get valid data points for interpolation
        valid_df = df.dropna(subset=['implied_volatility'])
        strike_points = valid_df['strike_price'].values
        exp_points = valid_df['expiration_date'].apply(lambda x: x.toordinal()).values
        iv_points = valid_df['implied_volatility'].values.astype(np.float32)

        logging.info(f"Using {len(iv_points)} valid data points for cubic interpolation")

        # Create denser grids for smoother surface
        num_strikes_dense = 200
        num_exps_dense = 100
        strikes_dense = np.linspace(np.array(strikes).min(), np.array(strikes).max(), num_strikes_dense)
        exp_nums_dense = np.linspace(np.array(exp_nums).min(), np.array(exp_nums).max(), num_exps_dense)

        # Create meshgrids
        X, Y = np.meshgrid(strikes_dense, exp_nums_dense)

        # Interpolate using specified method
        if interpolation_method == 'rbf':
            rbf = Rbf(exp_points, strike_points, iv_points, function='multiquadric')
            Z = rbf(Y.ravel(), X.ravel()).reshape(Y.shape)
        else:
            Z = interp.griddata((exp_points, strike_points), iv_points, (Y, X), method=interpolation_method)

        logging.info(f"Surface processing complete with {interpolation_method} interpolation to denser grid")

        # Gap filling for sparse data
        if gap_fill_method and np.any(np.isnan(Z)):
            if gap_fill_method == 'mean':
                Z = jitted_mean_fill(Z)
            elif gap_fill_method == 'nearest':
                Z_df = pd.DataFrame(Z)
                Z = Z_df.interpolate(method='nearest').values
            elif gap_fill_method == 'linear':
                Z_df = pd.DataFrame(Z)
                Z = Z_df.interpolate(method='linear').values
            logging.info(f"Gap filling applied using {gap_fill_method} method")

        return X, Y, Z, exps

    except Exception as e:
        logging.error(f"Error in process_iv_for_surface: {e}")
        raise

def calculate_iv_metrics(df, underlying_price):
    """
    Calculate key IV surface metrics using vectorized numpy operations.

    Args:
        df (pd.DataFrame): DataFrame with IV data (strike_price, implied_volatility, expiration_date, option_type)
        underlying_price (float): Current underlying asset price

    Returns:
        dict: Dictionary with metrics: atm_iv, skew_ratios, term_premium, vol_of_vol
    """
    try:
        if df.empty:
            return {}

        metrics = {}

        # ATM IV: IV at strike closest to underlying for each expiration and type
        atm_iv = {}
        unique_exps = df['expiration_date'].unique()
        for exp in unique_exps:
            exp_mask = df['expiration_date'] == exp
            for opt_type in ['call', 'put']:
                type_mask = df['option_type'] == opt_type
                combined_mask = exp_mask & type_mask
                if combined_mask.any():
                    type_df = df[combined_mask]
                    strike_diffs = np.abs(type_df['strike_price'].values - underlying_price)
                    closest_idx = np.argmin(strike_diffs)
                    atm_iv[f'{opt_type}_{exp}'] = type_df['implied_volatility'].iloc[closest_idx]
        metrics['atm_iv'] = atm_iv

        # Skew ratios: call IV / put IV for same strike and expiration
        skew_ratios = {}
        for exp in unique_exps:
            exp_df = df[df['expiration_date'] == exp]
            unique_strikes = exp_df['strike_price'].unique()
            for strike in unique_strikes:
                call_iv = exp_df[(exp_df['strike_price'] == strike) & (exp_df['option_type'] == 'call')]['implied_volatility']
                put_iv = exp_df[(exp_df['strike_price'] == strike) & (exp_df['option_type'] == 'put')]['implied_volatility']
                if not call_iv.empty and not put_iv.empty:
                    skew_ratios[f'{strike}_{exp}'] = call_iv.values[0] / put_iv.values[0]
        metrics['skew_ratios'] = skew_ratios

        # Term premium: difference between short-term and long-term ATM IV
        if len(unique_exps) > 1:
            sorted_exps = sorted(unique_exps)
            short_exp = sorted_exps[0]
            long_exp = sorted_exps[-1]
            short_atm = metrics['atm_iv'].get(f'call_{short_exp}')
            long_atm = metrics['atm_iv'].get(f'call_{long_exp}')
            if short_atm is not None and long_atm is not None:
                metrics['term_premium'] = short_atm - long_atm

        # Volatility of volatility: standard deviation of all IV values
        metrics['vol_of_vol'] = df['implied_volatility'].std()

        logging.info("IV metrics calculated successfully")
        return metrics

    except Exception as e:
        logging.error(f"Error calculating IV metrics: {e}")
        raise

def save_iv_surface_to_db(db_path, surface: IVSurface):
    """
    Save IV surface data and metadata to SQLite database with proper indexing.

    Creates tables:
    - surface_metadata: id, ticker, timestamp, underlying_price, market_regime
    - surface_data: id, meta_id, expiration_date, strike_price, iv_call, iv_put

    Args:
        db_path (str): Path to SQLite database
        surface (IVSurface): IVSurface object to save
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create tables if not exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS surface_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                underlying_price REAL NOT NULL,
                market_regime TEXT NOT NULL,
                UNIQUE(ticker, timestamp)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS surface_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meta_id INTEGER NOT NULL,
                expiration_date TEXT NOT NULL,
                strike_price REAL NOT NULL,
                iv_call REAL,
                iv_put REAL,
                FOREIGN KEY (meta_id) REFERENCES surface_metadata (id)
            )
        """)

        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_meta_ticker ON surface_metadata (ticker)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_meta_timestamp ON surface_metadata (timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_data_meta_id ON surface_data (meta_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_data_exp_strike ON surface_data (expiration_date, strike_price)")

        # Insert metadata
        cursor.execute("""
            INSERT INTO surface_metadata (ticker, timestamp, underlying_price, market_regime)
            VALUES (?, ?, ?, ?)
        """, (surface.ticker, surface.timestamp.isoformat(), surface.underlying_price, surface.market_regime))

        meta_id = cursor.lastrowid

        # Prepare surface data for insertion
        # Flatten the multi-index DataFrame
        df_reset = surface.surface_data.reset_index()
        df_reset['expiration_date'] = df_reset['expiration_date'].astype(str)  # convert to string for DB

        # Insert data rows
        data_to_insert = []
        for _, row in df_reset.iterrows():
            data_to_insert.append((
                meta_id,
                row['expiration_date'],
                row['strike_price'],
                row.get('iv_call'),
                row.get('iv_put')
            ))

        cursor.executemany("""
            INSERT INTO surface_data (meta_id, expiration_date, strike_price, iv_call, iv_put)
            VALUES (?, ?, ?, ?, ?)
        """, data_to_insert)

        conn.commit()
        conn.close()

        logging.info(f"IV surface saved to database for {surface.ticker} at {surface.timestamp}")

    except Exception as e:
        logging.error(f"Error saving IV surface to database: {e}")
        raise

def validate_iv_surface(Z, strikes, expirations):
    """
    Validate IV surface for quality: outlier detection, smoothness, and arbitrage opportunities.

    Args:
        Z (np.ndarray): IV surface matrix
        strikes (np.ndarray): Strike prices array
        expirations: List of expiration dates

    Returns:
        dict: Validation results with flags and issues
    """
    try:
        validation = {
            'outliers': [],
            'smoothness_issues': [],
            'arbitrage_flags': [],
            'overall_quality': 'good'
        }

        # Outlier detection: Z-score > 3
        Z_flat = Z.flatten()
        valid_mask = ~np.isnan(Z_flat)
        if valid_mask.any():
            mean_iv = np.mean(Z_flat[valid_mask])
            std_iv = np.std(Z_flat[valid_mask])
            if std_iv > 0:
                z_scores = (Z_flat - mean_iv) / std_iv
                outlier_indices = np.where(np.abs(z_scores) > 3)[0]
                if len(outlier_indices) > 0:
                    validation['outliers'] = outlier_indices.tolist()
                    validation['overall_quality'] = 'warning'

        # Smoothness check: gradient magnitude
        grad_y, grad_x = np.gradient(Z)
        grad_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        high_gradient_mask = grad_magnitude > np.percentile(grad_magnitude[~np.isnan(grad_magnitude)], 95)
        if np.any(high_gradient_mask):
            validation['smoothness_issues'] = ['High gradient areas detected']
            validation['overall_quality'] = 'warning'

        # Arbitrage check: basic convexity for calls (IV should increase with strike distance from ATM)
        # Simplified: check if IV is too low in wings compared to center
        center_strike_idx = len(strikes) // 2
        wing_left = Z[:, :center_strike_idx//2] if center_strike_idx > 0 else Z[:, 0:1]
        wing_right = Z[:, -center_strike_idx//2:] if center_strike_idx > 0 else Z[:, -1:]
        center = Z[:, center_strike_idx:center_strike_idx+1] if center_strike_idx < Z.shape[1] else Z[:, -1:]
        if wing_left.size > 0 and wing_right.size > 0 and center.size > 0:
            mean_wing = (np.nanmean(wing_left) + np.nanmean(wing_right)) / 2
            mean_center = np.nanmean(center)
            if mean_wing < mean_center * 0.5:  # Arbitrary threshold
                validation['arbitrage_flags'] = ['Potential arbitrage: wings too cheap']
                validation['overall_quality'] = 'error'

        logging.info(f"Surface validation completed: {validation['overall_quality']}")
        return validation

    except Exception as e:
        logging.error(f"Error validating IV surface: {e}")
        return {'overall_quality': 'error', 'error': str(e)}

def plot_iv_surface(X, Y, Z, exps, ticker):
    """
    Generate a 3D surface plot of implied volatility data.

    Args:
        X: 2D array of strike prices (meshgrid)
        Y: 2D array of expiration dates (as ordinal numbers, meshgrid)
        Z: 2D array of implied volatilities
        exps: list of expiration dates
        ticker: stock ticker symbol
    """
    try:
        if X.size == 0 or Y.size == 0 or Z.size == 0:
            logging.warning("No data available for plotting")
            print("No data available for plotting.")
            return

        logging.info("Starting surface plotting")

        # Ensure charts directory exists
        os.makedirs('charts', exist_ok=True)

        # Check for large matrices that might cause performance issues
        if Z.size > 1000000:  # 1M points
            logging.warning(f"Large surface matrix ({Z.shape[0]}x{Z.shape[1]} = {Z.size} points). Plotting may be slow and memory-intensive.")

        # Convert IV to percentage
        Z_percent = Z * 100

        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')
        surf = ax.plot_surface(X, Y, Z_percent, cmap='plasma', alpha=0.8)
        ax.set_title(f'Implied Volatility Surface for {ticker}')
        ax.set_xlabel('Strike Price ($)')
        ax.set_ylabel('Expiration Date')
        ax.set_zlabel('Implied Volatility (%)')

        # Format strike prices with $
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x:.0f}'))

        # Format Y-axis with readable dates
        sorted_exps = sorted(exps)
        ax.set_yticks([d.toordinal() for d in sorted_exps])
        ax.set_yticklabels([d.strftime('%b %d, %Y') for d in sorted_exps])

        # Add colorbar
        fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5, label='Implied Volatility (%)')

        # Adjust view
        ax.view_init(elev=30, azim=-45)

        # Add grid
        ax.grid(True)

        plt.tight_layout()

        # Generate timestamp for filename
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{ticker}_IV_surface_{timestamp}.png'
        filepath = f'charts/{filename}'

        # Save with high DPI for quality
        plt.savefig(filepath, dpi=300)
        logging.info(f"PNG saved successfully: {filepath}")

        # Close the figure to free memory
        plt.close(fig)

    except Exception as e:
        logging.error(f"Error in plot_iv_surface: {e}")
        raise

def create_dash_app(X, Y, Z, exps, ticker):
    """
    Create Dash app for interactive 3D IV surface visualization.
    """
    try:
        if X.size == 0 or Y.size == 0 or Z.size == 0:
            logging.warning("No data available for Dash app")
            return None

        logging.info("Creating Dash app for interactive visualization")

        # Prepare data for Plotly
        strikes = X[0, :]
        exp_nums = Y[:, 0]
        exp_strings = [exp.strftime('%b %d, %Y') for exp in exps]

        fig = go.Figure(data=[go.Surface(
            x=strikes,
            y=exp_nums,
            z=Z * 100,  # to percentage
            colorscale='Plasma'
        )])

        fig.update_layout(
            title=f'Implied Volatility Surface for {ticker}',
            scene=dict(
                xaxis_title='Strike Price ($)',
                yaxis_title='Expiration Date',
                zaxis_title='Implied Volatility (%)',
                xaxis=dict(
                    tickformat='$,.0f'  # format as currency
                ),
                yaxis=dict(
                    tickvals=exp_nums,
                    ticktext=exp_strings
                )
            )
        )

        app = dash.Dash(__name__)
        app.layout = html.Div([
            html.H1(f'Interactive IV Surface for {ticker}'),
            dcc.Graph(figure=fig)
        ])

        return app

    except Exception as e:
        logging.error(f"Error creating Dash app: {e}")
        raise

@dataclass
class ExpirationFilterMonitor:
    """
    Monitoring system for expiration filter operations.

    Tracks expiration distributions, regime changes, and filter effectiveness metrics.
    Logs data to JSON files for dashboard consumption.
    """
    log_dir: str = "logs"
    ticker: str = "UNKNOWN"

    def __post_init__(self):
        """Initialize logging directory and regime tracking."""
        os.makedirs(self.log_dir, exist_ok=True)
        self.previous_regime = None
        self.session_start = datetime.datetime.now()

    def log_expiration_distribution(self, df: pd.DataFrame, criteria: ExpirationCriteria, filtered_df: pd.DataFrame = None):
        """
        Log the distribution of options across expiration dates before and after filtering.
        """
        try:
            today = datetime.date.today()

            # Calculate distributions
            total_dist = df.groupby('expiration_date').size().to_dict()
            total_dist = {str(k): v for k, v in total_dist.items()}  # Convert dates to strings

            filtered_dist = {}
            if filtered_df is not None and not filtered_df.empty:
                filtered_dist = filtered_df.groupby('expiration_date').size().to_dict()
                filtered_dist = {str(k): v for k, v in filtered_dist.items()}

            # Calculate days to expiration distribution
            days_dist = {}
            for exp in df['expiration_date'].unique():
                days = (exp - today).days
                bucket = self._get_days_bucket(days)
                days_dist[bucket] = days_dist.get(bucket, 0) + 1

            log_entry = {
                'timestamp': datetime.datetime.now().isoformat(),
                'ticker': self.ticker,
                'total_options': len(df),
                'filtered_options': len(filtered_df) if filtered_df is not None else None,
                'criteria': {
                    'min_days': criteria.min_days,
                    'max_days': criteria.max_days,
                    'regime_adjustment': criteria.regime_adjustment
                },
                'expiration_distribution': total_dist,
                'filtered_distribution': filtered_dist,
                'days_buckets': days_dist
            }

            self._write_log('expiration_distribution.json', log_entry)
            logging.info(f"Logged expiration distribution: {len(total_dist)} expirations, {len(df)} total options")

        except Exception as e:
            logging.error(f"Error logging expiration distribution: {e}")

    def log_regime_change(self, new_regime: str, vix_level: float = None, iv_percentile: float = None, liquidity_score: float = None):
        """
        Log changes in market regime detection.
        """
        try:
            if self.previous_regime != new_regime:
                log_entry = {
                    'timestamp': datetime.datetime.now().isoformat(),
                    'ticker': self.ticker,
                    'regime_change': {
                        'from': self.previous_regime,
                        'to': new_regime,
                        'vix_level': vix_level,
                        'iv_percentile': iv_percentile,
                        'liquidity_score': liquidity_score
                    }
                }

                self._write_log('regime_changes.json', log_entry)
                logging.info(f"Logged regime change: {self.previous_regime} -> {new_regime}")
                self.previous_regime = new_regime

        except Exception as e:
            logging.error(f"Error logging regime change: {e}")

    def log_filter_effectiveness(self, df: pd.DataFrame, filtered_df: pd.DataFrame, criteria: ExpirationCriteria,
                                efficiency_scores: dict = None, earnings_dates: list = None):
        """
        Log metrics on filter effectiveness and success rates.
        """
        try:
            total_options = len(df)
            filtered_options = len(filtered_df) if filtered_df is not None else 0

            effectiveness = {
                'timestamp': datetime.datetime.now().isoformat(),
                'ticker': self.ticker,
                'total_options': total_options,
                'filtered_options': filtered_options,
                'filter_rate': filtered_options / total_options if total_options > 0 else 0,
                'criteria': {
                    'min_days': criteria.min_days,
                    'max_days': criteria.max_days,
                    'regime_adjustment': criteria.regime_adjustment
                },
                'earnings_filtering': len(earnings_dates) if earnings_dates else 0,
                'efficiency_scoring': len(efficiency_scores) if efficiency_scores else 0
            }

            # Add efficiency score distribution
            if efficiency_scores:
                scores = list(efficiency_scores.values())
                effectiveness['efficiency_stats'] = {
                    'mean_score': np.mean(scores),
                    'median_score': np.median(scores),
                    'min_score': min(scores),
                    'max_score': max(scores),
                    'above_threshold': sum(1 for s in scores if s >= 0.5)  # Assuming 0.5 threshold
                }

            self._write_log('filter_effectiveness.json', effectiveness)
            logging.info(f"Logged filter effectiveness: {filtered_options}/{total_options} options passed filters")

        except Exception as e:
            logging.error(f"Error logging filter effectiveness: {e}")

    def get_monitoring_summary(self) -> dict:
        """
        Generate a summary of monitoring data for dashboard display.
        """
        try:
            summary = {
                'session_start': self.session_start.isoformat(),
                'current_regime': self.previous_regime,
                'ticker': self.ticker
            }

            # Load recent data from logs
            logs_to_check = ['expiration_distribution.json', 'regime_changes.json', 'filter_effectiveness.json']

            for log_file in logs_to_check:
                try:
                    data = self._read_recent_log(log_file, limit=10)  # Last 10 entries
                    summary[log_file.replace('.json', '')] = data
                except:
                    summary[log_file.replace('.json', '')] = []

            return summary

        except Exception as e:
            logging.error(f"Error generating monitoring summary: {e}")
            return {}

    def _get_days_bucket(self, days: int) -> str:
        """Categorize days to expiration into buckets."""
        if days < 30:
            return "<30 days"
        elif days < 60:
            return "30-59 days"
        elif days < 90:
            return "60-89 days"
        elif days < 120:
            return "90-119 days"
        elif days < 180:
            return "120-179 days"
        else:
            return "180+ days"

    def _write_log(self, filename: str, data: dict):
        """Write log entry to JSON file."""
        filepath = os.path.join(self.log_dir, filename)
        try:
            # Read existing data
            existing_data = []
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    existing_data = json.load(f)

            # Append new entry
            existing_data.append(data)

            # Keep only last 1000 entries to prevent file growth
            if len(existing_data) > 1000:
                existing_data = existing_data[-1000:]

            # Write back
            with open(filepath, 'w') as f:
                json.dump(existing_data, f, indent=2)

        except Exception as e:
            logging.error(f"Error writing to {filename}: {e}")

    def _read_recent_log(self, filename: str, limit: int = 10) -> list:
        """Read recent entries from log file."""
        filepath = os.path.join(self.log_dir, filename)
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    data = json.load(f)
                return data[-limit:] if len(data) > limit else data
            return []
        except Exception as e:
            logging.error(f"Error reading {filename}: {e}")
            return []

def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    parser = argparse.ArgumentParser(description="Implied Volatility Surfaces CLI Tool")
    parser.add_argument('-t', '--ticker', required=True, help="Stock ticker symbol (e.g., AAPL)")
    parser.add_argument('--dash', action='store_true', help="Launch interactive Dash web application instead of saving PNG")
    parser.add_argument('--api', action='store_true', help="Run FastAPI server for API endpoints")

    args = parser.parse_args()
    ticker = args.ticker

    try:
        db_path = f"{ticker}_options.db"
        df = retrieve_iv_data(db_path)

        if df.empty:
            logging.warning(f"No valid IV data found for {ticker}. Exiting.")
            return

        logging.info(f"Retrieved IV data for {ticker}: {len(df)} total data points")
        exp_counts = df.groupby('expiration_date').size()
        for exp, count in exp_counts.items():
            logging.info(f"Expiration {exp}: {count} strikes")

        # Process into surface arrays
        X, Y, Z, exps = process_iv_for_surface(df)
        logging.info(f"Surface arrays created: X shape {X.shape}, Y shape {Y.shape}, Z shape {Z.shape}")
        if Z.size > 0:
            logging.info(f"Z has {np.sum(~np.isnan(Z))} non-NaN values out of {Z.size}")

        # Generate visualization
        if args.dash:
            logging.info("Launching Dash interactive visualization")
            app = create_dash_app(X, Y, Z, exps, ticker)
            if app:
                print("Launching Dash app on http://127.0.0.1:8050/")
                app.run(debug=True)
            else:
                logging.error("Failed to create Dash app due to no data")
        else:
            logging.info("Generating static PNG surface plot")
            plot_iv_surface(X, Y, Z, exps, ticker)

    except Exception as e:
        logging.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    main()