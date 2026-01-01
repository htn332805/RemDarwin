import pandas as pd
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from ...core.database import db_manager
from ...core.config import config
import redis
import json
import logging
from ...ingestion.models import (
    IncomeStatement, BalanceSheet, CashFlow, HistoricalPrice,
    FinancialRatioReported, DataSource, UpdateLog
)
from .ticker_repository import TickerRepository
from ...core.exceptions import DatabaseError, DataNotFoundError
from ...core.validation import ValidationMixin, ValidationError
from ...core.models import IncomeStatementData, BalanceSheetData, CashFlowData, RatioData, PriceData
from datetime import datetime


class FinancialDataRepository(ValidationMixin):
    """Repository for financial data operations using SQLAlchemy ORM."""

    def __init__(self):
        self.ticker_repo = TickerRepository()
        self._ticker_id_cache = {}  # Simple in-memory cache for ticker_id lookups
        self.redis_client = None
        self.caching_enabled = config.config.get('redis', {}).get('caching', {}).get('enabled', False)
        if self.caching_enabled:
            self._init_redis()
        self.logger = logging.getLogger(__name__)

    def _init_redis(self):
        """Initialize Redis client for caching."""
        try:
            redis_config = config.config.get('redis', {})
            self.redis_client = redis.Redis(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                db=redis_config.get('db', 0),
                password=redis_config.get('password', ''),
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            self.logger.info("Redis client initialized successfully for caching.")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Redis client: {e}. Caching disabled.")
            self.redis_client = None
            self.caching_enabled = False

    def _get_ttl(self, data_type: str) -> int:
        """Get TTL for cache entry based on data type."""
        ttl_config = config.config.get('redis', {}).get('caching', {}).get('ttl', {})
        return ttl_config.get(data_type, 1800)  # Default 30 minutes

    def _get_from_cache(self, key: str) -> Optional[str]:
        """Retrieve data from Redis cache."""
        if not self.caching_enabled or not self.redis_client:
            return None
        try:
            value = self.redis_client.get(key)
            if value:
                self.logger.debug(f"Cache hit for key: {key}")
                return value
            else:
                self.logger.debug(f"Cache miss for key: {key}")
                return None
        except Exception as e:
            self.logger.warning(f"Error retrieving from cache: {e}")
            return None

    def _store_in_cache(self, key: str, value: str, data_type: str):
        """Store data in Redis cache with TTL."""
        if not self.caching_enabled or not self.redis_client:
            return
        try:
            ttl = self._get_ttl(data_type)
            self.redis_client.setex(key, ttl, value)
            self.logger.debug(f"Cached data for key: {key} with TTL: {ttl}")
        except Exception as e:
            self.logger.warning(f"Error storing in cache: {e}")

    def _delete_from_cache(self, key: str):
        """Delete data from Redis cache."""
        if not self.caching_enabled or not self.redis_client:
            return
        try:
            self.redis_client.delete(key)
            self.logger.debug(f"Deleted cache entry for key: {key}")
        except Exception as e:
            self.logger.warning(f"Error deleting from cache: {e}")

    def _delete_cache_keys_by_pattern(self, pattern: str):
        """Delete all cache keys matching a pattern."""
        if not self.caching_enabled or not self.redis_client:
            return
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                self.logger.debug(f"Deleted {len(keys)} cache entries matching pattern: {pattern}")
        except Exception as e:
            self.logger.warning(f"Error deleting cache keys by pattern: {e}")

    def _get_ticker_id_cached(self, ticker_symbol: str) -> Optional[int]:
        """Get ticker_id with caching to reduce database lookups."""
        if ticker_symbol not in self._ticker_id_cache:
            self._ticker_id_cache[ticker_symbol] = self.ticker_repo.get_ticker_id(ticker_symbol)
        return self._ticker_id_cache[ticker_symbol]

    def get_income_statement(self, ticker_symbol: str, period_type: str, fiscal_date: str) -> Optional[Dict[str, Any]]:
        """Get income statement data for a specific ticker, period, and date."""
        cache_key = f"income_statement:{ticker_symbol}:{period_type}:{fiscal_date}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return json.loads(cached_data)

        ticker_id = self._get_ticker_id_cached(ticker_symbol)
        if not ticker_id:
            return None

        with db_manager.session() as session:
            stmt = session.query(IncomeStatement).filter_by(
                ticker_id=ticker_id,
                period_type=period_type,
                fiscal_date=fiscal_date
            ).first()

            if stmt:
                data = {
                    'statement_id': stmt.statement_id,
                    'ticker_id': stmt.ticker_id,
                    'period_type': stmt.period_type,
                    'fiscal_date': stmt.fiscal_date,
                    'fiscal_year': stmt.fiscal_year,
                    'fiscal_quarter': stmt.fiscal_quarter,
                    'statement_data': stmt.statement_data,
                    'source_id': stmt.source_id,
                    'created_at': stmt.created_at
                }
                self._store_in_cache(cache_key, json.dumps(data), 'statements')
                return data
        return None

    def get_balance_sheet(self, ticker_symbol: str, period_type: str, fiscal_date: str) -> Optional[Dict[str, Any]]:
        """Get balance sheet data."""
        cache_key = f"balance_sheet:{ticker_symbol}:{period_type}:{fiscal_date}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return json.loads(cached_data)

        ticker_id = self._get_ticker_id_cached(ticker_symbol)
        if not ticker_id:
            return None

        with db_manager.session() as session:
            stmt = session.query(BalanceSheet).filter_by(
                ticker_id=ticker_id,
                period_type=period_type,
                fiscal_date=fiscal_date
            ).first()

            if stmt:
                data = {
                    'statement_id': stmt.statement_id,
                    'ticker_id': stmt.ticker_id,
                    'period_type': stmt.period_type,
                    'fiscal_date': stmt.fiscal_date,
                    'fiscal_year': stmt.fiscal_year,
                    'fiscal_quarter': stmt.fiscal_quarter,
                    'statement_data': stmt.statement_data,
                    'source_id': stmt.source_id,
                    'created_at': stmt.created_at
                }
                self._store_in_cache(cache_key, json.dumps(data), 'statements')
                return data
        return None

    def get_cash_flow(self, ticker_symbol: str, period_type: str, fiscal_date: str) -> Optional[Dict[str, Any]]:
        """Get cash flow data."""
        cache_key = f"cash_flow:{ticker_symbol}:{period_type}:{fiscal_date}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return json.loads(cached_data)

        ticker_id = self._get_ticker_id_cached(ticker_symbol)
        if not ticker_id:
            return None

        with db_manager.session() as session:
            stmt = session.query(CashFlow).filter_by(
                ticker_id=ticker_id,
                period_type=period_type,
                fiscal_date=fiscal_date
            ).first()

            if stmt:
                data = {
                    'statement_id': stmt.statement_id,
                    'ticker_id': stmt.ticker_id,
                    'period_type': stmt.period_type,
                    'fiscal_date': stmt.fiscal_date,
                    'fiscal_year': stmt.fiscal_year,
                    'fiscal_quarter': stmt.fiscal_quarter,
                    'statement_data': stmt.statement_data,
                    'source_id': stmt.source_id,
                    'created_at': stmt.created_at
                }
                self._store_in_cache(cache_key, json.dumps(data), 'statements')
                return data
        return None

    def get_historical_price_at_date(self, ticker_symbol: str, trade_date: str) -> Optional[Dict[str, Any]]:
        """Get historical price data for a specific date."""
        cache_key = f"price_at_date:{ticker_symbol}:{trade_date}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return json.loads(cached_data)

        ticker_id = self._get_ticker_id_cached(ticker_symbol)
        if not ticker_id:
            return None

        with db_manager.session() as session:
            price = session.query(HistoricalPrice).filter_by(
                ticker_id=ticker_id,
                trade_date=trade_date
            ).first()

            if price:
                data = {
                    'price_id': price.price_id,
                    'ticker_id': price.ticker_id,
                    'trade_date': price.trade_date,
                    'open': price.open,
                    'high': price.high,
                    'low': price.low,
                    'close': price.close,
                    'adj_close': price.adj_close,
                    'volume': price.volume,
                    'extra_data': price.extra_data,
                    'source_id': price.source_id,
                    'created_at': price.created_at
                }
                self._store_in_cache(cache_key, json.dumps(data), 'prices')
                return data
        return None

    def get_historical_prices(self, ticker_symbol: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all historical prices for a ticker, ordered by date desc."""
        ticker_id = self._get_ticker_id_cached(ticker_symbol)
        if not ticker_id:
            return []

        with db_manager.session() as session:
            query = session.query(HistoricalPrice).filter_by(ticker_id=ticker_id).order_by(HistoricalPrice.trade_date.desc())
            if limit:
                query = query.limit(limit)
            prices = query.all()

            return [
                {
                    'price_id': p.price_id,
                    'ticker_id': p.ticker_id,
                    'trade_date': p.trade_date,
                    'open': p.open,
                    'high': p.high,
                    'low': p.low,
                    'close': p.close,
                    'adj_close': p.adj_close,
                    'volume': p.volume,
                    'extra_data': p.extra_data,
                    'source_id': p.source_id,
                    'created_at': p.created_at
                }
                for p in prices
            ]

    def get_historical_prices_ordered(self, ticker_symbol: str, order: str = 'desc', limit: Optional[int] = None, up_to_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get historical prices for a ticker, ordered by date, optionally up to a date."""
        limit_str = str(limit) if limit else "none"
        up_to_date_str = up_to_date if up_to_date else "none"
        cache_key = f"prices_ordered:{ticker_symbol}:{order}:{limit_str}:{up_to_date_str}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return json.loads(cached_data)

        ticker_id = self._get_ticker_id_cached(ticker_symbol)
        if not ticker_id:
            return []

        with db_manager.session() as session:
            query = session.query(HistoricalPrice).filter_by(ticker_id=ticker_id)
            if up_to_date:
                query = query.filter(HistoricalPrice.trade_date <= up_to_date)
            if order == 'asc':
                query = query.order_by(HistoricalPrice.trade_date.asc())
            else:
                query = query.order_by(HistoricalPrice.trade_date.desc())
            if limit:
                query = query.limit(limit)
            prices = query.all()

            data = [
                {
                    'price_id': p.price_id,
                    'ticker_id': p.ticker_id,
                    'trade_date': p.trade_date,
                    'open': p.open,
                    'high': p.high,
                    'low': p.low,
                    'close': p.close,
                    'adj_close': p.adj_close,
                    'volume': p.volume,
                    'extra_data': p.extra_data,
                    'source_id': p.source_id,
                    'created_at': p.created_at
                }
                for p in prices
            ]
            self._store_in_cache(cache_key, json.dumps(data), 'prices')
            return data

    def get_ratios(self, ticker_symbol: str, period_type: str, fiscal_date: str) -> Optional[Dict[str, Any]]:
        """Get reported ratios data."""
        cache_key = f"ratios:{ticker_symbol}:{period_type}:{fiscal_date}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return json.loads(cached_data)

        ticker_id = self._get_ticker_id_cached(ticker_symbol)
        if not ticker_id:
            return None

        with db_manager.session() as session:
            ratio = session.query(FinancialRatioReported).filter_by(
                ticker_id=ticker_id,
                period_type=period_type,
                fiscal_date=fiscal_date
            ).first()

            if ratio:
                data = {
                    'ratio_id': ratio.ratio_id,
                    'ticker_id': ratio.ticker_id,
                    'period_type': ratio.period_type,
                    'fiscal_date': ratio.fiscal_date,
                    'ratio_data': ratio.ratio_data,
                    'source_id': ratio.source_id,
                    'created_at': ratio.created_at
                }
                self._store_in_cache(cache_key, json.dumps(data), 'ratios')
                return data
        return None

    def upsert_statement(self, df: pd.DataFrame, table: str, symbol: str, period_type: str) -> Tuple[int, int]:
        """Upsert financial statement data."""
        if df.empty:
            return 0, 0

        ticker_id = self.ticker_repo.add_ticker(symbol)

        model_map = {
            'income_statement': IncomeStatement,
            'balance_sheet': BalanceSheet,
            'cash_flow': CashFlow
        }
        Model = model_map[table]

        with db_manager.session() as session:
            try:
                source_id = self._get_source_id(session)
                records_added = 0
                records_skipped = 0

                new_records = []
                for _, row in df.iterrows():
                    row_dict = row.to_dict()
                    fiscal_date = row_dict.get("date") or row_dict.get("calendarDate")
                    if not fiscal_date:
                        continue

                    # Validate fiscal_date format
                    self.validate_date_format(fiscal_date)

                    fiscal_year = row_dict.get("calendarYear")
                    fiscal_quarter = row_dict.get("period") if period_type == "quarterly" else None

                    # Validate fiscal_year and fiscal_quarter
                    if fiscal_year is not None:
                        fiscal_year = self.validate_numeric(fiscal_year, min_val=1900, max_val=2100)
                        fiscal_year = int(fiscal_year)
                    if fiscal_quarter is not None:
                        fiscal_quarter = self.validate_numeric(fiscal_quarter, min_val=1, max_val=4)
                        fiscal_quarter = int(fiscal_quarter)

                    exclude_keys = {"date", "calendarDate", "calendarYear", "period", "symbol"}
                    statement_data = {k: v for k, v in row_dict.items() if k not in exclude_keys}

                    # Validate statement_data using Pydantic models
                    if table == 'income_statement':
                        IncomeStatementData(**statement_data)
                    elif table == 'balance_sheet':
                        BalanceSheetData(**statement_data)
                    elif table == 'cash_flow':
                        CashFlowData(**statement_data)

                    exists = session.query(Model).filter_by(ticker_id=ticker_id, period_type=period_type, fiscal_date=fiscal_date).first()
                    if exists:
                        records_skipped += 1
                        continue

                    new_records.append({
                        'ticker_id': ticker_id,
                        'period_type': period_type,
                        'fiscal_date': fiscal_date,
                        'fiscal_year': fiscal_year,
                        'fiscal_quarter': fiscal_quarter,
                        'statement_data': statement_data,
                        'source_id': source_id
                    })
                    records_added += 1

                # Batch insert new records
                if new_records:
                    session.bulk_insert_mappings(Model, new_records)

                session.commit()
                self._log_update(session, ticker_id, table, records_added, records_skipped)
                # Invalidate cache for this ticker and table
                if records_added > 0:
                    pattern = f"{table}:{symbol}:*"
                    self._delete_cache_keys_by_pattern(pattern)
                return records_added, records_skipped
            except Exception as e:
                session.rollback()
                raise DatabaseError(f"Error upserting {table} for {symbol}: {str(e)}")

    def upsert_ratios(self, df: pd.DataFrame, table: str, symbol: str, period_type: str) -> Tuple[int, int]:
        """Upsert ratios data."""
        if df.empty:
            return 0, 0

        ticker_id = self.ticker_repo.add_ticker(symbol)

        with db_manager.session() as session:
            try:
                source_id = self._get_source_id(session)
                records_added = 0
                records_skipped = 0

                new_records = []
                for _, row in df.iterrows():
                    row_dict = row.to_dict()
                    fiscal_date = row_dict.get("date")
                    if not fiscal_date:
                        continue

                    # Validate fiscal_date format
                    self.validate_date_format(fiscal_date)

                    exclude_keys = {"date", "symbol"}
                    ratio_data = {k: v for k, v in row_dict.items() if k not in exclude_keys}

                    # Validate ratio_data using Pydantic model
                    RatioData(**ratio_data)

                    exists = session.query(FinancialRatioReported).filter_by(ticker_id=ticker_id, period_type=period_type, fiscal_date=fiscal_date).first()
                    if exists:
                        records_skipped += 1
                        continue

                    new_records.append({
                        'ticker_id': ticker_id,
                        'period_type': period_type,
                        'fiscal_date': fiscal_date,
                        'ratio_data': ratio_data,
                        'source_id': source_id
                    })
                    records_added += 1

                # Batch insert new records
                if new_records:
                    session.bulk_insert_mappings(FinancialRatioReported, new_records)

                session.commit()
                self._log_update(session, ticker_id, table, records_added, records_skipped)
                # Invalidate cache for this ticker and table
                if records_added > 0:
                    pattern = f"ratios:{symbol}:*"
                    self._delete_cache_keys_by_pattern(pattern)
                return records_added, records_skipped
            except Exception as e:
                session.rollback()
                raise DatabaseError(f"Error upserting {table} for {symbol}: {str(e)}")

    def upsert_historical_prices(self, df: pd.DataFrame, symbol: str) -> Tuple[int, int]:
        """Upsert historical price data."""
        if df.empty:
            return 0, 0

        ticker_id = self.ticker_repo.add_ticker(symbol)

        with db_manager.session() as session:
            try:
                source_id = self._get_source_id(session)
                records_added = 0
                records_skipped = 0

                new_records = []
                for _, row in df.iterrows():
                    row_dict = row.to_dict()
                    trade_date = row_dict.get("date")
                    if not trade_date:
                        continue

                    open_price = row_dict.get("open")
                    high = row_dict.get("high")
                    low = row_dict.get("low")
                    close = row_dict.get("close")
                    adj_close = row_dict.get("adjClose")
                    volume = row_dict.get("volume")

                    # Validate using PriceData model
                    price_data = {
                        'date': trade_date,
                        'open': open_price,
                        'high': high,
                        'low': low,
                        'close': close,
                        'adj_close': adj_close,
                        'volume': volume
                    }
                    PriceData(**price_data)

                    exists = session.query(HistoricalPrice).filter_by(ticker_id=ticker_id, trade_date=trade_date).first()
                    if exists:
                        records_skipped += 1
                        continue

                    new_records.append({
                        'ticker_id': ticker_id,
                        'trade_date': trade_date,
                        'open': open_price,
                        'high': high,
                        'low': low,
                        'close': close,
                        'adj_close': adj_close,
                        'volume': volume,
                        'source_id': source_id
                    })
                    records_added += 1

                # Batch insert new records
                if new_records:
                    session.bulk_insert_mappings(HistoricalPrice, new_records)

                session.commit()
                self._log_update(session, ticker_id, "historical_price", records_added, records_skipped)
                # Invalidate cache for this ticker's prices
                if records_added > 0:
                    self._delete_cache_keys_by_pattern(f"price_at_date:{symbol}:*")
                    self._delete_cache_keys_by_pattern(f"prices_ordered:{symbol}:*")
                return records_added, records_skipped
            except Exception as e:
                session.rollback()
                raise DatabaseError(f"Error upserting historical_price for {symbol}: {str(e)}")

    def _get_source_id(self, session: Session) -> int:
        """Get or create FMP data source."""
        source = session.query(DataSource).filter_by(name="FMP", provider="Financial Modeling Prep").first()
        if source:
            return source.source_id
        source = DataSource(name="FMP", provider="Financial Modeling Prep", api_version="v3")
        session.add(source)
        session.commit()
        return source.source_id

    def _log_update(self, session: Session, ticker_id: int, table_name: str, records_added: int, records_skipped: int):
        """Log the update operation."""
        log_entry = UpdateLog(
            ticker_id=ticker_id,
            table_name=table_name,
            records_added=records_added,
            records_skipped=records_skipped,
            update_type="incremental"
        )
        session.add(log_entry)
        session.commit()