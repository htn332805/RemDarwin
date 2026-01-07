import yfinance as yf  # Import the yfinance library to interface with Yahoo Finance's API, providing access to options chain data, underlying stock prices, and market information; this is a core dependency for this module's options data fetching functionality within RemDarwin's quantitative trading system.
import dataclasses  # Import dataclasses module for conversion utilities; this enables converting between dataclass instances and dictionaries for validation processing in RemDarwin's data pipeline.
from dataclasses import dataclass, field  # Import dataclass and field from the dataclasses module to define structured data classes for option contracts; this enables clean, immutable data structures for representing options data, supporting RemDarwin's options analysis by organizing contract attributes efficiently.
from typing import List, Optional  # Import type hints for List and Optional to provide static type checking and better code documentation; this helps in defining the structure of data collections (like lists of option contracts) and optional fields in the OptionContract dataclass, enhancing code maintainability in RemDarwin's options data handling.
from datetime import datetime  # Import datetime class to handle date and time operations, particularly for parsing expiration dates and calculating days to expiration; this is crucial for options data processing in RemDarwin, as expiration timing affects option pricing and strategy decisions.
import logging  # Import the logging module to enable structured logging of operations, errors, and warnings during options data fetching; this supports debugging and monitoring in RemDarwin's options system, ensuring robust error tracking and operational visibility.
import pandas as pd  # Import pandas library as pd for data manipulation and analysis, particularly for handling DataFrames returned by yfinance; this enables efficient processing of options chain data in tabular format, supporting RemDarwin's data analysis workflows for options trading.
from icecream import ic  # Import icecream's ic function for enhanced debugging and inspection of variables during development; this allows quick printing of expressions with context, aiding in troubleshooting options data parsing and validation in RemDarwin's development process.
from scipy.stats import norm  # Import norm from scipy.stats for cumulative distribution function in Black-Scholes calculations; this enables accurate computation of option Greeks in RemDarwin's quantitative options analysis.
import math  # Import math module for mathematical functions like sqrt, exp, log; this provides essential utilities for Black-Scholes model implementations in RemDarwin's options valuation.
import json  # Import json module for parsing parameter configuration files; this enables loading customizable risk parameters from external JSON files in RemDarwin's options pricing system.
import os  # Import os module for file system operations; this provides utilities for checking file existence and constructing paths in RemDarwin's parameter loading mechanism.
import sqlite3  # Import sqlite3 module for SQLite database operations; this enables local data storage for options contracts in RemDarwin's data persistence layer.
import argparse  # Import argparse module for command-line argument parsing; this enables CLI support for specifying ticker symbols and other parameters in RemDarwin's options data fetching script.
import sys  # Import sys module for path manipulation; this enables adding the current directory to the Python path for importing local modules in RemDarwin's options system.
import os  # Import os module for path operations; this provides utilities for constructing file paths in RemDarwin's module imports.
sys.path.append(os.path.dirname(__file__))  # Add current directory to Python path; this allows importing sibling modules in RemDarwin's options package.
from options_greeks import (  # Import Greeks calculation functions from the new options_greeks module; this provides individual Greek calculations using both Black-Scholes and Binomial models, with Binomial as default for American options.
    calculate_delta, calculate_gamma, calculate_theta, calculate_vega, calculate_rho
)
from data_validation import (  # Import data validation functions from the data_validation module; this enables comprehensive validation, gap-filling, normalization, and reporting for RemDarwin's options data quality assurance.
    validate_option_data, validate_greeks, gap_fill_missing_data, normalize_option_data, generate_validation_report
)
import re  # Import re module for regex validation; this enables pattern matching for ticker symbol validation in RemDarwin's input processing.

class GreekCalculator:  # Define the GreekCalculator class to compute option Greeks using the Black-Scholes model; this class encapsulates the mathematical calculations for delta, gamma, theta, vega, and rho, supporting RemDarwin's options risk analysis and strategy development.
    def __init__(self, risk_free_rate=None, dividend_yield=None):  # Initialize the GreekCalculator, loading parameters from static_parameters.json if available, otherwise using defaults; this enables configurable risk parameters in RemDarwin's options pricing.
        # Load parameters from static_parameters.json if it exists
        params_file = 'static_parameters.json'  # Path to the parameter configuration file; this allows external configuration of RemDarwin's options pricing parameters.
        if os.path.exists(params_file):  # Check if the parameter file exists; this enables conditional loading of custom parameters in RemDarwin's system.
            with open(params_file, 'r') as f:  # Open the parameter file for reading; this retrieves user-defined values for RemDarwin's options calculations.
                params = json.load(f)  # Parse the JSON content into a dictionary; this loads the structured parameters for RemDarwin's Greek calculations.
            self.r = params.get('risk_free_rate', 0.05)  # Extract risk-free rate from parameters or use default; this sets the interest rate for RemDarwin's Black-Scholes models.
            self.q = params.get('dividend_yield', 0.0)  # Extract dividend yield from parameters or use default; this sets the dividend rate for RemDarwin's options valuation.
        else:  # If parameter file does not exist, use provided arguments or defaults; this ensures RemDarwin's calculator always has valid parameters.
            self.r = risk_free_rate if risk_free_rate is not None else 0.05  # Set risk-free rate to provided value or default; this maintains flexibility in RemDarwin's parameter configuration.
            self.q = dividend_yield if dividend_yield is not None else 0.0  # Set dividend yield to provided value or default; this allows customization while providing safe fallbacks in RemDarwin's system.

    def _binomial_price(self, S, K, T, sigma, r, q, option_type, steps):  # Helper method to price American options using binomial tree model; this implements the Cox-Ross-Rubinstein model for accurate American option valuation in RemDarwin.
        """Price American option using binomial tree.
        
        Args:
            S: Underlying asset price
            K: Strike price
            T: Time to expiration in years
            sigma: Implied volatility
            r: Risk-free rate
            q: Dividend yield
            option_type: 'call' or 'put'
            steps: Number of time steps in the tree
        
        Returns:
            float: Option price
        """
        if T <= 0 or sigma <= 0 or steps < 1:  # Validate parameters to prevent invalid calculations; this ensures numerical stability in RemDarwin's binomial pricing.
            return 0.0  # Return zero for invalid inputs; this provides safe defaults for RemDarwin's options processing.
        
        dt = T / steps  # Calculate time step; this determines the granularity of the binomial tree in RemDarwin's pricing model.
        u = math.exp(sigma * math.sqrt(dt))  # Calculate up factor; this represents the upward movement in the stock price tree for RemDarwin's binomial model.
        d = 1 / u  # Calculate down factor; this represents the downward movement, ensuring recombining tree in RemDarwin's implementation.
        
        if u == d:  # Check for degenerate case; this handles scenarios where volatility leads to no price movement in RemDarwin's tree.
            if option_type.lower() == 'call':  # For call options, return intrinsic value; this provides correct pricing when tree collapses in RemDarwin.
                return max(0, S - K)  # Calculate call intrinsic value; this ensures accurate pricing for degenerate cases in RemDarwin.
            else:  # For put options, return intrinsic value; this maintains consistency for put pricing in RemDarwin.
                return max(0, K - S)  # Calculate put intrinsic value; this completes degenerate case handling in RemDarwin.
        
        p = (math.exp((r - q) * dt) - d) / (u - d)  # Calculate risk-neutral probability; this weights the expected value in RemDarwin's binomial valuation.
        if not (0 < p < 1):  # Validate probability bounds; this prevents invalid pricing due to parameter issues in RemDarwin.
            return 0.0  # Return zero for invalid probability; this ensures safe fallback in RemDarwin's options pricing.
        
        discount = math.exp(-r * dt)  # Calculate discount factor; this accounts for time value of money in RemDarwin's risk-neutral valuation.
        
        # Initialize option values at expiration
        option_values = [0.0] * (steps + 1)  # Create array for option values at each node; this stores the final payoffs in RemDarwin's tree structure.
        for j in range(steps + 1):  # Loop over final nodes; this populates the terminal values for RemDarwin's binomial tree.
            stock_price = S * (u ** (steps - j)) * (d ** j)  # Calculate stock price at node; this determines the underlying price for payoff calculation in RemDarwin.
            if option_type.lower() == 'call':  # For call options, calculate payoff; this implements the call option terminal value in RemDarwin.
                option_values[j] = max(0, stock_price - K)  # Calculate call payoff; this sets the intrinsic value at expiration for RemDarwin.
            else:  # For put options, calculate payoff; this handles put option terminal values in RemDarwin.
                option_values[j] = max(0, K - stock_price)  # Calculate put payoff; this completes terminal value calculation for RemDarwin.
        
        # Work backwards through the tree
        for i in range(steps - 1, -1, -1):  # Loop backwards through time steps; this propagates option values through RemDarwin's binomial tree.
            new_values = [0.0] * (i + 1)  # Create array for current time step; this holds updated option values for RemDarwin's backward induction.
            for j in range(i + 1):  # Loop over nodes at current time; this processes each branch in RemDarwin's tree.
                stock_price = S * (u ** (i - j)) * (d ** j)  # Calculate stock price at current node; this enables intrinsic value calculation in RemDarwin.
                intrinsic = max(0, stock_price - K) if option_type.lower() == 'call' else max(0, K - stock_price)  # Calculate intrinsic value; this determines the minimum value for American options in RemDarwin.
                expected = (p * option_values[j] + (1 - p) * option_values[j + 1]) * discount  # Calculate expected value; this computes the risk-neutral expectation in RemDarwin's valuation.
                new_values[j] = max(intrinsic, expected)  # Take maximum for American option; this implements the early exercise feature in RemDarwin's binomial model.
            option_values = new_values  # Update option values for next iteration; this propagates values backwards through RemDarwin's tree.
        
        return option_values[0]  # Return root node value; this provides the option price from RemDarwin's binomial tree calculation.

    def calculate_american_greeks(self, S, K, T, sigma, option_type, steps=100):  # Define the method to calculate American option Greeks using binomial tree; this provides accurate Greeks for American options with early exercise in RemDarwin.
        """Calculate option Greeks for American options using binomial tree model.
        
        Args:
            S: Underlying asset price
            K: Strike price
            T: Time to expiration in years
            sigma: Implied volatility
            option_type: 'call' or 'put'
            steps: Number of time steps in binomial tree (default 100)
        
        Returns:
            dict: Dictionary containing option price and Greeks
        """
        if T <= 0 or sigma <= 0:  # Validate input parameters to prevent invalid calculations; this ensures numerical stability in RemDarwin's American Greek computations.
            return {'price': 0.0, 'delta': 0.0, 'gamma': 0.0, 'theta': 0.0, 'vega': 0.0, 'rho': 0.0, 'prob_itm': 0.0, 'prob_otm': 0.0, 'prob_touch': 0.0}  # Return zero values for invalid inputs; this provides safe defaults for RemDarwin's options processing.
        
        # Small perturbation values for finite differences
        deltaS = 0.01  # Perturbation for stock price; this enables delta and gamma calculation in RemDarwin's numerical differentiation.
        dsigma = 0.001  # Perturbation for volatility; this allows vega computation in RemDarwin's Greek analysis.
        dr = 0.0001  # Perturbation for risk-free rate; this enables rho calculation in RemDarwin's interest rate sensitivity analysis.
        dT = min(0.01, T / 10) if T > 0.01 else T / 2  # Perturbation for time; this handles theta calculation near expiration in RemDarwin.
        
        # Calculate base price
        price = self._binomial_price(S, K, T, sigma, self.r, self.q, option_type, steps)  # Compute option price using binomial tree; this provides the base value for RemDarwin's Greek calculations.
        
        # Calculate perturbed prices for Greeks
        price_up = self._binomial_price(S + deltaS, K, T, sigma, self.r, self.q, option_type, steps)  # Price at increased stock price; this supports delta calculation in RemDarwin.
        price_down = self._binomial_price(S - deltaS, K, T, sigma, self.r, self.q, option_type, steps)  # Price at decreased stock price; this enables delta computation in RemDarwin.
        price_vega = self._binomial_price(S, K, T, sigma + dsigma, self.r, self.q, option_type, steps)  # Price at increased volatility; this allows vega calculation in RemDarwin.
        price_rho = self._binomial_price(S, K, T, sigma, self.r + dr, self.q, option_type, steps)  # Price at increased risk-free rate; this enables rho computation in RemDarwin.
        price_theta = self._binomial_price(S, K, T - dT, sigma, self.r, self.q, option_type, steps) if T > dT else price  # Price at decreased time; this supports theta calculation in RemDarwin.
        
        # Compute Greeks using finite differences
        delta = (price_up - price_down) / (2 * deltaS)  # Calculate delta; this measures directional risk for American options in RemDarwin.
        gamma = (price_up - 2 * price + price_down) / (deltaS ** 2)  # Calculate gamma; this measures delta change rate for American options in RemDarwin.
        vega = (price_vega - price) / dsigma  # Calculate vega; this measures volatility sensitivity for American options in RemDarwin.
        rho = (price_rho - price) / dr  # Calculate rho; this measures interest rate sensitivity for American options in RemDarwin.
        theta = (price_theta - price) / (-dT) if T > dT else 0.0  # Calculate theta; this quantifies time decay for American options in RemDarwin (negative for typical cases).
        
        # Use Black-Scholes for probabilities (approximation for American options)
        d1 = (math.log(S / K) + (self.r - self.q + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))  # Calculate d1 for probabilities; this approximates moneyness probabilities in RemDarwin.
        d2 = d1 - sigma * math.sqrt(T)  # Calculate d2; this complements d1 for probability calculations in RemDarwin.
        prob_itm = norm.cdf(d2) if option_type.lower() == 'call' else norm.cdf(-d2)  # Probability in the money; this provides moneyness assessment for RemDarwin's options analysis.
        prob_otm = 1 - prob_itm  # Probability out of the money; this completes probability calculations in RemDarwin.
        prob_touch = prob_itm  # Probability touching strike; approximated as prob_itm in RemDarwin.
        
        return {  # Return the calculated values as a dictionary; this structured output facilitates integration into RemDarwin's options data processing pipeline.
            'price': price,  # Include option price in the return; this provides the primary valuation from RemDarwin's binomial model.
            'delta': delta,  # Include delta; this enables delta-based hedging for American options in RemDarwin.
            'gamma': gamma,  # Include gamma; this supports gamma-neutral strategies for American options in RemDarwin.
            'theta': theta,  # Include theta; this allows time decay analysis for American options in RemDarwin.
            'vega': vega,  # Include vega; this enables volatility risk assessment for American options in RemDarwin.
            'rho': rho,  # Include rho; this completes Greek analysis for interest rate sensitivity in RemDarwin.
            'prob_itm': prob_itm,  # Probability in the money at expiration (approximated)
            'prob_otm': prob_otm,  # Probability out of the money at expiration
            'prob_touch': prob_touch  # Probability touching the strike (approximated)
        }

    def calculate_greeks(self, S, K, T, sigma, option_type):  # Define the method to calculate option Greeks, preferring binomial tree for American options with Black-Scholes fallback; this provides comprehensive options analysis with American option handling as default in RemDarwin.
        """Calculate option Greeks, attempting binomial tree for American options first, falling back to Black-Scholes.
        
        Args:
            S: Underlying asset price
            K: Strike price
            T: Time to expiration in years
            sigma: Implied volatility
            option_type: 'call' or 'put'
        
        Returns:
            dict: Dictionary containing delta, gamma, theta, vega, rho values
        """
        try:  # Attempt binomial tree calculation for American options; this prioritizes accurate American option pricing in RemDarwin's analysis.
            binomial_result = self.calculate_american_greeks(S, K, T, sigma, option_type)  # Calculate Greeks using binomial tree; this provides American option values as default in RemDarwin.
            return {k: v for k, v in binomial_result.items() if k != 'price'}  # Return Greeks from binomial calculation; this implements American option analysis as primary method in RemDarwin.
        except Exception as e:  # Fallback to Black-Scholes if binomial fails; this ensures robust calculation in RemDarwin's options processing.
            # Log the fallback if needed, but for now proceed with Black-Scholes
            pass  # Proceed to Black-Scholes calculation; this maintains continuity in RemDarwin's Greek computations.
        
        # Black-Scholes calculation as fallback
        if T <= 0 or sigma <= 0:  # Validate input parameters to prevent invalid calculations; this ensures numerical stability in RemDarwin's fallback Greek computations.
            return {'delta': 0.0, 'gamma': 0.0, 'theta': 0.0, 'vega': 0.0, 'rho': 0.0, 'prob_itm': 0.0, 'prob_otm': 0.0, 'prob_touch': 0.0}  # Return zero Greeks for invalid inputs; this provides safe defaults for RemDarwin's options processing.
        
        d1 = (math.log(S / K) + (self.r - self.q + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))  # Calculate d1 parameter for Black-Scholes model; this intermediate value is used in all Greek calculations in RemDarwin's framework.
        d2 = d1 - sigma * math.sqrt(T)  # Calculate d2 parameter; this complements d1 for complete Black-Scholes implementation in RemDarwin's options analysis.
        
        if option_type.lower() == 'call':  # Branch for call option calculations; this handles the specific formulas for call options in RemDarwin's Greek computations.
            delta = math.exp(-self.q * T) * norm.cdf(d1)  # Calculate delta for call options; this measures directional risk in RemDarwin's options strategies.
            gamma = math.exp(-self.q * T) * norm.pdf(d1) / (S * sigma * math.sqrt(T))  # Calculate gamma for options; this measures delta change rate, crucial for hedging in RemDarwin's risk management.
            theta = - (S * sigma * math.exp(-self.q * T) * norm.pdf(d1) / (2 * math.sqrt(T))) - self.r * K * math.exp(-self.r * T) * norm.cdf(d2) + self.q * S * math.exp(-self.q * T) * norm.cdf(d1)  # Calculate theta for call options; this quantifies time decay in RemDarwin's options valuation.
            vega = S * math.exp(-self.q * T) * norm.pdf(d1) * math.sqrt(T)  # Calculate vega for options; this measures volatility sensitivity in RemDarwin's risk analysis.
            rho = K * T * math.exp(-self.r * T) * norm.cdf(d2)  # Calculate rho for call options; this assesses interest rate risk in RemDarwin's comprehensive options evaluation.
            prob_itm = norm.cdf(d2)  # Probability in the money for call options
        else:  # put  # Branch for put option calculations; this applies the appropriate formulas for put options in RemDarwin's Greek computations.
            delta = -math.exp(-self.q * T) * norm.cdf(-d1)  # Calculate delta for put options; this provides directional exposure measurement for RemDarwin's put strategies.
            gamma = math.exp(-self.q * T) * norm.pdf(d1) / (S * sigma * math.sqrt(T))  # Calculate gamma for put options (same as call); this enables consistent gamma hedging across option types in RemDarwin.
            theta = - (S * sigma * math.exp(-self.q * T) * norm.pdf(d1) / (2 * math.sqrt(T))) + self.r * K * math.exp(-self.r * T) * norm.cdf(-d2) - self.q * S * math.exp(-self.q * T) * norm.cdf(-d1)  # Calculate theta for put options; this supports time decay analysis for RemDarwin's put positions.
            vega = S * math.exp(-self.q * T) * norm.pdf(d1) * math.sqrt(T)  # Calculate vega for put options (same as call); this maintains volatility risk consistency in RemDarwin's models.
            rho = -K * T * math.exp(-self.r * T) * norm.cdf(-d2)  # Calculate rho for put options; this evaluates interest rate exposure for RemDarwin's put option analysis.
            prob_itm = norm.cdf(-d2)  # Probability in the money for put options

        prob_otm = 1 - prob_itm  # Probability out of the money
        prob_touch = prob_itm  # Probability touching the strike, approximated as prob_itm
        
        return {  # Return the calculated Greeks as a dictionary; this structured output facilitates easy integration into RemDarwin's options data processing pipeline.
            'delta': delta,  # Include delta in the return dictionary; this enables RemDarwin's delta-based hedging and risk management.
            'gamma': gamma,  # Include gamma in the return dictionary; this supports gamma-neutral strategies in RemDarwin's portfolio optimization.
            'theta': theta,  # Include theta in the return dictionary; this allows RemDarwin to account for time decay in options pricing and strategy timing.
            'vega': vega,  # Include vega in the return dictionary; this enables volatility risk assessment in RemDarwin's options trading decisions.
            'rho': rho,  # Include rho in the return dictionary; this completes RemDarwin's comprehensive Greek analysis for interest rate sensitivity.
            'prob_itm': prob_itm,  # Probability in the money at expiration
            'prob_otm': prob_otm,  # Probability out of the money at expiration
            'prob_touch': prob_touch  # Probability touching the strike, approximated as prob_itm
        }

# Define a dataclass to represent each option contract
#	Change	% Change	Implied Volatility
@dataclass  # Apply the dataclass decorator to the following class definition, automatically generating __init__, __repr__, and other methods; this simplifies the creation of data structures for option contracts, enabling clean and efficient representation of options data in RemDarwin's analysis pipeline.
class OptionContract:  # Define the OptionContract class as a dataclass to encapsulate all attributes of an options contract, including pricing data, Greeks, and metadata; this class serves as the core data model for options data in RemDarwin, facilitating structured storage and manipulation of option chain information.
    symbol: str  # Define the symbol field as a string representing the ticker symbol of the underlying asset (e.g., 'AAPL'); this identifies the stock for which the option contract is written, essential for associating options data with the correct underlying in RemDarwin's trading system.
    expiration_date: datetime  # Define the expiration_date field as a datetime object indicating when the option contract expires; this date is critical for options valuation and strategy implementation in RemDarwin, determining the time value and exercise possibilities.
    strike_price: float  # Define the strike_price field as a float representing the strike price of the option contract; this price level determines whether the option is in-the-money or out-of-the-money, fundamental to options pricing and payoff calculations in RemDarwin's quantitative models.
    option_type: str  # 'call' or 'put'  # Define the option_type field as a string specifying whether the contract is a 'call' or 'put' option; this binary classification is essential for options strategy logic and payoff calculations in RemDarwin's trading algorithms.
    bid: float  # Define the bid field as a float representing the current bid price for the option contract; this price indicates the maximum amount buyers are willing to pay, used in liquidity and pricing analysis within RemDarwin's options market data processing.
    ask: float  # Define the ask field as a float representing the current ask price for the option contract; this price indicates the minimum amount sellers are willing to accept, critical for spread analysis and execution decisions in RemDarwin's automated trading system.
    last_price: float  # Define the last_price field as a float representing the most recent traded price of the option contract; this real-time pricing data supports market monitoring and trade timing in RemDarwin's options strategy implementation.
    volume: int  # Define the volume field as an integer representing the number of contracts traded in the current session; this volume data helps assess market activity and liquidity for options contracts in RemDarwin's quantitative analysis.
    open_interest: int  # Define the open_interest field as an integer representing the total number of outstanding option contracts that have not yet been settled; this metric indicates market participation and contract liquidity, essential for options strategy evaluation in RemDarwin.
    implied_volatility: float  # Define the implied_volatility field as a float representing the market's expectation of future volatility implied by the option's price; this key metric drives options pricing models and risk assessments in RemDarwin's systematic trading framework.
    change: float  # Define the change field as a float representing the dollar change in the option's price from the previous close; this price movement data enables trend analysis and momentum-based strategies in RemDarwin's options trading algorithms.
    percent_change: float  # Define the percent_change field as a float representing the percentage change in the option's price from the previous close; this relative price movement facilitates comparative analysis across different strikes and expirations in RemDarwin's quantitative models.
    delta: float  # Define the delta field as a float representing the rate of change of the option price with respect to the underlying asset's price; this Greek measures directional risk and is used in delta-hedging strategies within RemDarwin's options portfolio management.
    gamma: float  # Define the gamma field as a float representing the rate of change of delta with respect to the underlying price; this second-order Greek indicates delta stability and is crucial for dynamic hedging in RemDarwin's risk management system.
    theta: float  # Define the theta field as a float representing the rate of time decay of the option's value; this Greek quantifies how much value the option loses daily, essential for timing options trades in RemDarwin's decay-based strategies.
    vega: float  # Define the vega field as a float representing the sensitivity of the option price to changes in implied volatility; this Greek helps assess volatility risk and is key to volatility-based trading decisions in RemDarwin's quantitative framework.
    rho: float  # Define the rho field as a float representing the sensitivity of the option price to changes in interest rates; this Greek evaluates interest rate risk, supporting comprehensive risk analysis in RemDarwin's options valuation models.
    prob_itm: float  # Probability in the money at expiration
    prob_otm: float  # Probability out of the money at expiration
    prob_touch: float  # Probability touching the strike, approximated as prob_itm
    days_to_expiration: Optional[int] = None  # Define the days_to_expiration field as an optional integer representing the number of days until the option expires; this temporal metric is fundamental to time value calculations and expiration-based strategies in RemDarwin's trading algorithms.
    underlying_price: Optional[float] = None  # Define the underlying_price field as an optional float representing the current market price of the underlying asset; this price is used for moneyness calculations and intrinsic value assessments in RemDarwin's options analysis pipeline.
    validated: bool = field(default=False)  # Define the validated field as a boolean with default False, indicating whether the contract has passed data validation checks; this flag ensures data quality and prevents invalid contracts from entering RemDarwin's downstream processing.
    max_covered_call_return: Optional[float] = None
    put_return_on_risk: Optional[float] = None
    put_return_on_capital: Optional[float] = None


def contract_to_dict(contract: OptionContract) -> dict:
    """
    Convert OptionContract dataclass to dictionary for validation processing.

    Args:
        contract: OptionContract instance

    Returns:
        dict: Dictionary representation with date strings
    """
    d = dataclasses.asdict(contract)
    # Convert datetime to ISO string for validation
    if d['expiration_date']:
        d['expiration_date'] = d['expiration_date'].isoformat()
    return d


def update_contract_from_dict(contract: OptionContract, data: dict) -> OptionContract:
    """
    Update OptionContract fields from normalized dictionary data.

    Args:
        contract: Original OptionContract instance
        data: Normalized dictionary data

    Returns:
        OptionContract: Updated contract instance
    """
    # Update numeric fields from normalized data, handling None values
    for field in ['bid', 'ask', 'strike_price', 'underlying_price', 'last_price',
                  'volume', 'open_interest', 'implied_volatility', 'change',
                  'percent_change', 'delta', 'gamma', 'theta', 'vega', 'rho',
                  'prob_itm', 'prob_otm', 'prob_touch', 'days_to_expiration',
                  'max_covered_call_return', 'put_return_on_risk', 'put_return_on_capital']:
        if field in data and data[field] is not None:
            setattr(contract, field, data[field])
    return contract


def validate_ticker(ticker: str) -> None:
    """
    Validate ticker symbol format.

    Args:
        ticker: Ticker symbol string

    Raises:
        ValueError: If ticker format is invalid
    """
    # Add regex pattern for valid ticker symbols (1-5 uppercase letters)
    pattern = r'^[A-Z]{1,5}


class YFinanceOptionChainFetcher:  # Define the YFinanceOptionChainFetcher class as the main component for fetching and processing options data from Yahoo Finance; this class encapsulates the logic for retrieving option chains, parsing data, and validating contracts, serving as the core engine for options data acquisition in RemDarwin's systematic trading system.
    def __init__(self, logger=None):  # Define the constructor method for YFinanceOptionChainFetcher, accepting an optional logger parameter; this initializes the fetcher with logging capabilities, allowing for configurable logging in RemDarwin's options data fetching operations.
        self.logger = logger or logging.getLogger(__name__)  # Assign the logger instance to the object, using the provided logger or creating a default one for this module; this enables consistent logging throughout the fetcher's operations, supporting debugging and monitoring in RemDarwin's options data pipeline.

    def fetch_option_chain(self, symbol: str):  # Define the main method to fetch the complete option chain for a given stock symbol; this method orchestrates the retrieval of all available option contracts, their parsing, validation, and organization into structured data, forming the primary interface for options data acquisition in RemDarwin's trading system.
        """
        Fetches the entire option chain (calls and puts) for the given symbol and validates basic contract data.
        Returns: Dict with 'calls' and 'puts', each a list of OptionContract instances, and 'underlying_price' of the stock.
        """
        try:  # Begin exception handling block to catch and manage errors during the options fetching process; this ensures robust operation by gracefully handling API failures, network issues, or data parsing errors, maintaining system stability in RemDarwin's data acquisition workflow.
            ticker = yf.Ticker(symbol)  # Create a Ticker object from yfinance for the specified stock symbol; this object provides access to all financial data for the stock, including options chains, serving as the primary data source interface in RemDarwin's options fetching mechanism.
            self.logger.info(f"Fetching option expirations for {symbol}")  # Log an informational message indicating the start of expiration date retrieval; this provides visibility into the fetching process, aiding in monitoring and debugging options data acquisition in RemDarwin's operational logs.
            exp_dates = ticker.options  # List of expiration date strings (YYYY-MM-DD)  # Retrieve the list of available option expiration dates from the ticker object; this collection of date strings defines the time frames for which options data will be fetched, enabling comprehensive coverage of the option chain in RemDarwin's data collection process.
            self.logger.info(f"Found {len(exp_dates)} expiration dates: {exp_dates}")  # Log the number and list of expiration dates found; this helps debug if no expirations are available.
            ic(ticker.option_chain)  # Use icecream's ic function to inspect the option_chain property of the ticker; this debugging call provides a quick view of the option chain structure, aiding in development and troubleshooting of the options data fetching logic in RemDarwin.
            all_calls = []  # Initialize an empty list to accumulate call option contracts across all expiration dates; this container will hold validated OptionContract instances for call options, enabling organized storage and processing of calls data in RemDarwin's options analysis pipeline.
            all_puts = []  # Initialize an empty list to accumulate put option contracts across all expiration dates; this container will hold validated OptionContract instances for put options, facilitating structured handling of puts data in RemDarwin's quantitative trading system.
            validation_results = []  # Initialize list to track validation results for reporting; this collects boolean outcomes of the comprehensive validation pipeline for each contract.
            try:
                hist = ticker.history(period='1d')  # Fetch the recent historical price data for the stock over the last trading day; this provides the current underlying price information needed for options valuation and moneyness calculations in RemDarwin's options analysis.
                if hist.empty:  # Check if the historical data DataFrame is empty, indicating no price data was retrieved; this handles cases where the ticker has no recent trading data, setting underlying price to None for safe processing in RemDarwin's options calculations.
                    underlying_price = None  # Set underlying_price to None when no historical data is available; this prevents invalid price values from affecting options analysis and maintains data integrity in RemDarwin's valuation models.
                else:  # If historical data is available, proceed to extract the closing price; this branch handles the normal case where price data is successfully retrieved for options pricing in RemDarwin.
                    underlying_price = hist['Close'].iloc[0]  # Extract the most recent closing price from the historical data; this provides the current underlying asset price for moneyness determination and intrinsic value calculations in RemDarwin's options framework.
                    if not underlying_price or underlying_price <= 0:  # Validate that the extracted price is positive and valid; this check ensures data quality by filtering out invalid or zero prices that could corrupt options analysis in RemDarwin.
                        self.logger.warning(f"Invalid underlying price for {symbol}: {underlying_price}")  # Log a warning for invalid prices with details; this provides visibility into data quality issues, supporting monitoring and troubleshooting in RemDarwin's data pipeline.
                        underlying_price = None  # Reset invalid price to None; this maintains consistency and prevents downstream errors from propagating through RemDarwin's options processing system.
            except Exception as e:  # Catch any exceptions during price retrieval and processing; this ensures robust error handling for network issues, API failures, or data parsing problems in RemDarwin's price fetching mechanism.
                self.logger.warning(f"Failed to fetch underlying price for {symbol}: {e}")  # Log the failure with error details; this enables debugging and operational monitoring of price data acquisition issues in RemDarwin's system.
                underlying_price = None  # Set price to None on failure; this allows the options fetching to continue without underlying price data, maintaining system resilience in RemDarwin's data processing workflow.
            for exp in exp_dates:  # Iterate over each available expiration date to fetch options chains; this loop ensures comprehensive coverage of all expiration periods, enabling complete option chain retrieval for RemDarwin's analysis across different time horizons.
                self.logger.info(f"Fetching options for expiration: {exp}")  # Log the current expiration being processed; this provides progress tracking and debugging information for options data fetching operations in RemDarwin's logging system.
                opt_chain = ticker.option_chain(exp)  # Retrieve the option chain (calls and puts) for the specific expiration date from yfinance; this fetches the raw options data that will be parsed and validated for RemDarwin's options database.
                # Process calls
                calls_count = 0
                calls_valid = 0
                for row in opt_chain.calls.itertuples():  # Iterate through each call option row in the DataFrame; this processes individual call contracts, extracting and structuring their data for RemDarwin's quantitative analysis.
                    calls_count += 1
                    contract = self._parse_option_row(row, symbol, 'call', exp, underlying_price)  # Parse the raw row data into an OptionContract instance for calls; this converts yfinance's DataFrame row into a structured object with all necessary fields for RemDarwin's options processing.
                    # Enhanced validation pipeline with comprehensive data validation
                    contract_dict = contract_to_dict(contract)
                    if validate_option_data(contract_dict):
                        greeks_dict = {k: v for k, v in contract_dict.items() if k in ['delta', 'gamma', 'theta', 'vega', 'rho']}
                        if validate_greeks(greeks_dict):
                            filled = gap_fill_missing_data(contract_dict)
                            normalized = normalize_option_data(filled)
                            contract = update_contract_from_dict(contract, normalized)
                            if self._validate_contract(contract):  # Final validation check
                                all_calls.append(contract)
                                calls_valid += 1
                                validation_results.append(True)
                            else:
                                validation_results.append(False)
                        else:
                            validation_results.append(False)
                    else:
                        validation_results.append(False)
                # Process puts
                puts_count = 0
                puts_valid = 0
                for row in opt_chain.puts.itertuples():  # Iterate through each put option row in the DataFrame; this processes individual put contracts, enabling comprehensive put option data extraction for RemDarwin's trading strategies.
                    puts_count += 1
                    contract = self._parse_option_row(row, symbol, 'put', exp, underlying_price)  # Parse the raw row data into an OptionContract instance for puts; this structures put option data into RemDarwin's standardized format for analysis and decision-making.
                    # Enhanced validation pipeline with comprehensive data validation
                    contract_dict = contract_to_dict(contract)
                    if validate_option_data(contract_dict):
                        greeks_dict = {k: v for k, v in contract_dict.items() if k in ['delta', 'gamma', 'theta', 'vega', 'rho']}
                        if validate_greeks(greeks_dict):
                            filled = gap_fill_missing_data(contract_dict)
                            normalized = normalize_option_data(filled)
                            contract = update_contract_from_dict(contract, normalized)
                            if self._validate_contract(contract):  # Final validation check
                                all_puts.append(contract)
                                puts_valid += 1
                                validation_results.append(True)
                            else:
                                validation_results.append(False)
                        else:
                            validation_results.append(False)
                    else:
                        validation_results.append(False)
                self.logger.info(f"Expiration {exp}: {calls_count} calls parsed, {calls_valid} valid; {puts_count} puts parsed, {puts_valid} valid")  # Log processing statistics for each expiration; this helps debug validation issues.
            self.logger.info(f"Fetched {len(all_calls)} calls and {len(all_puts)} puts for {symbol}")  # Log the successful completion with counts of fetched contracts; this provides summary statistics for monitoring the effectiveness of options data acquisition in RemDarwin's system.
            # Generate validation report
            report = generate_validation_report(validation_results)
            return {  # Return the complete options data structure with all fetched and validated contracts; this delivers the processed options chain data to RemDarwin's downstream analysis and trading components.
                'calls': all_calls,  # Include the list of validated call option contracts; this provides call options data for RemDarwin's call-based trading strategies and analysis.
                'puts': all_puts,  # Include the list of validated put option contracts; this provides put options data for RemDarwin's put-based trading strategies and risk management.
                'underlying_price': underlying_price,  # Include the fetched underlying stock price; this enables moneyness calculations and intrinsic value assessments in RemDarwin's options valuation models.
                'fetch_timestamp': datetime.utcnow(),  # Include the UTC timestamp of the fetch operation; this provides temporal context for data freshness and supports time-series analysis in RemDarwin's options system.
                'validation_report': report  # Include the validation report with success metrics; this provides insights into data quality and validation effectiveness for RemDarwin's monitoring.
            }
        except Exception as e:  # Catch any unhandled exceptions during the entire fetching process; this provides a safety net for unexpected errors, ensuring RemDarwin's system remains stable even with API or processing failures.
            self.logger.error(f"Failed to fetch options for {symbol}: {e}")  # Log the critical error with details; this enables debugging and alerts for system failures in RemDarwin's options data pipeline.
            return {  # Return an empty data structure on failure; this maintains API consistency while indicating that no valid options data was retrieved for RemDarwin's processing.
                'calls': [],  # Return empty list for calls on error; this prevents downstream components from attempting to process invalid data in RemDarwin's system.
                'puts': [],  # Return empty list for puts on error; this ensures safe failure handling in RemDarwin's options analysis pipeline.
                'underlying_price': None,  # Return None for price on error; this clearly indicates price unavailability to RemDarwin's valuation calculations.
                'fetch_timestamp': datetime.utcnow()  # Include timestamp even on failure; this provides timing context for error analysis in RemDarwin's monitoring and logging system.
            }

    def _parse_option_row(self, row, symbol, option_type, expiration_date_str, underlying_price):  # Define the private method to parse raw yfinance DataFrame rows into OptionContract objects; this method handles data type conversion, NaN handling, and field extraction for both call and put options in RemDarwin's data processing pipeline.
        """ Parse a row from yfinance option DataFrame into an OptionContract. """
        expiration_date = datetime.strptime(expiration_date_str, "%Y-%m-%d")  # Parse the expiration date string into a datetime object; this converts the string format from yfinance into a usable date for RemDarwin's temporal calculations and contract identification.
        days_to_expiration = (expiration_date - datetime.utcnow()).days  # Calculate the number of days until expiration from the current UTC time; this temporal metric is crucial for time value decay analysis and expiration-based strategies in RemDarwin's options framework.
        implied_vol = getattr(row, 'impliedVolatility', None)  # Extract the implied volatility value from the row, handling missing attributes gracefully; this retrieves the market's volatility expectation for pricing models in RemDarwin's options valuation.
        iv = implied_vol if implied_vol is not None else 0.0  # Set implied volatility to extracted value or default to 0.0 for missing data; this ensures a valid IV value for RemDarwin's calculations, preventing NaN propagation.

        strike = getattr(row, 'strike', 0)  # Extract the strike price from the row, defaulting to 0 if missing; this gets the key price level that determines option moneyness for RemDarwin's analysis.
        strike_price = float(strike) if not pd.isna(strike) else 0.0  # Convert strike to float if valid, otherwise use 0.0; this ensures numeric strike price data for RemDarwin's calculations, handling pandas NaN values safely.

        # Calculate option Greeks using binomial model for American options (default) if valid data is available
        if underlying_price and iv > 0:  # Check for valid underlying price and implied volatility to enable Greek calculations; this ensures RemDarwin only computes Greeks with reliable market data.
            T_years = days_to_expiration / 365.0  # Convert days to expiration to years for options calculations; this standardizes time units for RemDarwin's options valuation models.
            # Calculate each Greek individually using binomial model as default for American options
            delta = calculate_delta(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate delta using binomial model for American options
            gamma = calculate_gamma(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate gamma using binomial model for American options
            theta = calculate_theta(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate theta using binomial model for American options
            vega = calculate_vega(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate vega using binomial model for American options
            rho = calculate_rho(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate rho using binomial model for American options
            # Use Black-Scholes for probabilities (approximation for American options)
            d1 = (math.log(underlying_price / strike_price) + (0.05 - 0.0 + 0.5 * iv**2) * T_years) / (iv * math.sqrt(T_years))  # Calculate d1 for probabilities; this approximates moneyness for American options.
            d2 = d1 - iv * math.sqrt(T_years)  # Calculate d2 for probabilities
            prob_itm = norm.cdf(d2) if option_type.lower() == 'call' else norm.cdf(-d2)  # Probability in the money
            prob_otm = 1 - prob_itm  # Probability out of the money
            prob_touch = prob_itm  # Probability touching strike, approximated
            greeks = {'delta': delta, 'gamma': gamma, 'theta': theta, 'vega': vega, 'rho': rho, 'prob_itm': prob_itm, 'prob_otm': prob_otm, 'prob_touch': prob_touch}  # Build greeks dictionary with calculated values
        else:  # If insufficient data for Greek calculation, set to zero; this provides safe defaults for RemDarwin's data processing when market data is unavailable.
            greeks = {'delta': 0.0, 'gamma': 0.0, 'theta': 0.0, 'vega': 0.0, 'rho': 0.0, 'prob_itm': 0.0, 'prob_otm': 0.0, 'prob_touch': 0.0}  # Assign zero values to all Greeks when calculation is not possible; this maintains data consistency in RemDarwin's options data structure.

        bid = getattr(row, 'bid', 0)  # Extract the bid price from the row; this gets the buyer's maximum offer price for liquidity analysis in RemDarwin's options trading decisions.
        bid_price = float(bid) if not pd.isna(bid) else 0.0  # Convert bid to float if valid; this provides numeric bid data for spread calculations in RemDarwin's market analysis.

        # Calculate strategy-specific returns
        max_covered_call_return = None
        put_return_on_risk = None
        put_return_on_capital = None
        if option_type == 'call' and underlying_price is not None:
            max_covered_call_return = strike_price - underlying_price + bid_price
        elif option_type == 'put':
            if strike_price > bid_price:
                put_return_on_risk = (bid_price / (strike_price - bid_price)) * 100
            put_return_on_capital = (bid_price / strike_price) * 100

        ask = getattr(row, 'ask', 0)  # Extract the ask price from the row; this gets the seller's minimum asking price for pricing analysis in RemDarwin's options strategies.
        ask_price = float(ask) if not pd.isna(ask) else 0.0  # Convert ask to float if valid; this ensures numeric ask data for RemDarwin's spread and execution cost evaluations.

        last = getattr(row, 'lastPrice', 0)  # Extract the last traded price from the row; this provides the most recent market price for real-time analysis in RemDarwin's options monitoring.
        last_price = float(last) if not pd.isna(last) else 0.0  # Convert last price to float if valid; this gives numeric last price data for price movement tracking in RemDarwin's system.

        vol = getattr(row, 'volume', 0)  # Extract the trading volume from the row; this indicates daily trading activity for liquidity assessment in RemDarwin's options analysis.
        volume = int(vol) if not pd.isna(vol) else 0  # Convert volume to integer if valid; this provides numeric volume data for RemDarwin's market activity evaluations.

        oi = getattr(row, 'openInterest', 0)  # Extract the open interest from the row; this shows outstanding contracts for market participation analysis in RemDarwin's strategies.
        open_interest = int(oi) if not pd.isna(oi) else 0  # Convert open interest to integer if valid; this gives numeric OI data for RemDarwin's contract liquidity and positioning analysis.

        ch = getattr(row, 'change', 0)  # Extract the price change from the row; this shows daily price movement for trend analysis in RemDarwin's options strategies.
        change = float(ch) if not pd.isna(ch) else 0.0  # Convert change to float if valid; this provides numeric change data for RemDarwin's price movement tracking.

        pch = getattr(row, 'percentChange', 0)  # column for % Change  # Extract the percentage change from the row; this indicates relative price movement for comparative analysis in RemDarwin's quantitative models.
        percent_change = float(pch) if not pd.isna(pch) else 0.0  # Convert percent change to float if valid; this gives numeric percentage data for RemDarwin's relative performance evaluations.

        return OptionContract(  # Create and return a new OptionContract instance with all parsed and processed data; this constructs the structured object that encapsulates option contract information for RemDarwin's analysis and storage.
            symbol=symbol,
            expiration_date=expiration_date,
            strike_price=strike_price,
            option_type=option_type,
            bid=bid_price,
            ask=ask_price,
            last_price=last_price,
            volume=volume,
            open_interest=open_interest,
            implied_volatility=iv,
            change=change,
            percent_change=percent_change,
            delta=greeks['delta'],
            gamma=greeks['gamma'],
            theta=greeks['theta'],
            vega=greeks['vega'],
            rho=greeks['rho'],
            prob_itm=greeks['prob_itm'],
            prob_otm=greeks['prob_otm'],
            prob_touch=greeks['prob_touch'],
            days_to_expiration=days_to_expiration,
            underlying_price=underlying_price,
            max_covered_call_return=max_covered_call_return,
            put_return_on_risk=put_return_on_risk,
            put_return_on_capital=put_return_on_capital,
            validated=False
        )

    def _validate_contract(self, contract: OptionContract) -> bool:  # Define the private validation method to check OptionContract data quality; this method applies business rules to ensure contracts are suitable for RemDarwin's quantitative analysis and trading decisions.
        """ Basic filter to ensure contract data validity before downstream processing. """
        # Basic bid-ask validation (relaxed to allow zero prices and equal bid/ask for data population)
        if (contract.bid is None or contract.ask is None or contract.ask < contract.bid or contract.bid < 0 or contract.ask < 0):  # Check for invalid bid/ask prices, allowing zero values and equal prices to populate more data for analysis.
            self.logger.debug(f"Invalid bid/ask for {contract.symbol} {contract.option_type} "
                              f"strike {contract.strike_price} exp {contract.expiration_date}")  # Log debug information for invalid bid/ask combinations; this aids in troubleshooting data quality issues in RemDarwin's validation process.
            return False  # Reject the contract due to invalid pricing data; this prevents corrupted price information from affecting RemDarwin's trading decisions.
        # Volume and Open Interest must be non-negative
        if contract.volume < 0 or contract.open_interest < 0:  # Validate that volume and open interest are non-negative; negative values indicate data errors that could mislead RemDarwin's liquidity analysis.
            self.logger.debug(f"Negative volume or open interest for {contract.symbol} "
                              f"{contract.option_type} strike {contract.strike_price}")  # Log debug info for negative trading metrics; this supports data integrity monitoring in RemDarwin's system.
            return False  # Reject contracts with invalid volume/open interest; this maintains data quality for RemDarwin's market analysis.
        # Implied Volatility must be reasonable
        if contract.implied_volatility < 0 or contract.implied_volatility > 5:  # 500% IV unlikely  # Check implied volatility is within reasonable bounds; extreme IV values may indicate data errors or extraordinary market conditions that require special handling in RemDarwin.
            self.logger.debug(f"Implied volatility out of range for {contract.symbol} "
                              f"{contract.option_type} strike {contract.strike_price}")  # Log debug info for unreasonable IV values; this enables monitoring of volatility data quality in RemDarwin's risk models.
            return False  # Reject contracts with invalid IV; this prevents unreliable volatility data from corrupting RemDarwin's pricing calculations.
        # Days to expiration must be positive and reasonable
        if contract.days_to_expiration < 0 or contract.days_to_expiration > 1000:  # Validate expiration timing is reasonable; negative days indicate expired contracts, excessive days suggest data errors in RemDarwin's temporal analysis.
            self.logger.debug(f"Invalid days to expiration for {contract.symbol} "
                              f"{contract.option_type} strike {contract.strike_price}")  # Log debug info for invalid expiration timing; this supports temporal data validation in RemDarwin's options processing.
            return False  # Reject contracts with invalid expiration; this ensures only current, valid options are processed by RemDarwin's system.
        contract.validated = True  # Mark the contract as validated; this flag indicates the contract has passed all quality checks for use in RemDarwin's downstream analysis.
        return True  # Accept the validated contract; this allows the contract to proceed to RemDarwin's quantitative analysis and trading algorithms.

    def save_to_database(self, symbol: str, option_data: dict):  # Define the method to save option contracts to a SQLite database with partitioning by expiration date; this method creates partitioned tables for each expiration, adds indexes, and inserts contracts into appropriate tables for RemDarwin's data persistence.
        """
        Saves the option data to a SQLite database with partitioning by expiration date.
        Creates partitioned tables named options_YYYY_MM_DD for each unique expiration.
        Adds indexes on symbol, expiration, strike, and each Greek after table creation.
        Uses TEXT type for all columns for simplicity.
        Unique constraint on (symbol, expiration_date, strike_price, option_type) with ON CONFLICT REPLACE.
        """
        db_name = f"{symbol}_options.db"  # Create database filename based on symbol; this ensures each stock has its own options database in RemDarwin's data organization.
        try:  # Begin exception handling for database operations; this ensures robust error handling during data persistence in RemDarwin's system.
            conn = sqlite3.connect(db_name)  # Establish connection to the SQLite database; this opens or creates the options database for the given symbol in RemDarwin's local storage.
            self.logger.info(f"Connected to database {db_name}")  # Log database connection; this confirms the save process has started.
            cursor = conn.cursor()  # Create a cursor object for executing SQL commands; this provides the interface for database operations in RemDarwin's data saving process.
            # Prepare data for insertion
            all_contracts = option_data.get('calls', []) + option_data.get('puts', [])  # Combine calls and puts contracts into a single list for processing; this enables efficient data handling across all option types in RemDarwin's database operations.
            # Collect unique expiration dates
            unique_expirations = set()
            for contract in all_contracts:
                exp_str = contract.expiration_date.strftime('%Y-%m-%d')
                unique_expirations.add(exp_str)
            # Create partitioned tables for each unique expiration
            for exp in unique_expirations:
                table_name = f"options_{exp.replace('-', '_')}"
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        symbol TEXT,
                        expiration_date TEXT,
                        strike_price TEXT,
                        option_type TEXT,
                        bid TEXT,
                        ask TEXT,
                        last_price TEXT,
                        volume TEXT,
                        open_interest TEXT,
                        implied_volatility TEXT,
                        change TEXT,
                        percent_change TEXT,
                        delta TEXT,
                        gamma TEXT,
                        theta TEXT,
                        vega TEXT,
                        rho TEXT,
                        prob_itm TEXT,
                        prob_otm TEXT,
                        prob_touch TEXT,
                        days_to_expiration TEXT,
                        underlying_price TEXT,
                        validated TEXT,
                        max_covered_call_return TEXT,
                        put_return_on_risk TEXT,
                        put_return_on_capital TEXT,
                        UNIQUE(symbol, expiration_date, strike_price, option_type) ON CONFLICT REPLACE
                    )
                ''')  # Execute table creation for each partitioned table; this sets up the database schema for storing option contract data by expiration in RemDarwin's persistent storage.
            # Add indexes on symbol, expiration, strike, and each Greek for each table
            for exp in unique_expirations:
                table_name = f"options_{exp.replace('-', '_')}"
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_symbol ON {table_name} (symbol)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_expiration ON {table_name} (expiration_date)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_strike ON {table_name} (strike_price)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_delta ON {table_name} (delta)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_gamma ON {table_name} (gamma)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_theta ON {table_name} (theta)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_vega ON {table_name} (vega)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_rho ON {table_name} (rho)')
            # Insert data into appropriate partitioned tables
            for contract in all_contracts:
                exp_str = contract.expiration_date.strftime('%Y_%m_%d')
                table_name = f"options_{exp_str}"
                values = (
                    contract.symbol,
                    str(contract.expiration_date) if contract.expiration_date else None,
                    str(contract.strike_price),
                    contract.option_type,
                    str(contract.bid),
                    str(contract.ask),
                    str(contract.last_price),
                    str(contract.volume),
                    str(contract.open_interest),
                    str(contract.implied_volatility),
                    str(contract.change),
                    str(contract.percent_change),
                    str(contract.delta),
                    str(contract.gamma),
                    str(contract.theta),
                    str(contract.vega),
                    str(contract.rho),
                    str(contract.prob_itm),
                    str(contract.prob_otm),
                    str(contract.prob_touch),
                    str(contract.days_to_expiration) if contract.days_to_expiration is not None else None,
                    str(contract.underlying_price) if contract.underlying_price is not None else None,
                    str(contract.validated),
                    str(contract.max_covered_call_return) if contract.max_covered_call_return is not None else None,
                    str(contract.put_return_on_risk) if contract.put_return_on_risk is not None else None,
                    str(contract.put_return_on_capital) if contract.put_return_on_capital is not None else None
                )  # Prepare tuple of string-converted values for database insertion; this ensures all data types are compatible with TEXT columns in RemDarwin's SQLite schema.
                cursor.execute(f'''
                    INSERT OR REPLACE INTO {table_name} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', values)  # Execute INSERT OR REPLACE into the appropriate partitioned table; this handles uniqueness constraints and ensures data is saved in RemDarwin's options database.
            conn.commit()  # Commit the partitioned table inserts; this ensures the main data is saved even if history fails.
            # Create options_history table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS options_history (
                    symbol TEXT,
                    expiration_date TEXT,
                    strike_price TEXT,
                    option_type TEXT,
                    bid TEXT,
                    ask TEXT,
                    last_price TEXT,
                    volume TEXT,
                    open_interest TEXT,
                    implied_volatility TEXT,
                    change TEXT,
                    percent_change TEXT,
                    delta TEXT,
                    gamma TEXT,
                    theta TEXT,
                    vega TEXT,
                    rho TEXT,
                    prob_itm TEXT,
                    prob_otm TEXT,
                    prob_touch TEXT,
                    days_to_expiration TEXT,
                    underlying_price TEXT,
                    validated TEXT,
                    max_covered_call_return TEXT,
                    put_return_on_risk TEXT,
                    put_return_on_capital TEXT,
                    fetch_timestamp TEXT
                )
            ''')
            # Insert all contracts into options_history with fetch_timestamp
            fetch_timestamp = str(option_data.get('fetch_timestamp', datetime.utcnow()))
            for contract in all_contracts:
                values = (
                    contract.symbol,
                    str(contract.expiration_date) if contract.expiration_date else None,
                    str(contract.strike_price),
                    contract.option_type,
                    str(contract.bid),
                    str(contract.ask),
                    str(contract.last_price),
                    str(contract.volume),
                    str(contract.open_interest),
                    str(contract.implied_volatility),
                    str(contract.change),
                    str(contract.percent_change),
                    str(contract.delta),
                    str(contract.gamma),
                    str(contract.theta),
                    str(contract.vega),
                    str(contract.rho),
                    str(contract.prob_itm),
                    str(contract.prob_otm),
                    str(contract.prob_touch),
                    str(contract.days_to_expiration) if contract.days_to_expiration is not None else None,
                    str(contract.underlying_price) if contract.underlying_price is not None else None,
                    str(contract.validated),
                    str(contract.max_covered_call_return) if contract.max_covered_call_return is not None else None,
                    str(contract.put_return_on_risk) if contract.put_return_on_risk is not None else None,
                    str(contract.put_return_on_capital) if contract.put_return_on_capital is not None else None,
                    fetch_timestamp
                )
                cursor.execute('''
                    INSERT INTO options_history VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', values)
            conn.commit()  # Commit the transaction to make changes permanent; this finalizes the database save operation in RemDarwin's data persistence process.
            self.logger.info(f"Saved {len(all_contracts)} options contracts to partitioned tables and options_history in {db_name}")  # Log successful save operation with count; this provides monitoring and confirmation of data persistence in RemDarwin's logging system.
        except Exception as e:  # Catch any exceptions during database operations; this ensures error handling for connection issues, SQL errors, or data conversion problems in RemDarwin's save functionality.
            self.logger.error(f"Failed to save options data to database for {symbol}: {e}")  # Log the error with details; this enables debugging and operational monitoring of database save failures in RemDarwin's system.
        finally:  # Ensure database connection is always closed; this prevents resource leaks and maintains clean database handling in RemDarwin's data operations.
            if 'conn' in locals():  # Check if connection was established before attempting to close; this avoids errors if connection failed to open in RemDarwin's error handling.
                conn.close()  # Close the database connection; this releases resources and completes the database interaction in RemDarwin's data saving method.

    def log_option_changes(self, symbol: str, option_data: dict):
        """
        Logs option changes to a history table.
        Creates 'option_changes' table in {symbol}_options.db with same columns as 'options' plus 'EnteredDate'.
        Inserts all contracts with today's date.
        No unique constraint.
        """
        db_name = f"{symbol}_options.db"
        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS option_changes (
                    symbol TEXT,
                    expiration_date TEXT,
                    strike_price TEXT,
                    option_type TEXT,
                    bid TEXT,
                    ask TEXT,
                    last_price TEXT,
                    volume TEXT,
                    open_interest TEXT,
                    implied_volatility TEXT,
                    change TEXT,
                    percent_change TEXT,
                    delta TEXT,
                    gamma TEXT,
                    theta TEXT,
                    vega TEXT,
                    rho TEXT,
                    prob_itm TEXT,
                    prob_otm TEXT,
                    prob_touch TEXT,
                    days_to_expiration TEXT,
                    underlying_price TEXT,
                    validated TEXT,
                    max_covered_call_return TEXT,
                    put_return_on_risk TEXT,
                    put_return_on_capital TEXT,
                    EnteredDate TEXT
                )
            ''')
            all_contracts = option_data.get('calls', []) + option_data.get('puts', [])
            today = str(datetime.now().date())
            for contract in all_contracts:
                values = (
                    contract.symbol,
                    str(contract.expiration_date) if contract.expiration_date else None,
                    str(contract.strike_price),
                    contract.option_type,
                    str(contract.bid),
                    str(contract.ask),
                    str(contract.last_price),
                    str(contract.volume),
                    str(contract.open_interest),
                    str(contract.implied_volatility),
                    str(contract.change),
                    str(contract.percent_change),
                    str(contract.delta),
                    str(contract.gamma),
                    str(contract.theta),
                    str(contract.vega),
                    str(contract.rho),
                    str(contract.prob_itm),
                    str(contract.prob_otm),
                    str(contract.prob_touch),
                    str(contract.days_to_expiration) if contract.days_to_expiration is not None else None,
                    str(contract.underlying_price) if contract.underlying_price is not None else None,
                    str(contract.validated),
                    str(contract.max_covered_call_return) if contract.max_covered_call_return is not None else None,
                    str(contract.put_return_on_risk) if contract.put_return_on_risk is not None else None,
                    str(contract.put_return_on_capital) if contract.put_return_on_capital is not None else None,
                    today
                )
                cursor.execute('''
                    INSERT INTO option_changes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', values)
            conn.commit()
            self.logger.info(f"Logged {len(all_contracts)} option changes to {db_name}")
        except Exception as e:
            self.logger.error(f"Failed to log option changes for {symbol}: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

# Example usage/demo code  # Section for demonstration and testing of the options fetching functionality; this allows standalone execution to verify RemDarwin's options data pipeline.
if __name__ == "__main__":  # Execute demo code only when script is run directly; this prevents demo execution when the module is imported by RemDarwin's main application.
    parser = argparse.ArgumentParser(description="Fetch options data for a given ticker symbol using Yahoo Finance.")  # Create argument parser for CLI support; this enables user to specify ticker via command line in RemDarwin's options fetching script.
    parser.add_argument('-t', '--ticker', required=True, help='Stock ticker symbol (e.g., AAPL)')  # Add required ticker argument; this allows dynamic specification of the stock symbol for options fetching in RemDarwin.
    parser.add_argument('--output-dir', default='./output', help='Output directory for data files')  # Add output directory argument with default; this allows specification of where to save output files in RemDarwin.
    parser.add_argument('--period', choices=['annual', 'quarterly'], default='annual', help='Financial period type')  # Add period argument with choices; this allows selection between annual and quarterly data in RemDarwin.
    parser.add_argument('--api-key', type=str, help='API key for data services')  # Add API key argument; this allows specification of API credentials for authenticated data access in RemDarwin.
    args = parser.parse_args()  # Parse command-line arguments; this processes user input for ticker symbol in RemDarwin's CLI interface.
    print(f"Parsed arguments: ticker={args.ticker}, output_dir={args.output_dir}, period={args.period}, api_key={args.api_key}")  # Print parsed arguments for verification; this provides user feedback on the parsed CLI inputs in RemDarwin.
    ticker_symbol = args.ticker.upper()  # Convert ticker to uppercase for consistency; this standardizes stock symbols in RemDarwin's data processing.
    logging.basicConfig(level=logging.INFO)  # Configure basic logging to INFO level for demo output; this enables visibility into the fetching process during RemDarwin's development and testing.
    fetcher = YFinanceOptionChainFetcher()  # Instantiate the fetcher class for options data retrieval; this creates the primary object for demonstrating RemDarwin's options fetching capabilities.
    # Fetch option chain for specified ticker
    result = fetcher.fetch_option_chain(ticker_symbol)  # Execute the main fetching method for the specified ticker options; this demonstrates RemDarwin's ability to retrieve comprehensive options data from Yahoo Finance.
    print(f"Underlying Price: {result['underlying_price']}")  # Display the fetched underlying stock price; this shows RemDarwin's integration with stock price data for options analysis.
    print(f"Total Calls fetched: {len(result['calls'])}")  # Show the count of call options retrieved; this demonstrates the volume of data RemDarwin can process for calls.
    print(f"Total Puts fetched: {len(result['puts'])}")  # Show the count of put options retrieved; this demonstrates the volume of data RemDarwin can process for puts.
    # Save to database
    fetcher.save_to_database(ticker_symbol, result)  # Save the fetched options data to the database with partitioning and indexing.
    # Print a sample contract
    if result['calls']:  # Check if calls data is available for display; this ensures safe demo output in RemDarwin's testing scenarios.
        sample_call = result['calls'][0]  # Select the first call contract as an example; this provides a concrete instance for RemDarwin's options data inspection.
        print("Sample Call:")  # Label the output for clarity; this organizes demo output in RemDarwin's development interface.
        print(sample_call)  # Display the sample call contract details; this shows the structured data format RemDarwin uses for options contracts.
    if result['puts']:  # Check if puts data is available for display; this ensures complete demo coverage in RemDarwin's testing.
        sample_put = result['puts'][0]  # Select the first put contract as an example; this complements the call example for comprehensive RemDarwin data demonstration.
        print("Sample Put:")  # Label the put output for clarity; this maintains organized demo presentation in RemDarwin's interface.
        print(sample_put)  # Display the sample put contract details; this completes the demonstration of RemDarwin's options data structure and fetching capabilities.
    if not re.match(pattern, ticker):
        raise ValueError(f"Invalid ticker symbol format: {ticker}. Must be 1-5 uppercase letters.")
    # Test validation with sample inputs (implicitly done by raising)


class YFinanceOptionChainFetcher:  # Define the YFinanceOptionChainFetcher class as the main component for fetching and processing options data from Yahoo Finance; this class encapsulates the logic for retrieving option chains, parsing data, and validating contracts, serving as the core engine for options data acquisition in RemDarwin's systematic trading system.
    def __init__(self, logger=None):  # Define the constructor method for YFinanceOptionChainFetcher, accepting an optional logger parameter; this initializes the fetcher with logging capabilities, allowing for configurable logging in RemDarwin's options data fetching operations.
        self.logger = logger or logging.getLogger(__name__)  # Assign the logger instance to the object, using the provided logger or creating a default one for this module; this enables consistent logging throughout the fetcher's operations, supporting debugging and monitoring in RemDarwin's options data pipeline.

    def fetch_option_chain(self, symbol: str):  # Define the main method to fetch the complete option chain for a given stock symbol; this method orchestrates the retrieval of all available option contracts, their parsing, validation, and organization into structured data, forming the primary interface for options data acquisition in RemDarwin's trading system.
        """
        Fetches the entire option chain (calls and puts) for the given symbol and validates basic contract data.
        Returns: Dict with 'calls' and 'puts', each a list of OptionContract instances, and 'underlying_price' of the stock.
        """
        try:  # Begin exception handling block to catch and manage errors during the options fetching process; this ensures robust operation by gracefully handling API failures, network issues, or data parsing errors, maintaining system stability in RemDarwin's data acquisition workflow.
            ticker = yf.Ticker(symbol)  # Create a Ticker object from yfinance for the specified stock symbol; this object provides access to all financial data for the stock, including options chains, serving as the primary data source interface in RemDarwin's options fetching mechanism.
            self.logger.info(f"Fetching option expirations for {symbol}")  # Log an informational message indicating the start of expiration date retrieval; this provides visibility into the fetching process, aiding in monitoring and debugging options data acquisition in RemDarwin's operational logs.
            exp_dates = ticker.options  # List of expiration date strings (YYYY-MM-DD)  # Retrieve the list of available option expiration dates from the ticker object; this collection of date strings defines the time frames for which options data will be fetched, enabling comprehensive coverage of the option chain in RemDarwin's data collection process.
            self.logger.info(f"Found {len(exp_dates)} expiration dates: {exp_dates}")  # Log the number and list of expiration dates found; this helps debug if no expirations are available.
            ic(ticker.option_chain)  # Use icecream's ic function to inspect the option_chain property of the ticker; this debugging call provides a quick view of the option chain structure, aiding in development and troubleshooting of the options data fetching logic in RemDarwin.
            all_calls = []  # Initialize an empty list to accumulate call option contracts across all expiration dates; this container will hold validated OptionContract instances for call options, enabling organized storage and processing of calls data in RemDarwin's options analysis pipeline.
            all_puts = []  # Initialize an empty list to accumulate put option contracts across all expiration dates; this container will hold validated OptionContract instances for put options, facilitating structured handling of puts data in RemDarwin's quantitative trading system.
            validation_results = []  # Initialize list to track validation results for reporting; this collects boolean outcomes of the comprehensive validation pipeline for each contract.
            try:
                hist = ticker.history(period='1d')  # Fetch the recent historical price data for the stock over the last trading day; this provides the current underlying price information needed for options valuation and moneyness calculations in RemDarwin's options analysis.
                if hist.empty:  # Check if the historical data DataFrame is empty, indicating no price data was retrieved; this handles cases where the ticker has no recent trading data, setting underlying price to None for safe processing in RemDarwin's options calculations.
                    underlying_price = None  # Set underlying_price to None when no historical data is available; this prevents invalid price values from affecting options analysis and maintains data integrity in RemDarwin's valuation models.
                else:  # If historical data is available, proceed to extract the closing price; this branch handles the normal case where price data is successfully retrieved for options pricing in RemDarwin.
                    underlying_price = hist['Close'].iloc[0]  # Extract the most recent closing price from the historical data; this provides the current underlying asset price for moneyness determination and intrinsic value calculations in RemDarwin's options framework.
                    if not underlying_price or underlying_price <= 0:  # Validate that the extracted price is positive and valid; this check ensures data quality by filtering out invalid or zero prices that could corrupt options analysis in RemDarwin.
                        self.logger.warning(f"Invalid underlying price for {symbol}: {underlying_price}")  # Log a warning for invalid prices with details; this provides visibility into data quality issues, supporting monitoring and troubleshooting in RemDarwin's data pipeline.
                        underlying_price = None  # Reset invalid price to None; this maintains consistency and prevents downstream errors from propagating through RemDarwin's options processing system.
            except Exception as e:  # Catch any exceptions during price retrieval and processing; this ensures robust error handling for network issues, API failures, or data parsing problems in RemDarwin's price fetching mechanism.
                self.logger.warning(f"Failed to fetch underlying price for {symbol}: {e}")  # Log the failure with error details; this enables debugging and operational monitoring of price data acquisition issues in RemDarwin's system.
                underlying_price = None  # Set price to None on failure; this allows the options fetching to continue without underlying price data, maintaining system resilience in RemDarwin's data processing workflow.
            for exp in exp_dates:  # Iterate over each available expiration date to fetch options chains; this loop ensures comprehensive coverage of all expiration periods, enabling complete option chain retrieval for RemDarwin's analysis across different time horizons.
                self.logger.info(f"Fetching options for expiration: {exp}")  # Log the current expiration being processed; this provides progress tracking and debugging information for options data fetching operations in RemDarwin's logging system.
                opt_chain = ticker.option_chain(exp)  # Retrieve the option chain (calls and puts) for the specific expiration date from yfinance; this fetches the raw options data that will be parsed and validated for RemDarwin's options database.
                # Process calls
                calls_count = 0
                calls_valid = 0
                for row in opt_chain.calls.itertuples():  # Iterate through each call option row in the DataFrame; this processes individual call contracts, extracting and structuring their data for RemDarwin's quantitative analysis.
                    calls_count += 1
                    contract = self._parse_option_row(row, symbol, 'call', exp, underlying_price)  # Parse the raw row data into an OptionContract instance for calls; this converts yfinance's DataFrame row into a structured object with all necessary fields for RemDarwin's options processing.
                    # Enhanced validation pipeline with comprehensive data validation
                    contract_dict = contract_to_dict(contract)
                    if validate_option_data(contract_dict):
                        greeks_dict = {k: v for k, v in contract_dict.items() if k in ['delta', 'gamma', 'theta', 'vega', 'rho']}
                        if validate_greeks(greeks_dict):
                            filled = gap_fill_missing_data(contract_dict)
                            normalized = normalize_option_data(filled)
                            contract = update_contract_from_dict(contract, normalized)
                            if self._validate_contract(contract):  # Final validation check
                                all_calls.append(contract)
                                calls_valid += 1
                                validation_results.append(True)
                            else:
                                validation_results.append(False)
                        else:
                            validation_results.append(False)
                    else:
                        validation_results.append(False)
                # Process puts
                puts_count = 0
                puts_valid = 0
                for row in opt_chain.puts.itertuples():  # Iterate through each put option row in the DataFrame; this processes individual put contracts, enabling comprehensive put option data extraction for RemDarwin's trading strategies.
                    puts_count += 1
                    contract = self._parse_option_row(row, symbol, 'put', exp, underlying_price)  # Parse the raw row data into an OptionContract instance for puts; this structures put option data into RemDarwin's standardized format for analysis and decision-making.
                    # Enhanced validation pipeline with comprehensive data validation
                    contract_dict = contract_to_dict(contract)
                    if validate_option_data(contract_dict):
                        greeks_dict = {k: v for k, v in contract_dict.items() if k in ['delta', 'gamma', 'theta', 'vega', 'rho']}
                        if validate_greeks(greeks_dict):
                            filled = gap_fill_missing_data(contract_dict)
                            normalized = normalize_option_data(filled)
                            contract = update_contract_from_dict(contract, normalized)
                            if self._validate_contract(contract):  # Final validation check
                                all_puts.append(contract)
                                puts_valid += 1
                                validation_results.append(True)
                            else:
                                validation_results.append(False)
                        else:
                            validation_results.append(False)
                    else:
                        validation_results.append(False)
                self.logger.info(f"Expiration {exp}: {calls_count} calls parsed, {calls_valid} valid; {puts_count} puts parsed, {puts_valid} valid")  # Log processing statistics for each expiration; this helps debug validation issues.
            self.logger.info(f"Fetched {len(all_calls)} calls and {len(all_puts)} puts for {symbol}")  # Log the successful completion with counts of fetched contracts; this provides summary statistics for monitoring the effectiveness of options data acquisition in RemDarwin's system.
            # Generate validation report
            report = generate_validation_report(validation_results)
            return {  # Return the complete options data structure with all fetched and validated contracts; this delivers the processed options chain data to RemDarwin's downstream analysis and trading components.
                'calls': all_calls,  # Include the list of validated call option contracts; this provides call options data for RemDarwin's call-based trading strategies and analysis.
                'puts': all_puts,  # Include the list of validated put option contracts; this provides put options data for RemDarwin's put-based trading strategies and risk management.
                'underlying_price': underlying_price,  # Include the fetched underlying stock price; this enables moneyness calculations and intrinsic value assessments in RemDarwin's options valuation models.
                'fetch_timestamp': datetime.utcnow(),  # Include the UTC timestamp of the fetch operation; this provides temporal context for data freshness and supports time-series analysis in RemDarwin's options system.
                'validation_report': report  # Include the validation report with success metrics; this provides insights into data quality and validation effectiveness for RemDarwin's monitoring.
            }
        except Exception as e:  # Catch any unhandled exceptions during the entire fetching process; this provides a safety net for unexpected errors, ensuring RemDarwin's system remains stable even with API or processing failures.
            self.logger.error(f"Failed to fetch options for {symbol}: {e}")  # Log the critical error with details; this enables debugging and alerts for system failures in RemDarwin's options data pipeline.
            return {  # Return an empty data structure on failure; this maintains API consistency while indicating that no valid options data was retrieved for RemDarwin's processing.
                'calls': [],  # Return empty list for calls on error; this prevents downstream components from attempting to process invalid data in RemDarwin's system.
                'puts': [],  # Return empty list for puts on error; this ensures safe failure handling in RemDarwin's options analysis pipeline.
                'underlying_price': None,  # Return None for price on error; this clearly indicates price unavailability to RemDarwin's valuation calculations.
                'fetch_timestamp': datetime.utcnow()  # Include timestamp even on failure; this provides timing context for error analysis in RemDarwin's monitoring and logging system.
            }

    def _parse_option_row(self, row, symbol, option_type, expiration_date_str, underlying_price):  # Define the private method to parse raw yfinance DataFrame rows into OptionContract objects; this method handles data type conversion, NaN handling, and field extraction for both call and put options in RemDarwin's data processing pipeline.
        """ Parse a row from yfinance option DataFrame into an OptionContract. """
        expiration_date = datetime.strptime(expiration_date_str, "%Y-%m-%d")  # Parse the expiration date string into a datetime object; this converts the string format from yfinance into a usable date for RemDarwin's temporal calculations and contract identification.
        days_to_expiration = (expiration_date - datetime.utcnow()).days  # Calculate the number of days until expiration from the current UTC time; this temporal metric is crucial for time value decay analysis and expiration-based strategies in RemDarwin's options framework.
        implied_vol = getattr(row, 'impliedVolatility', None)  # Extract the implied volatility value from the row, handling missing attributes gracefully; this retrieves the market's volatility expectation for pricing models in RemDarwin's options valuation.
        iv = implied_vol if implied_vol is not None else 0.0  # Set implied volatility to extracted value or default to 0.0 for missing data; this ensures a valid IV value for RemDarwin's calculations, preventing NaN propagation.

        strike = getattr(row, 'strike', 0)  # Extract the strike price from the row, defaulting to 0 if missing; this gets the key price level that determines option moneyness for RemDarwin's analysis.
        strike_price = float(strike) if not pd.isna(strike) else 0.0  # Convert strike to float if valid, otherwise use 0.0; this ensures numeric strike price data for RemDarwin's calculations, handling pandas NaN values safely.

        # Calculate option Greeks using binomial model for American options (default) if valid data is available
        if underlying_price and iv > 0:  # Check for valid underlying price and implied volatility to enable Greek calculations; this ensures RemDarwin only computes Greeks with reliable market data.
            T_years = days_to_expiration / 365.0  # Convert days to expiration to years for options calculations; this standardizes time units for RemDarwin's options valuation models.
            # Calculate each Greek individually using binomial model as default for American options
            delta = calculate_delta(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate delta using binomial model for American options
            gamma = calculate_gamma(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate gamma using binomial model for American options
            theta = calculate_theta(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate theta using binomial model for American options
            vega = calculate_vega(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate vega using binomial model for American options
            rho = calculate_rho(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate rho using binomial model for American options
            # Use Black-Scholes for probabilities (approximation for American options)
            d1 = (math.log(underlying_price / strike_price) + (0.05 - 0.0 + 0.5 * iv**2) * T_years) / (iv * math.sqrt(T_years))  # Calculate d1 for probabilities; this approximates moneyness for American options.
            d2 = d1 - iv * math.sqrt(T_years)  # Calculate d2 for probabilities
            prob_itm = norm.cdf(d2) if option_type.lower() == 'call' else norm.cdf(-d2)  # Probability in the money
            prob_otm = 1 - prob_itm  # Probability out of the money
            prob_touch = prob_itm  # Probability touching strike, approximated
            greeks = {'delta': delta, 'gamma': gamma, 'theta': theta, 'vega': vega, 'rho': rho, 'prob_itm': prob_itm, 'prob_otm': prob_otm, 'prob_touch': prob_touch}  # Build greeks dictionary with calculated values
        else:  # If insufficient data for Greek calculation, set to zero; this provides safe defaults for RemDarwin's data processing when market data is unavailable.
            greeks = {'delta': 0.0, 'gamma': 0.0, 'theta': 0.0, 'vega': 0.0, 'rho': 0.0, 'prob_itm': 0.0, 'prob_otm': 0.0, 'prob_touch': 0.0}  # Assign zero values to all Greeks when calculation is not possible; this maintains data consistency in RemDarwin's options data structure.

        bid = getattr(row, 'bid', 0)  # Extract the bid price from the row; this gets the buyer's maximum offer price for liquidity analysis in RemDarwin's options trading decisions.
        bid_price = float(bid) if not pd.isna(bid) else 0.0  # Convert bid to float if valid; this provides numeric bid data for spread calculations in RemDarwin's market analysis.

        # Calculate strategy-specific returns
        max_covered_call_return = None
        put_return_on_risk = None
        put_return_on_capital = None
        if option_type == 'call' and underlying_price is not None:
            max_covered_call_return = strike_price - underlying_price + bid_price
        elif option_type == 'put':
            if strike_price > bid_price:
                put_return_on_risk = (bid_price / (strike_price - bid_price)) * 100
            put_return_on_capital = (bid_price / strike_price) * 100

        ask = getattr(row, 'ask', 0)  # Extract the ask price from the row; this gets the seller's minimum asking price for pricing analysis in RemDarwin's options strategies.
        ask_price = float(ask) if not pd.isna(ask) else 0.0  # Convert ask to float if valid; this ensures numeric ask data for RemDarwin's spread and execution cost evaluations.

        last = getattr(row, 'lastPrice', 0)  # Extract the last traded price from the row; this provides the most recent market price for real-time analysis in RemDarwin's options monitoring.
        last_price = float(last) if not pd.isna(last) else 0.0  # Convert last price to float if valid; this gives numeric last price data for price movement tracking in RemDarwin's system.

        vol = getattr(row, 'volume', 0)  # Extract the trading volume from the row; this indicates daily trading activity for liquidity assessment in RemDarwin's options analysis.
        volume = int(vol) if not pd.isna(vol) else 0  # Convert volume to integer if valid; this provides numeric volume data for RemDarwin's market activity evaluations.

        oi = getattr(row, 'openInterest', 0)  # Extract the open interest from the row; this shows outstanding contracts for market participation analysis in RemDarwin's strategies.
        open_interest = int(oi) if not pd.isna(oi) else 0  # Convert open interest to integer if valid; this gives numeric OI data for RemDarwin's contract liquidity and positioning analysis.

        ch = getattr(row, 'change', 0)  # Extract the price change from the row; this shows daily price movement for trend analysis in RemDarwin's options strategies.
        change = float(ch) if not pd.isna(ch) else 0.0  # Convert change to float if valid; this provides numeric change data for RemDarwin's price movement tracking.

        pch = getattr(row, 'percentChange', 0)  # column for % Change  # Extract the percentage change from the row; this indicates relative price movement for comparative analysis in RemDarwin's quantitative models.
        percent_change = float(pch) if not pd.isna(pch) else 0.0  # Convert percent change to float if valid; this gives numeric percentage data for RemDarwin's relative performance evaluations.

        return OptionContract(  # Create and return a new OptionContract instance with all parsed and processed data; this constructs the structured object that encapsulates option contract information for RemDarwin's analysis and storage.
            symbol=symbol,
            expiration_date=expiration_date,
            strike_price=strike_price,
            option_type=option_type,
            bid=bid_price,
            ask=ask_price,
            last_price=last_price,
            volume=volume,
            open_interest=open_interest,
            implied_volatility=iv,
            change=change,
            percent_change=percent_change,
            delta=greeks['delta'],
            gamma=greeks['gamma'],
            theta=greeks['theta'],
            vega=greeks['vega'],
            rho=greeks['rho'],
            prob_itm=greeks['prob_itm'],
            prob_otm=greeks['prob_otm'],
            prob_touch=greeks['prob_touch'],
            days_to_expiration=days_to_expiration,
            underlying_price=underlying_price,
            max_covered_call_return=max_covered_call_return,
            put_return_on_risk=put_return_on_risk,
            put_return_on_capital=put_return_on_capital,
            validated=False
        )

    def _validate_contract(self, contract: OptionContract) -> bool:  # Define the private validation method to check OptionContract data quality; this method applies business rules to ensure contracts are suitable for RemDarwin's quantitative analysis and trading decisions.
        """ Basic filter to ensure contract data validity before downstream processing. """
        # Basic bid-ask validation (relaxed to allow zero prices and equal bid/ask for data population)
        if (contract.bid is None or contract.ask is None or contract.ask < contract.bid or contract.bid < 0 or contract.ask < 0):  # Check for invalid bid/ask prices, allowing zero values and equal prices to populate more data for analysis.
            self.logger.debug(f"Invalid bid/ask for {contract.symbol} {contract.option_type} "
                              f"strike {contract.strike_price} exp {contract.expiration_date}")  # Log debug information for invalid bid/ask combinations; this aids in troubleshooting data quality issues in RemDarwin's validation process.
            return False  # Reject the contract due to invalid pricing data; this prevents corrupted price information from affecting RemDarwin's trading decisions.
        # Volume and Open Interest must be non-negative
        if contract.volume < 0 or contract.open_interest < 0:  # Validate that volume and open interest are non-negative; negative values indicate data errors that could mislead RemDarwin's liquidity analysis.
            self.logger.debug(f"Negative volume or open interest for {contract.symbol} "
                              f"{contract.option_type} strike {contract.strike_price}")  # Log debug info for negative trading metrics; this supports data integrity monitoring in RemDarwin's system.
            return False  # Reject contracts with invalid volume/open interest; this maintains data quality for RemDarwin's market analysis.
        # Implied Volatility must be reasonable
        if contract.implied_volatility < 0 or contract.implied_volatility > 5:  # 500% IV unlikely  # Check implied volatility is within reasonable bounds; extreme IV values may indicate data errors or extraordinary market conditions that require special handling in RemDarwin.
            self.logger.debug(f"Implied volatility out of range for {contract.symbol} "
                              f"{contract.option_type} strike {contract.strike_price}")  # Log debug info for unreasonable IV values; this enables monitoring of volatility data quality in RemDarwin's risk models.
            return False  # Reject contracts with invalid IV; this prevents unreliable volatility data from corrupting RemDarwin's pricing calculations.
        # Days to expiration must be positive and reasonable
        if contract.days_to_expiration < 0 or contract.days_to_expiration > 1000:  # Validate expiration timing is reasonable; negative days indicate expired contracts, excessive days suggest data errors in RemDarwin's temporal analysis.
            self.logger.debug(f"Invalid days to expiration for {contract.symbol} "
                              f"{contract.option_type} strike {contract.strike_price}")  # Log debug info for invalid expiration timing; this supports temporal data validation in RemDarwin's options processing.
            return False  # Reject contracts with invalid expiration; this ensures only current, valid options are processed by RemDarwin's system.
        contract.validated = True  # Mark the contract as validated; this flag indicates the contract has passed all quality checks for use in RemDarwin's downstream analysis.
        return True  # Accept the validated contract; this allows the contract to proceed to RemDarwin's quantitative analysis and trading algorithms.

    def save_to_database(self, symbol: str, option_data: dict):  # Define the method to save option contracts to a SQLite database with partitioning by expiration date; this method creates partitioned tables for each expiration, adds indexes, and inserts contracts into appropriate tables for RemDarwin's data persistence.
        """
        Saves the option data to a SQLite database with partitioning by expiration date.
        Creates partitioned tables named options_YYYY_MM_DD for each unique expiration.
        Adds indexes on symbol, expiration, strike, and each Greek after table creation.
        Uses TEXT type for all columns for simplicity.
        Unique constraint on (symbol, expiration_date, strike_price, option_type) with ON CONFLICT REPLACE.
        """
        db_name = f"{symbol}_options.db"  # Create database filename based on symbol; this ensures each stock has its own options database in RemDarwin's data organization.
        try:  # Begin exception handling for database operations; this ensures robust error handling during data persistence in RemDarwin's system.
            conn = sqlite3.connect(db_name)  # Establish connection to the SQLite database; this opens or creates the options database for the given symbol in RemDarwin's local storage.
            self.logger.info(f"Connected to database {db_name}")  # Log database connection; this confirms the save process has started.
            cursor = conn.cursor()  # Create a cursor object for executing SQL commands; this provides the interface for database operations in RemDarwin's data saving process.
            # Prepare data for insertion
            all_contracts = option_data.get('calls', []) + option_data.get('puts', [])  # Combine calls and puts contracts into a single list for processing; this enables efficient data handling across all option types in RemDarwin's database operations.
            # Collect unique expiration dates
            unique_expirations = set()
            for contract in all_contracts:
                exp_str = contract.expiration_date.strftime('%Y-%m-%d')
                unique_expirations.add(exp_str)
            # Create partitioned tables for each unique expiration
            for exp in unique_expirations:
                table_name = f"options_{exp.replace('-', '_')}"
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        symbol TEXT,
                        expiration_date TEXT,
                        strike_price TEXT,
                        option_type TEXT,
                        bid TEXT,
                        ask TEXT,
                        last_price TEXT,
                        volume TEXT,
                        open_interest TEXT,
                        implied_volatility TEXT,
                        change TEXT,
                        percent_change TEXT,
                        delta TEXT,
                        gamma TEXT,
                        theta TEXT,
                        vega TEXT,
                        rho TEXT,
                        prob_itm TEXT,
                        prob_otm TEXT,
                        prob_touch TEXT,
                        days_to_expiration TEXT,
                        underlying_price TEXT,
                        validated TEXT,
                        max_covered_call_return TEXT,
                        put_return_on_risk TEXT,
                        put_return_on_capital TEXT,
                        UNIQUE(symbol, expiration_date, strike_price, option_type) ON CONFLICT REPLACE
                    )
                ''')  # Execute table creation for each partitioned table; this sets up the database schema for storing option contract data by expiration in RemDarwin's persistent storage.
            # Add indexes on symbol, expiration, strike, and each Greek for each table
            for exp in unique_expirations:
                table_name = f"options_{exp.replace('-', '_')}"
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_symbol ON {table_name} (symbol)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_expiration ON {table_name} (expiration_date)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_strike ON {table_name} (strike_price)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_delta ON {table_name} (delta)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_gamma ON {table_name} (gamma)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_theta ON {table_name} (theta)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_vega ON {table_name} (vega)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_rho ON {table_name} (rho)')
            # Insert data into appropriate partitioned tables
            for contract in all_contracts:
                exp_str = contract.expiration_date.strftime('%Y_%m_%d')
                table_name = f"options_{exp_str}"
                values = (
                    contract.symbol,
                    str(contract.expiration_date) if contract.expiration_date else None,
                    str(contract.strike_price),
                    contract.option_type,
                    str(contract.bid),
                    str(contract.ask),
                    str(contract.last_price),
                    str(contract.volume),
                    str(contract.open_interest),
                    str(contract.implied_volatility),
                    str(contract.change),
                    str(contract.percent_change),
                    str(contract.delta),
                    str(contract.gamma),
                    str(contract.theta),
                    str(contract.vega),
                    str(contract.rho),
                    str(contract.prob_itm),
                    str(contract.prob_otm),
                    str(contract.prob_touch),
                    str(contract.days_to_expiration) if contract.days_to_expiration is not None else None,
                    str(contract.underlying_price) if contract.underlying_price is not None else None,
                    str(contract.validated),
                    str(contract.max_covered_call_return) if contract.max_covered_call_return is not None else None,
                    str(contract.put_return_on_risk) if contract.put_return_on_risk is not None else None,
                    str(contract.put_return_on_capital) if contract.put_return_on_capital is not None else None
                )  # Prepare tuple of string-converted values for database insertion; this ensures all data types are compatible with TEXT columns in RemDarwin's SQLite schema.
                cursor.execute(f'''
                    INSERT OR REPLACE INTO {table_name} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', values)  # Execute INSERT OR REPLACE into the appropriate partitioned table; this handles uniqueness constraints and ensures data is saved in RemDarwin's options database.
            conn.commit()  # Commit the partitioned table inserts; this ensures the main data is saved even if history fails.
            # Create options_history table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS options_history (
                    symbol TEXT,
                    expiration_date TEXT,
                    strike_price TEXT,
                    option_type TEXT,
                    bid TEXT,
                    ask TEXT,
                    last_price TEXT,
                    volume TEXT,
                    open_interest TEXT,
                    implied_volatility TEXT,
                    change TEXT,
                    percent_change TEXT,
                    delta TEXT,
                    gamma TEXT,
                    theta TEXT,
                    vega TEXT,
                    rho TEXT,
                    prob_itm TEXT,
                    prob_otm TEXT,
                    prob_touch TEXT,
                    days_to_expiration TEXT,
                    underlying_price TEXT,
                    validated TEXT,
                    max_covered_call_return TEXT,
                    put_return_on_risk TEXT,
                    put_return_on_capital TEXT,
                    fetch_timestamp TEXT
                )
            ''')
            # Insert all contracts into options_history with fetch_timestamp
            fetch_timestamp = str(option_data.get('fetch_timestamp', datetime.utcnow()))
            for contract in all_contracts:
                values = (
                    contract.symbol,
                    str(contract.expiration_date) if contract.expiration_date else None,
                    str(contract.strike_price),
                    contract.option_type,
                    str(contract.bid),
                    str(contract.ask),
                    str(contract.last_price),
                    str(contract.volume),
                    str(contract.open_interest),
                    str(contract.implied_volatility),
                    str(contract.change),
                    str(contract.percent_change),
                    str(contract.delta),
                    str(contract.gamma),
                    str(contract.theta),
                    str(contract.vega),
                    str(contract.rho),
                    str(contract.prob_itm),
                    str(contract.prob_otm),
                    str(contract.prob_touch),
                    str(contract.days_to_expiration) if contract.days_to_expiration is not None else None,
                    str(contract.underlying_price) if contract.underlying_price is not None else None,
                    str(contract.validated),
                    str(contract.max_covered_call_return) if contract.max_covered_call_return is not None else None,
                    str(contract.put_return_on_risk) if contract.put_return_on_risk is not None else None,
                    str(contract.put_return_on_capital) if contract.put_return_on_capital is not None else None,
                    fetch_timestamp
                )
                cursor.execute('''
                    INSERT INTO options_history VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', values)
            conn.commit()  # Commit the transaction to make changes permanent; this finalizes the database save operation in RemDarwin's data persistence process.
            self.logger.info(f"Saved {len(all_contracts)} options contracts to partitioned tables and options_history in {db_name}")  # Log successful save operation with count; this provides monitoring and confirmation of data persistence in RemDarwin's logging system.
        except Exception as e:  # Catch any exceptions during database operations; this ensures error handling for connection issues, SQL errors, or data conversion problems in RemDarwin's save functionality.
            self.logger.error(f"Failed to save options data to database for {symbol}: {e}")  # Log the error with details; this enables debugging and operational monitoring of database save failures in RemDarwin's system.
        finally:  # Ensure database connection is always closed; this prevents resource leaks and maintains clean database handling in RemDarwin's data operations.
            if 'conn' in locals():  # Check if connection was established before attempting to close; this avoids errors if connection failed to open in RemDarwin's error handling.
                conn.close()  # Close the database connection; this releases resources and completes the database interaction in RemDarwin's data saving method.

    def log_option_changes(self, symbol: str, option_data: dict):
        """
        Logs option changes to a history table.
        Creates 'option_changes' table in {symbol}_options.db with same columns as 'options' plus 'EnteredDate'.
        Inserts all contracts with today's date.
        No unique constraint.
        """
        db_name = f"{symbol}_options.db"
        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS option_changes (
                    symbol TEXT,
                    expiration_date TEXT,
                    strike_price TEXT,
                    option_type TEXT,
                    bid TEXT,
                    ask TEXT,
                    last_price TEXT,
                    volume TEXT,
                    open_interest TEXT,
                    implied_volatility TEXT,
                    change TEXT,
                    percent_change TEXT,
                    delta TEXT,
                    gamma TEXT,
                    theta TEXT,
                    vega TEXT,
                    rho TEXT,
                    prob_itm TEXT,
                    prob_otm TEXT,
                    prob_touch TEXT,
                    days_to_expiration TEXT,
                    underlying_price TEXT,
                    validated TEXT,
                    max_covered_call_return TEXT,
                    put_return_on_risk TEXT,
                    put_return_on_capital TEXT,
                    EnteredDate TEXT
                )
            ''')
            all_contracts = option_data.get('calls', []) + option_data.get('puts', [])
            today = str(datetime.now().date())
            for contract in all_contracts:
                values = (
                    contract.symbol,
                    str(contract.expiration_date) if contract.expiration_date else None,
                    str(contract.strike_price),
                    contract.option_type,
                    str(contract.bid),
                    str(contract.ask),
                    str(contract.last_price),
                    str(contract.volume),
                    str(contract.open_interest),
                    str(contract.implied_volatility),
                    str(contract.change),
                    str(contract.percent_change),
                    str(contract.delta),
                    str(contract.gamma),
                    str(contract.theta),
                    str(contract.vega),
                    str(contract.rho),
                    str(contract.prob_itm),
                    str(contract.prob_otm),
                    str(contract.prob_touch),
                    str(contract.days_to_expiration) if contract.days_to_expiration is not None else None,
                    str(contract.underlying_price) if contract.underlying_price is not None else None,
                    str(contract.validated),
                    str(contract.max_covered_call_return) if contract.max_covered_call_return is not None else None,
                    str(contract.put_return_on_risk) if contract.put_return_on_risk is not None else None,
                    str(contract.put_return_on_capital) if contract.put_return_on_capital is not None else None,
                    today
                )
                cursor.execute('''
                    INSERT INTO option_changes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', values)
            conn.commit()
            self.logger.info(f"Logged {len(all_contracts)} option changes to {db_name}")
        except Exception as e:
            self.logger.error(f"Failed to log option changes for {symbol}: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

# Example usage/demo code  # Section for demonstration and testing of the options fetching functionality; this allows standalone execution to verify RemDarwin's options data pipeline.
if __name__ == "__main__":  # Execute demo code only when script is run directly; this prevents demo execution when the module is imported by RemDarwin's main application.
    parser = argparse.ArgumentParser(description="Fetch options data for a given ticker symbol using Yahoo Finance.")  # Create argument parser for CLI support; this enables user to specify ticker via command line in RemDarwin's options fetching script.
    parser.add_argument('-t', '--ticker', required=True, help='Stock ticker symbol (e.g., AAPL)')  # Add required ticker argument; this allows dynamic specification of the stock symbol for options fetching in RemDarwin.
    parser.add_argument('--output-dir', default='./output', help='Output directory for data files')  # Add output directory argument with default; this allows specification of where to save output files in RemDarwin.
    parser.add_argument('--period', choices=['annual', 'quarterly'], default='annual', help='Financial period type')  # Add period argument with choices; this allows selection between annual and quarterly data in RemDarwin.
    parser.add_argument('--api-key', type=str, help='API key for data services')  # Add API key argument; this allows specification of API credentials for authenticated data access in RemDarwin.
    args = parser.parse_args()  # Parse command-line arguments; this processes user input for ticker symbol in RemDarwin's CLI interface.
    print(f"Parsed arguments: ticker={args.ticker}, output_dir={args.output_dir}, period={args.period}, api_key={args.api_key}")  # Print parsed arguments for verification; this provides user feedback on the parsed CLI inputs in RemDarwin.
    ticker_symbol = args.ticker.upper()  # Convert ticker to uppercase for consistency; this standardizes stock symbols in RemDarwin's data processing.
    logging.basicConfig(level=logging.INFO)  # Configure basic logging to INFO level for demo output; this enables visibility into the fetching process during RemDarwin's development and testing.
    fetcher = YFinanceOptionChainFetcher()  # Instantiate the fetcher class for options data retrieval; this creates the primary object for demonstrating RemDarwin's options fetching capabilities.
    # Fetch option chain for specified ticker
    result = fetcher.fetch_option_chain(ticker_symbol)  # Execute the main fetching method for the specified ticker options; this demonstrates RemDarwin's ability to retrieve comprehensive options data from Yahoo Finance.
    print(f"Underlying Price: {result['underlying_price']}")  # Display the fetched underlying stock price; this shows RemDarwin's integration with stock price data for options analysis.
    print(f"Total Calls fetched: {len(result['calls'])}")  # Show the count of call options retrieved; this demonstrates the volume of data RemDarwin can process for calls.
    print(f"Total Puts fetched: {len(result['puts'])}")  # Show the count of put options retrieved; this demonstrates the volume of data RemDarwin can process for puts.
    # Save to database
    fetcher.save_to_database(ticker_symbol, result)  # Save the fetched options data to the database with partitioning and indexing.
    # Print a sample contract
    if result['calls']:  # Check if calls data is available for display; this ensures safe demo output in RemDarwin's testing scenarios.
        sample_call = result['calls'][0]  # Select the first call contract as an example; this provides a concrete instance for RemDarwin's options data inspection.
        print("Sample Call:")  # Label the output for clarity; this organizes demo output in RemDarwin's development interface.
        print(sample_call)  # Display the sample call contract details; this shows the structured data format RemDarwin uses for options contracts.
    if result['puts']:  # Check if puts data is available for display; this ensures complete demo coverage in RemDarwin's testing.
        sample_put = result['puts'][0]  # Select the first put contract as an example; this complements the call example for comprehensive RemDarwin data demonstration.
        print("Sample Put:")  # Label the put output for clarity; this maintains organized demo presentation in RemDarwin's interface.
        print(sample_put)  # Display the sample put contract details; this completes the demonstration of RemDarwin's options data structure and fetching capabilities.


class YFinanceOptionChainFetcher:  # Define the YFinanceOptionChainFetcher class as the main component for fetching and processing options data from Yahoo Finance; this class encapsulates the logic for retrieving option chains, parsing data, and validating contracts, serving as the core engine for options data acquisition in RemDarwin's systematic trading system.
    def __init__(self, logger=None):  # Define the constructor method for YFinanceOptionChainFetcher, accepting an optional logger parameter; this initializes the fetcher with logging capabilities, allowing for configurable logging in RemDarwin's options data fetching operations.
        self.logger = logger or logging.getLogger(__name__)  # Assign the logger instance to the object, using the provided logger or creating a default one for this module; this enables consistent logging throughout the fetcher's operations, supporting debugging and monitoring in RemDarwin's options data pipeline.

    def fetch_option_chain(self, symbol: str):  # Define the main method to fetch the complete option chain for a given stock symbol; this method orchestrates the retrieval of all available option contracts, their parsing, validation, and organization into structured data, forming the primary interface for options data acquisition in RemDarwin's trading system.
        """
        Fetches the entire option chain (calls and puts) for the given symbol and validates basic contract data.
        Returns: Dict with 'calls' and 'puts', each a list of OptionContract instances, and 'underlying_price' of the stock.
        """
        try:  # Begin exception handling block to catch and manage errors during the options fetching process; this ensures robust operation by gracefully handling API failures, network issues, or data parsing errors, maintaining system stability in RemDarwin's data acquisition workflow.
            ticker = yf.Ticker(symbol)  # Create a Ticker object from yfinance for the specified stock symbol; this object provides access to all financial data for the stock, including options chains, serving as the primary data source interface in RemDarwin's options fetching mechanism.
            self.logger.info(f"Fetching option expirations for {symbol}")  # Log an informational message indicating the start of expiration date retrieval; this provides visibility into the fetching process, aiding in monitoring and debugging options data acquisition in RemDarwin's operational logs.
            exp_dates = ticker.options  # List of expiration date strings (YYYY-MM-DD)  # Retrieve the list of available option expiration dates from the ticker object; this collection of date strings defines the time frames for which options data will be fetched, enabling comprehensive coverage of the option chain in RemDarwin's data collection process.
            self.logger.info(f"Found {len(exp_dates)} expiration dates: {exp_dates}")  # Log the number and list of expiration dates found; this helps debug if no expirations are available.
            ic(ticker.option_chain)  # Use icecream's ic function to inspect the option_chain property of the ticker; this debugging call provides a quick view of the option chain structure, aiding in development and troubleshooting of the options data fetching logic in RemDarwin.
            all_calls = []  # Initialize an empty list to accumulate call option contracts across all expiration dates; this container will hold validated OptionContract instances for call options, enabling organized storage and processing of calls data in RemDarwin's options analysis pipeline.
            all_puts = []  # Initialize an empty list to accumulate put option contracts across all expiration dates; this container will hold validated OptionContract instances for put options, facilitating structured handling of puts data in RemDarwin's quantitative trading system.
            validation_results = []  # Initialize list to track validation results for reporting; this collects boolean outcomes of the comprehensive validation pipeline for each contract.
            try:
                hist = ticker.history(period='1d')  # Fetch the recent historical price data for the stock over the last trading day; this provides the current underlying price information needed for options valuation and moneyness calculations in RemDarwin's options analysis.
                if hist.empty:  # Check if the historical data DataFrame is empty, indicating no price data was retrieved; this handles cases where the ticker has no recent trading data, setting underlying price to None for safe processing in RemDarwin's options calculations.
                    underlying_price = None  # Set underlying_price to None when no historical data is available; this prevents invalid price values from affecting options analysis and maintains data integrity in RemDarwin's valuation models.
                else:  # If historical data is available, proceed to extract the closing price; this branch handles the normal case where price data is successfully retrieved for options pricing in RemDarwin.
                    underlying_price = hist['Close'].iloc[0]  # Extract the most recent closing price from the historical data; this provides the current underlying asset price for moneyness determination and intrinsic value calculations in RemDarwin's options framework.
                    if not underlying_price or underlying_price <= 0:  # Validate that the extracted price is positive and valid; this check ensures data quality by filtering out invalid or zero prices that could corrupt options analysis in RemDarwin.
                        self.logger.warning(f"Invalid underlying price for {symbol}: {underlying_price}")  # Log a warning for invalid prices with details; this provides visibility into data quality issues, supporting monitoring and troubleshooting in RemDarwin's data pipeline.
                        underlying_price = None  # Reset invalid price to None; this maintains consistency and prevents downstream errors from propagating through RemDarwin's options processing system.
            except Exception as e:  # Catch any exceptions during price retrieval and processing; this ensures robust error handling for network issues, API failures, or data parsing problems in RemDarwin's price fetching mechanism.
                self.logger.warning(f"Failed to fetch underlying price for {symbol}: {e}")  # Log the failure with error details; this enables debugging and operational monitoring of price data acquisition issues in RemDarwin's system.
                underlying_price = None  # Set price to None on failure; this allows the options fetching to continue without underlying price data, maintaining system resilience in RemDarwin's data processing workflow.
            for exp in exp_dates:  # Iterate over each available expiration date to fetch options chains; this loop ensures comprehensive coverage of all expiration periods, enabling complete option chain retrieval for RemDarwin's analysis across different time horizons.
                self.logger.info(f"Fetching options for expiration: {exp}")  # Log the current expiration being processed; this provides progress tracking and debugging information for options data fetching operations in RemDarwin's logging system.
                opt_chain = ticker.option_chain(exp)  # Retrieve the option chain (calls and puts) for the specific expiration date from yfinance; this fetches the raw options data that will be parsed and validated for RemDarwin's options database.
                # Process calls
                calls_count = 0
                calls_valid = 0
                for row in opt_chain.calls.itertuples():  # Iterate through each call option row in the DataFrame; this processes individual call contracts, extracting and structuring their data for RemDarwin's quantitative analysis.
                    calls_count += 1
                    contract = self._parse_option_row(row, symbol, 'call', exp, underlying_price)  # Parse the raw row data into an OptionContract instance for calls; this converts yfinance's DataFrame row into a structured object with all necessary fields for RemDarwin's options processing.
                    # Enhanced validation pipeline with comprehensive data validation
                    contract_dict = contract_to_dict(contract)
                    if validate_option_data(contract_dict):
                        greeks_dict = {k: v for k, v in contract_dict.items() if k in ['delta', 'gamma', 'theta', 'vega', 'rho']}
                        if validate_greeks(greeks_dict):
                            filled = gap_fill_missing_data(contract_dict)
                            normalized = normalize_option_data(filled)
                            contract = update_contract_from_dict(contract, normalized)
                            if self._validate_contract(contract):  # Final validation check
                                all_calls.append(contract)
                                calls_valid += 1
                                validation_results.append(True)
                            else:
                                validation_results.append(False)
                        else:
                            validation_results.append(False)
                    else:
                        validation_results.append(False)
                # Process puts
                puts_count = 0
                puts_valid = 0
                for row in opt_chain.puts.itertuples():  # Iterate through each put option row in the DataFrame; this processes individual put contracts, enabling comprehensive put option data extraction for RemDarwin's trading strategies.
                    puts_count += 1
                    contract = self._parse_option_row(row, symbol, 'put', exp, underlying_price)  # Parse the raw row data into an OptionContract instance for puts; this structures put option data into RemDarwin's standardized format for analysis and decision-making.
                    # Enhanced validation pipeline with comprehensive data validation
                    contract_dict = contract_to_dict(contract)
                    if validate_option_data(contract_dict):
                        greeks_dict = {k: v for k, v in contract_dict.items() if k in ['delta', 'gamma', 'theta', 'vega', 'rho']}
                        if validate_greeks(greeks_dict):
                            filled = gap_fill_missing_data(contract_dict)
                            normalized = normalize_option_data(filled)
                            contract = update_contract_from_dict(contract, normalized)
                            if self._validate_contract(contract):  # Final validation check
                                all_puts.append(contract)
                                puts_valid += 1
                                validation_results.append(True)
                            else:
                                validation_results.append(False)
                        else:
                            validation_results.append(False)
                    else:
                        validation_results.append(False)
                self.logger.info(f"Expiration {exp}: {calls_count} calls parsed, {calls_valid} valid; {puts_count} puts parsed, {puts_valid} valid")  # Log processing statistics for each expiration; this helps debug validation issues.
            self.logger.info(f"Fetched {len(all_calls)} calls and {len(all_puts)} puts for {symbol}")  # Log the successful completion with counts of fetched contracts; this provides summary statistics for monitoring the effectiveness of options data acquisition in RemDarwin's system.
            # Generate validation report
            report = generate_validation_report(validation_results)
            return {  # Return the complete options data structure with all fetched and validated contracts; this delivers the processed options chain data to RemDarwin's downstream analysis and trading components.
                'calls': all_calls,  # Include the list of validated call option contracts; this provides call options data for RemDarwin's call-based trading strategies and analysis.
                'puts': all_puts,  # Include the list of validated put option contracts; this provides put options data for RemDarwin's put-based trading strategies and risk management.
                'underlying_price': underlying_price,  # Include the fetched underlying stock price; this enables moneyness calculations and intrinsic value assessments in RemDarwin's options valuation models.
                'fetch_timestamp': datetime.utcnow(),  # Include the UTC timestamp of the fetch operation; this provides temporal context for data freshness and supports time-series analysis in RemDarwin's options system.
                'validation_report': report  # Include the validation report with success metrics; this provides insights into data quality and validation effectiveness for RemDarwin's monitoring.
            }
        except Exception as e:  # Catch any unhandled exceptions during the entire fetching process; this provides a safety net for unexpected errors, ensuring RemDarwin's system remains stable even with API or processing failures.
            self.logger.error(f"Failed to fetch options for {symbol}: {e}")  # Log the critical error with details; this enables debugging and alerts for system failures in RemDarwin's options data pipeline.
            return {  # Return an empty data structure on failure; this maintains API consistency while indicating that no valid options data was retrieved for RemDarwin's processing.
                'calls': [],  # Return empty list for calls on error; this prevents downstream components from attempting to process invalid data in RemDarwin's system.
                'puts': [],  # Return empty list for puts on error; this ensures safe failure handling in RemDarwin's options analysis pipeline.
                'underlying_price': None,  # Return None for price on error; this clearly indicates price unavailability to RemDarwin's valuation calculations.
                'fetch_timestamp': datetime.utcnow()  # Include timestamp even on failure; this provides timing context for error analysis in RemDarwin's monitoring and logging system.
            }

    def _parse_option_row(self, row, symbol, option_type, expiration_date_str, underlying_price):  # Define the private method to parse raw yfinance DataFrame rows into OptionContract objects; this method handles data type conversion, NaN handling, and field extraction for both call and put options in RemDarwin's data processing pipeline.
        """ Parse a row from yfinance option DataFrame into an OptionContract. """
        expiration_date = datetime.strptime(expiration_date_str, "%Y-%m-%d")  # Parse the expiration date string into a datetime object; this converts the string format from yfinance into a usable date for RemDarwin's temporal calculations and contract identification.
        days_to_expiration = (expiration_date - datetime.utcnow()).days  # Calculate the number of days until expiration from the current UTC time; this temporal metric is crucial for time value decay analysis and expiration-based strategies in RemDarwin's options framework.
        implied_vol = getattr(row, 'impliedVolatility', None)  # Extract the implied volatility value from the row, handling missing attributes gracefully; this retrieves the market's volatility expectation for pricing models in RemDarwin's options valuation.
        iv = implied_vol if implied_vol is not None else 0.0  # Set implied volatility to extracted value or default to 0.0 for missing data; this ensures a valid IV value for RemDarwin's calculations, preventing NaN propagation.

        strike = getattr(row, 'strike', 0)  # Extract the strike price from the row, defaulting to 0 if missing; this gets the key price level that determines option moneyness for RemDarwin's analysis.
        strike_price = float(strike) if not pd.isna(strike) else 0.0  # Convert strike to float if valid, otherwise use 0.0; this ensures numeric strike price data for RemDarwin's calculations, handling pandas NaN values safely.

        # Calculate option Greeks using binomial model for American options (default) if valid data is available
        if underlying_price and iv > 0:  # Check for valid underlying price and implied volatility to enable Greek calculations; this ensures RemDarwin only computes Greeks with reliable market data.
            T_years = days_to_expiration / 365.0  # Convert days to expiration to years for options calculations; this standardizes time units for RemDarwin's options valuation models.
            # Calculate each Greek individually using binomial model as default for American options
            delta = calculate_delta(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate delta using binomial model for American options
            gamma = calculate_gamma(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate gamma using binomial model for American options
            theta = calculate_theta(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate theta using binomial model for American options
            vega = calculate_vega(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate vega using binomial model for American options
            rho = calculate_rho(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate rho using binomial model for American options
            # Use Black-Scholes for probabilities (approximation for American options)
            d1 = (math.log(underlying_price / strike_price) + (0.05 - 0.0 + 0.5 * iv**2) * T_years) / (iv * math.sqrt(T_years))  # Calculate d1 for probabilities; this approximates moneyness for American options.
            d2 = d1 - iv * math.sqrt(T_years)  # Calculate d2 for probabilities
            prob_itm = norm.cdf(d2) if option_type.lower() == 'call' else norm.cdf(-d2)  # Probability in the money
            prob_otm = 1 - prob_itm  # Probability out of the money
            prob_touch = prob_itm  # Probability touching strike, approximated
            greeks = {'delta': delta, 'gamma': gamma, 'theta': theta, 'vega': vega, 'rho': rho, 'prob_itm': prob_itm, 'prob_otm': prob_otm, 'prob_touch': prob_touch}  # Build greeks dictionary with calculated values
        else:  # If insufficient data for Greek calculation, set to zero; this provides safe defaults for RemDarwin's data processing when market data is unavailable.
            greeks = {'delta': 0.0, 'gamma': 0.0, 'theta': 0.0, 'vega': 0.0, 'rho': 0.0, 'prob_itm': 0.0, 'prob_otm': 0.0, 'prob_touch': 0.0}  # Assign zero values to all Greeks when calculation is not possible; this maintains data consistency in RemDarwin's options data structure.

        bid = getattr(row, 'bid', 0)  # Extract the bid price from the row; this gets the buyer's maximum offer price for liquidity analysis in RemDarwin's options trading decisions.
        bid_price = float(bid) if not pd.isna(bid) else 0.0  # Convert bid to float if valid; this provides numeric bid data for spread calculations in RemDarwin's market analysis.

        # Calculate strategy-specific returns
        max_covered_call_return = None
        put_return_on_risk = None
        put_return_on_capital = None
        if option_type == 'call' and underlying_price is not None:
            max_covered_call_return = strike_price - underlying_price + bid_price
        elif option_type == 'put':
            if strike_price > bid_price:
                put_return_on_risk = (bid_price / (strike_price - bid_price)) * 100
            put_return_on_capital = (bid_price / strike_price) * 100

        ask = getattr(row, 'ask', 0)  # Extract the ask price from the row; this gets the seller's minimum asking price for pricing analysis in RemDarwin's options strategies.
        ask_price = float(ask) if not pd.isna(ask) else 0.0  # Convert ask to float if valid; this ensures numeric ask data for RemDarwin's spread and execution cost evaluations.

        last = getattr(row, 'lastPrice', 0)  # Extract the last traded price from the row; this provides the most recent market price for real-time analysis in RemDarwin's options monitoring.
        last_price = float(last) if not pd.isna(last) else 0.0  # Convert last price to float if valid; this gives numeric last price data for price movement tracking in RemDarwin's system.

        vol = getattr(row, 'volume', 0)  # Extract the trading volume from the row; this indicates daily trading activity for liquidity assessment in RemDarwin's options analysis.
        volume = int(vol) if not pd.isna(vol) else 0  # Convert volume to integer if valid; this provides numeric volume data for RemDarwin's market activity evaluations.

        oi = getattr(row, 'openInterest', 0)  # Extract the open interest from the row; this shows outstanding contracts for market participation analysis in RemDarwin's strategies.
        open_interest = int(oi) if not pd.isna(oi) else 0  # Convert open interest to integer if valid; this gives numeric OI data for RemDarwin's contract liquidity and positioning analysis.

        ch = getattr(row, 'change', 0)  # Extract the price change from the row; this shows daily price movement for trend analysis in RemDarwin's options strategies.
        change = float(ch) if not pd.isna(ch) else 0.0  # Convert change to float if valid; this provides numeric change data for RemDarwin's price movement tracking.

        pch = getattr(row, 'percentChange', 0)  # column for % Change  # Extract the percentage change from the row; this indicates relative price movement for comparative analysis in RemDarwin's quantitative models.
        percent_change = float(pch) if not pd.isna(pch) else 0.0  # Convert percent change to float if valid; this gives numeric percentage data for RemDarwin's relative performance evaluations.

        return OptionContract(  # Create and return a new OptionContract instance with all parsed and processed data; this constructs the structured object that encapsulates option contract information for RemDarwin's analysis and storage.
            symbol=symbol,
            expiration_date=expiration_date,
            strike_price=strike_price,
            option_type=option_type,
            bid=bid_price,
            ask=ask_price,
            last_price=last_price,
            volume=volume,
            open_interest=open_interest,
            implied_volatility=iv,
            change=change,
            percent_change=percent_change,
            delta=greeks['delta'],
            gamma=greeks['gamma'],
            theta=greeks['theta'],
            vega=greeks['vega'],
            rho=greeks['rho'],
            prob_itm=greeks['prob_itm'],
            prob_otm=greeks['prob_otm'],
            prob_touch=greeks['prob_touch'],
            days_to_expiration=days_to_expiration,
            underlying_price=underlying_price,
            max_covered_call_return=max_covered_call_return,
            put_return_on_risk=put_return_on_risk,
            put_return_on_capital=put_return_on_capital,
            validated=False
        )

    def _validate_contract(self, contract: OptionContract) -> bool:  # Define the private validation method to check OptionContract data quality; this method applies business rules to ensure contracts are suitable for RemDarwin's quantitative analysis and trading decisions.
        """ Basic filter to ensure contract data validity before downstream processing. """
        # Basic bid-ask validation (relaxed to allow zero prices and equal bid/ask for data population)
        if (contract.bid is None or contract.ask is None or contract.ask < contract.bid or contract.bid < 0 or contract.ask < 0):  # Check for invalid bid/ask prices, allowing zero values and equal prices to populate more data for analysis.
            self.logger.debug(f"Invalid bid/ask for {contract.symbol} {contract.option_type} "
                              f"strike {contract.strike_price} exp {contract.expiration_date}")  # Log debug information for invalid bid/ask combinations; this aids in troubleshooting data quality issues in RemDarwin's validation process.
            return False  # Reject the contract due to invalid pricing data; this prevents corrupted price information from affecting RemDarwin's trading decisions.
        # Volume and Open Interest must be non-negative
        if contract.volume < 0 or contract.open_interest < 0:  # Validate that volume and open interest are non-negative; negative values indicate data errors that could mislead RemDarwin's liquidity analysis.
            self.logger.debug(f"Negative volume or open interest for {contract.symbol} "
                              f"{contract.option_type} strike {contract.strike_price}")  # Log debug info for negative trading metrics; this supports data integrity monitoring in RemDarwin's system.
            return False  # Reject contracts with invalid volume/open interest; this maintains data quality for RemDarwin's market analysis.
        # Implied Volatility must be reasonable
        if contract.implied_volatility < 0 or contract.implied_volatility > 5:  # 500% IV unlikely  # Check implied volatility is within reasonable bounds; extreme IV values may indicate data errors or extraordinary market conditions that require special handling in RemDarwin.
            self.logger.debug(f"Implied volatility out of range for {contract.symbol} "
                              f"{contract.option_type} strike {contract.strike_price}")  # Log debug info for unreasonable IV values; this enables monitoring of volatility data quality in RemDarwin's risk models.
            return False  # Reject contracts with invalid IV; this prevents unreliable volatility data from corrupting RemDarwin's pricing calculations.
        # Days to expiration must be positive and reasonable
        if contract.days_to_expiration < 0 or contract.days_to_expiration > 1000:  # Validate expiration timing is reasonable; negative days indicate expired contracts, excessive days suggest data errors in RemDarwin's temporal analysis.
            self.logger.debug(f"Invalid days to expiration for {contract.symbol} "
                              f"{contract.option_type} strike {contract.strike_price}")  # Log debug info for invalid expiration timing; this supports temporal data validation in RemDarwin's options processing.
            return False  # Reject contracts with invalid expiration; this ensures only current, valid options are processed by RemDarwin's system.
        contract.validated = True  # Mark the contract as validated; this flag indicates the contract has passed all quality checks for use in RemDarwin's downstream analysis.
        return True  # Accept the validated contract; this allows the contract to proceed to RemDarwin's quantitative analysis and trading algorithms.

    def save_to_database(self, symbol: str, option_data: dict):  # Define the method to save option contracts to a SQLite database with partitioning by expiration date; this method creates partitioned tables for each expiration, adds indexes, and inserts contracts into appropriate tables for RemDarwin's data persistence.
        """
        Saves the option data to a SQLite database with partitioning by expiration date.
        Creates partitioned tables named options_YYYY_MM_DD for each unique expiration.
        Adds indexes on symbol, expiration, strike, and each Greek after table creation.
        Uses TEXT type for all columns for simplicity.
        Unique constraint on (symbol, expiration_date, strike_price, option_type) with ON CONFLICT REPLACE.
        """
        db_name = f"{symbol}_options.db"  # Create database filename based on symbol; this ensures each stock has its own options database in RemDarwin's data organization.
        try:  # Begin exception handling for database operations; this ensures robust error handling during data persistence in RemDarwin's system.
            conn = sqlite3.connect(db_name)  # Establish connection to the SQLite database; this opens or creates the options database for the given symbol in RemDarwin's local storage.
            self.logger.info(f"Connected to database {db_name}")  # Log database connection; this confirms the save process has started.
            cursor = conn.cursor()  # Create a cursor object for executing SQL commands; this provides the interface for database operations in RemDarwin's data saving process.
            # Prepare data for insertion
            all_contracts = option_data.get('calls', []) + option_data.get('puts', [])  # Combine calls and puts contracts into a single list for processing; this enables efficient data handling across all option types in RemDarwin's database operations.
            # Collect unique expiration dates
            unique_expirations = set()
            for contract in all_contracts:
                exp_str = contract.expiration_date.strftime('%Y-%m-%d')
                unique_expirations.add(exp_str)
            # Create partitioned tables for each unique expiration
            for exp in unique_expirations:
                table_name = f"options_{exp.replace('-', '_')}"
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        symbol TEXT,
                        expiration_date TEXT,
                        strike_price TEXT,
                        option_type TEXT,
                        bid TEXT,
                        ask TEXT,
                        last_price TEXT,
                        volume TEXT,
                        open_interest TEXT,
                        implied_volatility TEXT,
                        change TEXT,
                        percent_change TEXT,
                        delta TEXT,
                        gamma TEXT,
                        theta TEXT,
                        vega TEXT,
                        rho TEXT,
                        prob_itm TEXT,
                        prob_otm TEXT,
                        prob_touch TEXT,
                        days_to_expiration TEXT,
                        underlying_price TEXT,
                        validated TEXT,
                        max_covered_call_return TEXT,
                        put_return_on_risk TEXT,
                        put_return_on_capital TEXT,
                        UNIQUE(symbol, expiration_date, strike_price, option_type) ON CONFLICT REPLACE
                    )
                ''')  # Execute table creation for each partitioned table; this sets up the database schema for storing option contract data by expiration in RemDarwin's persistent storage.
            # Add indexes on symbol, expiration, strike, and each Greek for each table
            for exp in unique_expirations:
                table_name = f"options_{exp.replace('-', '_')}"
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_symbol ON {table_name} (symbol)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_expiration ON {table_name} (expiration_date)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_strike ON {table_name} (strike_price)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_delta ON {table_name} (delta)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_gamma ON {table_name} (gamma)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_theta ON {table_name} (theta)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_vega ON {table_name} (vega)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_rho ON {table_name} (rho)')
            # Insert data into appropriate partitioned tables
            for contract in all_contracts:
                exp_str = contract.expiration_date.strftime('%Y_%m_%d')
                table_name = f"options_{exp_str}"
                values = (
                    contract.symbol,
                    str(contract.expiration_date) if contract.expiration_date else None,
                    str(contract.strike_price),
                    contract.option_type,
                    str(contract.bid),
                    str(contract.ask),
                    str(contract.last_price),
                    str(contract.volume),
                    str(contract.open_interest),
                    str(contract.implied_volatility),
                    str(contract.change),
                    str(contract.percent_change),
                    str(contract.delta),
                    str(contract.gamma),
                    str(contract.theta),
                    str(contract.vega),
                    str(contract.rho),
                    str(contract.prob_itm),
                    str(contract.prob_otm),
                    str(contract.prob_touch),
                    str(contract.days_to_expiration) if contract.days_to_expiration is not None else None,
                    str(contract.underlying_price) if contract.underlying_price is not None else None,
                    str(contract.validated),
                    str(contract.max_covered_call_return) if contract.max_covered_call_return is not None else None,
                    str(contract.put_return_on_risk) if contract.put_return_on_risk is not None else None,
                    str(contract.put_return_on_capital) if contract.put_return_on_capital is not None else None
                )  # Prepare tuple of string-converted values for database insertion; this ensures all data types are compatible with TEXT columns in RemDarwin's SQLite schema.
                cursor.execute(f'''
                    INSERT OR REPLACE INTO {table_name} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', values)  # Execute INSERT OR REPLACE into the appropriate partitioned table; this handles uniqueness constraints and ensures data is saved in RemDarwin's options database.
            conn.commit()  # Commit the partitioned table inserts; this ensures the main data is saved even if history fails.
            # Create options_history table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS options_history (
                    symbol TEXT,
                    expiration_date TEXT,
                    strike_price TEXT,
                    option_type TEXT,
                    bid TEXT,
                    ask TEXT,
                    last_price TEXT,
                    volume TEXT,
                    open_interest TEXT,
                    implied_volatility TEXT,
                    change TEXT,
                    percent_change TEXT,
                    delta TEXT,
                    gamma TEXT,
                    theta TEXT,
                    vega TEXT,
                    rho TEXT,
                    prob_itm TEXT,
                    prob_otm TEXT,
                    prob_touch TEXT,
                    days_to_expiration TEXT,
                    underlying_price TEXT,
                    validated TEXT,
                    max_covered_call_return TEXT,
                    put_return_on_risk TEXT,
                    put_return_on_capital TEXT,
                    fetch_timestamp TEXT
                )
            ''')
            # Insert all contracts into options_history with fetch_timestamp
            fetch_timestamp = str(option_data.get('fetch_timestamp', datetime.utcnow()))
            for contract in all_contracts:
                values = (
                    contract.symbol,
                    str(contract.expiration_date) if contract.expiration_date else None,
                    str(contract.strike_price),
                    contract.option_type,
                    str(contract.bid),
                    str(contract.ask),
                    str(contract.last_price),
                    str(contract.volume),
                    str(contract.open_interest),
                    str(contract.implied_volatility),
                    str(contract.change),
                    str(contract.percent_change),
                    str(contract.delta),
                    str(contract.gamma),
                    str(contract.theta),
                    str(contract.vega),
                    str(contract.rho),
                    str(contract.prob_itm),
                    str(contract.prob_otm),
                    str(contract.prob_touch),
                    str(contract.days_to_expiration) if contract.days_to_expiration is not None else None,
                    str(contract.underlying_price) if contract.underlying_price is not None else None,
                    str(contract.validated),
                    str(contract.max_covered_call_return) if contract.max_covered_call_return is not None else None,
                    str(contract.put_return_on_risk) if contract.put_return_on_risk is not None else None,
                    str(contract.put_return_on_capital) if contract.put_return_on_capital is not None else None,
                    fetch_timestamp
                )
                cursor.execute('''
                    INSERT INTO options_history VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', values)
            conn.commit()  # Commit the transaction to make changes permanent; this finalizes the database save operation in RemDarwin's data persistence process.
            self.logger.info(f"Saved {len(all_contracts)} options contracts to partitioned tables and options_history in {db_name}")  # Log successful save operation with count; this provides monitoring and confirmation of data persistence in RemDarwin's logging system.
        except Exception as e:  # Catch any exceptions during database operations; this ensures error handling for connection issues, SQL errors, or data conversion problems in RemDarwin's save functionality.
            self.logger.error(f"Failed to save options data to database for {symbol}: {e}")  # Log the error with details; this enables debugging and operational monitoring of database save failures in RemDarwin's system.
        finally:  # Ensure database connection is always closed; this prevents resource leaks and maintains clean database handling in RemDarwin's data operations.
            if 'conn' in locals():  # Check if connection was established before attempting to close; this avoids errors if connection failed to open in RemDarwin's error handling.
                conn.close()  # Close the database connection; this releases resources and completes the database interaction in RemDarwin's data saving method.

    def log_option_changes(self, symbol: str, option_data: dict):
        """
        Logs option changes to a history table.
        Creates 'option_changes' table in {symbol}_options.db with same columns as 'options' plus 'EnteredDate'.
        Inserts all contracts with today's date.
        No unique constraint.
        """
        db_name = f"{symbol}_options.db"
        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS option_changes (
                    symbol TEXT,
                    expiration_date TEXT,
                    strike_price TEXT,
                    option_type TEXT,
                    bid TEXT,
                    ask TEXT,
                    last_price TEXT,
                    volume TEXT,
                    open_interest TEXT,
                    implied_volatility TEXT,
                    change TEXT,
                    percent_change TEXT,
                    delta TEXT,
                    gamma TEXT,
                    theta TEXT,
                    vega TEXT,
                    rho TEXT,
                    prob_itm TEXT,
                    prob_otm TEXT,
                    prob_touch TEXT,
                    days_to_expiration TEXT,
                    underlying_price TEXT,
                    validated TEXT,
                    max_covered_call_return TEXT,
                    put_return_on_risk TEXT,
                    put_return_on_capital TEXT,
                    EnteredDate TEXT
                )
            ''')
            all_contracts = option_data.get('calls', []) + option_data.get('puts', [])
            today = str(datetime.now().date())
            for contract in all_contracts:
                values = (
                    contract.symbol,
                    str(contract.expiration_date) if contract.expiration_date else None,
                    str(contract.strike_price),
                    contract.option_type,
                    str(contract.bid),
                    str(contract.ask),
                    str(contract.last_price),
                    str(contract.volume),
                    str(contract.open_interest),
                    str(contract.implied_volatility),
                    str(contract.change),
                    str(contract.percent_change),
                    str(contract.delta),
                    str(contract.gamma),
                    str(contract.theta),
                    str(contract.vega),
                    str(contract.rho),
                    str(contract.prob_itm),
                    str(contract.prob_otm),
                    str(contract.prob_touch),
                    str(contract.days_to_expiration) if contract.days_to_expiration is not None else None,
                    str(contract.underlying_price) if contract.underlying_price is not None else None,
                    str(contract.validated),
                    str(contract.max_covered_call_return) if contract.max_covered_call_return is not None else None,
                    str(contract.put_return_on_risk) if contract.put_return_on_risk is not None else None,
                    str(contract.put_return_on_capital) if contract.put_return_on_capital is not None else None,
                    today
                )
                cursor.execute('''
                    INSERT INTO option_changes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', values)
            conn.commit()
            self.logger.info(f"Logged {len(all_contracts)} option changes to {db_name}")
        except Exception as e:
            self.logger.error(f"Failed to log option changes for {symbol}: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

# Example usage/demo code  # Section for demonstration and testing of the options fetching functionality; this allows standalone execution to verify RemDarwin's options data pipeline.
if __name__ == "__main__":  # Execute demo code only when script is run directly; this prevents demo execution when the module is imported by RemDarwin's main application.
    parser = argparse.ArgumentParser(description="Fetch options data for a given ticker symbol using Yahoo Finance.")  # Create argument parser for CLI support; this enables user to specify ticker via command line in RemDarwin's options fetching script.
    parser.add_argument('-t', '--ticker', required=True, help='Stock ticker symbol (e.g., AAPL)')  # Add required ticker argument; this allows dynamic specification of the stock symbol for options fetching in RemDarwin.
    parser.add_argument('--output-dir', default='./output', help='Output directory for data files')  # Add output directory argument with default; this allows specification of where to save output files in RemDarwin.
    parser.add_argument('--period', choices=['annual', 'quarterly'], default='annual', help='Financial period type')  # Add period argument with choices; this allows selection between annual and quarterly data in RemDarwin.
    parser.add_argument('--api-key', type=str, help='API key for data services')  # Add API key argument; this allows specification of API credentials for authenticated data access in RemDarwin.
    args = parser.parse_args()  # Parse command-line arguments; this processes user input for ticker symbol in RemDarwin's CLI interface.
    print(f"Parsed arguments: ticker={args.ticker}, output_dir={args.output_dir}, period={args.period}, api_key={args.api_key}")  # Print parsed arguments for verification; this provides user feedback on the parsed CLI inputs in RemDarwin.
    ticker_symbol = args.ticker.upper()  # Convert ticker to uppercase for consistency; this standardizes stock symbols in RemDarwin's data processing.
    logging.basicConfig(level=logging.INFO)  # Configure basic logging to INFO level for demo output; this enables visibility into the fetching process during RemDarwin's development and testing.
    fetcher = YFinanceOptionChainFetcher()  # Instantiate the fetcher class for options data retrieval; this creates the primary object for demonstrating RemDarwin's options fetching capabilities.
    # Fetch option chain for specified ticker
    result = fetcher.fetch_option_chain(ticker_symbol)  # Execute the main fetching method for the specified ticker options; this demonstrates RemDarwin's ability to retrieve comprehensive options data from Yahoo Finance.
    print(f"Underlying Price: {result['underlying_price']}")  # Display the fetched underlying stock price; this shows RemDarwin's integration with stock price data for options analysis.
    print(f"Total Calls fetched: {len(result['calls'])}")  # Show the count of call options retrieved; this demonstrates the volume of data RemDarwin can process for calls.
    print(f"Total Puts fetched: {len(result['puts'])}")  # Show the count of put options retrieved; this demonstrates the volume of data RemDarwin can process for puts.
    # Save to database
    fetcher.save_to_database(ticker_symbol, result)  # Save the fetched options data to the database with partitioning and indexing.
    # Print a sample contract
    if result['calls']:  # Check if calls data is available for display; this ensures safe demo output in RemDarwin's testing scenarios.
        sample_call = result['calls'][0]  # Select the first call contract as an example; this provides a concrete instance for RemDarwin's options data inspection.
        print("Sample Call:")  # Label the output for clarity; this organizes demo output in RemDarwin's development interface.
        print(sample_call)  # Display the sample call contract details; this shows the structured data format RemDarwin uses for options contracts.
    if result['puts']:  # Check if puts data is available for display; this ensures complete demo coverage in RemDarwin's testing.
        sample_put = result['puts'][0]  # Select the first put contract as an example; this complements the call example for comprehensive RemDarwin data demonstration.
        print("Sample Put:")  # Label the put output for clarity; this maintains organized demo presentation in RemDarwin's interface.
        print(sample_put)  # Display the sample put contract details; this completes the demonstration of RemDarwin's options data structure and fetching capabilities.
    if not re.match(pattern, ticker):
        raise ValueError(f"Invalid ticker symbol format: {ticker}. Must be 1-5 uppercase letters.")
    # Test validation with sample inputs (implicitly done by raising)


class YFinanceOptionChainFetcher:  # Define the YFinanceOptionChainFetcher class as the main component for fetching and processing options data from Yahoo Finance; this class encapsulates the logic for retrieving option chains, parsing data, and validating contracts, serving as the core engine for options data acquisition in RemDarwin's systematic trading system.
    def __init__(self, logger=None):  # Define the constructor method for YFinanceOptionChainFetcher, accepting an optional logger parameter; this initializes the fetcher with logging capabilities, allowing for configurable logging in RemDarwin's options data fetching operations.
        self.logger = logger or logging.getLogger(__name__)  # Assign the logger instance to the object, using the provided logger or creating a default one for this module; this enables consistent logging throughout the fetcher's operations, supporting debugging and monitoring in RemDarwin's options data pipeline.

    def fetch_option_chain(self, symbol: str):  # Define the main method to fetch the complete option chain for a given stock symbol; this method orchestrates the retrieval of all available option contracts, their parsing, validation, and organization into structured data, forming the primary interface for options data acquisition in RemDarwin's trading system.
        """
        Fetches the entire option chain (calls and puts) for the given symbol and validates basic contract data.
        Returns: Dict with 'calls' and 'puts', each a list of OptionContract instances, and 'underlying_price' of the stock.
        """
        try:  # Begin exception handling block to catch and manage errors during the options fetching process; this ensures robust operation by gracefully handling API failures, network issues, or data parsing errors, maintaining system stability in RemDarwin's data acquisition workflow.
            ticker = yf.Ticker(symbol)  # Create a Ticker object from yfinance for the specified stock symbol; this object provides access to all financial data for the stock, including options chains, serving as the primary data source interface in RemDarwin's options fetching mechanism.
            self.logger.info(f"Fetching option expirations for {symbol}")  # Log an informational message indicating the start of expiration date retrieval; this provides visibility into the fetching process, aiding in monitoring and debugging options data acquisition in RemDarwin's operational logs.
            exp_dates = ticker.options  # List of expiration date strings (YYYY-MM-DD)  # Retrieve the list of available option expiration dates from the ticker object; this collection of date strings defines the time frames for which options data will be fetched, enabling comprehensive coverage of the option chain in RemDarwin's data collection process.
            self.logger.info(f"Found {len(exp_dates)} expiration dates: {exp_dates}")  # Log the number and list of expiration dates found; this helps debug if no expirations are available.
            ic(ticker.option_chain)  # Use icecream's ic function to inspect the option_chain property of the ticker; this debugging call provides a quick view of the option chain structure, aiding in development and troubleshooting of the options data fetching logic in RemDarwin.
            all_calls = []  # Initialize an empty list to accumulate call option contracts across all expiration dates; this container will hold validated OptionContract instances for call options, enabling organized storage and processing of calls data in RemDarwin's options analysis pipeline.
            all_puts = []  # Initialize an empty list to accumulate put option contracts across all expiration dates; this container will hold validated OptionContract instances for put options, facilitating structured handling of puts data in RemDarwin's quantitative trading system.
            validation_results = []  # Initialize list to track validation results for reporting; this collects boolean outcomes of the comprehensive validation pipeline for each contract.
            try:
                hist = ticker.history(period='1d')  # Fetch the recent historical price data for the stock over the last trading day; this provides the current underlying price information needed for options valuation and moneyness calculations in RemDarwin's options analysis.
                if hist.empty:  # Check if the historical data DataFrame is empty, indicating no price data was retrieved; this handles cases where the ticker has no recent trading data, setting underlying price to None for safe processing in RemDarwin's options calculations.
                    underlying_price = None  # Set underlying_price to None when no historical data is available; this prevents invalid price values from affecting options analysis and maintains data integrity in RemDarwin's valuation models.
                else:  # If historical data is available, proceed to extract the closing price; this branch handles the normal case where price data is successfully retrieved for options pricing in RemDarwin.
                    underlying_price = hist['Close'].iloc[0]  # Extract the most recent closing price from the historical data; this provides the current underlying asset price for moneyness determination and intrinsic value calculations in RemDarwin's options framework.
                    if not underlying_price or underlying_price <= 0:  # Validate that the extracted price is positive and valid; this check ensures data quality by filtering out invalid or zero prices that could corrupt options analysis in RemDarwin.
                        self.logger.warning(f"Invalid underlying price for {symbol}: {underlying_price}")  # Log a warning for invalid prices with details; this provides visibility into data quality issues, supporting monitoring and troubleshooting in RemDarwin's data pipeline.
                        underlying_price = None  # Reset invalid price to None; this maintains consistency and prevents downstream errors from propagating through RemDarwin's options processing system.
            except Exception as e:  # Catch any exceptions during price retrieval and processing; this ensures robust error handling for network issues, API failures, or data parsing problems in RemDarwin's price fetching mechanism.
                self.logger.warning(f"Failed to fetch underlying price for {symbol}: {e}")  # Log the failure with error details; this enables debugging and operational monitoring of price data acquisition issues in RemDarwin's system.
                underlying_price = None  # Set price to None on failure; this allows the options fetching to continue without underlying price data, maintaining system resilience in RemDarwin's data processing workflow.
            for exp in exp_dates:  # Iterate over each available expiration date to fetch options chains; this loop ensures comprehensive coverage of all expiration periods, enabling complete option chain retrieval for RemDarwin's analysis across different time horizons.
                self.logger.info(f"Fetching options for expiration: {exp}")  # Log the current expiration being processed; this provides progress tracking and debugging information for options data fetching operations in RemDarwin's logging system.
                opt_chain = ticker.option_chain(exp)  # Retrieve the option chain (calls and puts) for the specific expiration date from yfinance; this fetches the raw options data that will be parsed and validated for RemDarwin's options database.
                # Process calls
                calls_count = 0
                calls_valid = 0
                for row in opt_chain.calls.itertuples():  # Iterate through each call option row in the DataFrame; this processes individual call contracts, extracting and structuring their data for RemDarwin's quantitative analysis.
                    calls_count += 1
                    contract = self._parse_option_row(row, symbol, 'call', exp, underlying_price)  # Parse the raw row data into an OptionContract instance for calls; this converts yfinance's DataFrame row into a structured object with all necessary fields for RemDarwin's options processing.
                    # Enhanced validation pipeline with comprehensive data validation
                    contract_dict = contract_to_dict(contract)
                    if validate_option_data(contract_dict):
                        greeks_dict = {k: v for k, v in contract_dict.items() if k in ['delta', 'gamma', 'theta', 'vega', 'rho']}
                        if validate_greeks(greeks_dict):
                            filled = gap_fill_missing_data(contract_dict)
                            normalized = normalize_option_data(filled)
                            contract = update_contract_from_dict(contract, normalized)
                            if self._validate_contract(contract):  # Final validation check
                                all_calls.append(contract)
                                calls_valid += 1
                                validation_results.append(True)
                            else:
                                validation_results.append(False)
                        else:
                            validation_results.append(False)
                    else:
                        validation_results.append(False)
                # Process puts
                puts_count = 0
                puts_valid = 0
                for row in opt_chain.puts.itertuples():  # Iterate through each put option row in the DataFrame; this processes individual put contracts, enabling comprehensive put option data extraction for RemDarwin's trading strategies.
                    puts_count += 1
                    contract = self._parse_option_row(row, symbol, 'put', exp, underlying_price)  # Parse the raw row data into an OptionContract instance for puts; this structures put option data into RemDarwin's standardized format for analysis and decision-making.
                    # Enhanced validation pipeline with comprehensive data validation
                    contract_dict = contract_to_dict(contract)
                    if validate_option_data(contract_dict):
                        greeks_dict = {k: v for k, v in contract_dict.items() if k in ['delta', 'gamma', 'theta', 'vega', 'rho']}
                        if validate_greeks(greeks_dict):
                            filled = gap_fill_missing_data(contract_dict)
                            normalized = normalize_option_data(filled)
                            contract = update_contract_from_dict(contract, normalized)
                            if self._validate_contract(contract):  # Final validation check
                                all_puts.append(contract)
                                puts_valid += 1
                                validation_results.append(True)
                            else:
                                validation_results.append(False)
                        else:
                            validation_results.append(False)
                    else:
                        validation_results.append(False)
                self.logger.info(f"Expiration {exp}: {calls_count} calls parsed, {calls_valid} valid; {puts_count} puts parsed, {puts_valid} valid")  # Log processing statistics for each expiration; this helps debug validation issues.
            self.logger.info(f"Fetched {len(all_calls)} calls and {len(all_puts)} puts for {symbol}")  # Log the successful completion with counts of fetched contracts; this provides summary statistics for monitoring the effectiveness of options data acquisition in RemDarwin's system.
            # Generate validation report
            report = generate_validation_report(validation_results)
            return {  # Return the complete options data structure with all fetched and validated contracts; this delivers the processed options chain data to RemDarwin's downstream analysis and trading components.
                'calls': all_calls,  # Include the list of validated call option contracts; this provides call options data for RemDarwin's call-based trading strategies and analysis.
                'puts': all_puts,  # Include the list of validated put option contracts; this provides put options data for RemDarwin's put-based trading strategies and risk management.
                'underlying_price': underlying_price,  # Include the fetched underlying stock price; this enables moneyness calculations and intrinsic value assessments in RemDarwin's options valuation models.
                'fetch_timestamp': datetime.utcnow(),  # Include the UTC timestamp of the fetch operation; this provides temporal context for data freshness and supports time-series analysis in RemDarwin's options system.
                'validation_report': report  # Include the validation report with success metrics; this provides insights into data quality and validation effectiveness for RemDarwin's monitoring.
            }
        except Exception as e:  # Catch any unhandled exceptions during the entire fetching process; this provides a safety net for unexpected errors, ensuring RemDarwin's system remains stable even with API or processing failures.
            self.logger.error(f"Failed to fetch options for {symbol}: {e}")  # Log the critical error with details; this enables debugging and alerts for system failures in RemDarwin's options data pipeline.
            return {  # Return an empty data structure on failure; this maintains API consistency while indicating that no valid options data was retrieved for RemDarwin's processing.
                'calls': [],  # Return empty list for calls on error; this prevents downstream components from attempting to process invalid data in RemDarwin's system.
                'puts': [],  # Return empty list for puts on error; this ensures safe failure handling in RemDarwin's options analysis pipeline.
                'underlying_price': None,  # Return None for price on error; this clearly indicates price unavailability to RemDarwin's valuation calculations.
                'fetch_timestamp': datetime.utcnow()  # Include timestamp even on failure; this provides timing context for error analysis in RemDarwin's monitoring and logging system.
            }

    def _parse_option_row(self, row, symbol, option_type, expiration_date_str, underlying_price):  # Define the private method to parse raw yfinance DataFrame rows into OptionContract objects; this method handles data type conversion, NaN handling, and field extraction for both call and put options in RemDarwin's data processing pipeline.
        """ Parse a row from yfinance option DataFrame into an OptionContract. """
        expiration_date = datetime.strptime(expiration_date_str, "%Y-%m-%d")  # Parse the expiration date string into a datetime object; this converts the string format from yfinance into a usable date for RemDarwin's temporal calculations and contract identification.
        days_to_expiration = (expiration_date - datetime.utcnow()).days  # Calculate the number of days until expiration from the current UTC time; this temporal metric is crucial for time value decay analysis and expiration-based strategies in RemDarwin's options framework.
        implied_vol = getattr(row, 'impliedVolatility', None)  # Extract the implied volatility value from the row, handling missing attributes gracefully; this retrieves the market's volatility expectation for pricing models in RemDarwin's options valuation.
        iv = implied_vol if implied_vol is not None else 0.0  # Set implied volatility to extracted value or default to 0.0 for missing data; this ensures a valid IV value for RemDarwin's calculations, preventing NaN propagation.

        strike = getattr(row, 'strike', 0)  # Extract the strike price from the row, defaulting to 0 if missing; this gets the key price level that determines option moneyness for RemDarwin's analysis.
        strike_price = float(strike) if not pd.isna(strike) else 0.0  # Convert strike to float if valid, otherwise use 0.0; this ensures numeric strike price data for RemDarwin's calculations, handling pandas NaN values safely.

        # Calculate option Greeks using binomial model for American options (default) if valid data is available
        if underlying_price and iv > 0:  # Check for valid underlying price and implied volatility to enable Greek calculations; this ensures RemDarwin only computes Greeks with reliable market data.
            T_years = days_to_expiration / 365.0  # Convert days to expiration to years for options calculations; this standardizes time units for RemDarwin's options valuation models.
            # Calculate each Greek individually using binomial model as default for American options
            delta = calculate_delta(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate delta using binomial model for American options
            gamma = calculate_gamma(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate gamma using binomial model for American options
            theta = calculate_theta(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate theta using binomial model for American options
            vega = calculate_vega(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate vega using binomial model for American options
            rho = calculate_rho(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate rho using binomial model for American options
            # Use Black-Scholes for probabilities (approximation for American options)
            d1 = (math.log(underlying_price / strike_price) + (0.05 - 0.0 + 0.5 * iv**2) * T_years) / (iv * math.sqrt(T_years))  # Calculate d1 for probabilities; this approximates moneyness for American options.
            d2 = d1 - iv * math.sqrt(T_years)  # Calculate d2 for probabilities
            prob_itm = norm.cdf(d2) if option_type.lower() == 'call' else norm.cdf(-d2)  # Probability in the money
            prob_otm = 1 - prob_itm  # Probability out of the money
            prob_touch = prob_itm  # Probability touching strike, approximated
            greeks = {'delta': delta, 'gamma': gamma, 'theta': theta, 'vega': vega, 'rho': rho, 'prob_itm': prob_itm, 'prob_otm': prob_otm, 'prob_touch': prob_touch}  # Build greeks dictionary with calculated values
        else:  # If insufficient data for Greek calculation, set to zero; this provides safe defaults for RemDarwin's data processing when market data is unavailable.
            greeks = {'delta': 0.0, 'gamma': 0.0, 'theta': 0.0, 'vega': 0.0, 'rho': 0.0, 'prob_itm': 0.0, 'prob_otm': 0.0, 'prob_touch': 0.0}  # Assign zero values to all Greeks when calculation is not possible; this maintains data consistency in RemDarwin's options data structure.

        bid = getattr(row, 'bid', 0)  # Extract the bid price from the row; this gets the buyer's maximum offer price for liquidity analysis in RemDarwin's options trading decisions.
        bid_price = float(bid) if not pd.isna(bid) else 0.0  # Convert bid to float if valid; this provides numeric bid data for spread calculations in RemDarwin's market analysis.

        # Calculate strategy-specific returns
        max_covered_call_return = None
        put_return_on_risk = None
        put_return_on_capital = None
        if option_type == 'call' and underlying_price is not None:
            max_covered_call_return = strike_price - underlying_price + bid_price
        elif option_type == 'put':
            if strike_price > bid_price:
                put_return_on_risk = (bid_price / (strike_price - bid_price)) * 100
            put_return_on_capital = (bid_price / strike_price) * 100

        ask = getattr(row, 'ask', 0)  # Extract the ask price from the row; this gets the seller's minimum asking price for pricing analysis in RemDarwin's options strategies.
        ask_price = float(ask) if not pd.isna(ask) else 0.0  # Convert ask to float if valid; this ensures numeric ask data for RemDarwin's spread and execution cost evaluations.

        last = getattr(row, 'lastPrice', 0)  # Extract the last traded price from the row; this provides the most recent market price for real-time analysis in RemDarwin's options monitoring.
        last_price = float(last) if not pd.isna(last) else 0.0  # Convert last price to float if valid; this gives numeric last price data for price movement tracking in RemDarwin's system.

        vol = getattr(row, 'volume', 0)  # Extract the trading volume from the row; this indicates daily trading activity for liquidity assessment in RemDarwin's options analysis.
        volume = int(vol) if not pd.isna(vol) else 0  # Convert volume to integer if valid; this provides numeric volume data for RemDarwin's market activity evaluations.

        oi = getattr(row, 'openInterest', 0)  # Extract the open interest from the row; this shows outstanding contracts for market participation analysis in RemDarwin's strategies.
        open_interest = int(oi) if not pd.isna(oi) else 0  # Convert open interest to integer if valid; this gives numeric OI data for RemDarwin's contract liquidity and positioning analysis.

        ch = getattr(row, 'change', 0)  # Extract the price change from the row; this shows daily price movement for trend analysis in RemDarwin's options strategies.
        change = float(ch) if not pd.isna(ch) else 0.0  # Convert change to float if valid; this provides numeric change data for RemDarwin's price movement tracking.

        pch = getattr(row, 'percentChange', 0)  # column for % Change  # Extract the percentage change from the row; this indicates relative price movement for comparative analysis in RemDarwin's quantitative models.
        percent_change = float(pch) if not pd.isna(pch) else 0.0  # Convert percent change to float if valid; this gives numeric percentage data for RemDarwin's relative performance evaluations.

        return OptionContract(  # Create and return a new OptionContract instance with all parsed and processed data; this constructs the structured object that encapsulates option contract information for RemDarwin's analysis and storage.
            symbol=symbol,
            expiration_date=expiration_date,
            strike_price=strike_price,
            option_type=option_type,
            bid=bid_price,
            ask=ask_price,
            last_price=last_price,
            volume=volume,
            open_interest=open_interest,
            implied_volatility=iv,
            change=change,
            percent_change=percent_change,
            delta=greeks['delta'],
            gamma=greeks['gamma'],
            theta=greeks['theta'],
            vega=greeks['vega'],
            rho=greeks['rho'],
            prob_itm=greeks['prob_itm'],
            prob_otm=greeks['prob_otm'],
            prob_touch=greeks['prob_touch'],
            days_to_expiration=days_to_expiration,
            underlying_price=underlying_price,
            max_covered_call_return=max_covered_call_return,
            put_return_on_risk=put_return_on_risk,
            put_return_on_capital=put_return_on_capital,
            validated=False
        )

    def _validate_contract(self, contract: OptionContract) -> bool:  # Define the private validation method to check OptionContract data quality; this method applies business rules to ensure contracts are suitable for RemDarwin's quantitative analysis and trading decisions.
        """ Basic filter to ensure contract data validity before downstream processing. """
        # Basic bid-ask validation (relaxed to allow zero prices and equal bid/ask for data population)
        if (contract.bid is None or contract.ask is None or contract.ask < contract.bid or contract.bid < 0 or contract.ask < 0):  # Check for invalid bid/ask prices, allowing zero values and equal prices to populate more data for analysis.
            self.logger.debug(f"Invalid bid/ask for {contract.symbol} {contract.option_type} "
                              f"strike {contract.strike_price} exp {contract.expiration_date}")  # Log debug information for invalid bid/ask combinations; this aids in troubleshooting data quality issues in RemDarwin's validation process.
            return False  # Reject the contract due to invalid pricing data; this prevents corrupted price information from affecting RemDarwin's trading decisions.
        # Volume and Open Interest must be non-negative
        if contract.volume < 0 or contract.open_interest < 0:  # Validate that volume and open interest are non-negative; negative values indicate data errors that could mislead RemDarwin's liquidity analysis.
            self.logger.debug(f"Negative volume or open interest for {contract.symbol} "
                              f"{contract.option_type} strike {contract.strike_price}")  # Log debug info for negative trading metrics; this supports data integrity monitoring in RemDarwin's system.
            return False  # Reject contracts with invalid volume/open interest; this maintains data quality for RemDarwin's market analysis.
        # Implied Volatility must be reasonable
        if contract.implied_volatility < 0 or contract.implied_volatility > 5:  # 500% IV unlikely  # Check implied volatility is within reasonable bounds; extreme IV values may indicate data errors or extraordinary market conditions that require special handling in RemDarwin.
            self.logger.debug(f"Implied volatility out of range for {contract.symbol} "
                              f"{contract.option_type} strike {contract.strike_price}")  # Log debug info for unreasonable IV values; this enables monitoring of volatility data quality in RemDarwin's risk models.
            return False  # Reject contracts with invalid IV; this prevents unreliable volatility data from corrupting RemDarwin's pricing calculations.
        # Days to expiration must be positive and reasonable
        if contract.days_to_expiration < 0 or contract.days_to_expiration > 1000:  # Validate expiration timing is reasonable; negative days indicate expired contracts, excessive days suggest data errors in RemDarwin's temporal analysis.
            self.logger.debug(f"Invalid days to expiration for {contract.symbol} "
                              f"{contract.option_type} strike {contract.strike_price}")  # Log debug info for invalid expiration timing; this supports temporal data validation in RemDarwin's options processing.
            return False  # Reject contracts with invalid expiration; this ensures only current, valid options are processed by RemDarwin's system.
        contract.validated = True  # Mark the contract as validated; this flag indicates the contract has passed all quality checks for use in RemDarwin's downstream analysis.
        return True  # Accept the validated contract; this allows the contract to proceed to RemDarwin's quantitative analysis and trading algorithms.

    def save_to_database(self, symbol: str, option_data: dict):  # Define the method to save option contracts to a SQLite database with partitioning by expiration date; this method creates partitioned tables for each expiration, adds indexes, and inserts contracts into appropriate tables for RemDarwin's data persistence.
        """
        Saves the option data to a SQLite database with partitioning by expiration date.
        Creates partitioned tables named options_YYYY_MM_DD for each unique expiration.
        Adds indexes on symbol, expiration, strike, and each Greek after table creation.
        Uses TEXT type for all columns for simplicity.
        Unique constraint on (symbol, expiration_date, strike_price, option_type) with ON CONFLICT REPLACE.
        """
        db_name = f"{symbol}_options.db"  # Create database filename based on symbol; this ensures each stock has its own options database in RemDarwin's data organization.
        try:  # Begin exception handling for database operations; this ensures robust error handling during data persistence in RemDarwin's system.
            conn = sqlite3.connect(db_name)  # Establish connection to the SQLite database; this opens or creates the options database for the given symbol in RemDarwin's local storage.
            self.logger.info(f"Connected to database {db_name}")  # Log database connection; this confirms the save process has started.
            cursor = conn.cursor()  # Create a cursor object for executing SQL commands; this provides the interface for database operations in RemDarwin's data saving process.
            # Prepare data for insertion
            all_contracts = option_data.get('calls', []) + option_data.get('puts', [])  # Combine calls and puts contracts into a single list for processing; this enables efficient data handling across all option types in RemDarwin's database operations.
            # Collect unique expiration dates
            unique_expirations = set()
            for contract in all_contracts:
                exp_str = contract.expiration_date.strftime('%Y-%m-%d')
                unique_expirations.add(exp_str)
            # Create partitioned tables for each unique expiration
            for exp in unique_expirations:
                table_name = f"options_{exp.replace('-', '_')}"
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        symbol TEXT,
                        expiration_date TEXT,
                        strike_price TEXT,
                        option_type TEXT,
                        bid TEXT,
                        ask TEXT,
                        last_price TEXT,
                        volume TEXT,
                        open_interest TEXT,
                        implied_volatility TEXT,
                        change TEXT,
                        percent_change TEXT,
                        delta TEXT,
                        gamma TEXT,
                        theta TEXT,
                        vega TEXT,
                        rho TEXT,
                        prob_itm TEXT,
                        prob_otm TEXT,
                        prob_touch TEXT,
                        days_to_expiration TEXT,
                        underlying_price TEXT,
                        validated TEXT,
                        max_covered_call_return TEXT,
                        put_return_on_risk TEXT,
                        put_return_on_capital TEXT,
                        UNIQUE(symbol, expiration_date, strike_price, option_type) ON CONFLICT REPLACE
                    )
                ''')  # Execute table creation for each partitioned table; this sets up the database schema for storing option contract data by expiration in RemDarwin's persistent storage.
            # Add indexes on symbol, expiration, strike, and each Greek for each table
            for exp in unique_expirations:
                table_name = f"options_{exp.replace('-', '_')}"
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_symbol ON {table_name} (symbol)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_expiration ON {table_name} (expiration_date)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_strike ON {table_name} (strike_price)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_delta ON {table_name} (delta)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_gamma ON {table_name} (gamma)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_theta ON {table_name} (theta)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_vega ON {table_name} (vega)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_rho ON {table_name} (rho)')
            # Insert data into appropriate partitioned tables
            for contract in all_contracts:
                exp_str = contract.expiration_date.strftime('%Y_%m_%d')
                table_name = f"options_{exp_str}"
                values = (
                    contract.symbol,
                    str(contract.expiration_date) if contract.expiration_date else None,
                    str(contract.strike_price),
                    contract.option_type,
                    str(contract.bid),
                    str(contract.ask),
                    str(contract.last_price),
                    str(contract.volume),
                    str(contract.open_interest),
                    str(contract.implied_volatility),
                    str(contract.change),
                    str(contract.percent_change),
                    str(contract.delta),
                    str(contract.gamma),
                    str(contract.theta),
                    str(contract.vega),
                    str(contract.rho),
                    str(contract.prob_itm),
                    str(contract.prob_otm),
                    str(contract.prob_touch),
                    str(contract.days_to_expiration) if contract.days_to_expiration is not None else None,
                    str(contract.underlying_price) if contract.underlying_price is not None else None,
                    str(contract.validated),
                    str(contract.max_covered_call_return) if contract.max_covered_call_return is not None else None,
                    str(contract.put_return_on_risk) if contract.put_return_on_risk is not None else None,
                    str(contract.put_return_on_capital) if contract.put_return_on_capital is not None else None
                )  # Prepare tuple of string-converted values for database insertion; this ensures all data types are compatible with TEXT columns in RemDarwin's SQLite schema.
                cursor.execute(f'''
                    INSERT OR REPLACE INTO {table_name} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', values)  # Execute INSERT OR REPLACE into the appropriate partitioned table; this handles uniqueness constraints and ensures data is saved in RemDarwin's options database.
            conn.commit()  # Commit the partitioned table inserts; this ensures the main data is saved even if history fails.
            # Create options_history table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS options_history (
                    symbol TEXT,
                    expiration_date TEXT,
                    strike_price TEXT,
                    option_type TEXT,
                    bid TEXT,
                    ask TEXT,
                    last_price TEXT,
                    volume TEXT,
                    open_interest TEXT,
                    implied_volatility TEXT,
                    change TEXT,
                    percent_change TEXT,
                    delta TEXT,
                    gamma TEXT,
                    theta TEXT,
                    vega TEXT,
                    rho TEXT,
                    prob_itm TEXT,
                    prob_otm TEXT,
                    prob_touch TEXT,
                    days_to_expiration TEXT,
                    underlying_price TEXT,
                    validated TEXT,
                    max_covered_call_return TEXT,
                    put_return_on_risk TEXT,
                    put_return_on_capital TEXT,
                    fetch_timestamp TEXT
                )
            ''')
            # Insert all contracts into options_history with fetch_timestamp
            fetch_timestamp = str(option_data.get('fetch_timestamp', datetime.utcnow()))
            for contract in all_contracts:
                values = (
                    contract.symbol,
                    str(contract.expiration_date) if contract.expiration_date else None,
                    str(contract.strike_price),
                    contract.option_type,
                    str(contract.bid),
                    str(contract.ask),
                    str(contract.last_price),
                    str(contract.volume),
                    str(contract.open_interest),
                    str(contract.implied_volatility),
                    str(contract.change),
                    str(contract.percent_change),
                    str(contract.delta),
                    str(contract.gamma),
                    str(contract.theta),
                    str(contract.vega),
                    str(contract.rho),
                    str(contract.prob_itm),
                    str(contract.prob_otm),
                    str(contract.prob_touch),
                    str(contract.days_to_expiration) if contract.days_to_expiration is not None else None,
                    str(contract.underlying_price) if contract.underlying_price is not None else None,
                    str(contract.validated),
                    str(contract.max_covered_call_return) if contract.max_covered_call_return is not None else None,
                    str(contract.put_return_on_risk) if contract.put_return_on_risk is not None else None,
                    str(contract.put_return_on_capital) if contract.put_return_on_capital is not None else None,
                    fetch_timestamp
                )
                cursor.execute('''
                    INSERT INTO options_history VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', values)
            conn.commit()  # Commit the transaction to make changes permanent; this finalizes the database save operation in RemDarwin's data persistence process.
            self.logger.info(f"Saved {len(all_contracts)} options contracts to partitioned tables and options_history in {db_name}")  # Log successful save operation with count; this provides monitoring and confirmation of data persistence in RemDarwin's logging system.
        except Exception as e:  # Catch any exceptions during database operations; this ensures error handling for connection issues, SQL errors, or data conversion problems in RemDarwin's save functionality.
            self.logger.error(f"Failed to save options data to database for {symbol}: {e}")  # Log the error with details; this enables debugging and operational monitoring of database save failures in RemDarwin's system.
        finally:  # Ensure database connection is always closed; this prevents resource leaks and maintains clean database handling in RemDarwin's data operations.
            if 'conn' in locals():  # Check if connection was established before attempting to close; this avoids errors if connection failed to open in RemDarwin's error handling.
                conn.close()  # Close the database connection; this releases resources and completes the database interaction in RemDarwin's data saving method.

    def log_option_changes(self, symbol: str, option_data: dict):
        """
        Logs option changes to a history table.
        Creates 'option_changes' table in {symbol}_options.db with same columns as 'options' plus 'EnteredDate'.
        Inserts all contracts with today's date.
        No unique constraint.
        """
        db_name = f"{symbol}_options.db"
        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS option_changes (
                    symbol TEXT,
                    expiration_date TEXT,
                    strike_price TEXT,
                    option_type TEXT,
                    bid TEXT,
                    ask TEXT,
                    last_price TEXT,
                    volume TEXT,
                    open_interest TEXT,
                    implied_volatility TEXT,
                    change TEXT,
                    percent_change TEXT,
                    delta TEXT,
                    gamma TEXT,
                    theta TEXT,
                    vega TEXT,
                    rho TEXT,
                    prob_itm TEXT,
                    prob_otm TEXT,
                    prob_touch TEXT,
                    days_to_expiration TEXT,
                    underlying_price TEXT,
                    validated TEXT,
                    max_covered_call_return TEXT,
                    put_return_on_risk TEXT,
                    put_return_on_capital TEXT,
                    EnteredDate TEXT
                )
            ''')
            all_contracts = option_data.get('calls', []) + option_data.get('puts', [])
            today = str(datetime.now().date())
            for contract in all_contracts:
                values = (
                    contract.symbol,
                    str(contract.expiration_date) if contract.expiration_date else None,
                    str(contract.strike_price),
                    contract.option_type,
                    str(contract.bid),
                    str(contract.ask),
                    str(contract.last_price),
                    str(contract.volume),
                    str(contract.open_interest),
                    str(contract.implied_volatility),
                    str(contract.change),
                    str(contract.percent_change),
                    str(contract.delta),
                    str(contract.gamma),
                    str(contract.theta),
                    str(contract.vega),
                    str(contract.rho),
                    str(contract.prob_itm),
                    str(contract.prob_otm),
                    str(contract.prob_touch),
                    str(contract.days_to_expiration) if contract.days_to_expiration is not None else None,
                    str(contract.underlying_price) if contract.underlying_price is not None else None,
                    str(contract.validated),
                    str(contract.max_covered_call_return) if contract.max_covered_call_return is not None else None,
                    str(contract.put_return_on_risk) if contract.put_return_on_risk is not None else None,
                    str(contract.put_return_on_capital) if contract.put_return_on_capital is not None else None,
                    today
                )
                cursor.execute('''
                    INSERT INTO option_changes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', values)
            conn.commit()
            self.logger.info(f"Logged {len(all_contracts)} option changes to {db_name}")
        except Exception as e:
            self.logger.error(f"Failed to log option changes for {symbol}: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

# Example usage/demo code  # Section for demonstration and testing of the options fetching functionality; this allows standalone execution to verify RemDarwin's options data pipeline.
if __name__ == "__main__":  # Execute demo code only when script is run directly; this prevents demo execution when the module is imported by RemDarwin's main application.
    parser = argparse.ArgumentParser(description="Fetch options data for a given ticker symbol using Yahoo Finance.")  # Create argument parser for CLI support; this enables user to specify ticker via command line in RemDarwin's options fetching script.
    parser.add_argument('-t', '--ticker', required=True, help='Stock ticker symbol (e.g., AAPL)')  # Add required ticker argument; this allows dynamic specification of the stock symbol for options fetching in RemDarwin.
    parser.add_argument('--output-dir', default='./output', help='Output directory for data files')  # Add output directory argument with default; this allows specification of where to save output files in RemDarwin.
    parser.add_argument('--period', choices=['annual', 'quarterly'], default='annual', help='Financial period type')  # Add period argument with choices; this allows selection between annual and quarterly data in RemDarwin.
    parser.add_argument('--api-key', type=str, help='API key for data services')  # Add API key argument; this allows specification of API credentials for authenticated data access in RemDarwin.
    args = parser.parse_args()  # Parse command-line arguments; this processes user input for ticker symbol in RemDarwin's CLI interface.
    print(f"Parsed arguments: ticker={args.ticker}, output_dir={args.output_dir}, period={args.period}, api_key={args.api_key}")  # Print parsed arguments for verification; this provides user feedback on the parsed CLI inputs in RemDarwin.
    ticker_symbol = args.ticker.upper()  # Convert ticker to uppercase for consistency; this standardizes stock symbols in RemDarwin's data processing.
    logging.basicConfig(level=logging.INFO)  # Configure basic logging to INFO level for demo output; this enables visibility into the fetching process during RemDarwin's development and testing.
    fetcher = YFinanceOptionChainFetcher()  # Instantiate the fetcher class for options data retrieval; this creates the primary object for demonstrating RemDarwin's options fetching capabilities.
    # Fetch option chain for specified ticker
    result = fetcher.fetch_option_chain(ticker_symbol)  # Execute the main fetching method for the specified ticker options; this demonstrates RemDarwin's ability to retrieve comprehensive options data from Yahoo Finance.
    print(f"Underlying Price: {result['underlying_price']}")  # Display the fetched underlying stock price; this shows RemDarwin's integration with stock price data for options analysis.
    print(f"Total Calls fetched: {len(result['calls'])}")  # Show the count of call options retrieved; this demonstrates the volume of data RemDarwin can process for calls.
    print(f"Total Puts fetched: {len(result['puts'])}")  # Show the count of put options retrieved; this demonstrates the volume of data RemDarwin can process for puts.
    # Save to database
    fetcher.save_to_database(ticker_symbol, result)  # Save the fetched options data to the database with partitioning and indexing.
    # Print a sample contract
    if result['calls']:  # Check if calls data is available for display; this ensures safe demo output in RemDarwin's testing scenarios.
        sample_call = result['calls'][0]  # Select the first call contract as an example; this provides a concrete instance for RemDarwin's options data inspection.
        print("Sample Call:")  # Label the output for clarity; this organizes demo output in RemDarwin's development interface.
        print(sample_call)  # Display the sample call contract details; this shows the structured data format RemDarwin uses for options contracts.
    if result['puts']:  # Check if puts data is available for display; this ensures complete demo coverage in RemDarwin's testing.
        sample_put = result['puts'][0]  # Select the first put contract as an example; this complements the call example for comprehensive RemDarwin data demonstration.
        print("Sample Put:")  # Label the put output for clarity; this maintains organized demo presentation in RemDarwin's interface.
        print(sample_put)  # Display the sample put contract details; this completes the demonstration of RemDarwin's options data structure and fetching capabilities.


class YFinanceOptionChainFetcher:  # Define the YFinanceOptionChainFetcher class as the main component for fetching and processing options data from Yahoo Finance; this class encapsulates the logic for retrieving option chains, parsing data, and validating contracts, serving as the core engine for options data acquisition in RemDarwin's systematic trading system.
    def __init__(self, logger=None):  # Define the constructor method for YFinanceOptionChainFetcher, accepting an optional logger parameter; this initializes the fetcher with logging capabilities, allowing for configurable logging in RemDarwin's options data fetching operations.
        self.logger = logger or logging.getLogger(__name__)  # Assign the logger instance to the object, using the provided logger or creating a default one for this module; this enables consistent logging throughout the fetcher's operations, supporting debugging and monitoring in RemDarwin's options data pipeline.

    def fetch_option_chain(self, symbol: str):  # Define the main method to fetch the complete option chain for a given stock symbol; this method orchestrates the retrieval of all available option contracts, their parsing, validation, and organization into structured data, forming the primary interface for options data acquisition in RemDarwin's trading system.
        """
        Fetches the entire option chain (calls and puts) for the given symbol and validates basic contract data.
        Returns: Dict with 'calls' and 'puts', each a list of OptionContract instances, and 'underlying_price' of the stock.
        """
        try:  # Begin exception handling block to catch and manage errors during the options fetching process; this ensures robust operation by gracefully handling API failures, network issues, or data parsing errors, maintaining system stability in RemDarwin's data acquisition workflow.
            ticker = yf.Ticker(symbol)  # Create a Ticker object from yfinance for the specified stock symbol; this object provides access to all financial data for the stock, including options chains, serving as the primary data source interface in RemDarwin's options fetching mechanism.
            self.logger.info(f"Fetching option expirations for {symbol}")  # Log an informational message indicating the start of expiration date retrieval; this provides visibility into the fetching process, aiding in monitoring and debugging options data acquisition in RemDarwin's operational logs.
            exp_dates = ticker.options  # List of expiration date strings (YYYY-MM-DD)  # Retrieve the list of available option expiration dates from the ticker object; this collection of date strings defines the time frames for which options data will be fetched, enabling comprehensive coverage of the option chain in RemDarwin's data collection process.
            self.logger.info(f"Found {len(exp_dates)} expiration dates: {exp_dates}")  # Log the number and list of expiration dates found; this helps debug if no expirations are available.
            ic(ticker.option_chain)  # Use icecream's ic function to inspect the option_chain property of the ticker; this debugging call provides a quick view of the option chain structure, aiding in development and troubleshooting of the options data fetching logic in RemDarwin.
            all_calls = []  # Initialize an empty list to accumulate call option contracts across all expiration dates; this container will hold validated OptionContract instances for call options, enabling organized storage and processing of calls data in RemDarwin's options analysis pipeline.
            all_puts = []  # Initialize an empty list to accumulate put option contracts across all expiration dates; this container will hold validated OptionContract instances for put options, facilitating structured handling of puts data in RemDarwin's quantitative trading system.
            validation_results = []  # Initialize list to track validation results for reporting; this collects boolean outcomes of the comprehensive validation pipeline for each contract.
            try:
                hist = ticker.history(period='1d')  # Fetch the recent historical price data for the stock over the last trading day; this provides the current underlying price information needed for options valuation and moneyness calculations in RemDarwin's options analysis.
                if hist.empty:  # Check if the historical data DataFrame is empty, indicating no price data was retrieved; this handles cases where the ticker has no recent trading data, setting underlying price to None for safe processing in RemDarwin's options calculations.
                    underlying_price = None  # Set underlying_price to None when no historical data is available; this prevents invalid price values from affecting options analysis and maintains data integrity in RemDarwin's valuation models.
                else:  # If historical data is available, proceed to extract the closing price; this branch handles the normal case where price data is successfully retrieved for options pricing in RemDarwin.
                    underlying_price = hist['Close'].iloc[0]  # Extract the most recent closing price from the historical data; this provides the current underlying asset price for moneyness determination and intrinsic value calculations in RemDarwin's options framework.
                    if not underlying_price or underlying_price <= 0:  # Validate that the extracted price is positive and valid; this check ensures data quality by filtering out invalid or zero prices that could corrupt options analysis in RemDarwin.
                        self.logger.warning(f"Invalid underlying price for {symbol}: {underlying_price}")  # Log a warning for invalid prices with details; this provides visibility into data quality issues, supporting monitoring and troubleshooting in RemDarwin's data pipeline.
                        underlying_price = None  # Reset invalid price to None; this maintains consistency and prevents downstream errors from propagating through RemDarwin's options processing system.
            except Exception as e:  # Catch any exceptions during price retrieval and processing; this ensures robust error handling for network issues, API failures, or data parsing problems in RemDarwin's price fetching mechanism.
                self.logger.warning(f"Failed to fetch underlying price for {symbol}: {e}")  # Log the failure with error details; this enables debugging and operational monitoring of price data acquisition issues in RemDarwin's system.
                underlying_price = None  # Set price to None on failure; this allows the options fetching to continue without underlying price data, maintaining system resilience in RemDarwin's data processing workflow.
            for exp in exp_dates:  # Iterate over each available expiration date to fetch options chains; this loop ensures comprehensive coverage of all expiration periods, enabling complete option chain retrieval for RemDarwin's analysis across different time horizons.
                self.logger.info(f"Fetching options for expiration: {exp}")  # Log the current expiration being processed; this provides progress tracking and debugging information for options data fetching operations in RemDarwin's logging system.
                opt_chain = ticker.option_chain(exp)  # Retrieve the option chain (calls and puts) for the specific expiration date from yfinance; this fetches the raw options data that will be parsed and validated for RemDarwin's options database.
                # Process calls
                calls_count = 0
                calls_valid = 0
                for row in opt_chain.calls.itertuples():  # Iterate through each call option row in the DataFrame; this processes individual call contracts, extracting and structuring their data for RemDarwin's quantitative analysis.
                    calls_count += 1
                    contract = self._parse_option_row(row, symbol, 'call', exp, underlying_price)  # Parse the raw row data into an OptionContract instance for calls; this converts yfinance's DataFrame row into a structured object with all necessary fields for RemDarwin's options processing.
                    # Enhanced validation pipeline with comprehensive data validation
                    contract_dict = contract_to_dict(contract)
                    if validate_option_data(contract_dict):
                        greeks_dict = {k: v for k, v in contract_dict.items() if k in ['delta', 'gamma', 'theta', 'vega', 'rho']}
                        if validate_greeks(greeks_dict):
                            filled = gap_fill_missing_data(contract_dict)
                            normalized = normalize_option_data(filled)
                            contract = update_contract_from_dict(contract, normalized)
                            if self._validate_contract(contract):  # Final validation check
                                all_calls.append(contract)
                                calls_valid += 1
                                validation_results.append(True)
                            else:
                                validation_results.append(False)
                        else:
                            validation_results.append(False)
                    else:
                        validation_results.append(False)
                # Process puts
                puts_count = 0
                puts_valid = 0
                for row in opt_chain.puts.itertuples():  # Iterate through each put option row in the DataFrame; this processes individual put contracts, enabling comprehensive put option data extraction for RemDarwin's trading strategies.
                    puts_count += 1
                    contract = self._parse_option_row(row, symbol, 'put', exp, underlying_price)  # Parse the raw row data into an OptionContract instance for puts; this structures put option data into RemDarwin's standardized format for analysis and decision-making.
                    # Enhanced validation pipeline with comprehensive data validation
                    contract_dict = contract_to_dict(contract)
                    if validate_option_data(contract_dict):
                        greeks_dict = {k: v for k, v in contract_dict.items() if k in ['delta', 'gamma', 'theta', 'vega', 'rho']}
                        if validate_greeks(greeks_dict):
                            filled = gap_fill_missing_data(contract_dict)
                            normalized = normalize_option_data(filled)
                            contract = update_contract_from_dict(contract, normalized)
                            if self._validate_contract(contract):  # Final validation check
                                all_puts.append(contract)
                                puts_valid += 1
                                validation_results.append(True)
                            else:
                                validation_results.append(False)
                        else:
                            validation_results.append(False)
                    else:
                        validation_results.append(False)
                self.logger.info(f"Expiration {exp}: {calls_count} calls parsed, {calls_valid} valid; {puts_count} puts parsed, {puts_valid} valid")  # Log processing statistics for each expiration; this helps debug validation issues.
            self.logger.info(f"Fetched {len(all_calls)} calls and {len(all_puts)} puts for {symbol}")  # Log the successful completion with counts of fetched contracts; this provides summary statistics for monitoring the effectiveness of options data acquisition in RemDarwin's system.
            # Generate validation report
            report = generate_validation_report(validation_results)
            return {  # Return the complete options data structure with all fetched and validated contracts; this delivers the processed options chain data to RemDarwin's downstream analysis and trading components.
                'calls': all_calls,  # Include the list of validated call option contracts; this provides call options data for RemDarwin's call-based trading strategies and analysis.
                'puts': all_puts,  # Include the list of validated put option contracts; this provides put options data for RemDarwin's put-based trading strategies and risk management.
                'underlying_price': underlying_price,  # Include the fetched underlying stock price; this enables moneyness calculations and intrinsic value assessments in RemDarwin's options valuation models.
                'fetch_timestamp': datetime.utcnow(),  # Include the UTC timestamp of the fetch operation; this provides temporal context for data freshness and supports time-series analysis in RemDarwin's options system.
                'validation_report': report  # Include the validation report with success metrics; this provides insights into data quality and validation effectiveness for RemDarwin's monitoring.
            }
        except Exception as e:  # Catch any unhandled exceptions during the entire fetching process; this provides a safety net for unexpected errors, ensuring RemDarwin's system remains stable even with API or processing failures.
            self.logger.error(f"Failed to fetch options for {symbol}: {e}")  # Log the critical error with details; this enables debugging and alerts for system failures in RemDarwin's options data pipeline.
            return {  # Return an empty data structure on failure; this maintains API consistency while indicating that no valid options data was retrieved for RemDarwin's processing.
                'calls': [],  # Return empty list for calls on error; this prevents downstream components from attempting to process invalid data in RemDarwin's system.
                'puts': [],  # Return empty list for puts on error; this ensures safe failure handling in RemDarwin's options analysis pipeline.
                'underlying_price': None,  # Return None for price on error; this clearly indicates price unavailability to RemDarwin's valuation calculations.
                'fetch_timestamp': datetime.utcnow()  # Include timestamp even on failure; this provides timing context for error analysis in RemDarwin's monitoring and logging system.
            }

    def _parse_option_row(self, row, symbol, option_type, expiration_date_str, underlying_price):  # Define the private method to parse raw yfinance DataFrame rows into OptionContract objects; this method handles data type conversion, NaN handling, and field extraction for both call and put options in RemDarwin's data processing pipeline.
        """ Parse a row from yfinance option DataFrame into an OptionContract. """
        expiration_date = datetime.strptime(expiration_date_str, "%Y-%m-%d")  # Parse the expiration date string into a datetime object; this converts the string format from yfinance into a usable date for RemDarwin's temporal calculations and contract identification.
        days_to_expiration = (expiration_date - datetime.utcnow()).days  # Calculate the number of days until expiration from the current UTC time; this temporal metric is crucial for time value decay analysis and expiration-based strategies in RemDarwin's options framework.
        implied_vol = getattr(row, 'impliedVolatility', None)  # Extract the implied volatility value from the row, handling missing attributes gracefully; this retrieves the market's volatility expectation for pricing models in RemDarwin's options valuation.
        iv = implied_vol if implied_vol is not None else 0.0  # Set implied volatility to extracted value or default to 0.0 for missing data; this ensures a valid IV value for RemDarwin's calculations, preventing NaN propagation.

        strike = getattr(row, 'strike', 0)  # Extract the strike price from the row, defaulting to 0 if missing; this gets the key price level that determines option moneyness for RemDarwin's analysis.
        strike_price = float(strike) if not pd.isna(strike) else 0.0  # Convert strike to float if valid, otherwise use 0.0; this ensures numeric strike price data for RemDarwin's calculations, handling pandas NaN values safely.

        # Calculate option Greeks using binomial model for American options (default) if valid data is available
        if underlying_price and iv > 0:  # Check for valid underlying price and implied volatility to enable Greek calculations; this ensures RemDarwin only computes Greeks with reliable market data.
            T_years = days_to_expiration / 365.0  # Convert days to expiration to years for options calculations; this standardizes time units for RemDarwin's options valuation models.
            # Calculate each Greek individually using binomial model as default for American options
            delta = calculate_delta(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate delta using binomial model for American options
            gamma = calculate_gamma(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate gamma using binomial model for American options
            theta = calculate_theta(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate theta using binomial model for American options
            vega = calculate_vega(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate vega using binomial model for American options
            rho = calculate_rho(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate rho using binomial model for American options
            # Use Black-Scholes for probabilities (approximation for American options)
            d1 = (math.log(underlying_price / strike_price) + (0.05 - 0.0 + 0.5 * iv**2) * T_years) / (iv * math.sqrt(T_years))  # Calculate d1 for probabilities; this approximates moneyness for American options.
            d2 = d1 - iv * math.sqrt(T_years)  # Calculate d2 for probabilities
            prob_itm = norm.cdf(d2) if option_type.lower() == 'call' else norm.cdf(-d2)  # Probability in the money
            prob_otm = 1 - prob_itm  # Probability out of the money
            prob_touch = prob_itm  # Probability touching strike, approximated
            greeks = {'delta': delta, 'gamma': gamma, 'theta': theta, 'vega': vega, 'rho': rho, 'prob_itm': prob_itm, 'prob_otm': prob_otm, 'prob_touch': prob_touch}  # Build greeks dictionary with calculated values
        else:  # If insufficient data for Greek calculation, set to zero; this provides safe defaults for RemDarwin's data processing when market data is unavailable.
            greeks = {'delta': 0.0, 'gamma': 0.0, 'theta': 0.0, 'vega': 0.0, 'rho': 0.0, 'prob_itm': 0.0, 'prob_otm': 0.0, 'prob_touch': 0.0}  # Assign zero values to all Greeks when calculation is not possible; this maintains data consistency in RemDarwin's options data structure.

        bid = getattr(row, 'bid', 0)  # Extract the bid price from the row; this gets the buyer's maximum offer price for liquidity analysis in RemDarwin's options trading decisions.
        bid_price = float(bid) if not pd.isna(bid) else 0.0  # Convert bid to float if valid; this provides numeric bid data for spread calculations in RemDarwin's market analysis.

        # Calculate strategy-specific returns
        max_covered_call_return = None
        put_return_on_risk = None
        put_return_on_capital = None
        if option_type == 'call' and underlying_price is not None:
            max_covered_call_return = strike_price - underlying_price + bid_price
        elif option_type == 'put':
            if strike_price > bid_price:
                put_return_on_risk = (bid_price / (strike_price - bid_price)) * 100
            put_return_on_capital = (bid_price / strike_price) * 100

        ask = getattr(row, 'ask', 0)  # Extract the ask price from the row; this gets the seller's minimum asking price for pricing analysis in RemDarwin's options strategies.
        ask_price = float(ask) if not pd.isna(ask) else 0.0  # Convert ask to float if valid; this ensures numeric ask data for RemDarwin's spread and execution cost evaluations.

        last = getattr(row, 'lastPrice', 0)  # Extract the last traded price from the row; this provides the most recent market price for real-time analysis in RemDarwin's options monitoring.
        last_price = float(last) if not pd.isna(last) else 0.0  # Convert last price to float if valid; this gives numeric last price data for price movement tracking in RemDarwin's system.

        vol = getattr(row, 'volume', 0)  # Extract the trading volume from the row; this indicates daily trading activity for liquidity assessment in RemDarwin's options analysis.
        volume = int(vol) if not pd.isna(vol) else 0  # Convert volume to integer if valid; this provides numeric volume data for RemDarwin's market activity evaluations.

        oi = getattr(row, 'openInterest', 0)  # Extract the open interest from the row; this shows outstanding contracts for market participation analysis in RemDarwin's strategies.
        open_interest = int(oi) if not pd.isna(oi) else 0  # Convert open interest to integer if valid; this gives numeric OI data for RemDarwin's contract liquidity and positioning analysis.

        ch = getattr(row, 'change', 0)  # Extract the price change from the row; this shows daily price movement for trend analysis in RemDarwin's options strategies.
        change = float(ch) if not pd.isna(ch) else 0.0  # Convert change to float if valid; this provides numeric change data for RemDarwin's price movement tracking.

        pch = getattr(row, 'percentChange', 0)  # column for % Change  # Extract the percentage change from the row; this indicates relative price movement for comparative analysis in RemDarwin's quantitative models.
        percent_change = float(pch) if not pd.isna(pch) else 0.0  # Convert percent change to float if valid; this gives numeric percentage data for RemDarwin's relative performance evaluations.

        return OptionContract(  # Create and return a new OptionContract instance with all parsed and processed data; this constructs the structured object that encapsulates option contract information for RemDarwin's analysis and storage.
            symbol=symbol,
            expiration_date=expiration_date,
            strike_price=strike_price,
            option_type=option_type,
            bid=bid_price,
            ask=ask_price,
            last_price=last_price,
            volume=volume,
            open_interest=open_interest,
            implied_volatility=iv,
            change=change,
            percent_change=percent_change,
            delta=greeks['delta'],
            gamma=greeks['gamma'],
            theta=greeks['theta'],
            vega=greeks['vega'],
            rho=greeks['rho'],
            prob_itm=greeks['prob_itm'],
            prob_otm=greeks['prob_otm'],
            prob_touch=greeks['prob_touch'],
            days_to_expiration=days_to_expiration,
            underlying_price=underlying_price,
            max_covered_call_return=max_covered_call_return,
            put_return_on_risk=put_return_on_risk,
            put_return_on_capital=put_return_on_capital,
            validated=False
        )

    def _validate_contract(self, contract: OptionContract) -> bool:  # Define the private validation method to check OptionContract data quality; this method applies business rules to ensure contracts are suitable for RemDarwin's quantitative analysis and trading decisions.
        """ Basic filter to ensure contract data validity before downstream processing. """
        # Basic bid-ask validation (relaxed to allow zero prices and equal bid/ask for data population)
        if (contract.bid is None or contract.ask is None or contract.ask < contract.bid or contract.bid < 0 or contract.ask < 0):  # Check for invalid bid/ask prices, allowing zero values and equal prices to populate more data for analysis.
            self.logger.debug(f"Invalid bid/ask for {contract.symbol} {contract.option_type} "
                              f"strike {contract.strike_price} exp {contract.expiration_date}")  # Log debug information for invalid bid/ask combinations; this aids in troubleshooting data quality issues in RemDarwin's validation process.
            return False  # Reject the contract due to invalid pricing data; this prevents corrupted price information from affecting RemDarwin's trading decisions.
        # Volume and Open Interest must be non-negative
        if contract.volume < 0 or contract.open_interest < 0:  # Validate that volume and open interest are non-negative; negative values indicate data errors that could mislead RemDarwin's liquidity analysis.
            self.logger.debug(f"Negative volume or open interest for {contract.symbol} "
                              f"{contract.option_type} strike {contract.strike_price}")  # Log debug info for negative trading metrics; this supports data integrity monitoring in RemDarwin's system.
            return False  # Reject contracts with invalid volume/open interest; this maintains data quality for RemDarwin's market analysis.
        # Implied Volatility must be reasonable
        if contract.implied_volatility < 0 or contract.implied_volatility > 5:  # 500% IV unlikely  # Check implied volatility is within reasonable bounds; extreme IV values may indicate data errors or extraordinary market conditions that require special handling in RemDarwin.
            self.logger.debug(f"Implied volatility out of range for {contract.symbol} "
                              f"{contract.option_type} strike {contract.strike_price}")  # Log debug info for unreasonable IV values; this enables monitoring of volatility data quality in RemDarwin's risk models.
            return False  # Reject contracts with invalid IV; this prevents unreliable volatility data from corrupting RemDarwin's pricing calculations.
        # Days to expiration must be positive and reasonable
        if contract.days_to_expiration < 0 or contract.days_to_expiration > 1000:  # Validate expiration timing is reasonable; negative days indicate expired contracts, excessive days suggest data errors in RemDarwin's temporal analysis.
            self.logger.debug(f"Invalid days to expiration for {contract.symbol} "
                              f"{contract.option_type} strike {contract.strike_price}")  # Log debug info for invalid expiration timing; this supports temporal data validation in RemDarwin's options processing.
            return False  # Reject contracts with invalid expiration; this ensures only current, valid options are processed by RemDarwin's system.
        contract.validated = True  # Mark the contract as validated; this flag indicates the contract has passed all quality checks for use in RemDarwin's downstream analysis.
        return True  # Accept the validated contract; this allows the contract to proceed to RemDarwin's quantitative analysis and trading algorithms.

    def save_to_database(self, symbol: str, option_data: dict):  # Define the method to save option contracts to a SQLite database with partitioning by expiration date; this method creates partitioned tables for each expiration, adds indexes, and inserts contracts into appropriate tables for RemDarwin's data persistence.
        """
        Saves the option data to a SQLite database with partitioning by expiration date.
        Creates partitioned tables named options_YYYY_MM_DD for each unique expiration.
        Adds indexes on symbol, expiration, strike, and each Greek after table creation.
        Uses TEXT type for all columns for simplicity.
        Unique constraint on (symbol, expiration_date, strike_price, option_type) with ON CONFLICT REPLACE.
        """
        db_name = f"{symbol}_options.db"  # Create database filename based on symbol; this ensures each stock has its own options database in RemDarwin's data organization.
        try:  # Begin exception handling for database operations; this ensures robust error handling during data persistence in RemDarwin's system.
            conn = sqlite3.connect(db_name)  # Establish connection to the SQLite database; this opens or creates the options database for the given symbol in RemDarwin's local storage.
            self.logger.info(f"Connected to database {db_name}")  # Log database connection; this confirms the save process has started.
            cursor = conn.cursor()  # Create a cursor object for executing SQL commands; this provides the interface for database operations in RemDarwin's data saving process.
            # Prepare data for insertion
            all_contracts = option_data.get('calls', []) + option_data.get('puts', [])  # Combine calls and puts contracts into a single list for processing; this enables efficient data handling across all option types in RemDarwin's database operations.
            # Collect unique expiration dates
            unique_expirations = set()
            for contract in all_contracts:
                exp_str = contract.expiration_date.strftime('%Y-%m-%d')
                unique_expirations.add(exp_str)
            # Create partitioned tables for each unique expiration
            for exp in unique_expirations:
                table_name = f"options_{exp.replace('-', '_')}"
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        symbol TEXT,
                        expiration_date TEXT,
                        strike_price TEXT,
                        option_type TEXT,
                        bid TEXT,
                        ask TEXT,
                        last_price TEXT,
                        volume TEXT,
                        open_interest TEXT,
                        implied_volatility TEXT,
                        change TEXT,
                        percent_change TEXT,
                        delta TEXT,
                        gamma TEXT,
                        theta TEXT,
                        vega TEXT,
                        rho TEXT,
                        prob_itm TEXT,
                        prob_otm TEXT,
                        prob_touch TEXT,
                        days_to_expiration TEXT,
                        underlying_price TEXT,
                        validated TEXT,
                        max_covered_call_return TEXT,
                        put_return_on_risk TEXT,
                        put_return_on_capital TEXT,
                        UNIQUE(symbol, expiration_date, strike_price, option_type) ON CONFLICT REPLACE
                    )
                ''')  # Execute table creation for each partitioned table; this sets up the database schema for storing option contract data by expiration in RemDarwin's persistent storage.
            # Add indexes on symbol, expiration, strike, and each Greek for each table
            for exp in unique_expirations:
                table_name = f"options_{exp.replace('-', '_')}"
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_symbol ON {table_name} (symbol)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_expiration ON {table_name} (expiration_date)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_strike ON {table_name} (strike_price)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_delta ON {table_name} (delta)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_gamma ON {table_name} (gamma)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_theta ON {table_name} (theta)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_vega ON {table_name} (vega)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_rho ON {table_name} (rho)')
            # Insert data into appropriate partitioned tables
            for contract in all_contracts:
                exp_str = contract.expiration_date.strftime('%Y_%m_%d')
                table_name = f"options_{exp_str}"
                values = (
                    contract.symbol,
                    str(contract.expiration_date) if contract.expiration_date else None,
                    str(contract.strike_price),
                    contract.option_type,
                    str(contract.bid),
                    str(contract.ask),
                    str(contract.last_price),
                    str(contract.volume),
                    str(contract.open_interest),
                    str(contract.implied_volatility),
                    str(contract.change),
                    str(contract.percent_change),
                    str(contract.delta),
                    str(contract.gamma),
                    str(contract.theta),
                    str(contract.vega),
                    str(contract.rho),
                    str(contract.prob_itm),
                    str(contract.prob_otm),
                    str(contract.prob_touch),
                    str(contract.days_to_expiration) if contract.days_to_expiration is not None else None,
                    str(contract.underlying_price) if contract.underlying_price is not None else None,
                    str(contract.validated),
                    str(contract.max_covered_call_return) if contract.max_covered_call_return is not None else None,
                    str(contract.put_return_on_risk) if contract.put_return_on_risk is not None else None,
                    str(contract.put_return_on_capital) if contract.put_return_on_capital is not None else None
                )  # Prepare tuple of string-converted values for database insertion; this ensures all data types are compatible with TEXT columns in RemDarwin's SQLite schema.
                cursor.execute(f'''
                    INSERT OR REPLACE INTO {table_name} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', values)  # Execute INSERT OR REPLACE into the appropriate partitioned table; this handles uniqueness constraints and ensures data is saved in RemDarwin's options database.
            conn.commit()  # Commit the partitioned table inserts; this ensures the main data is saved even if history fails.
            # Create options_history table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS options_history (
                    symbol TEXT,
                    expiration_date TEXT,
                    strike_price TEXT,
                    option_type TEXT,
                    bid TEXT,
                    ask TEXT,
                    last_price TEXT,
                    volume TEXT,
                    open_interest TEXT,
                    implied_volatility TEXT,
                    change TEXT,
                    percent_change TEXT,
                    delta TEXT,
                    gamma TEXT,
                    theta TEXT,
                    vega TEXT,
                    rho TEXT,
                    prob_itm TEXT,
                    prob_otm TEXT,
                    prob_touch TEXT,
                    days_to_expiration TEXT,
                    underlying_price TEXT,
                    validated TEXT,
                    max_covered_call_return TEXT,
                    put_return_on_risk TEXT,
                    put_return_on_capital TEXT,
                    fetch_timestamp TEXT
                )
            ''')
            # Insert all contracts into options_history with fetch_timestamp
            fetch_timestamp = str(option_data.get('fetch_timestamp', datetime.utcnow()))
            for contract in all_contracts:
                values = (
                    contract.symbol,
                    str(contract.expiration_date) if contract.expiration_date else None,
                    str(contract.strike_price),
                    contract.option_type,
                    str(contract.bid),
                    str(contract.ask),
                    str(contract.last_price),
                    str(contract.volume),
                    str(contract.open_interest),
                    str(contract.implied_volatility),
                    str(contract.change),
                    str(contract.percent_change),
                    str(contract.delta),
                    str(contract.gamma),
                    str(contract.theta),
                    str(contract.vega),
                    str(contract.rho),
                    str(contract.prob_itm),
                    str(contract.prob_otm),
                    str(contract.prob_touch),
                    str(contract.days_to_expiration) if contract.days_to_expiration is not None else None,
                    str(contract.underlying_price) if contract.underlying_price is not None else None,
                    str(contract.validated),
                    str(contract.max_covered_call_return) if contract.max_covered_call_return is not None else None,
                    str(contract.put_return_on_risk) if contract.put_return_on_risk is not None else None,
                    str(contract.put_return_on_capital) if contract.put_return_on_capital is not None else None,
                    fetch_timestamp
                )
                cursor.execute('''
                    INSERT INTO options_history VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', values)
            conn.commit()  # Commit the transaction to make changes permanent; this finalizes the database save operation in RemDarwin's data persistence process.
            self.logger.info(f"Saved {len(all_contracts)} options contracts to partitioned tables and options_history in {db_name}")  # Log successful save operation with count; this provides monitoring and confirmation of data persistence in RemDarwin's logging system.
        except Exception as e:  # Catch any exceptions during database operations; this ensures error handling for connection issues, SQL errors, or data conversion problems in RemDarwin's save functionality.
            self.logger.error(f"Failed to save options data to database for {symbol}: {e}")  # Log the error with details; this enables debugging and operational monitoring of database save failures in RemDarwin's system.
        finally:  # Ensure database connection is always closed; this prevents resource leaks and maintains clean database handling in RemDarwin's data operations.
            if 'conn' in locals():  # Check if connection was established before attempting to close; this avoids errors if connection failed to open in RemDarwin's error handling.
                conn.close()  # Close the database connection; this releases resources and completes the database interaction in RemDarwin's data saving method.

    def log_option_changes(self, symbol: str, option_data: dict):
        """
        Logs option changes to a history table.
        Creates 'option_changes' table in {symbol}_options.db with same columns as 'options' plus 'EnteredDate'.
        Inserts all contracts with today's date.
        No unique constraint.
        """
        db_name = f"{symbol}_options.db"
        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS option_changes (
                    symbol TEXT,
                    expiration_date TEXT,
                    strike_price TEXT,
                    option_type TEXT,
                    bid TEXT,
                    ask TEXT,
                    last_price TEXT,
                    volume TEXT,
                    open_interest TEXT,
                    implied_volatility TEXT,
                    change TEXT,
                    percent_change TEXT,
                    delta TEXT,
                    gamma TEXT,
                    theta TEXT,
                    vega TEXT,
                    rho TEXT,
                    prob_itm TEXT,
                    prob_otm TEXT,
                    prob_touch TEXT,
                    days_to_expiration TEXT,
                    underlying_price TEXT,
                    validated TEXT,
                    max_covered_call_return TEXT,
                    put_return_on_risk TEXT,
                    put_return_on_capital TEXT,
                    EnteredDate TEXT
                )
            ''')
            all_contracts = option_data.get('calls', []) + option_data.get('puts', [])
            today = str(datetime.now().date())
            for contract in all_contracts:
                values = (
                    contract.symbol,
                    str(contract.expiration_date) if contract.expiration_date else None,
                    str(contract.strike_price),
                    contract.option_type,
                    str(contract.bid),
                    str(contract.ask),
                    str(contract.last_price),
                    str(contract.volume),
                    str(contract.open_interest),
                    str(contract.implied_volatility),
                    str(contract.change),
                    str(contract.percent_change),
                    str(contract.delta),
                    str(contract.gamma),
                    str(contract.theta),
                    str(contract.vega),
                    str(contract.rho),
                    str(contract.prob_itm),
                    str(contract.prob_otm),
                    str(contract.prob_touch),
                    str(contract.days_to_expiration) if contract.days_to_expiration is not None else None,
                    str(contract.underlying_price) if contract.underlying_price is not None else None,
                    str(contract.validated),
                    str(contract.max_covered_call_return) if contract.max_covered_call_return is not None else None,
                    str(contract.put_return_on_risk) if contract.put_return_on_risk is not None else None,
                    str(contract.put_return_on_capital) if contract.put_return_on_capital is not None else None,
                    today
                )
                cursor.execute('''
                    INSERT INTO option_changes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', values)
            conn.commit()
            self.logger.info(f"Logged {len(all_contracts)} option changes to {db_name}")
        except Exception as e:
            self.logger.error(f"Failed to log option changes for {symbol}: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

# Example usage/demo code  # Section for demonstration and testing of the options fetching functionality; this allows standalone execution to verify RemDarwin's options data pipeline.
if __name__ == "__main__":  # Execute demo code only when script is run directly; this prevents demo execution when the module is imported by RemDarwin's main application.
    parser = argparse.ArgumentParser(description="Fetch options data for a given ticker symbol using Yahoo Finance.")  # Create argument parser for CLI support; this enables user to specify ticker via command line in RemDarwin's options fetching script.
    parser.add_argument('-t', '--ticker', required=True, help='Stock ticker symbol (e.g., AAPL)')  # Add required ticker argument; this allows dynamic specification of the stock symbol for options fetching in RemDarwin.
    parser.add_argument('--output-dir', default='./output', help='Output directory for data files')  # Add output directory argument with default; this allows specification of where to save output files in RemDarwin.
    parser.add_argument('--period', choices=['annual', 'quarterly'], default='annual', help='Financial period type')  # Add period argument with choices; this allows selection between annual and quarterly data in RemDarwin.
    parser.add_argument('--api-key', type=str, help='API key for data services')  # Add API key argument; this allows specification of API credentials for authenticated data access in RemDarwin.
    args = parser.parse_args()  # Parse command-line arguments; this processes user input for ticker symbol in RemDarwin's CLI interface.
    print(f"Parsed arguments: ticker={args.ticker}, output_dir={args.output_dir}, period={args.period}, api_key={args.api_key}")  # Print parsed arguments for verification; this provides user feedback on the parsed CLI inputs in RemDarwin.
    ticker_symbol = args.ticker.upper()  # Convert ticker to uppercase for consistency; this standardizes stock symbols in RemDarwin's data processing.
    logging.basicConfig(level=logging.INFO)  # Configure basic logging to INFO level for demo output; this enables visibility into the fetching process during RemDarwin's development and testing.
    fetcher = YFinanceOptionChainFetcher()  # Instantiate the fetcher class for options data retrieval; this creates the primary object for demonstrating RemDarwin's options fetching capabilities.
    # Fetch option chain for specified ticker
    result = fetcher.fetch_option_chain(ticker_symbol)  # Execute the main fetching method for the specified ticker options; this demonstrates RemDarwin's ability to retrieve comprehensive options data from Yahoo Finance.
    print(f"Underlying Price: {result['underlying_price']}")  # Display the fetched underlying stock price; this shows RemDarwin's integration with stock price data for options analysis.
    print(f"Total Calls fetched: {len(result['calls'])}")  # Show the count of call options retrieved; this demonstrates the volume of data RemDarwin can process for calls.
    print(f"Total Puts fetched: {len(result['puts'])}")  # Show the count of put options retrieved; this demonstrates the volume of data RemDarwin can process for puts.
    # Save to database
    fetcher.save_to_database(ticker_symbol, result)  # Save the fetched options data to the database with partitioning and indexing.
    # Print a sample contract
    if result['calls']:  # Check if calls data is available for display; this ensures safe demo output in RemDarwin's testing scenarios.
        sample_call = result['calls'][0]  # Select the first call contract as an example; this provides a concrete instance for RemDarwin's options data inspection.
        print("Sample Call:")  # Label the output for clarity; this organizes demo output in RemDarwin's development interface.
        print(sample_call)  # Display the sample call contract details; this shows the structured data format RemDarwin uses for options contracts.
    if result['puts']:  # Check if puts data is available for display; this ensures complete demo coverage in RemDarwin's testing.
        sample_put = result['puts'][0]  # Select the first put contract as an example; this complements the call example for comprehensive RemDarwin data demonstration.
        print("Sample Put:")  # Label the put output for clarity; this maintains organized demo presentation in RemDarwin's interface.
        print(sample_put)  # Display the sample put contract details; this completes the demonstration of RemDarwin's options data structure and fetching capabilities.
    if not re.match(pattern, ticker):
        raise ValueError(f"Invalid ticker symbol format: {ticker}. Must be 1-5 uppercase letters.")
    # Test validation with sample inputs (implicitly done by raising)


class YFinanceOptionChainFetcher:  # Define the YFinanceOptionChainFetcher class as the main component for fetching and processing options data from Yahoo Finance; this class encapsulates the logic for retrieving option chains, parsing data, and validating contracts, serving as the core engine for options data acquisition in RemDarwin's systematic trading system.
    def __init__(self, logger=None):  # Define the constructor method for YFinanceOptionChainFetcher, accepting an optional logger parameter; this initializes the fetcher with logging capabilities, allowing for configurable logging in RemDarwin's options data fetching operations.
        self.logger = logger or logging.getLogger(__name__)  # Assign the logger instance to the object, using the provided logger or creating a default one for this module; this enables consistent logging throughout the fetcher's operations, supporting debugging and monitoring in RemDarwin's options data pipeline.

    def fetch_option_chain(self, symbol: str):  # Define the main method to fetch the complete option chain for a given stock symbol; this method orchestrates the retrieval of all available option contracts, their parsing, validation, and organization into structured data, forming the primary interface for options data acquisition in RemDarwin's trading system.
        """
        Fetches the entire option chain (calls and puts) for the given symbol and validates basic contract data.
        Returns: Dict with 'calls' and 'puts', each a list of OptionContract instances, and 'underlying_price' of the stock.
        """
        try:  # Begin exception handling block to catch and manage errors during the options fetching process; this ensures robust operation by gracefully handling API failures, network issues, or data parsing errors, maintaining system stability in RemDarwin's data acquisition workflow.
            ticker = yf.Ticker(symbol)  # Create a Ticker object from yfinance for the specified stock symbol; this object provides access to all financial data for the stock, including options chains, serving as the primary data source interface in RemDarwin's options fetching mechanism.
            self.logger.info(f"Fetching option expirations for {symbol}")  # Log an informational message indicating the start of expiration date retrieval; this provides visibility into the fetching process, aiding in monitoring and debugging options data acquisition in RemDarwin's operational logs.
            exp_dates = ticker.options  # List of expiration date strings (YYYY-MM-DD)  # Retrieve the list of available option expiration dates from the ticker object; this collection of date strings defines the time frames for which options data will be fetched, enabling comprehensive coverage of the option chain in RemDarwin's data collection process.
            self.logger.info(f"Found {len(exp_dates)} expiration dates: {exp_dates}")  # Log the number and list of expiration dates found; this helps debug if no expirations are available.
            ic(ticker.option_chain)  # Use icecream's ic function to inspect the option_chain property of the ticker; this debugging call provides a quick view of the option chain structure, aiding in development and troubleshooting of the options data fetching logic in RemDarwin.
            all_calls = []  # Initialize an empty list to accumulate call option contracts across all expiration dates; this container will hold validated OptionContract instances for call options, enabling organized storage and processing of calls data in RemDarwin's options analysis pipeline.
            all_puts = []  # Initialize an empty list to accumulate put option contracts across all expiration dates; this container will hold validated OptionContract instances for put options, facilitating structured handling of puts data in RemDarwin's quantitative trading system.
            validation_results = []  # Initialize list to track validation results for reporting; this collects boolean outcomes of the comprehensive validation pipeline for each contract.
            try:
                hist = ticker.history(period='1d')  # Fetch the recent historical price data for the stock over the last trading day; this provides the current underlying price information needed for options valuation and moneyness calculations in RemDarwin's options analysis.
                if hist.empty:  # Check if the historical data DataFrame is empty, indicating no price data was retrieved; this handles cases where the ticker has no recent trading data, setting underlying price to None for safe processing in RemDarwin's options calculations.
                    underlying_price = None  # Set underlying_price to None when no historical data is available; this prevents invalid price values from affecting options analysis and maintains data integrity in RemDarwin's valuation models.
                else:  # If historical data is available, proceed to extract the closing price; this branch handles the normal case where price data is successfully retrieved for options pricing in RemDarwin.
                    underlying_price = hist['Close'].iloc[0]  # Extract the most recent closing price from the historical data; this provides the current underlying asset price for moneyness determination and intrinsic value calculations in RemDarwin's options framework.
                    if not underlying_price or underlying_price <= 0:  # Validate that the extracted price is positive and valid; this check ensures data quality by filtering out invalid or zero prices that could corrupt options analysis in RemDarwin.
                        self.logger.warning(f"Invalid underlying price for {symbol}: {underlying_price}")  # Log a warning for invalid prices with details; this provides visibility into data quality issues, supporting monitoring and troubleshooting in RemDarwin's data pipeline.
                        underlying_price = None  # Reset invalid price to None; this maintains consistency and prevents downstream errors from propagating through RemDarwin's options processing system.
            except Exception as e:  # Catch any exceptions during price retrieval and processing; this ensures robust error handling for network issues, API failures, or data parsing problems in RemDarwin's price fetching mechanism.
                self.logger.warning(f"Failed to fetch underlying price for {symbol}: {e}")  # Log the failure with error details; this enables debugging and operational monitoring of price data acquisition issues in RemDarwin's system.
                underlying_price = None  # Set price to None on failure; this allows the options fetching to continue without underlying price data, maintaining system resilience in RemDarwin's data processing workflow.
            for exp in exp_dates:  # Iterate over each available expiration date to fetch options chains; this loop ensures comprehensive coverage of all expiration periods, enabling complete option chain retrieval for RemDarwin's analysis across different time horizons.
                self.logger.info(f"Fetching options for expiration: {exp}")  # Log the current expiration being processed; this provides progress tracking and debugging information for options data fetching operations in RemDarwin's logging system.
                opt_chain = ticker.option_chain(exp)  # Retrieve the option chain (calls and puts) for the specific expiration date from yfinance; this fetches the raw options data that will be parsed and validated for RemDarwin's options database.
                # Process calls
                calls_count = 0
                calls_valid = 0
                for row in opt_chain.calls.itertuples():  # Iterate through each call option row in the DataFrame; this processes individual call contracts, extracting and structuring their data for RemDarwin's quantitative analysis.
                    calls_count += 1
                    contract = self._parse_option_row(row, symbol, 'call', exp, underlying_price)  # Parse the raw row data into an OptionContract instance for calls; this converts yfinance's DataFrame row into a structured object with all necessary fields for RemDarwin's options processing.
                    # Enhanced validation pipeline with comprehensive data validation
                    contract_dict = contract_to_dict(contract)
                    if validate_option_data(contract_dict):
                        greeks_dict = {k: v for k, v in contract_dict.items() if k in ['delta', 'gamma', 'theta', 'vega', 'rho']}
                        if validate_greeks(greeks_dict):
                            filled = gap_fill_missing_data(contract_dict)
                            normalized = normalize_option_data(filled)
                            contract = update_contract_from_dict(contract, normalized)
                            if self._validate_contract(contract):  # Final validation check
                                all_calls.append(contract)
                                calls_valid += 1
                                validation_results.append(True)
                            else:
                                validation_results.append(False)
                        else:
                            validation_results.append(False)
                    else:
                        validation_results.append(False)
                # Process puts
                puts_count = 0
                puts_valid = 0
                for row in opt_chain.puts.itertuples():  # Iterate through each put option row in the DataFrame; this processes individual put contracts, enabling comprehensive put option data extraction for RemDarwin's trading strategies.
                    puts_count += 1
                    contract = self._parse_option_row(row, symbol, 'put', exp, underlying_price)  # Parse the raw row data into an OptionContract instance for puts; this structures put option data into RemDarwin's standardized format for analysis and decision-making.
                    # Enhanced validation pipeline with comprehensive data validation
                    contract_dict = contract_to_dict(contract)
                    if validate_option_data(contract_dict):
                        greeks_dict = {k: v for k, v in contract_dict.items() if k in ['delta', 'gamma', 'theta', 'vega', 'rho']}
                        if validate_greeks(greeks_dict):
                            filled = gap_fill_missing_data(contract_dict)
                            normalized = normalize_option_data(filled)
                            contract = update_contract_from_dict(contract, normalized)
                            if self._validate_contract(contract):  # Final validation check
                                all_puts.append(contract)
                                puts_valid += 1
                                validation_results.append(True)
                            else:
                                validation_results.append(False)
                        else:
                            validation_results.append(False)
                    else:
                        validation_results.append(False)
                self.logger.info(f"Expiration {exp}: {calls_count} calls parsed, {calls_valid} valid; {puts_count} puts parsed, {puts_valid} valid")  # Log processing statistics for each expiration; this helps debug validation issues.
            self.logger.info(f"Fetched {len(all_calls)} calls and {len(all_puts)} puts for {symbol}")  # Log the successful completion with counts of fetched contracts; this provides summary statistics for monitoring the effectiveness of options data acquisition in RemDarwin's system.
            # Generate validation report
            report = generate_validation_report(validation_results)
            return {  # Return the complete options data structure with all fetched and validated contracts; this delivers the processed options chain data to RemDarwin's downstream analysis and trading components.
                'calls': all_calls,  # Include the list of validated call option contracts; this provides call options data for RemDarwin's call-based trading strategies and analysis.
                'puts': all_puts,  # Include the list of validated put option contracts; this provides put options data for RemDarwin's put-based trading strategies and risk management.
                'underlying_price': underlying_price,  # Include the fetched underlying stock price; this enables moneyness calculations and intrinsic value assessments in RemDarwin's options valuation models.
                'fetch_timestamp': datetime.utcnow(),  # Include the UTC timestamp of the fetch operation; this provides temporal context for data freshness and supports time-series analysis in RemDarwin's options system.
                'validation_report': report  # Include the validation report with success metrics; this provides insights into data quality and validation effectiveness for RemDarwin's monitoring.
            }
        except Exception as e:  # Catch any unhandled exceptions during the entire fetching process; this provides a safety net for unexpected errors, ensuring RemDarwin's system remains stable even with API or processing failures.
            self.logger.error(f"Failed to fetch options for {symbol}: {e}")  # Log the critical error with details; this enables debugging and alerts for system failures in RemDarwin's options data pipeline.
            return {  # Return an empty data structure on failure; this maintains API consistency while indicating that no valid options data was retrieved for RemDarwin's processing.
                'calls': [],  # Return empty list for calls on error; this prevents downstream components from attempting to process invalid data in RemDarwin's system.
                'puts': [],  # Return empty list for puts on error; this ensures safe failure handling in RemDarwin's options analysis pipeline.
                'underlying_price': None,  # Return None for price on error; this clearly indicates price unavailability to RemDarwin's valuation calculations.
                'fetch_timestamp': datetime.utcnow()  # Include timestamp even on failure; this provides timing context for error analysis in RemDarwin's monitoring and logging system.
            }

    def _parse_option_row(self, row, symbol, option_type, expiration_date_str, underlying_price):  # Define the private method to parse raw yfinance DataFrame rows into OptionContract objects; this method handles data type conversion, NaN handling, and field extraction for both call and put options in RemDarwin's data processing pipeline.
        """ Parse a row from yfinance option DataFrame into an OptionContract. """
        expiration_date = datetime.strptime(expiration_date_str, "%Y-%m-%d")  # Parse the expiration date string into a datetime object; this converts the string format from yfinance into a usable date for RemDarwin's temporal calculations and contract identification.
        days_to_expiration = (expiration_date - datetime.utcnow()).days  # Calculate the number of days until expiration from the current UTC time; this temporal metric is crucial for time value decay analysis and expiration-based strategies in RemDarwin's options framework.
        implied_vol = getattr(row, 'impliedVolatility', None)  # Extract the implied volatility value from the row, handling missing attributes gracefully; this retrieves the market's volatility expectation for pricing models in RemDarwin's options valuation.
        iv = implied_vol if implied_vol is not None else 0.0  # Set implied volatility to extracted value or default to 0.0 for missing data; this ensures a valid IV value for RemDarwin's calculations, preventing NaN propagation.

        strike = getattr(row, 'strike', 0)  # Extract the strike price from the row, defaulting to 0 if missing; this gets the key price level that determines option moneyness for RemDarwin's analysis.
        strike_price = float(strike) if not pd.isna(strike) else 0.0  # Convert strike to float if valid, otherwise use 0.0; this ensures numeric strike price data for RemDarwin's calculations, handling pandas NaN values safely.

        # Calculate option Greeks using binomial model for American options (default) if valid data is available
        if underlying_price and iv > 0:  # Check for valid underlying price and implied volatility to enable Greek calculations; this ensures RemDarwin only computes Greeks with reliable market data.
            T_years = days_to_expiration / 365.0  # Convert days to expiration to years for options calculations; this standardizes time units for RemDarwin's options valuation models.
            # Calculate each Greek individually using binomial model as default for American options
            delta = calculate_delta(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate delta using binomial model for American options
            gamma = calculate_gamma(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate gamma using binomial model for American options
            theta = calculate_theta(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate theta using binomial model for American options
            vega = calculate_vega(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate vega using binomial model for American options
            rho = calculate_rho(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate rho using binomial model for American options
            # Use Black-Scholes for probabilities (approximation for American options)
            d1 = (math.log(underlying_price / strike_price) + (0.05 - 0.0 + 0.5 * iv**2) * T_years) / (iv * math.sqrt(T_years))  # Calculate d1 for probabilities; this approximates moneyness for American options.
            d2 = d1 - iv * math.sqrt(T_years)  # Calculate d2 for probabilities
            prob_itm = norm.cdf(d2) if option_type.lower() == 'call' else norm.cdf(-d2)  # Probability in the money
            prob_otm = 1 - prob_itm  # Probability out of the money
            prob_touch = prob_itm  # Probability touching strike, approximated
            greeks = {'delta': delta, 'gamma': gamma, 'theta': theta, 'vega': vega, 'rho': rho, 'prob_itm': prob_itm, 'prob_otm': prob_otm, 'prob_touch': prob_touch}  # Build greeks dictionary with calculated values
        else:  # If insufficient data for Greek calculation, set to zero; this provides safe defaults for RemDarwin's data processing when market data is unavailable.
            greeks = {'delta': 0.0, 'gamma': 0.0, 'theta': 0.0, 'vega': 0.0, 'rho': 0.0, 'prob_itm': 0.0, 'prob_otm': 0.0, 'prob_touch': 0.0}  # Assign zero values to all Greeks when calculation is not possible; this maintains data consistency in RemDarwin's options data structure.

        bid = getattr(row, 'bid', 0)  # Extract the bid price from the row; this gets the buyer's maximum offer price for liquidity analysis in RemDarwin's options trading decisions.
        bid_price = float(bid) if not pd.isna(bid) else 0.0  # Convert bid to float if valid; this provides numeric bid data for spread calculations in RemDarwin's market analysis.

        # Calculate strategy-specific returns
        max_covered_call_return = None
        put_return_on_risk = None
        put_return_on_capital = None
        if option_type == 'call' and underlying_price is not None:
            max_covered_call_return = strike_price - underlying_price + bid_price
        elif option_type == 'put':
            if strike_price > bid_price:
                put_return_on_risk = (bid_price / (strike_price - bid_price)) * 100
            put_return_on_capital = (bid_price / strike_price) * 100

        ask = getattr(row, 'ask', 0)  # Extract the ask price from the row; this gets the seller's minimum asking price for pricing analysis in RemDarwin's options strategies.
        ask_price = float(ask) if not pd.isna(ask) else 0.0  # Convert ask to float if valid; this ensures numeric ask data for RemDarwin's spread and execution cost evaluations.

        last = getattr(row, 'lastPrice', 0)  # Extract the last traded price from the row; this provides the most recent market price for real-time analysis in RemDarwin's options monitoring.
        last_price = float(last) if not pd.isna(last) else 0.0  # Convert last price to float if valid; this gives numeric last price data for price movement tracking in RemDarwin's system.

        vol = getattr(row, 'volume', 0)  # Extract the trading volume from the row; this indicates daily trading activity for liquidity assessment in RemDarwin's options analysis.
        volume = int(vol) if not pd.isna(vol) else 0  # Convert volume to integer if valid; this provides numeric volume data for RemDarwin's market activity evaluations.

        oi = getattr(row, 'openInterest', 0)  # Extract the open interest from the row; this shows outstanding contracts for market participation analysis in RemDarwin's strategies.
        open_interest = int(oi) if not pd.isna(oi) else 0  # Convert open interest to integer if valid; this gives numeric OI data for RemDarwin's contract liquidity and positioning analysis.

        ch = getattr(row, 'change', 0)  # Extract the price change from the row; this shows daily price movement for trend analysis in RemDarwin's options strategies.
        change = float(ch) if not pd.isna(ch) else 0.0  # Convert change to float if valid; this provides numeric change data for RemDarwin's price movement tracking.

        pch = getattr(row, 'percentChange', 0)  # column for % Change  # Extract the percentage change from the row; this indicates relative price movement for comparative analysis in RemDarwin's quantitative models.
        percent_change = float(pch) if not pd.isna(pch) else 0.0  # Convert percent change to float if valid; this gives numeric percentage data for RemDarwin's relative performance evaluations.

        return OptionContract(  # Create and return a new OptionContract instance with all parsed and processed data; this constructs the structured object that encapsulates option contract information for RemDarwin's analysis and storage.
            symbol=symbol,
            expiration_date=expiration_date,
            strike_price=strike_price,
            option_type=option_type,
            bid=bid_price,
            ask=ask_price,
            last_price=last_price,
            volume=volume,
            open_interest=open_interest,
            implied_volatility=iv,
            change=change,
            percent_change=percent_change,
            delta=greeks['delta'],
            gamma=greeks['gamma'],
            theta=greeks['theta'],
            vega=greeks['vega'],
            rho=greeks['rho'],
            prob_itm=greeks['prob_itm'],
            prob_otm=greeks['prob_otm'],
            prob_touch=greeks['prob_touch'],
            days_to_expiration=days_to_expiration,
            underlying_price=underlying_price,
            max_covered_call_return=max_covered_call_return,
            put_return_on_risk=put_return_on_risk,
            put_return_on_capital=put_return_on_capital,
            validated=False
        )

    def _validate_contract(self, contract: OptionContract) -> bool:  # Define the private validation method to check OptionContract data quality; this method applies business rules to ensure contracts are suitable for RemDarwin's quantitative analysis and trading decisions.
        """ Basic filter to ensure contract data validity before downstream processing. """
        # Basic bid-ask validation (relaxed to allow zero prices and equal bid/ask for data population)
        if (contract.bid is None or contract.ask is None or contract.ask < contract.bid or contract.bid < 0 or contract.ask < 0):  # Check for invalid bid/ask prices, allowing zero values and equal prices to populate more data for analysis.
            self.logger.debug(f"Invalid bid/ask for {contract.symbol} {contract.option_type} "
                              f"strike {contract.strike_price} exp {contract.expiration_date}")  # Log debug information for invalid bid/ask combinations; this aids in troubleshooting data quality issues in RemDarwin's validation process.
            return False  # Reject the contract due to invalid pricing data; this prevents corrupted price information from affecting RemDarwin's trading decisions.
        # Volume and Open Interest must be non-negative
        if contract.volume < 0 or contract.open_interest < 0:  # Validate that volume and open interest are non-negative; negative values indicate data errors that could mislead RemDarwin's liquidity analysis.
            self.logger.debug(f"Negative volume or open interest for {contract.symbol} "
                              f"{contract.option_type} strike {contract.strike_price}")  # Log debug info for negative trading metrics; this supports data integrity monitoring in RemDarwin's system.
            return False  # Reject contracts with invalid volume/open interest; this maintains data quality for RemDarwin's market analysis.
        # Implied Volatility must be reasonable
        if contract.implied_volatility < 0 or contract.implied_volatility > 5:  # 500% IV unlikely  # Check implied volatility is within reasonable bounds; extreme IV values may indicate data errors or extraordinary market conditions that require special handling in RemDarwin.
            self.logger.debug(f"Implied volatility out of range for {contract.symbol} "
                              f"{contract.option_type} strike {contract.strike_price}")  # Log debug info for unreasonable IV values; this enables monitoring of volatility data quality in RemDarwin's risk models.
            return False  # Reject contracts with invalid IV; this prevents unreliable volatility data from corrupting RemDarwin's pricing calculations.
        # Days to expiration must be positive and reasonable
        if contract.days_to_expiration < 0 or contract.days_to_expiration > 1000:  # Validate expiration timing is reasonable; negative days indicate expired contracts, excessive days suggest data errors in RemDarwin's temporal analysis.
            self.logger.debug(f"Invalid days to expiration for {contract.symbol} "
                              f"{contract.option_type} strike {contract.strike_price}")  # Log debug info for invalid expiration timing; this supports temporal data validation in RemDarwin's options processing.
            return False  # Reject contracts with invalid expiration; this ensures only current, valid options are processed by RemDarwin's system.
        contract.validated = True  # Mark the contract as validated; this flag indicates the contract has passed all quality checks for use in RemDarwin's downstream analysis.
        return True  # Accept the validated contract; this allows the contract to proceed to RemDarwin's quantitative analysis and trading algorithms.

    def save_to_database(self, symbol: str, option_data: dict):  # Define the method to save option contracts to a SQLite database with partitioning by expiration date; this method creates partitioned tables for each expiration, adds indexes, and inserts contracts into appropriate tables for RemDarwin's data persistence.
        """
        Saves the option data to a SQLite database with partitioning by expiration date.
        Creates partitioned tables named options_YYYY_MM_DD for each unique expiration.
        Adds indexes on symbol, expiration, strike, and each Greek after table creation.
        Uses TEXT type for all columns for simplicity.
        Unique constraint on (symbol, expiration_date, strike_price, option_type) with ON CONFLICT REPLACE.
        """
        db_name = f"{symbol}_options.db"  # Create database filename based on symbol; this ensures each stock has its own options database in RemDarwin's data organization.
        try:  # Begin exception handling for database operations; this ensures robust error handling during data persistence in RemDarwin's system.
            conn = sqlite3.connect(db_name)  # Establish connection to the SQLite database; this opens or creates the options database for the given symbol in RemDarwin's local storage.
            self.logger.info(f"Connected to database {db_name}")  # Log database connection; this confirms the save process has started.
            cursor = conn.cursor()  # Create a cursor object for executing SQL commands; this provides the interface for database operations in RemDarwin's data saving process.
            # Prepare data for insertion
            all_contracts = option_data.get('calls', []) + option_data.get('puts', [])  # Combine calls and puts contracts into a single list for processing; this enables efficient data handling across all option types in RemDarwin's database operations.
            # Collect unique expiration dates
            unique_expirations = set()
            for contract in all_contracts:
                exp_str = contract.expiration_date.strftime('%Y-%m-%d')
                unique_expirations.add(exp_str)
            # Create partitioned tables for each unique expiration
            for exp in unique_expirations:
                table_name = f"options_{exp.replace('-', '_')}"
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        symbol TEXT,
                        expiration_date TEXT,
                        strike_price TEXT,
                        option_type TEXT,
                        bid TEXT,
                        ask TEXT,
                        last_price TEXT,
                        volume TEXT,
                        open_interest TEXT,
                        implied_volatility TEXT,
                        change TEXT,
                        percent_change TEXT,
                        delta TEXT,
                        gamma TEXT,
                        theta TEXT,
                        vega TEXT,
                        rho TEXT,
                        prob_itm TEXT,
                        prob_otm TEXT,
                        prob_touch TEXT,
                        days_to_expiration TEXT,
                        underlying_price TEXT,
                        validated TEXT,
                        max_covered_call_return TEXT,
                        put_return_on_risk TEXT,
                        put_return_on_capital TEXT,
                        UNIQUE(symbol, expiration_date, strike_price, option_type) ON CONFLICT REPLACE
                    )
                ''')  # Execute table creation for each partitioned table; this sets up the database schema for storing option contract data by expiration in RemDarwin's persistent storage.
            # Add indexes on symbol, expiration, strike, and each Greek for each table
            for exp in unique_expirations:
                table_name = f"options_{exp.replace('-', '_')}"
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_symbol ON {table_name} (symbol)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_expiration ON {table_name} (expiration_date)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_strike ON {table_name} (strike_price)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_delta ON {table_name} (delta)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_gamma ON {table_name} (gamma)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_theta ON {table_name} (theta)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_vega ON {table_name} (vega)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_rho ON {table_name} (rho)')
            # Insert data into appropriate partitioned tables
            for contract in all_contracts:
                exp_str = contract.expiration_date.strftime('%Y_%m_%d')
                table_name = f"options_{exp_str}"
                values = (
                    contract.symbol,
                    str(contract.expiration_date) if contract.expiration_date else None,
                    str(contract.strike_price),
                    contract.option_type,
                    str(contract.bid),
                    str(contract.ask),
                    str(contract.last_price),
                    str(contract.volume),
                    str(contract.open_interest),
                    str(contract.implied_volatility),
                    str(contract.change),
                    str(contract.percent_change),
                    str(contract.delta),
                    str(contract.gamma),
                    str(contract.theta),
                    str(contract.vega),
                    str(contract.rho),
                    str(contract.prob_itm),
                    str(contract.prob_otm),
                    str(contract.prob_touch),
                    str(contract.days_to_expiration) if contract.days_to_expiration is not None else None,
                    str(contract.underlying_price) if contract.underlying_price is not None else None,
                    str(contract.validated),
                    str(contract.max_covered_call_return) if contract.max_covered_call_return is not None else None,
                    str(contract.put_return_on_risk) if contract.put_return_on_risk is not None else None,
                    str(contract.put_return_on_capital) if contract.put_return_on_capital is not None else None
                )  # Prepare tuple of string-converted values for database insertion; this ensures all data types are compatible with TEXT columns in RemDarwin's SQLite schema.
                cursor.execute(f'''
                    INSERT OR REPLACE INTO {table_name} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', values)  # Execute INSERT OR REPLACE into the appropriate partitioned table; this handles uniqueness constraints and ensures data is saved in RemDarwin's options database.
            conn.commit()  # Commit the partitioned table inserts; this ensures the main data is saved even if history fails.
            # Create options_history table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS options_history (
                    symbol TEXT,
                    expiration_date TEXT,
                    strike_price TEXT,
                    option_type TEXT,
                    bid TEXT,
                    ask TEXT,
                    last_price TEXT,
                    volume TEXT,
                    open_interest TEXT,
                    implied_volatility TEXT,
                    change TEXT,
                    percent_change TEXT,
                    delta TEXT,
                    gamma TEXT,
                    theta TEXT,
                    vega TEXT,
                    rho TEXT,
                    prob_itm TEXT,
                    prob_otm TEXT,
                    prob_touch TEXT,
                    days_to_expiration TEXT,
                    underlying_price TEXT,
                    validated TEXT,
                    max_covered_call_return TEXT,
                    put_return_on_risk TEXT,
                    put_return_on_capital TEXT,
                    fetch_timestamp TEXT
                )
            ''')
            # Insert all contracts into options_history with fetch_timestamp
            fetch_timestamp = str(option_data.get('fetch_timestamp', datetime.utcnow()))
            for contract in all_contracts:
                values = (
                    contract.symbol,
                    str(contract.expiration_date) if contract.expiration_date else None,
                    str(contract.strike_price),
                    contract.option_type,
                    str(contract.bid),
                    str(contract.ask),
                    str(contract.last_price),
                    str(contract.volume),
                    str(contract.open_interest),
                    str(contract.implied_volatility),
                    str(contract.change),
                    str(contract.percent_change),
                    str(contract.delta),
                    str(contract.gamma),
                    str(contract.theta),
                    str(contract.vega),
                    str(contract.rho),
                    str(contract.prob_itm),
                    str(contract.prob_otm),
                    str(contract.prob_touch),
                    str(contract.days_to_expiration) if contract.days_to_expiration is not None else None,
                    str(contract.underlying_price) if contract.underlying_price is not None else None,
                    str(contract.validated),
                    str(contract.max_covered_call_return) if contract.max_covered_call_return is not None else None,
                    str(contract.put_return_on_risk) if contract.put_return_on_risk is not None else None,
                    str(contract.put_return_on_capital) if contract.put_return_on_capital is not None else None,
                    fetch_timestamp
                )
                cursor.execute('''
                    INSERT INTO options_history VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', values)
            conn.commit()  # Commit the transaction to make changes permanent; this finalizes the database save operation in RemDarwin's data persistence process.
            self.logger.info(f"Saved {len(all_contracts)} options contracts to partitioned tables and options_history in {db_name}")  # Log successful save operation with count; this provides monitoring and confirmation of data persistence in RemDarwin's logging system.
        except Exception as e:  # Catch any exceptions during database operations; this ensures error handling for connection issues, SQL errors, or data conversion problems in RemDarwin's save functionality.
            self.logger.error(f"Failed to save options data to database for {symbol}: {e}")  # Log the error with details; this enables debugging and operational monitoring of database save failures in RemDarwin's system.
        finally:  # Ensure database connection is always closed; this prevents resource leaks and maintains clean database handling in RemDarwin's data operations.
            if 'conn' in locals():  # Check if connection was established before attempting to close; this avoids errors if connection failed to open in RemDarwin's error handling.
                conn.close()  # Close the database connection; this releases resources and completes the database interaction in RemDarwin's data saving method.

    def log_option_changes(self, symbol: str, option_data: dict):
        """
        Logs option changes to a history table.
        Creates 'option_changes' table in {symbol}_options.db with same columns as 'options' plus 'EnteredDate'.
        Inserts all contracts with today's date.
        No unique constraint.
        """
        db_name = f"{symbol}_options.db"
        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS option_changes (
                    symbol TEXT,
                    expiration_date TEXT,
                    strike_price TEXT,
                    option_type TEXT,
                    bid TEXT,
                    ask TEXT,
                    last_price TEXT,
                    volume TEXT,
                    open_interest TEXT,
                    implied_volatility TEXT,
                    change TEXT,
                    percent_change TEXT,
                    delta TEXT,
                    gamma TEXT,
                    theta TEXT,
                    vega TEXT,
                    rho TEXT,
                    prob_itm TEXT,
                    prob_otm TEXT,
                    prob_touch TEXT,
                    days_to_expiration TEXT,
                    underlying_price TEXT,
                    validated TEXT,
                    max_covered_call_return TEXT,
                    put_return_on_risk TEXT,
                    put_return_on_capital TEXT,
                    EnteredDate TEXT
                )
            ''')
            all_contracts = option_data.get('calls', []) + option_data.get('puts', [])
            today = str(datetime.now().date())
            for contract in all_contracts:
                values = (
                    contract.symbol,
                    str(contract.expiration_date) if contract.expiration_date else None,
                    str(contract.strike_price),
                    contract.option_type,
                    str(contract.bid),
                    str(contract.ask),
                    str(contract.last_price),
                    str(contract.volume),
                    str(contract.open_interest),
                    str(contract.implied_volatility),
                    str(contract.change),
                    str(contract.percent_change),
                    str(contract.delta),
                    str(contract.gamma),
                    str(contract.theta),
                    str(contract.vega),
                    str(contract.rho),
                    str(contract.prob_itm),
                    str(contract.prob_otm),
                    str(contract.prob_touch),
                    str(contract.days_to_expiration) if contract.days_to_expiration is not None else None,
                    str(contract.underlying_price) if contract.underlying_price is not None else None,
                    str(contract.validated),
                    str(contract.max_covered_call_return) if contract.max_covered_call_return is not None else None,
                    str(contract.put_return_on_risk) if contract.put_return_on_risk is not None else None,
                    str(contract.put_return_on_capital) if contract.put_return_on_capital is not None else None,
                    today
                )
                cursor.execute('''
                    INSERT INTO option_changes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', values)
            conn.commit()
            self.logger.info(f"Logged {len(all_contracts)} option changes to {db_name}")
        except Exception as e:
            self.logger.error(f"Failed to log option changes for {symbol}: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

# Example usage/demo code  # Section for demonstration and testing of the options fetching functionality; this allows standalone execution to verify RemDarwin's options data pipeline.
if __name__ == "__main__":  # Execute demo code only when script is run directly; this prevents demo execution when the module is imported by RemDarwin's main application.
    parser = argparse.ArgumentParser(description="Fetch options data for a given ticker symbol using Yahoo Finance.")  # Create argument parser for CLI support; this enables user to specify ticker via command line in RemDarwin's options fetching script.
    parser.add_argument('-t', '--ticker', required=True, help='Stock ticker symbol (e.g., AAPL)')  # Add required ticker argument; this allows dynamic specification of the stock symbol for options fetching in RemDarwin.
    parser.add_argument('--output-dir', default='./output', help='Output directory for data files')  # Add output directory argument with default; this allows specification of where to save output files in RemDarwin.
    parser.add_argument('--period', choices=['annual', 'quarterly'], default='annual', help='Financial period type')  # Add period argument with choices; this allows selection between annual and quarterly data in RemDarwin.
    parser.add_argument('--api-key', type=str, help='API key for data services')  # Add API key argument; this allows specification of API credentials for authenticated data access in RemDarwin.
    args = parser.parse_args()  # Parse command-line arguments; this processes user input for ticker symbol in RemDarwin's CLI interface.
    print(f"Parsed arguments: ticker={args.ticker}, output_dir={args.output_dir}, period={args.period}, api_key={args.api_key}")  # Print parsed arguments for verification; this provides user feedback on the parsed CLI inputs in RemDarwin.
    ticker_symbol = args.ticker.upper()  # Convert ticker to uppercase for consistency; this standardizes stock symbols in RemDarwin's data processing.
    logging.basicConfig(level=logging.INFO)  # Configure basic logging to INFO level for demo output; this enables visibility into the fetching process during RemDarwin's development and testing.
    fetcher = YFinanceOptionChainFetcher()  # Instantiate the fetcher class for options data retrieval; this creates the primary object for demonstrating RemDarwin's options fetching capabilities.
    # Fetch option chain for specified ticker
    result = fetcher.fetch_option_chain(ticker_symbol)  # Execute the main fetching method for the specified ticker options; this demonstrates RemDarwin's ability to retrieve comprehensive options data from Yahoo Finance.
    print(f"Underlying Price: {result['underlying_price']}")  # Display the fetched underlying stock price; this shows RemDarwin's integration with stock price data for options analysis.
    print(f"Total Calls fetched: {len(result['calls'])}")  # Show the count of call options retrieved; this demonstrates the volume of data RemDarwin can process for calls.
    print(f"Total Puts fetched: {len(result['puts'])}")  # Show the count of put options retrieved; this demonstrates the volume of data RemDarwin can process for puts.
    # Save to database
    fetcher.save_to_database(ticker_symbol, result)  # Save the fetched options data to the database with partitioning and indexing.
    # Print a sample contract
    if result['calls']:  # Check if calls data is available for display; this ensures safe demo output in RemDarwin's testing scenarios.
        sample_call = result['calls'][0]  # Select the first call contract as an example; this provides a concrete instance for RemDarwin's options data inspection.
        print("Sample Call:")  # Label the output for clarity; this organizes demo output in RemDarwin's development interface.
        print(sample_call)  # Display the sample call contract details; this shows the structured data format RemDarwin uses for options contracts.
    if result['puts']:  # Check if puts data is available for display; this ensures complete demo coverage in RemDarwin's testing.
        sample_put = result['puts'][0]  # Select the first put contract as an example; this complements the call example for comprehensive RemDarwin data demonstration.
        print("Sample Put:")  # Label the put output for clarity; this maintains organized demo presentation in RemDarwin's interface.
        print(sample_put)  # Display the sample put contract details; this completes the demonstration of RemDarwin's options data structure and fetching capabilities.


class YFinanceOptionChainFetcher:  # Define the YFinanceOptionChainFetcher class as the main component for fetching and processing options data from Yahoo Finance; this class encapsulates the logic for retrieving option chains, parsing data, and validating contracts, serving as the core engine for options data acquisition in RemDarwin's systematic trading system.
    def __init__(self, logger=None):  # Define the constructor method for YFinanceOptionChainFetcher, accepting an optional logger parameter; this initializes the fetcher with logging capabilities, allowing for configurable logging in RemDarwin's options data fetching operations.
        self.logger = logger or logging.getLogger(__name__)  # Assign the logger instance to the object, using the provided logger or creating a default one for this module; this enables consistent logging throughout the fetcher's operations, supporting debugging and monitoring in RemDarwin's options data pipeline.

    def fetch_option_chain(self, symbol: str):  # Define the main method to fetch the complete option chain for a given stock symbol; this method orchestrates the retrieval of all available option contracts, their parsing, validation, and organization into structured data, forming the primary interface for options data acquisition in RemDarwin's trading system.
        """
        Fetches the entire option chain (calls and puts) for the given symbol and validates basic contract data.
        Returns: Dict with 'calls' and 'puts', each a list of OptionContract instances, and 'underlying_price' of the stock.
        """
        try:  # Begin exception handling block to catch and manage errors during the options fetching process; this ensures robust operation by gracefully handling API failures, network issues, or data parsing errors, maintaining system stability in RemDarwin's data acquisition workflow.
            ticker = yf.Ticker(symbol)  # Create a Ticker object from yfinance for the specified stock symbol; this object provides access to all financial data for the stock, including options chains, serving as the primary data source interface in RemDarwin's options fetching mechanism.
            self.logger.info(f"Fetching option expirations for {symbol}")  # Log an informational message indicating the start of expiration date retrieval; this provides visibility into the fetching process, aiding in monitoring and debugging options data acquisition in RemDarwin's operational logs.
            exp_dates = ticker.options  # List of expiration date strings (YYYY-MM-DD)  # Retrieve the list of available option expiration dates from the ticker object; this collection of date strings defines the time frames for which options data will be fetched, enabling comprehensive coverage of the option chain in RemDarwin's data collection process.
            self.logger.info(f"Found {len(exp_dates)} expiration dates: {exp_dates}")  # Log the number and list of expiration dates found; this helps debug if no expirations are available.
            ic(ticker.option_chain)  # Use icecream's ic function to inspect the option_chain property of the ticker; this debugging call provides a quick view of the option chain structure, aiding in development and troubleshooting of the options data fetching logic in RemDarwin.
            all_calls = []  # Initialize an empty list to accumulate call option contracts across all expiration dates; this container will hold validated OptionContract instances for call options, enabling organized storage and processing of calls data in RemDarwin's options analysis pipeline.
            all_puts = []  # Initialize an empty list to accumulate put option contracts across all expiration dates; this container will hold validated OptionContract instances for put options, facilitating structured handling of puts data in RemDarwin's quantitative trading system.
            validation_results = []  # Initialize list to track validation results for reporting; this collects boolean outcomes of the comprehensive validation pipeline for each contract.
            try:
                hist = ticker.history(period='1d')  # Fetch the recent historical price data for the stock over the last trading day; this provides the current underlying price information needed for options valuation and moneyness calculations in RemDarwin's options analysis.
                if hist.empty:  # Check if the historical data DataFrame is empty, indicating no price data was retrieved; this handles cases where the ticker has no recent trading data, setting underlying price to None for safe processing in RemDarwin's options calculations.
                    underlying_price = None  # Set underlying_price to None when no historical data is available; this prevents invalid price values from affecting options analysis and maintains data integrity in RemDarwin's valuation models.
                else:  # If historical data is available, proceed to extract the closing price; this branch handles the normal case where price data is successfully retrieved for options pricing in RemDarwin.
                    underlying_price = hist['Close'].iloc[0]  # Extract the most recent closing price from the historical data; this provides the current underlying asset price for moneyness determination and intrinsic value calculations in RemDarwin's options framework.
                    if not underlying_price or underlying_price <= 0:  # Validate that the extracted price is positive and valid; this check ensures data quality by filtering out invalid or zero prices that could corrupt options analysis in RemDarwin.
                        self.logger.warning(f"Invalid underlying price for {symbol}: {underlying_price}")  # Log a warning for invalid prices with details; this provides visibility into data quality issues, supporting monitoring and troubleshooting in RemDarwin's data pipeline.
                        underlying_price = None  # Reset invalid price to None; this maintains consistency and prevents downstream errors from propagating through RemDarwin's options processing system.
            except Exception as e:  # Catch any exceptions during price retrieval and processing; this ensures robust error handling for network issues, API failures, or data parsing problems in RemDarwin's price fetching mechanism.
                self.logger.warning(f"Failed to fetch underlying price for {symbol}: {e}")  # Log the failure with error details; this enables debugging and operational monitoring of price data acquisition issues in RemDarwin's system.
                underlying_price = None  # Set price to None on failure; this allows the options fetching to continue without underlying price data, maintaining system resilience in RemDarwin's data processing workflow.
            for exp in exp_dates:  # Iterate over each available expiration date to fetch options chains; this loop ensures comprehensive coverage of all expiration periods, enabling complete option chain retrieval for RemDarwin's analysis across different time horizons.
                self.logger.info(f"Fetching options for expiration: {exp}")  # Log the current expiration being processed; this provides progress tracking and debugging information for options data fetching operations in RemDarwin's logging system.
                opt_chain = ticker.option_chain(exp)  # Retrieve the option chain (calls and puts) for the specific expiration date from yfinance; this fetches the raw options data that will be parsed and validated for RemDarwin's options database.
                # Process calls
                calls_count = 0
                calls_valid = 0
                for row in opt_chain.calls.itertuples():  # Iterate through each call option row in the DataFrame; this processes individual call contracts, extracting and structuring their data for RemDarwin's quantitative analysis.
                    calls_count += 1
                    contract = self._parse_option_row(row, symbol, 'call', exp, underlying_price)  # Parse the raw row data into an OptionContract instance for calls; this converts yfinance's DataFrame row into a structured object with all necessary fields for RemDarwin's options processing.
                    # Enhanced validation pipeline with comprehensive data validation
                    contract_dict = contract_to_dict(contract)
                    if validate_option_data(contract_dict):
                        greeks_dict = {k: v for k, v in contract_dict.items() if k in ['delta', 'gamma', 'theta', 'vega', 'rho']}
                        if validate_greeks(greeks_dict):
                            filled = gap_fill_missing_data(contract_dict)
                            normalized = normalize_option_data(filled)
                            contract = update_contract_from_dict(contract, normalized)
                            if self._validate_contract(contract):  # Final validation check
                                all_calls.append(contract)
                                calls_valid += 1
                                validation_results.append(True)
                            else:
                                validation_results.append(False)
                        else:
                            validation_results.append(False)
                    else:
                        validation_results.append(False)
                # Process puts
                puts_count = 0
                puts_valid = 0
                for row in opt_chain.puts.itertuples():  # Iterate through each put option row in the DataFrame; this processes individual put contracts, enabling comprehensive put option data extraction for RemDarwin's trading strategies.
                    puts_count += 1
                    contract = self._parse_option_row(row, symbol, 'put', exp, underlying_price)  # Parse the raw row data into an OptionContract instance for puts; this structures put option data into RemDarwin's standardized format for analysis and decision-making.
                    # Enhanced validation pipeline with comprehensive data validation
                    contract_dict = contract_to_dict(contract)
                    if validate_option_data(contract_dict):
                        greeks_dict = {k: v for k, v in contract_dict.items() if k in ['delta', 'gamma', 'theta', 'vega', 'rho']}
                        if validate_greeks(greeks_dict):
                            filled = gap_fill_missing_data(contract_dict)
                            normalized = normalize_option_data(filled)
                            contract = update_contract_from_dict(contract, normalized)
                            if self._validate_contract(contract):  # Final validation check
                                all_puts.append(contract)
                                puts_valid += 1
                                validation_results.append(True)
                            else:
                                validation_results.append(False)
                        else:
                            validation_results.append(False)
                    else:
                        validation_results.append(False)
                self.logger.info(f"Expiration {exp}: {calls_count} calls parsed, {calls_valid} valid; {puts_count} puts parsed, {puts_valid} valid")  # Log processing statistics for each expiration; this helps debug validation issues.
            self.logger.info(f"Fetched {len(all_calls)} calls and {len(all_puts)} puts for {symbol}")  # Log the successful completion with counts of fetched contracts; this provides summary statistics for monitoring the effectiveness of options data acquisition in RemDarwin's system.
            # Generate validation report
            report = generate_validation_report(validation_results)
            return {  # Return the complete options data structure with all fetched and validated contracts; this delivers the processed options chain data to RemDarwin's downstream analysis and trading components.
                'calls': all_calls,  # Include the list of validated call option contracts; this provides call options data for RemDarwin's call-based trading strategies and analysis.
                'puts': all_puts,  # Include the list of validated put option contracts; this provides put options data for RemDarwin's put-based trading strategies and risk management.
                'underlying_price': underlying_price,  # Include the fetched underlying stock price; this enables moneyness calculations and intrinsic value assessments in RemDarwin's options valuation models.
                'fetch_timestamp': datetime.utcnow(),  # Include the UTC timestamp of the fetch operation; this provides temporal context for data freshness and supports time-series analysis in RemDarwin's options system.
                'validation_report': report  # Include the validation report with success metrics; this provides insights into data quality and validation effectiveness for RemDarwin's monitoring.
            }
        except Exception as e:  # Catch any unhandled exceptions during the entire fetching process; this provides a safety net for unexpected errors, ensuring RemDarwin's system remains stable even with API or processing failures.
            self.logger.error(f"Failed to fetch options for {symbol}: {e}")  # Log the critical error with details; this enables debugging and alerts for system failures in RemDarwin's options data pipeline.
            return {  # Return an empty data structure on failure; this maintains API consistency while indicating that no valid options data was retrieved for RemDarwin's processing.
                'calls': [],  # Return empty list for calls on error; this prevents downstream components from attempting to process invalid data in RemDarwin's system.
                'puts': [],  # Return empty list for puts on error; this ensures safe failure handling in RemDarwin's options analysis pipeline.
                'underlying_price': None,  # Return None for price on error; this clearly indicates price unavailability to RemDarwin's valuation calculations.
                'fetch_timestamp': datetime.utcnow()  # Include timestamp even on failure; this provides timing context for error analysis in RemDarwin's monitoring and logging system.
            }

    def _parse_option_row(self, row, symbol, option_type, expiration_date_str, underlying_price):  # Define the private method to parse raw yfinance DataFrame rows into OptionContract objects; this method handles data type conversion, NaN handling, and field extraction for both call and put options in RemDarwin's data processing pipeline.
        """ Parse a row from yfinance option DataFrame into an OptionContract. """
        expiration_date = datetime.strptime(expiration_date_str, "%Y-%m-%d")  # Parse the expiration date string into a datetime object; this converts the string format from yfinance into a usable date for RemDarwin's temporal calculations and contract identification.
        days_to_expiration = (expiration_date - datetime.utcnow()).days  # Calculate the number of days until expiration from the current UTC time; this temporal metric is crucial for time value decay analysis and expiration-based strategies in RemDarwin's options framework.
        implied_vol = getattr(row, 'impliedVolatility', None)  # Extract the implied volatility value from the row, handling missing attributes gracefully; this retrieves the market's volatility expectation for pricing models in RemDarwin's options valuation.
        iv = implied_vol if implied_vol is not None else 0.0  # Set implied volatility to extracted value or default to 0.0 for missing data; this ensures a valid IV value for RemDarwin's calculations, preventing NaN propagation.

        strike = getattr(row, 'strike', 0)  # Extract the strike price from the row, defaulting to 0 if missing; this gets the key price level that determines option moneyness for RemDarwin's analysis.
        strike_price = float(strike) if not pd.isna(strike) else 0.0  # Convert strike to float if valid, otherwise use 0.0; this ensures numeric strike price data for RemDarwin's calculations, handling pandas NaN values safely.

        # Calculate option Greeks using binomial model for American options (default) if valid data is available
        if underlying_price and iv > 0:  # Check for valid underlying price and implied volatility to enable Greek calculations; this ensures RemDarwin only computes Greeks with reliable market data.
            T_years = days_to_expiration / 365.0  # Convert days to expiration to years for options calculations; this standardizes time units for RemDarwin's options valuation models.
            # Calculate each Greek individually using binomial model as default for American options
            delta = calculate_delta(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate delta using binomial model for American options
            gamma = calculate_gamma(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate gamma using binomial model for American options
            theta = calculate_theta(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate theta using binomial model for American options
            vega = calculate_vega(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate vega using binomial model for American options
            rho = calculate_rho(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate rho using binomial model for American options
            # Use Black-Scholes for probabilities (approximation for American options)
            d1 = (math.log(underlying_price / strike_price) + (0.05 - 0.0 + 0.5 * iv**2) * T_years) / (iv * math.sqrt(T_years))  # Calculate d1 for probabilities; this approximates moneyness for American options.
            d2 = d1 - iv * math.sqrt(T_years)  # Calculate d2 for probabilities
            prob_itm = norm.cdf(d2) if option_type.lower() == 'call' else norm.cdf(-d2)  # Probability in the money
            prob_otm = 1 - prob_itm  # Probability out of the money
            prob_touch = prob_itm  # Probability touching strike, approximated
            greeks = {'delta': delta, 'gamma': gamma, 'theta': theta, 'vega': vega, 'rho': rho, 'prob_itm': prob_itm, 'prob_otm': prob_otm, 'prob_touch': prob_touch}  # Build greeks dictionary with calculated values
        else:  # If insufficient data for Greek calculation, set to zero; this provides safe defaults for RemDarwin's data processing when market data is unavailable.
            greeks = {'delta': 0.0, 'gamma': 0.0, 'theta': 0.0, 'vega': 0.0, 'rho': 0.0, 'prob_itm': 0.0, 'prob_otm': 0.0, 'prob_touch': 0.0}  # Assign zero values to all Greeks when calculation is not possible; this maintains data consistency in RemDarwin's options data structure.

        bid = getattr(row, 'bid', 0)  # Extract the bid price from the row; this gets the buyer's maximum offer price for liquidity analysis in RemDarwin's options trading decisions.
        bid_price = float(bid) if not pd.isna(bid) else 0.0  # Convert bid to float if valid; this provides numeric bid data for spread calculations in RemDarwin's market analysis.

        # Calculate strategy-specific returns
        max_covered_call_return = None
        put_return_on_risk = None
        put_return_on_capital = None
        if option_type == 'call' and underlying_price is not None:
            max_covered_call_return = strike_price - underlying_price + bid_price
        elif option_type == 'put':
            if strike_price > bid_price:
                put_return_on_risk = (bid_price / (strike_price - bid_price)) * 100
            put_return_on_capital = (bid_price / strike_price) * 100

        ask = getattr(row, 'ask', 0)  # Extract the ask price from the row; this gets the seller's minimum asking price for pricing analysis in RemDarwin's options strategies.
        ask_price = float(ask) if not pd.isna(ask) else 0.0  # Convert ask to float if valid; this ensures numeric ask data for RemDarwin's spread and execution cost evaluations.

        last = getattr(row, 'lastPrice', 0)  # Extract the last traded price from the row; this provides the most recent market price for real-time analysis in RemDarwin's options monitoring.
        last_price = float(last) if not pd.isna(last) else 0.0  # Convert last price to float if valid; this gives numeric last price data for price movement tracking in RemDarwin's system.

        vol = getattr(row, 'volume', 0)  # Extract the trading volume from the row; this indicates daily trading activity for liquidity assessment in RemDarwin's options analysis.
        volume = int(vol) if not pd.isna(vol) else 0  # Convert volume to integer if valid; this provides numeric volume data for RemDarwin's market activity evaluations.

        oi = getattr(row, 'openInterest', 0)  # Extract the open interest from the row; this shows outstanding contracts for market participation analysis in RemDarwin's strategies.
        open_interest = int(oi) if not pd.isna(oi) else 0  # Convert open interest to integer if valid; this gives numeric OI data for RemDarwin's contract liquidity and positioning analysis.

        ch = getattr(row, 'change', 0)  # Extract the price change from the row; this shows daily price movement for trend analysis in RemDarwin's options strategies.
        change = float(ch) if not pd.isna(ch) else 0.0  # Convert change to float if valid; this provides numeric change data for RemDarwin's price movement tracking.

        pch = getattr(row, 'percentChange', 0)  # column for % Change  # Extract the percentage change from the row; this indicates relative price movement for comparative analysis in RemDarwin's quantitative models.
        percent_change = float(pch) if not pd.isna(pch) else 0.0  # Convert percent change to float if valid; this gives numeric percentage data for RemDarwin's relative performance evaluations.

        return OptionContract(  # Create and return a new OptionContract instance with all parsed and processed data; this constructs the structured object that encapsulates option contract information for RemDarwin's analysis and storage.
            symbol=symbol,
            expiration_date=expiration_date,
            strike_price=strike_price,
            option_type=option_type,
            bid=bid_price,
            ask=ask_price,
            last_price=last_price,
            volume=volume,
            open_interest=open_interest,
            implied_volatility=iv,
            change=change,
            percent_change=percent_change,
            delta=greeks['delta'],
            gamma=greeks['gamma'],
            theta=greeks['theta'],
            vega=greeks['vega'],
            rho=greeks['rho'],
            prob_itm=greeks['prob_itm'],
            prob_otm=greeks['prob_otm'],
            prob_touch=greeks['prob_touch'],
            days_to_expiration=days_to_expiration,
            underlying_price=underlying_price,
            max_covered_call_return=max_covered_call_return,
            put_return_on_risk=put_return_on_risk,
            put_return_on_capital=put_return_on_capital,
            validated=False
        )

    def _validate_contract(self, contract: OptionContract) -> bool:  # Define the private validation method to check OptionContract data quality; this method applies business rules to ensure contracts are suitable for RemDarwin's quantitative analysis and trading decisions.
        """ Basic filter to ensure contract data validity before downstream processing. """
        # Basic bid-ask validation (relaxed to allow zero prices and equal bid/ask for data population)
        if (contract.bid is None or contract.ask is None or contract.ask < contract.bid or contract.bid < 0 or contract.ask < 0):  # Check for invalid bid/ask prices, allowing zero values and equal prices to populate more data for analysis.
            self.logger.debug(f"Invalid bid/ask for {contract.symbol} {contract.option_type} "
                              f"strike {contract.strike_price} exp {contract.expiration_date}")  # Log debug information for invalid bid/ask combinations; this aids in troubleshooting data quality issues in RemDarwin's validation process.
            return False  # Reject the contract due to invalid pricing data; this prevents corrupted price information from affecting RemDarwin's trading decisions.
        # Volume and Open Interest must be non-negative
        if contract.volume < 0 or contract.open_interest < 0:  # Validate that volume and open interest are non-negative; negative values indicate data errors that could mislead RemDarwin's liquidity analysis.
            self.logger.debug(f"Negative volume or open interest for {contract.symbol} "
                              f"{contract.option_type} strike {contract.strike_price}")  # Log debug info for negative trading metrics; this supports data integrity monitoring in RemDarwin's system.
            return False  # Reject contracts with invalid volume/open interest; this maintains data quality for RemDarwin's market analysis.
        # Implied Volatility must be reasonable
        if contract.implied_volatility < 0 or contract.implied_volatility > 5:  # 500% IV unlikely  # Check implied volatility is within reasonable bounds; extreme IV values may indicate data errors or extraordinary market conditions that require special handling in RemDarwin.
            self.logger.debug(f"Implied volatility out of range for {contract.symbol} "
                              f"{contract.option_type} strike {contract.strike_price}")  # Log debug info for unreasonable IV values; this enables monitoring of volatility data quality in RemDarwin's risk models.
            return False  # Reject contracts with invalid IV; this prevents unreliable volatility data from corrupting RemDarwin's pricing calculations.
        # Days to expiration must be positive and reasonable
        if contract.days_to_expiration < 0 or contract.days_to_expiration > 1000:  # Validate expiration timing is reasonable; negative days indicate expired contracts, excessive days suggest data errors in RemDarwin's temporal analysis.
            self.logger.debug(f"Invalid days to expiration for {contract.symbol} "
                              f"{contract.option_type} strike {contract.strike_price}")  # Log debug info for invalid expiration timing; this supports temporal data validation in RemDarwin's options processing.
            return False  # Reject contracts with invalid expiration; this ensures only current, valid options are processed by RemDarwin's system.
        contract.validated = True  # Mark the contract as validated; this flag indicates the contract has passed all quality checks for use in RemDarwin's downstream analysis.
        return True  # Accept the validated contract; this allows the contract to proceed to RemDarwin's quantitative analysis and trading algorithms.

    def save_to_database(self, symbol: str, option_data: dict):  # Define the method to save option contracts to a SQLite database with partitioning by expiration date; this method creates partitioned tables for each expiration, adds indexes, and inserts contracts into appropriate tables for RemDarwin's data persistence.
        """
        Saves the option data to a SQLite database with partitioning by expiration date.
        Creates partitioned tables named options_YYYY_MM_DD for each unique expiration.
        Adds indexes on symbol, expiration, strike, and each Greek after table creation.
        Uses TEXT type for all columns for simplicity.
        Unique constraint on (symbol, expiration_date, strike_price, option_type) with ON CONFLICT REPLACE.
        """
        db_name = f"{symbol}_options.db"  # Create database filename based on symbol; this ensures each stock has its own options database in RemDarwin's data organization.
        try:  # Begin exception handling for database operations; this ensures robust error handling during data persistence in RemDarwin's system.
            conn = sqlite3.connect(db_name)  # Establish connection to the SQLite database; this opens or creates the options database for the given symbol in RemDarwin's local storage.
            self.logger.info(f"Connected to database {db_name}")  # Log database connection; this confirms the save process has started.
            cursor = conn.cursor()  # Create a cursor object for executing SQL commands; this provides the interface for database operations in RemDarwin's data saving process.
            # Prepare data for insertion
            all_contracts = option_data.get('calls', []) + option_data.get('puts', [])  # Combine calls and puts contracts into a single list for processing; this enables efficient data handling across all option types in RemDarwin's database operations.
            # Collect unique expiration dates
            unique_expirations = set()
            for contract in all_contracts:
                exp_str = contract.expiration_date.strftime('%Y-%m-%d')
                unique_expirations.add(exp_str)
            # Create partitioned tables for each unique expiration
            for exp in unique_expirations:
                table_name = f"options_{exp.replace('-', '_')}"
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        symbol TEXT,
                        expiration_date TEXT,
                        strike_price TEXT,
                        option_type TEXT,
                        bid TEXT,
                        ask TEXT,
                        last_price TEXT,
                        volume TEXT,
                        open_interest TEXT,
                        implied_volatility TEXT,
                        change TEXT,
                        percent_change TEXT,
                        delta TEXT,
                        gamma TEXT,
                        theta TEXT,
                        vega TEXT,
                        rho TEXT,
                        prob_itm TEXT,
                        prob_otm TEXT,
                        prob_touch TEXT,
                        days_to_expiration TEXT,
                        underlying_price TEXT,
                        validated TEXT,
                        max_covered_call_return TEXT,
                        put_return_on_risk TEXT,
                        put_return_on_capital TEXT,
                        UNIQUE(symbol, expiration_date, strike_price, option_type) ON CONFLICT REPLACE
                    )
                ''')  # Execute table creation for each partitioned table; this sets up the database schema for storing option contract data by expiration in RemDarwin's persistent storage.
            # Add indexes on symbol, expiration, strike, and each Greek for each table
            for exp in unique_expirations:
                table_name = f"options_{exp.replace('-', '_')}"
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_symbol ON {table_name} (symbol)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_expiration ON {table_name} (expiration_date)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_strike ON {table_name} (strike_price)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_delta ON {table_name} (delta)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_gamma ON {table_name} (gamma)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_theta ON {table_name} (theta)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_vega ON {table_name} (vega)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_rho ON {table_name} (rho)')
            # Insert data into appropriate partitioned tables
            for contract in all_contracts:
                exp_str = contract.expiration_date.strftime('%Y_%m_%d')
                table_name = f"options_{exp_str}"
                values = (
                    contract.symbol,
                    str(contract.expiration_date) if contract.expiration_date else None,
                    str(contract.strike_price),
                    contract.option_type,
                    str(contract.bid),
                    str(contract.ask),
                    str(contract.last_price),
                    str(contract.volume),
                    str(contract.open_interest),
                    str(contract.implied_volatility),
                    str(contract.change),
                    str(contract.percent_change),
                    str(contract.delta),
                    str(contract.gamma),
                    str(contract.theta),
                    str(contract.vega),
                    str(contract.rho),
                    str(contract.prob_itm),
                    str(contract.prob_otm),
                    str(contract.prob_touch),
                    str(contract.days_to_expiration) if contract.days_to_expiration is not None else None,
                    str(contract.underlying_price) if contract.underlying_price is not None else None,
                    str(contract.validated),
                    str(contract.max_covered_call_return) if contract.max_covered_call_return is not None else None,
                    str(contract.put_return_on_risk) if contract.put_return_on_risk is not None else None,
                    str(contract.put_return_on_capital) if contract.put_return_on_capital is not None else None
                )  # Prepare tuple of string-converted values for database insertion; this ensures all data types are compatible with TEXT columns in RemDarwin's SQLite schema.
                cursor.execute(f'''
                    INSERT OR REPLACE INTO {table_name} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', values)  # Execute INSERT OR REPLACE into the appropriate partitioned table; this handles uniqueness constraints and ensures data is saved in RemDarwin's options database.
            conn.commit()  # Commit the partitioned table inserts; this ensures the main data is saved even if history fails.
            # Create options_history table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS options_history (
                    symbol TEXT,
                    expiration_date TEXT,
                    strike_price TEXT,
                    option_type TEXT,
                    bid TEXT,
                    ask TEXT,
                    last_price TEXT,
                    volume TEXT,
                    open_interest TEXT,
                    implied_volatility TEXT,
                    change TEXT,
                    percent_change TEXT,
                    delta TEXT,
                    gamma TEXT,
                    theta TEXT,
                    vega TEXT,
                    rho TEXT,
                    prob_itm TEXT,
                    prob_otm TEXT,
                    prob_touch TEXT,
                    days_to_expiration TEXT,
                    underlying_price TEXT,
                    validated TEXT,
                    max_covered_call_return TEXT,
                    put_return_on_risk TEXT,
                    put_return_on_capital TEXT,
                    fetch_timestamp TEXT
                )
            ''')
            # Insert all contracts into options_history with fetch_timestamp
            fetch_timestamp = str(option_data.get('fetch_timestamp', datetime.utcnow()))
            for contract in all_contracts:
                values = (
                    contract.symbol,
                    str(contract.expiration_date) if contract.expiration_date else None,
                    str(contract.strike_price),
                    contract.option_type,
                    str(contract.bid),
                    str(contract.ask),
                    str(contract.last_price),
                    str(contract.volume),
                    str(contract.open_interest),
                    str(contract.implied_volatility),
                    str(contract.change),
                    str(contract.percent_change),
                    str(contract.delta),
                    str(contract.gamma),
                    str(contract.theta),
                    str(contract.vega),
                    str(contract.rho),
                    str(contract.prob_itm),
                    str(contract.prob_otm),
                    str(contract.prob_touch),
                    str(contract.days_to_expiration) if contract.days_to_expiration is not None else None,
                    str(contract.underlying_price) if contract.underlying_price is not None else None,
                    str(contract.validated),
                    str(contract.max_covered_call_return) if contract.max_covered_call_return is not None else None,
                    str(contract.put_return_on_risk) if contract.put_return_on_risk is not None else None,
                    str(contract.put_return_on_capital) if contract.put_return_on_capital is not None else None,
                    fetch_timestamp
                )
                cursor.execute('''
                    INSERT INTO options_history VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', values)
            conn.commit()  # Commit the transaction to make changes permanent; this finalizes the database save operation in RemDarwin's data persistence process.
            self.logger.info(f"Saved {len(all_contracts)} options contracts to partitioned tables and options_history in {db_name}")  # Log successful save operation with count; this provides monitoring and confirmation of data persistence in RemDarwin's logging system.
        except Exception as e:  # Catch any exceptions during database operations; this ensures error handling for connection issues, SQL errors, or data conversion problems in RemDarwin's save functionality.
            self.logger.error(f"Failed to save options data to database for {symbol}: {e}")  # Log the error with details; this enables debugging and operational monitoring of database save failures in RemDarwin's system.
        finally:  # Ensure database connection is always closed; this prevents resource leaks and maintains clean database handling in RemDarwin's data operations.
            if 'conn' in locals():  # Check if connection was established before attempting to close; this avoids errors if connection failed to open in RemDarwin's error handling.
                conn.close()  # Close the database connection; this releases resources and completes the database interaction in RemDarwin's data saving method.

    def log_option_changes(self, symbol: str, option_data: dict):
        """
        Logs option changes to a history table.
        Creates 'option_changes' table in {symbol}_options.db with same columns as 'options' plus 'EnteredDate'.
        Inserts all contracts with today's date.
        No unique constraint.
        """
        db_name = f"{symbol}_options.db"
        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS option_changes (
                    symbol TEXT,
                    expiration_date TEXT,
                    strike_price TEXT,
                    option_type TEXT,
                    bid TEXT,
                    ask TEXT,
                    last_price TEXT,
                    volume TEXT,
                    open_interest TEXT,
                    implied_volatility TEXT,
                    change TEXT,
                    percent_change TEXT,
                    delta TEXT,
                    gamma TEXT,
                    theta TEXT,
                    vega TEXT,
                    rho TEXT,
                    prob_itm TEXT,
                    prob_otm TEXT,
                    prob_touch TEXT,
                    days_to_expiration TEXT,
                    underlying_price TEXT,
                    validated TEXT,
                    max_covered_call_return TEXT,
                    put_return_on_risk TEXT,
                    put_return_on_capital TEXT,
                    EnteredDate TEXT
                )
            ''')
            all_contracts = option_data.get('calls', []) + option_data.get('puts', [])
            today = str(datetime.now().date())
            for contract in all_contracts:
                values = (
                    contract.symbol,
                    str(contract.expiration_date) if contract.expiration_date else None,
                    str(contract.strike_price),
                    contract.option_type,
                    str(contract.bid),
                    str(contract.ask),
                    str(contract.last_price),
                    str(contract.volume),
                    str(contract.open_interest),
                    str(contract.implied_volatility),
                    str(contract.change),
                    str(contract.percent_change),
                    str(contract.delta),
                    str(contract.gamma),
                    str(contract.theta),
                    str(contract.vega),
                    str(contract.rho),
                    str(contract.prob_itm),
                    str(contract.prob_otm),
                    str(contract.prob_touch),
                    str(contract.days_to_expiration) if contract.days_to_expiration is not None else None,
                    str(contract.underlying_price) if contract.underlying_price is not None else None,
                    str(contract.validated),
                    str(contract.max_covered_call_return) if contract.max_covered_call_return is not None else None,
                    str(contract.put_return_on_risk) if contract.put_return_on_risk is not None else None,
                    str(contract.put_return_on_capital) if contract.put_return_on_capital is not None else None,
                    today
                )
                cursor.execute('''
                    INSERT INTO option_changes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', values)
            conn.commit()
            self.logger.info(f"Logged {len(all_contracts)} option changes to {db_name}")
        except Exception as e:
            self.logger.error(f"Failed to log option changes for {symbol}: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

# Example usage/demo code  # Section for demonstration and testing of the options fetching functionality; this allows standalone execution to verify RemDarwin's options data pipeline.
if __name__ == "__main__":  # Execute demo code only when script is run directly; this prevents demo execution when the module is imported by RemDarwin's main application.
    parser = argparse.ArgumentParser(description="Fetch options data for a given ticker symbol using Yahoo Finance.")  # Create argument parser for CLI support; this enables user to specify ticker via command line in RemDarwin's options fetching script.
    parser.add_argument('-t', '--ticker', required=True, help='Stock ticker symbol (e.g., AAPL)')  # Add required ticker argument; this allows dynamic specification of the stock symbol for options fetching in RemDarwin.
    parser.add_argument('--output-dir', default='./output', help='Output directory for data files')  # Add output directory argument with default; this allows specification of where to save output files in RemDarwin.
    parser.add_argument('--period', choices=['annual', 'quarterly'], default='annual', help='Financial period type')  # Add period argument with choices; this allows selection between annual and quarterly data in RemDarwin.
    parser.add_argument('--api-key', type=str, help='API key for data services')  # Add API key argument; this allows specification of API credentials for authenticated data access in RemDarwin.
    args = parser.parse_args()  # Parse command-line arguments; this processes user input for ticker symbol in RemDarwin's CLI interface.
    print(f"Parsed arguments: ticker={args.ticker}, output_dir={args.output_dir}, period={args.period}, api_key={args.api_key}")  # Print parsed arguments for verification; this provides user feedback on the parsed CLI inputs in RemDarwin.
    ticker_symbol = args.ticker.upper()  # Convert ticker to uppercase for consistency; this standardizes stock symbols in RemDarwin's data processing.
    logging.basicConfig(level=logging.INFO)  # Configure basic logging to INFO level for demo output; this enables visibility into the fetching process during RemDarwin's development and testing.
    fetcher = YFinanceOptionChainFetcher()  # Instantiate the fetcher class for options data retrieval; this creates the primary object for demonstrating RemDarwin's options fetching capabilities.
    # Fetch option chain for specified ticker
    result = fetcher.fetch_option_chain(ticker_symbol)  # Execute the main fetching method for the specified ticker options; this demonstrates RemDarwin's ability to retrieve comprehensive options data from Yahoo Finance.
    print(f"Underlying Price: {result['underlying_price']}")  # Display the fetched underlying stock price; this shows RemDarwin's integration with stock price data for options analysis.
    print(f"Total Calls fetched: {len(result['calls'])}")  # Show the count of call options retrieved; this demonstrates the volume of data RemDarwin can process for calls.
    print(f"Total Puts fetched: {len(result['puts'])}")  # Show the count of put options retrieved; this demonstrates the volume of data RemDarwin can process for puts.
    # Save to database
    fetcher.save_to_database(ticker_symbol, result)  # Save the fetched options data to the database with partitioning and indexing.
    # Print a sample contract
    if result['calls']:  # Check if calls data is available for display; this ensures safe demo output in RemDarwin's testing scenarios.
        sample_call = result['calls'][0]  # Select the first call contract as an example; this provides a concrete instance for RemDarwin's options data inspection.
        print("Sample Call:")  # Label the output for clarity; this organizes demo output in RemDarwin's development interface.
        print(sample_call)  # Display the sample call contract details; this shows the structured data format RemDarwin uses for options contracts.
    if result['puts']:  # Check if puts data is available for display; this ensures complete demo coverage in RemDarwin's testing.
        sample_put = result['puts'][0]  # Select the first put contract as an example; this complements the call example for comprehensive RemDarwin data demonstration.
        print("Sample Put:")  # Label the put output for clarity; this maintains organized demo presentation in RemDarwin's interface.
        print(sample_put)  # Display the sample put contract details; this completes the demonstration of RemDarwin's options data structure and fetching capabilities.
    if not re.match(pattern, ticker):
        raise ValueError(f"Invalid ticker symbol format: {ticker}. Must be 1-5 uppercase letters.")
    # Test validation with sample inputs (implicitly done by raising)


class YFinanceOptionChainFetcher:  # Define the YFinanceOptionChainFetcher class as the main component for fetching and processing options data from Yahoo Finance; this class encapsulates the logic for retrieving option chains, parsing data, and validating contracts, serving as the core engine for options data acquisition in RemDarwin's systematic trading system.
    def __init__(self, logger=None):  # Define the constructor method for YFinanceOptionChainFetcher, accepting an optional logger parameter; this initializes the fetcher with logging capabilities, allowing for configurable logging in RemDarwin's options data fetching operations.
        self.logger = logger or logging.getLogger(__name__)  # Assign the logger instance to the object, using the provided logger or creating a default one for this module; this enables consistent logging throughout the fetcher's operations, supporting debugging and monitoring in RemDarwin's options data pipeline.

    def fetch_option_chain(self, symbol: str):  # Define the main method to fetch the complete option chain for a given stock symbol; this method orchestrates the retrieval of all available option contracts, their parsing, validation, and organization into structured data, forming the primary interface for options data acquisition in RemDarwin's trading system.
        """
        Fetches the entire option chain (calls and puts) for the given symbol and validates basic contract data.
        Returns: Dict with 'calls' and 'puts', each a list of OptionContract instances, and 'underlying_price' of the stock.
        """
        try:  # Begin exception handling block to catch and manage errors during the options fetching process; this ensures robust operation by gracefully handling API failures, network issues, or data parsing errors, maintaining system stability in RemDarwin's data acquisition workflow.
            ticker = yf.Ticker(symbol)  # Create a Ticker object from yfinance for the specified stock symbol; this object provides access to all financial data for the stock, including options chains, serving as the primary data source interface in RemDarwin's options fetching mechanism.
            self.logger.info(f"Fetching option expirations for {symbol}")  # Log an informational message indicating the start of expiration date retrieval; this provides visibility into the fetching process, aiding in monitoring and debugging options data acquisition in RemDarwin's operational logs.
            exp_dates = ticker.options  # List of expiration date strings (YYYY-MM-DD)  # Retrieve the list of available option expiration dates from the ticker object; this collection of date strings defines the time frames for which options data will be fetched, enabling comprehensive coverage of the option chain in RemDarwin's data collection process.
            self.logger.info(f"Found {len(exp_dates)} expiration dates: {exp_dates}")  # Log the number and list of expiration dates found; this helps debug if no expirations are available.
            ic(ticker.option_chain)  # Use icecream's ic function to inspect the option_chain property of the ticker; this debugging call provides a quick view of the option chain structure, aiding in development and troubleshooting of the options data fetching logic in RemDarwin.
            all_calls = []  # Initialize an empty list to accumulate call option contracts across all expiration dates; this container will hold validated OptionContract instances for call options, enabling organized storage and processing of calls data in RemDarwin's options analysis pipeline.
            all_puts = []  # Initialize an empty list to accumulate put option contracts across all expiration dates; this container will hold validated OptionContract instances for put options, facilitating structured handling of puts data in RemDarwin's quantitative trading system.
            validation_results = []  # Initialize list to track validation results for reporting; this collects boolean outcomes of the comprehensive validation pipeline for each contract.
            try:
                hist = ticker.history(period='1d')  # Fetch the recent historical price data for the stock over the last trading day; this provides the current underlying price information needed for options valuation and moneyness calculations in RemDarwin's options analysis.
                if hist.empty:  # Check if the historical data DataFrame is empty, indicating no price data was retrieved; this handles cases where the ticker has no recent trading data, setting underlying price to None for safe processing in RemDarwin's options calculations.
                    underlying_price = None  # Set underlying_price to None when no historical data is available; this prevents invalid price values from affecting options analysis and maintains data integrity in RemDarwin's valuation models.
                else:  # If historical data is available, proceed to extract the closing price; this branch handles the normal case where price data is successfully retrieved for options pricing in RemDarwin.
                    underlying_price = hist['Close'].iloc[0]  # Extract the most recent closing price from the historical data; this provides the current underlying asset price for moneyness determination and intrinsic value calculations in RemDarwin's options framework.
                    if not underlying_price or underlying_price <= 0:  # Validate that the extracted price is positive and valid; this check ensures data quality by filtering out invalid or zero prices that could corrupt options analysis in RemDarwin.
                        self.logger.warning(f"Invalid underlying price for {symbol}: {underlying_price}")  # Log a warning for invalid prices with details; this provides visibility into data quality issues, supporting monitoring and troubleshooting in RemDarwin's data pipeline.
                        underlying_price = None  # Reset invalid price to None; this maintains consistency and prevents downstream errors from propagating through RemDarwin's options processing system.
            except Exception as e:  # Catch any exceptions during price retrieval and processing; this ensures robust error handling for network issues, API failures, or data parsing problems in RemDarwin's price fetching mechanism.
                self.logger.warning(f"Failed to fetch underlying price for {symbol}: {e}")  # Log the failure with error details; this enables debugging and operational monitoring of price data acquisition issues in RemDarwin's system.
                underlying_price = None  # Set price to None on failure; this allows the options fetching to continue without underlying price data, maintaining system resilience in RemDarwin's data processing workflow.
            for exp in exp_dates:  # Iterate over each available expiration date to fetch options chains; this loop ensures comprehensive coverage of all expiration periods, enabling complete option chain retrieval for RemDarwin's analysis across different time horizons.
                self.logger.info(f"Fetching options for expiration: {exp}")  # Log the current expiration being processed; this provides progress tracking and debugging information for options data fetching operations in RemDarwin's logging system.
                opt_chain = ticker.option_chain(exp)  # Retrieve the option chain (calls and puts) for the specific expiration date from yfinance; this fetches the raw options data that will be parsed and validated for RemDarwin's options database.
                # Process calls
                calls_count = 0
                calls_valid = 0
                for row in opt_chain.calls.itertuples():  # Iterate through each call option row in the DataFrame; this processes individual call contracts, extracting and structuring their data for RemDarwin's quantitative analysis.
                    calls_count += 1
                    contract = self._parse_option_row(row, symbol, 'call', exp, underlying_price)  # Parse the raw row data into an OptionContract instance for calls; this converts yfinance's DataFrame row into a structured object with all necessary fields for RemDarwin's options processing.
                    # Enhanced validation pipeline with comprehensive data validation
                    contract_dict = contract_to_dict(contract)
                    if validate_option_data(contract_dict):
                        greeks_dict = {k: v for k, v in contract_dict.items() if k in ['delta', 'gamma', 'theta', 'vega', 'rho']}
                        if validate_greeks(greeks_dict):
                            filled = gap_fill_missing_data(contract_dict)
                            normalized = normalize_option_data(filled)
                            contract = update_contract_from_dict(contract, normalized)
                            if self._validate_contract(contract):  # Final validation check
                                all_calls.append(contract)
                                calls_valid += 1
                                validation_results.append(True)
                            else:
                                validation_results.append(False)
                        else:
                            validation_results.append(False)
                    else:
                        validation_results.append(False)
                # Process puts
                puts_count = 0
                puts_valid = 0
                for row in opt_chain.puts.itertuples():  # Iterate through each put option row in the DataFrame; this processes individual put contracts, enabling comprehensive put option data extraction for RemDarwin's trading strategies.
                    puts_count += 1
                    contract = self._parse_option_row(row, symbol, 'put', exp, underlying_price)  # Parse the raw row data into an OptionContract instance for puts; this structures put option data into RemDarwin's standardized format for analysis and decision-making.
                    # Enhanced validation pipeline with comprehensive data validation
                    contract_dict = contract_to_dict(contract)
                    if validate_option_data(contract_dict):
                        greeks_dict = {k: v for k, v in contract_dict.items() if k in ['delta', 'gamma', 'theta', 'vega', 'rho']}
                        if validate_greeks(greeks_dict):
                            filled = gap_fill_missing_data(contract_dict)
                            normalized = normalize_option_data(filled)
                            contract = update_contract_from_dict(contract, normalized)
                            if self._validate_contract(contract):  # Final validation check
                                all_puts.append(contract)
                                puts_valid += 1
                                validation_results.append(True)
                            else:
                                validation_results.append(False)
                        else:
                            validation_results.append(False)
                    else:
                        validation_results.append(False)
                self.logger.info(f"Expiration {exp}: {calls_count} calls parsed, {calls_valid} valid; {puts_count} puts parsed, {puts_valid} valid")  # Log processing statistics for each expiration; this helps debug validation issues.
            self.logger.info(f"Fetched {len(all_calls)} calls and {len(all_puts)} puts for {symbol}")  # Log the successful completion with counts of fetched contracts; this provides summary statistics for monitoring the effectiveness of options data acquisition in RemDarwin's system.
            # Generate validation report
            report = generate_validation_report(validation_results)
            return {  # Return the complete options data structure with all fetched and validated contracts; this delivers the processed options chain data to RemDarwin's downstream analysis and trading components.
                'calls': all_calls,  # Include the list of validated call option contracts; this provides call options data for RemDarwin's call-based trading strategies and analysis.
                'puts': all_puts,  # Include the list of validated put option contracts; this provides put options data for RemDarwin's put-based trading strategies and risk management.
                'underlying_price': underlying_price,  # Include the fetched underlying stock price; this enables moneyness calculations and intrinsic value assessments in RemDarwin's options valuation models.
                'fetch_timestamp': datetime.utcnow(),  # Include the UTC timestamp of the fetch operation; this provides temporal context for data freshness and supports time-series analysis in RemDarwin's options system.
                'validation_report': report  # Include the validation report with success metrics; this provides insights into data quality and validation effectiveness for RemDarwin's monitoring.
            }
        except Exception as e:  # Catch any unhandled exceptions during the entire fetching process; this provides a safety net for unexpected errors, ensuring RemDarwin's system remains stable even with API or processing failures.
            self.logger.error(f"Failed to fetch options for {symbol}: {e}")  # Log the critical error with details; this enables debugging and alerts for system failures in RemDarwin's options data pipeline.
            return {  # Return an empty data structure on failure; this maintains API consistency while indicating that no valid options data was retrieved for RemDarwin's processing.
                'calls': [],  # Return empty list for calls on error; this prevents downstream components from attempting to process invalid data in RemDarwin's system.
                'puts': [],  # Return empty list for puts on error; this ensures safe failure handling in RemDarwin's options analysis pipeline.
                'underlying_price': None,  # Return None for price on error; this clearly indicates price unavailability to RemDarwin's valuation calculations.
                'fetch_timestamp': datetime.utcnow()  # Include timestamp even on failure; this provides timing context for error analysis in RemDarwin's monitoring and logging system.
            }

    def _parse_option_row(self, row, symbol, option_type, expiration_date_str, underlying_price):  # Define the private method to parse raw yfinance DataFrame rows into OptionContract objects; this method handles data type conversion, NaN handling, and field extraction for both call and put options in RemDarwin's data processing pipeline.
        """ Parse a row from yfinance option DataFrame into an OptionContract. """
        expiration_date = datetime.strptime(expiration_date_str, "%Y-%m-%d")  # Parse the expiration date string into a datetime object; this converts the string format from yfinance into a usable date for RemDarwin's temporal calculations and contract identification.
        days_to_expiration = (expiration_date - datetime.utcnow()).days  # Calculate the number of days until expiration from the current UTC time; this temporal metric is crucial for time value decay analysis and expiration-based strategies in RemDarwin's options framework.
        implied_vol = getattr(row, 'impliedVolatility', None)  # Extract the implied volatility value from the row, handling missing attributes gracefully; this retrieves the market's volatility expectation for pricing models in RemDarwin's options valuation.
        iv = implied_vol if implied_vol is not None else 0.0  # Set implied volatility to extracted value or default to 0.0 for missing data; this ensures a valid IV value for RemDarwin's calculations, preventing NaN propagation.

        strike = getattr(row, 'strike', 0)  # Extract the strike price from the row, defaulting to 0 if missing; this gets the key price level that determines option moneyness for RemDarwin's analysis.
        strike_price = float(strike) if not pd.isna(strike) else 0.0  # Convert strike to float if valid, otherwise use 0.0; this ensures numeric strike price data for RemDarwin's calculations, handling pandas NaN values safely.

        # Calculate option Greeks using binomial model for American options (default) if valid data is available
        if underlying_price and iv > 0:  # Check for valid underlying price and implied volatility to enable Greek calculations; this ensures RemDarwin only computes Greeks with reliable market data.
            T_years = days_to_expiration / 365.0  # Convert days to expiration to years for options calculations; this standardizes time units for RemDarwin's options valuation models.
            # Calculate each Greek individually using binomial model as default for American options
            delta = calculate_delta(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate delta using binomial model for American options
            gamma = calculate_gamma(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate gamma using binomial model for American options
            theta = calculate_theta(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate theta using binomial model for American options
            vega = calculate_vega(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate vega using binomial model for American options
            rho = calculate_rho(S=underlying_price, K=strike_price, T=T_years, sigma=iv, option_type=option_type, model='binomial')  # Calculate rho using binomial model for American options
            # Use Black-Scholes for probabilities (approximation for American options)
            d1 = (math.log(underlying_price / strike_price) + (0.05 - 0.0 + 0.5 * iv**2) * T_years) / (iv * math.sqrt(T_years))  # Calculate d1 for probabilities; this approximates moneyness for American options.
            d2 = d1 - iv * math.sqrt(T_years)  # Calculate d2 for probabilities
            prob_itm = norm.cdf(d2) if option_type.lower() == 'call' else norm.cdf(-d2)  # Probability in the money
            prob_otm = 1 - prob_itm  # Probability out of the money
            prob_touch = prob_itm  # Probability touching strike, approximated
            greeks = {'delta': delta, 'gamma': gamma, 'theta': theta, 'vega': vega, 'rho': rho, 'prob_itm': prob_itm, 'prob_otm': prob_otm, 'prob_touch': prob_touch}  # Build greeks dictionary with calculated values
        else:  # If insufficient data for Greek calculation, set to zero; this provides safe defaults for RemDarwin's data processing when market data is unavailable.
            greeks = {'delta': 0.0, 'gamma': 0.0, 'theta': 0.0, 'vega': 0.0, 'rho': 0.0, 'prob_itm': 0.0, 'prob_otm': 0.0, 'prob_touch': 0.0}  # Assign zero values to all Greeks when calculation is not possible; this maintains data consistency in RemDarwin's options data structure.

        bid = getattr(row, 'bid', 0)  # Extract the bid price from the row; this gets the buyer's maximum offer price for liquidity analysis in RemDarwin's options trading decisions.
        bid_price = float(bid) if not pd.isna(bid) else 0.0  # Convert bid to float if valid; this provides numeric bid data for spread calculations in RemDarwin's market analysis.

        # Calculate strategy-specific returns
        max_covered_call_return = None
        put_return_on_risk = None
        put_return_on_capital = None
        if option_type == 'call' and underlying_price is not None:
            max_covered_call_return = strike_price - underlying_price + bid_price
        elif option_type == 'put':
            if strike_price > bid_price:
                put_return_on_risk = (bid_price / (strike_price - bid_price)) * 100
            put_return_on_capital = (bid_price / strike_price) * 100

        ask = getattr(row, 'ask', 0)  # Extract the ask price from the row; this gets the seller's minimum asking price for pricing analysis in RemDarwin's options strategies.
        ask_price = float(ask) if not pd.isna(ask) else 0.0  # Convert ask to float if valid; this ensures numeric ask data for RemDarwin's spread and execution cost evaluations.

        last = getattr(row, 'lastPrice', 0)  # Extract the last traded price from the row; this provides the most recent market price for real-time analysis in RemDarwin's options monitoring.
        last_price = float(last) if not pd.isna(last) else 0.0  # Convert last price to float if valid; this gives numeric last price data for price movement tracking in RemDarwin's system.

        vol = getattr(row, 'volume', 0)  # Extract the trading volume from the row; this indicates daily trading activity for liquidity assessment in RemDarwin's options analysis.
        volume = int(vol) if not pd.isna(vol) else 0  # Convert volume to integer if valid; this provides numeric volume data for RemDarwin's market activity evaluations.

        oi = getattr(row, 'openInterest', 0)  # Extract the open interest from the row; this shows outstanding contracts for market participation analysis in RemDarwin's strategies.
        open_interest = int(oi) if not pd.isna(oi) else 0  # Convert open interest to integer if valid; this gives numeric OI data for RemDarwin's contract liquidity and positioning analysis.

        ch = getattr(row, 'change', 0)  # Extract the price change from the row; this shows daily price movement for trend analysis in RemDarwin's options strategies.
        change = float(ch) if not pd.isna(ch) else 0.0  # Convert change to float if valid; this provides numeric change data for RemDarwin's price movement tracking.

        pch = getattr(row, 'percentChange', 0)  # column for % Change  # Extract the percentage change from the row; this indicates relative price movement for comparative analysis in RemDarwin's quantitative models.
        percent_change = float(pch) if not pd.isna(pch) else 0.0  # Convert percent change to float if valid; this gives numeric percentage data for RemDarwin's relative performance evaluations.

        return OptionContract(  # Create and return a new OptionContract instance with all parsed and processed data; this constructs the structured object that encapsulates option contract information for RemDarwin's analysis and storage.
            symbol=symbol,
            expiration_date=expiration_date,
            strike_price=strike_price,
            option_type=option_type,
            bid=bid_price,
            ask=ask_price,
            last_price=last_price,
            volume=volume,
            open_interest=open_interest,
            implied_volatility=iv,
            change=change,
            percent_change=percent_change,
            delta=greeks['delta'],
            gamma=greeks['gamma'],
            theta=greeks['theta'],
            vega=greeks['vega'],
            rho=greeks['rho'],
            prob_itm=greeks['prob_itm'],
            prob_otm=greeks['prob_otm'],
            prob_touch=greeks['prob_touch'],
            days_to_expiration=days_to_expiration,
            underlying_price=underlying_price,
            max_covered_call_return=max_covered_call_return,
            put_return_on_risk=put_return_on_risk,
            put_return_on_capital=put_return_on_capital,
            validated=False
        )

    def _validate_contract(self, contract: OptionContract) -> bool:  # Define the private validation method to check OptionContract data quality; this method applies business rules to ensure contracts are suitable for RemDarwin's quantitative analysis and trading decisions.
        """ Basic filter to ensure contract data validity before downstream processing. """
        # Basic bid-ask validation (relaxed to allow zero prices and equal bid/ask for data population)
        if (contract.bid is None or contract.ask is None or contract.ask < contract.bid or contract.bid < 0 or contract.ask < 0):  # Check for invalid bid/ask prices, allowing zero values and equal prices to populate more data for analysis.
            self.logger.debug(f"Invalid bid/ask for {contract.symbol} {contract.option_type} "
                              f"strike {contract.strike_price} exp {contract.expiration_date}")  # Log debug information for invalid bid/ask combinations; this aids in troubleshooting data quality issues in RemDarwin's validation process.
            return False  # Reject the contract due to invalid pricing data; this prevents corrupted price information from affecting RemDarwin's trading decisions.
        # Volume and Open Interest must be non-negative
        if contract.volume < 0 or contract.open_interest < 0:  # Validate that volume and open interest are non-negative; negative values indicate data errors that could mislead RemDarwin's liquidity analysis.
            self.logger.debug(f"Negative volume or open interest for {contract.symbol} "
                              f"{contract.option_type} strike {contract.strike_price}")  # Log debug info for negative trading metrics; this supports data integrity monitoring in RemDarwin's system.
            return False  # Reject contracts with invalid volume/open interest; this maintains data quality for RemDarwin's market analysis.
        # Implied Volatility must be reasonable
        if contract.implied_volatility < 0 or contract.implied_volatility > 5:  # 500% IV unlikely  # Check implied volatility is within reasonable bounds; extreme IV values may indicate data errors or extraordinary market conditions that require special handling in RemDarwin.
            self.logger.debug(f"Implied volatility out of range for {contract.symbol} "
                              f"{contract.option_type} strike {contract.strike_price}")  # Log debug info for unreasonable IV values; this enables monitoring of volatility data quality in RemDarwin's risk models.
            return False  # Reject contracts with invalid IV; this prevents unreliable volatility data from corrupting RemDarwin's pricing calculations.
        # Days to expiration must be positive and reasonable
        if contract.days_to_expiration < 0 or contract.days_to_expiration > 1000:  # Validate expiration timing is reasonable; negative days indicate expired contracts, excessive days suggest data errors in RemDarwin's temporal analysis.
            self.logger.debug(f"Invalid days to expiration for {contract.symbol} "
                              f"{contract.option_type} strike {contract.strike_price}")  # Log debug info for invalid expiration timing; this supports temporal data validation in RemDarwin's options processing.
            return False  # Reject contracts with invalid expiration; this ensures only current, valid options are processed by RemDarwin's system.
        contract.validated = True  # Mark the contract as validated; this flag indicates the contract has passed all quality checks for use in RemDarwin's downstream analysis.
        return True  # Accept the validated contract; this allows the contract to proceed to RemDarwin's quantitative analysis and trading algorithms.

    def save_to_database(self, symbol: str, option_data: dict):  # Define the method to save option contracts to a SQLite database with partitioning by expiration date; this method creates partitioned tables for each expiration, adds indexes, and inserts contracts into appropriate tables for RemDarwin's data persistence.
        """
        Saves the option data to a SQLite database with partitioning by expiration date.
        Creates partitioned tables named options_YYYY_MM_DD for each unique expiration.
        Adds indexes on symbol, expiration, strike, and each Greek after table creation.
        Uses TEXT type for all columns for simplicity.
        Unique constraint on (symbol, expiration_date, strike_price, option_type) with ON CONFLICT REPLACE.
        """
        db_name = f"{symbol}_options.db"  # Create database filename based on symbol; this ensures each stock has its own options database in RemDarwin's data organization.
        try:  # Begin exception handling for database operations; this ensures robust error handling during data persistence in RemDarwin's system.
            conn = sqlite3.connect(db_name)  # Establish connection to the SQLite database; this opens or creates the options database for the given symbol in RemDarwin's local storage.
            self.logger.info(f"Connected to database {db_name}")  # Log database connection; this confirms the save process has started.
            cursor = conn.cursor()  # Create a cursor object for executing SQL commands; this provides the interface for database operations in RemDarwin's data saving process.
            # Prepare data for insertion
            all_contracts = option_data.get('calls', []) + option_data.get('puts', [])  # Combine calls and puts contracts into a single list for processing; this enables efficient data handling across all option types in RemDarwin's database operations.
            # Collect unique expiration dates
            unique_expirations = set()
            for contract in all_contracts:
                exp_str = contract.expiration_date.strftime('%Y-%m-%d')
                unique_expirations.add(exp_str)
            # Create partitioned tables for each unique expiration
            for exp in unique_expirations:
                table_name = f"options_{exp.replace('-', '_')}"
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        symbol TEXT,
                        expiration_date TEXT,
                        strike_price TEXT,
                        option_type TEXT,
                        bid TEXT,
                        ask TEXT,
                        last_price TEXT,
                        volume TEXT,
                        open_interest TEXT,
                        implied_volatility TEXT,
                        change TEXT,
                        percent_change TEXT,
                        delta TEXT,
                        gamma TEXT,
                        theta TEXT,
                        vega TEXT,
                        rho TEXT,
                        prob_itm TEXT,
                        prob_otm TEXT,
                        prob_touch TEXT,
                        days_to_expiration TEXT,
                        underlying_price TEXT,
                        validated TEXT,
                        max_covered_call_return TEXT,
                        put_return_on_risk TEXT,
                        put_return_on_capital TEXT,
                        UNIQUE(symbol, expiration_date, strike_price, option_type) ON CONFLICT REPLACE
                    )
                ''')  # Execute table creation for each partitioned table; this sets up the database schema for storing option contract data by expiration in RemDarwin's persistent storage.
            # Add indexes on symbol, expiration, strike, and each Greek for each table
            for exp in unique_expirations:
                table_name = f"options_{exp.replace('-', '_')}"
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_symbol ON {table_name} (symbol)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_expiration ON {table_name} (expiration_date)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_strike ON {table_name} (strike_price)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_delta ON {table_name} (delta)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_gamma ON {table_name} (gamma)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_theta ON {table_name} (theta)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_vega ON {table_name} (vega)')
                cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_rho ON {table_name} (rho)')
            # Insert data into appropriate partitioned tables
            for contract in all_contracts:
                exp_str = contract.expiration_date.strftime('%Y_%m_%d')
                table_name = f"options_{exp_str}"
                values = (
                    contract.symbol,
                    str(contract.expiration_date) if contract.expiration_date else None,
                    str(contract.strike_price),
                    contract.option_type,
                    str(contract.bid),
                    str(contract.ask),
                    str(contract.last_price),
                    str(contract.volume),
                    str(contract.open_interest),
                    str(contract.implied_volatility),
                    str(contract.change),
                    str(contract.percent_change),
                    str(contract.delta),
                    str(contract.gamma),
                    str(contract.theta),
                    str(contract.vega),
                    str(contract.rho),
                    str(contract.prob_itm),
                    str(contract.prob_otm),
                    str(contract.prob_touch),
                    str(contract.days_to_expiration) if contract.days_to_expiration is not None else None,
                    str(contract.underlying_price) if contract.underlying_price is not None else None,
                    str(contract.validated),
                    str(contract.max_covered_call_return) if contract.max_covered_call_return is not None else None,
                    str(contract.put_return_on_risk) if contract.put_return_on_risk is not None else None,
                    str(contract.put_return_on_capital) if contract.put_return_on_capital is not None else None
                )  # Prepare tuple of string-converted values for database insertion; this ensures all data types are compatible with TEXT columns in RemDarwin's SQLite schema.
                cursor.execute(f'''
                    INSERT OR REPLACE INTO {table_name} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', values)  # Execute INSERT OR REPLACE into the appropriate partitioned table; this handles uniqueness constraints and ensures data is saved in RemDarwin's options database.
            conn.commit()  # Commit the partitioned table inserts; this ensures the main data is saved even if history fails.
            # Create options_history table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS options_history (
                    symbol TEXT,
                    expiration_date TEXT,
                    strike_price TEXT,
                    option_type TEXT,
                    bid TEXT,
                    ask TEXT,
                    last_price TEXT,
                    volume TEXT,
                    open_interest TEXT,
                    implied_volatility TEXT,
                    change TEXT,
                    percent_change TEXT,
                    delta TEXT,
                    gamma TEXT,
                    theta TEXT,
                    vega TEXT,
                    rho TEXT,
                    prob_itm TEXT,
                    prob_otm TEXT,
                    prob_touch TEXT,
                    days_to_expiration TEXT,
                    underlying_price TEXT,
                    validated TEXT,
                    max_covered_call_return TEXT,
                    put_return_on_risk TEXT,
                    put_return_on_capital TEXT,
                    fetch_timestamp TEXT
                )
            ''')
            # Insert all contracts into options_history with fetch_timestamp
            fetch_timestamp = str(option_data.get('fetch_timestamp', datetime.utcnow()))
            for contract in all_contracts:
                values = (
                    contract.symbol,
                    str(contract.expiration_date) if contract.expiration_date else None,
                    str(contract.strike_price),
                    contract.option_type,
                    str(contract.bid),
                    str(contract.ask),
                    str(contract.last_price),
                    str(contract.volume),
                    str(contract.open_interest),
                    str(contract.implied_volatility),
                    str(contract.change),
                    str(contract.percent_change),
                    str(contract.delta),
                    str(contract.gamma),
                    str(contract.theta),
                    str(contract.vega),
                    str(contract.rho),
                    str(contract.prob_itm),
                    str(contract.prob_otm),
                    str(contract.prob_touch),
                    str(contract.days_to_expiration) if contract.days_to_expiration is not None else None,
                    str(contract.underlying_price) if contract.underlying_price is not None else None,
                    str(contract.validated),
                    str(contract.max_covered_call_return) if contract.max_covered_call_return is not None else None,
                    str(contract.put_return_on_risk) if contract.put_return_on_risk is not None else None,
                    str(contract.put_return_on_capital) if contract.put_return_on_capital is not None else None,
                    fetch_timestamp
                )
                cursor.execute('''
                    INSERT INTO options_history VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', values)
            conn.commit()  # Commit the transaction to make changes permanent; this finalizes the database save operation in RemDarwin's data persistence process.
            self.logger.info(f"Saved {len(all_contracts)} options contracts to partitioned tables and options_history in {db_name}")  # Log successful save operation with count; this provides monitoring and confirmation of data persistence in RemDarwin's logging system.
        except Exception as e:  # Catch any exceptions during database operations; this ensures error handling for connection issues, SQL errors, or data conversion problems in RemDarwin's save functionality.
            self.logger.error(f"Failed to save options data to database for {symbol}: {e}")  # Log the error with details; this enables debugging and operational monitoring of database save failures in RemDarwin's system.
        finally:  # Ensure database connection is always closed; this prevents resource leaks and maintains clean database handling in RemDarwin's data operations.
            if 'conn' in locals():  # Check if connection was established before attempting to close; this avoids errors if connection failed to open in RemDarwin's error handling.
                conn.close()  # Close the database connection; this releases resources and completes the database interaction in RemDarwin's data saving method.

    def log_option_changes(self, symbol: str, option_data: dict):
        """
        Logs option changes to a history table.
        Creates 'option_changes' table in {symbol}_options.db with same columns as 'options' plus 'EnteredDate'.
        Inserts all contracts with today's date.
        No unique constraint.
        """
        db_name = f"{symbol}_options.db"
        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS option_changes (
                    symbol TEXT,
                    expiration_date TEXT,
                    strike_price TEXT,
                    option_type TEXT,
                    bid TEXT,
                    ask TEXT,
                    last_price TEXT,
                    volume TEXT,
                    open_interest TEXT,
                    implied_volatility TEXT,
                    change TEXT,
                    percent_change TEXT,
                    delta TEXT,
                    gamma TEXT,
                    theta TEXT,
                    vega TEXT,
                    rho TEXT,
                    prob_itm TEXT,
                    prob_otm TEXT,
                    prob_touch TEXT,
                    days_to_expiration TEXT,
                    underlying_price TEXT,
                    validated TEXT,
                    max_covered_call_return TEXT,
                    put_return_on_risk TEXT,
                    put_return_on_capital TEXT,
                    EnteredDate TEXT
                )
            ''')
            all_contracts = option_data.get('calls', []) + option_data.get('puts', [])
            today = str(datetime.now().date())
            for contract in all_contracts:
                values = (
                    contract.symbol,
                    str(contract.expiration_date) if contract.expiration_date else None,
                    str(contract.strike_price),
                    contract.option_type,
                    str(contract.bid),
                    str(contract.ask),
                    str(contract.last_price),
                    str(contract.volume),
                    str(contract.open_interest),
                    str(contract.implied_volatility),
                    str(contract.change),
                    str(contract.percent_change),
                    str(contract.delta),
                    str(contract.gamma),
                    str(contract.theta),
                    str(contract.vega),
                    str(contract.rho),
                    str(contract.prob_itm),
                    str(contract.prob_otm),
                    str(contract.prob_touch),
                    str(contract.days_to_expiration) if contract.days_to_expiration is not None else None,
                    str(contract.underlying_price) if contract.underlying_price is not None else None,
                    str(contract.validated),
                    str(contract.max_covered_call_return) if contract.max_covered_call_return is not None else None,
                    str(contract.put_return_on_risk) if contract.put_return_on_risk is not None else None,
                    str(contract.put_return_on_capital) if contract.put_return_on_capital is not None else None,
                    today
                )
                cursor.execute('''
                    INSERT INTO option_changes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', values)
            conn.commit()
            self.logger.info(f"Logged {len(all_contracts)} option changes to {db_name}")
        except Exception as e:
            self.logger.error(f"Failed to log option changes for {symbol}: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

# Example usage/demo code  # Section for demonstration and testing of the options fetching functionality; this allows standalone execution to verify RemDarwin's options data pipeline.
if __name__ == "__main__":  # Execute demo code only when script is run directly; this prevents demo execution when the module is imported by RemDarwin's main application.
    parser = argparse.ArgumentParser(description="Fetch options data for a given ticker symbol using Yahoo Finance.")  # Create argument parser for CLI support; this enables user to specify ticker via command line in RemDarwin's options fetching script.
    parser.add_argument('-t', '--ticker', required=True, help='Stock ticker symbol (e.g., AAPL)')  # Add required ticker argument; this allows dynamic specification of the stock symbol for options fetching in RemDarwin.
    parser.add_argument('--output-dir', default='./output', help='Output directory for data files')  # Add output directory argument with default; this allows specification of where to save output files in RemDarwin.
    parser.add_argument('--period', choices=['annual', 'quarterly'], default='annual', help='Financial period type')  # Add period argument with choices; this allows selection between annual and quarterly data in RemDarwin.
    parser.add_argument('--api-key', type=str, help='API key for data services')  # Add API key argument; this allows specification of API credentials for authenticated data access in RemDarwin.
    args = parser.parse_args()  # Parse command-line arguments; this processes user input for ticker symbol in RemDarwin's CLI interface.
    print(f"Parsed arguments: ticker={args.ticker}, output_dir={args.output_dir}, period={args.period}, api_key={args.api_key}")  # Print parsed arguments for verification; this provides user feedback on the parsed CLI inputs in RemDarwin.
    ticker_symbol = args.ticker.upper()  # Convert ticker to uppercase for consistency; this standardizes stock symbols in RemDarwin's data processing.
    logging.basicConfig(level=logging.INFO)  # Configure basic logging to INFO level for demo output; this enables visibility into the fetching process during RemDarwin's development and testing.
    fetcher = YFinanceOptionChainFetcher()  # Instantiate the fetcher class for options data retrieval; this creates the primary object for demonstrating RemDarwin's options fetching capabilities.
    # Fetch option chain for specified ticker
    result = fetcher.fetch_option_chain(ticker_symbol)  # Execute the main fetching method for the specified ticker options; this demonstrates RemDarwin's ability to retrieve comprehensive options data from Yahoo Finance.
    print(f"Underlying Price: {result['underlying_price']}")  # Display the fetched underlying stock price; this shows RemDarwin's integration with stock price data for options analysis.
    print(f"Total Calls fetched: {len(result['calls'])}")  # Show the count of call options retrieved; this demonstrates the volume of data RemDarwin can process for calls.
    print(f"Total Puts fetched: {len(result['puts'])}")  # Show the count of put options retrieved; this demonstrates the volume of data RemDarwin can process for puts.
    # Save to database
    fetcher.save_to_database(ticker_symbol, result)  # Save the fetched options data to the database with partitioning and indexing.
    # Print a sample contract
    if result['calls']:  # Check if calls data is available for display; this ensures safe demo output in RemDarwin's testing scenarios.
        sample_call = result['calls'][0]  # Select the first call contract as an example; this provides a concrete instance for RemDarwin's options data inspection.
        print("Sample Call:")  # Label the output for clarity; this organizes demo output in RemDarwin's development interface.
        print(sample_call)  # Display the sample call contract details; this shows the structured data format RemDarwin uses for options contracts.
    if result['puts']:  # Check if puts data is available for display; this ensures complete demo coverage in RemDarwin's testing.
        sample_put = result['puts'][0]  # Select the first put contract as an example; this complements the call example for comprehensive RemDarwin data demonstration.
        print("Sample Put:")  # Label the put output for clarity; this maintains organized demo presentation in RemDarwin's interface.
        print(sample_put)  # Display the sample put contract details; this completes the demonstration of RemDarwin's options data structure and fetching capabilities.