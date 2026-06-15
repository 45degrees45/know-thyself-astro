import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from api.services.llm_adapter import LLMAdapter

async def test_complete_returns_string():
    with patch("anthropic.AsyncAnthropic") as MockClient:
        instance = MockClient.return_value
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text="You are a Pisces rising.")]
        instance.messages.create = AsyncMock(return_value=mock_msg)
        adapter = LLMAdapter(provider="anthropic", api_key="test-key")
        result = await adapter.complete("Describe my chart", "You are an astrologer.")
    assert "Pisces" in result

async def test_stream_yields_chunks():
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
        adapter = LLMAdapter(provider="anthropic", api_key="test-key")
        chunks = []
        async for chunk in adapter.stream("Tell me about Pisces", "You are an astrologer."):
            chunks.append(chunk)
    assert "".join(chunks) == "Hello world"

async def test_openai_complete_returns_string():
    with patch("openai.AsyncOpenAI") as MockClient:
        mock_choice = MagicMock()
        mock_choice.message.content = "Your Sun is in Pisces."
        mock_resp = MagicMock()
        mock_resp.choices = [mock_choice]
        instance = MockClient.return_value
        instance.chat.completions.create = AsyncMock(return_value=mock_resp)

        adapter = LLMAdapter(provider="openai", api_key="test-key")
        result = await adapter.complete("Describe my chart", "You are an astrologer.")
    assert "Pisces" in result

async def test_openai_stream_yields_chunks():
    async def fake_openai_stream():
        for text in ["Saturn ", "rules"]:
            chunk = MagicMock()
            chunk.choices = [MagicMock()]
            chunk.choices[0].delta.content = text
            yield chunk

    with patch("openai.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat.completions.create = AsyncMock(return_value=fake_openai_stream())
        adapter = LLMAdapter(provider="openai", api_key="test-key")
        chunks = []
        async for chunk in adapter.stream("Tell me about Saturn", "You are an astrologer."):
            chunks.append(chunk)
    assert "".join(chunks) == "Saturn rules"
