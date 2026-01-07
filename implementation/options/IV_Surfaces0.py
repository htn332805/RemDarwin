import argparse
import sqlite3
import os
import datetime
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import dash
from dash import html, dcc
import plotly.graph_objects as go
from scipy import interpolate as interp

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

        # Build union query
        union_queries = []
        for table in tables:
            union_queries.append(f"SELECT strike_price, implied_volatility, expiration_date FROM {table} WHERE option_type='call'")
        full_query = " UNION ALL ".join(union_queries)

        # Fetch all data at once
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

def process_iv_for_surface(df):
    """
    Process the retrieved IV data into numpy arrays suitable for 3D plotting.

    Args:
        df (pd.DataFrame): DataFrame with columns strike_price, implied_volatility, expiration_date

    Returns:
        tuple: (X, Y, Z) where X and Y are 2D meshgrids (strikes, expirations), Z is IV matrix with NaNs for missing values

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

        # Interpolate using cubic method for smoother surface
        Z = interp.griddata((exp_points, strike_points), iv_points, (Y, X), method='cubic')

        logging.info("Surface processing complete with cubic interpolation to denser grid")

        return X, Y, Z, exps

    except Exception as e:
        logging.error(f"Error in process_iv_for_surface: {e}")
        raise

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

def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    parser = argparse.ArgumentParser(description="Implied Volatility Surfaces CLI Tool")
    parser.add_argument('-t', '--ticker', required=True, help="Stock ticker symbol (e.g., AAPL)")
    parser.add_argument('--dash', action='store_true', help="Launch interactive Dash web application instead of saving PNG")

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