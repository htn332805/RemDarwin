import logging
from typing import List, Optional
from dataclasses import dataclass
import sqlite3
from datetime import datetime
import pandas as pd
import argparse

# Import from yfinance_options.py
from yfinance_options import GreekCalculator, OptionContract

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FilterConfig:
    # Delta ranges for covered calls and cash-secured puts
    delta_range_calls: tuple = (0.15, 0.35)
    delta_range_puts: tuple = (-0.35, -0.15)
    min_theta: float = None #-0.02  # Minimum theta (negative value)
    max_vega: float = None #0.15
    max_gamma: float = None #0.10
    max_rho: float = None #0.05  # For high volatility and holiday special regimes
    high_volatility_sigma_threshold: float = None #0.5
    holiday_dividend_yield_threshold: float = None #0.03
    # Custom filter defaults
    min_delta: float = None #0.0
    max_theta: float = None #1.0
    min_volume: int = 100 #0
    premium_spread: float = 0.05
    liquidity_threshold: float = 0.5  # Minimum liquidity score (0-1)

class OptionFilter:
    def __init__(self, db_path: str, config: Optional[FilterConfig] = None):
        self.db_path = db_path
        self.config = config or FilterConfig()
        self.greek_calculator = GreekCalculator()

    def calculate_spread_metrics(self, contract: OptionContract) -> tuple:
        """Calculate raw spread and spread percentage using midpoint method.
        Returns (raw_spread, spread_pct) or (None, None) if insufficient data."""
        if contract.bid <= 0 or contract.ask <= 0:
            return None, None
        raw_spread = contract.ask - contract.bid
        midpoint = (contract.ask + contract.bid) / 2
        spread_pct = raw_spread / midpoint * 100
        return raw_spread, spread_pct

    def calculate_liquidity_score(self, contract: OptionContract, max_oi: int, max_vol: int) -> float:
        """Calculate composite liquidity score for a contract.
        Scores from 0 (illiquid) to 1 (highly liquid)."""
        if max_oi == 0 or max_vol == 0:
            return 0.0

        # Open interest score: normalized to max in chain
        oi_score = min(contract.open_interest / max_oi, 1.0)

        # Volume score: normalized to max in chain
        vol_score = min(contract.volume / max_vol, 1.0)

        # Spread score: inverse of spread percentage
        _, spread_pct = self.calculate_spread_metrics(contract)
        if spread_pct is None:
            spread_score = 0.0  # No spread data
        else:
            spread_score = 1 / (1 + spread_pct / 100)  # Normalize to 0-1

        # Market impact estimate: spread * sqrt(volume) / OI
        if contract.open_interest > 0 and spread_pct is not None:
            impact = (spread_pct / 100) * (contract.volume ** 0.5) / contract.open_interest
            impact_score = max(0, 1 - impact)  # Higher impact, lower score
        else:
            impact_score = 0.0

        # Composite score with weights
        liquidity_score = (0.3 * oi_score) + (0.3 * vol_score) + (0.2 * spread_score) + (0.2 * impact_score)
        return round(liquidity_score, 3)

    def generate_liquidity_report(self):
        """Task 2.5: Generate liquidity coverage report across option chains."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get all partitioned tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'options_%'")
            tables = [row[0] for row in cursor.fetchall()]

            total_contracts = 0
            liquid_contracts = 0
            coverage_stats = []

            for table in tables:
                cursor.execute(f"SELECT COUNT(*), COUNT(CASE WHEN liquidity_score >= 0.7 THEN 1 END) FROM {table} WHERE validated = 'True' OR validated = '1'")
                count_total, count_liquid = cursor.fetchone()
                total_contracts += count_total
                liquid_contracts += count_liquid
                coverage = (count_liquid / count_total * 100) if count_total > 0 else 0
                coverage_stats.append(f"{table}: {count_liquid}/{count_total} ({coverage:.1f}%)")

            overall_coverage = (liquid_contracts / total_contracts * 100) if total_contracts > 0 else 0

            report = f"""
Liquidity Coverage Report for {self.db_path}
==========================================
Total Contracts: {total_contracts}
Highly Liquid (>=0.7): {liquid_contracts}
Overall Coverage: {overall_coverage:.1f}%

Per Expiration:
{chr(10).join(coverage_stats)}
"""
            print(report)

        except Exception as e:
            logger.error(f"Error generating liquidity report: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

    def update_spread_data_in_db(self):
        """Task 1.3: Add spread columns to database tables and populate with calculated data."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get all partitioned tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'options_%'")
            tables = [row[0] for row in cursor.fetchall()]

            for table in tables:
                # Add columns if they don't exist
                try:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN raw_spread REAL")
                except sqlite3.OperationalError:
                    pass  # Column might already exist
                try:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN bid_ask_spread_pct REAL")
                except sqlite3.OperationalError:
                    pass
                try:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN bid_size INTEGER")
                except sqlite3.OperationalError:
                    pass
                try:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN ask_size INTEGER")
                except sqlite3.OperationalError:
                    pass
                try:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN liquidity_score REAL")
                except sqlite3.OperationalError:
                    pass

                # Get max OI and max volume for liquidity calculation
                cursor.execute(f"SELECT MAX(open_interest), MAX(volume) FROM {table}")
                max_oi, max_vol = cursor.fetchone()
                max_oi = int(max_oi) if max_oi else 0
                max_vol = int(max_vol) if max_vol else 0

                # Update existing rows with calculated spreads and liquidity
                cursor.execute(f"""
                    SELECT ROWID, bid, ask, open_interest, volume FROM {table}
                    WHERE CAST(bid AS REAL) > 0 AND CAST(ask AS REAL) > 0 AND (raw_spread IS NULL OR bid_ask_spread_pct IS NULL OR liquidity_score IS NULL)
                """)
                rows = cursor.fetchall()
                for rowid, bid, ask, oi, vol in rows:
                    bid_val = float(bid) if bid and bid != 'None' else 0.0
                    ask_val = float(ask) if ask and ask != 'None' else 0.0
                    oi_val = int(oi) if oi and oi != 'None' else 0
                    vol_val = int(vol) if vol and vol != 'None' else 0

                    if bid_val > 0 and ask_val > 0:
                        raw_spread = ask_val - bid_val
                        midpoint = (ask_val + bid_val) / 2
                        spread_pct = raw_spread / midpoint * 100

                        # Create a contract-like object for liquidity calc
                        class TempContract:
                            def __init__(self, b, a, oi, vol):
                                self.bid = b
                                self.ask = a
                                self.open_interest = oi
                                self.volume = vol

                        temp_contract = TempContract(bid_val, ask_val, oi_val, vol_val)
                        liquidity_score = self.calculate_liquidity_score(temp_contract, max_oi, max_vol)

                        cursor.execute(f"""
                            UPDATE {table} SET raw_spread = ?, bid_ask_spread_pct = ?, liquidity_score = ? WHERE ROWID = ?
                        """, (raw_spread, spread_pct, liquidity_score, rowid))

            conn.commit()
            logger.info(f"Updated spread data for {len(tables)} tables in {self.db_path}")

        except Exception as e:
            logger.error(f"Error updating spread data in DB: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

    def _fetch_options_from_db(self) -> List[OptionContract]:
        """Fetch all validated options from SQLite database."""
        options = []
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Get list of partitioned tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'options_20%'")
            tables = [row[0] for row in cursor.fetchall()]
            if not tables:
                # Check for options_history
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='options_history'")
                if cursor.fetchone():
                    tables = ['options_history']
                else:
                    logger.warning("No options tables found in database")
                    return []
            # Build union query
            union_query = " UNION ALL ".join([f"SELECT symbol, expiration_date, strike_price, option_type, bid, ask, last_price, volume, open_interest, implied_volatility, change, percent_change, delta, gamma, theta, vega, rho, prob_itm, prob_otm, prob_touch, days_to_expiration, underlying_price, validated, max_covered_call_return, put_return_on_risk, put_return_on_capital FROM {table} WHERE validated = 'True' OR validated = '1'" for table in tables])
            cursor.execute(union_query)
            rows = cursor.fetchall()
            for row in rows:
                # Convert TEXT fields back to appropriate types
                try:
                    opt = OptionContract(
                        symbol=row[0],
                        expiration_date=datetime.fromisoformat(row[1]) if row[1] and row[1] != 'None' else None,
                        strike_price=float(row[2]) if row[2] and row[2] != 'None' else 0.0,
                        option_type=row[3],
                        bid=float(row[4]) if row[4] and row[4] != 'None' else 0.0,
                        ask=float(row[5]) if row[5] and row[5] != 'None' else 0.0,
                        last_price=float(row[6]) if row[6] and row[6] != 'None' else 0.0,
                        volume=int(float(row[7])) if row[7] and row[7] != 'None' else 0,
                        open_interest=int(float(row[8])) if row[8] and row[8] != 'None' else 0,
                        implied_volatility=float(row[9]) if row[9] and row[9] != 'None' else 0.0,
                        change=float(row[10]) if row[10] and row[10] != 'None' else 0.0,
                        percent_change=float(row[11]) if row[11] and row[11] != 'None' else 0.0,
                        delta=float(row[12]) if row[12] and row[12] != 'None' else 0.0,
                        gamma=float(row[13]) if row[13] and row[13] != 'None' else 0.0,
                        theta=float(row[14]) if row[14] and row[14] != 'None' else 0.0,
                        vega=float(row[15]) if row[15] and row[15] != 'None' else 0.0,
                        rho=float(row[16]) if row[16] and row[16] != 'None' else 0.0,
                        prob_itm=float(row[17]) if row[17] and row[17] != 'None' else 0.0,
                        prob_otm=float(row[18]) if row[18] and row[18] != 'None' else 0.0,
                        prob_touch=float(row[19]) if row[19] and row[19] != 'None' else 0.0,
                        days_to_expiration=int(float(row[20])) if row[20] and row[20] != 'None' else None,
                        underlying_price=float(row[21]) if row[21] and row[21] != 'None' else None,
                        validated=row[22] == 'True' or row[22] == '1',
                        max_covered_call_return=float(row[23]) if row[23] and row[23] != 'None' else None,
                        put_return_on_risk=float(row[24]) if row[24] and row[24] != 'None' else None,
                        put_return_on_capital=float(row[25]) if row[25] and row[25] != 'None' else None
                    )
                    options.append(opt)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping invalid option record: {e}")
                    continue
        except Exception as e:
            logger.error(f"Error fetching options from DB: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
        return options

    def option_passes_filters(self, contract: OptionContract, market_regime: str) -> bool:
        """Apply quantitative filters based on FilterConfig, ignoring None parameters."""
        # Bid-ask spread filter: Ensure spread is less than premium_spread percentage
        # Task 1.2: Calculate using (Ask - Bid) / Midpoint Price × 100
        if contract.bid > 0 and contract.ask > 0:
            midpoint = (contract.ask + contract.bid) / 2
            spread_pct = (contract.ask - contract.bid) / midpoint * 100
            if spread_pct > self.config.premium_spread * 100:
                return False
        # If bid is 0 or ask is 0, skip spread check

        # Custom filters
        if self.config.min_delta is not None and abs(contract.delta) < self.config.min_delta:
            return False
        if self.config.max_theta is not None and contract.theta > self.config.max_theta:
            return False
        if self.config.min_volume is not None and contract.volume < self.config.min_volume:
            return False

        # Delta range filter
        if self.config.delta_range_calls is not None or self.config.delta_range_puts is not None:
            delta_min, delta_max = self._get_delta_range(contract.option_type, market_regime)
            if not (delta_min <= contract.delta <= delta_max):
                return False

        # Theta filter: Favor options with sufficiently high time decay
        if self.config.min_theta is not None:
            min_theta = self._get_min_theta(contract.option_type, market_regime)
            if contract.theta > min_theta:
                return False

        # Vega filter: Avoid excess volatility sensitivity
        if self.config.max_vega is not None:
            max_vega = self._get_max_vega(market_regime)
            if abs(contract.vega) > max_vega:
                return False

        # Gamma filter: Control convexity exposure
        if self.config.max_gamma is not None:
            if abs(contract.gamma) > self.config.max_gamma:
                return False

        # Rho filter: Adjust for interest rate sensitivity
        if self.config.max_rho is not None:
            max_rho = self._get_max_rho(market_regime)
            if abs(contract.rho) > max_rho:
                return False

        return True

    def filter_options(self, market_regime: str = 'normal', option_type: str = 'both') -> List[OptionContract]:
        """Apply quantitative filters to options from database based on FilterConfig."""
        options = self._fetch_options_from_db()
        filtered = []
        for opt in options:
            if option_type != 'both' and opt.option_type.lower() != option_type.lower():
                continue
            if self.option_passes_filters(opt, market_regime):
                filtered.append(opt)
        return filtered

    def _get_delta_range(self, option_type: str, market_regime: str):
        if option_type.lower() == 'call':
            base = self.config.delta_range_calls
        else:
            base = self.config.delta_range_puts
        if base is None:
            return (-float('inf'), float('inf'))  # No filter if None
        if market_regime == 'high_volatility':
            adjustment = 0.05
            return (base[0] - adjustment, base[1] + adjustment)
        elif market_regime == 'holiday':
            adjustment = 0.03
            return (base[0] - adjustment, base[1] + adjustment)
        else:
            return base

    def _get_min_theta(self, option_type: str, market_regime: str):
        base = self.config.min_theta
        if base is None:
            return -float('inf')  # No filter
        if market_regime == 'high_volatility':
            return base * 1.5  # Stricter theta in high vol
        return base

    def _get_max_vega(self, market_regime: str):
        base = self.config.max_vega
        if base is None:
            return float('inf')  # No filter
        if market_regime == 'high_volatility':
            return base * 0.7  # Reduce Vega exposure in high vol
        return base

    def _get_max_rho(self, market_regime: str):
        base = self.config.max_rho
        if base is None:
            return float('inf')  # No filter
        if market_regime == 'low_vol':
            return base * 2.0  # More lenient in low vol
        return base

def main():
    SENTINEL = object()
    parser = argparse.ArgumentParser(description='Filter options contracts with quantitative criteria')
    parser.add_argument('-t', '--ticker', required=True, help='Ticker symbol (e.g., AAPL)')
    parser.add_argument('-r', '--regime', choices=['normal', 'high_volatility', 'holiday', 'low_vol'],
                       default='normal', help='Market regime for filter adjustments')
    parser.add_argument('-o', '--option-type', choices=['call', 'put', 'both'],
                       default='both', help='Option type to filter (default: both)')
    # Custom filter arguments - use SENTINEL to detect if provided
    parser.add_argument('--min-delta', type=float, default=SENTINEL,
                       help='Minimum delta threshold (absolute value)')
    parser.add_argument('--max-theta', type=float, default=SENTINEL,
                       help='Maximum theta threshold')
    parser.add_argument('--min-volume', type=int, default=SENTINEL,
                       help='Minimum trading volume filter')
    parser.add_argument('--delta-range-calls', nargs=2, type=float, default=SENTINEL,
                       help='Delta range for calls (min max)')
    parser.add_argument('--delta-range-puts', nargs=2, type=float, default=SENTINEL,
                       help='Delta range for puts (min max)')
    parser.add_argument('--min-theta', type=float, default=SENTINEL,
                       help='Minimum theta threshold')
    parser.add_argument('--max-vega', type=float, default=SENTINEL,
                       help='Maximum vega threshold')
    parser.add_argument('--max-gamma', type=float, default=SENTINEL,
                       help='Maximum gamma threshold')
    parser.add_argument('--max-rho', type=float, default=SENTINEL,
                       help='Maximum rho threshold')

    args = parser.parse_args()

    # Build FilterConfig based on provided args
    config_kwargs = {}
    if args.min_delta is not SENTINEL:
        config_kwargs['min_delta'] = args.min_delta
    if args.max_theta is not SENTINEL:
        config_kwargs['max_theta'] = args.max_theta
    if args.min_volume is not SENTINEL:
        config_kwargs['min_volume'] = args.min_volume
    if args.delta_range_calls is not SENTINEL:
        config_kwargs['delta_range_calls'] = tuple(args.delta_range_calls)
    if args.delta_range_puts is not SENTINEL:
        config_kwargs['delta_range_puts'] = tuple(args.delta_range_puts)
    if args.min_theta is not SENTINEL:
        config_kwargs['min_theta'] = args.min_theta
    if args.max_vega is not SENTINEL:
        config_kwargs['max_vega'] = args.max_vega
    if args.max_gamma is not SENTINEL:
        config_kwargs['max_gamma'] = args.max_gamma
    if args.max_rho is not SENTINEL:
        config_kwargs['max_rho'] = args.max_rho

    config = FilterConfig(**config_kwargs)

    db_path = f'{args.ticker}_options.db'
    filterer = OptionFilter(db_path=db_path, config=config)

    try:
        filtered_opts = filterer.filter_options(market_regime=args.regime, option_type=args.option_type)

        # Convert to DataFrame
        if filtered_opts:
            df = pd.DataFrame([opt.__dict__ for opt in filtered_opts])
            print(f"Filtered options for {args.ticker} ({args.regime} regime):")
            print(f"Total contracts: {len(filtered_opts)}")
            print(f"Calls: {len([opt for opt in filtered_opts if opt.option_type.lower() == 'call'])}")
            print(f"Puts: {len([opt for opt in filtered_opts if opt.option_type.lower() == 'put'])}")
            print("\nDataFrame:")
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', None)
            print(df.to_string(index=False))
            # Export to CSV
            df.to_csv('filtered_contracts.csv', index=False)
            print(f"\nResults exported to 'filtered_contracts.csv'")
        else:
            print(f"No options passed filters for {args.ticker} in {args.regime} regime.")

    except Exception as e:
        logger.error(f"Error filtering options: {e}")
        print(f"Error: {e}")

if __name__ == '__main__':
    main()