from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., description="Natural language question about stocks or markets.")


class AskResponse(BaseModel):
    answer: str = Field(..., description="AI-generated response to the user's question.")


class StockQuote(BaseModel):
    ticker: str
    current_price: float | None = None
    change_percent: float | None = None
    volume: int | None = None
    error: str | None = None


class CompanyProfile(BaseModel):
    ticker: str
    name: str | None = None
    market_cap: float | None = None
    pe_ratio: float | None = None
    error: str | None = None


class MarketNewsItem(BaseModel):
    ticker: str
    headline: str | None = None
    source: str | None = None
    url: str | None = None
    error: str | None = None


class CompareStocksResult(BaseModel):
    tickers: list[str]
    quotes: list[StockQuote]
    profiles: list[CompanyProfile]

