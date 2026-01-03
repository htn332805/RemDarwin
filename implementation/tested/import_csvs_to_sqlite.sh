#!/bin/bash

# import_csvs_to_sqlite.sh
#
# This shell script imports multiple CSV files into a SQLite database.
# It takes two arguments: the stock ticker and the folder containing the CSV files.
# The script uses the existing save_to_database.py script to import each CSV.
#
# Usage: ./import_csvs_to_sqlite.sh TICKER FOLDER
# Example: ./import_csvs_to_sqlite.sh CSCO ./data
#
# The script will create or update <TICKER>_sqlite.db and import the specified CSVs
# into corresponding tables. For ratios_ttm and stock_price_change CSVs, it adds
# the --date-column EnteredDate flag.

set -e  # Exit on any error



# Function to import a single CSV
import_csv() {
    local ticker="$1"
    local file="$2"
    local table="$3"

    echo "Processing: $file -> table: $table"

    if [[ "$table" == "ratios_ttm" ]] || [[ "$table" == "stock_price_change" ]]; then
        echo "  Importing with date column: EnteredDate"
        python3 ../save_to_database.py -t "$ticker" -i "$file" -d "$table" --date-column EnteredDate
    else
        python3 ../save_to_database.py -t "$ticker" -i "$file" -d "$table"
    fi

    echo "  Successfully imported $file"
}

# Main function
main() {
    if [[ $# -ne 2 ]]; then
        echo "Error: Exactly 2 arguments required: TICKER FOLDER"
        echo "Usage: $0 TICKER FOLDER"
        echo "Example: $0 CSCO ./data"
        exit 1
    fi

    local ticker="$1"
    local folder="$2"

    if [[ ! -d "$folder" ]]; then
        echo "Error: Folder '$folder' not found"
        exit 1
    fi

    cd "$folder"
    local db_path="./${ticker}_sqlite.db"

    echo "Starting CSV import process for ticker: $ticker, folder: $folder"
    echo "Database: $db_path"

    # List of CSV base names to import
    local csv_bases=(
        "analyst_estimates_annual"
        "analyst_estimates_quarterly"
        "analyst_recommendations"
        "balance_sheet_annual"
        "balance_sheet_growth_annual"
        "balance_sheet_growth_quarterly"
        "balance_sheet_quarterly"
        "cash_flow_statement_annual"
        "cash_flow_statement_growth_annual"
        "cash_flow_statement_growth_quarterly"
        "cash_flow_statement_quarterly"
        "discounted_cash_flow"
        "enterprise_values_annual"
        "enterprise_values_quarterly"
        "financial_growth_annual"
        "financial_growth_quarterly"
        "historical_market_cap"
        "historical_rating"
        "income_statement_annual"
        "income_statement_growth_annual"
        "income_statement_growth_quarterly"
        "income_statement_quarterly"
        "institutional_holder"
        "key_metrics_annual"
        "key_metrics_quarterly"
        "key_metrics_ttm"
        "rating"
        "ratios_annual"
        "ratios_quarterly"
        "technical_indicators"
        "historical_prices"
        "ratios_ttm"
        "stock_price_change"
    )

    local success_count=0
    local error_count=0

    # Process each CSV
    for base in "${csv_bases[@]}"; do
        local file="${ticker}_${base}.csv"
        if [[ -f "$file" ]]; then
            if import_csv "$ticker" "$file" "$base"; then
                ((success_count++))
            else
                ((error_count++))
                echo "  Failed to import $base"
            fi
        else
            echo "Skipping $base: file $file not found"
        fi
    done

    echo "Import process completed."
    echo "Successful imports: $success_count"
    echo "Failed imports: $error_count"
    echo "Total processed: $((success_count + error_count))"
}

# Run main function
main "$@"