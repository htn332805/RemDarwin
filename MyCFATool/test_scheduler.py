#!/usr/bin/env python3
"""
Test script for scheduler functionality.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from ingestion.scheduler import DataScheduler

def test_scheduler():
    scheduler = DataScheduler()
    print("Testing manual updates...")

    # Test update for AAPL
    try:
        scheduler.update_historical_prices("AAPL")
        print("Historical prices update test completed.")
    except Exception as e:
        print(f"Error in historical prices update: {e}")

    try:
        scheduler.update_statements("AAPL", "annual")
        print("Annual statements update test completed.")
    except Exception as e:
        print(f"Error in annual statements update: {e}")

    try:
        scheduler.update_ratios("AAPL", "annual")
        print("Annual ratios update test completed.")
    except Exception as e:
        print(f"Error in annual ratios update: {e}")

    scheduler.stop()
    print("Test completed. Check logs for details.")

if __name__ == "__main__":
    test_scheduler()