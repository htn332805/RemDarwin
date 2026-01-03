#!/usr/bin/env python3
"""
save_to_database.py

This script imports CSV data into SQLite databases with duplicate prevention.
It provides a command-line interface for processing CSV files and storing their
data in SQLite databases, ensuring that duplicate entries are handled appropriately.

Usage:
    python save_to_database.py -t TICKER -i INPUT_CSV -d TABLE_NAME [-n COLUMN_NAME]

Examples:
    python save_to_database.py -t AAPL -i data/AAPL_stock_data.csv -d stock_prices
    python save_to_database.py --ticker MSFT --input data/MSFT.csv --table financials --date-column date

Arguments:
    -t TICKER, --ticker TICKER
        The stock ticker symbol (required)
    -i INPUT_CSV, --input INPUT_CSV
        Path to the input CSV file (required, must be readable)
    -d TABLE_NAME, --table TABLE_NAME
        Name of the database table (required)
    -n COLUMN_NAME, --date-column COLUMN_NAME
        Name of the date column (optional, used for date-based operations)

The script uses argparse for CLI, sqlite3 for database operations,
csv for reading CSV files, logging for output, os/sys for system interactions,
and datetime for timestamp handling.
"""

import sqlite3
import csv
import argparse
import logging
import os
import sys
import datetime

def read_csv_data(csv_path):
    """
    Read CSV data from the specified path and return column names and data rows.

    Args:
        csv_path (str): Path to the CSV file.

    Returns:
        tuple: (column_names list, data_rows list of dicts)
    """
    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            column_names = reader.fieldnames
            data_rows = list(reader)

        # Infer data types based on sample data (first row)
        type_inference = {}
        if data_rows:
            sample_row = data_rows[0]
            for col in column_names:
                value = sample_row.get(col, '')
                if value == '':
                    type_inference[col] = 'TEXT'
                else:
                    try:
                        int(value)
                        type_inference[col] = 'INTEGER'
                    except ValueError:
                        try:
                            float(value)
                            type_inference[col] = 'REAL'
                        except ValueError:
                            type_inference[col] = 'TEXT'

        logging.info(f"Successfully read CSV file: {csv_path}")
        logging.info(f"Column names: {column_names}")
        logging.info(f"Inferred types: {type_inference}")
        logging.info(f"Number of data rows: {len(data_rows)}")
        return column_names, data_rows, type_inference
    except FileNotFoundError:
        logging.error(f"CSV file not found: {csv_path}")
        raise
    except Exception as e:
        logging.error(f"Error reading CSV file {csv_path}: {e}")
        raise

def check_database_and_table(db_path, table_name):
    """
    Check if the database file exists, connect to it, and check if the table exists.

    Args:
        db_path (str): Path to the SQLite database file.
        table_name (str): Name of the table to check.

    Returns:
        tuple: (connection object, table_exists boolean, existing_columns list)
    """
    db_exists = os.path.exists(db_path)
    logging.info(f"Database file '{db_path}' exists: {db_exists}")

    try:
        conn = sqlite3.connect(db_path)
        logging.info(f"Connected to database: {db_path}")
    except sqlite3.Error as e:
        logging.error(f"Error connecting to database {db_path}: {e}")
        raise

    # Check if table exists
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    table_exists = cursor.fetchone() is not None
    logging.info(f"Table '{table_name}' exists in database: {table_exists}")

    existing_columns = []
    if table_exists:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()
        existing_columns = [col[1] for col in columns_info]  # column names
        logging.info(f"Existing columns in table '{table_name}': {existing_columns}")

    return conn, table_exists, existing_columns

def create_table_if_not_exists(conn, table_name, csv_columns, date_column, type_inference):
    """
    Create table if not exists with dynamic schema based on CSV columns.

    Args:
        conn: SQLite connection object
        table_name (str): Name of the table to create
        csv_columns (list): List of column names from CSV
        date_column (str or None): Name of the date column if specified
        type_inference (dict): Inferred data types for columns
    """


    # Build column definitions
    columns_sql = []
    for col in csv_columns:
        sql_type = type_inference.get(col, 'TEXT')
        if date_column and col == date_column:
            sql_type = 'DATE'
        columns_sql.append(f'"{col}" {sql_type}')

    # Add date column if specified and not already in csv_columns
    if date_column and date_column not in csv_columns:
        columns_sql.append(f'"{date_column}" DATE')

    # Generate CREATE TABLE SQL
    columns_part = ', '.join(columns_sql)
    sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" (id INTEGER PRIMARY KEY, {columns_part})'

    # Execute the SQL
    try:
        conn.execute(sql)
        logging.info(f"Created table '{table_name}' with schema: {sql}")
        # Create unique index
        unique_cols = ', '.join(f'"{col}"' for col in csv_columns)
        conn.execute(f'CREATE UNIQUE INDEX IF NOT EXISTS unique_{table_name} ON "{table_name}" ({unique_cols})')
        logging.info(f"Created unique index on table '{table_name}' for columns: {csv_columns}")
    except sqlite3.Error as e:
        logging.error(f"Error creating table {table_name}: {e}")
        raise

def alter_table_schema(conn, table_name, csv_columns, existing_columns, date_column):
    """
    Alter table schema by adding new columns from CSV if any, and update unique constraint.

    Args:
        conn: SQLite connection object
        table_name (str): Name of the table
        csv_columns (list): Columns from current CSV
        existing_columns (list): Existing columns in table
        date_column (str or None): Date column name
    """
    new_cols = set(csv_columns) - set(existing_columns)
    if date_column and date_column not in existing_columns:
        new_cols.add(date_column)

    if new_cols:
        cursor = conn.cursor()
        # Add new columns
        for col in new_cols:
            col_type = 'DATE' if date_column and col == date_column else 'TEXT'
            alter_sql = f'ALTER TABLE "{table_name}" ADD COLUMN "{col}" {col_type}'
            try:
                cursor.execute(alter_sql)
                logging.info(f"Added column '{col}' of type {col_type} to table '{table_name}'")
            except sqlite3.Error as e:
                logging.error(f"Error adding column {col} to {table_name}: {e}")
                raise
        # Update unique index
        # Drop existing unique index
        cursor.execute(f'DROP INDEX IF EXISTS unique_{table_name}')
        logging.info(f"Dropped existing unique index on table '{table_name}'")
        # Create new unique index with csv_columns
        unique_cols = ', '.join(f'"{col}"' for col in csv_columns)
        cursor.execute(f'CREATE UNIQUE INDEX unique_{table_name} ON "{table_name}" ({unique_cols})')
        logging.info(f"Created new unique index on table '{table_name}' for columns: {csv_columns}")
    else:
        logging.info(f"No new columns to add to table '{table_name}'")

def insert_csv_data(conn, table_name, csv_columns, data_rows, date_column):
    """
    Insert CSV data into the database using INSERT OR IGNORE to prevent duplicates.

    Args:
        conn: SQLite connection object
        table_name (str): Name of the table
        csv_columns (list): List of CSV column names
        data_rows (list): List of dicts representing CSV rows
        date_column (str or None): Name of the date column if specified
    """
    if not data_rows:
        logging.info("No data rows to insert.")
        return

    # Prepare column list
    col_list = csv_columns[:]
    if date_column and date_column not in col_list:
        col_list.append(date_column)

    # Prepare the INSERT OR IGNORE SQL
    placeholders = ', '.join(['?'] * len(col_list))
    columns_str = ', '.join(f'"{col}"' for col in col_list)
    sql = f'INSERT OR IGNORE INTO "{table_name}" ({columns_str}) VALUES ({placeholders})'

    # Get initial row count
    cursor = conn.cursor()
    cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
    initial_count = cursor.fetchone()[0]

    # Prepare data for insertion
    insert_data = []
    for row in data_rows:
        values = [row.get(col, None) for col in csv_columns]
        if date_column:
            values.append(datetime.datetime.now().isoformat())
        insert_data.append(tuple(values))

    # Execute batch insert
    try:
        cursor.executemany(sql, insert_data)
        conn.commit()
        logging.info(f"Inserted {cursor.rowcount} rows into table '{table_name}'")
    except sqlite3.Error as e:
        logging.error(f"Error during data insertion: {e}")
        conn.rollback()
        raise

    # Get final row count and calculate statistics
    cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
    final_count = cursor.fetchone()[0]
    successful_inserts = final_count - initial_count
    ignored_duplicates = len(data_rows) - successful_inserts

    logging.info(f"Insertion statistics: {successful_inserts} rows inserted, {ignored_duplicates} duplicates ignored")

# Basic logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('save_to_database.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    """
    Main function for the script.
    """
    parser = argparse.ArgumentParser(description="Import CSV data into SQLite database with duplicate prevention.")
    parser.add_argument('-t', '--ticker', required=True, help='The stock ticker symbol')
    parser.add_argument('-i', '--input', type=argparse.FileType('r'), required=True, help='Path to the input CSV file')
    parser.add_argument('-d', '--table', required=True, help='Name of the database table')
    parser.add_argument('-n', '--date-column', help='Name of the date column (optional)')
    args = parser.parse_args()
    logging.info(f"Parsed arguments: ticker={args.ticker}, input={args.input.name}, table={args.table}, date_column={args.date_column}")

    column_names, data_rows, type_inference = read_csv_data(args.input.name)

    db_path = f"{args.ticker}_sqlite.db"
    conn, table_exists, existing_columns = check_database_and_table(db_path, args.table)

    if not table_exists:
        create_table_if_not_exists(conn, args.table, column_names, args.date_column, type_inference)

    if table_exists:
        alter_table_schema(conn, args.table, column_names, existing_columns, args.date_column)

    # Insert CSV data
    insert_csv_data(conn, args.table, column_names, data_rows, args.date_column)

    logging.info("Data import process completed successfully.")
    conn.close()

if __name__ == '__main__':
    main()