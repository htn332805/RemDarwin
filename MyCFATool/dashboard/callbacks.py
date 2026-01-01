from dash import Input, Output, State
from dash import html
from .app import app
from .layouts import (
    overview_layout,
    financial_statements_layout,
    ratio_analysis_layout,
    risk_metrics_layout,
    valuation_layout,
    peer_comparison_layout,
    technicals_layout,
    forecasting_layout,
    portfolio_layout,
    validation_audit_layout
)
import sqlite3
import json
import yaml
import os
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from ..domain.services.fundamental_analysis_service import FundamentalAnalysisService
from ..domain.services.technical_analysis_service import TechnicalAnalysisService
from ..domain.services.valuation_service import ValuationService
from ..domain.services.forecasting_service import ForecastingService
from ..domain.repositories.financial_data_repository import FinancialDataRepository
from .pdf_exporter import PDFExporter
from .components.chart import create_line_chart, create_bar_chart
from .components.table import create_table
from ..core.config import Config
from ..core.database import get_session, db_manager
from ..ingestion.models import User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user
from sklearn.linear_model import LinearRegression
import numpy as np

def get_services():
    config = Config()
    session = get_session()
    repo = FinancialDataRepository(session)
    fundamental_service = FundamentalAnalysisService(repo)
    technical_service = TechnicalAnalysisService(repo)
    valuation_service = ValuationService(repo, fundamental_service)
    forecasting_service = ForecastingService()
    return {
        'repo': repo,
        'fundamental': fundamental_service,
        'technical': technical_service,
        'valuation': valuation_service,
        'forecasting': forecasting_service
    }

def load_financial_data(ticker):
    services = get_services()
    repo = services['repo']
    fundamental_service = services['fundamental']

    # Get latest fiscal_date
    fiscal_date = repo.get_latest_fiscal_date(ticker, 'annual')
    if not fiscal_date:
        return None

    # Get income statement data
    income_data = repo.get_income_statement(ticker, 'annual', fiscal_date)
    if not income_data:
        return None

    revenue = income_data.get('revenue')
    net_income = income_data.get('netIncome')

    # Compute ROE
    roe_result = fundamental_service.compute_return_on_equity(ticker, 'annual', fiscal_date)
    roe = roe_result['value'] if roe_result else None

    return {'revenue': revenue, 'net_income': net_income, 'roe': roe}

def load_overview_trends(ticker, period_type):
    services = get_services()
    repo = services['repo']

    income_statements = repo.get_income_statements(ticker, period_type)
    data = []
    for stmt in income_statements:
        data.append({
            'fiscal_date': stmt['fiscal_date'],
            'revenue': stmt.get('revenue'),
            'net_income': stmt.get('netIncome')
        })
    return pd.DataFrame(data)

def load_overview_table(ticker, period_type):
    # Simple table with latest key metrics
    data = load_financial_data(ticker)
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame([data])
    return df

def load_income_statement(ticker, period_type):
    services = get_services()
    repo = services['repo']

    income_statements = repo.get_income_statements(ticker, period_type)
    # Sort by fiscal_date descending and take last 5
    income_statements_sorted = sorted(income_statements, key=lambda x: x['fiscal_date'], reverse=True)[:5]
    data = []
    for stmt in income_statements_sorted:
        data.append({'fiscal_date': stmt['fiscal_date'], **stmt})
    return pd.DataFrame(data)

def load_balance_sheet(ticker, period_type):
    services = get_services()
    repo = services['repo']

    balance_sheets = repo.get_balance_sheets(ticker, period_type)
    # Sort by fiscal_date descending and take last 5
    balance_sheets_sorted = sorted(balance_sheets, key=lambda x: x['fiscal_date'], reverse=True)[:5]
    data = []
    for stmt in balance_sheets_sorted:
        data.append({'fiscal_date': stmt['fiscal_date'], **stmt})
    return pd.DataFrame(data)

def load_cash_flow(ticker, period_type):
    services = get_services()
    repo = services['repo']

    cash_flows = repo.get_cash_flows(ticker, period_type)
    # Sort by fiscal_date descending and take last 5
    cash_flows_sorted = sorted(cash_flows, key=lambda x: x['fiscal_date'], reverse=True)[:5]
    data = []
    for stmt in cash_flows_sorted:
        data.append({'fiscal_date': stmt['fiscal_date'], **stmt})
    return pd.DataFrame(data)

def load_ratio_trends(ticker, period_type):
    services = get_services()
    repo = services['repo']

    ratios = repo.get_ratios(ticker, period_type)
    data = []
    for ratio in ratios:
        data.append({
            'fiscal_date': ratio['fiscal_date'],
            'roe': ratio.get('returnOnEquity')
        })
    return pd.DataFrame(data)

def load_risk_scores(ticker, period_type):
    services = get_services()
    repo = services['repo']
    fundamental_service = services['fundamental']

    ratios = repo.get_ratios(ticker, period_type)
    data = []
    for ratio in ratios:
        fiscal_date = ratio['fiscal_date']
        z_score = fundamental_service.compute_altman_z_score(ticker, period_type, fiscal_date)
        m_score = fundamental_service.compute_beneish_m_score(ticker, period_type, fiscal_date)
        dd = fundamental_service.compute_merton_dd(ticker, period_type, fiscal_date, rf=0.05, T=1)
        o_score = fundamental_service.compute_ohlson_o_score(ticker, period_type, fiscal_date)
        entry = {'fiscal_date': fiscal_date}
        if z_score:
            entry['z_score'] = z_score['z_score']
        if m_score:
            entry['m_score'] = m_score['m_score']
        if dd:
            entry['merton_dd'] = dd['dd']
        if o_score:
            entry['o_score'] = o_score['o_score']
        data.append(entry)
    return pd.DataFrame(data)

def load_peer_data(ticker, period_type='annual'):
    if not ticker:
        return {}

    services = get_services()
    repo = services['repo']
    fundamental_service = services['fundamental']

    # Get all available tickers from repo
    all_tickers = repo.get_all_tickers()

    # Peers: all except selected
    peers = [t for t in all_tickers if t != ticker]

    if not peers:
        return {}

    # Key ratios to compare
    key_ratios = ['returnOnEquity', 'currentRatio', 'debtRatio', 'returnOnAssets']

    # Collect peer values for each ratio
    peer_values = {r: [] for r in key_ratios}

    for peer in peers:
        # Get latest fiscal_date for peer
        fiscal_date = repo.get_latest_fiscal_date(peer, period_type)
        if not fiscal_date:
            continue

        # Compute ratios
        for ratio in key_ratios:
            if ratio == 'returnOnEquity':
                value = fundamental_service.compute_return_on_equity(peer, period_type, fiscal_date)
            elif ratio == 'currentRatio':
                value = fundamental_service.compute_current_ratio(peer, period_type, fiscal_date)
            elif ratio == 'debtRatio':
                value = fundamental_service.compute_debt_ratio(peer, period_type, fiscal_date)
            elif ratio == 'returnOnAssets':
                value = fundamental_service.compute_return_on_assets(peer, period_type, fiscal_date)
            if value and 'value' in value:
                peer_values[ratio].append(value['value'])

    # Compute peer averages and std_dev
    peer_averages = {}
    for ratio, values in peer_values.items():
        if values:
            avg = sum(values) / len(values)
            std = pd.Series(values).std() if len(values) > 1 else None
            peer_averages[ratio] = {'average': avg, 'std_dev': std}

    if not peer_averages:
        return {}

    # Now for selected ticker, get fiscal_date
    fiscal_date = repo.get_latest_fiscal_date(ticker, period_type)
    if not fiscal_date:
        return {}

    # Compare to peers
    comparison = fundamental_service.compare_to_peers(ticker, period_type, fiscal_date, peer_averages)

    return {'comparison': comparison, 'peer_averages': peer_averages}

def load_technical_indicators(ticker):
    services = get_services()
    repo = services['repo']
    technical_service = services['technical']

    # Get latest trade_date
    latest_date = repo.get_latest_trade_date(ticker)
    if not latest_date:
        return {}
    fiscal_date = latest_date
    indicators = {}
    try:
        indicators['obv'] = technical_service.compute_obv(ticker, fiscal_date)
    except:
        indicators['obv'] = None
    try:
        indicators['vroc'] = technical_service.compute_vroc(ticker, fiscal_date)
    except:
        indicators['vroc'] = None
    try:
        indicators['atr'] = technical_service.compute_atr(ticker, fiscal_date)
    except:
        indicators['atr'] = None
    try:
        indicators['adx'] = technical_service.compute_adx(ticker, fiscal_date)
    except:
        indicators['adx'] = None
    try:
        indicators['rsi'] = technical_service.compute_rsi(ticker, fiscal_date)
    except:
        indicators['rsi'] = None
    try:
        indicators['macd'] = technical_service.compute_macd(ticker, fiscal_date)
    except:
        indicators['macd'] = None
    try:
        indicators['bollinger_bands'] = technical_service.compute_bollinger_bands(ticker, fiscal_date)
    except:
        indicators['bollinger_bands'] = None
    try:
        indicators['doji'] = technical_service.detect_doji(ticker, fiscal_date)
    except:
        indicators['doji'] = None
    try:
        indicators['engulfing'] = technical_service.detect_engulfing(ticker, fiscal_date)
    except:
        indicators['engulfing'] = None
    try:
        indicators['hammer'] = technical_service.detect_hammer(ticker, fiscal_date)
    except:
        indicators['hammer'] = None
    try:
        indicators['shooting_star'] = technical_service.detect_shooting_star(ticker, fiscal_date)
    except:
        indicators['shooting_star'] = None
    return indicators

def load_technical_price_data(ticker, start_date=None, end_date=None):
    services = get_services()
    repo = services['repo']

    prices = repo.get_historical_prices(ticker)
    if not prices:
        return pd.DataFrame()
    prices_df = pd.DataFrame(prices)
    prices_df['date'] = pd.to_datetime(prices_df['trade_date'])
    prices_df['volume'] = prices_df['volume'].fillna(0)
    prices_df['price'] = prices_df['close']  # For compatibility

    # Filter by date range if provided
    if start_date:
        prices_df = prices_df[prices_df['date'] >= pd.to_datetime(start_date)]
    if end_date:
        prices_df = prices_df[prices_df['date'] <= pd.to_datetime(end_date)]

    if len(prices_df) >= 20:
        prices_df['sma_20'] = prices_df['price'].rolling(window=20).mean()
        prices_df['ema_20'] = prices_df['price'].ewm(span=20).mean()
    # Compute OBV
    prices_df['price_change'] = prices_df['close'].diff()
    prices_df['obv'] = (prices_df['volume'] * prices_df['price_change'].apply(lambda x: 1 if x > 0 else -1 if x < 0 else 0)).cumsum()
    # Compute ATR
    if len(prices_df) >= 15:
        prices_df['prev_close'] = prices_df['close'].shift(1)
        prices_df['tr'] = prices_df.apply(lambda row: max(row['high'] - row['low'],
                                                          abs(row['high'] - row['prev_close']) if pd.notna(row['prev_close']) else row['high'] - row['low'],
                                                          abs(row['low'] - row['prev_close']) if pd.notna(row['prev_close']) else row['high'] - row['low']), axis=1)
        prices_df['atr'] = prices_df['tr'].rolling(window=14).mean()
    # Compute Bollinger Bands
    if len(prices_df) >= 20:
        prices_df['bb_middle'] = prices_df['price'].rolling(window=20).mean()
        prices_df['bb_std'] = prices_df['price'].rolling(window=20).std()
        prices_df['bb_upper'] = prices_df['bb_middle'] + (prices_df['bb_std'] * 2)
        prices_df['bb_lower'] = prices_df['bb_middle'] - (prices_df['bb_std'] * 2)
    # Compute RSI
    if len(prices_df) >= 15:
        delta = prices_df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        prices_df['rsi'] = 100 - (100 / (1 + rs))
    # Compute MACD
    if len(prices_df) >= 26:
        ema12 = prices_df['close'].ewm(span=12).mean()
        ema26 = prices_df['close'].ewm(span=26).mean()
        prices_df['macd'] = ema12 - ema26
        prices_df['macd_signal'] = prices_df['macd'].ewm(span=9).mean()
        prices_df['macd_histogram'] = prices_df['macd'] - prices_df['macd_signal']
    # Compute VROC (Volume Rate of Change, 10-day)
    if len(prices_df) >= 11:
        prices_df['volume_10_ago'] = prices_df['volume'].shift(10)
        prices_df['vroc'] = ((prices_df['volume'] - prices_df['volume_10_ago']) / prices_df['volume_10_ago']) * 100
    return prices_df

def load_historical_data(ticker, data_type, periods=100):
    """
    Load historical data for forecasting.
    data_type: 'price', 'revenue', 'net_income'
    """
    services = get_services()
    repo = services['repo']

    if data_type == 'price':
        prices = repo.get_historical_prices(ticker)
        if not prices:
            return pd.DataFrame()
        df = pd.DataFrame(prices)
        df['date'] = pd.to_datetime(df['trade_date'])
        df['value'] = df['close']
    elif data_type in ['revenue', 'net_income']:
        income_statements = repo.get_income_statements(ticker, 'annual')
        data = []
        for stmt in income_statements:
            value = stmt.get('revenue' if data_type == 'revenue' else 'netIncome')
            if value is not None:
                data.append({'date': stmt['fiscal_date'], 'value': value})
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data).sort_values('date').reset_index(drop=True)
    else:
        return pd.DataFrame()

    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    df['value'] = df['value'].interpolate(method='linear').fillna(method='bfill').fillna(method='ffill')
    return df

def load_ratio_history(ticker, ratio_method, periods=10):
    services = get_services()
    fundamental_service = services['fundamental']
    repo = services['repo']

    try:
        # Get latest balance sheet date
        latest_balance = None
        for i in range(periods):
            dt = datetime.now() - timedelta(days=i*365)
            f_date = dt.isoformat()[:10]
            bal = repo.get_balance_sheet(ticker, 'annual', f_date)
            if bal:
                latest_balance = bal
                break
        if not latest_balance:
            return pd.DataFrame()
        current_dt = datetime.fromisoformat(latest_balance['fiscal_date'])

        data = []
        for i in range(periods):
            dt = current_dt.replace(year=current_dt.year - i)
            f_date = dt.isoformat()[:10]
            ratio = getattr(fundamental_service, ratio_method)(ticker, 'annual', f_date)
            if ratio is not None and 'value' in ratio:
                data.append({'date': pd.to_datetime(f_date), 'value': ratio['value']})

        if len(data) < 3:
            return pd.DataFrame()

        df = pd.DataFrame(data).sort_values('date').reset_index(drop=True)
        df['value'] = df['value'].interpolate(method='linear').fillna(method='bfill').fillna(method='ffill')
        return df
    except ValueError:
        return pd.DataFrame()

def generate_forecast(ticker, forecast_type, horizon, data_type):
    services = get_services()
    forecasting_service = services['forecasting']

    if data_type == 'price':
        target = 'price'
        ratio_method = None
        df_hist = load_historical_data(ticker, 'price', periods=100)
    else:
        target = 'ratio'
        ratio_method = data_type
        df_hist = load_ratio_history(ticker, ratio_method, periods=10)

    if df_hist.empty:
        return None

    # Call forecasting service
    if forecast_type == 'arima':
        result = forecasting_service.arima_forecast(ticker, target=target, ratio_method=ratio_method, forecast_periods=horizon)
    elif forecast_type == 'exp_smoothing':
        result = forecasting_service.exponential_smoothing_forecast(ticker, target=target, ratio_method=ratio_method, forecast_periods=horizon)
    elif forecast_type == 'linear_regression':
        result = forecasting_service.linear_regression_forecast(ticker, target=target, ratio_method=ratio_method, forecast_periods=horizon)
    else:
        result = None

    if result:
        result['historical'] = df_hist.to_dict('records')
    return result

# Page routing callback
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/' or pathname == '/overview':
        return overview_layout()
    elif pathname == '/financial_statements':
        return financial_statements_layout()
    elif pathname == '/ratio_analysis':
        return ratio_analysis_layout()
    elif pathname == '/risk_metrics':
        return risk_metrics_layout()
    elif pathname == '/valuation':
        return valuation_layout()
    elif pathname == '/peer_comparison':
        return peer_comparison_layout()
    elif pathname == '/technicals':
        return technicals_layout()
    elif pathname == '/forecasting':
        return forecasting_layout()
    elif pathname == '/portfolio':
        return portfolio_layout()
    elif pathname == '/validation_audit':
        return validation_audit_layout()
    else:
        return html.Div([
            html.H1("404 - Page Not Found"),
            html.P(f"The page {pathname} does not exist.")
        ])

# Callback to update URL pathname based on tab selection
@app.callback(
    Output('url', 'pathname'),
    Input('tabs', 'value')
)
def update_pathname(tab_value):
    return f'/{tab_value}'

# Callback to update ticker data
# Callback to update overview chart
@app.callback(
    Output('overview-chart', 'figure'),
    Input('ticker-dropdown', 'value'),
    Input('period-dropdown', 'value')
)
def update_overview_chart(ticker, period):
    if ticker and period:
        df = load_overview_trends(ticker, period)
        if not df.empty:
            # Create line chart for revenue and net_income
            fig = create_line_chart(df, 'fiscal_date', 'revenue', 'Revenue Trends')
            # Add net_income trace
            fig.add_trace(create_line_chart(df, 'fiscal_date', 'net_income', 'Net Income Trends').data[0])
            fig.update_layout(title='Revenue and Net Income Trends')
            return fig
    return {}

# Callback to update overview table
@app.callback(
    Output('overview-table', 'children'),
    Input('ticker-dropdown', 'value'),
    Input('period-dropdown', 'value')
)
def update_overview_table(ticker, period):
    if ticker and period:
        df = load_overview_table(ticker, period)
        if not df.empty:
            return create_table(df, 'overview-table-id')
    return create_table(df, 'overview-table-id')

# Callbacks for Financial Statements tables
@app.callback(
    Output('income-table', 'children'),
    Input('fs-ticker-dropdown', 'value'),
    Input('fs-period-dropdown', 'value')
)
def update_income_table(ticker, period):
    if ticker and period:
        df = load_income_statement(ticker, period)
        if not df.empty:
            return create_table(df, 'income-table-id')
    return html.P("No data")

@app.callback(
    Output('balance-table', 'children'),
    Input('fs-ticker-dropdown', 'value'),
    Input('fs-period-dropdown', 'value')
)
def update_balance_table(ticker, period):
    if ticker and period:
        df = load_balance_sheet(ticker, period)
        if not df.empty:
            return create_table(df, 'balance-table-id')
    return html.P("No data")

@app.callback(
    Output('cash-table', 'children'),
    Input('fs-ticker-dropdown', 'value'),
    Input('fs-period-dropdown', 'value')
)
def update_cash_table(ticker, period):
    if ticker and period:
        df = load_cash_flow(ticker, period)
        if not df.empty:
            return create_table(df, 'cash-table-id')
    return html.P("No data")

# Callback for Ratio Analysis chart
@app.callback(
    Output('ra-chart', 'figure'),
    Input('ra-ticker-dropdown', 'value'),
    Input('ra-period-dropdown', 'value')
)
def update_ra_chart(ticker, period):
    if ticker and period:
        df = load_ratio_trends(ticker, period)
        if not df.empty:
            return create_line_chart(df, 'fiscal_date', 'roe', 'ROE Trends')
    return {}

# Callback for Ratio Analysis table (placeholder)
@app.callback(
    Output('ra-table', 'children'),
    Input('ra-ticker-dropdown', 'value'),
    Input('ra-period-dropdown', 'value')
)
def update_ra_table(ticker, period):
    # Placeholder: computed vs reported
    if ticker and period:
        df = load_ratio_trends(ticker, period).tail(1)  # Latest
        if not df.empty:
            return create_table(df, 'ra-table-id')
    return html.P("No data")

# Callbacks for Risk Metrics charts
@app.callback(
    Output('rm-z-chart', 'figure'),
    Input('rm-ticker-dropdown', 'value'),
    Input('rm-period-dropdown', 'value')
)
def update_rm_z_chart(ticker, period):
    if ticker and period:
        df = load_risk_scores(ticker, period)
        if not df.empty and 'z_score' in df.columns:
            fig = create_line_chart(df.dropna(subset=['z_score']), 'fiscal_date', 'z_score', 'Altman Z-Score Trends')
            # Add threshold lines
            fig.add_hline(y=3, line_dash="dash", line_color="green", annotation_text="Safe (>3)")
            fig.add_hline(y=1.8, line_dash="dash", line_color="yellow", annotation_text="Gray (1.8-3)")
            fig.add_hline(y=1.8, line_dash="dash", line_color="red", annotation_text="Distress (<1.8)")
            return fig
    return {}

@app.callback(
    Output('rm-m-chart', 'figure'),
    Input('rm-ticker-dropdown', 'value'),
    Input('rm-period-dropdown', 'value')
)
def update_rm_m_chart(ticker, period):
    if ticker and period:
        df = load_risk_scores(ticker, period)
        if not df.empty and 'm_score' in df.columns:
            fig = create_line_chart(df.dropna(subset=['m_score']), 'fiscal_date', 'm_score', 'Beneish M-Score Trends')
            fig.add_hline(y=-2.22, line_dash="dash", line_color="red", annotation_text="High Risk (>-2.22)")
            return fig
    return {}

@app.callback(
    Output('rm-dd-chart', 'figure'),
    Input('rm-ticker-dropdown', 'value'),
    Input('rm-period-dropdown', 'value')
)
def update_rm_dd_chart(ticker, period):
    if ticker and period:
        df = load_risk_scores(ticker, period)
        if not df.empty and 'merton_dd' in df.columns:
            fig = create_line_chart(df.dropna(subset=['merton_dd']), 'fiscal_date', 'merton_dd', 'Merton Distance to Default Trends')
            # Higher DD better, but no specific thresholds mentioned
            return fig
    return {}

@app.callback(
    Output('rm-o-chart', 'figure'),
    Input('rm-ticker-dropdown', 'value'),
    Input('rm-period-dropdown', 'value')
)
def update_rm_o_chart(ticker, period):
    if ticker and period:
        df = load_risk_scores(ticker, period)
        if not df.empty and 'o_score' in df.columns:
            fig = create_line_chart(df.dropna(subset=['o_score']), 'fiscal_date', 'o_score', 'Ohlson O-Score Trends')
            fig.add_hline(y=0.5, line_dash="dash", line_color="red", annotation_text="High Risk (>0.5)")
            return fig
    return {}

# Callback for Risk Metrics table
@app.callback(
    Output('rm-table', 'children'),
    Input('rm-ticker-dropdown', 'value'),
    Input('rm-period-dropdown', 'value')
)
def update_rm_table(ticker, period):
    if ticker and period:
        df = load_risk_scores(ticker, period).tail(1)
        if not df.empty:
            # Create custom table with color-coding
            latest = df.iloc[0]
            table_data = []
            if 'z_score' in latest and pd.notna(latest['z_score']):
                z = latest['z_score']
                color = 'red' if z < 1.8 else 'yellow' if z < 3 else 'green'
                table_data.append({'Score': 'Altman Z-Score', 'Value': ".3f", 'Threshold': '<1.8 Distress, 1.8-3 Gray, >3 Safe', 'color': color})
            if 'm_score' in latest and pd.notna(latest['m_score']):
                m = latest['m_score']
                color = 'red' if m > -2.22 else 'green'
                table_data.append({'Score': 'Beneish M-Score', 'Value': ".3f", 'Threshold': '> -2.22 High Risk', 'color': color})
            if 'merton_dd' in latest and pd.notna(latest['merton_dd']):
                dd = latest['merton_dd']
                color = 'blue'  # No specific threshold
                table_data.append({'Score': 'Merton Distance to Default', 'Value': ".3f", 'Threshold': 'Higher Better', 'color': color})
            if 'o_score' in latest and pd.notna(latest['o_score']):
                o = latest['o_score']
                color = 'red' if o > 0.5 else 'green'
                table_data.append({'Score': 'Ohlson O-Score', 'Value': ".3f", 'Threshold': '>0.5 High Risk', 'color': color})
            if table_data:
                table = html.Table([
                    html.Thead(html.Tr([html.Th(col) for col in ['Score', 'Value', 'Threshold']])),
                    html.Tbody([
                        html.Tr([
                            html.Td(row['Score']),
                            html.Td(row['Value'], style={'color': row['color']}),
                            html.Td(row['Threshold'])
                        ]) for row in table_data
                    ])
                ], style={'width': '100%', 'border': '1px solid black'})
                return table
    return html.P("No data")

# Callback for Peer Comparison chart
@app.callback(
    Output('pc-chart', 'figure'),
    Input('pc-ticker-dropdown', 'value'),
    Input('pc-period-dropdown', 'value')
)
def update_pc_chart(ticker, period):
    data = load_peer_data(ticker, period)
    if not data or 'comparison' not in data:
        return {}
    comparison = data['comparison']
    # Create plot data
    plot_data = []
    for ratio, comp in comparison.items():
        if comp['company'] is not None and comp['peer_average'] is not None:
            plot_data.append({
                'ratio': ratio,
                'company': comp['company'],
                'peer_avg': comp['peer_average']
            })
    if not plot_data:
        return {}
    df = pd.DataFrame(plot_data)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['ratio'], y=df['company'], name='Company'))
    fig.add_trace(go.Bar(x=df['ratio'], y=df['peer_avg'], name='Peer Average'))
    fig.update_layout(title='Peer Comparison: Company vs Peer Averages', barmode='group')
    return fig

# Callback for Peer Comparison table
@app.callback(
    Output('pc-table', 'children'),
    Input('pc-ticker-dropdown', 'value'),
    Input('pc-period-dropdown', 'value')
)
def update_pc_table(ticker, period):
    data = load_peer_data(ticker, period)
    if not data or 'comparison' not in data:
        return html.P("No data")
    comparison = data['comparison']
    # Create df for table
    table_data = []
    for ratio, comp in comparison.items():
        company = comp['company']
        peer_avg = comp['peer_average']
        difference = comp['difference']
        z_score = comp['z_score']
        interpretation = None
        if z_score is not None:
            if z_score > 1:
                interpretation = 'Above Average'
            elif z_score < -1:
                interpretation = 'Below Average'
            else:
                interpretation = 'Average'
        table_data.append({
            'Ratio': ratio,
            'Company Value': company,
            'Peer Average': peer_avg,
            'Difference': difference,
            'Z-Score': z_score,
            'Interpretation': interpretation
        })
    if not table_data:
        return html.P("No data")
    df = pd.DataFrame(table_data)
    return create_table(df, 'pc-table-id')

# Callback for Technicals main chart
@app.callback(
    Output('tech-main-chart', 'figure'),
    Input('tech-ticker-dropdown', 'value'),
    Input('tech-period-dropdown', 'value'),
    Input('tech-date-range', 'start_date'),
    Input('tech-date-range', 'end_date'),
    Input('tech-indicator-checklist', 'value')
)
def update_tech_main_chart(ticker, period, start_date, end_date, selected_indicators):
    if ticker:
        df = load_technical_price_data(ticker, start_date, end_date)
        if not df.empty:
            # Compute ADX if selected
            if 'adx' in selected_indicators and len(df) >= 30:
                # Simple ADX computation
                df['prev_high'] = df['high'].shift(1)
                df['prev_low'] = df['low'].shift(1)
                df['+dm'] = df.apply(lambda row: row['high'] - row['prev_high'] if row['high'] - row['prev_high'] > row['prev_low'] - row['low'] and row['high'] - row['prev_high'] > 0 else 0, axis=1)
                df['-dm'] = df.apply(lambda row: row['prev_low'] - row['low'] if row['prev_low'] - row['low'] > row['high'] - row['prev_high'] and row['prev_low'] - row['low'] > 0 else 0, axis=1)
                df['+di'] = 100 * (df['+dm'].ewm(span=14).mean() / df['atr'])
                df['-di'] = 100 * (df['-dm'].ewm(span=14).mean() / df['atr'])
                df['dx'] = 100 * abs(df['+di'] - df['-di']) / (df['+di'] + df['-di'])
                df['adx'] = df['dx'].ewm(span=14).mean()

            fig = go.Figure()

            # Candlestick
            fig.add_trace(go.Candlestick(x=df['date'],
                                         open=df['open'],
                                         high=df['high'],
                                         low=df['low'],
                                         close=df['close'],
                                         name='Candlestick'))

            # Overlays
            if 'sma' in selected_indicators and 'sma_20' in df.columns:
                fig.add_trace(go.Scatter(x=df['date'], y=df['sma_20'], mode='lines', name='SMA 20', line=dict(color='blue')))
            if 'ema' in selected_indicators and 'ema_20' in df.columns:
                fig.add_trace(go.Scatter(x=df['date'], y=df['ema_20'], mode='lines', name='EMA 20', line=dict(color='red')))
            if 'bb' in selected_indicators:
                if 'bb_upper' in df.columns:
                    fig.add_trace(go.Scatter(x=df['date'], y=df['bb_upper'], mode='lines', name='BB Upper', line=dict(color='gray', dash='dot')))
                    fig.add_trace(go.Scatter(x=df['date'], y=df['bb_lower'], mode='lines', name='BB Lower', line=dict(color='gray', dash='dot')))
                    fig.add_trace(go.Scatter(x=df['date'], y=df['bb_middle'], mode='lines', name='BB Middle', line=dict(color='gray')))

            # Patterns overlay if selected
            if 'patterns' in selected_indicators:
                # Detect patterns for each row
                for i, row in df.iterrows():
                    if i > 0:  # Need previous
                        prev_row = df.iloc[i-1]
                        # Doji: abs(open - close) / (high - low) < 0.1
                        body = abs(row['close'] - row['open'])
                        range_ = row['high'] - row['low']
                        if range_ > 0 and body / range_ < 0.05:
                            fig.add_annotation(x=row['date'], y=row['high'], text="Doji", showarrow=True, arrowhead=1, ax=0, ay=-30)
                        # Engulfing: current body engulfs previous
                        if row['close'] > row['open'] and prev_row['close'] < prev_row['open'] and row['open'] < prev_row['close'] and row['close'] > prev_row['open']:
                            fig.add_annotation(x=row['date'], y=row['high'], text="Bull Engulf", showarrow=True, arrowhead=1, ax=0, ay=-30, arrowcolor='green')
                        elif row['close'] < row['open'] and prev_row['close'] > prev_row['open'] and row['open'] > prev_row['close'] and row['close'] < prev_row['open']:
                            fig.add_annotation(x=row['date'], y=row['low'], text="Bear Engulf", showarrow=True, arrowhead=1, ax=0, ay=30, arrowcolor='red')

            fig.update_layout(
                title='Candlestick Chart with Indicators and Patterns',
                xaxis_rangeslider_visible=True,
                height=600
            )
            fig.update_xaxes(showgrid=True)
            fig.update_yaxes(showgrid=True)
            return fig
    return {}

# Callback for volume indicators chart
@app.callback(
    Output('tech-volume-chart', 'figure'),
    Input('tech-ticker-dropdown', 'value'),
    Input('tech-date-range', 'start_date'),
    Input('tech-date-range', 'end_date'),
    Input('tech-indicator-checklist', 'value')
)
def update_tech_volume_chart(ticker, start_date, end_date, selected_indicators):
    if ticker and ('obv' in selected_indicators or 'vroc' in selected_indicators):
        df = load_technical_price_data(ticker, start_date, end_date)
        if not df.empty:
            fig = go.Figure()
            if 'obv' in selected_indicators and 'obv' in df.columns:
                fig.add_trace(go.Scatter(x=df['date'], y=df['obv'], mode='lines', name='OBV', line=dict(color='blue')))
            if 'vroc' in selected_indicators and 'vroc' in df.columns:
                fig.add_trace(go.Scatter(x=df['date'], y=df['vroc'], mode='lines', name='VROC', line=dict(color='green')))
            fig.update_layout(
                title='Volume Indicators',
                xaxis_rangeslider_visible=True,
                height=400
            )
            return fig
    return {}

# Callback for trend indicators chart
@app.callback(
    Output('tech-trend-chart', 'figure'),
    Input('tech-ticker-dropdown', 'value'),
    Input('tech-date-range', 'start_date'),
    Input('tech-date-range', 'end_date'),
    Input('tech-indicator-checklist', 'value')
)
def update_tech_trend_chart(ticker, start_date, end_date, selected_indicators):
    if ticker and ('atr' in selected_indicators or 'adx' in selected_indicators):
        df = load_technical_price_data(ticker, start_date, end_date)
        if not df.empty:
            fig = go.Figure()
            if 'atr' in selected_indicators and 'atr' in df.columns:
                fig.add_trace(go.Scatter(x=df['date'], y=df['atr'], mode='lines', name='ATR', line=dict(color='orange')))
            if 'adx' in selected_indicators and 'adx' in df.columns:
                fig.add_trace(go.Scatter(x=df['date'], y=df['adx'], mode='lines', name='ADX', line=dict(color='purple')))
                fig.add_hline(y=25, line_dash="dash", line_color="black", annotation_text="Strong Trend (>25)")
                fig.add_hline(y=20, line_dash="dash", line_color="gray", annotation_text="Weak Trend (<20)")
            fig.update_layout(
                title='Trend Indicators',
                xaxis_rangeslider_visible=True,
                height=400
            )
            return fig
    return {}

# Callback for oscillators chart
@app.callback(
    Output('tech-oscillator-chart', 'figure'),
    Input('tech-ticker-dropdown', 'value'),
    Input('tech-date-range', 'start_date'),
    Input('tech-date-range', 'end_date'),
    Input('tech-indicator-checklist', 'value')
)
def update_tech_oscillator_chart(ticker, start_date, end_date, selected_indicators):
    if ticker and ('rsi' in selected_indicators or 'macd' in selected_indicators):
        df = load_technical_price_data(ticker, start_date, end_date)
        if not df.empty:
            fig = go.Figure()
            if 'rsi' in selected_indicators and 'rsi' in df.columns:
                fig.add_trace(go.Scatter(x=df['date'], y=df['rsi'], mode='lines', name='RSI', line=dict(color='purple')))
                fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
                fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
            if 'macd' in selected_indicators and 'macd' in df.columns:
                fig.add_trace(go.Scatter(x=df['date'], y=df['macd'], mode='lines', name='MACD', line=dict(color='blue')))
                fig.add_trace(go.Scatter(x=df['date'], y=df['macd_signal'], mode='lines', name='Signal', line=dict(color='red')))
            fig.update_layout(
                title='Oscillators',
                xaxis_rangeslider_visible=True,
                height=400
            )
            return fig
    return {}

# Callback for Technicals table
@app.callback(
    Output('tech-table', 'children'),
    Input('tech-ticker-dropdown', 'value'),
    Input('tech-period-dropdown', 'value')
)
def update_tech_table(ticker, period):
    if ticker:
        indicators = load_technical_indicators(ticker)
        table_data = []
        if indicators.get('obv'):
            obv = indicators['obv']
            table_data.append({
                'Indicator': 'On-Balance Volume (OBV)',
                'Value': ".2f",
                'Signal': obv['signal'],
                'Interpretation': obv['interpretation']
            })
        if indicators.get('vroc'):
            vroc = indicators['vroc']
            table_data.append({
                'Indicator': 'Volume Rate of Change (VROC)',
                'Value': ".2f",
                'Signal': vroc['signal'],
                'Interpretation': vroc['interpretation']
            })
        if indicators.get('atr'):
            atr = indicators['atr']
            table_data.append({
                'Indicator': 'Average True Range (ATR)',
                'Value': ".2f",
                'Signal': atr['signal'],
                'Interpretation': atr['interpretation']
            })
        if indicators.get('adx'):
            adx = indicators['adx']
            table_data.append({
                'Indicator': 'Average Directional Index (ADX)',
                'Value': ".2f",
                'Signal': adx['signal'],
                'Interpretation': adx['interpretation']
            })
        if indicators.get('rsi'):
            rsi = indicators['rsi']
            table_data.append({
                'Indicator': 'Relative Strength Index (RSI)',
                'Value': ".2f",
                'Signal': rsi['signal'],
                'Interpretation': rsi['interpretation']
            })
        if indicators.get('macd'):
            macd = indicators['macd']
            table_data.append({
                'Indicator': 'MACD',
                'Value': ".4f",
                'Signal': macd['trend_signal'],
                'Interpretation': macd['interpretation']
            })
        if indicators.get('bollinger_bands'):
            bb = indicators['bollinger_bands']
            table_data.append({
                'Indicator': 'Bollinger Bands',
                'Value': ".2f",
                'Signal': bb['signal'],
                'Interpretation': bb['interpretation']
            })
        if indicators.get('doji'):
            doji = indicators['doji']
            table_data.append({
                'Indicator': 'Doji Pattern',
                'Presence': doji['pattern_detected'],
                'Signal': doji['signal'],
                'Strength': ".2f"
            })
        if indicators.get('engulfing'):
            engulf = indicators['engulfing']
            table_data.append({
                'Indicator': 'Engulfing Pattern',
                'Presence': engulf['pattern_detected'],
                'Signal': engulf['signal'],
                'Strength': ".2f"
            })
        if indicators.get('hammer'):
            hammer = indicators['hammer']
            table_data.append({
                'Indicator': 'Hammer Pattern',
                'Presence': hammer['pattern_detected'],
                'Signal': hammer['signal'],
                'Strength': ".2f"
            })
        if indicators.get('shooting_star'):
            ss = indicators['shooting_star']
            table_data.append({
                'Indicator': 'Shooting Star Pattern',
                'Presence': ss['pattern_detected'],
                'Signal': ss['signal'],
                'Strength': ".2f"
            })
        if indicators.get('adx'):
            adx = indicators['adx']
            table_data.append({
                'Indicator': 'Average Directional Index (ADX)',
                'Value': ".2f",
                'Signal': adx['signal'],
                'Interpretation': adx['interpretation']
            })
        if table_data:
            df = pd.DataFrame(table_data)
            return create_table(df, 'tech-table-id')
    return html.P("No data")

# Original callback for ticker-output, perhaps remove or keep
@app.callback(
    Output('ticker-output', 'children'),
    Input('ticker-dropdown', 'value')
)
def update_ticker_data(ticker):
    if ticker:
        data = load_financial_data(ticker)
        if data:
            return html.Div([
                html.P(f"Revenue: {data['revenue']}"),
                html.P(f"Net Income: {data['net_income']}"),
                html.P(f"ROE: {data['roe']:.4f}" if data['roe'] else "ROE: N/A")
            ])
        else:
            return f"No data found for {ticker}."
    else:
        return "No ticker selected."

# Forecasting callbacks
@app.callback(
    Output('forecast-chart', 'figure'),
    Input('generate-forecast-btn', 'n_clicks'),
    State('forecast-ticker-dropdown', 'value'),
    State('forecast-type-dropdown', 'value'),
    State('forecast-horizon-dropdown', 'value'),
    State('forecast-data-dropdown', 'value')
)
def update_forecast_chart(n_clicks, ticker, forecast_type, horizon, data_type):
    if n_clicks and ticker and forecast_type and horizon and data_type:
        result = generate_forecast(ticker, forecast_type, horizon, data_type)
        if result and 'historical' in result:
            df_hist = pd.DataFrame(result['historical'])
            forecast_values = result['forecasted_values']
            fig = go.Figure()
            # Historical
            fig.add_trace(go.Scatter(x=df_hist['date'], y=df_hist['value'], mode='lines', name='Historical'))
            # Forecast
            freq = 'M' if data_type == 'price' else 'Y'
            future_dates = pd.date_range(start=df_hist['date'].iloc[-1], periods=horizon+1, freq=freq)[1:]
            fig.add_trace(go.Scatter(x=future_dates, y=forecast_values, mode='lines', name='Forecast', line=dict(dash='dash')))
            # Confidence intervals if available
            if 'confidence_intervals' in result and result['confidence_intervals']:
                lower = [ci[0] for ci in result['confidence_intervals']]
                upper = [ci[1] for ci in result['confidence_intervals']]
                fig.add_trace(go.Scatter(x=future_dates, y=lower, mode='lines', name='Lower CI', line=dict(color='lightblue')))
                fig.add_trace(go.Scatter(x=future_dates, y=upper, mode='lines', name='Upper CI', line=dict(color='lightblue'), fill='tonexty'))
            fig.update_layout(title=f'{forecast_type.upper()} Forecast for {ticker} {data_type}')
            return fig
    return {}

@app.callback(
    Output('forecast-table', 'children'),
    Input('generate-forecast-btn', 'n_clicks'),
    State('forecast-ticker-dropdown', 'value'),
    State('forecast-type-dropdown', 'value'),
    State('forecast-horizon-dropdown', 'value'),
    State('forecast-data-dropdown', 'value')
)
def update_forecast_table(n_clicks, ticker, forecast_type, horizon, data_type):
    if n_clicks and ticker and forecast_type and horizon and data_type:
        result = generate_forecast(ticker, forecast_type, horizon, data_type)
        if result:
            table_data = []
            cis = result.get('confidence_intervals')
            for i, val in enumerate(result['forecasted_values']):
                lower_ci = cis[i][0] if cis else None
                upper_ci = cis[i][1] if cis else None
                table_data.append({
                    'Period': i+1,
                    'Forecasted Value': f"{val:.2f}",
                    'Lower CI': f"{lower_ci:.2f}" if lower_ci is not None else 'N/A',
                    'Upper CI': f"{upper_ci:.2f}" if upper_ci is not None else 'N/A'
                })
            table_data.append({'Period': 'Interpretation', 'Forecasted Value': result.get('interpretation', ''), 'Lower CI': '', 'Upper CI': ''})
            df = pd.DataFrame(table_data)
            return create_table(df, 'forecast-table-id')
    return html.P("Click Generate to see forecast.")

def compute_portfolio_aggregates(tickers, weights, period_type='annual'):
    if not tickers or len(tickers) != len(weights):
        return None
    services = get_services()
    repo = services['repo']
    fundamental_service = services['fundamental']

    # Normalize weights
    total_weight = sum(weights)
    if total_weight == 0:
        return None
    normalized_weights = [w / total_weight for w in weights]

    portfolio_data = {
        'total_revenue': 0,
        'total_net_income': 0,
        'total_assets': 0,
        'total_liabilities': 0,
        'total_equity': 0,
        'weighted_roe': 0,
        'weighted_roa': 0,
        'weighted_debt_ratio': 0,
        'weighted_current_ratio': 0
    }

    for i, ticker in enumerate(tickers):
        fiscal_date = repo.get_latest_fiscal_date(ticker, period_type)
        if not fiscal_date:
            continue

        # Load income statement
        income_data = repo.get_income_statement(ticker, period_type, fiscal_date)
        if income_data:
            revenue = income_data.get('revenue', 0) or 0
            net_income = income_data.get('netIncome', 0) or 0
            portfolio_data['total_revenue'] += revenue * normalized_weights[i]
            portfolio_data['total_net_income'] += net_income * normalized_weights[i]

        # Load balance sheet
        balance_data = repo.get_balance_sheet(ticker, period_type, fiscal_date)
        if balance_data:
            total_assets = balance_data.get('totalAssets', 0) or 0
            total_liabilities = balance_data.get('totalLiabilities', 0) or 0
            total_equity = balance_data.get('totalStockholdersEquity', 0) or 0
            portfolio_data['total_assets'] += total_assets * normalized_weights[i]
            portfolio_data['total_liabilities'] += total_liabilities * normalized_weights[i]
            portfolio_data['total_equity'] += total_equity * normalized_weights[i]

        # Compute ratios
        roe_result = fundamental_service.compute_return_on_equity(ticker, period_type, fiscal_date)
        roa_result = fundamental_service.compute_return_on_assets(ticker, period_type, fiscal_date)
        debt_ratio_result = fundamental_service.compute_debt_ratio(ticker, period_type, fiscal_date)
        current_ratio_result = fundamental_service.compute_current_ratio(ticker, period_type, fiscal_date)

        if roe_result and 'value' in roe_result:
            portfolio_data['weighted_roe'] += roe_result['value'] * normalized_weights[i]
        if roa_result and 'value' in roa_result:
            portfolio_data['weighted_roa'] += roa_result['value'] * normalized_weights[i]
        if debt_ratio_result and 'value' in debt_ratio_result:
            portfolio_data['weighted_debt_ratio'] += debt_ratio_result['value'] * normalized_weights[i]
        if current_ratio_result and 'value' in current_ratio_result:
            portfolio_data['weighted_current_ratio'] += current_ratio_result['value'] * normalized_weights[i]

    return portfolio_data

def compute_portfolio_risks(tickers, weights, period_type='annual'):
    if not tickers or len(tickers) != len(weights):
        return None
    services = get_services()
    repo = services['repo']
    fundamental_service = services['fundamental']

    # Normalize weights
    total_weight = sum(weights)
    if total_weight == 0:
        return None
    normalized_weights = [w / total_weight for w in weights]

    risk_scores = {
        'weighted_z_score': 0,
        'weighted_m_score': 0,
        'weighted_dd': 0,
        'weighted_o_score': 0
    }

    for i, ticker in enumerate(tickers):
        fiscal_date = repo.get_latest_fiscal_date(ticker, period_type)
        if not fiscal_date:
            continue

        z_score = fundamental_service.compute_altman_z_score(ticker, period_type, fiscal_date)
        m_score = fundamental_service.compute_beneish_m_score(ticker, period_type, fiscal_date)
        dd = fundamental_service.compute_merton_dd(ticker, period_type, fiscal_date, rf=0.05, T=1)
        o_score = fundamental_service.compute_ohlson_o_score(ticker, period_type, fiscal_date)

        if z_score:
            risk_scores['weighted_z_score'] += z_score['z_score'] * normalized_weights[i]
        if m_score:
            risk_scores['weighted_m_score'] += m_score['m_score'] * normalized_weights[i]
        if dd:
            risk_scores['weighted_dd'] += dd['dd'] * normalized_weights[i]
        if o_score:
            risk_scores['weighted_o_score'] += o_score['o_score'] * normalized_weights[i]

    return risk_scores

def load_audit_report(ticker, period, fiscal_date):
    services = get_services()
    fundamental_service = services['fundamental']
    # For trends, use last 3 years if available
    trend_dates = [fiscal_date]
    try:
        current_dt = datetime.fromisoformat(fiscal_date)
        for i in range(1, 4):
            prev_dt = current_dt.replace(year=current_dt.year - i)
            trend_dates.append(prev_dt.isoformat()[:10])
    except:
        pass
    # Assuming FundamentalAnalysisService has generate_audit_report
    report = fundamental_service.generate_audit_report(ticker, period, fiscal_date, trend_dates)
    return report

@app.callback(
    Output('va-fiscal-date-dropdown', 'options'),
    Input('va-ticker-dropdown', 'value'),
    Input('va-period-dropdown', 'value')
)
def update_va_dates(ticker, period):
    if not ticker or not period:
        return []
    services = get_services()
    repo = services['repo']
    income_statements = repo.get_income_statements(ticker, period)
    dates = sorted(set(stmt['fiscal_date'] for stmt in income_statements), reverse=True)
    options = [{'label': d, 'value': d} for d in dates]
    return options

@app.callback(
    Output('va-summary-stats', 'children'),
    Input('va-ticker-dropdown', 'value'),
    Input('va-period-dropdown', 'value'),
    Input('va-fiscal-date-dropdown', 'value')
)
def update_va_summary(ticker, period, fiscal_date):
    if not ticker or not period or not fiscal_date:
        return ""
    report = load_audit_report(ticker, period, fiscal_date)
    if not report:
        return html.P("No data available")
    summary = report.get('summary', '')
    disc_logged = report.get('discrepancies_logged', False)
    missing = report.get('missing_data', [])
    return html.Div([
        html.H3("Summary Statistics"),
        html.P(f"Summary: {summary}"),
        html.P(f"Discrepancies Logged: {disc_logged}"),
        html.P(f"Missing Analyses: {', '.join(missing) if missing else 'None'}")
    ])

# Portfolio callbacks
@app.callback(
    Output('portfolio-weight-inputs', 'children'),
    Input('portfolio-ticker-dropdown', 'value')
)
def update_portfolio_weight_inputs(selected_tickers):
    if not selected_tickers:
        return html.P("Select tickers to enter weights")
    inputs = []
    for ticker in selected_tickers:
        inputs.append(html.Div([
            html.Label(f"Weight for {ticker}:"),
            dcc.Input(id=f'weight-{ticker}', type='number', value=1.0, min=0, step=0.01)
        ]))
    return inputs

@app.callback(
    Output('portfolio-summary-table', 'children'),
    Input('create-portfolio-btn', 'n_clicks'),
    State('portfolio-ticker-dropdown', 'value')
)
def update_portfolio_summary(n_clicks, selected_tickers):
    if not n_clicks or not selected_tickers:
        return html.P("Create portfolio to see summary")
    # Get weights from inputs
    weights = []
    for ticker in selected_tickers:
        weight = 1.0  # Default, since we can't easily get from inputs in state
        # Actually, to get weights, we need to use State for each input
        # For simplicity, assume equal weights for now
        weights.append(1.0)
    portfolio_data = compute_portfolio_aggregates(selected_tickers, weights)
    if not portfolio_data:
        return html.P("Unable to compute portfolio data")
    # Create table
    table_data = [
        {'Metric': 'Total Revenue', 'Value': f"{portfolio_data['total_revenue']:.2f}"},
        {'Metric': 'Total Net Income', 'Value': f"{portfolio_data['total_net_income']:.2f}"},
        {'Metric': 'Total Assets', 'Value': f"{portfolio_data['total_assets']:.2f}"},
        {'Metric': 'Total Liabilities', 'Value': f"{portfolio_data['total_liabilities']:.2f}"},
        {'Metric': 'Total Equity', 'Value': f"{portfolio_data['total_equity']:.2f}"},
        {'Metric': 'Weighted ROE', 'Value': f"{portfolio_data['weighted_roe']:.4f}"},
        {'Metric': 'Weighted ROA', 'Value': f"{portfolio_data['weighted_roa']:.4f}"},
        {'Metric': 'Weighted Debt Ratio', 'Value': f"{portfolio_data['weighted_debt_ratio']:.4f}"},
        {'Metric': 'Weighted Current Ratio', 'Value': f"{portfolio_data['weighted_current_ratio']:.4f}"}
    ]
    df = pd.DataFrame(table_data)
    return create_table(df, 'portfolio-summary-id')

@app.callback(
    Output('portfolio-pie-chart', 'figure'),
    Input('create-portfolio-btn', 'n_clicks'),
    State('portfolio-ticker-dropdown', 'value')
)
def update_portfolio_pie_chart(n_clicks, selected_tickers):
    if not n_clicks or not selected_tickers:
        return {}
    # Assume equal weights for pie
    weights = [1.0 / len(selected_tickers)] * len(selected_tickers)
    fig = go.Figure(data=[go.Pie(labels=selected_tickers, values=weights)])
    fig.update_layout(title='Asset Allocation')
    return fig

@app.callback(
    Output('portfolio-performance-chart', 'figure'),
    Input('create-portfolio-btn', 'n_clicks'),
    State('portfolio-ticker-dropdown', 'value')
)
def update_portfolio_performance_chart(n_clicks, selected_tickers):
    if not n_clicks or not selected_tickers:
        return {}
    services = get_services()
    repo = services['repo']
    fig = go.Figure()
    for ticker in selected_tickers:
        prices = repo.get_historical_prices(ticker)
        if prices:
            dates = [p['trade_date'] for p in prices]
            closes = [p['close'] for p in prices]
            fig.add_trace(go.Scatter(x=dates, y=closes, mode='lines', name=ticker))
    fig.update_layout(title='Historical Price Performance')
    return fig

@app.callback(
    Output('portfolio-risk-table', 'children'),
    Input('create-portfolio-btn', 'n_clicks'),
    State('portfolio-ticker-dropdown', 'value')
)
def update_portfolio_risk_table(n_clicks, selected_tickers):
    if not n_clicks or not selected_tickers:
        return html.P("Create portfolio to see risk metrics")
    weights = [1.0] * len(selected_tickers)  # Equal
    risk_data = compute_portfolio_risks(selected_tickers, weights)
    if not risk_data:
        return html.P("Unable to compute risk data")
    table_data = [
        {'Risk Metric': 'Weighted Z-Score', 'Value': f"{risk_data['weighted_z_score']:.4f}"},
        {'Risk Metric': 'Weighted M-Score', 'Value': f"{risk_data['weighted_m_score']:.4f}"},
        {'Risk Metric': 'Weighted DD', 'Value': f"{risk_data['weighted_dd']:.4f}"},
        {'Risk Metric': 'Weighted O-Score', 'Value': f"{risk_data['weighted_o_score']:.4f}"}
    ]
    df = pd.DataFrame(table_data)
    return create_table(df, 'portfolio-risk-id')

@app.callback(
    Output('va-table', 'children'),
    Input('va-ticker-dropdown', 'value'),
    Input('va-period-dropdown', 'value'),
    Input('va-fiscal-date-dropdown', 'value'),
    Input('va-type-filter', 'value')
)
def update_va_table(ticker, period, fiscal_date, filter_type):
    if not ticker or not period or not fiscal_date:
        return html.P("Select ticker, period, and fiscal date")
    report = load_audit_report(ticker, period, fiscal_date)
    if not report:
        return html.P("No audit report available")
    table_data = []
    if 'scores' in report and (filter_type == 'all' or filter_type in ['altman', 'piotroski', 'dupont']):
        for k, v in report['scores'].items():
            if filter_type == 'all' or (filter_type == 'altman' and 'altman' in k.lower()) or (filter_type == 'piotroski' and 'piotroski' in k.lower()) or (filter_type == 'dupont' and 'dupont' in k.lower()):
                table_data.append({'Type': k, 'Value': str(v)})
    if 'recommendations' in report and filter_type == 'all':
        for rec in report['recommendations']:
            table_data.append({'Type': 'Recommendation', 'Value': rec})
    if 'trends' in report and report['trends'] and filter_type == 'all':
        for date, val in report['trends'].get('ratio_values', {}).items():
            table_data.append({'Type': f'ROE Trend {date}', 'Value': str(val)})
    if not table_data:
        return html.P("No data matches the filter")
    df = pd.DataFrame(table_data)
    return create_table(df, 'va-table-id')

# Auth callbacks
@app.callback(
    Output('auth-msg', 'children'),
    Input('login-btn', 'n_clicks'),
    State('username-input', 'value'),
    State('password-input', 'value')
)
def handle_login(n_clicks, username, password):
    if n_clicks:
        if not username or not password:
            return "Please enter username and password"
        with db_manager.session() as session:
            user = session.query(User).filter_by(username=username).first()
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                return "Login successful. Please refresh the page to access the dashboard."
            else:
                return "Invalid credentials"
    return ""

@app.callback(
    Output('auth-msg', 'children'),
    Input('register-btn', 'n_clicks'),
    State('username-input', 'value'),
    State('password-input', 'value'),
    State('api-key-input', 'value')
)
def handle_register(n_clicks, username, password, api_key):
    if n_clicks:
        if not username or not password:
            return "Please enter username and password"
        with db_manager.session() as session:
            existing = session.query(User).filter_by(username=username).first()
            if existing:
                return "Username already exists"
            hashed = generate_password_hash(password)
            user = User(username=username, password_hash=hashed, api_key=api_key)
            session.add(user)
            session.commit()
            return "Registration successful. You can now login."
    return ""

@app.callback(
    Output('url', 'pathname'),
    Input('logout-btn', 'n_clicks')
)
def handle_logout(n_clicks):
    if n_clicks:
        logout_user()
        return '/'
    return dash.no_update

# DCF Valuation callbacks
@app.callback(
    Output('dcf-results', 'children'),
    Input('compute-dcf-btn', 'n_clicks'),
    State('val-ticker-dropdown', 'value'),
    State('val-period-dropdown', 'value'),
    State('val-projection-years-dropdown', 'value'),
    State('val-growth-rate-input', 'value'),
    State('val-risk-free-input', 'value'),
    State('val-market-premium-input', 'value'),
    State('val-beta-input', 'value')
)
def update_dcf_results(n_clicks, ticker, period, projection_years, growth_rate, risk_free, market_premium, beta):
    if not n_clicks or not ticker or not period:
        return html.P("Compute DCF to see results")
    services = get_services()
    repo = services['repo']
    valuation_service = services['valuation']
    fiscal_date = repo.get_latest_fiscal_date(ticker, period)
    if not fiscal_date:
        return html.P("No data available")
    result = valuation_service.compute_dcf_valuation(ticker, period, fiscal_date, projection_years, growth_rate/100, risk_free/100, market_premium/100, beta)
    if not result:
        return html.P("DCF calculation failed")
    return html.Div([
        html.P(f"Intrinsic Value: ${result['intrinsic_value']:.2f}"),
        html.P(f"WACC: {result['wacc']:.4f}"),
        html.P(f"Terminal Value: ${result['terminal_value']:.2f}"),
        html.P(f"Signal: {result['signal']}"),
        html.P(f"Interpretation: {result['interpretation']}")
    ])

@app.callback(
    Output('dcf-fcf-table', 'children'),
    Input('compute-dcf-btn', 'n_clicks'),
    State('val-ticker-dropdown', 'value'),
    State('val-period-dropdown', 'value'),
    State('val-projection-years-dropdown', 'value'),
    State('val-growth-rate-input', 'value'),
    State('val-risk-free-input', 'value'),
    State('val-market-premium-input', 'value'),
    State('val-beta-input', 'value')
)
def update_dcf_fcf_table(n_clicks, ticker, period, projection_years, growth_rate, risk_free, market_premium, beta):
    if not n_clicks or not ticker or not period:
        return html.P("Compute DCF to see FCF projections")
    services = get_services()
    repo = services['repo']
    valuation_service = services['valuation']
    fiscal_date = repo.get_latest_fiscal_date(ticker, period)
    if not fiscal_date:
        return html.P("No data")
    fcfs = valuation_service.project_free_cash_flows(ticker, period, fiscal_date, projection_years, growth_rate/100)
    if not fcfs:
        return html.P("No FCF projections")
    table_data = [{'Year': i+1, 'Projected FCF': f"{fcf:.2f}"} for i, fcf in enumerate(fcfs)]
    df = pd.DataFrame(table_data)
    return create_table(df, 'dcf-fcf-id')

@app.callback(
    Output('dcf-sensitivity-table', 'children'),
    Input('compute-dcf-btn', 'n_clicks'),
    State('val-ticker-dropdown', 'value'),
    State('val-period-dropdown', 'value'),
    State('val-projection-years-dropdown', 'value'),
    State('val-growth-rate-input', 'value'),
    State('val-risk-free-input', 'value'),
    State('val-market-premium-input', 'value'),
    State('val-beta-input', 'value')
)
def update_dcf_sensitivity(n_clicks, ticker, period, projection_years, growth_rate, risk_free, market_premium, beta):
    if not n_clicks or not ticker or not period:
        return html.P("Compute DCF to see sensitivity")
    services = get_services()
    repo = services['repo']
    valuation_service = services['valuation']
    fiscal_date = repo.get_latest_fiscal_date(ticker, period)
    if not fiscal_date:
        return html.P("No data")
    base_result = valuation_service.compute_dcf_valuation(ticker, period, fiscal_date, projection_years, growth_rate/100, risk_free/100, market_premium/100, beta)
    if not base_result:
        return html.P("Base DCF failed")
    sensitivity = valuation_service.perform_sensitivity_analysis(base_result)
    table_data = []
    for (gr, dr), val in sensitivity.items():
        if val:
            table_data.append({'Growth Rate': f"{gr:.1%}", 'Discount Rate': f"{dr:.1%}", 'Intrinsic Value': f"{val:.2f}"})
    if not table_data:
        return html.P("No sensitivity data")
    df = pd.DataFrame(table_data)
    return create_table(df, 'dcf-sensitivity-id')

# PDF Export Callbacks
@app.callback(
    Output('overview-export-msg', 'children'),
    Input('overview-export-btn', 'n_clicks'),
    State('ticker-dropdown', 'value'),
    State('period-dropdown', 'value')
)
def export_overview_pdf(n_clicks, ticker, period):
    if n_clicks > 0 and ticker and period:
        config_path = os.path.join(os.path.dirname(__file__), '../../config/settings.yaml')
        exporter = PDFExporter(config_path)
        filename = exporter.generate_overview_pdf(ticker, period)
        return f"PDF generated: {filename}"
    return ""

@app.callback(
    Output('fs-export-msg', 'children'),
    Input('fs-export-btn', 'n_clicks'),
    State('fs-ticker-dropdown', 'value'),
    State('fs-period-dropdown', 'value')
)
def export_fs_pdf(n_clicks, ticker, period):
    if n_clicks > 0 and ticker and period:
        config_path = os.path.join(os.path.dirname(__file__), '../../config/settings.yaml')
        exporter = PDFExporter(config_path)
        filename = exporter.generate_financial_statements_pdf(ticker, period)
        return f"PDF generated: {filename}"
    return ""

@app.callback(
    Output('valuation-export-msg', 'children'),
    Input('valuation-export-btn', 'n_clicks'),
    State('val-ticker-dropdown', 'value'),
    State('val-period-dropdown', 'value'),
    State('val-projection-years-dropdown', 'value'),
    State('val-growth-rate-input', 'value'),
    State('val-risk-free-input', 'value'),
    State('val-market-premium-input', 'value'),
    State('val-beta-input', 'value')
)
def export_valuation_pdf(n_clicks, ticker, period, projection_years, growth_rate, risk_free, market_premium, beta):
    if n_clicks > 0 and ticker and period:
        config_path = os.path.join(os.path.dirname(__file__), '../../config/settings.yaml')
        exporter = PDFExporter(config_path)
        filename = exporter.generate_valuation_pdf(ticker, period, projection_years, growth_rate, risk_free, market_premium, beta)
        return f"PDF generated: {filename}"
    return ""