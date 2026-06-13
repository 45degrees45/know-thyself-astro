import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from api.services.llm_adapter import LLMAdapter

async def test_complete_returns_string():
    adapter = LLMAdapter(provider="anthropic", api_key="test-key")
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text="You are a Pisces rising.")]
    with patch("anthropic.AsyncAnthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create = AsyncMock(return_value=mock_msg)
        result = await adapter.complete("Describe my chart", "You are an astrologer.")
    assert "Pisces" in result

async def test_stream_yields_chunks():
    adapter = LLMAdapter(provider="anthropic", api_key="test-key")

    async def fake_stream():
        for text in ["Hello", " world"]:
            event = MagicMock()
            event.type = "content_block_delta"
            event.delta = MagicMock(text=text)
            yield event

    mock_stream_ctx = MagicMock()
    mock_stream_ctx.__aenter__ = AsyncMock(return_value=fake_stream())
    mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch("anthropic.AsyncAnthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.stream.return_value = mock_stream_ctx
        chunks = []
        async for chunk in adapter.stream("Tell me about Pisces", "You are an astrologer."):
            chunks.append(chunk)
    assert "".join(chunks) == "Hello world"
