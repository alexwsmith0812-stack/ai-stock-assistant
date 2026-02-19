from typing import List, Optional

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., description="Natural language question about stocks or markets.")


class AskResponse(BaseModel):
    answer: str = Field(..., description="AI-generated response to the user's question.")


class StockQuote(BaseModel):
    ticker: str
    current_price: Optional[float] = None
    change_percent: Optional[float] = None
    volume: Optional[int] = None
    error: Optional[str] = None


class CompanyProfile(BaseModel):
    ticker: str
    name: Optional[str] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    error: Optional[str] = None


class MarketNewsItem(BaseModel):
    ticker: str
    headline: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None


class CompareStocksResult(BaseModel):
    tickers: List[str]
    quotes: List[StockQuote]
    profiles: List[CompanyProfile]

