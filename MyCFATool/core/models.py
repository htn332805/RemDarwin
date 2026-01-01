from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime


class FinancialStatement(BaseModel):
    """Base model for financial statements"""
    ticker: str = Field(..., min_length=1, max_length=10)
    period_type: str = Field(..., regex=r'^(annual|quarterly)$')
    fiscal_date: str = Field(..., regex=r'^\d{4}-\d{2}-\d{2}$')
    fiscal_year: Optional[int] = Field(None, ge=1900, le=2100)
    fiscal_quarter: Optional[int] = Field(None, ge=1, le=4)
    currency: str = Field(default='USD', min_length=3, max_length=3)
    data: Dict[str, Any] = Field(...)


class IncomeStatementData(BaseModel):
    """Data structure for income statement"""
    revenue: Optional[float] = Field(None, ge=0)
    costOfRevenue: Optional[float] = Field(None, ge=0)
    grossProfit: Optional[float] = Field(None, ge=0)
    operatingExpenses: Optional[float] = Field(None, ge=0)
    operatingIncome: Optional[float] = Field(None, ge=0)
    interestExpense: Optional[float] = Field(None, ge=0)
    incomeBeforeTax: Optional[float] = Field(None, ge=0)
    incomeTaxExpense: Optional[float] = Field(None, ge=0)
    netIncome: Optional[float] = Field(None)
    eps: Optional[float] = Field(None)
    epsDiluted: Optional[float] = Field(None)
    weightedAverageSharesOutstanding: Optional[float] = Field(None, gt=0)
    weightedAverageSharesOutstandingDiluted: Optional[float] = Field(None, gt=0)


class BalanceSheetData(BaseModel):
    """Data structure for balance sheet"""
    totalAssets: Optional[float] = Field(None, ge=0)
    totalCurrentAssets: Optional[float] = Field(None, ge=0)
    cashAndCashEquivalents: Optional[float] = Field(None, ge=0)
    shortTermInvestments: Optional[float] = Field(None, ge=0)
    netReceivables: Optional[float] = Field(None, ge=0)
    inventory: Optional[float] = Field(None, ge=0)
    otherCurrentAssets: Optional[float] = Field(None, ge=0)
    totalNonCurrentAssets: Optional[float] = Field(None, ge=0)
    propertyPlantEquipmentNet: Optional[float] = Field(None, ge=0)
    goodwill: Optional[float] = Field(None, ge=0)
    intangibleAssets: Optional[float] = Field(None, ge=0)
    longTermInvestments: Optional[float] = Field(None, ge=0)
    totalLiabilities: Optional[float] = Field(None, ge=0)
    totalCurrentLiabilities: Optional[float] = Field(None, ge=0)
    shortTermDebt: Optional[float] = Field(None, ge=0)
    accountsPayable: Optional[float] = Field(None, ge=0)
    totalNonCurrentLiabilities: Optional[float] = Field(None, ge=0)
    longTermDebt: Optional[float] = Field(None, ge=0)
    totalEquity: Optional[float] = Field(None)
    retainedEarnings: Optional[float] = Field(None)
    commonStock: Optional[float] = Field(None, ge=0)


class CashFlowData(BaseModel):
    """Data structure for cash flow statement"""
    netIncome: Optional[float] = Field(None)
    operatingCashFlow: Optional[float] = Field(None)
    cashFlowFromOperations: Optional[float] = Field(None)
    cashFlowFromInvesting: Optional[float] = Field(None)
    cashFlowFromFinancing: Optional[float] = Field(None)
    capitalExpenditure: Optional[float] = Field(None, le=0)  # Usually negative
    freeCashFlow: Optional[float] = Field(None)
    netChangeInCash: Optional[float] = Field(None)
    cashAtBeginningOfPeriod: Optional[float] = Field(None, ge=0)
    cashAtEndOfPeriod: Optional[float] = Field(None, ge=0)


class RatioData(BaseModel):
    """Data structure for financial ratios"""
    peRatio: Optional[float] = Field(None, gt=0)
    pbRatio: Optional[float] = Field(None, gt=0)
    priceToSalesRatio: Optional[float] = Field(None, gt=0)
    priceToBookRatio: Optional[float] = Field(None, gt=0)
    priceToCashFlowRatio: Optional[float] = Field(None, gt=0)
    priceToFreeCashFlowRatio: Optional[float] = Field(None, gt=0)
    enterpriseValue: Optional[float] = Field(None)
    enterpriseValueOverEBITDA: Optional[float] = Field(None, gt=0)
    returnOnEquity: Optional[float] = Field(None)
    returnOnAssets: Optional[float] = Field(None)
    returnOnCapitalEmployed: Optional[float] = Field(None)
    debtToEquity: Optional[float] = Field(None, ge=0)
    debtToAssets: Optional[float] = Field(None, ge=0, le=1)
    currentRatio: Optional[float] = Field(None, gt=0)
    quickRatio: Optional[float] = Field(None, gt=0)
    cashRatio: Optional[float] = Field(None, gt=0)
    grossMargin: Optional[float] = Field(None, ge=0, le=1)
    operatingMargin: Optional[float] = Field(None, ge=-1, le=1)
    netMargin: Optional[float] = Field(None, ge=-1, le=1)
    dividendYield: Optional[float] = Field(None, ge=0)
    payoutRatio: Optional[float] = Field(None, ge=0, le=1)


class ForecastInput(BaseModel):
    """Input data for forecasting models"""
    ticker: str = Field(..., min_length=1, max_length=10)
    variable: str = Field(..., min_length=1)  # e.g., 'revenue', 'netIncome'
    historical_data: List[float] = Field(..., min_items=2)
    periods_ahead: int = Field(..., gt=0, le=10)
    model_type: str = Field(default='linear', regex=r'^(linear|exponential|arima)$')
    confidence_level: float = Field(default=0.95, gt=0, lt=1)


class PriceData(BaseModel):
    """Individual price data point"""
    date: str = Field(..., regex=r'^\d{4}-\d{2}-\d{2}$')
    open: Optional[float] = Field(None, gt=0)
    high: Optional[float] = Field(None, gt=0)
    low: Optional[float] = Field(None, gt=0)
    close: float = Field(..., gt=0)
    adj_close: Optional[float] = Field(None, gt=0)
    volume: Optional[int] = Field(None, ge=0)


class TechnicalIndicatorInput(BaseModel):
    """Input data for technical analysis indicators"""
    ticker: str = Field(..., min_length=1, max_length=10)
    price_data: List[PriceData] = Field(..., min_items=1)
    indicators: List[str] = Field(default=[], items={'type': 'string', 'enum': ['SMA', 'EMA', 'RSI', 'MACD', 'BollingerBands']})
    periods: Dict[str, int] = Field(default={})  # e.g., {'SMA': 20, 'RSI': 14}

    @validator('price_data')
    def sort_price_data_by_date(cls, v):
        return sorted(v, key=lambda x: x.date)