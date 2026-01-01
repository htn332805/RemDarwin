#!/usr/bin/env python3
"""
Test script for batch ingestion of tickers using testing configuration.
"""

import os
import sys
import time
import logging
import yaml
sys.path.append('MyCFATool')

# Load environment variables
if os.path.exists('MyCFATool/.env'):
    with open('MyCFATool/.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key] = value.strip('"')

from MyCFATool.ingestion.fmp_client import FMPClient
from MyCFATool.domain.services.data_ingestion_service import DataIngestionService

def setup_logging():
    """Setup comprehensive logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/batch_ingestion_test.log')
        ]
    )
    return logging.getLogger(__name__)

def get_testing_tickers(config_path="MyCFATool/config/settings.yaml"):
    """Get the testing subset of tickers from S&P 500."""
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)

    testing_config = config.get("testing", {})
    if testing_config.get("enabled", False):
        fmp_client = FMPClient(config_path)
        sp500_tickers = fmp_client.get_sp500_tickers()
        limit = testing_config.get("tickers_limit", 10)
        return sp500_tickers[:limit]
    else:
        # Fallback to static list
        return config.get("tickers", [])

def test_batch_ingestion():
    """Test batch ingestion with testing configuration tickers."""
    logger = setup_logging()

    # Get testing tickers
    test_tickers = get_testing_tickers()
    logger.info(f"Starting batch ingestion test for {len(test_tickers)} tickers: {test_tickers}")

    # Initialize service
    service = DataIngestionService(
        config_path="MyCFATool/config/settings.yaml",
        log_level="INFO",
        log_file="logs/batch_ingestion_test.log"
    )

    start_time = time.time()

    # Perform batch ingestion
    result = service.ingest_batch_tickers(
        test_tickers,
        max_concurrent=1,
        continue_on_error=True
    )

    end_time = time.time()
    total_time = end_time - start_time

    logger.info(f"Batch ingestion completed in {total_time:.2f} seconds")
    logger.info(f"  Total tickers: {result['total_tickers']}")
    logger.info(f"  Successful: {result['successful']}")
    logger.info(f"  Failed: {result['failed']}")

    # Detailed results per ticker
    logger.info("\nDetailed results per ticker:")
    for ticker in test_tickers:
        if ticker in result['errors']:
            logger.info(f"  {ticker}: FAILED - {result['errors'][ticker]}")
        else:
            logger.info(f"  {ticker}: SUCCESS")
            if ticker in result['results']:
                data = result['results'][ticker]
                total_added = sum(stats.get('added', 0) for stats in data.values() if isinstance(stats, dict))
                total_skipped = sum(stats.get('skipped', 0) for stats in data.values() if isinstance(stats, dict))
                logger.info(f"    Total records: added {total_added}, skipped {total_skipped}")
                for category, stats in data.items():
                    if isinstance(stats, dict) and 'added' in stats:
                        logger.info(f"      {category}: added {stats['added']}, skipped {stats['skipped']}")

    if result['errors']:
        logger.info("\nError summary:")
        for ticker, error in result['errors'].items():
            logger.info(f"  {ticker}: {error}")

    # Summary statistics
    success_rate = (result['successful'] / result['total_tickers']) * 100 if result['total_tickers'] > 0 else 0
    avg_time_per_ticker = total_time / result['total_tickers'] if result['total_tickers'] > 0 else 0

    logger.info("\nSummary Statistics:")
    logger.info(f"  Success Rate: {success_rate:.1f}%")
    logger.info(f"  Total Processing Time: {total_time:.2f} seconds")
    logger.info(f"  Average Time per Ticker: {avg_time_per_ticker:.2f} seconds")

if __name__ == "__main__":
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    test_batch_ingestion()