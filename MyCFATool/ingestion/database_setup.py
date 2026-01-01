from ..core.database import db_manager
from .models import Base, Ticker, DataSource

def create_database_schema():
    """
    Create the database schema using SQLAlchemy.
    """
    # Create all tables
    Base.metadata.create_all(db_manager.engine)
    print("Database schema created")

def initialize_ticker_and_source(ticker_symbol: str):
    """
    Initialize ticker and data source records.

    Args:
        ticker_symbol: The ticker symbol (e.g., 'AAPL')
    """
    with db_manager.session() as session:
        try:
            # Insert ticker if not exists
            existing_ticker = session.query(Ticker).filter_by(symbol=ticker_symbol).first()
            if not existing_ticker:
                ticker = Ticker(symbol=ticker_symbol)
                session.add(ticker)
                print(f"Inserted new ticker: {ticker_symbol}")

            # Insert data source if not exists
            existing_source = session.query(DataSource).filter_by(name="FMP", provider="Financial Modeling Prep").first()
            if not existing_source:
                source = DataSource(name="FMP", provider="Financial Modeling Prep", api_version="v3")
                session.add(source)
                print(f"Inserted new data source: FMP")

            session.commit()
            print(f"Initialized ticker {ticker_symbol} and data source")
        except Exception as e:
            session.rollback()
            print(f"Error initializing ticker and source: {e}")
            raise

class DatabaseConnection:
    """
    Compatibility class for PDFExporter to use the new repository architecture.
    """
    def __init__(self, config_path):
        self.config_path = config_path
        from MyCFATool.domain.repositories.financial_data_repository import FinancialDataRepository
        self.repo = FinancialDataRepository()

    def load_financial_data(self, ticker, period):
        """
        Load combined financial data for the latest period.
        """
        balance = self.repo.get_balance_sheet(ticker, period, 'latest')
        income = self.repo.get_income_statement(ticker, period, 'latest')
        if balance and income:
            data = balance['statement_data'].copy()
            data.update(income['statement_data'])
            return data
        return None

    def load_income_statement(self, ticker, period):
        """
        Load income statement data as list of dicts.
        """
        statements = self.repo.get_income_statement(ticker, period)
        return [{
            'fiscal_date': s['fiscal_date'],
            'revenue': s['statement_data'].get('revenue', 0),
            'netIncome': s['statement_data'].get('netIncome', 0)
        } for s in statements]

    def load_balance_sheet(self, ticker, period):
        """
        Load balance sheet data as list of dicts.
        """
        statements = self.repo.get_balance_sheet(ticker, period)
        return [{
            'fiscal_date': s['fiscal_date'],
            'totalAssets': s['statement_data'].get('totalAssets', 0),
            'totalLiabilities': s['statement_data'].get('totalLiabilities', 0),
            'totalStockholdersEquity': s['statement_data'].get('totalShareholdersEquity', 0)
        } for s in statements]

if __name__ == "__main__":
    # Example usage
    ticker = "AAPL"
    create_database_schema()
    initialize_ticker_and_source(ticker)