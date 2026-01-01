from typing import Optional
from sqlalchemy.orm import Session
from ...core.database import db_manager
from ...ingestion.models import Ticker
from ...core.exceptions import DatabaseError
from ...core.validation import ValidationMixin, ValidationError
import redis
import json
from ...core.config import config


class TickerRepository(ValidationMixin):
    """Repository for ticker management operations."""

    def __init__(self):
        redis_config = config.config.get('redis', {})
        self.caching_enabled = redis_config.get('caching', {}).get('enabled', False)
        if self.caching_enabled:
            try:
                self.redis_client = redis.Redis(
                    host=redis_config.get('host', 'localhost'),
                    port=redis_config.get('port', 6379),
                    db=redis_config.get('db', 0),
                    password=redis_config.get('password') or None,
                    decode_responses=True
                )
                # Test connection
                self.redis_client.ping()
            except Exception:
                self.redis_client = None  # Graceful degradation if Redis unavailable
                self.caching_enabled = False
        else:
            self.redis_client = None

    def get_ticker_id(self, symbol: str, session: Optional[Session] = None) -> Optional[int]:
        """Get ticker_id for a symbol, returns None if not found."""
        cache_key = f"ticker_id:{symbol}"

        # Try cache first
        if self.caching_enabled and self.redis_client:
            try:
                cached_id = self.redis_client.get(cache_key)
                if cached_id:
                    return int(cached_id)
            except Exception:
                pass  # Fall back to database

        # Fetch from database
        with db_manager.session() as s:
            ticker = s.query(Ticker).filter_by(symbol=symbol).first()
            ticker_id = ticker.ticker_id if ticker else None

            # Cache the result (even if None, to avoid repeated lookups)
            if self.caching_enabled and self.redis_client:
                try:
                    # Cache for 1 hour
                    self.redis_client.setex(cache_key, 3600, str(ticker_id) if ticker_id else "none")
                except Exception:
                    pass

            return ticker_id

    def add_ticker(self, symbol: str, company_name: Optional[str] = None,
                   exchange: Optional[str] = None, sector: Optional[str] = None,
                   industry: Optional[str] = None, currency: Optional[str] = None) -> int:
        """Add a new ticker if it doesn't exist, return ticker_id."""
        # Validate ticker symbol: alphanumeric, length 1-10
        if not (symbol.isalnum() and 1 <= len(symbol) <= 10):
            raise ValidationError(f"Invalid ticker symbol '{symbol}': must be alphanumeric and 1-10 characters long")

        with db_manager.session() as session:
            try:
                existing = session.query(Ticker).filter_by(symbol=symbol).first()
                if existing:
                    return existing.ticker_id

                ticker = Ticker(
                    symbol=symbol,
                    company_name=company_name,
                    exchange=exchange,
                    sector=sector,
                    industry=industry,
                    currency=currency
                )
                session.add(ticker)
                session.commit()

                # Invalidate all_tickers cache
                if self.caching_enabled and self.redis_client:
                    try:
                        self.redis_client.delete("all_tickers")
                    except Exception:
                        pass

                return ticker.ticker_id
            except Exception as e:
                session.rollback()
                raise DatabaseError(f"Failed to add ticker {symbol}: {str(e)}")

    def get_all_tickers(self) -> list[dict]:
        """Get all tickers as list of dicts with Redis caching."""
        cache_key = "all_tickers"

        # Try Redis cache first
        if self.caching_enabled and self.redis_client:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            except Exception:
                pass  # Fall back to database

        # Fetch from database
        with db_manager.session() as session:
            tickers = session.query(Ticker).all()
            ticker_list = [
                {
                    'ticker_id': t.ticker_id,
                    'symbol': t.symbol,
                    'company_name': t.company_name,
                    'exchange': t.exchange,
                    'sector': t.sector,
                    'industry': t.industry,
                    'currency': t.currency,
                    'created_at': str(t.created_at)  # Convert to string for JSON
                }
                for t in tickers
            ]

            # Cache in Redis for 1 hour (3600 seconds)
            if self.caching_enabled and self.redis_client:
                try:
                    self.redis_client.setex(cache_key, 3600, json.dumps(ticker_list))
                except Exception:
                    pass  # Don't fail if caching fails

            return ticker_list

    def update_ticker(self, ticker_id: int, **kwargs) -> bool:
        """Update ticker information."""
        with db_manager.session() as session:
            try:
                ticker = session.query(Ticker).filter_by(ticker_id=ticker_id).first()
                if not ticker:
                    return False

                for key, value in kwargs.items():
                    if hasattr(ticker, key):
                        setattr(ticker, key, value)

                session.commit()

                # Invalidate caches
                if self.caching_enabled and self.redis_client:
                    try:
                        self.redis_client.delete("all_tickers")
                        self.redis_client.delete(f"ticker_id:{ticker.symbol}")
                    except Exception:
                        pass

                return True
            except Exception as e:
                session.rollback()
                raise DatabaseError(f"Failed to update ticker {ticker_id}: {str(e)}")

    def delete_ticker(self, ticker_id: int) -> bool:
        """Delete a ticker by ID."""
        with db_manager.session() as session:
            try:
                ticker = session.query(Ticker).filter_by(ticker_id=ticker_id).first()
                if not ticker:
                    return False

                session.delete(ticker)
                session.commit()

                # Invalidate caches
                if self.caching_enabled and self.redis_client:
                    try:
                        self.redis_client.delete("all_tickers")
                        self.redis_client.delete(f"ticker_id:{ticker.symbol}")
                    except Exception:
                        pass

                return True
            except Exception as e:
                session.rollback()
                raise DatabaseError(f"Failed to delete ticker {ticker_id}: {str(e)}")