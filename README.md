# fmp_fetcher.py

A command-line interface (CLI) tool for fetching comprehensive financial data from the Financial Modeling Prep (FMP) API. This script is part of the MyCFATool project, designed for institutional-grade financial analysis, providing automated retrieval of financial statements, ratios, metrics, historical prices, and more for specified stock tickers.

## Features

- **Comprehensive Data Coverage**: Retrieves income statements, balance sheets, cash flow statements, financial ratios, enterprise values, key metrics, analyst estimates, owner earnings, scores, ratings, historical prices, insider trading data, technical indicators, and more.
- **Flexible Periods**: Supports both annual and quarterly financial data where applicable.
- **Secure Authentication**: Uses environment variables for API key management.
- **CSV Export**: Automatically saves fetched data to CSV files for auditability and analysis.
- **Logging**: Detailed file-based logging for operation tracking and error recording.
- **Error Handling**: Robust error handling for API responses, network issues, and file operations.
- **Extensible Design**: Modular structure for easy addition of new data types and processing logic.

## Installation

### Prerequisites
- Python 3.7 or higher
- A valid Financial Modeling Prep (FMP) API key (obtain from [Financial Modeling Prep](https://financialmodelingprep.com/developer/docs))

### Install Dependencies
```bash
pip install requests python-dotenv
```

## Configuration

1. Create a `.env` file in the project root directory.
2. Add your FMP API key to the `.env` file:

```
FMP_API_KEY=your_actual_api_key_here
```

**Security Note**: Never commit the `.env` file to version control. Add `.env` to your `.gitignore` file.

## Usage

### Basic Usage
```bash
python fmp_fetcher.py --ticker AAPL --output ./output --period annual
```

This fetches annual financial data for Apple Inc. (AAPL) and saves it to the `./output` directory.

### Command-Line Arguments

| Argument | Short | Description | Default | Required |
|----------|-------|-------------|---------|----------|
| `--ticker` | `-t` | Stock ticker symbol to fetch data for | AAPL | No |
| `--output` | `-o` | Output directory to save CSV files | ./output | No |
| `--period` | `-p` | Period for financial data: 'annual' or 'quarterly' | annual | No |

### Examples

1. **Fetch quarterly data for Tesla**:
   ```bash
   python fmp_fetcher.py --ticker TSLA --period quarterly
   ```

2. **Fetch annual data and save to a custom directory**:
   ```bash
   python fmp_fetcher.py --ticker MSFT --output ./financial_data --period annual
   ```

3. **Use default settings (AAPL, annual, ./output)**:
   ```bash
   python fmp_fetcher.py
   ```

## Output Description

The script fetches data from 26+ FMP API endpoints and saves each dataset as a separate CSV file in the specified output directory. File naming convention: `{ticker}_{data_type}_{period}.csv` or `{ticker}_{data_type}.csv` for non-period data.

### Sample Output Files
For ticker `AAPL` with period `annual`:
- `AAPL_income_statement_annual.csv`
- `AAPL_balance_sheet_annual.csv`
- `AAPL_cash_flow_statement_annual.csv`
- `AAPL_ratios_annual.csv`
- `AAPL_analyst_estimates_annual.csv`
- `AAPL_rating.csv`
- `AAPL_historical_price_full.csv`
- `AAPL_technical_indicators.csv`
- And many more...

### CSV Format
- **Headers**: Column names derived from FMP API response fields (e.g., `date`, `revenue`, `totalAssets`, `peRatioTTM`)
- **Rows**: One row per data point (e.g., one row per fiscal period)
- **Data Types**: Mostly numeric values, dates, and strings
- **Missing Data**: Represented as empty strings or null values

### Log File
- **Filename**: `fmp_fetcher.log` (in the output directory)
- **Content**: Timestamped entries for each fetch operation, successes, failures, and any errors
- **Format**: Standard logging format with timestamps, log levels, and messages

### Console Output
At the end of execution, the script displays a summary:
```
Summary:
Total fetches attempted: 26
Successful: 25
Failed: 1
```

## Data Categories

The script fetches the following data categories:

### Period-Dependent (Annual/Quarterly)
- Income Statement
- Balance Sheet
- Cash Flow Statement
- Ratios
- Enterprise Values
- Financial Growth
- Balance Sheet Growth
- Income Statement Growth
- Cash Flow Statement Growth
- Key Metrics
- Analyst Estimates

### Non-Period Dependent
- Owner Earnings
- Score
- Key Metrics TTM
- Ratios TTM
- Discounted Cash Flow
- Advanced DCF
- Advanced Levered DCF
- Rating
- Historical Rating
- Historical Price Dividend
- Historical Price Full
- Historical Sectors Performance
- Employee Count
- Shares Float
- Analyst Recommendations
- Historical Market Cap
- Earning Calendar
- Institutional Holder
- ETF Sector Weightings
- Historical Price EOD
- Stock Price Change

### Special Categories
- **Insider Trading**: All, Purchases, Sales
- **Technical Indicators**: SMA, EMA, RSI, MACD, WMA, DEMA, TEMA, Williams, ADX, Standard Deviation

## Troubleshooting

### Common Issues

1. **API Key Not Found**
   - **Error**: "Error: FMP_API_KEY environment variable not found."
   - **Solution**: Ensure `.env` file exists in the project root and contains `FMP_API_KEY=your_key`

2. **Network/Connection Errors**
   - **Error**: "Error fetching data: [connection error]"
   - **Solution**: Check internet connection and FMP API status

3. **Invalid Ticker Symbol**
   - **Error**: No data fetched for certain categories
   - **Solution**: Verify ticker symbol is valid on FMP API

4. **Permission Errors**
   - **Error**: "Error writing to CSV file"
   - **Solution**: Ensure write permissions for the output directory

5. **Rate Limiting**
   - **Error**: API returns 429 status code
   - **Solution**: Wait and retry, or upgrade FMP API plan for higher limits

6. **Missing Dependencies**
   - **Error**: ImportError for requests or dotenv
   - **Solution**: Install dependencies with `pip install requests python-dotenv`

### Debugging
- Check the `fmp_fetcher.log` file for detailed error messages and operation status
- Use `--help` to verify command-line arguments
- Test with a known working ticker like `AAPL`

## Integration with MyCFATool

This script is the data ingestion component of the MyCFATool platform. The fetched CSV files serve as the foundation for:
- SQLite database storage
- Financial ratio computation and validation
- Technical analysis
- Forecasting
- Interactive Dash dashboard visualization

For the full MyCFATool experience, see the project brief in `projectBrief.md`.

## API Limits and Usage
- FMP API has rate limits depending on your subscription tier
- Free tier: Limited requests per day
- Paid tiers: Higher limits for production use
- Monitor your usage on the FMP dashboard

## Contributing
This is part of the MyCFATool project. Contributions should follow the project's coding standards and include appropriate tests.

## License
MIT License - See LICENSE file for details.

## ratio_trend_charts.py

A command-line tool for generating trend charts of key financial ratios from CSV data fetched by fmp_fetcher.py. This script calculates liquidity, solvency, and profitability ratios and creates visual trend plots.

### Features

- **Ratio Calculations**: Computes current ratio, quick ratio, cash ratio, debt-to-equity, debt-to-assets, interest coverage, ROE, ROA, gross margin, operating margin, and net margin.
- **Chart Generation**: Creates line or bar charts for ratio trends over time.
- **Flexible Output**: Saves PNG charts to a specified directory.
- **Data Validation**: Handles missing data and invalid calculations gracefully.
- **Logging**: Detailed logging for debugging and monitoring.
- **CSV Export**: Saves calculated ratios to a CSV file named `{ticker}_ratios_{period}.csv` with all calculated ratios.

### Prerequisites

- Python 3.7 or higher
- Required libraries: pandas, numpy, matplotlib
- Financial data CSV files (from fmp_fetcher.py)

### Installation

Ensure dependencies are installed:
```bash
pip install pandas numpy matplotlib
```

### Usage

#### Basic Usage
```bash
python ratio_trend_charts.py -t CSCO
```

Generates annual ratio trend charts for Cisco Systems (CSCO) using data in the default 'data' directory.

#### Command-Line Arguments

| Argument | Short | Description | Default | Required |
|----------|-------|-------------|---------|----------|
| `--ticker` | `-t` | Stock ticker symbol | None | Yes |
| `--directory` | `-d` | Directory containing CSV files | data | No |
| `--quarterly` | `-q` | Use quarterly data instead of annual | False | No |
| `--chart-type` | `-c` | Chart type: 'line' or 'bar' | line | No |
| `--output-dir` | `-o` | Output directory for PNG files | charts | No |

#### Examples

1. **Generate quarterly bar charts for Apple**:
   ```bash
   python ratio_trend_charts.py -t AAPL -q -c bar -o ./charts
   ```

2. **Generate annual line charts using custom data directory**:
   ```bash
   python ratio_trend_charts.py -t MSFT -d ./financial_data -o ./output_charts
   ```

3. **Default annual line charts**:
   ```bash
   python ratio_trend_charts.py -t TSLA
   ```

### Output

- **PNG Files**: One PNG per ratio, named `{ticker}_{category}_{ratio_name}_{period}.png`
- **CSV File**: One CSV file containing all calculated ratios, named `{ticker}_ratios_{period}.csv`
- **Log File**: `ratio_trend_charts.log` in the current directory
- **Console Output**: Summary of generated charts

### Required CSV Files

The script expects the following CSV files in the data directory:
- `{ticker}_balance_sheet_{period}.csv`
- `{ticker}_income_statement_{period}.csv`
- `{ticker}_cash_flow_statement_{period}.csv` (currently unused)

### Troubleshooting

- **Missing Data**: Ensure CSV files are present and contain required columns.
- **No Plots Generated**: Check log file for warnings about missing columns or empty data.
- **Import Errors**: Install required packages.

## command.py

A command-line interface (CLI) tool for computing fundamental financial ratios. This script allows users to calculate various financial ratios by providing the necessary input values as command-line arguments.

### Features

- **Comprehensive Ratio Calculations**: Supports a wide range of financial ratios including liquidity, profitability, solvency, efficiency, valuation, and per-share metrics.
- **Input Validation**: Validates input types, handles division by zero, and provides informative error messages.
- **Flexible CLI**: Easy-to-use command-line interface with metric selection and positional arguments for inputs.
- **Extensible Design**: Modular class-based structure for easy addition of new ratios.

### Prerequisites

- Python 3.7 or higher

### Usage

#### Basic Usage
```bash
python3 command.py -m current_ratio 2000000 1000000
```

This computes the current ratio with current assets = 2,000,000 and current liabilities = 1,000,000, outputting 2.0.

#### Command-Line Arguments

| Argument | Short | Description | Required |
|----------|-------|-------------|----------|
| `--metric` | `-m` | The ratio to compute (e.g., current_ratio, quick_ratio) | Yes |
| `inputs` | | Positional arguments for the ratio inputs (floats) | Yes |

#### Examples

1. **Compute Quick Ratio**:
   ```bash
   python3 command.py -m quick_ratio 2000000 500000 1000000
   ```
   Inputs: current_assets, inventory, current_liabilities

2. **Compute Return on Assets**:
   ```bash
   python3 command.py -m return_on_assets 100000 5000000
   ```
   Inputs: net_income, total_assets

3. **Compute Price to Earnings Ratio**:
   ```bash
   python3 command.py -m price_earnings_ratio 150 3
   ```
   Inputs: market_price_per_share, earnings_per_share

#### Supported Ratios

The script supports the following ratios (replace underscores with spaces for readability):

- Liquidity: current_ratio, quick_ratio, cash_ratio
- Profitability: gross_profit_margin, operating_profit_margin, net_profit_margin, return_on_assets, return_on_equity, effective_tax_rate, etc.
- Solvency: debt_ratio, debt_equity_ratio, interest_coverage, etc.
- Efficiency: days_of_sales_outstanding, receivables_turnover, inventory_turnover, asset_turnover, etc.
- Valuation: price_to_book_ratio, price_to_sales_ratio, price_earnings_ratio, dividend_yield, etc.
- Per-Share: revenue_per_share, net_income_per_share, cash_per_share, book_value_per_share, etc.
- And many more...

For a complete list and required inputs, refer to the source code docstrings.

### Output

- **Success**: Prints the computed ratio value.
- **Error**: Prints an error message if inputs are invalid or missing.

### Error Handling

- **Missing Inputs**: "Missing required input: [input_name]"
- **Invalid Types**: "Inputs must be numeric"
- **Division by Zero**: "Division by zero: [denominator] cannot be zero"
- **Unknown Ratio**: "Error: Ratio '[ratio]' not implemented."

### Integration

This script complements the data fetched by fmp_fetcher.py, allowing manual computation and verification of ratios.

## Author
Auto-generated for MyCFATool project.

## Version
1.0.0