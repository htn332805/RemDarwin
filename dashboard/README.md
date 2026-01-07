# RemDarwin LLM Trading Dashboard

A comprehensive human-in-the-loop interface for monitoring and managing LLM-enhanced trading decisions.

## Features

### 🤖 Trade Queue Management
- **Real-time Trade Queue**: View pending trades with LLM recommendations
- **Confidence Scoring**: Color-coded confidence levels (high/medium/low)
- **Bulk Actions**: Approve/reject multiple trades at once
- **Filtering**: Filter by confidence thresholds and risk levels

### 🎯 Decision Review & Override
- **Detailed Trade Analysis**: Comprehensive view of trade parameters and AI reasoning
- **Human Override**: Manual approval/rejection with rationale logging
- **LLM Reasoning Display**: View AI decision-making process
- **Audit Trail**: Complete logging of human-AI interactions

### 📈 Performance Analytics
- **Historical Performance**: 30-day performance tracking
- **Risk Metrics**: Sharpe ratio, win rate, return distributions
- **Trade History**: Recent trade outcomes and P&L
- **Interactive Charts**: Plotly-powered performance visualizations

### 🔧 System Health Monitoring
- **API Status**: Real-time health of all system components
- **Performance Metrics**: Latency, success rates, cost tracking
- **Alert Management**: Active alerts and system notifications
- **Usage Analytics**: API usage patterns and trends

## Installation

```bash
# Install dependencies
pip install streamlit plotly pandas numpy

# Run the dashboard
cd dashboard
streamlit run app.py
```

## Usage

### Starting the Dashboard
```bash
streamlit run dashboard/app.py
```

The dashboard will open in your default web browser at `http://localhost:8501`.

### Key Workflows

#### 1. Daily Trade Review
1. Check the **Trade Queue** tab for pending recommendations
2. Review high-confidence trades (green highlighting)
3. Use bulk actions for efficient processing
4. Review borderline cases individually in the **Decision Review** tab

#### 2. Human Override Process
1. Select a trade from the dropdown in **Decision Review**
2. Review AI reasoning and confidence metrics
3. Choose to approve, request additional review, or reject
4. Provide rationale for override decisions

#### 3. Performance Monitoring
1. Review daily performance metrics in the **Performance** tab
2. Monitor system health in the **System Health** tab
3. Check for alerts and take corrective actions

## Configuration

### Environment Variables
```bash
# Database connection
DATABASE_URL=sqlite:///data/historical_trades.db

# API endpoints (for production integration)
LLM_API_ENDPOINT=https://api.perplexity.ai
MONITORING_ENDPOINT=http://localhost:9090

# Authentication (future feature)
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=secure_password
```

### Customization Options

#### Risk Thresholds
Adjust confidence thresholds in the sidebar:
- **High Confidence**: >80% (automatic approval candidates)
- **Medium Confidence**: 40-80% (review recommended)
- **Low Confidence**: <40% (requires careful review)

#### Auto-Refresh Settings
- Enable/disable automatic dashboard refresh
- Configure refresh intervals (10-300 seconds)
- Manual refresh button available

## Architecture

### Components
- **Streamlit Frontend**: Interactive web interface
- **Data Layer**: SQLite database for trade history
- **API Integration**: Connection to LLM and quantitative engines
- **Monitoring**: Real-time system health tracking

### Data Flow
1. **Trade Generation**: New trades enter the queue with AI analysis
2. **Human Review**: Traders review and override AI recommendations
3. **Execution**: Approved trades are executed
4. **Performance Tracking**: Results feed back into analytics

## Security Considerations

### Future Enhancements
- **User Authentication**: Login system for multiple users
- **Role-Based Access**: Different permission levels
- **Audit Logging**: Comprehensive action tracking
- **Data Encryption**: Secure storage of sensitive information

### Current Limitations
- Single-user interface (no authentication yet)
- Mock data for demonstration
- No real-time trade execution integration

## Troubleshooting

### Common Issues

#### Dashboard Not Loading
- Ensure all dependencies are installed
- Check that port 8501 is available
- Verify Python version compatibility

#### Data Not Updating
- Check database connectivity
- Verify API endpoints are accessible
- Review system health indicators

#### Performance Issues
- Reduce auto-refresh interval
- Limit data range in queries
- Check system resource usage

## Development

### Adding New Features
1. Create new functions in `app.py`
2. Add corresponding tabs or sections
3. Update mock data functions for testing
4. Add proper error handling

### Testing
```bash
# Run with mock data
streamlit run app.py --server.headless true

# Check for import errors
python -c "import app; print('Import successful')"
```

## Contributing

### Code Standards
- Use clear, descriptive variable names
- Add docstrings to all functions
- Include error handling for user inputs
- Follow Streamlit best practices for UI design

### Feature Requests
- New dashboard components
- Additional analytics views
- Enhanced filtering options
- Mobile responsiveness improvements