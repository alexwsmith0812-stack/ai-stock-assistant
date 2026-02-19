import json
from unittest.mock import MagicMock, patch

import pytest

from app.services import ai_service


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    return MagicMock()


@pytest.fixture
def mock_finnhub_client():
    """Create a mock Finnhub client."""
    return MagicMock()


@pytest.mark.asyncio
async def test_get_ai_response_direct_answer(mock_openai_client, mock_finnhub_client):
    """Test when OpenAI returns a direct answer without tool calls."""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="Apple Inc. (AAPL) is currently trading at $150.25.",
                tool_calls=None,
            )
        )
    ]
    mock_openai_client.chat.completions.create.return_value = mock_response

    result = await ai_service.get_ai_response(
        "What is the current price of AAPL?",
        openai_client=mock_openai_client,
        finnhub_client=mock_finnhub_client,
    )

    assert "AAPL" in result or "Apple" in result or "150" in result
    mock_openai_client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_get_ai_response_with_tool_call(mock_openai_client, mock_finnhub_client):
    """Test when OpenAI requests a tool call and we execute it."""
    # First call: OpenAI requests a tool call
    mock_tool_call = MagicMock()
    mock_tool_call.id = "call_123"
    mock_tool_call.function.name = "get_stock_quote"
    mock_tool_call.function.arguments = json.dumps({"ticker": "AAPL"})

    mock_message_with_tool = MagicMock()
    mock_message_with_tool.content = None
    mock_message_with_tool.tool_calls = [mock_tool_call]

    # Second call: OpenAI returns final answer after seeing tool results
    mock_message_final = MagicMock()
    mock_message_final.content = "AAPL is trading at $150.25, up 2.5%."
    mock_message_final.tool_calls = None

    mock_openai_client.chat.completions.create.side_effect = [
        MagicMock(choices=[MagicMock(message=mock_message_with_tool)]),
        MagicMock(choices=[MagicMock(message=mock_message_final)]),
    ]

    # Mock the stock service to return quote data
    with patch("app.services.ai_service.stock_service.get_stock_quote") as mock_get_quote:
        mock_get_quote.return_value = MagicMock(
            ticker="AAPL",
            current_price=150.25,
            change_percent=2.5,
            volume=1000000,
            error=None,
            model_dump=lambda: {
                "ticker": "AAPL",
                "current_price": 150.25,
                "change_percent": 2.5,
                "volume": 1000000,
                "error": None,
            },
        )

        result = await ai_service.get_ai_response(
            "What is the price of AAPL?",
            openai_client=mock_openai_client,
            finnhub_client=mock_finnhub_client,
        )

        assert "AAPL" in result or "150" in result
        assert mock_openai_client.chat.completions.create.call_count == 2
        mock_get_quote.assert_called_once_with(mock_finnhub_client, "AAPL")


@pytest.mark.asyncio
async def test_get_ai_response_compare_stocks_tool(mock_openai_client, mock_finnhub_client):
    """Test tool calling for compare_stocks."""
    mock_tool_call = MagicMock()
    mock_tool_call.id = "call_456"
    mock_tool_call.function.name = "compare_stocks"
    mock_tool_call.function.arguments = json.dumps({"tickers": ["AAPL", "MSFT"]})

    mock_message_with_tool = MagicMock()
    mock_message_with_tool.content = None
    mock_message_with_tool.tool_calls = [mock_tool_call]

    mock_message_final = MagicMock()
    mock_message_final.content = "AAPL and MSFT comparison complete."
    mock_message_final.tool_calls = None

    mock_openai_client.chat.completions.create.side_effect = [
        MagicMock(choices=[MagicMock(message=mock_message_with_tool)]),
        MagicMock(choices=[MagicMock(message=mock_message_final)]),
    ]

    with patch("app.services.ai_service.stock_service.compare_stocks") as mock_compare:
        mock_compare.return_value = MagicMock(
            tickers=["AAPL", "MSFT"],
            quotes=[],
            profiles=[],
            model_dump=lambda: {"tickers": ["AAPL", "MSFT"], "quotes": [], "profiles": []},
        )

        result = await ai_service.get_ai_response(
            "Compare AAPL and MSFT",
            openai_client=mock_openai_client,
            finnhub_client=mock_finnhub_client,
        )

        assert "AAPL" in result or "MSFT" in result or "comparison" in result.lower()
        mock_compare.assert_called_once_with(mock_finnhub_client, ["AAPL", "MSFT"])


@pytest.mark.asyncio
async def test_get_ai_response_invalid_json_arguments(mock_openai_client, mock_finnhub_client):
    """Test handling of malformed tool call arguments."""
    mock_tool_call = MagicMock()
    mock_tool_call.id = "call_789"
    mock_tool_call.function.name = "get_stock_quote"
    mock_tool_call.function.arguments = "invalid json{"

    mock_message_with_tool = MagicMock()
    mock_message_with_tool.content = None
    mock_message_with_tool.tool_calls = [mock_tool_call]

    mock_message_final = MagicMock()
    mock_message_final.content = "I encountered an error processing your request."
    mock_message_final.tool_calls = None

    mock_openai_client.chat.completions.create.side_effect = [
        MagicMock(choices=[MagicMock(message=mock_message_with_tool)]),
        MagicMock(choices=[MagicMock(message=mock_message_final)]),
    ]

    result = await ai_service.get_ai_response(
        "Get AAPL quote",
        openai_client=mock_openai_client,
        finnhub_client=mock_finnhub_client,
    )

    # Should still return a response despite the JSON error
    assert result is not None


@pytest.mark.asyncio
async def test_get_ai_response_max_iterations(mock_openai_client, mock_finnhub_client):
    """Test that the loop terminates after max iterations."""
    mock_tool_call = MagicMock()
    mock_tool_call.id = "call_999"
    mock_tool_call.function.name = "get_stock_quote"
    mock_tool_call.function.arguments = json.dumps({"ticker": "AAPL"})

    mock_message_with_tool = MagicMock()
    mock_message_with_tool.content = None
    mock_message_with_tool.tool_calls = [mock_tool_call]

    # Always return tool calls, never a final answer
    mock_openai_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=mock_message_with_tool)]
    )

    with patch("app.services.ai_service.stock_service.get_stock_quote") as mock_get_quote:
        mock_get_quote.return_value = MagicMock(
            model_dump=lambda: {"ticker": "AAPL", "current_price": 150.25}
        )

        result = await ai_service.get_ai_response(
            "Get AAPL",
            openai_client=mock_openai_client,
            finnhub_client=mock_finnhub_client,
        )

        # Should return a graceful error message after max iterations
        assert "trouble" in result.lower() or "try" in result.lower()
        # Should have called OpenAI 3 times (max iterations)
        assert mock_openai_client.chat.completions.create.call_count == 3


@pytest.mark.asyncio
async def test_get_ai_response_unknown_tool(mock_openai_client, mock_finnhub_client):
    """Test handling of unknown tool names."""
    mock_tool_call = MagicMock()
    mock_tool_call.id = "call_unknown"
    mock_tool_call.function.name = "unknown_tool"
    mock_tool_call.function.arguments = json.dumps({})

    mock_message_with_tool = MagicMock()
    mock_message_with_tool.content = None
    mock_message_with_tool.tool_calls = [mock_tool_call]

    mock_message_final = MagicMock()
    mock_message_final.content = "I'll try a different approach."
    mock_message_final.tool_calls = None

    mock_openai_client.chat.completions.create.side_effect = [
        MagicMock(choices=[MagicMock(message=mock_message_with_tool)]),
        MagicMock(choices=[MagicMock(message=mock_message_final)]),
    ]

    result = await ai_service.get_ai_response(
        "Do something",
        openai_client=mock_openai_client,
        finnhub_client=mock_finnhub_client,
    )

    assert result is not None
