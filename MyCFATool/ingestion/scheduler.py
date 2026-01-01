import yaml
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
from datetime import datetime
from .fmp_client import FMPClient
from .data_updater import DataUpdater
from ..domain.services.data_ingestion_service import DataIngestionService

class DataScheduler:
    """
    Scheduler for automated financial data updates using APScheduler.
    """

    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config = self._load_config(config_path)
        self.fmp_client = FMPClient(config_path)
        self.tickers = self.config["tickers"]
        self.batch_config = self.config.get("batch_ingestion", {"max_concurrent": 1, "continue_on_error": True})
        self.data_updaters = {}  # Cache updaters per ticker
        self.ingestion_service = DataIngestionService(
            config_path=config_path,
            log_level=self.config["logging"]["level"],
            log_file=self.config["logging"]["file"]
        )
        self.scheduler = BackgroundScheduler(timezone=self.config["scheduler"]["timezone"])
        self.logger = logging.getLogger(__name__)

        # Setup logging
        self.logger.setLevel(getattr(logging, self.config["logging"]["level"].upper(), logging.INFO))
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        if self.config["logging"]["file"]:
            os.makedirs(os.path.dirname(self.config["logging"]["file"]), exist_ok=True)
            fh = logging.FileHandler(self.config["logging"]["file"])
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)

    def _get_data_updater(self, ticker: str) -> DataUpdater:
        if ticker not in self.data_updaters:
            self.data_updaters[ticker] = DataUpdater(
                log_level=self.config["logging"]["level"],
                log_file=self.config["logging"]["file"]
            )
        return self.data_updaters[ticker]

    def _load_config(self, config_path: str) -> dict:
        with open(config_path, "r") as file:
            return yaml.safe_load(file)

    def _get_trigger(self, interval: str):
        if interval == "daily":
            return IntervalTrigger(days=1)
        elif interval == "weekly":
            return IntervalTrigger(weeks=1)
        elif interval == "monthly":
            return IntervalTrigger(weeks=4)  # Approximate
        else:
            raise ValueError(f"Unsupported interval: {interval}")

    def update_all_data_for_ticker(self, ticker: str):
        """
        Update all financial data for a given ticker using DataIngestionService.
        """
        try:
            self.logger.info(f"Starting data update for {ticker}")
            self.ingestion_service.ingest_all_financial_data(ticker)
            self.logger.info(f"Completed data update for {ticker}")
        except Exception as e:
            self.logger.error(f"Error updating data for {ticker}: {str(e)}")

    def update_all_data_batch(self):
        """
        Update all financial data for all configured tickers in batch mode.
        """
        try:
            self.logger.info("Starting batch data update for all tickers")
            tickers = self._get_ticker_list()
            result = self.ingestion_service.ingest_batch_tickers(
                tickers,
                max_concurrent=self.batch_config.get("max_concurrent", 1),
                continue_on_error=self.batch_config.get("continue_on_error", True)
            )
            self.logger.info(f"Completed batch data update: {result['successful']} successful, {result['failed']} failed")
        except Exception as e:
            self.logger.error(f"Error in batch data update: {str(e)}")

    def _get_ticker_list(self) -> list[str]:
        """
        Get the list of tickers to process. Supports static list, S&P 500, or dynamic fetch.
        Handles testing mode with limited S&P 500 tickers.
        """
        testing_config = self.config.get("testing", {})
        if testing_config.get("enabled", False):
            # Testing mode: Use S&P 500 with limited tickers
            sp500_tickers = self.fmp_client.get_sp500_tickers()
            limit = testing_config.get("tickers_limit", 10)
            return sp500_tickers[:limit]
        else:
            # Production mode
            ticker_source = self.config.get("tickers_source", "static")
            if ticker_source == "sp500":
                return self.fmp_client.get_sp500_tickers()
            elif ticker_source == "dynamic":
                limit = self.config.get("tickers_limit", 1000)
                return self.fmp_client.get_available_tickers(limit)
            else:
                return self.tickers  # static list

    def schedule_updates(self):
        """
        Schedule the data update jobs based on config intervals.
        Schedule batch updates for all job types.
        """
        intervals = self.config["scheduler"]["intervals"]
        batch_mode = self.config.get("scheduler", {}).get("batch_mode", False)

        if batch_mode:
            # Schedule batch updates
            for job_type, interval in intervals.items():
                if job_type == "all_data":
                    trigger = self._get_trigger(interval)
                    self.scheduler.add_job(
                        self.update_all_data_batch,
                        trigger,
                        id=f"batch_{job_type}",
                        name=f"Batch update {job_type}"
                    )
                # For backward compatibility, still support individual types but in batch
                elif job_type.startswith("statements") or job_type.startswith("ratios") or job_type == "historical_prices":
                    trigger = self._get_trigger(interval)
                    self.scheduler.add_job(
                        self.update_all_data_batch,
                        trigger,
                        id=f"batch_{job_type}",
                        name=f"Batch update {job_type}"
                    )
        else:
            # Legacy per-ticker scheduling
            self._schedule_legacy_updates()

    def _schedule_legacy_updates(self):
        """
        Schedule updates using the legacy per-ticker approach.
        """
        intervals = self.config["scheduler"]["intervals"]
        for job_type, interval in intervals.items():
            trigger = self._get_trigger(interval)
            if job_type == "historical_prices":
                for ticker in self.tickers:
                    self.scheduler.add_job(
                        self.update_historical_prices,
                        trigger,
                        args=[ticker],
                        id=f"{job_type}_{ticker}",
                        name=f"Update {job_type} for {ticker}"
                    )
            else:
                # For statements and ratios, schedule combined updates
                if job_type.startswith("statements"):
                    period = job_type.split("_")[1]  # annual or quarterly
                    for ticker in self.tickers:
                        self.scheduler.add_job(
                            self.update_statements,
                            trigger,
                            args=[ticker, period],
                            id=f"{job_type}_{ticker}",
                            name=f"Update {job_type} for {ticker}"
                        )
                elif job_type.startswith("ratios"):
                    period = job_type.split("_")[1]
                    for ticker in self.tickers:
                        self.scheduler.add_job(
                            self.update_ratios,
                            trigger,
                            args=[ticker, period],
                            id=f"{job_type}_{ticker}",
                            name=f"Update {job_type} for {ticker}"
                        )

    def update_statements(self, ticker: str, period: str):
        """
        Update statements for a ticker and period.
        """
        try:
            self.logger.info(f"Updating statements for {ticker} {period}")
            updater = self._get_data_updater(ticker)
            if period == "annual":
                annual_is = self.fmp_client.get_annual_income_statement(ticker)
                updater.upsert_statement(annual_is, "income_statement", ticker, period)

                annual_bs = self.fmp_client.get_annual_balance_sheet(ticker)
                updater.upsert_statement(annual_bs, "balance_sheet", ticker, period)

                annual_cf = self.fmp_client.get_annual_cash_flow(ticker)
                updater.upsert_statement(annual_cf, "cash_flow", ticker, period)
            elif period == "quarterly":
                quarterly_is = self.fmp_client.get_quarterly_income_statement(ticker)
                updater.upsert_statement(quarterly_is, "income_statement", ticker, period)

                quarterly_bs = self.fmp_client.get_quarterly_balance_sheet(ticker)
                updater.upsert_statement(quarterly_bs, "balance_sheet", ticker, period)

                quarterly_cf = self.fmp_client.get_quarterly_cash_flow(ticker)
                updater.upsert_statement(quarterly_cf, "cash_flow", ticker, period)

            self.logger.info(f"Completed statements update for {ticker} {period}")
        except Exception as e:
            self.logger.error(f"Error updating statements for {ticker} {period}: {str(e)}")

    def update_ratios(self, ticker: str, period: str):
        """
        Update ratios for a ticker and period.
        """
        try:
            self.logger.info(f"Updating ratios for {ticker} {period}")
            updater = self._get_data_updater(ticker)
            if period == "annual":
                annual_ratios = self.fmp_client.get_annual_ratios(ticker)
                updater.upsert_ratios(annual_ratios, "financial_ratio_reported", ticker, period)
            elif period == "quarterly":
                quarterly_ratios = self.fmp_client.get_quarterly_ratios(ticker)
                updater.upsert_ratios(quarterly_ratios, "financial_ratio_reported", ticker, period)

            self.logger.info(f"Completed ratios update for {ticker} {period}")
        except Exception as e:
            self.logger.error(f"Error updating ratios for {ticker} {period}: {str(e)}")

    def update_historical_prices(self, ticker: str):
        """
        Update historical prices for a ticker.
        """
        try:
            self.logger.info(f"Updating historical prices for {ticker}")
            historical_prices = self.fmp_client.get_historical_price(ticker)
            updater = self._get_data_updater(ticker)
            updater.upsert_historical_prices(historical_prices, ticker)
            self.logger.info(f"Completed historical prices update for {ticker}")
        except Exception as e:
            self.logger.error(f"Error updating historical prices for {ticker}: {str(e)}")

    def start(self):
        """
        Start the scheduler.
        """
        if self.config["scheduler"]["enabled"]:
            self.schedule_updates()
            self.scheduler.start()
            self.logger.info("Scheduler started")
        else:
            self.logger.info("Scheduler disabled in config")

    def stop(self):
        """
        Stop the scheduler.
        """
        self.scheduler.shutdown()
        for updater in self.data_updaters.values():
            updater.close()
        self.logger.info("Scheduler stopped")

if __name__ == "__main__":
    scheduler = DataScheduler()
    scheduler.start()
    try:
        # Keep running
        import time
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        scheduler.stop()