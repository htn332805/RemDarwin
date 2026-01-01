import pandas as pd
import json
from datetime import datetime
from typing import Optional
import logging
import os
from MyCFATool.core.config import config
from MyCFATool.domain.repositories.financial_data_repository import FinancialDataRepository

class DataUpdater:
    """
    Handles storage and updating of FMP data using FinancialDataRepository.
    Avoids duplicates and appends new data automatically.
    """

    def __init__(self, log_level: str = "INFO", log_file: str = None):
        self.repository = FinancialDataRepository()

        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Console handler
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

        # File handler if specified
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)

    def upsert_statement(self, df: pd.DataFrame, table: str, symbol: str, period_type: str) -> tuple[int, int]:
        """
        Upsert financial statement data into the database.

        Args:
            df: DataFrame with statement data
            table: Table name (e.g., 'income_statement')
            symbol: Ticker symbol
            period_type: 'annual' or 'quarterly'

        Returns:
            Tuple of (records_added, records_skipped)
        """
        try:
            records_added, records_skipped = self.repository.upsert_statement(df, table, symbol, period_type)
            self.logger.info(f"Upserted {table} for {symbol} {period_type}: added {records_added}, skipped {records_skipped}")
            return records_added, records_skipped
        except Exception as e:
            self.logger.error(f"Error upserting {table} for {symbol}: {str(e)}")
            return 0, 0

    def upsert_ratios(self, df: pd.DataFrame, table: str, symbol: str, period_type: str) -> tuple[int, int]:
        """
        Upsert ratios data.
        """
        try:
            records_added, records_skipped = self.repository.upsert_ratios(df, table, symbol, period_type)
            self.logger.info(f"Upserted {table} for {symbol} {period_type}: added {records_added}, skipped {records_skipped}")
            return records_added, records_skipped
        except Exception as e:
            self.logger.error(f"Error upserting {table} for {symbol}: {str(e)}")
            return 0, 0

    def upsert_historical_prices(self, df: pd.DataFrame, symbol: str) -> tuple[int, int]:
        """
        Upsert historical price data.
        """
        try:
            records_added, records_skipped = self.repository.upsert_historical_prices(df, symbol)
            self.logger.info(f"Upserted historical_price for {symbol}: added {records_added}, skipped {records_skipped}")
            return records_added, records_skipped
        except Exception as e:
            self.logger.error(f"Error upserting historical_price for {symbol}: {str(e)}")
            return 0, 0

