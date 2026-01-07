# app.py - Main Dash application for risk management dashboard
"""
Institutional-grade risk management dashboard with interactive visualizations,
real-time monitoring, and customizable views.
"""

import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from risk_management import RiskFramework, RiskConfig
from filters import FilterManager

# Initialize the Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="Risk Management Dashboard",
    update_title=None,
)

# Database path
DB_PATH = "../../risk_management.db"

# Initialize risk framework and filter manager
config = RiskConfig()
risk_framework = None
filter_manager = None

def get_risk_framework():
    """Get or create risk framework instance"""
    global risk_framework
    if risk_framework is None:
        try:
            risk_framework = RiskFramework(config, DB_PATH)
        except Exception as e:
            print(f"Warning: Could not initialize risk framework: {e}")
            return None
    return risk_framework

def get_filter_manager():
    """Get or create filter manager instance"""
    global filter_manager
    if filter_manager is None:
        filter_manager = FilterManager(DB_PATH)
    return filter_manager

def get_database_connection():
    """Get database connection for dashboard queries"""
    try:
        return sqlite3.connect(DB_PATH)
    except Exception as e:
        print(f"Warning: Could not connect to database: {e}")
        return None

def get_available_filters():
    """Get available filter options from database"""
    conn = get_database_connection()
    if not conn:
        return {'symbols': [], 'sectors': []}

    try:
        # Get unique symbols from positions (placeholder - would need actual position table)
        cursor = conn.cursor()

        # For now, return sample data
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA']
        sectors = ['Technology', 'Healthcare', 'Financials', 'Consumer', 'Energy']

        return {
            'symbols': [{'label': s, 'value': s} for s in symbols],
            'sectors': [{'label': s, 'value': s} for s in sectors]
        }

    except Exception as e:
        print(f"Error getting filter options: {e}")
        return {'symbols': [], 'sectors': []}
    finally:
        conn.close()

# App layout
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("Risk Management Dashboard", className="text-center my-4"),
            html.P("Real-time portfolio risk monitoring and analytics", className="text-center text-muted")
        ])
    ]),

    # Navigation tabs
    dbc.Row([
        dbc.Col([
            dbc.Tabs(id="main-tabs", active_tab="overview", children=[
                dbc.Tab(label="Portfolio Overview", tab_id="overview"),
                dbc.Tab(label="Risk Metrics", tab_id="risk"),
                dbc.Tab(label="Greeks Exposure", tab_id="greeks"),
                dbc.Tab(label="P&L Analysis", tab_id="pnl"),
                dbc.Tab(label="Alerts & Notifications", tab_id="alerts"),
                dbc.Tab(label="Backtesting", tab_id="backtest"),
            ])
        ])
    ], className="my-3"),

    # Filters section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Filters & Views"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Underlying Symbols"),
                            dcc.Dropdown(
                                id="symbol-filter",
                                options=[],  # Will be populated dynamically
                                multi=True,
                                placeholder="Select symbols..."
                            )
                        ], md=3),
                        dbc.Col([
                            html.Label("Sectors"),
                            dcc.Dropdown(
                                id="sector-filter",
                                options=[],  # Will be populated dynamically
                                multi=True,
                                placeholder="Select sectors..."
                            )
                        ], md=2),
                        dbc.Col([
                            html.Label("Brokers"),
                            dcc.Dropdown(
                                id="broker-filter",
                                options=[],  # Will be populated dynamically
                                multi=True,
                                placeholder="Select brokers..."
                            )
                        ], md=2),
                        dbc.Col([
                            html.Label("Time Range"),
                            dcc.DatePickerRange(
                                id="date-range",
                                start_date=datetime.now() - timedelta(days=30),
                                end_date=datetime.now(),
                            )
                        ], md=3),
                        dbc.Col([
                            html.Label("Filter Logic"),
                            dcc.RadioItems(
                                id="filter-logic",
                                options=[
                                    {'label': 'AND (all conditions)', 'value': 'AND'},
                                    {'label': 'OR (any condition)', 'value': 'OR'}
                                ],
                                value='AND',
                                className="mb-2"
                            ),
                            dbc.Button("Apply Filters", id="apply-filters", color="primary"),
                            dbc.Button("Reset", id="reset-filters", color="secondary", className="ms-2"),
                            dbc.Button("Save Preset", id="save-preset", color="info", className="ms-2"),
                        ], md=3),
                        dbc.Col([
                            html.Label("Filter Presets"),
                            dcc.Dropdown(
                                id="preset-dropdown",
                                options=[],  # Will be populated with saved presets
                                placeholder="Select preset...",
                                className="mb-2"
                            ),
                            dbc.Input(
                                id="preset-name-input",
                                type="text",
                                placeholder="Preset name...",
                                className="mb-2"
                            ),
                            dbc.Button("Load Preset", id="load-preset", color="success", size="sm"),
                            dbc.Button("Delete Preset", id="delete-preset", color="danger", size="sm", className="ms-2"),
                        ], md=3),
                    ])
                ])
            ])
        ])
    ], className="my-3"),

    # Main content area
    dbc.Row([
        dbc.Col([
            html.Div(id="tab-content")
        ])
    ]),

    # Footer
    dbc.Row([
        dbc.Col([
            html.Hr(),
            html.P("Risk Management System v2.0 | Real-time data updates every 30 seconds",
                   className="text-center text-muted small")
        ])
    ]),

    # Interval for real-time updates
    dcc.Interval(id="update-interval", interval=30*1000, n_intervals=0),  # 30 seconds

    # Store for filter state
    dcc.Store(id="filter-state", data={}),
    dcc.Store(id="last-update", data=datetime.now().isoformat()),

], fluid=True, className="p-4")


# Callback to populate filter dropdowns and presets
@app.callback(
    Output("symbol-filter", "options"),
    Output("sector-filter", "options"),
    Output("broker-filter", "options"),
    Output("preset-dropdown", "options"),
    Input("update-interval", "n_intervals")
)
def populate_filters_and_presets(n):
    """Populate filter dropdowns and preset list"""
    fm = get_filter_manager()
    symbols = fm.get_available_symbols()
    sectors = fm.get_available_sectors()
    brokers = fm.get_available_brokers()
    presets = [{'label': preset, 'value': preset} for preset in fm.get_filter_presets()]
    return symbols, sectors, brokers, presets

# Callback for tab content
@app.callback(
    Output("tab-content", "children"),
    Input("main-tabs", "active_tab"),
    Input("filter-state", "data")
)
def render_tab_content(active_tab, filter_state):
    """Render content based on active tab"""

    if active_tab == "overview":
        return get_portfolio_overview(filter_state)
    elif active_tab == "risk":
        return get_risk_metrics_view(filter_state)
    elif active_tab == "greeks":
        return get_greeks_exposure_view(filter_state)
    elif active_tab == "pnl":
        return get_pnl_analysis_view(filter_state)
    elif active_tab == "alerts":
        return get_alerts_view(filter_state)
    elif active_tab == "backtest":
        return get_backtesting_view(filter_state)
    else:
        return html.Div("Tab content not implemented yet")


# Helper functions for tab content
def get_portfolio_overview(filter_state):
    """Generate portfolio overview tab content"""
    risk_framework = get_risk_framework()
    filter_manager = get_filter_manager()

    if not risk_framework:
        return html.Div("Risk framework not available", className="alert alert-warning")

    try:
        dashboard_data = risk_framework.get_dashboard_data()

        # Apply filters to the data
        if filter_state:
            # Filter alerts data
            if dashboard_data.get('alerts_data'):
                alerts_df = pd.DataFrame(dashboard_data['alerts_data'])
                filtered_alerts = filter_manager.apply_filters(alerts_df, filter_state)
                dashboard_data['alerts'] = filtered_alerts.to_dict('records') if not filtered_alerts.empty else []

            # Filter positions data
            if dashboard_data.get('positions'):
                positions_df = pd.DataFrame(dashboard_data['positions'])
                filtered_positions = filter_manager.apply_filters(positions_df, filter_state)
                dashboard_data['positions'] = filtered_positions.to_dict('records') if not filtered_positions.empty else []

        return dbc.Container([
            dbc.Row([
                # Key metrics cards
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Portfolio Value", className="card-title"),
                            html.H2(f"${dashboard_data['portfolio_value']:,.0f}", className="text-primary"),
                        ])
                    ])
                ], md=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("VaR (95%)", className="card-title"),
                            html.H2(f"${dashboard_data['risk_metrics']['var_95']:,.0f}",
                                   className="text-warning"),
                        ])
                    ])
                ], md=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Active Positions", className="card-title"),
                            html.H2(f"{len(dashboard_data['positions'])}", className="text-info"),
                        ])
                    ])
                ], md=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Alerts", className="card-title"),
                            html.H2(f"{len(dashboard_data['alerts'])}",
                                   className="text-danger" if dashboard_data['alerts'] else "text-success"),
                        ])
                    ])
                ], md=3),
            ], className="my-3"),

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Recent Alerts"),
                        dbc.CardBody([
                            html.Ul([
                                html.Li(alert, className="text-danger small")
                                for alert in dashboard_data['alerts'][:5]
                            ]) if dashboard_data['alerts'] else html.P("No active alerts", className="text-success")
                        ])
                    ])
                ], md=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Portfolio Composition"),
                        dbc.CardBody([
                            dcc.Graph(
                                figure=create_portfolio_composition_chart(dashboard_data['positions']),
                                style={'height': '300px'}
                            )
                        ])
                    ])
                ], md=6),
            ])
        ])

    except Exception as e:
        return html.Div(f"Error loading portfolio overview: {str(e)}", className="alert alert-danger")


def create_portfolio_composition_chart(positions):
    """Create portfolio composition visualization"""
    if not positions:
        return go.Figure()

    df = pd.DataFrame(positions)
    if 'value' not in df.columns:
        return go.Figure()

    fig = px.pie(df, values='value', names=df.index.astype(str),
                title="Portfolio Composition by Position")
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    return fig


def get_risk_metrics_view(filter_state):
    """Generate risk metrics tab content"""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H3("Risk Metrics Dashboard"),
                html.P("Comprehensive risk analytics and monitoring"),
                html.Div("Risk metrics visualizations will be implemented here")
            ])
        ])
    ])


def get_greeks_exposure_view(filter_state):
    """Generate Greeks exposure tab content"""
    risk_framework = get_risk_framework()
    filter_manager = get_filter_manager()

    if not risk_framework:
        return html.Div("Risk framework not available", className="alert alert-warning")

    try:
        # Get Greeks data
        greeks_data = risk_framework.aggregate_daily_greeks()

        # Create Greeks exposure heatmap
        heatmap_fig = create_greeks_heatmap(greeks_data)

        # Get current positions for detailed breakdown
        positions = risk_framework.get_current_positions()

        # Apply filters if any
        if filter_state and positions:
            positions_df = pd.DataFrame(positions)
            filtered_positions = filter_manager.apply_filters(positions_df, filter_state)
            positions = filtered_positions.to_dict('records') if not filtered_positions.empty else []

        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H3("Greeks Exposure Analysis"),
                    html.P("Portfolio sensitivity analysis across all Greek measures"),
                    html.Hr()
                ])
            ]),

            # Greeks Heatmap
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Portfolio Greeks Heatmap"),
                        dbc.CardBody([
                            dcc.Graph(
                                figure=heatmap_fig,
                                style={'height': '400px'}
                            )
                        ])
                    ])
                ], md=8),

                # Greeks Summary Cards
                dbc.Col([
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H6("Net Delta", className="card-title text-center"),
                                    html.H4(f"{greeks_data.get('delta', 0):.2f}",
                                           className="text-center text-primary")
                                ])
                            ])
                        ], md=6),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H6("Net Gamma", className="card-title text-center"),
                                    html.H4(f"{greeks_data.get('gamma', 0):.2f}",
                                           className="text-center text-info")
                                ])
                            ])
                        ], md=6),
                    ], className="mb-3"),

                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H6("Net Theta", className="card-title text-center"),
                                    html.H4(f"{greeks_data.get('theta', 0):.2f}",
                                           className="text-center text-success")
                                ])
                            ])
                        ], md=6),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H6("Net Vega", className="card-title text-center"),
                                    html.H4(f"{greeks_data.get('vega', 0):.2f}",
                                           className="text-center text-warning")
                                ])
                            ])
                        ], md=6),
                    ])
                ], md=4)
            ], className="mb-4"),

            # Position-level Greeks breakdown
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Position Greeks Breakdown"),
                        dbc.CardBody([
                            html.Div(
                                create_position_greeks_table(positions),
                                style={'maxHeight': '400px', 'overflowY': 'auto'}
                            )
                        ])
                    ])
                ])
            ])
        ])

    except Exception as e:
        return html.Div(f"Error loading Greeks exposure view: {str(e)}", className="alert alert-danger")


def create_greeks_heatmap(greeks_data):
    """Create a heatmap visualization of portfolio Greeks."""
    greeks = ['delta', 'gamma', 'theta', 'vega', 'rho']
    values = [greeks_data.get(greek, 0) for greek in greeks]

    # Create a simple bar chart for now (can be enhanced to true heatmap)
    fig = go.Figure()

    # Add bars for each Greek
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    for i, (greek, value) in enumerate(zip(greeks, values)):
        fig.add_trace(go.Bar(
            x=[greek.upper()],
            y=[value],
            name=greek.upper(),
            marker_color=colors[i % len(colors)],
            showlegend=False
        ))

    fig.update_layout(
        title="Portfolio Greeks Exposure",
        xaxis_title="Greek",
        yaxis_title="Exposure Value",
        template="plotly_white",
        hovermode="x unified",
        xaxis=dict(
            showgrid=True,
            zeroline=True,
            showline=True
        ),
        yaxis=dict(
            showgrid=True,
            zeroline=True,
            showline=True
        )
    )

    # Add range selector for zoom
    fig.update_xaxes(rangeslider_visible=False)

    return fig


def create_position_greeks_table(positions):
    """Create a table showing Greeks for each position."""
    if not positions:
        return html.P("No position data available")

    # Create table data
    table_header = [
        html.Thead(html.Tr([
            html.Th("Symbol"),
            html.Th("Delta"),
            html.Th("Gamma"),
            html.Th("Theta"),
            html.Th("Vega"),
            html.Th("Rho")
        ]))
    ]

    table_rows = []
    for pos in positions[:20]:  # Limit to first 20 positions
        table_rows.append(html.Tr([
            html.Td(pos.get('symbol', 'N/A')),
            html.Td(f"{pos.get('delta', 0):.3f}"),
            html.Td(f"{pos.get('gamma', 0):.3f}"),
            html.Td(f"{pos.get('theta', 0):.3f}"),
            html.Td(f"{pos.get('vega', 0):.3f}"),
            html.Td(f"{pos.get('rho', 0):.3f}")
        ]))

    return dbc.Table(table_header + [html.Tbody(table_rows)], bordered=True, hover=True, responsive=True, size="sm")


def get_pnl_analysis_view(filter_state):
    """Generate P&L analysis tab content"""
    try:
        # Create sample P&L time series data (would be replaced with real data)
        pnl_data = generate_sample_pnl_data()

        # Apply filters if provided
        if filter_state:
            # Filter logic can be applied here based on symbols, dates, etc.
            pass

        # Create P&L time series chart
        pnl_chart = create_pnl_time_series_chart(pnl_data)

        # Create attribution waterfall (placeholder)
        attribution_data = generate_sample_attribution_data()
        attribution_chart = create_attribution_waterfall_chart(attribution_data)

        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H3("P&L Analysis & Attribution"),
                    html.P("Profit/loss tracking and performance attribution analysis"),
                    html.Hr()
                ])
            ]),

            # P&L Time Series Chart
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Portfolio P&L Time Series"),
                        dbc.CardBody([
                            dcc.Graph(
                                figure=pnl_chart,
                                style={'height': '400px'}
                            )
                        ])
                    ])
                ], md=8),

                # P&L Summary Cards
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Total P&L", className="card-title text-center"),
                            html.H4("$12,450",
                                   className="text-center text-success" if pnl_data['total_pnl'] >= 0 else "text-center text-danger"),
                            html.Small("Last 30 days", className="text-muted text-center d-block")
                        ])
                    ], className="mb-3"),

                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Daily Avg P&L", className="card-title text-center"),
                            html.H4("$415",
                                   className="text-center text-info"),
                            html.Small("30-day average", className="text-muted text-center d-block")
                        ])
                    ], className="mb-3"),

                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Best Day", className="card-title text-center"),
                            html.H4("$2,150",
                                   className="text-center text-success"),
                            html.Small("Peak performance", className="text-muted text-center d-block")
                        ])
                    ])
                ], md=4)
            ], className="mb-4"),

            # Attribution Analysis
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Performance Attribution Waterfall"),
                        dbc.CardBody([
                            dcc.Graph(
                                figure=attribution_chart,
                                style={'height': '350px'}
                            )
                        ])
                    ])
                ], md=6),

                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Attribution Summary"),
                        dbc.CardBody([
                            html.Div([
                                html.P("• Premium Decay: $8,200 (65.9%)", className="mb-1"),
                                html.P("• Underlying Movement: $2,100 (16.9%)", className="mb-1"),
                                html.P("• Volatility Changes: $1,850 (14.9%)", className="mb-1"),
                                html.P("• Interest Rate Impact: $300 (2.3%)", className="mb-1"),
                                html.Hr(),
                                html.P("• Total Explained: $12,450 (100%)", className="fw-bold mb-0")
                            ])
                        ])
                    ])
                ], md=6)
            ])
        ])

    except Exception as e:
        return html.Div(f"Error loading P&L analysis: {str(e)}", className="alert alert-danger")


def generate_sample_pnl_data():
    """Generate sample P&L data for demonstration."""
    dates = pd.date_range(start='2024-12-01', end='2024-12-31', freq='D')
    np.random.seed(42)  # For reproducible results

    # Generate realistic P&L data with some trend and volatility
    base_pnl = np.cumsum(np.random.normal(400, 800, len(dates)))

    pnl_data = {
        'dates': dates,
        'pnl': base_pnl,
        'total_pnl': base_pnl[-1] if len(base_pnl) > 0 else 0,
        'daily_pnl': np.diff(base_pnl, prepend=0)
    }

    return pnl_data


def create_pnl_time_series_chart(pnl_data):
    """Create P&L time series visualization."""
    fig = go.Figure()

    # Add P&L line
    fig.add_trace(go.Scatter(
        x=pnl_data['dates'],
        y=pnl_data['pnl'],
        mode='lines+markers',
        name='Portfolio P&L',
        line=dict(color='#2ca02c', width=2),
        fill='tozeroy',
        fillcolor='rgba(44, 160, 44, 0.1)'
    ))

    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

    # Add interactive buttons for different time periods
    fig.update_layout(
        title="Portfolio P&L Over Time",
        xaxis_title="Date",
        yaxis_title="P&L ($)",
        template="plotly_white",
        hovermode="x unified",
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=7, label="1W", step="day", stepmode="backward"),
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=3, label="3M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(visible=True),
            type="date"
        ),
        yaxis=dict(
            autorange=True,
            fixedrange=False
        ),
        updatemenus=[
            dict(
                type="buttons",
                buttons=[
                    dict(label="Linear", method="relayout", args=[{"yaxis.type": "linear"}]),
                    dict(label="Log", method="relayout", args=[{"yaxis.type": "log"}])
                ],
                direction="right",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.1,
                xanchor="left",
                y=1.1,
                yanchor="top"
            )
        ]
    )

    return fig


def generate_sample_attribution_data():
    """Generate sample attribution data."""
    components = [
        'Premium Decay',
        'Underlying Movement',
        'Volatility Changes',
        'Interest Rate Impact'
    ]

    values = [8200, 2100, 1850, 300]

    return {
        'components': components,
        'values': values
    }


def create_attribution_waterfall_chart(attribution_data):
    """Create attribution waterfall chart."""
    fig = go.Figure()

    # Calculate cumulative values for waterfall
    values = attribution_data['values']
    cumulative = [0] + list(np.cumsum(values)[:-1])

    # Create waterfall bars
    fig.add_trace(go.Waterfall(
        name="Attribution",
        orientation="v",
        measure=["absolute"] * len(values),
        x=attribution_data['components'],
        y=values,
        base=cumulative,
        decreasing=dict(marker=dict(color="#d62728")),
        increasing=dict(marker=dict(color="#2ca02c")),
        totals=dict(marker=dict(color="#1f77b4")),
        connector=dict(mode="between", line=dict(width=2, color="rgb(63, 63, 63)"))
    ))

    fig.update_layout(
        title="Performance Attribution Breakdown",
        template="plotly_white",
        showlegend=False
    )

    return fig


def get_alerts_view(filter_state):
    """Generate alerts and notifications tab content with drill-down functionality"""
    try:
        # Get alerts data
        alerts_data = get_alerts_data()

        # Apply filters if provided
        filter_manager = get_filter_manager()
        if filter_state and alerts_data:
            alerts_df = pd.DataFrame(alerts_data)
            filtered_alerts = filter_manager.apply_filters(alerts_df, filter_state)
            alerts_data = filtered_alerts.to_dict('records') if not filtered_alerts.empty else []

        # Categorize alerts by severity
        critical_alerts = [a for a in alerts_data if a.get('severity') == 'critical']
        warning_alerts = [a for a in alerts_data if a.get('severity') == 'warning']
        info_alerts = [a for a in alerts_data if a.get('severity') == 'info']

        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H3("Alerts & Notifications Dashboard"),
                    html.P("Real-time risk alerts with drill-down analysis and management"),
                    html.Hr()
                ])
            ]),

            # Alert Summary Cards
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Critical Alerts", className="card-title text-center"),
                            html.H2(f"{len(critical_alerts)}",
                                   className="text-center text-danger"),
                            html.Small("Immediate action required", className="text-muted text-center d-block")
                        ])
                    ], className="mb-3")
                ], md=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Warning Alerts", className="card-title text-center"),
                            html.H2(f"{len(warning_alerts)}",
                                   className="text-center text-warning"),
                            html.Small("Monitor closely", className="text-muted text-center d-block")
                        ])
                    ], className="mb-3")
                ], md=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Info Alerts", className="card-title text-center"),
                            html.H2(f"{len(info_alerts)}",
                                   className="text-center text-info"),
                            html.Small("Informational notices", className="text-muted text-center d-block")
                        ])
                    ], className="mb-3")
                ], md=4),
            ], className="mb-4"),

            # Alert Tabs for Drill-down
            dbc.Row([
                dbc.Col([
                    dbc.Tabs([
                        dbc.Tab([
                            html.Div(create_alerts_table(critical_alerts, "critical"))
                        ], label=f"Critical ({len(critical_alerts)})", tab_id="critical"),

                        dbc.Tab([
                            html.Div(create_alerts_table(warning_alerts, "warning"))
                        ], label=f"Warnings ({len(warning_alerts)})", tab_id="warning"),

                        dbc.Tab([
                            html.Div(create_alerts_table(info_alerts, "info"))
                        ], label=f"Info ({len(info_alerts)})", tab_id="info"),

                        dbc.Tab([
                            html.Div(create_alert_history_chart())
                        ], label="History", tab_id="history"),
                    ], id="alerts-tabs", active_tab="critical")
                ])
            ]),

            # Alert Actions Panel
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Alert Management Actions"),
                        dbc.CardBody([
                            dbc.Button("Acknowledge Selected", color="primary", className="me-2"),
                            dbc.Button("Escalate Critical", color="danger", className="me-2"),
                            dbc.Button("Suppress Similar", color="warning", className="me-2"),
                            dbc.Button("Export Alerts", color="info"),
                            html.Hr(),
                            html.P("• Select alerts in the table above to perform bulk actions", className="small text-muted"),
                            html.P("• Critical alerts require immediate response", className="small text-danger"),
                            html.P("• Use filters to focus on specific symbols or alert types", className="small text-muted")
                        ])
                    ])
                ])
            ])
        ])

    except Exception as e:
        return html.Div(f"Error loading alerts view: {str(e)}", className="alert alert-danger")


def get_alerts_data():
    """Get current alerts data from risk monitoring system."""
    # In a real implementation, this would query the database
    # For now, return sample alerts
    return [
        {
            'timestamp': '2024-12-31T10:30:00',
            'symbol': 'AAPL',
            'severity': 'critical',
            'type': 'Greeks Breach',
            'message': 'Portfolio delta exceeded limit: 0.35 > 0.20',
            'details': 'Net delta exposure too high, recommend reducing position sizes',
            'action_required': 'Reduce position sizes by 15%'
        },
        {
            'timestamp': '2024-12-31T09:15:00',
            'symbol': 'MSFT',
            'severity': 'warning',
            'type': 'Liquidity Risk',
            'message': 'Bid-ask spread widening: $0.12 > $0.08',
            'details': 'Market liquidity deteriorating for MSFT options',
            'action_required': 'Monitor spread, consider position adjustment'
        },
        {
            'timestamp': '2024-12-31T08:45:00',
            'symbol': 'TSLA',
            'severity': 'info',
            'type': 'Volatility Spike',
            'message': 'Implied volatility increased by 15%',
            'details': 'Normal market movement detected',
            'action_required': 'Monitor for continued volatility'
        },
        {
            'timestamp': '2024-12-30T16:30:00',
            'symbol': 'GOOGL',
            'severity': 'warning',
            'type': 'Concentration Risk',
            'message': 'Technology sector exposure: 32% > 25%',
            'details': 'Portfolio over-concentrated in technology sector',
            'action_required': 'Diversify sector exposure'
        }
    ]


def create_alerts_table(alerts, severity):
    """Create interactive alerts table with drill-down capability."""
    if not alerts:
        return html.P(f"No {severity} alerts at this time.", className="text-muted")

    # Create color mapping for severity
    color_map = {
        'critical': 'danger',
        'warning': 'warning',
        'info': 'info'
    }

    table_header = [
        html.Thead(html.Tr([
            html.Th("Time", style={'width': '15%'}),
            html.Th("Symbol", style={'width': '10%'}),
            html.Th("Type", style={'width': '15%'}),
            html.Th("Message", style={'width': '35%'}),
            html.Th("Action", style={'width': '15%'}),
            html.Th("Select", style={'width': '10%'})
        ]))
    ]

    table_rows = []
    for i, alert in enumerate(alerts):
        table_rows.append(html.Tr([
            html.Td(alert['timestamp'][:19], className="small"),
            html.Td(html.B(alert['symbol'])),
            html.Td(html.Span(alert['type'], className=f"badge bg-{color_map.get(severity, 'secondary')}")),
            html.Td(alert['message'], className="small"),
            html.Td(alert['action_required'], className="small text-muted"),
            html.Td(dbc.Checkbox(id=f"alert-select-{i}"))
        ]))

    table = dbc.Table(
        table_header + [html.Tbody(table_rows)],
        bordered=True,
        hover=True,
        responsive=True,
        size="sm",
        className="alerts-table"
    )

    return table


def create_alert_history_chart():
    """Create alerts history visualization."""
    # Sample historical data
    dates = pd.date_range(start='2024-12-01', end='2024-12-31', freq='D')
    critical_counts = np.random.poisson(0.5, len(dates))
    warning_counts = np.random.poisson(2, len(dates))
    info_counts = np.random.poisson(5, len(dates))

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=dates, y=critical_counts,
        mode='lines+markers',
        name='Critical',
        line=dict(color='red', width=2),
        stackgroup='one'
    ))

    fig.add_trace(go.Scatter(
        x=dates, y=warning_counts,
        mode='lines+markers',
        name='Warning',
        line=dict(color='orange', width=2),
        stackgroup='one'
    ))

    fig.add_trace(go.Scatter(
        x=dates, y=info_counts,
        mode='lines+markers',
        name='Info',
        line=dict(color='blue', width=2),
        stackgroup='one'
    ))

    fig.update_layout(
        title="Alert Frequency History",
        xaxis_title="Date",
        yaxis_title="Number of Alerts",
        template="plotly_white",
        hovermode="x unified"
    )

    return dcc.Graph(figure=fig, style={'height': '400px'})


def get_backtesting_view(filter_state):
    """Generate backtesting tab content"""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H3("Backtesting & Performance Validation"),
                html.P("Historical testing and regime-based analysis"),
                html.Div("Backtesting results and analytics will be implemented here")
            ])
        ])
    ])


# Callback for filter application
@app.callback(
    Output("filter-state", "data"),
    Output("main-tabs", "active_tab"),  # Trigger content refresh
    Input("apply-filters", "n_clicks"),
    Input("reset-filters", "n_clicks"),
    State("symbol-filter", "value"),
    State("sector-filter", "value"),
    State("broker-filter", "value"),
    State("date-range", "start_date"),
    State("date-range", "end_date"),
    State("filter-logic", "value"),
    State("filter-state", "data"),
    prevent_initial_call=True
)
def update_filters(apply_clicks, reset_clicks, symbols, sectors, brokers, start_date, end_date, filter_logic, current_filters):
    """Update filter state based on user input"""
    ctx = dash.callback_context
    if not ctx.triggered:
        return current_filters, dash.no_update

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    fm = get_filter_manager()

    if trigger_id == "reset-filters":
        reset_filters = fm.reset_filters()
        return reset_filters, dash.no_update
    elif trigger_id == "apply-filters":
        new_filters = {
            'symbols': symbols or [],
            'sectors': sectors or [],
            'brokers': brokers or [],
            'start_date': start_date,
            'end_date': end_date,
            'logic': filter_logic or 'AND'
        }

        # Validate filters
        is_valid, error_msg = fm.validate_filters(new_filters)
        if not is_valid:
            # Could show error message to user here
            print(f"Filter validation error: {error_msg}")
            return current_filters, dash.no_update

        return new_filters, dash.no_update

    return current_filters, dash.no_update


# Callback for preset management
@app.callback(
    Output("filter-state", "data", allow_duplicate=True),
    Output("preset-dropdown", "options", allow_duplicate=True),
    Input("save-preset", "n_clicks"),
    Input("load-preset", "n_clicks"),
    Input("delete-preset", "n_clicks"),
    State("filter-state", "data"),
    State("preset-dropdown", "value"),
    State("preset-name-input", "value"),
    prevent_initial_call=True
)
def manage_presets(save_clicks, load_clicks, delete_clicks, current_filters, selected_preset, preset_name):
    """Handle preset save, load, and delete operations"""
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update

    fm = get_filter_manager()
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == "save-preset":
        if not current_filters:
            return dash.no_update, dash.no_update  # No filters to save

        # For now, use a default name - could add a modal for name input
        preset_name = preset_name or f"Preset_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        success = fm.save_filter_preset(preset_name, current_filters)
        if success:
            # Refresh preset list
            presets = [{'label': preset, 'value': preset} for preset in fm.get_filter_presets()]
            return current_filters, presets

    elif trigger_id == "load-preset" and selected_preset:
        loaded_filters = fm.load_filter_preset(selected_preset)
        if loaded_filters:
            return loaded_filters, dash.no_update

    elif trigger_id == "delete-preset" and selected_preset:
        # Note: FilterManager doesn't have delete method yet, would need to add
        # For now, just refresh the list
        presets = [{'label': preset, 'value': preset} for preset in fm.get_filter_presets()]
        return dash.no_update, presets

    return dash.no_update, dash.no_update


# Callback for real-time updates
@app.callback(
    Output("last-update", "data"),
    Input("update-interval", "n_intervals")
)
def update_timestamp(n):
    """Update timestamp for real-time data"""
    return datetime.now().isoformat()


if __name__ == "__main__":
    print("Starting Risk Management Dashboard...")
    print("Access at: http://127.0.0.1:8050/")
    app.run_server(debug=True, host='0.0.0.0', port=8050)