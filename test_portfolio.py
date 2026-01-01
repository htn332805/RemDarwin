#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'MyCFATool'))

from MyCFATool.dashboard.callbacks import compute_portfolio_aggregates, compute_portfolio_risks

# Test with AAPL and CSCO
tickers = ['AAPL', 'CSCO']
weights = [0.6, 0.4]

print("Testing portfolio aggregates...")
portfolio = compute_portfolio_aggregates(tickers, weights)
print(portfolio)

print("Testing portfolio risks...")
risks = compute_portfolio_risks(tickers, weights)
print(risks)