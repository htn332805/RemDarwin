"""
RemDarwin LLM Trading Dashboard - Human-in-the-Loop Interface

A comprehensive Streamlit dashboard for monitoring, reviewing, and manually
overriding LLM-enhanced trading decisions in real-time.

Features:
- Live trade queue monitoring
- Decision review and override interface
- Historical performance analytics
- System health and monitoring
- Confidence score visualization
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
from typing import Dict, Any, List, Optional
import logging

# Configure page
st.set_page_config(
    page_title="RemDarwin LLM Trading Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()

# Mock data for demonstration (would connect to actual systems in production)
def get_mock_trade_queue():
    """Generate mock pending trades for demonstration"""
    trades = []
    strategies = ['covered_call', 'cash_secured_put']
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA']

    for i in range(8):
        trade = {
            'trade_id': f'TRADE_{i:03d}',
            'symbol': np.random.choice(symbols),
            'strategy': np.random.choice(strategies),
            'expiration': (datetime.now() + timedelta(days=np.random.randint(7, 45))).strftime('%Y-%m-%d'),
            'strike_price': np.round(np.random.uniform(100, 400), 2),
            'current_price': np.round(np.random.uniform(80, 380), 2),
            'llm_confidence': np.round(np.random.uniform(0.3, 0.9), 2),
            'quantitative_score': np.round(np.random.uniform(50, 90), 1),
            'composite_score': np.round(np.random.uniform(45, 85), 1),
            'decision': np.random.choice(['BUY', 'HOLD', 'AVOID'], p=[0.4, 0.4, 0.2]),
            'submitted_at': datetime.now() - timedelta(minutes=np.random.randint(1, 60)),
            'market_regime': np.random.choice(['bull', 'bear', 'sideways']),
            'volatility_environment': np.random.choice(['low', 'normal', 'high'])
        }
        trades.append(trade)

    return pd.DataFrame(trades)

def get_system_health_data():
    """Generate mock system health metrics"""
    return {
        'api_status': 'healthy',
        'llm_status': 'operational',
        'database_status': 'connected',
        'last_api_call': datetime.now() - timedelta(seconds=30),
        'total_requests_today': 247,
        'success_rate_24h': 0.967,
        'avg_latency_ms': 1250,
        'total_cost_today': 2.47,
        'active_alerts': 1,
        'pending_trades': 8,
        'processed_trades_24h': 23
    }

def get_performance_metrics():
    """Generate mock performance metrics"""
    dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
    performance = []

    for date in dates:
        performance.append({
            'date': date,
            'daily_return': np.random.normal(0.001, 0.02),
            'win_rate': np.random.uniform(0.55, 0.75),
            'sharpe_ratio': np.random.uniform(1.2, 2.1),
            'total_trades': np.random.randint(15, 35),
            'profitable_trades': np.random.randint(8, 25)
        })

    return pd.DataFrame(performance)

# Main dashboard
def main():
    st.title("🤖 RemDarwin LLM Trading Dashboard")
    st.markdown("*Human-in-the-Loop Trading Decision Support*")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Controls")

        # Auto-refresh toggle
        auto_refresh = st.checkbox("Auto Refresh", value=True)

        # Refresh interval
        refresh_interval = st.slider("Refresh Interval (seconds)", 10, 300, 30)

        # Risk level filter
        risk_filter = st.multiselect(
            "Risk Level Filter",
            ["Low", "Moderate", "High"],
            default=["Low", "Moderate", "High"]
        )

        # Confidence threshold
        confidence_threshold = st.slider("Min Confidence Threshold", 0.0, 1.0, 0.4)

        st.markdown("---")

        # System status
        health = get_system_health_data()
        st.metric("System Status", health['api_status'].upper(),
                 delta="-" if health['active_alerts'] > 0 else "✓")

        if st.button("🔄 Manual Refresh"):
            st.session_state.last_refresh = datetime.now()
            st.rerun()

    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Trade Queue",
        "🎯 Decision Review",
        "📈 Performance",
        "🔧 System Health"
    ])

    with tab1:
        show_trade_queue()

    with tab2:
        show_decision_review()

    with tab3:
        show_performance_analytics()

    with tab4:
        show_system_health()

    # Auto-refresh logic
    if auto_refresh:
        time_since_refresh = (datetime.now() - st.session_state.last_refresh).seconds
        if time_since_refresh >= refresh_interval:
            st.session_state.last_refresh = datetime.now()
            time.sleep(0.1)  # Brief pause
            st.rerun()

def show_trade_queue():
    """Display pending trade queue with LLM recommendations"""
    st.header("📊 Pending Trade Queue")

    # Get trade data
    trades_df = get_mock_trade_queue()

    # Filter by confidence threshold
    confidence_threshold = st.session_state.get('confidence_threshold', 0.4)
    filtered_trades = trades_df[trades_df['llm_confidence'] >= confidence_threshold]

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Pending Trades", len(filtered_trades))
    with col2:
        avg_confidence = filtered_trades['llm_confidence'].mean()
        st.metric("Avg Confidence", ".1%")
    with col3:
        buy_trades = len(filtered_trades[filtered_trades['decision'] == 'BUY'])
        st.metric("Buy Recommendations", buy_trades)
    with col4:
        high_conf = len(filtered_trades[filtered_trades['llm_confidence'] > 0.8])
        st.metric("High Confidence", high_conf)

    # Trade queue table
    st.subheader("Trade Recommendations")

    # Format the dataframe for display
    display_df = filtered_trades.copy()
    display_df['submitted_at'] = display_df['submitted_at'].dt.strftime('%H:%M:%S')

    # Color coding for confidence
    def color_confidence(val):
        if val > 0.8:
            return 'background-color: #d4edda; color: #155724'  # Green
        elif val > 0.6:
            return 'background-color: #fff3cd; color: #856404'  # Yellow
        else:
            return 'background-color: #f8d7da; color: #721c24'  # Red

    styled_df = display_df.style.applymap(color_confidence, subset=['llm_confidence'])

    st.dataframe(
        styled_df,
        column_config={
            "trade_id": st.column_config.TextColumn("Trade ID", width="small"),
            "symbol": st.column_config.TextColumn("Symbol", width="small"),
            "strategy": st.column_config.TextColumn("Strategy"),
            "llm_confidence": st.column_config.NumberColumn("LLM Confidence", format="%.1%"),
            "quantitative_score": st.column_config.NumberColumn("Quant Score", format="%.1f"),
            "composite_score": st.column_config.NumberColumn("Composite", format="%.1f"),
            "decision": st.column_config.TextColumn("Decision"),
            "market_regime": st.column_config.TextColumn("Regime")
        },
        hide_index=True,
        use_container_width=True
    )

    # Quick actions
    st.subheader("Quick Actions")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("✅ Approve All High Confidence", type="primary"):
            high_conf_trades = filtered_trades[filtered_trades['llm_confidence'] > 0.8]
            st.success(f"Approved {len(high_conf_trades)} high-confidence trades")

    with col2:
        if st.button("👁️ Review Borderline Cases"):
            borderline = filtered_trades[
                (filtered_trades['llm_confidence'] > 0.4) &
                (filtered_trades['llm_confidence'] < 0.7)
            ]
            st.info(f"{len(borderline)} borderline trades need review")

    with col3:
        if st.button("🚫 Reject Low Confidence"):
            low_conf = filtered_trades[filtered_trades['llm_confidence'] < 0.5]
            st.warning(f"Rejected {len(low_conf)} low-confidence trades")

def show_decision_review():
    """Interactive decision review and override interface"""
    st.header("🎯 Decision Review & Override")

    trades_df = get_mock_trade_queue()

    # Select trade for detailed review
    trade_options = [f"{row['trade_id']} - {row['symbol']} ({row['decision']})"
                    for _, row in trades_df.iterrows()]
    selected_trade = st.selectbox("Select Trade for Review", trade_options)

    if selected_trade:
        trade_id = selected_trade.split(' - ')[0]
        trade_data = trades_df[trades_df['trade_id'] == trade_id].iloc[0]

        # Trade details
        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("📈 Trade Details")
            st.write(f"**Symbol:** {trade_data['symbol']}")
            st.write(f"**Strategy:** {trade_data['strategy']}")
            st.write(f"**Expiration:** {trade_data['expiration']}")
            st.write(f"**Strike:** ${trade_data['strike_price']}")
            st.write(f"**Current Price:** ${trade_data['current_price']}")

        with col2:
            st.subheader("🤖 AI Analysis")
            st.metric("LLM Confidence", ".1%", delta=f"{trade_data['llm_confidence']:.0%}")
            st.metric("Quantitative Score", ".1f")
            st.metric("Composite Score", ".1f")

            # Confidence gauge
            confidence_pct = int(trade_data['llm_confidence'] * 100)
            st.progress(confidence_pct/100)
            st.caption(f"Confidence Level: {confidence_pct}%")

        with col3:
            st.subheader("💡 Recommendation")
            decision_color = {
                'BUY': '🟢',
                'HOLD': '🟡',
                'AVOID': '🔴'
            }
            st.markdown(f"### {decision_color[trade_data['decision']]} {trade_data['decision']}")
            st.write(f"**Market Regime:** {trade_data['market_regime']}")
            st.write(f"**Volatility:** {trade_data['volatility_environment']}")

        # Decision reasoning (mock)
        st.subheader("🧠 Decision Reasoning")
        with st.expander("View LLM Analysis"):
            st.write("""
            **Primary Catalyst:** Strong earnings momentum with positive analyst sentiment.

            **Market Context:** Current bull market phase with technology sector leadership.

            **Risk Assessment:** Moderate risk level with favorable volatility positioning.

            **Quantitative Factors:**
            - Greeks profile: Favorable delta positioning
            - Volatility: Within optimal percentile range
            - Technical: Positive trend strength

            **Recommendation Confidence:** High conviction based on multi-factor analysis.
            """)

        # Human override interface
        st.subheader("👤 Human Override")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("✅ APPROVE TRADE", type="primary", use_container_width=True):
                st.success(f"Trade {trade_id} approved and executed!")

        with col2:
            if st.button("🔄 REQUEST REVIEW", use_container_width=True):
                st.info(f"Trade {trade_id} flagged for additional review")

        with col3:
            if st.button("❌ REJECT TRADE", type="secondary", use_container_width=True):
                st.error(f"Trade {trade_id} rejected")

        # Override rationale
        with st.expander("Add Override Rationale"):
            rationale = st.text_area("Reason for override decision", height=100,
                                   placeholder="Explain your reasoning for overriding the AI recommendation...")
            if st.button("Submit Override"):
                st.success("Override rationale recorded in audit log")

def show_performance_analytics():
    """Display performance analytics and trends"""
    st.header("📈 Performance Analytics")

    perf_data = get_performance_metrics()

    # Performance overview
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_return = perf_data['daily_return'].sum()
        st.metric("30-Day Return", ".1%", delta=f"{total_return:.1%}")

    with col2:
        avg_win_rate = perf_data['win_rate'].mean()
        st.metric("Avg Win Rate", ".1%")

    with col3:
        avg_sharpe = perf_data['sharpe_ratio'].mean()
        st.metric("Avg Sharpe Ratio", ".2f")

    with col4:
        total_trades = perf_data['total_trades'].sum()
        st.metric("Total Trades", total_trades)

    # Performance chart
    st.subheader("Daily Performance")
    fig = px.line(perf_data, x='date', y='daily_return',
                 title='Daily Returns (30-Day History)')
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

    # Win rate trend
    col1, col2 = st.columns(2)

    with col1:
        fig_winrate = px.area(perf_data, x='date', y='win_rate',
                             title='Win Rate Trend')
        fig_winrate.update_layout(height=250)
        st.plotly_chart(fig_winrate, use_container_width=True)

    with col2:
        # Sharpe ratio distribution
        fig_sharpe = px.histogram(perf_data, x='sharpe_ratio',
                                title='Sharpe Ratio Distribution')
        fig_sharpe.update_layout(height=250)
        st.plotly_chart(fig_sharpe, use_container_width=True)

    # Recent trades table
    st.subheader("Recent Trade Performance")
    recent_trades = [
        {'date': '2024-01-06', 'symbol': 'AAPL', 'pnl': 245.50, 'outcome': 'Profit'},
        {'date': '2024-01-06', 'symbol': 'MSFT', 'pnl': -120.25, 'outcome': 'Loss'},
        {'date': '2024-01-05', 'symbol': 'GOOGL', 'pnl': 380.75, 'outcome': 'Profit'},
        {'date': '2024-01-05', 'symbol': 'AMZN', 'pnl': 95.20, 'outcome': 'Profit'},
        {'date': '2024-01-04', 'symbol': 'TSLA', 'pnl': -55.80, 'outcome': 'Loss'}
    ]

    trades_df = pd.DataFrame(recent_trades)
    st.dataframe(trades_df, use_container_width=True)

def show_system_health():
    """Display system health and monitoring dashboard"""
    st.header("🔧 System Health & Monitoring")

    health = get_system_health_data()

    # Overall status
    if health['api_status'] == 'healthy' and health['active_alerts'] == 0:
        st.success("✅ All Systems Operational")
    elif health['active_alerts'] > 0:
        st.warning(f"⚠️ {health['active_alerts']} Active Alert(s)")
    else:
        st.error("❌ System Issues Detected")

    # Health metrics grid
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("API Status", health['api_status'].upper())
        st.metric("LLM Status", health['llm_status'].upper())

    with col2:
        st.metric("Database", health['database_status'].upper())
        st.metric("Active Alerts", health['active_alerts'])

    with col3:
        st.metric("Success Rate (24h)", ".1%")
        st.metric("Avg Latency", f"{health['avg_latency_ms']}ms")

    with col4:
        st.metric("Requests Today", health['total_requests_today'])
        st.metric("Cost Today", ".2f")

    # Active alerts
    if health['active_alerts'] > 0:
        st.subheader("🚨 Active Alerts")
        alerts = [
            {"type": "High Latency", "message": "Average response time above threshold", "severity": "warning"},
        ]

        for alert in alerts:
            if alert['severity'] == 'warning':
                st.warning(f"**{alert['type']}:** {alert['message']}")
            else:
                st.error(f"**{alert['type']}:** {alert['message']}")

    # API usage chart (mock data)
    st.subheader("API Usage Over Time")
    hours = pd.date_range(start=datetime.now() - timedelta(hours=24), end=datetime.now(), freq='H')
    usage_data = pd.DataFrame({
        'hour': hours,
        'requests': np.random.poisson(10, len(hours)),
        'latency': np.random.normal(1200, 200, len(hours))
    })

    fig = px.line(usage_data, x='hour', y=['requests', 'latency'],
                 title='API Usage & Latency (24h)')
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

    # System logs
    st.subheader("Recent System Logs")
    logs = [
        {"timestamp": "14:32:15", "level": "INFO", "message": "Trade TRADE_001 approved"},
        {"timestamp": "14:31:42", "level": "WARNING", "message": "High latency detected: 2500ms"},
        {"timestamp": "14:30:18", "level": "INFO", "message": "LLM calibration completed"},
        {"timestamp": "14:28:55", "level": "INFO", "message": "Database backup completed"},
        {"timestamp": "14:25:12", "level": "ERROR", "message": "Temporary API rate limit exceeded"}
    ]

    logs_df = pd.DataFrame(logs)
    st.dataframe(logs_df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()