import logging
import sys
import os

from MyCFATool.ingestion.scheduler import DataScheduler

def main():
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger(__name__)

    try:
        logger.info("Starting full S&P 500 batch ingestion script")
        scheduler = DataScheduler(config_path="config/settings.yaml")
        scheduler.update_all_data_batch()
        logger.info("Batch ingestion completed successfully")
    except Exception as e:
        logger.error(f"An error occurred during batch ingestion: {str(e)}")
        raise

if __name__ == "__main__":
    main()