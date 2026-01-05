# Selling Options Plan: Systematic Approach to Covered Calls and Cash-Secured Puts

## Overview

This plan outlines a comprehensive, automated system for generating passive income through selling options (covered calls and cash-secured puts), mimicking institutional approaches like JP Morgan's quantitative trading strategies. The system combines rule-based quantitative analysis with LLM-powered interpretive capabilities to identify low-risk, high-probability trades while maintaining institutional-grade risk management.

The approach focuses on:
- **Covered Calls**: Selling call options against owned stock positions
- **Cash-Secured Puts**: Selling put options with sufficient cash backing
- **Automation**: Fully automated trade identification and monitoring
- **Risk Management**: Institutional-level position sizing and risk controls
- **Performance Tracking**: Comprehensive backtesting and live performance metrics

## Overall Architecture

### Core Components
1. **Data Layer**: Extended FMP API integration for options data, market data, and fundamental analysis
2. **Analysis Engine**: Multi-layered quantitative scoring system with rule-based filters
3. **LLM Interpretation Layer**: AI-driven risk assessment and trade rationale generation
4. **Decision Framework**: Automated trade selection with institutional risk parameters
5. **Execution Interface**: Integration with brokerage APIs for order placement
6. **Monitoring System**: Real-time position tracking and automated alerts

### Technology Stack
- **Language**: Python with async capabilities for real-time data
- **Data Storage**: SQLite/PostgreSQL for options chains and trade history
- **LLM Integration**: OpenAI/Claude API for interpretive analysis
- **Brokerage APIs**: Alpaca/Interactive Brokers for execution
- **Monitoring**: Grafana/Prometheus for dashboard and alerts

## Atomic Subtasks with Checklists

### Subtask 1: Data Collection Framework
**Objective**: Extend current FMP fetcher to include comprehensive options chain data and real-time market feeds.

**Checklist**:
- [ ] Implement option chain fetcher for calls and puts
- [ ] Add Greek calculations (delta, gamma, theta, vega, rho)
- [ ] Integrate implied volatility surfaces
- [ ] Fetch open interest and volume data
- [x] Include bid/ask spreads and liquidity metrics
- [ ] Add real-time quote updates (every 5 minutes)
- [ ] Implement data validation and gap-filling logic
- [ ] Create options database schema with indexing

**Success Criteria**:
- Data completeness: >95% of active options covered
- Latency: <10 seconds for option chain refresh
- Accuracy: All calculated Greeks within 1% of industry standards

### Subtask 2: Quantitative Screening Engine
**Objective**: Develop rule-based filters to identify high-probability trades with defined risk parameters.

**Covered Call Filters**:
- [ ] Underlying stock ownership verification
- [ ] Minimum liquidity: Open interest > 100 contracts
- [ ] Premium yield: >2% annualized
- [ ] Delta range: 0.15-0.35 (moderate moneyness)
- [ ] Implied volatility percentile: 20th-60th (not overpriced)
- [ ] Time to expiration: 30-90 days
- [ ] Maximum loss potential: <5% of position value

**Cash-Secured Put Filters**:
### Cash Availability: 100% of Notional Value Secured

#### Context within Cash-Secured Put Filters and Quantitative Screening Engine

The cash availability filter represents a critical risk management component within the quantitative screening engine for cash-secured puts. Positioned as the foundational requirement in the **Cash-Secured Put Filters** checklist (Subtask 2), this filter ensures that all put-selling strategies maintain full collateral coverage. The screening engine integrates this verification into its multi-layered quantitative assessment, requiring 100% cash backing before any cash-secured put position can be considered for execution. This filter operates in conjunction with other quantitative metrics such as premium yield, delta range, put-call ratio, and earnings proximity, forming a comprehensive gatekeeping mechanism that eliminates uncollateralized risk exposure.

The filter's placement at the beginning of the cash-secured put screening process ensures that position sizing calculations are grounded in actual cash availability rather than theoretical limits. The engine cross-references portfolio cash positions against proposed trade notional values (strike price × 100 shares per contract), automatically adjusting position sizes downward if cash constraints exist. This integration enables systematic scaling across different market conditions while maintaining the core principle that every cash-secured put represents a synthetic covered call with full downside protection.

#### Explanation of 100% Cash Securing Requirement and Implications

The 100% cash securing requirement mandates that investors maintain cash reserves equal to the full notional value of sold put options, calculated as strike price × 100 shares per contract. This requirement stems from regulatory frameworks (FINRA Rule 4210 for cash-secured puts) and risk management principles that eliminate margin borrowing and forced liquidation risks. Unlike naked puts that require margin maintenance, cash-secured puts convert potential losses into guaranteed cash outflows, providing institutional-grade risk isolation.

**Key Implications:**

1. **Risk Mitigation**: Eliminates margin call risk during severe market declines, as the cash collateral fully covers exercise obligations without requiring position liquidation.

2. **Regulatory Compliance**: Ensures adherence to SEC and FINRA requirements for cash-secured put strategies, preventing regulatory violations that could result in trading restrictions or penalties.

3. **Position Sizing Constraints**: Limits portfolio exposure to available cash reserves, naturally constraining leverage and promoting conservative position sizing relative to total portfolio value.

4. **Liquidity Management**: Requires careful cash flow planning, as tied-up cash cannot be deployed in other investments, impacting overall portfolio yield optimization.

5. **Tax Efficiency**: Provides favorable tax treatment compared to margin-based strategies, with losses treated as capital losses rather than interest expenses.

6. **Counterparty Risk Reduction**: Minimizes broker default risk, as positions are fully collateralized with cash rather than relying on broker margin guarantees.

The requirement creates a natural feedback loop where market volatility inversely correlates with available position sizing capacity, forcing more conservative allocations during stress periods and enabling larger positions during stable conditions.

#### Detailed Example: Impact of Catalysts and Scenarios on Cash Availability and Position Sizing

This section demonstrates how the 100% cash securing requirement interacts with various market catalysts and scenarios extracted from the comprehensive options selling framework. Each scenario illustrates how external catalysts affect cash availability calculations and subsequent position sizing adjustments for cash-secured puts, showing the dynamic interplay between market conditions, liquidity constraints, and risk management protocols.

##### Scenario 1: Normal Market Conditions - Steady Cash Deployment

**Catalyst Context**: In stable market environments with moderate volatility (catalysts: economic stability, balanced monetary policy, steady growth), liquidity conditions support standard position sizing with predictable cash flow patterns.

**Cash Availability Impact**: Normal market conditions typically show optimal liquidity with bid-ask spreads under 3% and volume scores above 0.7. Cash availability remains at full portfolio capacity, with minimal frictional costs from transaction spreads.

**Position Sizing Calculation**:
```python
# Normal market cash-secured put sizing
portfolio_cash = 1000000  # $1M available cash
put_strike = 150  # $150 strike
contracts_per_trade = 10  # Standard position

notional_value = put_strike * 100 * contracts_per_trade  # $150,000
cash_required = notional_value * 1.0  # 100% securing

if cash_required <= portfolio_cash:
    max_contracts = int(portfolio_cash / (put_strike * 100))
    position_size = min(contracts_per_trade, max_contracts)
    # Result: Full position size (10 contracts) approved
```

**Implications**: Enables standard position sizing (5% of portfolio per trade) with full cash utilization. Premium yields of 3%+ annualized remain attractive without liquidity discounts.

##### Scenario 2: High Volatility Events - Conservative Cash Allocation

**Catalyst Context**: During periods of elevated uncertainty (catalysts: geopolitical tensions, economic data surprises, central bank shocks, systemic risk events), volatility spikes create liquidity stress with spreads widening to 5-15%.

**Cash Availability Impact**: Crisis conditions reduce effective cash availability through increased frictional costs (3-10% of premium) and conservative liquidity adjustments. The screening engine applies a volatility multiplier (1.2-2.0x) to cash requirements, effectively reducing available position capacity.

**Position Sizing Calculation**:
```python
# High volatility cash adjustment
volatility_event = True
volatility_multiplier = 2.0  # 2x cash requirement during crisis
liquidity_decay = 0.7  # 30% liquidity reduction

effective_cash_available = portfolio_cash * liquidity_decay
adjusted_cash_required = cash_required * volatility_multiplier

max_contracts = int(effective_cash_available / (put_strike * 100 * volatility_multiplier))
position_size = min(contracts_per_trade, max_contracts) * 0.25  # 25% normal size
# Result: Position size reduced to 2-3 contracts
```

**Implications**: Automatic position size reduction to 25% of normal levels, prioritizing capital preservation over yield generation. Cash remains fully secured but deployment velocity decreases significantly.

##### Scenario 3: Earnings Season - Targeted Cash Reservation

**Catalyst Context**: Pre-earnings periods (catalysts: analyst expectations, institutional positioning, conference call uncertainty) show concentrated volatility with liquidity decay factors of 0.5-0.7 closer to earnings dates.

**Cash Availability Impact**: Earnings season creates binary risk profiles requiring enhanced cash reserves. The screening engine implements earnings-specific adjustments with 50% normal position sizes and extended cash reservation periods.

**Position Sizing Calculation**:
```python
# Earnings season cash management
days_to_earnings = 5
earnings_decay_factor = max(0.5, 1 - (7 - days_to_earnings) / 14)
earnings_volatility_adjustment = 1.3  # 30% premium for earnings risk

earnings_adjusted_cash = portfolio_cash * earnings_decay_factor
earnings_cash_required = cash_required * earnings_volatility_adjustment

if days_to_earnings <= 3:
    position_size = 0  # Avoid positions within 3 days of earnings
else:
    max_contracts = int(earnings_adjusted_cash / (put_strike * 100 * earnings_volatility_adjustment))
    position_size = min(contracts_per_trade * 0.5, max_contracts)  # 50% normal size
    # Result: Position size halved, cash utilization reduced
```

**Implications**: Pre-earnings cash reservation prevents forced exercise during gap moves. Position sizing automatically adjusts based on proximity to earnings dates, with complete avoidance within 3 days of announcements.

##### Scenario 4: Holiday and Low Activity Periods - Extended Cash Holding

**Catalyst Context**: Holiday periods (catalysts: Christmas/New Year effects, summer seasonality, reduced participation) show 40-60% volume reductions with wider spreads and potential gap risk.

**Cash Availability Impact**: Low activity periods extend cash holding requirements due to illiquidity. The screening engine applies holding period adjustments (1.5x normal) and reduces position sizes to 75% of standard levels.

**Position Sizing Calculation**:
```python
# Holiday period cash adjustments
holiday_multipliers = {
    'spread_multiplier': 1.5,
    'volume_multiplier': 0.4,
    'holding_period_adjustment': 1.5
}

holiday_adjusted_cash = portfolio_cash * holiday_multipliers['volume_multiplier']
holiday_cash_required = cash_required * holiday_multipliers['holding_period_adjustment']

max_contracts = int(holiday_adjusted_cash / (put_strike * 100 * holiday_multipliers['holding_period_adjustment']))
position_size = min(contracts_per_trade * 0.75, max_contracts)  # 75% normal size
# Result: Reduced position size, extended cash commitment
```

**Implications**: Conservative sizing prevents holiday gap risk exposure. Cash remains locked longer due to reduced liquidity, impacting overall portfolio cash flow management.

##### Scenario 5: Sector-Specific Liquidity Events - Event-Driven Cash Scaling

**Catalyst Context**: Sector events (catalysts: biotech FDA decisions, tech product launches, energy shocks, financial regulatory announcements) create asymmetric volatility requiring sector-aware cash adjustments.

**Cash Availability Impact**: Sector-specific catalysts apply volatility multipliers (1.2-2.8x) based on event type, with biotech FDA events showing highest adjustment factors due to binary outcomes.

**Position Sizing Calculation**:
```python
# Sector event cash adjustments
sector_adjustments = {
    'biotech_fda': {'volatility_multiplier': 2.8, 'liquidity_decay': 0.6},
    'tech_launch': {'volatility_multiplier': 2.5, 'liquidity_decay': 0.7},
    'energy_shock': {'volatility_multiplier': 2.8, 'liquidity_decay': 0.5},
    'financial_regulatory': {'volatility_multiplier': 2.2, 'liquidity_decay': 0.8}
}

sector_config = sector_adjustments.get('biotech_fda', sector_adjustments['tech_launch'])
sector_adjusted_cash = portfolio_cash * sector_config['liquidity_decay']
sector_cash_required = cash_required * sector_config['volatility_multiplier']

max_contracts = int(sector_adjusted_cash / (put_strike * 100 * sector_config['volatility_multiplier']))
position_size = min(contracts_per_trade, max_contracts) * 0.3  # Conservative sizing
# Result: Significant position reduction for high-volatility sector events
```

**Implications**: Sector-specific cash requirements prevent overexposure to concentrated volatility events. Position sizes automatically scale based on sector risk profiles.

##### Scenario 6: Multi-Asset Portfolio Liquidity Management - Cross-Asset Cash Coordination

**Catalyst Context**: Portfolio-level management (catalysts: rebalancing stress, sector rotation, correlation breakdowns, risk parity adjustments) requires coordinated cash allocation across multiple option positions.

**Cash Availability Impact**: Cross-asset analysis detects correlated liquidity stress, applying portfolio-wide cash adjustments. Correlation coefficients (0.5-0.8) between assets reduce aggregate cash availability.

**Position Sizing Calculation**:
```python
# Portfolio cash coordination
portfolio_symbols = ['AAPL', 'MSFT', 'GOOGL']
correlation_matrix = {
    'AAPL_MSFT': 0.8, 'AAPL_GOOGL': 0.7, 'MSFT_GOOGL': 0.75
}

# Calculate portfolio liquidity stress
portfolio_liquidity_score = calculate_portfolio_liquidity_score(portfolio_symbols)
correlation_stress = max(correlation_matrix.values())

portfolio_adjusted_cash = portfolio_cash * portfolio_liquidity_score
correlated_cash_required = cash_required * (1 + correlation_stress)

# Distribute cash across portfolio
total_portfolio_notional = sum(calculate_symbol_notional(symbol) for symbol in portfolio_symbols)
symbol_allocation_pct = calculate_symbol_notional('TARGET_SYMBOL') / total_portfolio_notional

max_contracts = int((portfolio_adjusted_cash * symbol_allocation_pct) / (put_strike * 100))
position_size = min(contracts_per_trade, max_contracts) * 0.8  # Conservative multi-asset sizing
# Result: Coordinated cash deployment across portfolio positions
```

**Implications**: Portfolio-level cash coordination prevents concentrated risk exposure. Position sizing reflects cross-asset correlations and liquidity dependencies, enabling systematic diversification while maintaining 100% cash securing requirements.

This comprehensive framework demonstrates how the 100% cash securing requirement creates a dynamic, catalyst-aware position sizing mechanism that automatically adapts to changing market conditions while maintaining institutional-grade risk management standards. The integration with quantitative screening ensures that cash availability never becomes a bottleneck for systematic options selling strategies.
- [ ] Premium yield: >3% annualized

[MEMORY BANK: ACTIVE]

#### Context within Cash-Secured Put Filters and Quantitative Screening Engine

The premium yield filter represents a cornerstone metric in the quantitative screening engine for cash-secured puts, positioned as a critical profitability threshold within the **Cash-Secured Put Filters** checklist (Subtask 2). This filter integrates with the broader options selling framework to ensure that only positions offering sufficient annualized premium compensation for the downside risk assumption are considered for execution. The screening engine evaluates premium yield as the ratio of option premium to strike price, annualized based on days to expiration, requiring a minimum of 3% annualized return to qualify for inclusion in the trade candidate pool.

Premium yield serves as a quantitative gatekeeper that balances risk-adjusted returns across different market conditions, ensuring that cash-secured put strategies maintain institutional-grade profitability standards. The filter operates in real-time within the screening engine, cross-referencing premium yields against underlying stock volatility, earnings proximity, and sector-specific catalysts to dynamically adjust position sizing and strike selection.

#### Explanation of Premium Yield >3% Annualized Requirement and Implications

The 3% annualized premium yield requirement establishes a minimum profitability threshold for cash-secured put strategies, calculated as (option_premium / strike_price) × (365 / days_to_expiration). This requirement stems from institutional risk management principles that demand adequate compensation for the opportunity cost of tying up capital that cannot be deployed elsewhere, while providing a buffer against exercise risk during market declines.

**Key Implications:**

1. **Risk-Adjusted Compensation**: Ensures premium capture adequately compensates for the opportunity cost of tying up capital that cannot be deployed elsewhere, while providing a buffer against exercise risk during market declines.

2. **Position Sizing Optimization**: Premium yield requirements directly influence position sizing limits, with higher-yielding opportunities allowing larger allocations within portfolio risk constraints.

3. **Strategy Viability Assessment**: Filters out low-premium opportunities that fail to meet institutional return thresholds, focusing capital on high-probability, well-compensated positions.

4. **Market Regime Adaptation**: Premium yields naturally adjust to volatility environments, with higher yields required in stable markets and lower thresholds acceptable during elevated uncertainty periods.

5. **Performance Consistency**: Maintains minimum return floors across different market cycles, ensuring systematic options selling generates consistent income streams regardless of market direction.

6. **Capital Efficiency**: Optimizes the trade-off between premium capture and capital utilization, ensuring efficient deployment of portfolio cash reserves.

The requirement creates a dynamic profitability threshold that adapts to changing market catalysts while maintaining institutional-grade return expectations for passive income generation.

#### Detailed Example: Impact of Catalysts and Scenarios on Premium Yield and Strategy Selection

This section demonstrates how the 3% annualized premium yield requirement interacts with various market catalysts and scenarios extracted from the comprehensive options selling framework. Each scenario illustrates how external catalysts affect premium yield calculations, strategy selection, and position sizing adjustments for cash-secured puts, showing the dynamic interplay between market conditions, volatility, and profitability thresholds.

##### Scenario 1: Normal Market Conditions - Steady Premium Capture

**Catalyst Context**: In stable market environments with moderate volatility (catalysts: economic stability, balanced monetary policy, steady growth), liquidity conditions support consistent premium yields with predictable return profiles.

**Premium Yield Impact**: Normal market conditions typically show balanced premium yields of 2-4% annualized for OTM cash-secured puts, with optimal yields around 3.5% for 45-90 day expirations. The screening engine accepts positions meeting the 3% minimum threshold with standard position sizing.

**Strategy Selection Calculation**:
```python
# Normal market cash-secured put premium yield analysis
portfolio_cash = 1000000  # $1M available cash
put_strike = 140  # $140 strike for $150 underlying
premium_received = 4.20  # $4.20 premium per contract
days_to_expiration = 60

annualized_yield = (premium_received / put_strike) * (365 / days_to_expiration)
# Result: 3.65% annualized yield (>3% threshold)

if annualized_yield >= 0.03:  # 3% minimum requirement
    max_contracts = int(portfolio_cash / (put_strike * 100))
    position_size = min(10, max_contracts)  # Standard position size
    # Result: Position approved with 10 contracts (5% portfolio allocation)
```

**Implications**: Enables full utilization of position sizing limits with predictable returns. Strategy selection focuses on strikes with 3-4% yields, optimizing the balance between premium capture and risk exposure.

##### Scenario 2: High Volatility Events - Elevated Premium Opportunities

**Catalyst Context**: During periods of elevated uncertainty (catalysts: geopolitical tensions, economic data surprises, central bank shocks, systemic risk events), volatility spikes create higher premium yields as option sellers demand greater compensation for increased risk.

**Premium Yield Impact**: Crisis conditions can elevate premium yields to 8-15% annualized for similar strike structures, though the screening engine maintains conservative position sizing despite attractive yields. Yields above 3% are abundant but require volatility-adjusted risk management.

**Strategy Selection Calculation**:
```python
# High volatility cash-secured put premium yield analysis
volatility_event = True
volatility_risk_multiplier = 1.5  # Higher risk adjustment
crisis_premium = 8.50  # $8.50 premium in crisis
annualized_yield = (crisis_premium / put_strike) * (365 / days_to_expiration)
# Result: 8.95% annualized yield (well above 3% threshold)

if annualized_yield >= 0.03:
    risk_adjusted_size = int(position_size / volatility_risk_multiplier)
    crisis_position_size = min(3, risk_adjusted_size)  # Conservative sizing
    # Result: Position approved but size reduced to 3 contracts (25% normal size)
```

**Implications**: Premium yields exceed thresholds significantly, but position sizing automatically reduces to manage volatility risk. Strategy selection prioritizes slightly OTM strikes with yields of 5-10% to balance premium capture with risk control.

##### Scenario 3: Earnings Season - Premium Yield Compression

**Catalyst Context**: Pre-earnings periods (catalysts: analyst expectations, institutional positioning, conference call uncertainty) show compressed premium yields due to concentrated volatility and hedging activity.

**Premium Yield Impact**: Earnings season often compresses premium yields to 1.5-2.5% annualized as volatility gets priced in, making it challenging to meet the 3% threshold. The screening engine applies stricter filters during earnings periods.

**Strategy Selection Calculation**:
```python
# Earnings season cash-secured put premium yield analysis
days_to_earnings = 5
earnings_volatility_compression = 0.7  # 30% yield compression
earnings_premium = 2.10  # Compressed premium
annualized_yield = (earnings_premium / put_strike) * (365 / days_to_expiration)
adjusted_yield = annualized_yield * earnings_volatility_compression
# Result: 1.85% adjusted annualized yield (<3% threshold)

if adjusted_yield >= 0.03:
    position_size = min(10, max_contracts)
else:
    # Threshold not met - seek alternative strikes or avoid
    alternative_strategy = "covered_call"  # Switch to covered calls
    # Result: Position rejected, strategy switched to covered calls
```

**Implications**: Premium yields often fail to meet thresholds, forcing strategy adaptation. Position sizing becomes more selective, focusing on post-earnings periods or avoiding earnings-proximate expirations.

##### Scenario 4: Holiday and Low Activity Periods - Extended Time Decay

**Catalyst Context**: Holiday periods (catalysts: Christmas/New Year effects, summer seasonality, reduced participation) show extended effective yields due to lower trading activity and longer holding periods.

**Premium Yield Impact**: Holiday periods can provide effective yields of 4-6% annualized when accounting for extended holding periods, as reduced liquidity leads to wider bid-ask spreads and higher premiums relative to normal conditions.

**Strategy Selection Calculation**:
```python
# Holiday period cash-secured put premium yield analysis
holiday_holding_extension = 1.4  # 40% longer effective holding
holiday_premium = 5.60  # Higher premium due to illiquidity
annualized_yield = (holiday_premium / put_strike) * (365 / days_to_expiration)
effective_yield = annualized_yield * holiday_holding_extension
# Result: 4.9% effective annualized yield (>3% threshold)

if effective_yield >= 0.03:
    holiday_position_size = int(position_size * 0.75)  # Conservative sizing
    # Result: Position approved with 7 contracts (reduced for holiday risk)
```

**Implications**: Effective yields meet or exceed thresholds due to extended decay periods. Strategy selection favors slightly longer expirations to maximize time decay benefits while maintaining conservative position sizing.

##### Scenario 5: Sector-Specific Liquidity Events - Catalyst-Driven Yields

**Catalyst Context**: Sector events (catalysts: biotech FDA decisions, tech product launches, energy shocks, financial regulatory announcements) create asymmetric volatility requiring sector-aware premium yield adjustments.

**Premium Yield Impact**: Sector-specific catalysts can create premium yields of 6-12% annualized during event windows, with yields varying significantly by sector risk profile and event timing.

**Strategy Selection Calculation**:
```python
# Sector event cash-secured put premium yield analysis
sector_volatility_premium = {
    'biotech_fda': 2.5,
    'tech_launch': 2.0,
    'energy_shock': 2.2,
    'financial_regulatory': 1.8
}
sector_config = sector_volatility_premium.get('biotech_fda', 2.0)
sector_premium = 9.80  # Elevated sector premium
annualized_yield = (sector_premium / put_strike) * (365 / days_to_expiration)
# Result: 8.7% annualized yield (>3% threshold)

if annualized_yield >= 0.03:
    sector_risk_adjustment = 0.4  # 40% position reduction for sector events
    sector_position_size = int(position_size * sector_risk_adjustment)
    # Result: Position approved with 4 contracts (40% normal size)
```

**Implications**: Premium yields significantly exceed thresholds during sector events. Strategy selection requires careful position sizing adjustments based on event type and sector volatility characteristics.

##### Scenario 6: Multi-Asset Portfolio Liquidity Management - Cross-Asset Yield Optimization

**Catalyst Context**: Portfolio-level management (catalysts: rebalancing stress, sector rotation, correlation breakdowns, risk parity adjustments) requires coordinated premium yield optimization across multiple option positions.

**Premium Yield Impact**: Portfolio management balances premium yields across correlated assets, with yields of 3-5% annualized optimized for overall portfolio risk exposure rather than individual position yields.

**Strategy Selection Calculation**:
```python
# Portfolio cash-secured put premium yield optimization
portfolio_symbols = ['AAPL', 'MSFT', 'GOOGL']
portfolio_correlation = 0.75
portfolio_yields = {
    'AAPL': 0.035,  # 3.5%
    'MSFT': 0.032,  # 3.2%
    'GOOGL': 0.038  # 3.8%
}
portfolio_avg_yield = sum(portfolio_yields.values()) / len(portfolio_yields)
correlation_adjustment = 1 - (portfolio_correlation * 0.3)
adjusted_portfolio_yield = portfolio_avg_yield * correlation_adjustment
# Result: 3.45% adjusted portfolio yield (>3% threshold)

if adjusted_portfolio_yield >= 0.03:
    # Distribute position sizes based on yield contribution
    total_allocation = 0.04  # 4% portfolio allocation for options
    yield_weighted_allocation = {
        symbol: (yield_pct / sum(portfolio_yields.values())) * total_allocation
        for symbol, yield_pct in portfolio_yields.items()
    }
    # Result: Positions approved with yield-weighted allocations
```

**Implications**: Premium yields are optimized at portfolio level rather than individual positions. Strategy selection coordinates across assets to maximize total portfolio yield while managing correlation risk.

#### Conclusion Framework

This comprehensive premium yield >3% annualized requirement establishes a robust profitability foundation for systematic cash-secured put strategies, dynamically adapting to all market catalysts while maintaining institutional-grade return standards. The framework ensures that passive income generation remains both consistent and risk-appropriate across varying market conditions, with automatic adjustments for volatility, liquidity, and sector-specific factors. Implementation within the quantitative screening engine provides real-time yield validation, enabling systematic capital deployment that balances premium capture with risk management imperatives. The requirement serves as both a minimum profitability threshold and a catalyst for strategy adaptation, ensuring options selling strategies maintain viability across all market scenarios while optimizing capital efficiency and return potential.

- [x] Delta range: -0.15 to -0.35

#### Context within Cash-Secured Put Filters and Quantitative Screening Engine

The delta range filter represents a critical moneyness criterion in the quantitative screening engine for cash-secured puts, positioned as a key risk management parameter within the **Cash-Secured Put Filters** checklist (Subtask 2). This filter integrates delta-based moneyness assessment into the broader options selling framework to ensure that only positions with appropriate risk-reward profiles are considered for execution. The screening engine evaluates delta ranges to balance premium capture potential against exercise risk, requiring cash-secured put candidates to fall within the -0.15 to -0.35 delta range for optimal systematic strategy implementation.

Delta range serves as a quantitative moneyness gatekeeper that adapts to changing volatility environments, ensuring cash-secured put strategies maintain institutional-grade risk control while optimizing premium collection. The filter operates in real-time within the screening engine, cross-referencing delta levels against underlying stock movement patterns, earnings proximity, and sector-specific volatility catalysts to dynamically adjust strike selection and position sizing.

#### Explanation of Delta Range -0.15 to -0.35 Requirement and Implications

The -0.15 to -0.35 delta range requirement establishes a moderate out-of-the-money (OTM) strike selection criterion for cash-secured put strategies, calculated as the sensitivity of option price to $1 changes in the underlying asset. This range corresponds to strike prices approximately 5-15% below current underlying prices, providing a balance between premium income potential and downside protection requirements.

**Key Implications:**

1. **Risk-Reward Optimization**: Balances premium capture (higher yields than deep OTM puts) with exercise protection (lower probability than ATM puts), optimizing the risk-adjusted return profile for systematic strategies.

2. **Position Sizing Efficiency**: Enables larger position allocations within portfolio risk limits compared to more conservative deep OTM puts, while maintaining acceptable exercise risk levels.

3. **Volatility Adaptation**: Delta ranges naturally adjust to volatility changes, with higher volatility expanding the range's moneyness distribution and lower volatility contracting it.

4. **Liquidity Considerations**: Strikes in this range typically offer better bid-ask spreads and open interest compared to extreme OTM positions, improving execution quality and slippage control.

5. **Time Decay Acceleration**: Moderate OTM positions benefit from accelerated theta decay as options approach expiration, enhancing the systematic premium harvest strategy.

6. **Portfolio Diversification**: Allows for broader strike distribution across different underlying assets, improving portfolio-level risk diversification while maintaining consistent strategy application.

The requirement creates a dynamic moneyness framework that adapts to all market catalysts while maintaining institutional-grade risk management standards, ensuring systematic cash-secured put strategies achieve optimal capital efficiency and return generation.

#### Detailed Example: Impact of Catalysts and Scenarios on Delta Range and Strategy Selection

This section demonstrates how the -0.15 to -0.35 delta range requirement interacts with various market catalysts and scenarios extracted from the comprehensive options selling framework. Each scenario illustrates how external catalysts affect delta range calculations, moneyness adjustments, and strike selection for cash-secured puts, showing the dynamic interplay between market conditions, volatility regimes, and risk management protocols.

##### Scenario 1: Normal Market Conditions - Balanced Delta Selection

**Catalyst Context**: In stable market environments with moderate volatility (catalysts: economic stability, balanced monetary policy, steady growth), liquidity conditions support standard delta range application with predictable moneyness profiles.

**Delta Range Impact**: Normal market conditions typically show stable delta distributions with strikes in the -0.15 to -0.35 range corresponding to 8-12% OTM puts, with optimal liquidity and execution characteristics.

**Strategy Selection Calculation**:
```python
# Normal market cash-secured put delta range analysis
portfolio_cash = 1000000  # $1M available cash
underlying_price = 150  # $150 stock price
target_delta_range = (-0.35, -0.15)  # Delta range requirement

# Find puts within delta range
eligible_puts = []
for put in option_chain['puts']:
    if target_delta_range[0] <= put.delta <= target_delta_range[1]:
        premium_yield = put.bid / underlying_price
        if premium_yield >= 0.012:  # 1.2% minimum yield
            eligible_puts.append({
                'strike': put.strike_price,
                'delta': put.delta,
                'premium_yield': premium_yield,
                'moneyness_pct': (underlying_price - put.strike_price) / underlying_price,
                'catalyst': 'normal_market_delta'
            })

# Select optimal strike
best_put = max(eligible_puts, key=lambda x: x['premium_yield'])
# Result: Strike selected within -0.15 to -0.35 delta range with optimal yield
```

**Implications**: Enables full utilization of position sizing limits with predictable returns. Strategy selection focuses on strikes with delta -0.25 (approximately 10% OTM), optimizing the balance between premium capture and risk exposure.

##### Scenario 2: High Volatility Events - Conservative Delta Adjustment

**Catalyst Context**: During periods of elevated uncertainty (catalysts: geopolitical tensions, economic data surprises, central bank shocks, systemic risk events), volatility spikes require delta range contraction for risk control.

**Delta Range Impact**: Crisis conditions compress effective delta ranges due to increased option sensitivity, requiring more conservative strike selection within the -0.15 to -0.25 subrange of the standard criteria.

**Strategy Selection Calculation**:
```python
# High volatility cash-secured put delta adjustment
volatility_event = True
volatility_multiplier = 1.5  # 50% more conservative
adjusted_delta_range = (-0.25, -0.15)  # Narrower range for volatility

crisis_puts = []
for put in option_chain['puts']:
    if adjusted_delta_range[0] <= put.delta <= adjusted_delta_range[1]:
        # Apply volatility risk adjustment
        risk_adjusted_premium = put.bid * (1 - volatility_multiplier * 0.1)  # Conservative estimate
        position_limit_pct = 0.25  # 25% normal size
        
        crisis_puts.append({
            'strike': put.strike_price,
            'original_delta': put.delta,
            'adjusted_premium': risk_adjusted_premium,
            'position_limit_pct': position_limit_pct,
            'volatility_adjustment': volatility_multiplier,
            'catalyst': 'high_volatility_delta'
        })

# Select most conservative position
conservative_put = min(crisis_puts, key=lambda x: abs(x['original_delta']))
# Result: Position size reduced, more conservative delta selection
```

**Implications**: Automatic delta range contraction prevents overexposure to volatility risk. Strategy selection prioritizes slightly less OTM strikes, reducing exercise probability while maintaining premium collection.

##### Scenario 3: Earnings Season - Dynamic Delta Management

**Catalyst Context**: Pre-earnings periods (catalysts: analyst expectations, institutional positioning, conference call uncertainty) show delta instability requiring proximity-based adjustments.

**Delta Range Impact**: Earnings season creates delta compression near announcement dates, requiring dynamic range expansion or contraction based on timing relative to earnings.

**Strategy Selection Calculation**:
```python
# Earnings season cash-secured put delta management
days_to_earnings = 5
earnings_delta_adjustment = {
    'compression_factor': max(0.8, 1 - (7 - days_to_earnings) / 14),  # Delta compression closer to earnings
    'range_expansion': 1.2 if days_to_earnings > 3 else 0.9  # Expand range further out
}

adjusted_range = (-0.35 * earnings_delta_adjustment['range_expansion'], 
                 -0.15 * earnings_delta_adjustment['compression_factor'])

earnings_puts = []
for put in option_chain['puts']:
    if adjusted_range[0] <= put.delta <= adjusted_range[1]:
        earnings_risk_premium = put.bid * (1 + 0.1 * (7 - days_to_earnings) / 7)  # Higher premium closer to earnings
        
        earnings_puts.append({
            'strike': put.strike_price,
            'delta': put.delta,
            'earnings_adjusted_premium': earnings_risk_premium,
            'days_to_earnings': days_to_earnings,
            'risk_adjustment': earnings_delta_adjustment,
            'catalyst': 'earnings_season_delta'
        })

# Avoid positions within 3 days of earnings
if days_to_earnings <= 3:
    selected_put = None  # No position
else:
    selected_put = max(earnings_puts, key=lambda x: x['earnings_adjusted_premium'])
# Result: Dynamic delta range adjustment based on earnings proximity
```

**Implications**: Pre-earnings delta management prevents adverse exercise during gap moves. Position sizing automatically adjusts based on proximity to earnings dates, with complete avoidance within critical periods.

##### Scenario 4: Holiday and Low Activity Periods - Extended Delta Stability

**Catalyst Context**: Holiday periods (catalysts: Christmas/New Year effects, summer seasonality, reduced participation) show extended delta stability due to lower trading activity.

**Delta Range Impact**: Low activity periods extend effective delta ranges due to reduced market impact, allowing slightly wider range utilization for better yield optimization.

**Strategy Selection Calculation**:
```python
# Holiday period cash-secured put delta stability
holiday_multipliers = {
    'delta_stability': 1.1,  # 10% more stable deltas
    'range_expansion': 1.15,  # 15% wider range utilization
    'holding_extension': 1.4  # Longer effective holding periods
}

holiday_range = (-0.35 * holiday_multipliers['range_expansion'], 
                -0.15 * holiday_multipliers['delta_stability'])

holiday_puts = []
for put in option_chain['puts']:
    if holiday_range[0] <= put.delta <= holiday_range[1]:
        extended_yield = put.bid / underlying_price * holiday_multipliers['holding_extension']
        
        holiday_puts.append({
            'strike': put.strike_price,
            'delta': put.delta,
            'extended_yield': extended_yield,
            'holding_adjustment': holiday_multipliers['holding_extension'],
            'liquidity_impact': 'reduced_volume',
            'catalyst': 'holiday_delta_stability'
        })

# Select for extended holding benefit
best_holiday_put = max(holiday_puts, key=lambda x: x['extended_yield'])
# Result: Wider delta range utilization for extended time decay benefits
```

**Implications**: Conservative delta range expansion prevents holiday gap risk exposure. Strategy selection favors positions benefiting from extended decay periods, with cash remaining locked longer.

##### Scenario 5: Sector-Specific Volatility Events - Catalyst-Driven Delta Adjustment

**Catalyst Context**: Sector events (catalysts: biotech FDA decisions, tech product launches, energy shocks, financial regulatory announcements) create asymmetric delta behavior requiring sector-aware adjustments.

**Delta Range Impact**: Sector-specific catalysts apply volatility multipliers to delta ranges, with biotech FDA events showing highest adjustment factors due to binary outcomes.

**Strategy Selection Calculation**:
```python
# Sector event cash-secured put delta adjustment
sector_adjustments = {
    'biotech_fda': {'delta_multiplier': 0.8, 'volatility_adjustment': 2.0},
    'tech_launch': {'delta_multiplier': 0.9, 'volatility_adjustment': 1.5},
    'energy_shock': {'delta_multiplier': 0.85, 'volatility_adjustment': 1.8},
    'financial_regulatory': {'delta_multiplier': 0.95, 'volatility_adjustment': 1.3}
}

sector_config = sector_adjustments.get('biotech_fda', sector_adjustments['tech_launch'])
sector_range = (-0.35 * sector_config['delta_multiplier'], 
               -0.15 * sector_config['delta_multiplier'])

sector_puts = []
for put in option_chain['puts']:
    if sector_range[0] <= put.delta <= sector_range[1]:
        sector_premium = put.bid * sector_config['volatility_adjustment']
        sector_risk_adjustment = 0.3  # Conservative sizing
        
        sector_puts.append({
            'strike': put.strike_price,
            'original_delta': put.delta,
            'sector_adjusted_delta_range': sector_range,
            'sector_premium': sector_premium,
            'risk_adjustment': sector_risk_adjustment,
            'catalyst': 'sector_volatility_delta'
        })

# Select most conservative for sector event
sector_put = min(sector_puts, key=lambda x: abs(x['original_delta']))
# Result: Significant position reduction for high-volatility sector events
```

**Implications**: Sector-specific delta requirements prevent overexposure to concentrated volatility events. Position sizing automatically scales based on sector risk profiles.

##### Scenario 6: Multi-Asset Portfolio Delta Coordination - Cross-Asset Range Optimization

**Catalyst Context**: Portfolio-level management (catalysts: rebalancing stress, sector rotation, correlation breakdowns, risk parity adjustments) requires coordinated delta range optimization across multiple assets.

**Delta Range Impact**: Cross-asset analysis detects correlated delta stress, applying portfolio-wide range adjustments. Correlation coefficients between assets reduce aggregate delta range utilization.

**Strategy Selection Calculation**:
```python
# Portfolio cash-secured put delta coordination
portfolio_symbols = ['AAPL', 'MSFT', 'GOOGL']
correlation_matrix = {
    'AAPL_MSFT': 0.8, 'AAPL_GOOGL': 0.7, 'MSFT_GOOGL': 0.75
}

# Calculate portfolio delta stress
portfolio_delta_stress = calculate_portfolio_delta_stress(portfolio_symbols)
correlation_adjustment = 1 - (max(correlation_matrix.values()) * 0.3)

portfolio_adjusted_range = (-0.35 * correlation_adjustment, 
                          -0.15 * correlation_adjustment)

portfolio_puts = []
for symbol in portfolio_symbols:
    symbol_chain = fetcher.fetch_option_chain(symbol)
    for put in symbol_chain['puts']:
        if portfolio_adjusted_range[0] <= put.delta <= portfolio_adjusted_range[1]:
            portfolio_puts.append({
                'symbol': symbol,
                'strike': put.strike_price,
                'delta': put.delta,
                'portfolio_adjustment': correlation_adjustment,
                'catalyst': 'portfolio_delta_coordination'
            })

# Distribute across portfolio
portfolio_allocation = distribute_positions_by_yield(portfolio_puts)
# Result: Coordinated delta range application across portfolio positions
```

**Implications**: Portfolio-level delta coordination prevents concentrated risk exposure. Position sizing reflects cross-asset correlations and delta dependencies, enabling systematic diversification.

#### Conclusion Framework

This comprehensive -0.15 to -0.35 delta range requirement establishes a robust moneyness foundation for systematic cash-secured put strategies, dynamically adapting to all market catalysts while maintaining institutional-grade risk control. The framework ensures that strike selection remains both consistent and risk-appropriate across varying market conditions, with automatic adjustments for volatility, liquidity, and sector-specific factors. Implementation within the quantitative screening engine provides real-time delta validation, enabling systematic capital deployment that balances premium capture with exercise risk management imperatives. The requirement serves as both a moneyness optimization parameter and a catalyst for strategy adaptation, ensuring options selling strategies maintain viability across all market scenarios while optimizing risk-adjusted returns.
- [ ] Put-call ratio: Below sector average

#### Context within Cash-Secured Put Filters and Quantitative Screening Engine

The put-call ratio filter represents a critical sentiment indicator in the quantitative screening engine for cash-secured puts, positioned as a key market sentiment parameter within the **Cash-Secured Put Filters** checklist (Subtask 2). This filter integrates put-call ratio analysis into the broader options selling framework to ensure that positions are established during periods of favorable market sentiment, requiring cash-secured put candidates to have sector put-call ratios below the historical average to qualify for execution. The screening engine evaluates put-call ratios across sector peers to identify environments where put buying pressure is relatively subdued, indicating potentially supportive conditions for systematic put selling strategies.

Put-call ratio serves as a quantitative sentiment gatekeeper that adapts to changing market catalysts, ensuring cash-secured put strategies maintain institutional-grade timing while optimizing entry conditions. The filter operates in real-time within the screening engine, cross-referencing sector put-call ratios against historical averages and volatility catalysts to dynamically adjust strike selection and position sizing.

#### Explanation of Put-Call Ratio Below Sector Average Requirement and Implications

The put-call ratio below sector average requirement establishes a sentiment-based timing criterion for cash-secured put strategies, calculated as the ratio of put option volume to call option volume within a sector, requiring this ratio to be below the sector's historical average. This requirement stems from institutional sentiment analysis principles that identify periods of reduced put buying pressure as favorable environments for put selling strategies, as lower put-call ratios typically indicate less market fear and potentially more supportive underlying conditions.

**Key Implications:**

1. **Sentiment Optimization**: Identifies sectors with relatively bullish sentiment where put buying pressure is below average, potentially indicating better risk-reward dynamics for put sellers.

2. **Position Sizing Enhancement**: Enables larger position allocations during favorable sentiment periods while automatically reducing exposure when sector fear levels rise.

3. **Strategy Timing**: Provides systematic entry signals based on sector sentiment rather than individual stock analysis, improving the consistency of put selling execution.

4. **Risk Mitigation**: Avoids put selling during periods of elevated sector fear, reducing the probability of adverse exercise during market stress events.

5. **Portfolio Diversification**: Facilitates sector rotation strategies by identifying sectors with more favorable put-call dynamics at any given time.

6. **Performance Consistency**: Maintains minimum sentiment thresholds across different market regimes, ensuring systematic put selling generates consistent results.

The requirement creates a dynamic sentiment framework that adapts to all market catalysts while maintaining institutional-grade risk management standards, ensuring systematic cash-secured put strategies achieve optimal timing and capital efficiency.

#### Detailed Example: Impact of Catalysts and Scenarios on Put-Call Ratio and Strategy Selection

This section demonstrates how the put-call ratio below sector average requirement interacts with various market catalysts and scenarios extracted from the comprehensive options selling framework. Each scenario illustrates how external catalysts affect put-call ratio calculations, sentiment analysis, and strike selection for cash-secured puts, showing the dynamic interplay between market conditions, sector sentiment, and risk management protocols.

##### Scenario 1: Normal Market Conditions - Balanced Sector Sentiment

**Catalyst Context**: In stable market environments with moderate volatility (catalysts: economic stability, balanced monetary policy, steady growth), sector sentiment shows balanced put-call ratios near historical averages with predictable patterns.

**Put-Call Ratio Impact**: Normal market conditions typically show sector put-call ratios around 0.6-0.8 (60-80 puts per 100 calls), with ratios below sector average indicating relatively stable sentiment without excessive fear.

**Strategy Selection Calculation**:
```python
# Normal market cash-secured put sentiment analysis
sector_put_call_ratios = {
    'technology': 0.65,  # Current ratio
    'healthcare': 0.72,
    'financials': 0.68
}
sector_historical_averages = {
    'technology': 0.75,  # Historical average
    'healthcare': 0.78,
    'financials': 0.70
}

# Identify sectors with favorable sentiment
favorable_sectors = []
for sector in sector_put_call_ratios:
    current_ratio = sector_put_call_ratios[sector]
    historical_avg = sector_historical_averages[sector]
    if current_ratio < historical_avg:  # Below average = favorable
        sentiment_score = (historical_avg - current_ratio) / historical_avg
        favorable_sectors.append({
            'sector': sector,
            'current_ratio': current_ratio,
            'historical_avg': historical_avg,
            'sentiment_score': sentiment_score,
            'catalyst': 'normal_market_stability'
        })

# Result: Technology and financials qualify for put selling
```

**Implications**: Enables standard position sizing in sectors with balanced but not excessive fear. Strategy selection focuses on sectors with ratios 10-15% below average, optimizing the balance between sentiment and opportunity.

##### Scenario 2: High Volatility Events - Elevated Sector Fear

**Catalyst Context**: During periods of elevated uncertainty (catalysts: geopolitical tensions, economic data surprises, central bank shocks, systemic risk events), sector put-call ratios spike dramatically due to increased put buying.

**Put-Call Ratio Impact**: Crisis conditions can elevate sector put-call ratios to 1.5-2.5 (150-250 puts per 100 calls), making it extremely challenging to find ratios below historical averages as fear dominates all sectors.

**Strategy Selection Calculation**:
```python
# High volatility cash-secured put sentiment analysis
crisis_put_call_ratios = {
    'technology': 2.1,  # Crisis ratio
    'healthcare': 1.8,
    'financials': 2.8
}
historical_averages = {
    'technology': 0.75,
    'healthcare': 0.78,
    'financials': 0.70
}

# Crisis sentiment analysis - likely no favorable sectors
favorable_sectors = []
for sector in crisis_put_call_ratios:
    current_ratio = crisis_put_call_ratios[sector]
    historical_avg = historical_averages[sector]
    if current_ratio < historical_avg:  # Unlikely during crisis
        sentiment_score = (historical_avg - current_ratio) / historical_avg
        favorable_sectors.append({
            'sector': sector,
            'current_ratio': current_ratio,
            'historical_avg': historical_avg,
            'sentiment_score': sentiment_score,
            'catalyst': 'high_volatility_crisis'
        })

# Result: No sectors qualify - put selling suspended or heavily restricted
```

**Implications**: Automatic strategy restriction during crisis periods prevents put selling when sector fear is elevated. Position sizing becomes minimal or zero, prioritizing capital preservation over yield generation.

##### Scenario 3: Earnings Season - Sector-Specific Sentiment Shifts

**Catalyst Context**: Pre-earnings periods (catalysts: analyst expectations, institutional positioning, conference call uncertainty) show concentrated put-call ratio spikes in earnings-impacted sectors.

**Put-Call Ratio Impact**: Earnings season creates sector-specific sentiment distortions, with ratios spiking 2-4x normal levels in earnings-heavy sectors while remaining relatively stable in others.

**Strategy Selection Calculation**:
```python
# Earnings season cash-secured put sentiment analysis
earnings_put_call_ratios = {
    'technology': 1.8,  # Earnings impact
    'healthcare': 0.65,  # Below average - favorable
    'financials': 1.2,
    'consumer': 0.58   # Below average - favorable
}
historical_averages = {
    'technology': 0.75,
    'healthcare': 0.78,
    'financials': 0.70,
    'consumer': 0.80
}

# Sector-specific earnings analysis
favorable_sectors = []
earnings_restricted_sectors = ['technology', 'financials']  # High earnings impact

for sector in earnings_put_call_ratios:
    current_ratio = earnings_put_call_ratios[sector]
    historical_avg = historical_averages[sector]
    
    if sector in earnings_restricted_sectors:
        # Additional restrictions for earnings sectors
        continue
    elif current_ratio < historical_avg:
        sentiment_score = (historical_avg - current_ratio) / historical_avg
        favorable_sectors.append({
            'sector': sector,
            'current_ratio': current_ratio,
            'historical_avg': historical_avg,
            'sentiment_score': sentiment_score,
            'earnings_impact': 'low',
            'catalyst': 'earnings_season_selective'
        })

# Result: Healthcare and consumer sectors qualify despite earnings season
```

**Implications**: Selective sector approach during earnings season avoids high-risk sectors while identifying relatively stable alternatives. Position sizing adjusts based on earnings proximity and sector sentiment stability.

##### Scenario 4: Holiday and Low Activity Periods - Stable Sector Sentiment

**Catalyst Context**: Holiday periods (catalysts: Christmas/New Year effects, summer seasonality, reduced participation) show stable put-call ratios due to lower trading activity.

**Put-Call Ratio Impact**: Low activity periods maintain relatively stable ratios close to or below historical averages, as reduced participation dampens extreme sentiment swings.

**Strategy Selection Calculation**:
```python
# Holiday period cash-secured put sentiment analysis
holiday_put_call_ratios = {
    'technology': 0.62,  # Stable ratio
    'healthcare': 0.68,
    'financials': 0.65
}
historical_averages = {
    'technology': 0.75,
    'healthcare': 0.78,
    'financials': 0.70
}

# Holiday stability analysis
favorable_sectors = []
for sector in holiday_put_call_ratios:
    current_ratio = holiday_put_call_ratios[sector]
    historical_avg = historical_averages[sector]
    if current_ratio < historical_avg:
        sentiment_score = (historical_avg - current_ratio) / historical_avg
        # Holiday adjustment for lower liquidity
        holiday_adjustment = 0.9  # Conservative sizing
        adjusted_sentiment = sentiment_score * holiday_adjustment
        
        favorable_sectors.append({
            'sector': sector,
            'current_ratio': current_ratio,
            'historical_avg': historical_avg,
            'sentiment_score': adjusted_sentiment,
            'liquidity_impact': 'reduced',
            'catalyst': 'holiday_stability'
        })

# Result: All sectors qualify with conservative position sizing
```

**Implications**: Broader sector qualification during holidays due to sentiment stability. Strategy selection favors longer-dated options to compensate for potentially extended holding periods.

##### Scenario 5: Sector-Specific Liquidity Events - Catalyst-Driven Sentiment

**Catalyst Context**: Sector events (catalysts: biotech FDA decisions, tech product launches, energy shocks, financial regulatory announcements) create asymmetric put-call ratio dynamics.

**Put-Call Ratio Impact**: Sector-specific catalysts can create extreme ratio distortions in affected sectors, with ratios spiking 3-5x normal levels during event windows.

**Strategy Selection Calculation**:
```python
# Sector event cash-secured put sentiment analysis
sector_event_ratios = {
    'biotech': 3.2,     # FDA decision impact
    'technology': 0.55, # Below average - favorable
    'energy': 2.1,      # Oil shock impact
    'financials': 0.62  # Below average - favorable
}
historical_averages = {
    'biotech': 0.75,
    'technology': 0.75,
    'energy': 0.80,
    'financials': 0.70
}

# Sector event sentiment analysis
favorable_sectors = []
event_restricted_sectors = ['biotech', 'energy']  # Event impact

for sector in sector_event_ratios:
    current_ratio = sector_event_ratios[sector]
    historical_avg = historical_averages[sector]
    
    if sector in event_restricted_sectors:
        # Avoid event-impacted sectors
        continue
    elif current_ratio < historical_avg:
        sentiment_score = (historical_avg - current_ratio) / historical_avg
        favorable_sectors.append({
            'sector': sector,
            'current_ratio': current_ratio,
            'historical_avg': historical_avg,
            'sentiment_score': sentiment_score,
            'event_impact': 'none',
            'catalyst': 'sector_event_selective'
        })

# Result: Technology and financials qualify, avoiding event-impacted sectors
```

**Implications**: Sector-specific restrictions during events prevent exposure to concentrated volatility. Strategy selection rotates to unaffected sectors with favorable sentiment.

##### Scenario 6: Multi-Asset Portfolio Liquidity Management - Cross-Sector Sentiment Coordination

**Catalyst Context**: Portfolio-level management (catalysts: rebalancing stress, sector rotation, correlation breakdowns, risk parity adjustments) requires coordinated sentiment analysis across multiple sectors.

**Put-Call Ratio Impact**: Portfolio management detects correlated sentiment stress across sectors, applying portfolio-wide sentiment adjustments when multiple sectors show elevated fear levels.

**Strategy Selection Calculation**:
```python
# Portfolio cash-secured put sentiment coordination
portfolio_sector_ratios = {
    'technology': 0.68,
    'healthcare': 0.72,
    'financials': 0.65,
    'consumer': 0.58
}
historical_averages = {
    'technology': 0.75,
    'healthcare': 0.78,
    'financials': 0.70,
    'consumer': 0.80
}

# Portfolio sentiment stress detection
portfolio_sentiment_stress = 0
favorable_sectors = []

for sector in portfolio_sector_ratios:
    current_ratio = portfolio_sector_ratios[sector]
    historical_avg = historical_averages[sector]
    
    if current_ratio > historical_avg:
        stress_contribution = (current_ratio - historical_avg) / historical_avg
        portfolio_sentiment_stress += stress_contribution
    elif current_ratio < historical_avg:
        sentiment_score = (historical_avg - current_ratio) / historical_avg
        favorable_sectors.append({
            'sector': sector,
            'current_ratio': current_ratio,
            'historical_avg': historical_avg,
            'sentiment_score': sentiment_score,
            'portfolio_impact': 'positive',
            'catalyst': 'portfolio_sentiment_coordination'
        })

# Portfolio stress adjustment
stress_threshold = 1.0  # 100% above average stress
if portfolio_sentiment_stress > stress_threshold:
    # Reduce position sizing across all sectors
    for sector in favorable_sectors:
        sector['adjusted_sentiment'] = sector['sentiment_score'] * 0.7  # Conservative adjustment

# Result: Coordinated sentiment analysis with portfolio stress adjustments
```

**Implications**: Portfolio-level sentiment coordination prevents overexposure to correlated fear spikes. Position sizing reflects cross-sector sentiment dependencies, enabling systematic diversification.

#### Conclusion Framework

This comprehensive put-call ratio below sector average requirement establishes a robust sentiment foundation for systematic cash-secured put strategies, dynamically adapting to all market catalysts while maintaining institutional-grade risk control. The framework ensures that sector timing remains both consistent and risk-appropriate across varying market conditions, with automatic adjustments for volatility, liquidity, and sector-specific factors. Implementation within the quantitative screening engine provides real-time sentiment validation, enabling systematic capital deployment that balances market timing with risk management imperatives. The requirement serves as both a sentiment optimization parameter and a catalyst for strategy adaptation, ensuring options selling strategies maintain viability across all market scenarios while optimizing risk-adjusted returns.

- [x] Earnings proximity: >14 days from expiration

#### Context within Cash-Secured Put Filters and Quantitative Screening Engine

The earnings proximity filter represents a critical volatility risk management parameter in the quantitative screening engine for cash-secured puts, positioned as a key timing criterion within the **Cash-Secured Put Filters** checklist (Subtask 2). This filter integrates earnings calendar analysis into the broader options selling framework to ensure that positions are established with sufficient temporal distance from upcoming earnings announcements, requiring cash-secured put candidates to have earnings dates occurring more than 14 days after option expiration to qualify for execution. The screening engine evaluates earnings proximity across the portfolio to dynamically adjust strike selection and position sizing based on earnings-related volatility expectations.

Earnings proximity serves as a quantitative timing gatekeeper that adapts to changing earnings calendars, ensuring cash-secured put strategies maintain institutional-grade risk control while optimizing entry conditions. The filter operates in real-time within the screening engine, cross-referencing earnings dates against option expiration schedules and sector-specific volatility catalysts to dynamically adjust position sizing and strike selection.

#### Explanation of Earnings Proximity >14 Days from Expiration Requirement and Implications

The earnings proximity >14 days from expiration requirement establishes a minimum temporal buffer between option expiration and subsequent earnings announcements, calculated as earnings_date - option_expiration_date > 14 days. This requirement stems from institutional risk management principles that recognize earnings announcements as major catalysts capable of generating 50-200% intraday volatility spikes, requiring adequate time for position management and risk mitigation.

**Key Implications:**

1. **Volatility Risk Mitigation**: Prevents position exposure to earnings-related volatility spikes that can cause 20-50% premium erosion within hours of announcement

2. **Position Sizing Optimization**: Enables larger position allocations when earnings proximity is favorable, while automatically reducing exposure near earnings dates

3. **Strategy Timing**: Provides systematic entry signals based on earnings calendar rather than individual stock analysis, improving the consistency of put selling execution

4. **Risk Management**: Avoids earnings-related gap risk during expiration weeks, reducing the probability of adverse exercise during announcement-driven volatility

5. **Portfolio Diversification**: Facilitates earnings-aware position allocation across different expiration cycles, improving portfolio-level risk diversification

6. **Performance Consistency**: Maintains minimum timing buffers across different earnings seasons, ensuring systematic put selling generates consistent results

The requirement creates a dynamic temporal framework that adapts to changing earnings calendars while maintaining institutional-grade risk management standards, ensuring systematic cash-secured put strategies achieve optimal risk-adjusted returns.

#### Detailed Example: Impact of Catalysts and Scenarios on Earnings Proximity and Strategy Selection

This section demonstrates how the earnings proximity >14 days from expiration requirement interacts with various market catalysts and scenarios extracted from the comprehensive options selling framework. Each scenario illustrates how external catalysts affect earnings proximity calculations, strategy selection, and position sizing adjustments for cash-secured puts, showing the dynamic interplay between market conditions, earnings calendars, and risk management protocols.

##### Scenario 1: Normal Market Conditions - Steady Earnings Calendar Management

**Catalyst Context**: In stable market environments with moderate volatility (catalysts: economic stability, balanced monetary policy, steady growth), earnings calendars follow predictable quarterly patterns with manageable volatility expectations.

**Earnings Proximity Impact**: Normal market conditions typically show balanced earnings proximity with 60-80% of options expirations meeting the >14 day buffer requirement, with optimal position sizing opportunities during non-earnings periods.

**Strategy Selection Calculation**:
```python
# Normal market earnings proximity analysis
portfolio_symbols = ['AAPL', 'MSFT', 'GOOGL']
earnings_calendar = {
    'AAPL': '2026-04-15',   # April earnings
    'MSFT': '2026-04-22',   # April earnings
    'GOOGL': '2026-04-25'   # April earnings
}

# Find expirations with >14 day earnings buffer
eligible_expirations = []
for symbol in portfolio_symbols:
    earnings_date = datetime.fromisoformat(earnings_calendar[symbol])
    
    # Check various expiration dates against earnings
    potential_expirations = [datetime(2026, 4, 5), datetime(2026, 4, 12), datetime(2026, 4, 19)]
    
    for exp_date in potential_expirations:
        days_to_earnings = (earnings_date - exp_date).days
        if days_to_earnings > 14:
            eligible_expirations.append({
                'symbol': symbol,
                'expiration': exp_date,
                'earnings_date': earnings_date,
                'days_buffer': days_to_earnings,
                'risk_rating': 'low',
                'position_size_multiplier': 1.0,  # Normal sizing
                'catalyst': 'normal_market_earnings'
            })

# Result: Multiple expiration dates qualify for each symbol
```

**Implications**: Enables full utilization of position sizing limits with predictable earnings-related risk. Strategy selection focuses on expirations providing 15-30 day buffers, optimizing the balance between earnings proximity and time decay potential.

##### Scenario 2: High Volatility Events - Conservative Earnings Proximity Management

**Catalyst Context**: During periods of elevated uncertainty (catalysts: geopolitical tensions, economic data surprises, central bank shocks, systemic risk events), earnings proximity requirements become more stringent due to amplified earnings-related volatility.

**Earnings Proximity Impact**: Crisis conditions reduce eligible expirations to 30-50% of normal levels, with automatic position size reductions for any positions near earnings dates, even with >14 day buffers.

**Strategy Selection Calculation**:
```python
# High volatility earnings proximity adjustment
volatility_event = True
volatility_multiplier = 1.5  # Stricter buffer requirement

crisis_earnings_proximity = {}
for symbol in portfolio_symbols:
    earnings_date = datetime.fromisoformat(earnings_calendar[symbol])
    
    # Apply volatility-adjusted buffer
    required_buffer = 14 * volatility_multiplier  # 21+ days required
    
    eligible_crisis_expirations = []
    for exp_date in potential_expirations:
        days_to_earnings = (earnings_date - exp_date).days
        if days_to_earnings > required_buffer:
            position_size_adjustment = min(1.0, days_to_earnings / (required_buffer * 1.5))
            eligible_crisis_expirations.append({
                'symbol': symbol,
                'expiration': exp_date,
                'earnings_date': earnings_date,
                'adjusted_buffer': days_to_earnings,
                'required_buffer': required_buffer,
                'position_size_multiplier': position_size_adjustment,
                'volatility_adjustment': volatility_multiplier,
                'catalyst': 'high_volatility_earnings'
            })
    
    crisis_earnings_proximity[symbol] = eligible_crisis_expirations

# Result: Reduced eligible expirations, smaller position sizes
```

**Implications**: Automatic earnings proximity tightening prevents amplified volatility exposure. Strategy selection prioritizes longest available buffers, with position sizing automatically reduced based on proximity to earnings dates.

##### Scenario 3: Earnings Season - Dynamic Proximity Management

**Catalyst Context**: Pre-earnings periods (catalysts: analyst expectations, institutional positioning, conference call uncertainty) show concentrated earnings proximity challenges with multiple companies reporting in short timeframes.

**Earnings Proximity Impact**: Earnings season creates proximity compression with only 20-40% of potential expirations meeting requirements, forcing strategy adaptation to longer-dated options or reduced position sizing.

**Strategy Selection Calculation**:
```python
# Earnings season proximity analysis
earnings_season_multiplier = 2.0  # Double buffer requirement
season_earnings_density = 0.8     # High density of earnings reports

earnings_season_proximity = {}
for symbol in portfolio_symbols:
    earnings_date = datetime.fromisoformat(earnings_calendar[symbol])
    
    # Earnings season adjustments
    adjusted_buffer = 14 * earnings_season_multiplier * season_earnings_density
    
    season_eligible = []
    for exp_date in potential_expirations:
        days_to_earnings = (earnings_date - exp_date).days
        
        if days_to_earnings > adjusted_buffer:
            # Additional density adjustment for clustered earnings
            density_penalty = 1 - (season_earnings_density * 0.3)
            position_size = min(1.0, density_penalty)
            
            season_eligible.append({
                'symbol': symbol,
                'expiration': exp_date,
                'earnings_date': earnings_date,
                'season_adjusted_buffer': adjusted_buffer,
                'density_penalty': density_penalty,
                'position_size_multiplier': position_size,
                'earnings_density': season_earnings_density,
                'catalyst': 'earnings_season_proximity'
            })
    
    earnings_season_proximity[symbol] = season_eligible

# Result: Severely restricted eligible expirations during earnings season
```

**Implications**: Pre-earnings proximity management prevents crowded trade execution during high-volatility periods. Strategy selection automatically shifts to longer expirations or alternative strategies when proximity requirements cannot be met.

##### Scenario 4: Holiday and Low Activity Periods - Extended Proximity Buffers

**Catalyst Context**: Holiday periods (catalysts: Christmas/New Year effects, summer seasonality, reduced participation) show extended effective proximity due to lower liquidity and potential gap risk around earnings.

**Earnings Proximity Impact**: Low activity periods extend effective proximity requirements to 18-25 days due to reduced market participation and potential holiday-related gap risk, though actual earnings calendars remain unchanged.

**Strategy Selection Calculation**:
```python
# Holiday period proximity adjustments
holiday_multipliers = {
    'spread_multiplier': 1.5,
    'volume_multiplier': 0.4,
    'proximity_buffer_extension': 1.4  # 40% longer buffer
}

holiday_proximity = {}
for symbol in portfolio_symbols:
    earnings_date = datetime.fromisoformat(earnings_calendar[symbol])
    
    # Holiday-adjusted proximity requirements
    holiday_buffer = 14 * holiday_multipliers['proximity_buffer_extension']
    
    holiday_eligible = []
    for exp_date in potential_expirations:
        days_to_earnings = (earnings_date - exp_date).days
        
        if days_to_earnings > holiday_buffer:
            # Holiday liquidity adjustment
            liquidity_adjustment = holiday_multipliers['volume_multiplier']
            position_size = min(1.0, liquidity_adjustment * 1.2)  # Slight boost for longer buffers
            
            holiday_eligible.append({
                'symbol': symbol,
                'expiration': exp_date,
                'earnings_date': earnings_date,
                'holiday_buffer': holiday_buffer,
                'liquidity_adjustment': liquidity_adjustment,
                'position_size_multiplier': position_size,
                'holiday_impact': 'extended_buffer_required',
                'catalyst': 'holiday_earnings_proximity'
            })
    
    holiday_proximity[symbol] = holiday_eligible

# Result: Extended proximity requirements but maintained eligibility
```

**Implications**: Conservative proximity management prevents holiday gap risk exposure. Strategy selection favors positions with extended buffers, with liquidity adjustments applied to account for reduced trading activity.

##### Scenario 5: Sector-Specific Liquidity Events - Catalyst-Driven Proximity Adjustments

**Catalyst Context**: Sector events (catalysts: biotech FDA decisions, tech product launches, energy shocks, financial regulatory announcements) create asymmetric proximity requirements based on event timing relative to earnings.

**Earnings Proximity Impact**: Sector-specific catalysts can extend proximity buffers to 20-35 days when events occur near earnings dates, with buffers varying significantly by sector risk profile and event type.

**Strategy Selection Calculation**:
```python
# Sector event proximity adjustments
sector_adjustments = {
    'biotech_fda': {'proximity_multiplier': 2.5, 'event_volatility': 3.0},
    'tech_launch': {'proximity_multiplier': 2.0, 'event_volatility': 2.2},
    'energy_shock': {'proximity_multiplier': 2.2, 'event_volatility': 2.5},
    'financial_regulatory': {'proximity_multiplier': 1.8, 'event_volatility': 1.8}
}

sector_proximity = {}
sector_event = 'biotech_fda'  # Example sector event

for symbol in portfolio_symbols[:1]:  # Focus on affected sector
    earnings_date = datetime.fromisoformat(earnings_calendar[symbol])
    
    # Sector event adjustments
    config = sector_adjustments.get(sector_event, sector_adjustments['tech_launch'])
    sector_buffer = 14 * config['proximity_multiplier']
    
    sector_eligible = []
    for exp_date in potential_expirations:
        days_to_earnings = (earnings_date - exp_date).days
        
        if days_to_earnings > sector_buffer:
            # Event-specific position sizing
            event_risk_adjustment = 1 / config['event_volatility']
            position_size = min(1.0, event_risk_adjustment)
            
            sector_eligible.append({
                'symbol': symbol,
                'expiration': exp_date,
                'earnings_date': earnings_date,
                'sector_buffer': sector_buffer,
                'event_volatility': config['event_volatility'],
                'position_size_multiplier': position_size,
                'sector_event': sector_event,
                'catalyst': f'sector_{sector_event}_earnings'
            })
    
    sector_proximity[symbol] = sector_eligible

# Result: Significantly extended proximity requirements for high-volatility sector events
```

**Implications**: Sector-specific proximity requirements prevent overexposure to event-driven volatility near earnings. Position sizing automatically scales based on sector event risk profiles.

##### Scenario 6: Multi-Asset Portfolio Liquidity Management - Cross-Asset Proximity Coordination

**Catalyst Context**: Portfolio-level management (catalysts: rebalancing stress, sector rotation, correlation breakdowns, risk parity adjustments) requires coordinated proximity management across multiple option positions.

**Earnings Proximity Impact**: Cross-asset analysis detects earnings calendar clustering, applying portfolio-wide proximity adjustments when multiple holdings have earnings in concentrated periods.

**Strategy Selection Calculation**:
```python
# Portfolio proximity coordination
portfolio_earnings_dates = [datetime.fromisoformat(date) for date in earnings_calendar.values()]

# Calculate earnings concentration
earnings_concentration = calculate_earnings_concentration(portfolio_earnings_dates)
portfolio_proximity_multiplier = 1 + (earnings_concentration * 0.5)

portfolio_proximity = {}
for symbol in portfolio_symbols:
    earnings_date = datetime.fromisoformat(earnings_calendar[symbol])
    
    # Portfolio-adjusted proximity requirements
    portfolio_buffer = 14 * portfolio_proximity_multiplier
    
    portfolio_eligible = []
    for exp_date in potential_expirations:
        days_to_earnings = (earnings_date - exp_date).days
        
        if days_to_earnings > portfolio_buffer:
            # Cross-asset correlation adjustment
            symbol_correlation = calculate_symbol_correlation(symbol, portfolio_symbols)
            correlation_adjustment = 1 - (symbol_correlation * 0.2)
            
            position_size = min(1.0, correlation_adjustment)
            
            portfolio_eligible.append({
                'symbol': symbol,
                'expiration': exp_date,
                'earnings_date': earnings_date,
                'portfolio_buffer': portfolio_buffer,
                'correlation_adjustment': correlation_adjustment,
                'position_size_multiplier': position_size,
                'earnings_concentration': earnings_concentration,
                'catalyst': 'portfolio_earnings_coordination'
            })
    
    portfolio_proximity[symbol] = portfolio_eligible

# Result: Coordinated proximity management across portfolio positions
```

**Implications**: Portfolio-level proximity coordination prevents concentrated earnings risk exposure. Position sizing reflects cross-asset earnings correlations and calendar clustering, enabling systematic diversification.

#### Conclusion Framework

This comprehensive earnings proximity >14 days from expiration requirement establishes a robust temporal risk management foundation for systematic cash-secured put strategies, dynamically adapting to all market catalysts while maintaining institutional-grade timing control. The framework ensures that earnings proximity remains both consistent and risk-appropriate across varying market conditions, with automatic adjustments for volatility, liquidity, and sector-specific factors. Implementation within the quantitative screening engine provides real-time earnings calendar validation, enabling systematic capital deployment that balances earnings timing risk with premium capture opportunities. The requirement serves as both a temporal risk optimization parameter and a catalyst for strategy adaptation, ensuring options selling strategies maintain viability across all market scenarios while optimizing risk-adjusted returns.
#### Context within Cash-Secured Put Filters and Quantitative Screening Engine

The credit rating filter represents a critical credit quality criterion in the quantitative screening engine for cash-secured puts, positioned as a key risk assessment parameter within the **Cash-Secured Put Filters** checklist (Subtask 2). This filter integrates credit rating evaluation into the broader options selling framework to ensure that positions are established only in underlying assets with sufficient credit quality, requiring cash-secured put candidates to have investment-grade credit ratings of BBB+ or equivalent from major rating agencies (S&P, Moody's, Fitch). The screening engine evaluates credit ratings to balance default risk exposure with premium capture potential, dynamically adjusting position sizing and strike selection based on credit quality assessments and market catalysts.

Credit rating serves as a quantitative credit quality gatekeeper that adapts to changing market conditions, ensuring cash-secured put strategies maintain institutional-grade risk control while optimizing entry conditions. The filter operates in real-time within the screening engine, cross-referencing credit ratings against volatility catalysts and sector-specific risk factors to dynamically adjust strike selection and position sizing based on credit quality evolution.

#### Explanation of Credit Rating BBB+ or Equivalent Requirement and Implications

The credit rating BBB+ or equivalent requirement establishes an investment-grade credit quality threshold for cash-secured put underlying assets, calculated as the lowest acceptable rating from recognized agencies (S&P BBB+, Moody's Baa1, Fitch BBB+). This requirement stems from institutional risk management principles that recognize credit quality as a primary determinant of default risk, with BBB+ representing the lowest investment-grade rating that provides reasonable assurance of capital preservation while maintaining sufficient market liquidity for options trading.

**Key Implications:**

1. **Default Risk Mitigation**: Ensures underlying assets have investment-grade credit quality, reducing the probability of bankruptcy or distressed selling that could cause 30-50%+ losses during default scenarios.

2. **Position Sizing Optimization**: Enables larger position allocations for higher-rated assets (A+/AA) while automatically reducing exposure for BBB+ rated companies, maintaining portfolio credit quality balance.

3. **Liquidity Considerations**: Investment-grade credits typically offer better options market liquidity with narrower bid-ask spreads and higher open interest, improving execution quality and slippage control.

4. **Volatility Adaptation**: Credit ratings naturally adjust to changing company fundamentals, with ratings pressure creating volatility spikes that require conservative position sizing during rating reviews or downgrades.

5. **Portfolio Diversification**: Facilitates credit-quality-aware position allocation across different rating tiers, improving portfolio-level risk diversification while maintaining investment-grade standards.

6. **Market Regime Adaptation**: Credit rating requirements become more stringent during economic stress periods, automatically reducing exposure to vulnerable BBB+ rated assets that may face downgrade risk.

The requirement creates a dynamic credit quality framework that adapts to changing fundamental conditions while maintaining institutional-grade risk management standards, ensuring systematic cash-secured put strategies achieve optimal risk-adjusted returns.

#### Detailed Example: Impact of Catalysts and Scenarios on Credit Rating Considerations and Strategy Selection

This section demonstrates how the credit rating BBB+ or equivalent requirement interacts with various market catalysts and scenarios extracted from the comprehensive options selling framework. Each category illustrates how external catalysts affect credit rating assessments, strategy selection, and position sizing adjustments for cash-secured puts, showing the dynamic interplay between market conditions, credit quality evolution, and risk management protocols. The analysis draws from the five key catalyst categories identified in the options selling framework: Market Conditions, Economic Factors, Company-Specific Events, External/Geopolitical Catalysts, and Portfolio and Risk Management Catalysts.

##### Market Conditions: Normal Market Environment - Stable Credit Quality Assessment

**Catalyst Context**: In stable market environments with moderate volatility (catalysts: economic stability, balanced monetary policy, steady growth), credit ratings remain relatively stable with predictable upgrade/downgrade patterns and minimal rating agency review activity.

**Credit Rating Impact**: Normal market conditions typically show stable BBB+ rated assets maintaining their investment-grade status, with options markets exhibiting normal liquidity and pricing efficiency. The screening engine accepts BBB+ rated assets with standard position sizing.

**Strategy Selection Calculation**:
```python
# Normal market credit rating assessment
credit_ratings = {
    'Company_A': 'BBB+',  # Investment grade
    'Company_B': 'BBB',   # Below threshold
    'Company_C': 'A-'     # Higher quality
}

eligible_assets = {}
for company, rating in credit_ratings.items():
    # Convert ratings to numerical scale for comparison
    rating_scale = {'AAA': 1.0, 'AA+': 0.95, 'AA': 0.90, 'AA-': 0.85,
                   'A+': 0.80, 'A': 0.75, 'A-': 0.70,
                   'BBB+': 0.65, 'BBB': 0.60, 'BBB-': 0.55}
    
    if rating in rating_scale and rating_scale[rating] >= rating_scale['BBB+']:
        # Normal market position sizing (5% of portfolio)
        position_limit = 0.05
        
        # Rating-based size adjustment (higher rating = larger position)
        rating_multiplier = rating_scale[rating] / rating_scale['BBB+']
        adjusted_position = position_limit * rating_multiplier
        
        eligible_assets[company] = {
            'rating': rating,
            'position_limit': adjusted_position,
            'monitoring_frequency': 'monthly',
            'catalyst': 'normal_market_stability'
        }

# Result: BBB+ and higher rated assets qualify with standard sizing
```

**Implications**: Enables full utilization of position sizing limits for BBB+ rated assets during stable periods. Strategy selection focuses on BBB+ rated companies with strong balance sheets, optimizing the balance between credit quality and premium yield potential.

##### Market Conditions: High Volatility Events - Elevated Rating Review Risk

**Catalyst Context**: During periods of elevated uncertainty (catalysts: geopolitical tensions, economic data surprises, central bank shocks, systemic risk events), credit rating agencies increase review activity, creating volatility in BBB+ rated assets that may face downgrade pressure.

**Credit Rating Impact**: Crisis conditions elevate downgrade risk for BBB+ rated assets, with rating agencies placing more companies on negative watchlists. Options markets show increased volatility and wider credit spreads, requiring conservative position sizing.

**Strategy Selection Calculation**:
```python
# High volatility credit rating adjustment
volatility_event = True
downgrade_risk_multiplier = 1.5  # Increased downgrade risk

crisis_rating_adjustments = {}
for company, data in eligible_assets.items():
    # Crisis-adjusted position sizing
    crisis_limit = data['position_limit'] * (1 / downgrade_risk_multiplier)
    
    # Enhanced monitoring during rating reviews
    monitoring_upgrade = 'weekly' if volatility_event else data['monitoring_frequency']
    
    # Conservative strike selection (more OTM)
    strike_adjustment = 1.1  # 10% further OTM to reduce exercise risk
    
    crisis_rating_adjustments[company] = {
        'original_limit': data['position_limit'],
        'crisis_limit': crisis_limit,
        'monitoring_frequency': monitoring_upgrade,
        'strike_adjustment': strike_adjustment,
        'risk_rating': 'elevated' if data['rating'] == 'BBB+' else 'moderate',
        'catalyst': 'high_volatility_downgrade_risk'
    }

# Result: Reduced position sizes, increased monitoring for BBB+ rated assets
```

**Implications**: Automatic position size reduction protects against potential rating downgrades during crisis periods. Strategy selection prioritizes more conservative strikes and shorter expirations to minimize exposure to credit quality deterioration.

##### Economic Factors: Recessionary Pressures - Broad-Based Rating Downgrade Risk

**Catalyst Context**: During economic downturns (catalysts: GDP contraction, unemployment spikes, corporate earnings declines, inflationary pressures), credit rating agencies face increased downgrade pressure across BBB+ rated companies due to deteriorating fundamentals.

**Credit Rating Impact**: Recessionary environments create correlated downgrade risk across industries, with BBB+ rated assets particularly vulnerable to rating actions. Options markets reflect increased credit risk through higher volatility and wider credit spreads.

**Strategy Selection Calculation**:
```python
# Economic recession credit rating analysis
recession_indicators = {
    'gdp_growth': -0.5,  # Negative growth
    'unemployment_rate': 6.5,  # Elevated unemployment
    'corporate_defaults': 2.8  # Higher default rates
}

# Recession-adjusted rating thresholds
recession_downgrade_probability = 0.25  # 25% chance of downgrade for BBB+
recession_rating_adjustments = {}

for company, data in eligible_assets.items():
    # Economic stress adjustment
    stress_multiplier = 1 + (recession_downgrade_probability * 0.5)
    recession_limit = data['position_limit'] / stress_multiplier
    
    # Industry-specific recession vulnerability
    industry_risk = get_industry_recession_risk(company)
    industry_adjustment = 1 + (industry_risk * 0.3)
    
    final_limit = recession_limit / industry_adjustment
    
    recession_rating_adjustments[company] = {
        'economic_stress_limit': final_limit,
        'downgrade_probability': recession_downgrade_probability,
        'industry_risk_factor': industry_risk,
        'monitoring_frequency': 'bi_weekly',
        'strategy_restriction': 'cash_secured_only',  # No naked positions
        'catalyst': 'recessionary_downgrade_pressure'
    }

# Result: Significantly reduced position sizes across BBB+ rated assets
```

**Implications**: Economic downturns trigger broad-based position size reductions and enhanced monitoring. Strategy selection focuses on defensive sectors and companies with strong cash positions to mitigate recession-related credit deterioration.

##### Economic Factors: Inflationary Environment - Sector-Specific Rating Impacts

**Catalyst Context**: During inflationary periods (catalysts: rising input costs, wage pressures, interest rate hikes, commodity price volatility), credit ratings face asymmetric pressure with certain sectors (energy, materials) experiencing upgrade potential while others face downgrade risk.

**Credit Rating Impact**: Inflation creates sector-divergent rating dynamics, with BBB+ rated assets in inflation-sensitive industries facing particular pressure from margin compression and refinancing challenges.

**Strategy Selection Calculation**:
```python
# Inflationary environment credit rating analysis
inflation_rate = 4.2  # High inflation
sector_inflation_sensitivity = {
    'energy': -0.3,     # Potential upgrades (higher prices)
    'materials': -0.2,  # Mixed impact
    'technology': 0.1,  # Potential downgrades (margin pressure)
    'consumer': 0.2     # Downgrade risk (higher costs)
}

inflation_rating_adjustments = {}
for company, data in eligible_assets.items():
    company_sector = get_company_sector(company)
    inflation_impact = sector_inflation_sensitivity.get(company_sector, 0)
    
    # Inflation-adjusted position sizing
    inflation_multiplier = 1 + abs(inflation_impact)
    adjusted_limit = data['position_limit'] / inflation_multiplier
    
    # Rating trajectory adjustment
    if inflation_impact < -0.1:  # Benefiting sectors
        rating_trend = 'upgrade_potential'
        monitoring_freq = 'monthly'
    elif inflation_impact > 0.1:  # Pressured sectors
        rating_trend = 'downgrade_risk'
        monitoring_freq = 'weekly'
    else:
        rating_trend = 'stable'
        monitoring_freq = 'monthly'
    
    inflation_rating_adjustments[company] = {
        'inflation_adjusted_limit': adjusted_limit,
        'sector_inflation_sensitivity': inflation_impact,
        'rating_trend': rating_trend,
        'monitoring_frequency': monitoring_freq,
        'strategy_adjustment': 'sector_rotation' if abs(inflation_impact) > 0.15 else 'standard',
        'catalyst': 'inflationary_sector_impact'
    }

# Result: Sector-specific position adjustments based on inflation sensitivity
```

**Implications**: Inflation creates opportunities for sector rotation within BBB+ rated assets. Strategy selection prioritizes inflation-resistant sectors while reducing exposure to margin-compressed industries facing downgrade risk.

##### Company-Specific Events: Earnings Disappointments - Individual Rating Pressure

**Catalyst Context**: Company-specific earnings misses or beats (catalysts: revenue shortfalls, margin compression, guidance revisions, competitive pressures) create targeted rating agency review activity for affected BBB+ rated companies.

**Credit Rating Impact**: Earnings disappointments trigger immediate rating agency scrutiny, with BBB+ rated companies facing heightened downgrade risk due to already constrained credit metrics.

**Strategy Selection Calculation**:
```python
# Company-specific earnings credit rating analysis
earnings_events = {
    'Company_A': {'earnings_surprise': -0.15, 'guidance_cut': True},  # Negative surprise
    'Company_B': {'earnings_surprise': 0.05, 'guidance_cut': False}   # Positive surprise
}

earnings_rating_impact = {}
for company, earnings_data in earnings_events.items():
    if company in eligible_assets:
        surprise_magnitude = abs(earnings_data['earnings_surprise'])
        guidance_impact = 1.5 if earnings_data.get('guidance_cut', False) else 1.0
        
        # Earnings-adjusted rating downgrade probability
        downgrade_probability = min(0.4, surprise_magnitude * 2) * guidance_impact
        
        # Position size reduction for affected companies
        earnings_limit = eligible_assets[company]['position_limit'] * (1 - downgrade_probability)
        
        # Immediate monitoring increase
        monitoring_freq = 'daily' if downgrade_probability > 0.2 else 'weekly'
        
        earnings_rating_impact[company] = {
            'earnings_surprise': earnings_data['earnings_surprise'],
            'downgrade_probability': downgrade_probability,
            'earnings_adjusted_limit': earnings_limit,
            'monitoring_frequency': monitoring_freq,
            'trading_restriction': 'halt_new_positions' if downgrade_probability > 0.3 else 'reduced_sizing',
            'catalyst': 'earnings_disappointment_rating_pressure'
        }

# Result: Immediate position adjustments for earnings-impacted BBB+ companies
```

**Implications**: Earnings events trigger rapid position adjustments and increased monitoring. Strategy selection automatically restricts or eliminates exposure to BBB+ rated companies experiencing negative earnings catalysts.

##### Company-Specific Events: Management Changes - Governance Rating Impacts

**Catalyst Context**: Leadership transitions or governance changes (catalysts: CEO departures, board restructuring, activist investor involvement, succession planning issues) create rating agency concern about management quality and strategic direction.

**Credit Rating Impact**: Management changes introduce uncertainty that rating agencies view negatively, particularly for BBB+ rated companies where governance quality is already a rating constraint.

**Strategy Selection Calculation**:
```python
# Management change credit rating analysis
management_events = {
    'Company_A': {'ceo_departure': True, 'successor_experience': 'low', 'board_support': True},
    'Company_B': {'activist_pressure': True, 'strategic_review': True, 'board_changes': False}
}

governance_rating_impact = {}
for company, mgmt_data in management_events.items():
    if company in eligible_assets:
        # Governance risk assessment
        risk_factors = sum([
            1 if mgmt_data.get('ceo_departure', False) else 0,
            1 if mgmt_data.get('successor_experience') == 'low' else 0,
            1 if mgmt_data.get('activist_pressure', False) else 0,
            1 if not mgmt_data.get('board_support', True) else 0
        ])
        
        governance_risk_score = risk_factors / 4.0  # 0-1 scale
        
        # Governance-adjusted position sizing
        governance_limit = eligible_assets[company]['position_limit'] * (1 - governance_risk_score)
        
        # Rating outlook adjustment
        if governance_risk_score > 0.5:
            rating_outlook = 'negative_watch'
            monitoring_freq = 'weekly'
        elif governance_risk_score > 0.25:
            rating_outlook = 'stable_negative'
            monitoring_freq = 'bi_weekly'
        else:
            rating_outlook = 'stable'
            monitoring_freq = 'monthly'
        
        governance_rating_impact[company] = {
            'governance_risk_score': governance_risk_score,
            'risk_factors': risk_factors,
            'governance_adjusted_limit': governance_limit,
            'rating_outlook': rating_outlook,
            'monitoring_frequency': monitoring_freq,
            'strategy_implication': 'increased_due_diligence' if governance_risk_score > 0.25 else 'standard',
            'catalyst': 'management_change_governance_impact'
        }

# Result: Governance-based position adjustments for management event companies
```

**Implications**: Management changes trigger governance-focused rating reviews and position adjustments. Strategy selection requires enhanced due diligence for BBB+ rated companies undergoing leadership transitions.

##### External/Geopolitical Catalysts: Trade War Escalation - Global Supply Chain Rating Impacts

**Catalyst Context**: International trade conflicts (catalysts: tariff impositions, trade agreement breakdowns, supply chain disruptions, currency volatility) create rating pressure on BBB+ rated companies with international exposure.

**Credit Rating Impact**: Trade wars introduce revenue uncertainty and margin pressure that rating agencies assess negatively, particularly affecting BBB+ rated companies in global industries.

**Strategy Selection Calculation**:
```python
# Trade war escalation credit rating analysis
trade_war_impacts = {
    'global_revenue_exposure': 0.35,  # 35% of revenues at risk
    'supply_chain_disruption': True,
    'currency_volatility': 0.12,  # 12% currency impact
    'tariff_exposure': 0.08  # 8% tariff impact
}

geopolitical_rating_adjustments = {}
for company, data in eligible_assets.items():
    company_trade_exposure = get_company_trade_exposure(company)
    
    # Geopolitical risk adjustment
    total_risk_impact = (
        trade_war_impacts['global_revenue_exposure'] * company_trade_exposure +
        trade_war_impacts['currency_volatility'] +
        trade_war_impacts['tariff_exposure']
    )
    
    geopolitical_limit = data['position_limit'] * (1 - total_risk_impact)
    
    # Rating agency watchlist probability
    watchlist_probability = min(0.6, total_risk_impact * 1.5)
    
    geopolitical_rating_adjustments[company] = {
        'trade_exposure': company_trade_exposure,
        'total_risk_impact': total_risk_impact,
        'geopolitical_adjusted_limit': geopolitical_limit,
        'watchlist_probability': watchlist_probability,
        'monitoring_frequency': 'weekly' if watchlist_probability > 0.3 else 'monthly',
        'hedging_requirement': 'currency_hedge' if trade_war_impacts['currency_volatility'] > 0.1 else 'none',
        'catalyst': 'trade_war_geopolitical_impact'
    }

# Result: Trade exposure-based position adjustments across BBB+ rated assets
```

**Implications**: Geopolitical events create global rating uncertainty requiring diversified position adjustments. Strategy selection favors domestically-focused BBB+ rated companies while reducing exposure to international trade-dependent assets.

##### External/Geopolitical Catalysts: Regulatory Changes - Industry-Specific Rating Impacts

**Catalyst Context**: Regulatory developments (catalysts: environmental regulations, healthcare reforms, financial industry changes, antitrust actions) create sector-specific rating implications for BBB+ rated companies.

**Credit Rating Impact**: Regulatory changes introduce compliance costs and business model uncertainty that rating agencies evaluate, with BBB+ rated companies in regulated industries facing particular scrutiny.

**Strategy Selection Calculation**:
```python
# Regulatory change credit rating analysis
regulatory_events = {
    'healthcare_reform': {'affected_sectors': ['healthcare', 'biotech'], 'impact_severity': 0.25},
    'environmental_regulation': {'affected_sectors': ['energy', 'materials'], 'impact_severity': 0.30},
    'financial_reregulation': {'affected_sectors': ['financials'], 'impact_severity': 0.35}
}

regulatory_rating_impact = {}
for company, data in eligible_assets.items():
    company_sector = get_company_sector(company)
    
    # Regulatory impact assessment
    regulatory_risk = 0
    for event, event_data in regulatory_events.items():
        if company_sector in event_data['affected_sectors']:
            regulatory_risk = event_data['impact_severity']
            break
    
    if regulatory_risk > 0:
        # Regulatory-adjusted position sizing
        regulatory_limit = data['position_limit'] * (1 - regulatory_risk)
        
        # Compliance monitoring increase
        compliance_monitoring = 'enhanced' if regulatory_risk > 0.25 else 'standard'
        
        regulatory_rating_impact[company] = {
            'sector': company_sector,
            'regulatory_risk': regulatory_risk,
            'regulatory_adjusted_limit': regulatory_limit,
            'compliance_monitoring': compliance_monitoring,
            'rating_implication': 'potential_downgrade' if regulatory_risk > 0.2 else 'stable',
            'strategy_adjustment': 'sector_avoidance' if regulatory_risk > 0.3 else 'reduced_exposure',
            'catalyst': 'regulatory_change_sector_impact'
        }

# Result: Sector-specific regulatory adjustments for BBB+ rated assets
```

**Implications**: Regulatory changes create sector-specific rating risks requiring targeted position adjustments. Strategy selection automatically reduces exposure to regulated industries facing adverse regulatory developments.

##### Portfolio and Risk Management Catalysts: Concentration Risk - Rating-Based Diversification

**Catalyst Context**: Portfolio management considerations (catalysts: sector concentration, credit quality clustering, correlation increases, risk parity requirements) create rating-based diversification needs across BBB+ rated positions.

**Credit Rating Impact**: Portfolio concentration in BBB+ rated assets increases correlated downgrade risk, requiring rating-aware diversification adjustments to maintain overall portfolio credit quality.

**Strategy Selection Calculation**:
```python
# Portfolio concentration credit rating analysis
portfolio_ratings = ['BBB+', 'BBB+', 'A-', 'BBB+', 'BBB-']  # Current holdings
portfolio_sector_concentration = {
    'technology': 0.35,  # 35% technology exposure
    'healthcare': 0.25,  # 25% healthcare exposure
    'financials': 0.20   # 20% financials exposure
}

# Rating concentration assessment
bbb_rating_count = portfolio_ratings.count('BBB+')
total_positions = len(portfolio_ratings)
rating_concentration = bbb_rating_count / total_positions

# Diversification adjustment
if rating_concentration > 0.4:  # Over 40% BBB+ exposure
    concentration_penalty = (rating_concentration - 0.4) * 2  # 20% penalty per 10% over limit
    diversification_required = True
else:
    concentration_penalty = 0
    diversification_required = False

portfolio_rating_adjustments = {
    'rating_concentration': rating_concentration,
    'concentration_penalty': concentration_penalty,
    'diversification_required': diversification_required,
    'max_new_bbb_position': 0.03 if diversification_required else 0.05,  # Reduced sizing
    'rebalancing_priority': 'high' if concentration_penalty > 0.1 else 'normal',
    'catalyst': 'portfolio_concentration_rating_risk'
}

# Result: Rating-based diversification adjustments for portfolio optimization
```

**Implications**: Portfolio concentration creates rating-based diversification requirements. Strategy selection automatically limits new BBB+ positions when concentration thresholds are exceeded.

##### Portfolio and Risk Management Catalysts: Liquidity Stress Testing - Rating Contingency Planning

**Catalyst Context**: Risk management protocols (catalysts: liquidity stress testing, rating downgrade scenarios, correlation stress events, VaR limit breaches) require rating-based contingency planning.

**Credit Rating Impact**: Stress testing reveals potential rating migration paths, with BBB+ rated assets having elevated downgrade probabilities during liquidity stress events.

**Strategy Selection Calculation**:
```python
# Liquidity stress credit rating analysis
stress_scenarios = {
    'market_crash': {'downgrade_probability': 0.15, 'correlation_increase': 0.3},
    'sector_crisis': {'downgrade_probability': 0.25, 'correlation_increase': 0.4},
    'rating_agency_crisis': {'downgrade_probability': 0.35, 'correlation_increase': 0.5}
}

stress_rating_contingencies = {}
for scenario, params in stress_scenarios.items():
    # Stress-adjusted rating thresholds
    stress_downgrade_prob = params['downgrade_probability']
    
    # Contingency position sizing
    stress_limit = 0.05 * (1 - stress_downgrade_prob)  # Base 5% reduced by downgrade risk
    
    # Correlation-adjusted diversification
    correlation_penalty = params['correlation_increase'] * 0.2
    final_stress_limit = stress_limit * (1 - correlation_penalty)
    
    stress_rating_contingencies[scenario] = {
        'downgrade_probability': stress_downgrade_prob,
        'correlation_increase': params['correlation_increase'],
        'stress_adjusted_limit': final_stress_limit,
        'contingency_actions': ['reduce_positions', 'increase_collateral', 'hedge_correlations'] if stress_downgrade_prob > 0.2 else ['monitor_closely'],
        'recovery_timeframe': '3_months' if stress_downgrade_prob > 0.2 else '1_month',
        'catalyst': f'{scenario}_stress_rating_contingency'
    }

# Result: Rating-based contingency planning for stress scenarios
```

**Implications**: Stress testing creates rating-aware contingency protocols. Strategy selection includes automatic position reductions and hedging requirements for BBB+ rated assets during stress scenarios.

#### Conclusion Framework

This comprehensive credit rating BBB+ or equivalent requirement establishes a robust credit quality foundation for systematic cash-secured put strategies, dynamically adapting to all market catalysts while maintaining institutional-grade risk control. The framework ensures that credit quality remains both consistent and risk-appropriate across varying market conditions, with automatic adjustments for volatility, liquidity, and catalyst-specific factors. Implementation within the quantitative screening engine provides real-time credit rating validation, enabling systematic capital deployment that balances default risk mitigation with premium capture opportunities. The requirement serves as both a credit quality optimization parameter and a catalyst for strategy adaptation, ensuring options selling strategies maintain viability across all market scenarios while optimizing risk-adjusted returns. The detailed scenario analysis demonstrates how external catalysts from all five framework categories necessitate dynamic credit rating considerations, with automatic position sizing, monitoring frequency, and strike selection adjustments to maintain institutional-grade risk management standards. This approach ensures that BBB+ rated assets receive appropriate treatment based on their elevated credit sensitivity while still enabling systematic premium capture in stable market environments.
#### Context within Cash-Secured Put Filters and Quantitative Screening Engine

The sector diversification filter represents a critical portfolio risk management parameter in the quantitative screening engine for cash-secured puts, positioned as a key concentration limit within the **Cash-Secured Put Filters** checklist (Subtask 2). This filter integrates sector exposure analysis into the broader options selling framework to ensure that portfolio allocation is diversified across economic sectors, requiring cash-secured put candidates to maintain sector exposure below 20% of total portfolio value to qualify for execution. The screening engine evaluates sector classifications against portfolio holdings to dynamically adjust position sizing and sector allocation based on diversification requirements and risk management imperatives.

Sector diversification serves as a quantitative concentration gatekeeper that adapts to changing market conditions, ensuring cash-secured put strategies maintain institutional-grade portfolio risk control while optimizing capital allocation across economic sectors. The filter operates in real-time within the screening engine, cross-referencing sector classifications against portfolio composition and volatility catalysts to dynamically adjust strike selection and position sizing based on diversification objectives.

#### Explanation of Sector Diversification Max 20% per Sector Requirement and Implications

The sector diversification max 20% per sector requirement establishes a concentration limit for portfolio exposure to individual economic sectors, calculated as the percentage of total portfolio value allocated to options positions in companies within a specific sector, requiring this exposure to remain below 20% to maintain acceptable diversification levels. This requirement stems from institutional risk management principles that recognize sector concentration as a primary driver of portfolio volatility and systematic risk, with overexposure to single sectors creating amplified loss potential during sector-specific adverse events.

**Key Implications:**

1. **Risk Mitigation**: Prevents catastrophic losses from sector-wide adverse events (e.g., regulatory changes in healthcare, commodity price shocks in energy), limiting maximum portfolio loss from any single sector to 20%.

2. **Position Sizing Optimization**: Enables larger position allocations in diversified sectors while automatically reducing exposure in concentrated sectors, maintaining portfolio balance across economic cycles.

3. **Strategy Adaptation**: Provides systematic sector rotation signals, automatically favoring under-allocated sectors and avoiding over-concentrated ones based on portfolio composition.

4. **Performance Consistency**: Maintains minimum diversification thresholds across different market regimes, ensuring systematic options selling generates consistent results regardless of sector performance.

5. **Capital Efficiency**: Optimizes the trade-off between sector-specific opportunities and portfolio-wide risk, ensuring efficient deployment of portfolio cash reserves.

6. **Regulatory Compliance**: Aligns with institutional investment guidelines requiring diversified exposure, preventing violations of concentration limits in managed portfolios.

The requirement creates a dynamic diversification framework that adapts to all market catalysts while maintaining institutional-grade risk management standards, ensuring systematic cash-secured put strategies achieve optimal risk-adjusted returns.

#### Detailed Example: Impact of Catalysts and Scenarios on Sector Diversification and Strategy Selection

This section demonstrates how the sector diversification max 20% per sector requirement interacts with various market catalysts and scenarios extracted from the comprehensive options selling framework. Each scenario illustrates how external catalysts affect sector diversification calculations, strategy selection, and position sizing adjustments for cash-secured puts, showing the dynamic interplay between market conditions, sector exposure, and risk management protocols.

##### Scenario 1: Normal Market Conditions - Balanced Sector Allocation

**Catalyst Context**: In stable market environments with moderate volatility (catalysts: economic stability, balanced monetary policy, steady growth), sector diversification operates within normal allocation limits, allowing standard position sizing across well-diversified sectors.

**Sector Diversification Impact**: Normal market conditions support balanced sector allocation with each sector maintaining exposure below 20%, enabling full utilization of position sizing limits across economic sectors.

**Strategy Selection Calculation**:

```python
# Normal market sector diversification analysis
portfolio_value = 1000000  # $1M portfolio
sector_exposure = {
    'technology': 0.12,  # 12% technology exposure
    'healthcare': 0.15,  # 15% healthcare exposure
    'financials': 0.08,  # 8% financials exposure
    'consumer': 0.10     # 10% consumer exposure
}

target_sector = 'energy'  # New position consideration
current_energy_exposure = sector_exposure.get('energy', 0)  # 0% currently

# Check diversification limit
max_sector_allocation = 0.20  # 20% max per sector
available_sector_capacity = max_sector_allocation - current_energy_exposure

if available_sector_capacity > 0:
    # Calculate position size based on sector capacity
    max_position_size = portfolio_value * available_sector_capacity * 0.05  # 5% normal position limit
    position_size = min(10000, max_position_size)  # $10K position size
    # Result: Position approved with standard sector diversification
```

**Implications**: Enables full portfolio utilization with balanced sector exposure, optimizing diversification benefits while maintaining growth opportunities.

##### Scenario 2: High Volatility Events - Sector Risk Concentration

**Catalyst Context**: During periods of elevated uncertainty (catalysts: geopolitical tensions, economic data surprises, central bank shocks, systemic risk events), sector diversification requirements become more stringent to prevent amplified losses from correlated sector declines.

**Sector Diversification Impact**: Crisis conditions reduce sector allocation limits as diversification requirements tighten, forcing position size reductions in vulnerable sectors to maintain overall portfolio balance.

**Strategy Selection Calculation**:

```python
# High volatility sector diversification adjustment
volatility_event = True
volatility_diversification_multiplier = 0.8  # 20% reduction in limits

adjusted_sector_limits = {sector: limit * volatility_diversification_multiplier 
                         for sector, limit in sector_exposure.items()}

crisis_sector = 'financials'  # Financials hit hard in crisis
current_exposure = adjusted_sector_limits['financials']

if current_exposure >= max_sector_allocation * 0.9:  # Near limit
    # Crisis position sizing reduction
    crisis_position_limit = portfolio_value * (max_sector_allocation - current_exposure) * 0.25  # 25% normal
    position_size = min(2500, crisis_position_limit)  # Significantly reduced
    # Result: Position size reduced to manage sector concentration risk
```

**Implications**: Automatic position size reductions during crises prevent sector concentration amplification, prioritizing portfolio-wide risk control over individual sector opportunities.

##### Scenario 3: Earnings Season - Sector-Specific Earnings Clustering

**Catalyst Context**: Pre-earnings periods (catalysts: analyst expectations, institutional positioning, conference call uncertainty) show concentrated earnings activity within specific sectors, requiring adjusted diversification calculations.

**Sector Diversification Impact**: Earnings season creates sector-specific exposure spikes due to clustered reporting, forcing diversification adjustments to account for amplified sector risk during earnings periods.

**Strategy Selection Calculation**:

```python
# Earnings season sector diversification analysis
earnings_sector = 'technology'  # Tech earnings concentration
earnings_risk_multiplier = 1.3  # 30% higher risk during earnings

earnings_adjusted_limit = max_sector_allocation / earnings_risk_multiplier
current_earnings_exposure = sector_exposure.get('technology', 0)

if current_earnings_exposure >= earnings_adjusted_limit:
    # Earnings season position restriction
    earnings_position_size = 0  # No new positions in concentrated earnings sector
    alternative_sector = 'utilities'  # Switch to defensive sector
    # Result: Position blocked in earnings-heavy sector, redirected to alternatives
```

**Implications**: Pre-earnings diversification adjustments prevent overexposure to sector-wide earnings volatility, automatically routing capital to less concentrated sectors.

##### Scenario 4: Holiday and Low Activity Periods - Extended Sector Holding

**Catalyst Context**: Holiday periods (catalysts: Christmas/New Year effects, summer seasonality, reduced participation) show stable sector exposures with reduced rebalancing activity, allowing slightly higher sector concentrations due to lower market impact.

**Sector Diversification Impact**: Low activity periods permit minor sector limit extensions due to reduced trading activity and market impact, while maintaining overall diversification discipline.

**Strategy Selection Calculation**:

```python
# Holiday period sector diversification adjustment
holiday_period = True
holiday_flexibility = 1.1  # 10% flexibility in limits

holiday_sector_limits = {sector: limit * holiday_flexibility 
                        for sector, limit in sector_exposure.items()}

holiday_sector = 'consumer'  # Retail holiday strength
current_holiday_exposure = holiday_sector_limits['consumer']

if current_holiday_exposure < max_sector_allocation * holiday_flexibility:
    # Holiday position sizing with flexibility
    holiday_position_size = portfolio_value * (max_sector_allocation * holiday_flexibility - current_holiday_exposure) * 0.75  # Conservative
    # Result: Slightly increased position size allowed during holiday stability
```

**Implications**: Holiday flexibility maintains diversification while capitalizing on sector-specific seasonal patterns, with automatic reversion to standard limits post-holiday.

##### Scenario 5: Sector-Specific Liquidity Events - Catalyst-Driven Sector Rotation

**Catalyst Context**: Sector events (catalysts: biotech FDA decisions, tech product launches, energy shocks, financial regulatory announcements) create asymmetric sector impacts, requiring dynamic diversification adjustments.

**Sector Diversification Impact**: Sector-specific catalysts trigger diversification limit adjustments, with affected sectors facing reduced allocation limits while unaffected sectors receive increased capacity.

**Strategy Selection Calculation**:

```python
# Sector event diversification adjustment
sector_event = 'biotech_fda'  # Biotech FDA decision
affected_sector = 'healthcare'
event_risk_multiplier = 2.0  # Double risk for affected sector

event_adjusted_limits = sector_exposure.copy()
event_adjusted_limits[affected_sector] = max_sector_allocation / event_risk_multiplier

current_event_exposure = event_adjusted_limits[affected_sector]

if current_event_exposure >= event_adjusted_limits[affected_sector]:
    # Block positions in affected sector
    event_position_size = 0
    # Redirect to alternative sector
    alternative_sector = 'technology'  # Unaffected sector
    alternative_exposure = event_adjusted_limits.get(alternative_sector, 0)
    alternative_position_size = portfolio_value * (max_sector_allocation - alternative_exposure) * 0.6
    # Result: Capital redirected from high-risk sector to diversified alternatives
```

**Implications**: Sector event diversification prevents concentration in volatile sectors, automatically optimizing portfolio allocation across catalyst-impacted market segments.

##### Scenario 6: Multi-Asset Portfolio Liquidity Management - Cross-Sector Correlation Adjustment

**Catalyst Context**: Portfolio-level management (catalysts: rebalancing stress, sector rotation, correlation breakdowns, risk parity adjustments) requires coordinated sector diversification across multiple portfolio positions.

**Sector Diversification Impact**: Cross-asset analysis detects correlated sector exposures, applying portfolio-wide diversification adjustments to maintain optimal risk distribution across economic sectors.

**Strategy Selection Calculation**:

```python
# Portfolio sector diversification coordination
portfolio_sector_correlations = {
    'technology_healthcare': 0.75,
    'technology_financials': 0.65,
    'healthcare_financials': 0.70
}

# Calculate effective sector diversification
effective_sector_limits = {}
for sector in sector_exposure.keys():
    correlated_sectors = [s for s in sector_exposure.keys() if s != sector]
    avg_correlation = np.mean([portfolio_sector_correlations.get(f"{sector}_{s}", 0.5) 
                              for s in correlated_sectors])
    
    # Adjust limits based on correlation
    correlation_adjustment = 1 - (avg_correlation * 0.3)  # Reduce limits for correlated sectors
    effective_sector_limits[sector] = max_sector_allocation * correlation_adjustment

# Portfolio diversification check
portfolio_sector = 'technology'
effective_limit = effective_sector_limits[portfolio_sector]
current_portfolio_exposure = sector_exposure[portfolio_sector]

if current_portfolio_exposure < effective_limit:
    # Portfolio-coordinated position sizing
    portfolio_position_size = portfolio_value * (effective_limit - current_portfolio_exposure) * 0.8  # Conservative
    # Result: Position size adjusted for portfolio-wide sector correlation
```

**Implications**: Portfolio-level sector diversification coordination prevents unintended concentration through correlated positions, enabling systematic risk management across interconnected economic sectors.

#### Conclusion Framework

This comprehensive sector diversification max 20% per sector requirement establishes a robust portfolio risk management foundation for systematic cash-secured put strategies, dynamically adapting to all market catalysts while maintaining institutional-grade diversification standards. The framework ensures that sector exposure remains both consistent and risk-appropriate across varying market conditions, with automatic adjustments for volatility, liquidity, and sector-specific factors. Implementation within the quantitative screening engine provides real-time sector exposure validation, enabling systematic capital deployment that balances sector opportunities with portfolio-wide risk management imperatives. The requirement serves as both a diversification optimization parameter and a catalyst for strategy adaptation, ensuring options selling strategies maintain viability across all market scenarios while optimizing risk-adjusted returns.

- [x] Sector diversification: Max 20% per sector

**Success Criteria**:
- False positive rate: <5%
- Historical win rate: >75% on backtested trades
- Maximum drawdown: <10% under stress scenarios

### Subtask 3: Risk Management Framework
**Objective**: Implement institutional-grade risk controls and position sizing.

**Position Sizing Rules**:
- [ ] Maximum allocation: 5% of total portfolio per trade
- [ ] Portfolio diversification: Max 10 positions at any time
- [ ] Greeks limits: Net delta ±0.2, gamma ±0.05
- [ ] Volatility exposure: Vega notional <2% of portfolio
- [ ] Sector concentration: Max 25% per sector
- [ ] Stop-loss triggers: 20% premium decay or volatility spike
- [ ] Rebalancing frequency: Weekly review

**Risk Metrics Monitoring**:
- [ ] Value at Risk (VaR): Daily calculation at 95% confidence
- [ ] Expected shortfall: Weekly stress testing
- [ ] Correlation matrix: Updated monthly
- [ ] Liquidity risk: Bid-ask spread monitoring
- [ ] Counterparty risk: Brokerage concentration limits

**Success Criteria**:
- Maximum portfolio loss: <10% in any 30-day period
- Risk-adjusted returns: Sharpe ratio >1.5
- Compliance: All trades within regulatory limits

### Subtask 4: LLM Interpretation Engine
**Objective**: Integrate AI capabilities for qualitative analysis and risk assessment.

**Prompt Engineering Framework**:
- [ ] Trade rationale generation templates
- [ ] Risk factor identification prompts
- [ ] Market sentiment analysis queries
- [ ] Earnings impact assessment
- [ ] Sector-specific context integration
- [ ] Macro-economic factor consideration

**LLM Analysis Components**:
- [ ] Pre-trade approval: AI review of quantitative signals
- [ ] Risk narrative generation: Explain potential catalysts
- [ ] Alternative scenario modeling: Best/worst case analysis
- [ ] Comparative analysis: Similar historical trades
- [ ] Exit strategy recommendations

**Success Criteria**:
- AI accuracy: >85% alignment with quantitative signals
- Response time: <5 seconds per analysis
- Cost efficiency: < $0.01 per trade analysis

### Subtask 5: Automated Decision Matrix
**Objective**: Create algorithmic trade selection combining quantitative scores and LLM insights.

**Scoring Algorithm**:
- [ ] Quantitative score: Weighted average of all filters (70% weight)
- [ ] LLM confidence score: AI assessment of trade viability (20% weight)
- [ ] Risk adjustment factor: Portfolio impact consideration (10% weight)
- [ ] Threshold requirements: Minimum score of 7.5/10 for execution

**Decision Flow**:
- [ ] Initial screening: Apply all quantitative filters
- [ ] LLM review: Generate interpretive analysis
- [ ] Portfolio fit: Check diversification and risk limits
- [ ] Final approval: Human override capability for edge cases
- [ ] Order generation: Automated limit order creation

**Success Criteria**:
- Automation rate: >90% of eligible trades executed automatically
- Override frequency: <5% requiring manual intervention
- Execution quality: Average slippage <2% of premium

### Subtask 6: Backtesting and Optimization
**Objective**: Validate strategy performance across market cycles.

**Backtesting Framework**:
- [ ] Historical data: 10+ years of options data
- [ ] Market regime segmentation: Bull, bear, sideways markets
- [ ] Walk-forward analysis: Rolling 2-year test periods
- [ ] Transaction cost modeling: Commissions and slippage
- [ ] Performance attribution: Source of returns analysis

**Parameter Optimization**:
- [ ] Filter threshold tuning using genetic algorithms
- [ ] Weight optimization via Monte Carlo simulation
- [ ] Risk parameter calibration to target volatility
- [ ] Seasonal adjustment factors for different months

**Success Criteria**:
- Backtested Sharpe ratio: >1.2
- Out-of-sample performance: Within 10% of in-sample results
- Drawdown analysis: Maximum drawdown <15% in worst periods

### Subtask 7: Execution and Monitoring System
**Objective**: Implement real-time trade execution and position management.

**Execution Layer**:
- [ ] Brokerage API integration with authentication
- [ ] Order type optimization: Limit orders with time-in-force
- [ ] Position reconciliation: Daily portfolio sync
- [ ] Tax optimization: Long-term vs short-term considerations

**Monitoring Dashboard**:
- [ ] Real-time P&L tracking
- [ ] Greeks exposure visualization
- [ ] Risk limit alerts with escalation
- [ ] Performance vs benchmark comparisons
- [ ] Automated rebalancing triggers

**Success Criteria**:
- Execution success rate: >99% of orders filled
- Monitoring latency: <1 minute for critical alerts
- System uptime: 99.9% availability

### Subtask 8: Reporting and Analytics
**Objective**: Generate institutional-quality performance reports and insights.

**Performance Reporting**:
- [ ] Monthly comprehensive reports with risk metrics
- [ ] Trade-by-trade analysis with entry/exit rationale
- [ ] Attribution analysis: Premium decay vs underlying movement
- [ ] Benchmark comparisons: S&P 500 options strategies
- [ ] Tax reporting integration

**Analytics Dashboard**:
- [ ] Interactive visualization of portfolio Greeks
- [ ] Historical performance heatmaps
- [ ] Scenario analysis tools
- [ ] Custom alerting based on user preferences

**Success Criteria**:
- Report generation: Fully automated monthly delivery
- Analytics depth: Covers all major risk and performance dimensions
- User adoption: >80% of features actively used

## Implementation Timeline

**Phase 1 (Weeks 1-4)**: Data collection and quantitative filters
**Phase 2 (Weeks 5-8)**: LLM integration and decision framework
**Phase 3 (Weeks 9-12)**: Backtesting, optimization, and risk management
**Phase 4 (Weeks 13-16)**: Execution system and monitoring
**Phase 5 (Weeks 17-20)**: Live testing and production deployment

## Risk Considerations

- **Model Risk**: Regular recalibration every 3 months
- **Liquidity Risk**: Minimum volume thresholds for all trades
- **Counterparty Risk**: Diversification across multiple brokerages
- **Regulatory Risk**: Compliance with SEC options regulations
- **Technology Risk**: Redundant systems and disaster recovery

## Success Metrics

- **Financial**: 8-12% annualized returns with <10% volatility
- **Operational**: >95% automation rate with <1% error rate
- **Risk**: Maximum drawdown <12% across market cycles
- **Compliance**: 100% adherence to regulatory requirements

This plan provides a systematic, scalable approach to options selling that combines quantitative rigor with AI-driven insights, enabling passive income generation with institutional-grade risk management.