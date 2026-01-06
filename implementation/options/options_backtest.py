# options_backtest.py
import sqlite3
import logging
from datetime import datetime, date, timedelta
import random
from typing import List, Dict, Any
import argparse
from yfinance_options import GreekCalculator, OptionContract  # Import from existing file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptionsBacktester:
    def __init__(
        self,
        ticker: str,
        greek_calculator: GreekCalculator,
        simulated_table: str = "simulated_options"
    ):
        self.ticker = ticker
        self.db_path = f"{ticker}_options.db"
        self.greek_calculator = greek_calculator
        self.simulated_table = simulated_table
        self.conn = sqlite3.connect(self.db_path)
        self._init_simulated_table()
        self.active_positions: List[Dict[str, Any]] = []  # Track active simulated trades

    def _init_simulated_table(self):
        """Create simulated options table if it does not exist."""
        cursor = self.conn.cursor()
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.simulated_table} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                expiration_date TEXT,
                strike_price REAL,
                option_type TEXT,
                simulated_date TEXT,
                underlying_price REAL,
                implied_volatility REAL,
                days_to_expiration INTEGER,
                delta REAL,
                gamma REAL,
                theta REAL,
                vega REAL,
                rho REAL,
                premium_collected REAL,
                status TEXT,  -- 'active', 'assigned', 'expired', 'closed'
                realized_gains REAL,
                actual_delta REAL,
                delta_error REAL,
                actual_implied_vol REAL,
                vol_error REAL
            )
            """
        )
        self.conn.commit()
        logger.info(f"Initialized simulated options table '{self.simulated_table}' in DB.")

    def simulate_market_data(self, base_price: float, base_vol: float) -> Dict[str, float]:
        """Simulate underlying price and implied volatility for a backtest step."""
        # Simulate price as random walk (normal increment)
        price_change_pct = random.normalvariate(0, 0.02)  # 2% daily std dev
        simulated_price = base_price * (1 + price_change_pct)
        # Simulate vol as mean reverting process around base_vol
        vol_change = random.normalvariate(0, 0.05)
        simulated_vol = max(0.05, min(1.0, base_vol + vol_change))  # Keep vol between 5% and 100%
        return {
            "underlying_price": simulated_price,
            "implied_volatility": simulated_vol,
        }

    def days_to_expiration(self, current_date: date, expiration_date: date) -> int:
        delta = expiration_date - current_date
        return max(delta.days, 0)

    def recalc_greeks(self, contract: OptionContract, underlying_price: float, implied_volatility: float, current_date: date) -> Dict[str, float]:
        """Recalculate Greeks using binomial tree with simulated parameters."""
        T = self.days_to_expiration(current_date, contract.expiration_date) / 365.0
        if T == 0:
            # Expired, no Greeks
            return {"delta": 0, "gamma": 0, "theta": 0, "vega": 0, "rho": 0}
        try:
            greeks = self.greek_calculator.calculate_greeks(
                S=underlying_price,
                K=contract.strike_price,
                T=T,
                sigma=implied_volatility,
                option_type=contract.option_type.lower()
            )
            return greeks
        except Exception as e:
            logger.warning(f"Failed Greek recalculation: {e}")
            return {"delta": 0, "gamma": 0, "theta": 0, "vega": 0, "rho": 0}

    def store_simulated_data(self, data: Dict[str, Any]):
        """Insert simulated data into the database."""
        cursor = self.conn.cursor()
        cursor.execute(
            f"""
            INSERT INTO {self.simulated_table} (
                symbol,
                expiration_date,
                strike_price,
                option_type,
                simulated_date,
                underlying_price,
                implied_volatility,
                days_to_expiration,
                delta,
                gamma,
                theta,
                vega,
                rho,
                premium_collected,
                status,
                realized_gains,
                actual_delta,
                delta_error,
                actual_implied_vol,
                vol_error
            ) VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? )
            """,
            (data['symbol'], data['expiration_date'], data['strike_price'], data['option_type'], data['simulated_date'], data['underlying_price'], data['implied_volatility'], data['days_to_expiration'], data['delta'], data['gamma'], data['theta'], data['vega'], data['rho'], data['premium_collected'], data['status'], data['realized_gains'], data['actual_delta'], data['delta_error'], data['actual_implied_vol'], data['vol_error']),
        )
        self.conn.commit()
        logger.info("Committed simulated data")

    def fetch_actual_data_for_date(self, contract: OptionContract, date: date) -> Dict[str, float]:
        """ Fetch actual underlying price and implied volatility from actual data tables for the contract and date to compare with simulation. """
        cursor = self.conn.cursor()
        try:
            # Example: Query actual option price & Greeks on date
            # Assume table 'options_history' contains actual data
            # Fetch actual delta and implied vol for this contract and closest date
            cursor.execute(
                """
                SELECT delta, implied_volatility, underlying_price FROM options_history
                WHERE symbol=? AND expiration_date=? AND strike_price=? AND option_type=?
                AND date(fetch_timestamp) = date(?)
                ORDER BY fetch_timestamp LIMIT 1
                """,
                (
                    contract.symbol,
                    contract.expiration_date.strftime("%Y-%m-%d"),
                    contract.strike_price,
                    contract.option_type,
                    date.strftime("%Y-%m-%d")
                )
            )
            row = cursor.fetchone()
            if row:
                return {
                    "actual_delta": row[0] or 0.0,
                    "actual_implied_vol": row[1] or 0.0,
                    "actual_underlying_price": row[2] or 0.0,
                }
            else:
                return {
                    "actual_delta": 0.0,
                    "actual_implied_vol": 0.0,
                    "actual_underlying_price": 0.0,
                }
        except Exception as e:
            logger.warning(f"Failed to fetch actual data for {contract} on {date}: {e}")
            return {
                "actual_delta": 0.0,
                "actual_implied_vol": 0.0,
                "actual_underlying_price": 0.0,
            }

    def compute_pnl_and_update_status(self, position: Dict[str, Any], current_price: float) -> Dict[str, Any]:
        """ Compute simulated trade P&L and update status. Parameters: position: dict tracking a trade with keys including 'premium_collected', 'strike_price', 'option_type', 'status', 'realized_gains', 'expiration_date' current_price: float current underlying price Returns: Updated position dict with P&L, status and gains updated. """
        status = position["status"]
        if status != "active":
            return position
        premium = position["premium_collected"]
        strike = position["strike_price"]
        opt_type = position["option_type"]
        expired = position["expiration_date"] <= position["simulated_date"]  # Compare dates
        # Determine if assignment or expiration
        if expired:
            # Option expired worthless or in the money
            if (opt_type == "call" and current_price > strike) or (opt_type == "put" and current_price < strike):
                # Assigned
                position["status"] = "assigned"
                intrinsic_value = max(0, (current_price - strike) if opt_type == "call" else (strike - current_price))
                position["realized_gains"] = premium - intrinsic_value
            else:
                # Expired worthless
                position["status"] = "expired"
                position["realized_gains"] = premium
        else:
            # Active: mark-to-market unrealized P&L (for tracking only)
            intrinsic = max(0, (current_price - strike) if opt_type == "call" else (strike - current_price))
            position["realized_gains"] = premium - intrinsic
        return position

    def run_backtest_step(self, current_date: date, base_underlying_price: float, base_iv: float):
        """ Runs a backtest step at current_date: 1) simulate market data 2) recalc Greeks 3) store simulation 4) update each active trade P&L/status 5) remove closed trades """
        logger.info(f"Backtest step on {current_date}")
        # Simulate market data
        simulated_data = self.simulate_market_data(base_underlying_price, base_iv)
        underlying_price = simulated_data["underlying_price"]
        implied_volatility = simulated_data["implied_volatility"]
        # Fetch all active options to simulate - for simplicity fetch all validated options once
        cursor = self.conn.cursor()
        cursor.execute(
            f"SELECT symbol, expiration_date, strike_price, option_type, premium_collected, status, realized_gains FROM {self.simulated_table} WHERE status='active'"
        )
        rows = cursor.fetchall()
        updated_positions = []
        for row in rows:
            symbol, exp_str, strike, opt_type, premium, status, gains = row
            expiration_date = date.fromisoformat(exp_str)
            days_to_exp = (expiration_date - current_date).days
            if days_to_exp < 0:
                days_to_exp = 0
            # Recalculate Greeks on simulated data
            greeks = self.greek_calculator.calculate_greeks(
                S=underlying_price,
                K=strike,
                T=days_to_exp / 365,
                sigma=implied_volatility,
                option_type=opt_type.lower()
            )
            # Update position dict
            pos = {
                "symbol": symbol,
                "expiration_date": expiration_date,
                "strike_price": strike,
                "option_type": opt_type,
                "simulated_date": current_date,
                "underlying_price": underlying_price,
                "implied_volatility": implied_volatility,
                "days_to_expiration": days_to_exp,
                "delta": greeks["delta"],
                "gamma": greeks["gamma"],
                "theta": greeks["theta"],
                "vega": greeks["vega"],
                "rho": greeks["rho"],
                "premium_collected": premium,
                "status": status,
                "realized_gains": gains,
            }
            # Fetch actual data for date and contract to calculate error
            actual_data = self.fetch_actual_data_for_date(
                OptionContract(
                    symbol=symbol,
                    expiration_date=expiration_date,
                    strike_price=strike,
                    option_type=opt_type,
                    bid=0,
                    ask=0,
                    last_price=0,
                    volume=0,
                    open_interest=0,
                    implied_volatility=implied_volatility,
                    change=0.0,
                    percent_change=0.0,
                    delta=0.0,
                    gamma=0.0,
                    theta=0.0,
                    vega=0.0,
                    rho=0.0,
                    prob_itm=0.0,
                    prob_otm=0.0,
                    prob_touch=0.0,
                    days_to_expiration=days_to_exp,
                    underlying_price=underlying_price,
                    validated=False
                ),
                current_date
            )
            pos["actual_delta"] = actual_data["actual_delta"]
            pos["actual_implied_vol"] = actual_data["actual_implied_vol"]
            pos["delta_error"] = abs(pos["delta"] - pos["actual_delta"])
            pos["vol_error"] = abs(pos["implied_volatility"] - pos["actual_implied_vol"])
            # Compute PnL and update status
            pos = self.compute_pnl_and_update_status(pos, underlying_price)
            # Store to DB
            self.store_simulated_data(pos)
            # Track active positions only if
            if pos["status"] == "active":
                updated_positions.append(pos)
        self.active_positions = updated_positions
        logger.info(f"Active positions remaining: {len(self.active_positions)}")

    def run_full_backtest(self, start_date: date, end_date: date, base_price: float, base_iv: float):
        """Run backtest from start_date to end_date (daily steps)."""
        current_date = start_date
        while current_date <= end_date:
            self.run_backtest_step(current_date, base_price, base_iv)
            current_date += timedelta(days=1)
        logger.info("Backtest complete.")

    def get_table_name(self, current_date: date) -> str:
        """Get the partitioned table name for the given date."""
        return f"options_{current_date.strftime('%Y_%m_%d')}"

    def sell_option_call(self, strike: float, expiration: str):
        """Sell a call option: create new simulated trade."""
        current_date = date.today()
        expiration_date = date.fromisoformat(expiration)
        table_name = f"options_{expiration.replace('-', '_')}"
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT last_price, delta, gamma, theta, vega, rho, underlying_price, implied_volatility
            FROM {table_name}
            WHERE symbol=? AND expiration_date LIKE ? AND strike_price=? AND option_type='call'
            """, (self.ticker, expiration + '%', str(strike)))
        row = cursor.fetchone()
        if not row:
            logger.error(f"No data found for contract {self.ticker} {strike} {expiration} on {current_date}")
            return
        premium = float(row[0])
        delta = float(row[1])
        gamma = float(row[2])
        theta = float(row[3])
        vega = float(row[4])
        rho = float(row[5])
        underlying_price = float(row[6])
        implied_volatility = float(row[7])
        # Create position dict
        pos = {
            "symbol": self.ticker,
            "expiration_date": expiration_date.strftime("%Y-%m-%d"),
            "strike_price": strike,
            "option_type": "call",
            "simulated_date": current_date.strftime("%Y-%m-%d"),
            "underlying_price": underlying_price,
            "implied_volatility": implied_volatility,
            "days_to_expiration": self.days_to_expiration(current_date, expiration_date),
            "delta": delta,
            "gamma": gamma,
            "theta": theta,
            "vega": vega,
            "rho": rho,
            "premium_collected": premium,
            "status": "active",
            "realized_gains": 0.0,
            "actual_delta": 0.0,
            "delta_error": 0.0,
            "actual_implied_vol": 0.0,
            "vol_error": 0.0,
        }
        # Store
        self.store_simulated_data(pos)
        logger.info(f"Stored simulated data for strike {strike}")
        logger.info(f"Sold call: strike {strike}, exp {expiration}, premium {premium}")

    def sell_option_put(self, strike: float, expiration: str):
        """Sell a put option: create new simulated trade."""
        current_date = date.today()
        expiration_date = date.fromisoformat(expiration)
        table_name = f"options_{expiration.replace('-', '_')}"
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT last_price, delta, gamma, theta, vega, rho, underlying_price, implied_volatility
            FROM {table_name}
            WHERE symbol=? AND expiration_date LIKE ? AND strike_price=? AND option_type='put'
            """, (self.ticker, expiration + '%', str(strike)))
        row = cursor.fetchone()
        if not row:
            logger.error(f"No data found for contract {self.ticker} {strike} {expiration} on {current_date}")
            return
        premium = float(row[0])
        delta = float(row[1])
        gamma = float(row[2])
        theta = float(row[3])
        vega = float(row[4])
        rho = float(row[5])
        underlying_price = float(row[6])
        implied_volatility = float(row[7])
        # Create position dict
        pos = {
            "symbol": self.ticker,
            "expiration_date": expiration_date.strftime("%Y-%m-%d"),
            "strike_price": strike,
            "option_type": "put",
            "simulated_date": current_date.strftime("%Y-%m-%d"),
            "underlying_price": underlying_price,
            "implied_volatility": implied_volatility,
            "days_to_expiration": self.days_to_expiration(current_date, expiration_date),
            "delta": delta,
            "gamma": gamma,
            "theta": theta,
            "vega": vega,
            "rho": rho,
            "premium_collected": premium,
            "status": "active",
            "realized_gains": 0.0,
            "actual_delta": 0.0,
            "delta_error": 0.0,
            "actual_implied_vol": 0.0,
            "vol_error": 0.0,
        }
        # Store
        self.store_simulated_data(pos)
        logger.info(f"Stored simulated data for strike {strike}")
        logger.info(f"Sold put: strike {strike}, exp {expiration}, premium {premium}")

    def close_trade(self, symbol: str, expiration: str, strike: float, option_type: str, buyback_premium: float):
        """Close an active trade by setting status to 'closed' and calculating realized gains."""
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT realized_gains FROM {self.simulated_table}
            WHERE symbol=? AND expiration_date=? AND strike_price=? AND option_type=? AND status='active'
        """, (symbol, expiration, strike, option_type))
        row = cursor.fetchone()
        if not row:
            logger.error(f"No active trade found for {symbol} {strike} {option_type} exp {expiration}")
            return
        current_realized_gains = row[0]
        final_pnl = current_realized_gains - buyback_premium
        cursor.execute(f"""
            UPDATE {self.simulated_table}
            SET status='closed', realized_gains=?
            WHERE symbol=? AND expiration_date=? AND strike_price=? AND option_type=? AND status='active'
        """, (final_pnl, symbol, expiration, strike, option_type))
        self.conn.commit()
        logger.info(f"Closed trade: {symbol} {strike} {option_type} {expiration}, realized_gains: {final_pnl}")

    def check_simulations(self):
        """Check and update all active simulated trades."""
        current_date = date.today()
        base_price = 100.0  # Use fixed for check
        base_iv = 0.2
        self.run_backtest_step(current_date, base_price, base_iv)


if __name__ == "__main__":
    # CLI functionality
    parser = argparse.ArgumentParser(description="Simulate option trades and check simulations.")
    parser.add_argument('--SimSell-Call', action='store_true', help='Sell a call option')
    parser.add_argument('--SimSell-Put', action='store_true', help='Sell a put option')
    parser.add_argument('--strike', type=float, help='Strike price')
    parser.add_argument('--expiration', type=str, help='Expiration date (YYYY-MM-DD)')
    parser.add_argument('--check-sim', action='store_true', help='Check and update all active simulated trades')
    parser.add_argument('--ticker', type=str, default='AAPL', help='Ticker symbol (default: AAPL)')
    parser.add_argument('--Close-Trade', action='store_true', help='Close a trade')
    parser.add_argument('--option-type', type=str, help='Option type (call or put)')
    parser.add_argument('--buyback-premium', type=float, help='Buyback premium')

    args = parser.parse_args()

    # Initialize
    greek_calc = GreekCalculator()
    backtester = OptionsBacktester(args.ticker, greek_calc)

    if args.SimSell_Call:
        if not args.strike or not args.expiration:
            parser.error("--SimSell-Call requires --strike and --expiration")
        backtester.sell_option_call(args.strike, args.expiration)
    elif args.SimSell_Put:
        if not args.strike or not args.expiration:
            parser.error("--SimSell-Put requires --strike and --expiration")
        backtester.sell_option_put(args.strike, args.expiration)
    elif args.check_sim:
        backtester.check_simulations()
    elif args.Close_Trade:
        if not args.strike or not args.expiration or not args.buyback_premium or not args.ticker or not args.option_type:
            parser.error("--Close-Trade requires --strike, --expiration, --buyback_premium, --ticker, and --option-type")
        backtester.close_trade(args.ticker, args.expiration, args.strike, args.option_type, args.buyback_premium)
    else:
        parser.print_help()

"""        test cases to be investigated later:
5. Scenario Coverage
The backtesting framework with integrated Greeks filtering and optimization covers:

Scenario	Market Catalyst Description	Model Use
Bull Market	Rising prices, low volatility	Favor covered calls with delta near 0.3, high theta decay
Bear Market	Falling prices, high volatility	Limit delta exposure, increase cash-secured puts with low delta
High Volatility Events	VIX surges, earnings reports, geopolitical crises	Tighten Greeks thresholds, reduce exposure to high gamma/vega
Earnings Season	Earnings proximity effects causing volatility spikes	Apply earnings proximity filters, avoid high gamma near earnings
Holiday Periods	Thin liquidity, wider spreads	Increase minimum liquidity thresholds, limit position sizes
Sector Crisis	Industry-specific sell-offs or regulation	Sector-level risk limits, adjust position sizes based on sector Greeks
Economic Shocks	GDP reports, inflation surprises	Adjust risk parameters (rho, vega), reevaluate filters dynamically
Global Events	Trade wars, supply chain disruptions	Increase systemic risk factor in model, simulate portfolio stress
Portfolio Stress Testing	Tail risk via VaR and expected shortfall	Use aggregated Greeks in simulations to estimate portfolio-level losses
Backtesting Walk-Forward	Rolling parameter recalibration to adapt to regime changes	Recalibrate Greeks thresholds every 2 years; simulate out-of-sample
6. Practical Notes
Greeks calculation using Black-Scholes is well-suited for European options; for American options, numerical methods like binomial trees or finite difference methods should be used.
Implied volatility surfaces can be estimated using options data to input accurate sigma per strike and expiration in the model.
Greeks filtering enhances risk management by identifying adverse sensitivities before execution.
Backtesting with scenario tagging (bull, bear, earnings, etc.) allows adaptive parameter tuning to maximize returns and reduce drawdowns.
"""