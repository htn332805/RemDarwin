import pytest
from unittest.mock import Mock
from MyCFATool.domain.services.fundamental_analysis_service import FundamentalAnalysisService
from MyCFATool.domain.services.technical_analysis_service import TechnicalAnalysisService
from MyCFATool.domain.services.valuation_service import ValuationService
from MyCFATool.domain.services.forecasting_service import ForecastingService
from MyCFATool.domain.services.data_ingestion_service import DataIngestionService


@pytest.fixture
def fundamental_service(mocker):
    service = FundamentalAnalysisService()
    # Mock the repo methods
    service.repo.get_balance_sheet = mocker.Mock()
    service.repo.get_income_statement = mocker.Mock()
    service.repo.get_cash_flow = mocker.Mock()
    service.repo.get_historical_price_at_date = mocker.Mock()
    service.repo.get_ratios = mocker.Mock()
    service.repo.get_historical_prices = mocker.Mock()
    service.repo.get_historical_prices_ordered = mocker.Mock()
    service.repo.ticker_repo.get_ticker_id = mocker.Mock(return_value=1)
    return service


@pytest.fixture
def technical_service(mocker):
    service = TechnicalAnalysisService()
    service.repo.get_historical_prices_ordered = mocker.Mock()
    service.repo.ticker_repo.get_ticker_id = mocker.Mock(return_value=1)
    return service


@pytest.fixture
def valuation_service(mocker):
    service = ValuationService()
    service.repo.get_balance_sheet = mocker.Mock()
    service.repo.get_income_statement = mocker.Mock()
    service.repo.get_cash_flow = mocker.Mock()
    service.repo.get_historical_price_at_date = mocker.Mock()
    service.repo.ticker_repo.get_ticker_id = mocker.Mock(return_value=1)
    return service


@pytest.fixture
def forecasting_service(mocker):
    service = ForecastingService()
    service.repo.get_historical_prices_ordered = mocker.Mock()
    service.repo.get_balance_sheet = mocker.Mock()
    service.repo.get_income_statement = mocker.Mock()
    service.repo.ticker_repo.get_ticker_id = mocker.Mock(return_value=1)
    service.fundamental_service = Mock()
    return service


@pytest.fixture
def data_ingestion_service(mocker):
    service = DataIngestionService()
    # Mock the repo and fmp_client if needed
    service.repo = Mock()
    service.fmp_client = Mock()
    return service