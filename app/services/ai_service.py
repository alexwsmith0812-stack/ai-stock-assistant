from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import Any

import finnhub
from openai import AsyncOpenAI, OpenAI

from app.core.config import get_settings
from app.services import stock_service


def _get_openai_client() -> OpenAI:
    settings = get_settings()
    return OpenAI(api_key=settings.openai_api_key)


def _get_finnhub_client() -> finnhub.Client:
    settings = get_settings()
    return finnhub.Client(api_key=settings.finnhub_api_key)


def _tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "get_stock_quote",
                "description": "Get the latest quote for a single stock ticker.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "Stock ticker symbol, e.g. AAPL or MSFT.",
                        }
                    },
                    "required": ["ticker"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_company_profile",
                "description": "Get basic company information and valuation metrics.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "Stock ticker symbol, e.g. TSLA or AMZN.",
                        }
                    },
                    "required": ["ticker"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "compare_stocks",
                "description": "Compare multiple stocks by fetching quotes and profiles.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tickers": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of stock ticker symbols.",
                        }
                    },
                    "required": ["tickers"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_market_news",
                "description": "Get recent market news headlines for a company.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "Stock ticker symbol.",
                        }
                    },
                    "required": ["ticker"],
                },
            },
        },
    ]


def _get_async_openai_client() -> AsyncOpenAI:
    settings = get_settings()
    return AsyncOpenAI(api_key=settings.openai_api_key)


async def get_ai_response(
    question: str,
    openai_client: OpenAI | None = None,
    finnhub_client: finnhub.Client | None = None,
    async_openai_client: AsyncOpenAI | None = None,
) -> AsyncGenerator[str, None]:
    """
    Send the user's question to OpenAI with tool definitions, handle tool calls,
    then stream the final natural language answer token by token.
    """
    client = openai_client or _get_openai_client()
    fh_client = finnhub_client or _get_finnhub_client()
    async_client = async_openai_client or _get_async_openai_client()
    settings = get_settings()

    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                "You are a helpful stock insights assistant. "
                "You have access to tools for fetching real-time stock quotes, "
                "company fundamentals, comparisons, and recent news. "
                "Always explain results in clear, user-friendly language and "
                "avoid giving financial advice or guarantees. "
                "If a question is not related to stocks or financial markets, "
                "politely let the user know you can only help with stock-related queries."
            ),
        },
        {"role": "user", "content": question},
    ]

    tools = _tool_definitions()

    # Tool-calling phase: non-streaming until we have a final answer.
    for _ in range(3):
        try:
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )
        except Exception:
            yield (
                "I couldn't reach the AI service right now. "
                "Please double-check your `OPENAI_API_KEY` and try again in a moment."
            )
            return

        choice = response.choices[0]
        message = choice.message

        # If the model produced a final answer, stream it.
        if not message.tool_calls:
            content = message.content or "I was unable to generate a response."
            # Stream the final response with a single streaming API call.
            async for chunk in _stream_completion(
                async_client, settings.openai_model, messages, content
            ):
                yield chunk
            return

        # Add assistant message with tool_calls, then tool results.
        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in (message.tool_calls or [])
                ],
            }
        )

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments or "{}")
            except json.JSONDecodeError:
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(
                            {"error": "Tool arguments could not be parsed."}
                        ),
                    }
                )
                continue

            result = _execute_tool(tool_name, arguments, fh_client)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                }
            )

    # Exhausted loop: yield a single error message.
    yield (
        "I had trouble answering this question using the available stock data. "
        "Please try rephrasing or asking about a specific ticker."
    )


async def _stream_completion(
    async_client: AsyncOpenAI,
    model: str,
    messages: list[dict[str, Any]],
    fallback_content: str,
) -> AsyncGenerator[str, None]:
    """
    Make a streaming completion call (no tools) and yield content deltas.
    Accepts an AsyncOpenAI client so tests can inject a mock.
    Falls back to yielding fallback_content if streaming fails or returns nothing.
    """
    try:
        stream = await async_client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
        )
        had_content = False
        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta and getattr(delta, "content", None):
                had_content = True
                yield delta.content
        if not had_content:
            yield fallback_content
    except Exception:
        yield fallback_content


def _execute_tool(
    name: str,
    arguments: dict[str, Any],
    fh_client: finnhub.Client,
) -> dict[str, Any]:
    """
    Route tool calls to the appropriate stock_service function and normalise
    the response for the language model.
    """
    if name == "get_stock_quote":
        ticker = arguments.get("ticker", "")
        result = stock_service.get_stock_quote(fh_client, ticker)
        return {"type": name, "data": result.model_dump()}

    if name == "get_company_profile":
        ticker = arguments.get("ticker", "")
        result = stock_service.get_company_profile(fh_client, ticker)
        return {"type": name, "data": result.model_dump()}

    if name == "compare_stocks":
        tickers = arguments.get("tickers") or []
        if not isinstance(tickers, list):
            tickers = [tickers]
        result = stock_service.compare_stocks(fh_client, tickers)
        return {"type": name, "data": result.model_dump()}

    if name == "get_market_news":
        ticker = arguments.get("ticker", "")
        items = stock_service.get_market_news(fh_client, ticker)
        return {
            "type": name,
            "data": [item.model_dump() for item in items],
        }

    return {"error": f"Unknown tool: {name}"}

