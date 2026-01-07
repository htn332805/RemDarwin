"""
RemDarwin Historical Trade Data Collector - Foundation for Validation Framework

This module provides comprehensive collection and structuring of historical trade data
for backtesting LLM-enhanced trading decisions and confidence score calibration.
"""

import logging
import sqlite3
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np

from .decision_matrix import QuantitativeScore, LLMScore, DecisionMatrixResult

logger = logging.getLogger(__name__)


@dataclass
class HistoricalTrade:
    """Structured representation of a historical trade"""
    trade_id: str
    timestamp: datetime
    stock_symbol: str
    strategy_type: str  # 'covered_call' or 'cash_secured_put'
    expiration_date: str
    strike_price: float
    entry_price: float
    exit_price: Optional[float]
    entry_date: datetime
    exit_date: Optional[datetime]

    # P&L calculation
    premium_collected: float
    commissions: float = 0.0
    realized_pnl: Optional[float] = None
    unrealized_pnl: Optional[float] = None

    # Market context at entry
    market_regime: str
    volatility_environment: str
    vix_level: Optional[float]
    market_return_30d: Optional[float]

    # Quantitative scores at decision time
    quantitative_score: Optional[QuantitativeScore] = None

    # LLM analysis (if available)
    llm_score: Optional[LLMScore] = None
    decision_matrix_result: Optional[DecisionMatrixResult] = None

    # Outcome classification
    outcome_category: str = "open"  # 'profitable', 'loss', 'breakeven', 'open'
    max_adverse_excursion: Optional[float] = None
    holding_period_days: Optional[int] = None

    # Metadata
    data_source: str = "manual_entry"
    confidence_at_entry: Optional[float] = None
    notes: str = ""

    def calculate_pnl(self) -> Optional[float]:
        """Calculate realized P&L for closed trades"""
        if self.exit_price is None or self.exit_date is None:
            return None

        # For covered calls: premium + (stock_price_change if assigned)
        # For cash-secured puts: premium - (stock_price_change if assigned)
        # Simplified calculation - would need full position tracking in production

        if self.strategy_type == "covered_call":
            # Premium collected is positive, stock movement depends on assignment
            pnl = self.premium_collected - self.commissions
            if self.exit_price > self.strike_price:  # Would be assigned
                pnl += (self.strike_price - self.entry_price)
        else:  # cash_secured_put
            pnl = self.premium_collected - self.commissions
            if self.exit_price < self.strike_price:  # Would be assigned
                pnl -= (self.strike_price - self.exit_price)

        return pnl

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = {
            "trade_id": self.trade_id,
            "timestamp": self.timestamp.isoformat(),
            "stock_symbol": self.stock_symbol,
            "strategy_type": self.strategy_type,
            "expiration_date": self.expiration_date,
            "strike_price": self.strike_price,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "entry_date": self.entry_date.isoformat(),
            "exit_date": self.exit_date.isoformat() if self.exit_date else None,
            "premium_collected": self.premium_collected,
            "commissions": self.commissions,
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": self.unrealized_pnl,
            "market_regime": self.market_regime,
            "volatility_environment": self.volatility_environment,
            "vix_level": self.vix_level,
            "market_return_30d": self.market_return_30d,
            "outcome_category": self.outcome_category,
            "max_adverse_excursion": self.max_adverse_excursion,
            "holding_period_days": self.holding_period_days,
            "data_source": self.data_source,
            "confidence_at_entry": self.confidence_at_entry,
            "notes": self.notes
        }

        # Add complex objects if they exist
        if self.quantitative_score:
            result["quantitative_score"] = self.quantitative_score.to_dict()
        if self.llm_score:
            result["llm_score"] = self.llm_score.to_dict()
        if self.decision_matrix_result:
            result["decision_matrix_result"] = self.decision_matrix_result.to_dict()

        return result


class HistoricalDataCollector:
    """
    Collector and manager for historical trade data

    Features:
    - SQLite-based storage for historical trades
    - Data validation and consistency checks
    - Performance analytics and reporting
    - Integration with validation framework
    """

    def __init__(self, db_path: str = "data/historical_trades.db"):
        """
        Initialize the historical data collector

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create tables if they don't exist
        self._initialize_database()

        logger.info(f"Historical data collector initialized with database: {self.db_path}")

    def _initialize_database(self):
        """Create database tables and indexes"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    trade_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    stock_symbol TEXT NOT NULL,
                    strategy_type TEXT NOT NULL,
                    expiration_date TEXT NOT NULL,
                    strike_price REAL NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    entry_date TEXT NOT NULL,
                    exit_date TEXT,
                    premium_collected REAL NOT NULL,
                    commissions REAL DEFAULT 0.0,
                    realized_pnl REAL,
                    unrealized_pnl REAL,
                    market_regime TEXT,
                    volatility_environment TEXT,
                    vix_level REAL,
                    market_return_30d REAL,
                    quantitative_score_json TEXT,
                    llm_score_json TEXT,
                    decision_matrix_json TEXT,
                    outcome_category TEXT DEFAULT 'open',
                    max_adverse_excursion REAL,
                    holding_period_days INTEGER,
                    data_source TEXT DEFAULT 'manual_entry',
                    confidence_at_entry REAL,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for efficient querying
            conn.execute("CREATE INDEX IF NOT EXISTS idx_symbol ON trades(stock_symbol)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_strategy ON trades(strategy_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_entry_date ON trades(entry_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_outcome ON trades(outcome_category)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_market_regime ON trades(market_regime)")

    def add_trade(self, trade: HistoricalTrade) -> bool:
        """
        Add a historical trade to the database

        Args:
            trade: HistoricalTrade object to add

        Returns:
            True if successful, False otherwise
        """
        try:
            # Calculate derived fields
            if trade.exit_date and trade.entry_date:
                trade.holding_period_days = (trade.exit_date - trade.entry_date).days

            trade.realized_pnl = trade.calculate_pnl()

            # Classify outcome
            if trade.realized_pnl is not None:
                if trade.realized_pnl > 0:
                    trade.outcome_category = "profitable"
                elif trade.realized_pnl < 0:
                    trade.outcome_category = "loss"
                else:
                    trade.outcome_category = "breakeven"

            # Convert to database format
            trade_dict = trade.to_dict()

            with sqlite3.connect(self.db_path) as conn:
                # Prepare data for insertion
                columns = [k for k in trade_dict.keys() if k not in ['quantitative_score', 'llm_score', 'decision_matrix_result']]
                values = [trade_dict[k] for k in columns]

                # Add JSON fields
                if trade.quantitative_score:
                    columns.append('quantitative_score_json')
                    values.append(json.dumps(trade.quantitative_score.to_dict()))

                if trade.llm_score:
                    columns.append('llm_score_json')
                    values.append(json.dumps(trade.llm_score.to_dict()))

                if trade.decision_matrix_result:
                    columns.append('decision_matrix_json')
                    values.append(json.dumps(trade.decision_matrix_result.to_dict()))

                # Insert or replace
                placeholders = ','.join(['?' for _ in columns])
                query = f"""
                    INSERT OR REPLACE INTO trades ({','.join(columns)})
                    VALUES ({placeholders})
                """

                conn.execute(query, values)
                conn.commit()

            logger.info(f"Added trade {trade.trade_id} to historical database")
            return True

        except Exception as e:
            logger.error(f"Failed to add trade {trade.trade_id}: {e}")
            return False

    def get_trades(self,
                   symbol: Optional[str] = None,
                   strategy: Optional[str] = None,
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None,
                   outcome: Optional[str] = None,
                   limit: int = 1000) -> List[HistoricalTrade]:
        """
        Retrieve historical trades with filtering

        Args:
            symbol: Filter by stock symbol
            strategy: Filter by strategy type
            start_date: Filter trades entered after this date
            end_date: Filter trades entered before this date
            outcome: Filter by outcome category
            limit: Maximum number of trades to return

        Returns:
            List of HistoricalTrade objects
        """
        conditions = []
        params = []

        if symbol:
            conditions.append("stock_symbol = ?")
            params.append(symbol)

        if strategy:
            conditions.append("strategy_type = ?")
            params.append(strategy)

        if start_date:
            conditions.append("entry_date >= ?")
            params.append(start_date.isoformat())

        if end_date:
            conditions.append("entry_date <= ?")
            params.append(end_date.isoformat())

        if outcome:
            conditions.append("outcome_category = ?")
            params.append(outcome)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"""
            SELECT * FROM trades
            WHERE {where_clause}
            ORDER BY entry_date DESC
            LIMIT ?
        """
        params.append(limit)

        trades = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)

            for row in cursor:
                trade = self._row_to_trade(row)
                if trade:
                    trades.append(trade)

        return trades

    def _row_to_trade(self, row) -> Optional[HistoricalTrade]:
        """Convert database row to HistoricalTrade object"""
        try:
            # Parse JSON fields
            quantitative_score = None
            if row['quantitative_score_json']:
                quantitative_score = QuantitativeScore(**json.loads(row['quantitative_score_json']))

            llm_score = None
            if row['llm_score_json']:
                llm_score = LLMScore(**json.loads(row['llm_score_json']))

            decision_matrix_result = None
            if row['decision_matrix_json']:
                decision_matrix_result = DecisionMatrixResult(**json.loads(row['decision_matrix_json']))

            return HistoricalTrade(
                trade_id=row['trade_id'],
                timestamp=datetime.fromisoformat(row['timestamp']),
                stock_symbol=row['stock_symbol'],
                strategy_type=row['strategy_type'],
                expiration_date=row['expiration_date'],
                strike_price=row['strike_price'],
                entry_price=row['entry_price'],
                exit_price=row['exit_price'],
                entry_date=datetime.fromisoformat(row['entry_date']),
                exit_date=datetime.fromisoformat(row['exit_date']) if row['exit_date'] else None,
                premium_collected=row['premium_collected'],
                commissions=row['commissions'],
                realized_pnl=row['realized_pnl'],
                unrealized_pnl=row['unrealized_pnl'],
                market_regime=row['market_regime'],
                volatility_environment=row['volatility_environment'],
                vix_level=row['vix_level'],
                market_return_30d=row['market_return_30d'],
                quantitative_score=quantitative_score,
                llm_score=llm_score,
                decision_matrix_result=decision_matrix_result,
                outcome_category=row['outcome_category'],
                max_adverse_excursion=row['max_adverse_excursion'],
                holding_period_days=row['holding_period_days'],
                data_source=row['data_source'],
                confidence_at_entry=row['confidence_at_entry'],
                notes=row['notes']
            )
        except Exception as e:
            logger.error(f"Failed to parse trade from database row: {e}")
            return None

    def get_performance_stats(self,
                             symbol: Optional[str] = None,
                             strategy: Optional[str] = None,
                             start_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Calculate performance statistics for historical trades

        Args:
            symbol: Filter by stock symbol
            strategy: Filter by strategy type
            start_date: Filter trades from this date onward

        Returns:
            Dictionary with performance statistics
        """
        trades = self.get_trades(symbol=symbol, strategy=strategy, start_date=start_date, limit=10000)
        closed_trades = [t for t in trades if t.outcome_category != 'open']

        if not closed_trades:
            return {"total_trades": 0, "message": "No closed trades found"}

        # Calculate basic metrics
        total_pnl = sum(t.realized_pnl for t in closed_trades if t.realized_pnl is not None)
        winning_trades = [t for t in closed_trades if t.realized_pnl and t.realized_pnl > 0]
        losing_trades = [t for t in closed_trades if t.realized_pnl and t.realized_pnl < 0]

        win_rate = len(winning_trades) / len(closed_trades) if closed_trades else 0

        avg_win = sum(t.realized_pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t.realized_pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0

        # Calculate Sharpe-like ratio (assuming daily returns)
        returns = [t.realized_pnl / t.premium_collected for t in closed_trades
                  if t.realized_pnl is not None and t.premium_collected > 0]
        sharpe_ratio = np.mean(returns) / np.std(returns) if returns else 0

        # Maximum drawdown calculation (simplified)
        cumulative_pnl = np.cumsum([t.realized_pnl for t in closed_trades if t.realized_pnl is not None])
        running_max = np.maximum.accumulate(cumulative_pnl)
        drawdowns = running_max - cumulative_pnl
        max_drawdown = np.max(drawdowns) if len(drawdowns) > 0 else 0

        return {
            "total_trades": len(trades),
            "closed_trades": len(closed_trades),
            "open_trades": len(trades) - len(closed_trades),
            "total_pnl": total_pnl,
            "win_rate": win_rate,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": abs(sum(t.realized_pnl for t in winning_trades) /
                               sum(t.realized_pnl for t in losing_trades)) if losing_trades else float('inf'),
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "avg_holding_period": np.mean([t.holding_period_days for t in closed_trades
                                         if t.holding_period_days is not None]),
            "symbols_traded": len(set(t.stock_symbol for t in trades)),
            "date_range": {
                "start": min(t.entry_date for t in trades).isoformat() if trades else None,
                "end": max(t.entry_date for t in trades).isoformat() if trades else None
            }
        }

    def import_from_csv(self, csv_path: str, data_source: str = "csv_import") -> int:
        """
        Import historical trades from CSV file

        Args:
            csv_path: Path to CSV file
            data_source: Source identifier for imported data

        Returns:
            Number of trades imported successfully
        """
        try:
            df = pd.read_csv(csv_path)

            imported_count = 0
            for _, row in df.iterrows():
                try:
                    # Map CSV columns to HistoricalTrade fields
                    # This would need customization based on CSV format
                    trade = HistoricalTrade(
                        trade_id=str(row.get('trade_id', f"import_{imported_count}")),
                        timestamp=datetime.fromisoformat(row['timestamp']) if 'timestamp' in row else datetime.now(),
                        stock_symbol=row['stock_symbol'],
                        strategy_type=row['strategy_type'],
                        expiration_date=row['expiration_date'],
                        strike_price=float(row['strike_price']),
                        entry_price=float(row['entry_price']),
                        exit_price=float(row['exit_price']) if pd.notna(row.get('exit_price')) else None,
                        entry_date=datetime.fromisoformat(row['entry_date']),
                        exit_date=datetime.fromisoformat(row['exit_date']) if pd.notna(row.get('exit_date')) else None,
                        premium_collected=float(row['premium_collected']),
                        market_regime=row.get('market_regime', 'unknown'),
                        volatility_environment=row.get('volatility_environment', 'normal'),
                        data_source=data_source
                    )

                    if self.add_trade(trade):
                        imported_count += 1

                except Exception as e:
                    logger.warning(f"Failed to import trade from CSV row: {e}")
                    continue

            logger.info(f"Imported {imported_count} trades from {csv_path}")
            return imported_count

        except Exception as e:
            logger.error(f"Failed to import from CSV {csv_path}: {e}")
            return 0

    def export_to_csv(self, csv_path: str, **filters) -> int:
        """
        Export historical trades to CSV file

        Args:
            csv_path: Path to output CSV file
            **filters: Filtering parameters passed to get_trades

        Returns:
            Number of trades exported
        """
        trades = self.get_trades(**filters)

        if not trades:
            logger.warning("No trades to export")
            return 0

        # Convert to DataFrame
        trade_dicts = [trade.to_dict() for trade in trades]
        df = pd.DataFrame(trade_dicts)

        # Flatten nested objects for CSV
        if 'quantitative_score' in df.columns:
            df = df.drop('quantitative_score', axis=1)  # Remove complex objects for CSV

        if 'llm_score' in df.columns:
            df = df.drop('llm_score', axis=1)

        if 'decision_matrix_result' in df.columns:
            df = df.drop('decision_matrix_result', axis=1)

        df.to_csv(csv_path, index=False)
        logger.info(f"Exported {len(trades)} trades to {csv_path}")
        return len(trades)


# Utility functions for data validation and generation
def create_sample_historical_data() -> List[HistoricalTrade]:
    """
    Create sample historical trade data for testing and validation

    Returns:
        List of sample HistoricalTrade objects
    """
    base_date = datetime.now() - timedelta(days=365)

    sample_trades = []

    # Generate 50 sample trades across different scenarios
    for i in range(50):
        entry_date = base_date + timedelta(days=np.random.randint(0, 365))
        exit_date = entry_date + timedelta(days=np.random.randint(7, 90))

        # Random but realistic trade data
        stock_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META']
        strategies = ['covered_call', 'cash_secured_put']

        trade = HistoricalTrade(
            trade_id=f"SAMPLE_{i:03d}",
            timestamp=entry_date,
            stock_symbol=np.random.choice(stock_symbols),
            strategy_type=np.random.choice(strategies),
            expiration_date=(entry_date + timedelta(days=30)).strftime('%Y-%m-%d'),
            strike_price=np.random.uniform(100, 500),
            entry_price=np.random.uniform(80, 450),
            exit_price=np.random.uniform(80, 450) if np.random.random() > 0.3 else None,  # 70% closed
            entry_date=entry_date,
            exit_date=exit_date if np.random.random() > 0.3 else None,
            premium_collected=np.random.uniform(1, 10),
            market_regime=np.random.choice(['bull', 'bear', 'sideways']),
            volatility_environment=np.random.choice(['low', 'normal', 'high']),
            vix_level=np.random.uniform(10, 40),
            market_return_30d=np.random.uniform(-0.15, 0.15),
            data_source="sample_generation"
        )

        sample_trades.append(trade)

    return sample_trades


if __name__ == "__main__":
    # Test the historical data collector
    collector = HistoricalDataCollector()

    # Add sample data
    sample_trades = create_sample_historical_data()
    for trade in sample_trades:
        collector.add_trade(trade)

    # Test queries
    all_trades = collector.get_trades(limit=10)
    print(f"Total trades in database: {len(collector.get_trades(limit=10000))}")
    print(f"Sample of 10 trades: {len(all_trades)}")

    # Test performance stats
    stats = collector.get_performance_stats()
    print(f"Performance stats: {stats['win_rate']:.1%} win rate, ${stats['total_pnl']:.2f} total P&L")

    print("Historical data collector test completed successfully!")