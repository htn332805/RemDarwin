from dash import html, dcc
import yaml
import os
from flask_login import current_user

try:
    import dash_bootstrap_components as dbc
except ImportError:
    dbc = None

# Import components
from .components.filter import ticker_dropdown, period_dropdown
from .components.chart import create_line_chart, create_bar_chart
from .components.table import create_table
from ..domain.repositories.ticker_repository import TickerRepository

def get_available_tickers():
    """Get list of available tickers from database."""
    try:
        repo = TickerRepository()
        tickers_data = repo.get_all_tickers()
        return [t['symbol'] for t in tickers_data]
    except Exception as e:
        # Fallback to config if DB not available
        config_path = os.path.join(os.path.dirname(__file__), '../../config/settings.yaml')
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config.get('tickers', [])

# Placeholder layout functions for each page
def overview_layout():
    tickers = get_available_tickers()
    return html.Div([
        html.H1("Overview"),
        ticker_dropdown(tickers, 'ticker-dropdown'),
        period_dropdown('period-dropdown'),
        dcc.Loading(
            id="loading-overview-chart",
            children=[
                html.Div([
                    html.H2("Revenue/Net Income Trends"),
                    dcc.Graph(id='overview-chart')
                ])
            ],
            type="default"
        ),
        dcc.Loading(
            id="loading-overview-table",
            children=[
                html.Div([
                    html.H2("Key Metrics"),
                    html.Div(id='overview-table')
                ])
            ],
            type="default"
        ),
        html.Button('Export PDF', id='overview-export-btn', n_clicks=0),
        html.Div(id='overview-export-msg')
    ])

def financial_statements_layout():
    tickers = get_available_tickers()
    return html.Div([
        html.H1("Financial Statements"),
        ticker_dropdown(tickers, 'fs-ticker-dropdown'),
        period_dropdown('fs-period-dropdown'),
        dcc.Tabs(id='fs-tabs', value='income', children=[
            dcc.Tab(label='Income Statement', value='income', children=[
                html.Div(id='income-table')
            ]),
            dcc.Tab(label='Balance Sheet', value='balance', children=[
                html.Div(id='balance-table')
            ]),
            dcc.Tab(label='Cash Flow', value='cash', children=[
                html.Div(id='cash-table')
            ])
        ]),
        html.Button('Export PDF', id='fs-export-btn', n_clicks=0),
        html.Div(id='fs-export-msg')
    ])

def ratio_analysis_layout():
    tickers = get_available_tickers()
    return html.Div([
        html.H1("Ratio Analysis"),
        ticker_dropdown(tickers, 'ra-ticker-dropdown'),
        period_dropdown('ra-period-dropdown'),
        html.Div([
            html.H2("Ratio Trends"),
            dcc.Graph(id='ra-chart')
        ]),
        html.Div([
            html.H2("Computed vs Reported Ratios"),
            html.Div(id='ra-table')
        ])
    ])

def risk_metrics_layout():
    tickers = get_available_tickers()
    return html.Div([
        html.H1("Risk Metrics"),
        ticker_dropdown(tickers, 'rm-ticker-dropdown'),
        period_dropdown('rm-period-dropdown'),
        html.Div([
            html.H2("Altman Z-Score Trend"),
            dcc.Graph(id='rm-z-chart')
        ]),
        html.Div([
            html.H2("Beneish M-Score Trend"),
            dcc.Graph(id='rm-m-chart')
        ]),
        html.Div([
            html.H2("Merton Distance to Default Trend"),
            dcc.Graph(id='rm-dd-chart')
        ]),
        html.Div([
            html.H2("Ohlson O-Score Trend"),
            dcc.Graph(id='rm-o-chart')
        ]),
        html.Div([
            html.H2("Latest Risk Scores"),
            html.Div(id='rm-table')
        ])
    ])

def valuation_layout():
    tickers = get_available_tickers()
    return html.Div([
        html.H1("DCF Valuation"),
        ticker_dropdown(tickers, 'val-ticker-dropdown'),
        period_dropdown('val-period-dropdown'),
        html.Div([
            html.Label("Projection Years"),
            dcc.Dropdown(
                id='val-projection-years-dropdown',
                options=[
                    {'label': '5 Years', 'value': 5},
                    {'label': '10 Years', 'value': 10}
                ],
                value=5
            )
        ]),
        html.Div([
            html.Label("Growth Rate (%)"),
            dcc.Input(id='val-growth-rate-input', type='number', value=3.0, step=0.1)
        ]),
        html.Div([
            html.Label("Risk-Free Rate (%)"),
            dcc.Input(id='val-risk-free-input', type='number', value=5.0, step=0.1)
        ]),
        html.Div([
            html.Label("Market Risk Premium (%)"),
            dcc.Input(id='val-market-premium-input', type='number', value=6.0, step=0.1)
        ]),
        html.Div([
            html.Label("Beta"),
            dcc.Input(id='val-beta-input', type='number', value=1.0, step=0.1)
        ]),
        html.Button('Compute DCF', id='compute-dcf-btn', n_clicks=0),
        dcc.Loading(
            id="loading-dcf-results",
            children=[
                html.Div([
                    html.H2("DCF Valuation Results"),
                    html.Div(id='dcf-results')
                ])
            ],
            type="default"
        ),
        dcc.Loading(
            id="loading-dcf-fcf-table",
            children=[
                html.Div([
                    html.H2("Projected FCF"),
                    html.Div(id='dcf-fcf-table')
                ])
            ],
            type="default"
        ),
        dcc.Loading(
            id="loading-dcf-sensitivity-table",
            children=[
                html.Div([
                    html.H2("Sensitivity Analysis"),
                    html.Div(id='dcf-sensitivity-table')
                ])
            ],
            type="default"
        ),
        html.Button('Export PDF', id='valuation-export-btn', n_clicks=0),
        html.Div(id='valuation-export-msg')
    ])

def peer_comparison_layout():
    tickers = get_available_tickers()
    return html.Div([
        html.H1("Peer Comparison"),
        ticker_dropdown(tickers, 'pc-ticker-dropdown'),
        period_dropdown('pc-period-dropdown'),
        html.Div([
            html.H2("Peer Comparisons"),
            dcc.Graph(id='pc-chart')
        ]),
        html.Div([
            html.H2("Peer Data"),
            html.Div(id='pc-table')
        ])
    ])

def technicals_layout():
    tickers = get_available_tickers()
    return html.Div([
        html.H1("Technicals"),
        ticker_dropdown(tickers, 'tech-ticker-dropdown'),
        period_dropdown('tech-period-dropdown'),
        html.Div([
            html.Label("Date Range"),
            dcc.DatePickerRange(
                id='tech-date-range',
                start_date=None,
                end_date=None,
                display_format='YYYY-MM-DD'
            )
        ]),
        html.Div([
            html.Label("Select Indicators and Overlays"),
            dcc.Checklist(
                id='tech-indicator-checklist',
                options=[
                    {'label': 'SMA 20', 'value': 'sma'},
                    {'label': 'EMA 20', 'value': 'ema'},
                    {'label': 'Bollinger Bands', 'value': 'bb'},
                    {'label': 'RSI', 'value': 'rsi'},
                    {'label': 'MACD', 'value': 'macd'},
                    {'label': 'ATR', 'value': 'atr'},
                    {'label': 'OBV', 'value': 'obv'},
                    {'label': 'ADX', 'value': 'adx'},
                    {'label': 'Candlestick Patterns', 'value': 'patterns'}
                ],
                value=['sma', 'ema', 'patterns'],  # Default selected
                inline=True
            )
        ]),
        dcc.Tabs(id='tech-tabs', value='main_chart', children=[
            dcc.Tab(label='Main Chart (Candlestick)', value='main_chart', children=[
                dcc.Loading(
                    id="loading-tech-main-chart",
                    children=[dcc.Graph(id='tech-main-chart', style={'height': '600px'})],
                    type="default"
                )
            ]),
            dcc.Tab(label='Volume Indicators', value='volume_indicators', children=[
                dcc.Loading(
                    id="loading-tech-volume-chart",
                    children=[dcc.Graph(id='tech-volume-chart', style={'height': '400px'})],
                    type="default"
                )
            ]),
            dcc.Tab(label='Trend Indicators', value='trend_indicators', children=[
                dcc.Loading(
                    id="loading-tech-trend-chart",
                    children=[dcc.Graph(id='tech-trend-chart', style={'height': '400px'})],
                    type="default"
                )
            ]),
            dcc.Tab(label='Oscillators', value='oscillators', children=[
                dcc.Loading(
                    id="loading-tech-oscillator-chart",
                    children=[dcc.Graph(id='tech-oscillator-chart', style={'height': '400px'})],
                    type="default"
                )
            ])
        ]),
        dcc.Loading(
            id="loading-tech-table",
            children=[
                html.Div([
                    html.H2("Technical Indicators and Signals"),
                    html.Div(id='tech-table')
                ])
            ],
            type="default"
        )
    ])

def forecasting_layout():
    tickers = get_available_tickers()
    return html.Div([
        html.H1("Forecasting"),
        ticker_dropdown(tickers, 'forecast-ticker-dropdown'),
        html.Div([
            html.Label("Forecast Type"),
            dcc.Dropdown(
                id='forecast-type-dropdown',
                options=[
                    {'label': 'ARIMA', 'value': 'arima'},
                    {'label': 'Exponential Smoothing', 'value': 'exp_smoothing'},
                    {'label': 'Linear Regression', 'value': 'linear_regression'}
                ],
                value='arima'
            )
        ]),
        html.Div([
            html.Label("Forecast Horizon (Months)"),
            dcc.Dropdown(
                id='forecast-horizon-dropdown',
                options=[
                    {'label': '6 Months', 'value': 6},
                    {'label': '12 Months', 'value': 12},
                    {'label': '18 Months', 'value': 18},
                    {'label': '24 Months', 'value': 24}
                ],
                value=12
            )
        ]),
        html.Div([
            html.Label("Data to Forecast"),
            dcc.Dropdown(
                id='forecast-data-dropdown',
                options=[
                    {'label': 'Stock Price', 'value': 'price'},
                    {'label': 'ROE (Return on Equity)', 'value': 'compute_return_on_equity'},
                    {'label': 'ROA (Return on Assets)', 'value': 'compute_return_on_assets'},
                    {'label': 'Debt-to-Equity Ratio', 'value': 'compute_debt_to_equity_ratio'},
                    {'label': 'Current Ratio', 'value': 'compute_current_ratio'},
                    {'label': 'Net Profit Margin', 'value': 'compute_net_profit_margin'}
                ],
                value='price'
            )
        ]),
        html.Button('Generate Forecast', id='generate-forecast-btn', n_clicks=0),
        dcc.Loading(
            id="loading-forecast-chart",
            children=[
                html.Div([
                    html.H2("Forecast Chart"),
                    dcc.Graph(id='forecast-chart')
                ])
            ],
            type="default"
        ),
        dcc.Loading(
            id="loading-forecast-table",
            children=[
                html.Div([
                    html.H2("Forecast Values and Metrics"),
                    html.Div(id='forecast-table')
                ])
            ],
            type="default"
        )
    ])

# Base layout function with navigation using dcc.Tabs and dcc.Location for routing
def portfolio_layout():
    # Load tickers from config
    config_path = os.path.join(os.path.dirname(__file__), '../../config/settings.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    tickers = config.get('tickers', [])
    return html.Div([
        html.H1("Portfolio Analysis"),
        html.Div([
            html.Label("Select Tickers for Portfolio"),
            dcc.Dropdown(
                id='portfolio-ticker-dropdown',
                options=[{'label': t, 'value': t} for t in tickers],
                multi=True,
                value=[],
                placeholder="Select tickers"
            )
        ]),
        html.Div(id='portfolio-weight-inputs'),  # Dynamic inputs for weights
        html.Button('Create Portfolio', id='create-portfolio-btn', n_clicks=0),
        html.Div([
            html.H2("Portfolio Summary"),
            html.Div(id='portfolio-summary-table')
        ]),
        html.Div([
            html.H2("Portfolio Asset Allocation"),
            dcc.Graph(id='portfolio-pie-chart')
        ]),
        html.Div([
            html.H2("Portfolio Performance vs Benchmark"),
            dcc.Graph(id='portfolio-performance-chart')
        ]),
        html.Div([
            html.H2("Portfolio Risk Metrics"),
            html.Div(id='portfolio-risk-table')
        ])
    ])

def validation_audit_layout():
    # Load tickers from config
    config_path = os.path.join(os.path.dirname(__file__), '../../config/settings.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    tickers = config.get('tickers', [])
    return html.Div([
        html.H1("Validation/Audit"),
        ticker_dropdown(tickers, 'va-ticker-dropdown'),
        period_dropdown('va-period-dropdown'),
        html.Div([
            html.Label("Fiscal Date"),
            dcc.Dropdown(id='va-fiscal-date-dropdown', options=[], value=None)
        ]),
        html.Div([
            html.Label("Filter by Validation Type"),
            dcc.Dropdown(
                id='va-type-filter',
                options=[
                    {'label': 'All', 'value': 'all'},
                    {'label': 'Altman Z-Score', 'value': 'altman'},
                    {'label': 'Piotroski F-Score', 'value': 'piotroski'},
                    {'label': 'DuPont Analysis', 'value': 'dupont'},
                ],
                value='all'
            )
        ]),
        html.Button('Export CSV', id='va-export-btn', n_clicks=0),
        html.Div(id='va-summary-stats'),
        html.Div([
            html.H2("Audit Report"),
            html.Div(id='va-table')
        ])
    ])

def login_layout():
    return html.Div([
        html.H1("MyCFATool Login"),
        html.Div([
            html.Label("Username"),
            dcc.Input(id='username-input', type='text', placeholder='Enter username'),
        ]),
        html.Div([
            html.Label("Password"),
            dcc.Input(id='password-input', type='password', placeholder='Enter password'),
        ]),
        html.Div([
            html.Label("API Key (for registration)"),
            dcc.Input(id='api-key-input', type='text', placeholder='Enter FMP API key'),
        ]),
        html.Button('Login', id='login-btn'),
        html.Button('Register', id='register-btn'),
        html.Div(id='auth-msg')
    ])

def base_layout():
    if not current_user.is_authenticated:
        return login_layout()

    base_div = html.Div([
        dcc.Location(id='url', refresh=False),
        html.Div([
            html.P(f"Logged in as {current_user.username}"),
            html.Button('Logout', id='logout-btn')
        ]),
        dcc.Tabs(id='tabs', value='overview', children=[
            dcc.Tab(label='Overview', value='overview'),
            dcc.Tab(label='Financial Statements', value='financial_statements'),
            dcc.Tab(label='Ratio Analysis', value='ratio_analysis'),
            dcc.Tab(label='Risk Metrics', value='risk_metrics'),
            dcc.Tab(label='Valuation', value='valuation'),
            dcc.Tab(label='Peer Comparison', value='peer_comparison'),
            dcc.Tab(label='Technicals', value='technicals'),
            dcc.Tab(label='Forecasting', value='forecasting'),
            dcc.Tab(label='Portfolio', value='portfolio'),
            dcc.Tab(label='Validation/Audit', value='validation_audit'),
        ]),
        html.Div(id='page-content')
    ])
    if dbc:
        return dbc.Container(base_div)
    else:
        return base_div