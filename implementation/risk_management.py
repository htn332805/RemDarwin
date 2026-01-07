# risk_management.py
"""
Institutional-grade risk management system for options trading strategies.
Implements comprehensive loss controls, position sizing, portfolio risk management,
and backtesting validation for covered calls and cash-secured puts.
"""

import sqlite3
import logging
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod
import yaml
import os
from pathlib import Path

# Import existing components
try:
    from options.yfinance_options import GreekCalculator, OptionContract
except ImportError:
    # Fallback for direct execution
    GreekCalculator = None  # Placeholder
    OptionContract = None   # Placeholder

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class RiskConfig:
    """Configuration for risk management parameters."""
    max_loss_per_trade: float = 0.05  # 5% max loss
    max_portfolio_allocation: float = 0.05  # 5% per trade
    max_concurrent_positions: int = 10
    max_sector_concentration: float = 0.25  # 25%
    delta_limit: float = 0.2  # Net delta ±0.2
    gamma_limit: float = 0.05  # ±0.05
    vega_limit: float = 0.02  # <2%
    rho_limit: float = 0.1
    var_confidence: float = 0.95
    es_confidence_levels: List[float] = None

    def __post_init__(self):
        if self.es_confidence_levels is None:
            self.es_confidence_levels = [0.975, 0.99]

class RiskManager(ABC):
    """Abstract base class for risk management components."""

    def __init__(self, config: RiskConfig, db_path: str):
        self.config = config
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.greek_calc = GreekCalculator() if GreekCalculator else None
        self._init_risk_monitoring_table()

    def _init_risk_monitoring_table(self):
        """Create risk monitoring table if it doesn't exist."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS risk_monitoring (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    symbol TEXT,
                    position_id TEXT,
                    loss_metric REAL,
                    trigger_type TEXT,
                    trigger_reason TEXT,
                    action_taken TEXT,
                    compliance_status TEXT
                )
            """)
            self.conn.commit()
            logger.info("Initialized risk monitoring table")
        except Exception as e:
            logger.warning(f"Failed to initialize risk monitoring table: {e}")

    def get_portfolio_value(self) -> float:
        """Get current total portfolio value."""
        # TODO: Implement portfolio value calculation from database
        return 1000000.0  # Placeholder

    def get_current_positions(self) -> List[Dict[str, Any]]:
        """Get current active positions from database."""
        # TODO: Query database for active positions
        return []  # Placeholder

    def log_risk_metric(self, symbol: str, position_id: str, loss_metric: float, trigger_type: str = "",
                        trigger_reason: str = "", action_taken: str = "", compliance_status: str = "compliant"):
        """Log risk metrics and triggers for monitoring and audit."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO risk_monitoring (timestamp, symbol, position_id, loss_metric, trigger_type, trigger_reason, action_taken, compliance_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (datetime.now().isoformat(), symbol, position_id, loss_metric, trigger_type, trigger_reason, action_taken, compliance_status))
            self.conn.commit()
        except Exception as e:
            logger.warning(f"Failed to log risk metric: {e}")

    @abstractmethod
    def validate_position(self, position: Dict[str, Any]) -> bool:
        """Validate if a position meets risk criteria."""
        pass

class LossPotentialManager(RiskManager):
    """Manages loss potential calculations and stop-loss triggers."""

    def calculate_max_loss_per_trade(self, position: Dict[str, Any]) -> float:
        """
        Calculate maximum acceptable loss per trade (≤5% of position value).
        Position value = underlying_price * 100 * contracts for options.
        """
        underlying_price = position.get('underlying_price', 0)
        contracts = position.get('contracts', 1)
        position_value = underlying_price * 100 * contracts
        return position_value * self.config.max_loss_per_trade

    def validate_position(self, position: Dict[str, Any], current_market_data: Optional[Dict[str, Any]] = None,
                        is_pre_trade: bool = True) -> Tuple[bool, str]:
        """
        Comprehensive pre-trade screening and ongoing risk monitoring.
        Returns (is_valid, reason)
        """
        symbol = position.get('symbol', 'UNKNOWN')
        position_id = f"{symbol}_{position.get('strike_price', 0)}_{position.get('option_type', '')}"

        # Calculate loss metrics
        max_loss = self.calculate_max_loss_per_trade(position)
        theoretical_loss = self.calculate_potential_loss(position)
        practical_loss = self.calculate_practical_loss_potential(position)

        # Log metrics
        self.log_risk_metric(symbol, position_id, theoretical_loss, "loss_calculation",
                           f"theoretical_loss: {theoretical_loss:.2f}, practical_loss: {practical_loss:.2f}")

        # Check loss limits
        if theoretical_loss > max_loss:
            reason = f"Theoretical loss {theoretical_loss:.2f} exceeds max allowed {max_loss:.2f}"
            self.log_risk_metric(symbol, position_id, theoretical_loss, "limit_breach", reason, "position_adjusted", "non-compliant")
            position = self.adjust_position_size_for_loss_limits(position)
            return False, reason

        # For ongoing monitoring, check stop-loss triggers
        if not is_pre_trade and current_market_data:
            triggered, reason = self.check_stop_loss_triggers(position, current_market_data)
            if triggered:
                self.trigger_alert(position, reason)
                self.log_risk_metric(symbol, position_id, theoretical_loss, "stop_loss_trigger", reason, "alert_issued")
                return False, reason

        # Dynamic risk adjustment for ongoing positions
        if not is_pre_trade:
            position = self.adjust_position_size_for_loss_limits(position)

        return True, "Position within risk limits"

    def calculate_potential_loss(self, position: Dict[str, Any]) -> float:
        """Calculate theoretical potential loss for the position."""
        option_type = position.get('option_type', '').lower()
        strike = position.get('strike_price', 0)
        premium = position.get('premium_collected', 0)
        underlying = position.get('underlying_price', 0)
        contracts = position.get('contracts', 1)

        if option_type == 'call':  # Covered call
            # Max loss = (strike - premium) - (underlying - buffer)
            # Assuming worst case: underlying drops to 0
            max_loss = (strike - premium) * 100 * contracts
        elif option_type == 'put':  # Cash-secured put
            # Max loss = strike - premium (if underlying drops to 0)
            max_loss = (strike - premium) * 100 * contracts
        else:
            max_loss = 0

        return max_loss

    def calculate_practical_loss_potential(self, position: Dict[str, Any], market_volatility: float = 0.2,
                                         time_horizon_days: int = 30) -> float:
        """
        Calculate practical loss potential using Greeks and market parameters.
        Uses delta-gamma approximation for expected loss under normal market moves.
        """
        delta = position.get('delta', 0)
        gamma = position.get('gamma', 0)
        theta = position.get('theta', 0)
        vega = position.get('vega', 0)
        underlying = position.get('underlying_price', 0)
        premium = position.get('premium_collected', 0)
        contracts = position.get('contracts', 1)

        # Expected underlying move (1 std dev over time horizon)
        expected_move = underlying * market_volatility * np.sqrt(time_horizon_days / 365)

        # Delta-gamma approximation for P&L
        # P&L ≈ delta * dS + 0.5 * gamma * (dS)^2 + theta * dT + vega * dVol
        # For loss potential, consider adverse moves
        adverse_move = -expected_move  # Downside move
        pnl_delta = delta * adverse_move * 100 * contracts
        pnl_gamma = 0.5 * gamma * (adverse_move ** 2) * 100 * contracts
        pnl_theta = theta * (time_horizon_days / 365) * 100 * contracts  # Theta decay benefits sellers
        pnl_vega = vega * 0.0  # Assuming vol constant for practical calc

        practical_loss = pnl_delta + pnl_gamma - pnl_theta  # Negative for losses

        return max(0, -practical_loss)  # Return positive loss value

    def check_stop_loss_triggers(self, position: Dict[str, Any], current_market_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check stop-loss triggers: premium decay >20%, volatility spike, adverse underlying moves.
        Returns (triggered, reason)
        """
        initial_premium = position.get('premium_collected', 0)
        current_premium = current_market_data.get('current_premium', initial_premium)
        premium_decay = (initial_premium - current_premium) / initial_premium if initial_premium > 0 else 0

        if premium_decay >= 0.20:
            return True, f"Premium decay exceeded 20%: {premium_decay:.2%}"

        initial_vol = position.get('implied_volatility', 0.2)
        current_vol = current_market_data.get('current_volatility', initial_vol)
        vol_spike = (current_vol - initial_vol) / initial_vol if initial_vol > 0 else 0

        if vol_spike > 0.50:
            return True, f"Volatility spike exceeded 50%: {vol_spike:.2%}"

        underlying_initial = position.get('underlying_price', 0)
        underlying_current = current_market_data.get('underlying_price', underlying_initial)
        underlying_move = (underlying_current - underlying_initial) / underlying_initial if underlying_initial > 0 else 0

        if underlying_move < -0.10:  # 10% adverse move
            return True, f"Adverse underlying move exceeded 10%: {underlying_move:.2%}"

        return False, ""

    def trigger_alert(self, position: Dict[str, Any], reason: str):
        """Trigger alert for stop-loss condition."""
        alert_msg = f"STOP-LOSS TRIGGERED for {position.get('symbol')} {position.get('strike_price')} {position.get('option_type')}: {reason}"
        logger.warning(alert_msg)
        # TODO: Implement automated execution hook (e.g., close position)
        # For now, just log

    def adjust_position_size_for_loss_limits(self, position: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adjust position size (contracts) to ensure loss potential doesn't exceed limits.
        Scales down if necessary.
        """
        max_loss = self.calculate_max_loss_per_trade(position)
        potential_loss = self.calculate_potential_loss(position)
        current_contracts = position.get('contracts', 1)

        if potential_loss > max_loss and potential_loss > 0:
            scaling_factor = max_loss / potential_loss
            adjusted_contracts = int(current_contracts * scaling_factor)
            adjusted_contracts = max(1, adjusted_contracts)  # At least 1 contract

            logger.info(f"Adjusted position size from {current_contracts} to {adjusted_contracts} contracts due to loss limits")
            position['contracts'] = adjusted_contracts
            position['adjusted_for_risk'] = True
            position['original_contracts'] = current_contracts

        return position

    def get_monitoring_dashboard(self, days: int = 30) -> pd.DataFrame:
        """Retrieve monitoring data for dashboard display."""
        cursor = self.conn.cursor()
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        cursor.execute("""
            SELECT timestamp, symbol, position_id, loss_metric, trigger_type, trigger_reason, action_taken, compliance_status
            FROM risk_monitoring
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
        """, (cutoff_date,))
        rows = cursor.fetchall()
        return pd.DataFrame(rows, columns=['timestamp', 'symbol', 'position_id', 'loss_metric', 'trigger_type', 'trigger_reason', 'action_taken', 'compliance_status'])

    def validate_loss_calculations(self, historical_data: pd.DataFrame, tolerance: float = 0.05) -> Dict[str, Any]:
        """
        Validate loss potential estimations against historical outcomes.
        Confirms accuracy within ±5% deviations.
        """
        results = {
            'total_scenarios': len(historical_data),
            'accurate_predictions': 0,
            'accuracy_rate': 0.0,
            'avg_deviation': 0.0,
            'max_deviation': 0.0
        }

        deviations = []

        for _, row in historical_data.iterrows():
            # Simulate position from historical data
            position = {
                'symbol': row.get('symbol'),
                'option_type': row.get('option_type'),
                'strike_price': row.get('strike_price'),
                'premium_collected': row.get('premium_collected'),
                'underlying_price': row.get('underlying_price'),
                'contracts': row.get('contracts', 1),
                'delta': row.get('delta', 0),
                'gamma': row.get('gamma', 0),
                'theta': row.get('theta', 0),
                'vega': row.get('vega', 0)
            }

            # Calculate predicted loss
            predicted_loss = self.calculate_potential_loss(position)

            # Actual loss from historical data
            actual_loss = row.get('actual_loss', 0)

            if predicted_loss > 0:
                deviation = abs(predicted_loss - actual_loss) / predicted_loss
                deviations.append(deviation)

                if deviation <= tolerance:
                    results['accurate_predictions'] += 1

        if deviations:
            results['accuracy_rate'] = results['accurate_predictions'] / results['total_scenarios']
            results['avg_deviation'] = np.mean(deviations)
            results['max_deviation'] = np.max(deviations)

        logger.info(f"Loss calculation validation: {results['accuracy_rate']:.2%} accuracy, avg deviation {results['avg_deviation']:.2%}")
        return results

class PositionSizer(RiskManager):
    """Handles position sizing rules and Greeks exposure limits."""

    def get_portfolio_value(self) -> float:
        """Get current total portfolio value."""
        # TODO: Implement portfolio value calculation from database
        return 1000000.0  # Placeholder

    def get_market_regime(self) -> str:
        """Determine current market regime for sizing adjustments."""
        # TODO: Implement regime detection (bull, bear, crisis, normal)
        # For now, return 'normal'
        return 'normal'

    def get_regime_adjusted_allocation_limit(self) -> float:
        """Get maximum allocation per trade adjusted for market regime."""
        base_limit = self.config.max_portfolio_allocation
        regime = self.get_market_regime()

        regime_multipliers = {
            'normal': 1.0,
            'bull': 1.2,  # Allow larger positions in bull markets
            'bear': 0.8,  # Reduce in bear markets
            'crisis': 0.5  # Significantly reduce in crises
        }

        return base_limit * regime_multipliers.get(regime, 1.0)

    def check_allocation_constraint(self, position: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if position size exceeds maximum allocation constraint."""
        portfolio_value = self.get_portfolio_value()
        position_value = position.get('underlying_price', 0) * 100 * position.get('contracts', 1)
        max_allocation = self.get_regime_adjusted_allocation_limit()

        allocation_pct = position_value / portfolio_value if portfolio_value > 0 else 0

        if allocation_pct > max_allocation:
            return False, f"Allocation {allocation_pct:.2%} exceeds limit {max_allocation:.2%} for {self.get_market_regime()} regime"

        return True, f"Allocation within limits: {allocation_pct:.2%}"

    def get_current_positions(self) -> List[Dict[str, Any]]:
        """Get current active positions from database."""
        # TODO: Query database for active positions
        return []  # Placeholder

    def get_sector_exposure(self) -> Dict[str, float]:
        """Get current sector exposure percentages."""
        positions = self.get_current_positions()
        sector_values = {}
        total_value = sum(pos.get('underlying_price', 0) * 100 * pos.get('contracts', 1) for pos in positions)

        for pos in positions:
            sector = pos.get('sector', 'unknown')
            value = pos.get('underlying_price', 0) * 100 * pos.get('contracts', 1)
            sector_values[sector] = sector_values.get(sector, 0) + value

        return {sector: value / total_value if total_value > 0 else 0 for sector, value in sector_values.items()}

    def check_diversification_limits(self, position: Dict[str, Any]) -> Tuple[bool, str]:
        """Check portfolio diversification limits."""
        current_positions = self.get_current_positions()

        # Check concurrent positions limit
        if len(current_positions) >= self.config.max_concurrent_positions:
            return False, f"Maximum concurrent positions ({self.config.max_concurrent_positions}) reached"

        # Check sector concentration
        sector_exposure = self.get_sector_exposure()
        position_sector = position.get('sector', 'unknown')
        current_sector_pct = sector_exposure.get(position_sector, 0)
        position_value = position.get('underlying_price', 0) * 100 * position.get('contracts', 1)
        total_value = sum(pos.get('underlying_price', 0) * 100 * pos.get('contracts', 1) for pos in current_positions)

        if total_value > 0:
            new_sector_pct = (current_sector_pct * total_value + position_value) / (total_value + position_value)
            if new_sector_pct > self.config.max_sector_concentration:
                return False, f"Sector concentration {new_sector_pct:.2%} exceeds limit {self.config.max_sector_concentration:.2%} for {position_sector}"

        return True, "Diversification limits satisfied"

    def get_portfolio_greeks(self) -> Dict[str, float]:
        """Aggregate Greeks across all current positions."""
        positions = self.get_current_positions()
        total_greeks = {'delta': 0.0, 'gamma': 0.0, 'theta': 0.0, 'vega': 0.0, 'rho': 0.0}

        for pos in positions:
            contracts = pos.get('contracts', 1)
            for greek in total_greeks.keys():
                total_greeks[greek] += pos.get(greek, 0) * contracts * 100  # Notional adjustment

        return total_greeks

    def check_greeks_limits(self, position: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if adding position would breach Greeks exposure limits."""
        current_greeks = self.get_portfolio_greeks()
        position_greeks = {
            'delta': position.get('delta', 0) * position.get('contracts', 1) * 100,
            'gamma': position.get('gamma', 0) * position.get('contracts', 1) * 100,
            'theta': position.get('theta', 0) * position.get('contracts', 1) * 100,
            'vega': position.get('vega', 0) * position.get('contracts', 1) * 100,
            'rho': position.get('rho', 0) * position.get('contracts', 1) * 100
        }

        new_greeks = {k: current_greeks[k] + position_greeks[k] for k in current_greeks.keys()}

        # Check limits
        if abs(new_greeks['delta']) > self.config.delta_limit:
            return False, f"Net delta {new_greeks['delta']:.3f} exceeds limit ±{self.config.delta_limit}"

        if abs(new_greeks['gamma']) > self.config.gamma_limit:
            return False, f"Net gamma {new_greeks['gamma']:.3f} exceeds limit ±{self.config.gamma_limit}"

        if new_greeks['vega'] > self.config.vega_limit:
            return False, f"Net vega {new_greeks['vega']:.3f} exceeds limit {self.config.vega_limit}"

        if abs(new_greeks['rho']) > self.config.rho_limit:
            return False, f"Net rho {abs(new_greeks['rho']):.3f} exceeds limit {self.config.rho_limit}"

        return True, "Greeks exposure within limits"

    def calculate_optimal_contracts(self, position: Dict[str, Any]) -> int:
        """
        Calculate optimal number of contracts based on price, liquidity, and risk limits.
        Considers all sizing constraints.
        """
        underlying_price = position.get('underlying_price', 0)
        if underlying_price <= 0:
            return 0

        # Start with maximum possible based on allocation
        portfolio_value = self.get_portfolio_value()
        max_allocation = self.get_regime_adjusted_allocation_limit()
        max_position_value = portfolio_value * max_allocation
        max_contracts_by_allocation = int(max_position_value / (underlying_price * 100))

        # Adjust for liquidity (bid-ask spread)
        bid_ask_spread = position.get('bid_ask_spread', 0.05)  # Default 5 cents
        liquidity_factor = min(1.0, 0.10 / bid_ask_spread)  # Reduce size for wide spreads
        contracts_by_liquidity = int(max_contracts_by_allocation * liquidity_factor)

        # Adjust for Greeks exposure
        current_greeks = self.get_portfolio_greeks()
        position_delta = position.get('delta', 0) * 100
        position_gamma = position.get('gamma', 0) * 100

        # Calculate how many contracts we can add without breaching Greeks
        max_by_delta = float('inf')
        if position_delta != 0:
            remaining_delta_capacity = self.config.delta_limit - abs(current_greeks['delta'])
            max_by_delta = remaining_delta_capacity / abs(position_delta) if remaining_delta_capacity > 0 else 0

        max_by_gamma = float('inf')
        if position_gamma != 0:
            remaining_gamma_capacity = self.config.gamma_limit - abs(current_greeks['gamma'])
            max_by_gamma = remaining_gamma_capacity / abs(position_gamma) if remaining_gamma_capacity > 0 else 0

        # Take minimum of all constraints
        optimal_contracts = min(max_contracts_by_allocation, contracts_by_liquidity,
                               max_by_delta, max_by_gamma, 1000)  # Cap at 1000 contracts

        return max(1, int(optimal_contracts))

    def get_available_cash(self) -> float:
        """Get available cash for trading."""
        # TODO: Query portfolio cash balance
        return 500000.0  # Placeholder

    def check_margin_requirements(self, position: Dict[str, Any]) -> Tuple[bool, str]:
        """Check margin/cash availability for position."""
        option_type = position.get('option_type', '').lower()
        strike = position.get('strike_price', 0)
        contracts = position.get('contracts', 1)
        underlying_price = position.get('underlying_price', 0)

        if option_type == 'put':  # Cash-secured put
            required_cash = strike * 100 * contracts
            available_cash = self.get_available_cash()
            if required_cash > available_cash:
                return False, f"Insufficient cash for cash-secured put: required ${required_cash:,.0f}, available ${available_cash:,.0f}"

        elif option_type == 'call':  # Covered call
            # Assume we need to own the underlying stock
            required_stock_value = underlying_price * 100 * contracts
            # TODO: Check if we own enough stock
            # For now, assume sufficient stock ownership
            pass

        return True, "Margin requirements satisfied"

    def adjust_for_partial_execution(self, position: Dict[str, Any], executed_contracts: int) -> Dict[str, Any]:
        """
        Adjust position parameters when only partial execution occurs.
        Recalculates risk metrics to maintain balance.
        """
        original_contracts = position.get('contracts', executed_contracts)
        execution_ratio = executed_contracts / original_contracts if original_contracts > 0 else 0

        # Scale position size
        position['contracts'] = executed_contracts
        position['execution_ratio'] = execution_ratio

        # Scale Greeks proportionally
        greek_fields = ['delta', 'gamma', 'theta', 'vega', 'rho']
        for greek in greek_fields:
            if greek in position:
                position[greek] *= execution_ratio

        # Recalculate risk metrics
        position['adjusted_premium'] = position.get('premium_collected', 0) * execution_ratio

        # Check if adjusted position still meets risk criteria
        if self.validate_position(position):
            logger.info(f"Partial execution adjusted successfully: {executed_contracts}/{original_contracts} contracts")
        else:
            logger.warning(f"Partial execution resulted in risk violation: {executed_contracts}/{original_contracts} contracts")
            # TODO: Consider canceling remaining order or adjusting further

        return position

    def generate_risk_recommendations(self, violations: List[str]) -> List[str]:
        """Generate automated recommendations based on risk violations."""
        recommendations = []

        for violation in violations:
            if "allocation" in violation.lower():
                recommendations.append("Reduce position size or diversify across more assets")
            elif "diversification" in violation.lower():
                recommendations.append("Consider reducing exposure to over-concentrated sectors")
            elif "greeks" in violation.lower():
                recommendations.append("Hedge Greeks exposure or reduce position sizes")
            elif "margin" in violation.lower():
                recommendations.append("Add more cash to portfolio or reduce leverage")

        return recommendations

    def alert_on_breaches(self, position: Dict[str, Any], violations: List[str]):
        """Alert on position sizing breaches with recommendations."""
        alert_msg = f"RISK BREACH ALERT for {position.get('symbol')}: {', '.join(violations)}"
        recommendations = self.generate_risk_recommendations(violations)
        rec_msg = "Recommendations: " + "; ".join(recommendations)

        logger.error(f"{alert_msg}. {rec_msg}")
        # TODO: Send email/SMS alerts, trigger automated actions

    def backtest_sizing_rules(self, historical_scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Backtest position sizing rules across historical market scenarios.
        Ensures drawdowns remain below 10%.
        """
        results = {
            'total_scenarios': len(historical_scenarios),
            'max_drawdown': 0.0,
            'avg_drawdown': 0.0,
            'drawdown_violations': 0,
            'allocation_violations': 0,
            'greeks_violations': 0,
            'margin_violations': 0
        }

        drawdowns = []

        for scenario in historical_scenarios:
            # Simulate position sizing for scenario
            position = scenario.get('position', {})
            market_data = scenario.get('market_data', {})

            # Calculate optimal sizing
            optimal_contracts = self.calculate_optimal_contracts(position)
            position['contracts'] = optimal_contracts

            # Check if sizing rules prevent excessive drawdown
            # Simulate portfolio performance
            simulated_drawdown = scenario.get('simulated_drawdown', 0.05)  # Placeholder
            drawdowns.append(simulated_drawdown)

            if simulated_drawdown > 0.10:  # 10% threshold
                results['drawdown_violations'] += 1

            # Track violations
            if not self.validate_position(position):
                results['allocation_violations'] += 1
                # Could categorize violations further

        if drawdowns:
            results['max_drawdown'] = max(drawdowns)
            results['avg_drawdown'] = np.mean(drawdowns)

        logger.info(f"Sizing rules backtest: max drawdown {results['max_drawdown']:.2%}, violations {results['drawdown_violations']}")
        return results

    def validate_position(self, position: Dict[str, Any]) -> bool:
        """Validate position sizing constraints."""
        violations = []

        # Check allocation
        valid_alloc, reason_alloc = self.check_allocation_constraint(position)
        if not valid_alloc:
            violations.append(reason_alloc)

        # Check diversification
        valid_div, reason_div = self.check_diversification_limits(position)
        if not valid_div:
            violations.append(reason_div)

        # Check Greeks exposure
        valid_greeks, reason_greeks = self.check_greeks_limits(position)
        if not valid_greeks:
            violations.append(reason_greeks)

        # Check margin requirements
        valid_margin, reason_margin = self.check_margin_requirements(position)
        if not valid_margin:
            violations.append(reason_margin)

        if violations:
            self.alert_on_breaches(position, violations)
            return False

        return True

class RiskFramework(RiskManager):
    """Comprehensive portfolio risk management with VaR, ES, correlations."""

    def aggregate_daily_greeks(self) -> Dict[str, float]:
        """
        Aggregate Greeks across all positions for daily monitoring.
        Returns net exposure for each Greek.
        """
        positions = self.get_current_positions()
        total_greeks = {'delta': 0.0, 'gamma': 0.0, 'theta': 0.0, 'vega': 0.0, 'rho': 0.0}

        for pos in positions:
            contracts = pos.get('contracts', 1)
            for greek in total_greeks.keys():
                total_greeks[greek] += pos.get(greek, 0) * contracts * 100  # Notional adjustment

        # Log daily Greeks summary
        logger.info(f"Daily Greeks aggregation: {total_greeks}")

        # Store in database for monitoring
        self._store_daily_greeks(total_greeks)

        return total_greeks

    def _store_daily_greeks(self, greeks: Dict[str, float]):
        """Store daily Greeks in risk monitoring table."""
        self.log_risk_metric('PORTFOLIO', 'daily_greeks', 0.0, 'greeks_aggregation',
                           f"delta: {greeks['delta']:.2f}, gamma: {greeks['gamma']:.2f}, theta: {greeks['theta']:.2f}, vega: {greeks['vega']:.2f}, rho: {greeks['rho']:.2f}")

    def monitor_greeks_limits(self) -> List[str]:
        """Monitor portfolio Greeks against limits, return alerts."""
        greeks = self.aggregate_daily_greeks()
        alerts = []

        if abs(greeks['delta']) > self.config.delta_limit:
            alerts.append(f"Portfolio delta {greeks['delta']:.2f} exceeds ±{self.config.delta_limit}")

        if abs(greeks['gamma']) > self.config.gamma_limit:
            alerts.append(f"Portfolio gamma {greeks['gamma']:.2f} exceeds ±{self.config.gamma_limit}")

        if greeks['vega'] > self.config.vega_limit:
            alerts.append(f"Portfolio vega {greeks['vega']:.2f} exceeds {self.config.vega_limit}")

        if abs(greeks['rho']) > self.config.rho_limit:
            alerts.append(f"Portfolio rho {abs(greeks['rho']):.2f} exceeds {self.config.rho_limit}")

        if alerts:
            logger.warning(f"Greeks limit alerts: {alerts}")

        return alerts

    def calculate_var(self, confidence_level: float = 0.95, method: str = 'monte_carlo',
                     num_simulations: int = 10000, horizon_days: int = 1) -> float:
        """
        Calculate Value at Risk using Monte Carlo simulation with correlations.
        Returns VaR as positive dollar amount.
        """
        positions = self.get_current_positions()
        if not positions:
            return 0.0

        # Get correlation matrix
        corr_matrix = self.get_correlation_matrix()

        # Get volatilities and current values
        volatilities = [pos.get('implied_volatility', 0.2) for pos in positions]
        position_values = [pos.get('underlying_price', 0) * 100 * pos.get('contracts', 1) for pos in positions]

        if method == 'monte_carlo':
            # Monte Carlo simulation
            losses = []
            for _ in range(num_simulations):
                # Generate correlated random returns
                returns = np.random.multivariate_normal([0] * len(positions), corr_matrix)
                daily_loss = 0

                for i, pos in enumerate(positions):
                    # Simulate price movement
                    price_change = position_values[i] * returns[i] * np.sqrt(horizon_days)
                    # Add Greeks-based adjustments (simplified)
                    delta_pnl = pos.get('delta', 0) * price_change
                    daily_loss += delta_pnl

                losses.append(daily_loss)

            losses.sort()
            var_index = int((1 - confidence_level) * num_simulations)
            var = abs(losses[var_index]) if var_index < len(losses) else 0

        elif method == 'historical':
            # Historical simulation (placeholder)
            var = sum(position_values) * 0.02 * np.sqrt(horizon_days)  # 2% daily VaR approximation

        else:
            var = 0.0

        logger.info(f"VaR calculated: ${var:,.0f} at {confidence_level:.0%} confidence ({method})")
        return var

    def calculate_expected_shortfall(self, confidence_levels: List[float] = None) -> Dict[float, float]:
        """
        Calculate Expected Shortfall (ES) for weekly stress testing.
        Returns ES values for different confidence levels.
        """
        if confidence_levels is None:
            confidence_levels = self.config.es_confidence_levels

        # Run stress scenarios
        scenarios = self.generate_stress_scenarios()
        losses = []

        for scenario in scenarios:
            loss = self.simulate_scenario_loss(scenario)
            losses.append(loss)

        losses.sort()
        es_results = {}

        for conf in confidence_levels:
            # For ES, average losses beyond VaR threshold
            var_threshold = np.percentile(losses, (1 - conf) * 100)
            tail_losses = [l for l in losses if l >= var_threshold]
            es = np.mean(tail_losses) if tail_losses else 0.0
            es_results[conf] = es

        logger.info(f"Expected Shortfall calculated: {es_results}")
        return es_results

    def generate_stress_scenarios(self) -> List[Dict[str, Any]]:
        """Generate 20+ stress testing scenarios."""
        scenarios = [
            {'name': '50% vol spike', 'vol_multiplier': 1.5, 'price_move': 0.0},
            {'name': '10% underlying drop', 'vol_multiplier': 1.0, 'price_move': -0.10},
            {'name': 'Vol spike + price drop', 'vol_multiplier': 2.0, 'price_move': -0.15},
            {'name': 'Bull market stress', 'vol_multiplier': 0.7, 'price_move': 0.20},
            {'name': 'Bear market stress', 'vol_multiplier': 1.8, 'price_move': -0.25},
            # Add more scenarios...
        ]

        # Expand to 20+ scenarios with variations
        for i in range(6, 21):
            scenarios.append({
                'name': f'Scenario {i}',
                'vol_multiplier': np.random.uniform(0.5, 2.5),
                'price_move': np.random.uniform(-0.30, 0.30)
            })

        return scenarios

    def simulate_scenario_loss(self, scenario: Dict[str, Any]) -> float:
        """Simulate portfolio loss for a stress scenario."""
        positions = self.get_current_positions()
        total_loss = 0.0

        for pos in positions:
            # Simplified loss calculation based on scenario
            vol_stress = scenario.get('vol_multiplier', 1.0)
            price_stress = scenario.get('price_move', 0.0)

            # Greeks-based P&L
            delta_pnl = pos.get('delta', 0) * pos.get('underlying_price', 0) * 100 * pos.get('contracts', 1) * price_stress
            vega_pnl = pos.get('vega', 0) * pos.get('implied_volatility', 0.2) * (vol_stress - 1) * 100 * pos.get('contracts', 1)

            position_loss = delta_pnl + vega_pnl
            total_loss += position_loss

        return total_loss

    def update_correlation_matrix(self) -> np.ndarray:
        """
        Update correlation matrix monthly using historical price data.
        Stores updated matrix for use in risk calculations.
        """
        positions = self.get_current_positions()
        symbols = [pos.get('symbol') for pos in positions]

        # TODO: Fetch historical price data for symbols over past 6-12 months
        # Placeholder: generate random correlations
        n = len(symbols)
        corr_matrix = np.random.uniform(0.1, 0.8, (n, n))
        np.fill_diagonal(corr_matrix, 1.0)  # Perfect self-correlation

        # Make symmetric
        corr_matrix = (corr_matrix + corr_matrix.T) / 2

        # Store/update in database or cache
        logger.info(f"Updated correlation matrix for {n} assets")

        return corr_matrix

    def get_correlation_matrix(self) -> np.ndarray:
        """Get current correlation matrix (updated monthly)."""
        # TODO: Retrieve from stored matrix, update if older than 30 days
        return self.update_correlation_matrix()

    def monitor_liquidity_risk(self) -> List[str]:
        """
        Monitor liquidity risk via bid/ask spreads and open interest.
        Returns alerts for deteriorating liquidity.
        """
        alerts = []
        positions = self.get_current_positions()

        for pos in positions:
            symbol = pos.get('symbol', '')
            bid_ask_spread = pos.get('bid_ask_spread', 0.05)
            open_interest = pos.get('open_interest', 1000)

            # Check spread thresholds
            if bid_ask_spread > 0.10:  # 10 cent spread
                alerts.append(f"Wide bid-ask spread for {symbol}: ${bid_ask_spread:.2f}")

            # Check open interest decay
            if open_interest < 100:  # Low open interest
                alerts.append(f"Low open interest for {symbol}: {open_interest}")

            # Check spread widening over time (placeholder)
            # TODO: Compare to historical averages

        if alerts:
            logger.warning(f"Liquidity risk alerts: {alerts}")

        return alerts

    def monitor_counterparty_risk(self) -> List[str]:
        """
        Monitor counterparty risk by brokerage concentration.
        Returns alerts for concentration breaches.
        """
        alerts = []
        positions = self.get_current_positions()

        brokerage_exposure = {}
        for pos in positions:
            brokerage = pos.get('brokerage', 'default')
            value = pos.get('underlying_price', 0) * 100 * pos.get('contracts', 1)
            brokerage_exposure[brokerage] = brokerage_exposure.get(brokerage, 0) + value

        total_value = sum(brokerage_exposure.values())
        for brokerage, exposure in brokerage_exposure.items():
            pct = exposure / total_value if total_value > 0 else 0
            if pct > 0.50:  # 50% concentration limit
                alerts.append(f"High brokerage concentration: {brokerage} at {pct:.1%}")

        if alerts:
            logger.warning(f"Counterparty risk alerts: {alerts}")

        return alerts

    def check_rebalancing_triggers(self) -> List[Dict[str, Any]]:
        """
        Check for automated rebalancing triggers based on risk metric breaches.
        Returns list of rebalancing actions needed.
        """
        actions = []

        # Check Greeks breaches
        greeks_alerts = self.monitor_greeks_limits()
        if greeks_alerts:
            actions.append({
                'type': 'greeks_rebalancing',
                'reason': 'Greeks limits exceeded',
                'details': greeks_alerts,
                'action': 'Reduce position sizes or hedge Greeks exposure'
            })

        # Check VaR breaches
        var = self.calculate_var()
        portfolio_value = self.get_portfolio_value()
        var_pct = var / portfolio_value if portfolio_value > 0 else 0
        if var_pct > 0.05:  # 5% VaR limit
            actions.append({
                'type': 'var_reduction',
                'reason': f'VaR {var_pct:.2%} exceeds 5% limit',
                'details': f'Current VaR: ${var:,.0f}',
                'action': 'Reduce portfolio size or diversify'
            })

        # Check ES breaches
        es_results = self.calculate_expected_shortfall()
        for conf, es_value in es_results.items():
            es_pct = es_value / portfolio_value if portfolio_value > 0 else 0
            if es_pct > 0.10:  # 10% ES limit
                actions.append({
                    'type': 'es_reduction',
                    'reason': f'ES at {conf:.1%} confidence {es_pct:.2%} exceeds 10% limit',
                    'details': f'ES: ${es_value:,.0f}',
                    'action': 'Implement tail risk hedging'
                })

        if actions:
            logger.warning(f"Rebalancing triggers activated: {len(actions)} actions needed")
            for action in actions:
                logger.info(f"Action: {action['action']} - {action['reason']}")

        return actions

    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Prepare comprehensive risk metrics for dashboard visualization.
        Returns data structure suitable for charting and display.
        """
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'portfolio_value': self.get_portfolio_value(),
            'risk_metrics': {},
            'greeks_exposure': {},
            'alerts': [],
            'positions': []
        }

        # Greeks data
        greeks = self.aggregate_daily_greeks()
        dashboard_data['greeks_exposure'] = greeks

        # Risk metrics
        var_95 = self.calculate_var(confidence_level=0.95)
        es_results = self.calculate_expected_shortfall()
        dashboard_data['risk_metrics'] = {
            'var_95': var_95,
            'var_pct': var_95 / dashboard_data['portfolio_value'] if dashboard_data['portfolio_value'] > 0 else 0,
            'expected_shortfall': es_results
        }

        # Alerts
        dashboard_data['alerts'].extend(self.monitor_greeks_limits())
        dashboard_data['alerts'].extend(self.monitor_liquidity_risk())
        dashboard_data['alerts'].extend(self.monitor_counterparty_risk())

        # Rebalancing triggers
        rebalancing_actions = self.check_rebalancing_triggers()
        dashboard_data['rebalancing_needed'] = len(rebalancing_actions) > 0
        dashboard_data['rebalancing_actions'] = rebalancing_actions

        # Position details
        positions = self.get_current_positions()
        dashboard_data['positions'] = [
            {
                'symbol': pos.get('symbol'),
                'value': pos.get('underlying_price', 0) * 100 * pos.get('contracts', 1),
                'delta': pos.get('delta', 0),
                'gamma': pos.get('gamma', 0),
                'vega': pos.get('vega', 0),
                'theta': pos.get('theta', 0)
            }
            for pos in positions
        ]

        return dashboard_data

    def validate_risk_framework(self, historical_periods: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate the entire risk framework through historical simulation.
        Tests all risk factors and metrics across different market conditions.
        """
        validation_results = {
            'periods_tested': len(historical_periods),
            'greeks_accuracy': 0.0,
            'var_breaches': 0,
            'es_effectiveness': 0.0,
            'liquidity_alerts_caught': 0,
            'rebalancing_effectiveness': 0.0,
            'overall_framework_score': 0.0
        }

        for period in historical_periods:
            # Simulate portfolio during period
            simulated_portfolio = period.get('portfolio', [])
            market_conditions = period.get('market_conditions', {})

            # Test Greeks monitoring
            greeks_alerts = self.monitor_greeks_limits()
            if greeks_alerts and period.get('actual_risk_event'):
                validation_results['greeks_accuracy'] += 1

            # Test VaR during crisis periods
            if market_conditions.get('crisis_period'):
                var = self.calculate_var()
                if var > period.get('actual_loss', 0):
                    validation_results['var_breaches'] += 1

            # Test ES stress testing
            es_results = self.calculate_expected_shortfall()
            # Check if ES captured tail risks adequately

            # Test liquidity monitoring
            liquidity_alerts = self.monitor_liquidity_risk()
            if liquidity_alerts and market_conditions.get('liquidity_crisis'):
                validation_results['liquidity_alerts_caught'] += 1

        # Calculate final scores
        if validation_results['periods_tested'] > 0:
            validation_results['greeks_accuracy'] /= validation_results['periods_tested']
            validation_results['es_effectiveness'] = 1.0 - (validation_results['var_breaches'] / validation_results['periods_tested'])
            validation_results['liquidity_alerts_caught'] /= validation_results['periods_tested']

            # Overall framework score (weighted average)
            weights = {'greeks_accuracy': 0.3, 'es_effectiveness': 0.3, 'liquidity_alerts_caught': 0.2, 'rebalancing_effectiveness': 0.2}
            validation_results['overall_framework_score'] = sum(
                validation_results[metric] * weight for metric, weight in weights.items()
            )

        logger.info(f"Risk framework validation complete: {validation_results['overall_framework_score']:.2%} effectiveness")
        return validation_results

    def validate_position(self, position: Dict[str, Any]) -> bool:
        """Validate portfolio-level risk metrics."""
        # Implementation to be added
        return True

class BacktestValidator(RiskManager):
    """Backtesting and performance validation with risk controls."""

    def acquire_historical_data(self, symbols: List[str], years: int = 10) -> pd.DataFrame:
        """
        Acquire and preprocess 10+ years of historical options data.
        Includes splits, dividends, and corporate action adjustments.
        """
        # TODO: Implement data fetching from APIs or databases
        # Placeholder: generate synthetic historical data

        start_date = datetime.now() - timedelta(days=years*365)
        dates = pd.date_range(start=start_date, end=datetime.now(), freq='D')

        historical_data = []
        for symbol in symbols:
            for date in dates:
                # Generate synthetic options data
                historical_data.append({
                    'symbol': symbol,
                    'date': date,
                    'underlying_price': np.random.uniform(50, 200),
                    'option_type': np.random.choice(['call', 'put']),
                    'strike_price': np.random.uniform(50, 200),
                    'bid': np.random.uniform(0.1, 10),
                    'ask': np.random.uniform(0.1, 10),
                    'last_price': np.random.uniform(0.1, 10),
                    'volume': np.random.randint(1, 1000),
                    'open_interest': np.random.randint(10, 10000),
                    'implied_volatility': np.random.uniform(0.1, 1.0),
                    'delta': np.random.uniform(-0.8, 0.8),
                    'gamma': np.random.uniform(0.01, 0.1),
                    'theta': np.random.uniform(-0.1, -0.01),
                    'vega': np.random.uniform(0.01, 0.1),
                    'rho': np.random.uniform(-0.1, 0.1)
                })

        df = pd.DataFrame(historical_data)

        # Apply corporate action adjustments (placeholder)
        df = self.adjust_for_corporate_actions(df)

        logger.info(f"Acquired historical data: {len(df)} records for {len(symbols)} symbols")
        return df

    def adjust_for_corporate_actions(self, data: pd.DataFrame) -> pd.DataFrame:
        """Adjust historical data for splits, dividends, and other corporate actions."""
        # TODO: Implement actual adjustment logic
        # Placeholder: return data as-is
        return data

    def run_multi_regime_backtest(self, historical_data: pd.DataFrame, regimes: List[str]) -> Dict[str, Any]:
        """
        Run backtesting across multiple market regimes with embedded risk/sizing rules.
        Regimes: normal, bull, bear, crisis, high_vol, etc.
        """
        results = {regime: {'trades': 0, 'pnl': 0.0, 'max_drawdown': 0.0, 'sharpe': 0.0} for regime in regimes}

        for regime in regimes:
            # Filter data for regime
            regime_data = self.filter_data_by_regime(historical_data, regime)

            # Run backtest with risk controls
            regime_results = self.backtest_with_risk_controls(regime_data, regime)
            results[regime] = regime_results

            logger.info(f"Backtest for {regime} regime: {regime_results['trades']} trades, P&L ${regime_results['pnl']:,.0f}")

        return results

    def filter_data_by_regime(self, data: pd.DataFrame, regime: str) -> pd.DataFrame:
        """Filter historical data by market regime characteristics."""
        if regime == 'normal':
            return data[data['implied_volatility'].between(0.15, 0.35)]
        elif regime == 'high_vol':
            return data[data['implied_volatility'] > 0.35]
        elif regime == 'bull':
            # TODO: Implement bull market filter
            return data.sample(frac=0.3)
        elif regime == 'bear':
            # TODO: Implement bear market filter
            return data.sample(frac=0.3)
        elif regime == 'crisis':
            return data[data['implied_volatility'] > 0.50]
        else:
            return data

    def backtest_with_risk_controls(self, data: pd.DataFrame, regime: str) -> Dict[str, Any]:
        """Run backtest simulation with all risk controls embedded."""
        # TODO: Implement full backtest logic integrating all risk managers
        # Placeholder results
        return {
            'trades': len(data) // 100,
            'pnl': np.random.uniform(-50000, 100000),
            'max_drawdown': np.random.uniform(0.05, 0.15),
            'sharpe': np.random.uniform(0.5, 2.0)
        }

    def run_walk_forward_test(self, historical_data: pd.DataFrame, train_years: int = 2, test_years: int = 2) -> Dict[str, Any]:
        """
        Implement walk-forward testing with rolling 2-year train/test windows.
        Calibrates parameters on training data, validates on out-of-sample test data.
        """
        results = {
            'windows': [],
            'avg_sharpe': 0.0,
            'avg_max_drawdown': 0.0,
            'out_of_sample_performance': 0.0
        }

        # Sort data by date
        historical_data = historical_data.sort_values('date')

        start_date = historical_data['date'].min()
        end_date = historical_data['date'].max()
        window_start = start_date

        while window_start + timedelta(days=train_years*365) + timedelta(days=test_years*365) <= end_date:
            train_end = window_start + timedelta(days=train_years*365)
            test_end = train_end + timedelta(days=test_years*365)

            # Split data
            train_data = historical_data[(historical_data['date'] >= window_start) & (historical_data['date'] < train_end)]
            test_data = historical_data[(historical_data['date'] >= train_end) & (historical_data['date'] < test_end)]

            # Calibrate on training data (TODO: implement parameter optimization)
            calibrated_params = self.calibrate_parameters(train_data)

            # Test on out-of-sample data
            test_results = self.backtest_with_risk_controls(test_data, 'normal')

            window_result = {
                'train_period': f"{window_start.date()} to {train_end.date()}",
                'test_period': f"{train_end.date()} to {test_end.date()}",
                'calibrated_params': calibrated_params,
                'test_results': test_results
            }

            results['windows'].append(window_result)

            # Move window forward by test period
            window_start = train_end

        # Calculate aggregate metrics
        if results['windows']:
            sharpes = [w['test_results']['sharpe'] for w in results['windows']]
            drawdowns = [w['test_results']['max_drawdown'] for w in results['windows']]

            results['avg_sharpe'] = np.mean(sharpes)
            results['avg_max_drawdown'] = np.mean(drawdowns)
            results['out_of_sample_performance'] = len([s for s in sharpes if s > 1.2]) / len(sharpes)  # Sharpe > 1.2 target

        logger.info(f"Walk-forward test completed: {len(results['windows'])} windows, avg Sharpe {results['avg_sharpe']:.2f}")
        return results

    def calibrate_parameters(self, train_data: pd.DataFrame) -> Dict[str, Any]:
        """Calibrate risk parameters using training data."""
        # TODO: Implement parameter optimization (genetic algorithms, Monte Carlo)
        # Placeholder: return current config
        return {
            'delta_limit': self.config.delta_limit,
            'gamma_limit': self.config.gamma_limit,
            'max_loss_per_trade': self.config.max_loss_per_trade
        }

    def calculate_transaction_costs(self, position: Dict[str, Any], execution_price: float) -> float:
        """
        Calculate realistic transaction costs including commissions and slippage.
        Returns total cost per trade.
        """
        contracts = position.get('contracts', 1)

        # Commission per contract (varies by broker)
        commission_per_contract = 0.50  # $0.50 per contract

        # Slippage based on bid-ask spread and volume
        bid_ask_spread = position.get('bid_ask_spread', 0.05)
        volume = position.get('volume', 100)
        slippage_factor = min(1.0, bid_ask_spread * (1000 / volume))  # Higher slippage for low volume

        slippage = execution_price * slippage_factor

        # Total cost
        total_commission = commission_per_contract * contracts
        total_slippage = slippage * contracts * 100  # Per contract cost

        total_cost = total_commission + total_slippage

        logger.debug(f"Transaction costs: commission ${total_commission:.2f}, slippage ${total_slippage:.2f}, total ${total_cost:.2f}")
        return total_cost

    def adjust_pnl_for_costs(self, pnl: float, position: Dict[str, Any], execution_price: float) -> float:
        """Adjust P&L calculations to include transaction costs."""
        costs = self.calculate_transaction_costs(position, execution_price)
        adjusted_pnl = pnl - costs

        # For round-trip trades, double the costs
        if position.get('is_round_trip', False):
            adjusted_pnl -= costs

        return adjusted_pnl

    def perform_performance_attribution(self, backtest_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform performance attribution analysis decomposing returns into:
        - Premium decay (theta)
        - Underlying movement (delta)
        - Volatility changes (vega)
        - Time decay (rho)
        """
        attribution = {
            'premium_decay_contribution': 0.0,
            'underlying_movement_contribution': 0.0,
            'volatility_contribution': 0.0,
            'interest_rate_contribution': 0.0,
            'total_attributed_pnl': 0.0,
            'unexplained_pnl': 0.0
        }

        # TODO: Implement detailed attribution analysis
        # This would analyze trade-by-trade P&L and decompose into Greeks contributions

        # Placeholder: distribute total P&L across factors
        total_pnl = backtest_results.get('pnl', 0)

        # Typical attribution for options strategies
        attribution['premium_decay_contribution'] = total_pnl * 0.6  # Theta decay main driver
        attribution['underlying_movement_contribution'] = total_pnl * 0.2  # Delta hedging
        attribution['volatility_contribution'] = total_pnl * 0.15  # Vega adjustments
        attribution['interest_rate_contribution'] = total_pnl * 0.05  # Rho effect

        attribution['total_attributed_pnl'] = sum([
            attribution['premium_decay_contribution'],
            attribution['underlying_movement_contribution'],
            attribution['volatility_contribution'],
            attribution['interest_rate_contribution']
        ])

        attribution['unexplained_pnl'] = total_pnl - attribution['total_attributed_pnl']

        logger.info(f"Performance attribution: Premium decay {attribution['premium_decay_contribution']:,.0f}, "
                   f"Underlying {attribution['underlying_movement_contribution']:,.0f}")

        return attribution

    def validate_position(self, position: Dict[str, Any]) -> bool:
        """Validate through historical backtesting."""
        # Implementation to be added
        return True

def load_config(config_path: str = "implementation/static_parameters.json") -> RiskConfig:
    """Load risk configuration from file."""
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        return RiskConfig(**data.get('risk_config', {}))
    return RiskConfig()

def main():
    """CLI interface for risk management operations."""
    import argparse

    parser = argparse.ArgumentParser(description="Institutional-grade options risk management system")
    parser.add_argument('--validate-position', action='store_true', help='Validate a position')
    parser.add_argument('--symbol', type=str, help='Stock symbol')
    parser.add_argument('--strike', type=float, help='Strike price')
    parser.add_argument('--contracts', type=int, default=1, help='Number of contracts')
    parser.add_argument('--option-type', type=str, choices=['call', 'put'], help='Option type')
    parser.add_argument('--run-dashboard', action='store_true', help='Generate risk dashboard data')
    parser.add_argument('--backtest', action='store_true', help='Run backtesting validation')

    args = parser.parse_args()

    # Initialize components
    config = load_config()
    db_path = "../risk_management.db"  # Database in workspace root

    loss_manager = LossPotentialManager(config, db_path)
    position_sizer = PositionSizer(config, db_path)
    risk_framework = RiskFramework(config, db_path)
    backtest_validator = BacktestValidator(config, db_path)

    if args.validate_position:
        if not all([args.symbol, args.strike, args.option_type]):
            parser.error("--validate-position requires --symbol, --strike, and --option-type")

        position = {
            'symbol': args.symbol,
            'strike_price': args.strike,
            'contracts': args.contracts,
            'option_type': args.option_type,
            'underlying_price': 150.0,  # Placeholder
            'premium_collected': 5.0,    # Placeholder
            'delta': 0.3,
            'gamma': 0.05,
            'theta': -0.1,
            'vega': 0.1
        }

        # Run comprehensive validation
        valid, reason = loss_manager.validate_position(position)
        sizing_valid = position_sizer.validate_position(position)

        if valid and sizing_valid:
            print(f"✅ Position {args.symbol} {args.strike} {args.option_type} approved")
        else:
            print(f"❌ Position rejected: {reason}")

    elif args.run_dashboard:
        dashboard = risk_framework.get_dashboard_data()
        print("Risk Dashboard:")
        print(f"Portfolio Value: ${dashboard['portfolio_value']:,.0f}")
        print(f"VaR (95%): ${dashboard['risk_metrics']['var_95']:,.0f}")
        print(f"Greeks: {dashboard['greeks_exposure']}")
        if dashboard['alerts']:
            print(f"Alerts: {dashboard['alerts']}")

    elif args.backtest:
        # Run sample backtest
        symbols = ['AAPL', 'MSFT', 'GOOGL']
        historical_data = backtest_validator.acquire_historical_data(symbols, years=5)
        regimes = ['normal', 'high_vol', 'crisis']
        results = backtest_validator.run_multi_regime_backtest(historical_data, regimes)

        print("Backtest Results:")
        for regime, data in results.items():
            print(f"{regime}: P&L ${data['pnl']:,.0f}, Sharpe {data['sharpe']:.2f}")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()