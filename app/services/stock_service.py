from __future__ import annotations

from datetime import date, timedelta
from typing import Protocol

from app.models.schemas import CompanyProfile, CompareStocksResult, MarketNewsItem, StockQuote


class FinnhubClientProtocol(Protocol):
    """Typed subset of the Finnhub client used by this service."""

    def quote(self, symbol: str) -> dict:  # pragma: no cover - protocol
        ...

    def company_profile2(self, symbol: str) -> dict:  # pragma: no cover - protocol
        ...

    def company_news(self, symbol: str, _from: str, to: str) -> list[dict]:  # pragma: no cover - protocol
        ...


def get_stock_quote(client: FinnhubClientProtocol, ticker: str) -> StockQuote:
    """Return a simplified stock quote for the given ticker."""
    try:
        raw = client.quote(ticker)
        if not isinstance(raw, dict) or not raw:
            return StockQuote(ticker=ticker, error="No quote data available.")

        current_price = raw.get("c")
        change_percent = raw.get("dp")
        volume = raw.get("v")

        return StockQuote(
            ticker=ticker,
            current_price=current_price,
            change_percent=change_percent,
            volume=volume,
        )
    except Exception as exc:  # pragma: no cover - defensive
        return StockQuote(ticker=ticker, error=f"Failed to fetch quote: {exc}")


def get_company_profile(client: FinnhubClientProtocol, ticker: str) -> CompanyProfile:
    """Return key company profile information for the given ticker."""
    try:
        raw = client.company_profile2(symbol=ticker)
        if not isinstance(raw, dict) or not raw:
            return CompanyProfile(ticker=ticker, error="No company profile found.")

        name = raw.get("name")
        market_cap = raw.get("marketCapitalization")
        pe_ratio = raw.get("peTTM")

        return CompanyProfile(
            ticker=ticker,
            name=name,
            market_cap=market_cap,
            pe_ratio=pe_ratio,
        )
    except Exception as exc:  # pragma: no cover - defensive
        return CompanyProfile(ticker=ticker, error=f"Failed to fetch company profile: {exc}")


def compare_stocks(client: FinnhubClientProtocol, tickers: list[str]) -> CompareStocksResult:
    """Compare multiple stocks by fetching both quotes and profiles."""
    quotes: list[StockQuote] = []
    profiles: list[CompanyProfile] = []

    for ticker in tickers:
        quotes.append(get_stock_quote(client, ticker))
        profiles.append(get_company_profile(client, ticker))

    return CompareStocksResult(tickers=tickers, quotes=quotes, profiles=profiles)


def get_market_news(client: FinnhubClientProtocol, ticker: str) -> list[MarketNewsItem]:
    """Return recent headlines for a stock ticker (capped at 5 most recent)."""
    try:
        today = date.today()
        week_ago = today - timedelta(days=7)
        raw_items = client.company_news(
            symbol=ticker,
            _from=week_ago.isoformat(),
            to=today.isoformat(),
        )

        if not isinstance(raw_items, list) or not raw_items:
            return [
                MarketNewsItem(
                    ticker=ticker,
                    error="No recent news found for this ticker.",
                )
            ]

        news: list[MarketNewsItem] = []
        for item in raw_items[:5]:
            news.append(
                MarketNewsItem(
                    ticker=ticker,
                    headline=item.get("headline"),
                    source=item.get("source"),
                    url=item.get("url"),
                )
            )
        return news
    except Exception as exc:  # pragma: no cover - defensive
        return [
            MarketNewsItem(
                ticker=ticker,
                error=f"Failed to fetch market news: {exc}",
            )
        ]

