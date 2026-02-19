from unittest.mock import MagicMock

import pytest

from app.models.schemas import CompanyProfile, CompareStocksResult, MarketNewsItem, StockQuote
from app.services import stock_service


@pytest.fixture
def mock_finnhub_client():
    """Create a mock Finnhub client."""
    return MagicMock()


def test_get_stock_quote_success(mock_finnhub_client):
    """Test successful quote retrieval."""
    mock_finnhub_client.quote.return_value = {
        "c": 150.25,
        "dp": 2.5,
        "v": 1000000,
    }

    result = stock_service.get_stock_quote(mock_finnhub_client, "AAPL")

    assert isinstance(result, StockQuote)
    assert result.ticker == "AAPL"
    assert result.current_price == 150.25
    assert result.change_percent == 2.5
    assert result.volume == 1000000
    assert result.error is None


def test_get_stock_quote_empty_response(mock_finnhub_client):
    """Test handling of empty quote response."""
    mock_finnhub_client.quote.return_value = {}

    result = stock_service.get_stock_quote(mock_finnhub_client, "INVALID")

    assert result.ticker == "INVALID"
    assert result.error == "No quote data available."


def test_get_stock_quote_api_error(mock_finnhub_client):
    """Test graceful handling of API exceptions."""
    mock_finnhub_client.quote.side_effect = Exception("API rate limit exceeded")

    result = stock_service.get_stock_quote(mock_finnhub_client, "AAPL")

    assert result.ticker == "AAPL"
    assert result.error is not None
    assert "Failed to fetch quote" in result.error


def test_get_company_profile_success(mock_finnhub_client):
    """Test successful company profile retrieval."""
    mock_finnhub_client.company_profile2.return_value = {
        "name": "Apple Inc.",
        "marketCapitalization": 2500000000000,
        "peTTM": 28.5,
    }

    result = stock_service.get_company_profile(mock_finnhub_client, "AAPL")

    assert isinstance(result, CompanyProfile)
    assert result.ticker == "AAPL"
    assert result.name == "Apple Inc."
    assert result.market_cap == 2500000000000
    assert result.pe_ratio == 28.5
    assert result.error is None


def test_get_company_profile_empty_response(mock_finnhub_client):
    """Test handling of empty profile response."""
    mock_finnhub_client.company_profile2.return_value = {}

    result = stock_service.get_company_profile(mock_finnhub_client, "INVALID")

    assert result.ticker == "INVALID"
    assert result.error == "No company profile found."


def test_get_company_profile_api_error(mock_finnhub_client):
    """Test graceful handling of profile API exceptions."""
    mock_finnhub_client.company_profile2.side_effect = Exception("Network error")

    result = stock_service.get_company_profile(mock_finnhub_client, "AAPL")

    assert result.ticker == "AAPL"
    assert result.error is not None
    assert "Failed to fetch company profile" in result.error


def test_compare_stocks(mock_finnhub_client):
    """Test comparing multiple stocks."""
    mock_finnhub_client.quote.side_effect = [
        {"c": 150.0, "dp": 1.0, "v": 500000},
        {"c": 300.0, "dp": -0.5, "v": 200000},
    ]
    mock_finnhub_client.company_profile2.side_effect = [
        {"name": "Apple Inc.", "marketCapitalization": 2500000000000, "peTTM": 28.0},
        {"name": "Microsoft Corp.", "marketCapitalization": 3000000000000, "peTTM": 35.0},
    ]

    result = stock_service.compare_stocks(mock_finnhub_client, ["AAPL", "MSFT"])

    assert isinstance(result, CompareStocksResult)
    assert result.tickers == ["AAPL", "MSFT"]
    assert len(result.quotes) == 2
    assert len(result.profiles) == 2
    assert result.quotes[0].ticker == "AAPL"
    assert result.quotes[1].ticker == "MSFT"


def test_get_market_news_success(mock_finnhub_client):
    """Test successful market news retrieval."""
    mock_finnhub_client.company_news.return_value = [
        {
            "headline": "Apple announces new product",
            "source": "Reuters",
            "url": "https://example.com/news1",
        },
        {
            "headline": "Stock price surges",
            "source": "Bloomberg",
            "url": "https://example.com/news2",
        },
    ]

    result = stock_service.get_market_news(mock_finnhub_client, "AAPL")

    assert len(result) == 2
    assert all(isinstance(item, MarketNewsItem) for item in result)
    assert result[0].ticker == "AAPL"
    assert result[0].headline == "Apple announces new product"
    assert result[0].source == "Reuters"


def test_get_market_news_empty_response(mock_finnhub_client):
    """Test handling of empty news response."""
    mock_finnhub_client.company_news.return_value = []

    result = stock_service.get_market_news(mock_finnhub_client, "AAPL")

    assert len(result) == 1
    assert result[0].error is not None
    assert "No recent news found" in result[0].error


def test_get_market_news_api_error(mock_finnhub_client):
    """Test graceful handling of news API exceptions."""
    mock_finnhub_client.company_news.side_effect = Exception("API unavailable")

    result = stock_service.get_market_news(mock_finnhub_client, "AAPL")

    assert len(result) == 1
    assert result[0].ticker == "AAPL"
    assert result[0].error is not None
    assert "Failed to fetch market news" in result[0].error
