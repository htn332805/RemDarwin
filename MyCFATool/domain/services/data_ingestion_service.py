import logging
from typing import Dict, Any
from ...ingestion.fmp_client import FMPClient
from ...ingestion.data_updater import DataUpdater
from ...core.exceptions import DataIngestionError


class DataIngestionService:
    """
    Service to orchestrate data ingestion from FMP API to database.
    Consolidates ingestion logic and eliminates direct database connections.
    """

    def __init__(self, config_path: str = "config/settings.yaml", log_level: str = "INFO", log_file: str = None):
        self.client = FMPClient(config_path)
        self.updater = DataUpdater(log_level, log_file)
        self.logger = logging.getLogger(__name__)

    def ingest_all_financial_data(self, ticker: str) -> Dict[str, Any]:
        """
        Ingest all financial data for a ticker: statements, ratios, and prices.

        Args:
            ticker: Ticker symbol

        Returns:
            Dict with summary of ingestion results
        """
        results = {
            'ticker': ticker,
            'statements': {},
            'ratios': {},
            'prices': {}
        }

        try:
            # Ingest annual statements
            results['statements']['annual'] = self._ingest_statements(ticker, 'annual')
            # Ingest quarterly statements
            results['statements']['quarterly'] = self._ingest_statements(ticker, 'quarterly')

            # Ingest annual ratios
            results['ratios']['annual'] = self._ingest_ratios(ticker, 'annual')
            # Ingest quarterly ratios
            results['ratios']['quarterly'] = self._ingest_ratios(ticker, 'quarterly')

            # Ingest historical prices
            results['prices'] = self._ingest_prices(ticker)

            self.logger.info(f"Completed ingestion for {ticker}")
        except Exception as e:
            self.logger.error(f"Error during ingestion for {ticker}: {str(e)}")
            raise DataIngestionError(f"Ingestion failed for {ticker}: {str(e)}")

        return results

    def _ingest_statements(self, ticker: str, period: str) -> Dict[str, Any]:
        """Ingest financial statements for given period."""
        result = {'income_statement': {}, 'balance_sheet': {}, 'cash_flow': {}}

        # Income statement
        df = self.client.get_annual_income_statement(ticker) if period == 'annual' else self.client.get_quarterly_income_statement(ticker)
        added, skipped = self.updater.upsert_statement(df, 'income_statement', ticker, period)
        result['income_statement'] = {'added': added, 'skipped': skipped}

        # Balance sheet
        df = self.client.get_annual_balance_sheet(ticker) if period == 'annual' else self.client.get_quarterly_balance_sheet(ticker)
        added, skipped = self.updater.upsert_statement(df, 'balance_sheet', ticker, period)
        result['balance_sheet'] = {'added': added, 'skipped': skipped}

        # Cash flow
        df = self.client.get_annual_cash_flow(ticker) if period == 'annual' else self.client.get_quarterly_cash_flow(ticker)
        added, skipped = self.updater.upsert_statement(df, 'cash_flow', ticker, period)
        result['cash_flow'] = {'added': added, 'skipped': skipped}

        return result

    def _ingest_ratios(self, ticker: str, period: str) -> Dict[str, Any]:
        """Ingest financial ratios for given period."""
        df = self.client.get_annual_ratios(ticker) if period == 'annual' else self.client.get_quarterly_ratios(ticker)
        added, skipped = self.updater.upsert_ratios(df, 'ratios', ticker, period)
        return {'added': added, 'skipped': skipped}

    def _ingest_prices(self, ticker: str) -> Dict[str, Any]:
        """Ingest historical prices."""
        df = self.client.get_historical_price(ticker)
        added, skipped = self.updater.upsert_historical_prices(df, ticker)
        return {'added': added, 'skipped': skipped}

    def ingest_batch_tickers(self, tickers: list[str], max_concurrent: int = 1, continue_on_error: bool = True) -> Dict[str, Any]:
        """
        Ingest all financial data for multiple tickers in batch mode.

        Args:
            tickers: List of ticker symbols
            max_concurrent: Maximum concurrent ingestion processes (future use)
            continue_on_error: If True, continue processing other tickers on error

        Returns:
            Dict with summary of batch ingestion results including success/failure per ticker
        """
        batch_results = {
            'total_tickers': len(tickers),
            'successful': 0,
            'failed': 0,
            'results': {},
            'errors': {}
        }

        for ticker in tickers:
            try:
                self.logger.info(f"Starting batch ingestion for {ticker}")
                result = self.ingest_all_financial_data(ticker)
                batch_results['results'][ticker] = result
                batch_results['successful'] += 1
                self.logger.info(f"Successfully ingested data for {ticker}")
            except Exception as e:
                batch_results['failed'] += 1
                batch_results['errors'][ticker] = str(e)
                self.logger.error(f"Failed to ingest data for {ticker}: {str(e)}")
                if not continue_on_error:
                    raise DataIngestionError(f"Batch ingestion stopped due to error for {ticker}: {str(e)}")

        self.logger.info(f"Batch ingestion completed: {batch_results['successful']} successful, {batch_results['failed']} failed")
        return batch_results