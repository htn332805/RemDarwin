import yfinance as yf
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
import logging

# Define a dataclass to represent each option contract
#	Change	% Change	Implied Volatility
@dataclass
class OptionContract:
    symbol: str
    expiration_date: datetime
    strike_price: float
    option_type: str  # 'call' or 'put'
    bid: float
    ask: float
    last_price: float
    volume: int
    open_interest: int
    implied_volatility: float
    change: float
    percent_change: float
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    rho: Optional[float] = None
    days_to_expiration: Optional[int] = None
    underlying_price: Optional[float] = None
    validated: bool = field(default=False)

class YFinanceOptionChainFetcher:
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    def fetch_option_chain(self, symbol: str):
        """
        Fetches the entire option chain (calls and puts) for the given symbol and validates basic contract data.
        Returns: Dict with 'calls' and 'puts', each a list of OptionContract instances, and 'underlying_price' of the stock.
        """
        try:
            ticker = yf.Ticker(symbol)
            self.logger.info(f"Fetching option expirations for {symbol}")
            exp_dates = ticker.options  # List of expiration date strings (YYYY-MM-DD)
            all_calls = []
            all_puts = []
            try:
                hist = ticker.history(period='1d')
                if hist.empty:
                    underlying_price = None
                else:
                    underlying_price = hist['Close'].iloc[0]
                    if not underlying_price or underlying_price <= 0:
                        self.logger.warning(f"Invalid underlying price for {symbol}: {underlying_price}")
                        underlying_price = None
            except Exception as e:
                self.logger.warning(f"Failed to fetch underlying price for {symbol}: {e}")
                underlying_price = None
            for exp in exp_dates:
                self.logger.info(f"Fetching options for expiration: {exp}")
                opt_chain = ticker.option_chain(exp)
                # Process calls
                for row in opt_chain.calls.itertuples():
                    contract = self._parse_option_row(row, symbol, 'call', exp, underlying_price)
                    if self._validate_contract(contract):
                        all_calls.append(contract)
                # Process puts
                for row in opt_chain.puts.itertuples():
                    contract = self._parse_option_row(row, symbol, 'put', exp, underlying_price)
                    if self._validate_contract(contract):
                        all_puts.append(contract)
            self.logger.info(f"Fetched {len(all_calls)} calls and {len(all_puts)} puts for {symbol}")
            return {
                'calls': all_calls,
                'puts': all_puts,
                'underlying_price': underlying_price,
                'fetch_timestamp': datetime.utcnow()
            }
        except Exception as e:
            self.logger.error(f"Failed to fetch options for {symbol}: {e}")
            return {
                'calls': [],
                'puts': [],
                'underlying_price': None,
                'fetch_timestamp': datetime.utcnow()
            }

    def _parse_option_row(self, row, symbol, option_type, expiration_date_str, underlying_price):
        """ Parse a row from yfinance option DataFrame into an OptionContract. """
        expiration_date = datetime.strptime(expiration_date_str, "%Y-%m-%d")
        days_to_expiration = (expiration_date - datetime.utcnow()).days
        implied_vol = getattr(row, 'impliedVolatility', None)
        iv = implied_vol if implied_vol is not None else 0.0
        return OptionContract(
            symbol=symbol,
            expiration_date=expiration_date,
            strike_price=float(getattr(row, 'strike', 0)),
            option_type=option_type,
            bid=float(getattr(row, 'bid', 0)),
            ask=float(getattr(row, 'ask', 0)),
            last_price=float(getattr(row, 'lastPrice', 0)),
            volume=int(getattr(row, 'volume', 0)),
            open_interest=int(getattr(row, 'openInterest', 0)),
            implied_volatility=iv,
            delta=None,
            gamma=None,
            theta=None,
            vega=None,
            rho=None,
            days_to_expiration=days_to_expiration,
            underlying_price=underlying_price,
            validated=False
        )

    def _validate_contract(self, contract: OptionContract) -> bool:
        """ Basic filter to ensure contract data validity before downstream processing. """
        # Basic bid-ask validation
        if (contract.bid is None or contract.ask is None or contract.ask <= contract.bid or contract.bid < 0 or contract.ask <= 0):
            self.logger.debug(f"Invalid bid/ask for {contract.symbol} {contract.option_type} "
                              f"strike {contract.strike_price} exp {contract.expiration_date}")
            return False
        # Volume and Open Interest must be non-negative
        if contract.volume < 0 or contract.open_interest < 0:
            self.logger.debug(f"Negative volume or open interest for {contract.symbol} "
                              f"{contract.option_type} strike {contract.strike_price}")
            return False
        # Implied Volatility must be reasonable
        if contract.implied_volatility < 0 or contract.implied_volatility > 5:  # 500% IV unlikely
            self.logger.debug(f"Implied volatility out of range for {contract.symbol} "
                              f"{contract.option_type} strike {contract.strike_price}")
            return False
        # Days to expiration must be positive and reasonable
        if contract.days_to_expiration < 0 or contract.days_to_expiration > 1000:
            self.logger.debug(f"Invalid days to expiration for {contract.symbol} "
                              f"{contract.option_type} strike {contract.strike_price}")
            return False
        contract.validated = True
        return True

# Example usage/demo code
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fetcher = YFinanceOptionChainFetcher()
    # Fetch option chain for Apple Inc.
    result = fetcher.fetch_option_chain("AAPL")
    print(f"Underlying Price: {result['underlying_price']}")
    print(f"Total Calls fetched: {len(result['calls'])}")
    print(f"Total Puts fetched: {len(result['puts'])}")
    # Print a sample contract
    if result['calls']:
        sample_call = result['calls'][0]
        print("Sample Call:")
        print(sample_call)
    if result['puts']:
        sample_put = result['puts'][0]
        print("Sample Put:")
        print(sample_put)