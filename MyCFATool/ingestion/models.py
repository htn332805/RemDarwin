from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, Boolean, JSON, ForeignKey, Index, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from flask_login import UserMixin

Base = declarative_base()

class Ticker(Base):
    __tablename__ = 'ticker'

    ticker_id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False, unique=True)
    company_name = Column(String)
    exchange = Column(String)
    sector = Column(String)
    industry = Column(String)
    currency = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_ticker_symbol', 'symbol'),
        Index('idx_ticker_exchange', 'exchange'),
        Index('idx_ticker_sector', 'sector'),
    )

class DataSource(Base):
    __tablename__ = 'data_source'

    source_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    api_version = Column(String)
    retrieved_at = Column(DateTime, default=datetime.utcnow)

class IncomeStatement(Base):
    __tablename__ = 'income_statement'

    statement_id = Column(Integer, primary_key=True, autoincrement=True)
    ticker_id = Column(Integer, ForeignKey('ticker.ticker_id'), nullable=False)
    period_type = Column(String, CheckConstraint("period_type IN ('annual', 'quarterly')"), nullable=False)
    fiscal_date = Column(String, nullable=False)
    fiscal_year = Column(Integer)
    fiscal_quarter = Column(Integer)
    statement_data = Column(JSON, nullable=False)
    source_id = Column(Integer, ForeignKey('data_source.source_id'))
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_income_statement_lookup', 'ticker_id', 'period_type', 'fiscal_date'),
        Index('idx_income_statement_date', 'fiscal_date'),
        Index('idx_income_statement_ticker_date', 'ticker_id', 'fiscal_date'),
        Index('idx_income_statement_year', 'ticker_id', 'fiscal_year'),
    )

class BalanceSheet(Base):
    __tablename__ = 'balance_sheet'

    statement_id = Column(Integer, primary_key=True, autoincrement=True)
    ticker_id = Column(Integer, ForeignKey('ticker.ticker_id'), nullable=False)
    period_type = Column(String, CheckConstraint("period_type IN ('annual', 'quarterly')"), nullable=False)
    fiscal_date = Column(String, nullable=False)
    fiscal_year = Column(Integer)
    fiscal_quarter = Column(Integer)
    statement_data = Column(JSON, nullable=False)
    source_id = Column(Integer, ForeignKey('data_source.source_id'))
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_balance_sheet_lookup', 'ticker_id', 'period_type', 'fiscal_date'),
        Index('idx_balance_sheet_date', 'fiscal_date'),
        Index('idx_balance_sheet_ticker_date', 'ticker_id', 'fiscal_date'),
        Index('idx_balance_sheet_year', 'ticker_id', 'fiscal_year'),
    )

class CashFlow(Base):
    __tablename__ = 'cash_flow'

    statement_id = Column(Integer, primary_key=True, autoincrement=True)
    ticker_id = Column(Integer, ForeignKey('ticker.ticker_id'), nullable=False)
    period_type = Column(String, CheckConstraint("period_type IN ('annual', 'quarterly')"), nullable=False)
    fiscal_date = Column(String, nullable=False)
    fiscal_year = Column(Integer)
    fiscal_quarter = Column(Integer)
    statement_data = Column(JSON, nullable=False)
    source_id = Column(Integer, ForeignKey('data_source.source_id'))
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_cash_flow_lookup', 'ticker_id', 'period_type', 'fiscal_date'),
        Index('idx_cash_flow_date', 'fiscal_date'),
        Index('idx_cash_flow_ticker_date', 'ticker_id', 'fiscal_date'),
        Index('idx_cash_flow_year', 'ticker_id', 'fiscal_year'),
    )

class HistoricalPrice(Base):
    __tablename__ = 'historical_price'

    price_id = Column(Integer, primary_key=True, autoincrement=True)
    ticker_id = Column(Integer, ForeignKey('ticker.ticker_id'), nullable=False)
    trade_date = Column(String, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    adj_close = Column(Float)
    volume = Column(Integer)
    extra_data = Column(JSON)
    source_id = Column(Integer, ForeignKey('data_source.source_id'))
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_historical_price_lookup', 'ticker_id', 'trade_date'),
        Index('idx_historical_price_date', 'trade_date'),
        Index('idx_historical_price_ticker_date_desc', 'ticker_id', 'trade_date'),
    )

class FinancialRatioReported(Base):
    __tablename__ = 'financial_ratio_reported'

    ratio_id = Column(Integer, primary_key=True, autoincrement=True)
    ticker_id = Column(Integer, ForeignKey('ticker.ticker_id'), nullable=False)
    period_type = Column(String, CheckConstraint("period_type IN ('annual', 'quarterly')"), nullable=False)
    fiscal_date = Column(String, nullable=False)
    ratio_data = Column(JSON, nullable=False)
    source_id = Column(Integer, ForeignKey('data_source.source_id'))
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_financial_ratio_reported_lookup', 'ticker_id', 'period_type', 'fiscal_date'),
        Index('idx_financial_ratio_reported_date', 'fiscal_date'),
        Index('idx_financial_ratio_reported_ticker_date', 'ticker_id', 'fiscal_date'),
    )

class FinancialRatioComputed(Base):
    __tablename__ = 'financial_ratio_computed'

    ratio_id = Column(Integer, primary_key=True, autoincrement=True)
    ticker_id = Column(Integer, ForeignKey('ticker.ticker_id'), nullable=False)
    period_type = Column(String, CheckConstraint("period_type IN ('annual', 'quarterly')"), nullable=False)
    fiscal_date = Column(String, nullable=False)
    ratio_data = Column(JSON, nullable=False)
    calculation_version = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_financial_ratio_computed_lookup', 'ticker_id', 'period_type', 'fiscal_date'),
    )

class KeyMetrics(Base):
    __tablename__ = 'key_metrics'

    metric_id = Column(Integer, primary_key=True, autoincrement=True)
    ticker_id = Column(Integer, ForeignKey('ticker.ticker_id'), nullable=False)
    period_type = Column(String, CheckConstraint("period_type IN ('annual', 'quarterly')"), nullable=False)
    fiscal_date = Column(String, nullable=False)
    metric_data = Column(JSON, nullable=False)
    source_id = Column(Integer, ForeignKey('data_source.source_id'))
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_key_metrics_lookup', 'ticker_id', 'period_type', 'fiscal_date'),
    )

class Forecast(Base):
    __tablename__ = 'forecast'

    forecast_id = Column(Integer, primary_key=True, autoincrement=True)
    ticker_id = Column(Integer, ForeignKey('ticker.ticker_id'), nullable=False)
    model_name = Column(String, nullable=False)
    target_variable = Column(String, nullable=False)
    forecast_start_date = Column(String)
    forecast_end_date = Column(String)
    forecast_data = Column(JSON, nullable=False)
    model_parameters = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_forecast_lookup', 'ticker_id', 'model_name', 'target_variable'),
    )

class AuditRatioValidation(Base):
    __tablename__ = 'audit_ratio_validation'

    audit_id = Column(Integer, primary_key=True, autoincrement=True)
    ticker_id = Column(Integer, ForeignKey('ticker.ticker_id'), nullable=False)
    fiscal_date = Column(String, nullable=False)
    ratio_name = Column(String, nullable=False)
    reported_value = Column(Float)
    computed_value = Column(Float)
    absolute_diff = Column(Float)
    relative_diff = Column(Float)
    pass_flag = Column(Integer, CheckConstraint("pass_flag IN (0,1)"))
    tolerance = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_audit_ratio_validation_lookup', 'ticker_id', 'fiscal_date', 'ratio_name'),
    )

class UpdateLog(Base):
    __tablename__ = 'update_log'

    update_id = Column(Integer, primary_key=True, autoincrement=True)
    ticker_id = Column(Integer, ForeignKey('ticker.ticker_id'), nullable=False)
    table_name = Column(String, nullable=False)
    records_added = Column(Integer)
    records_skipped = Column(Integer)
    update_type = Column(String)
    executed_at = Column(DateTime, default=datetime.utcnow)

class User(Base, UserMixin):
    __tablename__ = 'user'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    api_key = Column(String)  # Optional API key for FMP
    created_at = Column(DateTime, default=datetime.utcnow)

    def get_id(self):
        return str(self.user_id)