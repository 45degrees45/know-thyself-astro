from typing import AsyncIterator
import anthropic

MODELS = {
    "anthropic": "claude-sonnet-4-6",
    "gemini": "gemini-1.5-pro",
    "openai": "gpt-4o",
    "nim": "meta/llama-3.1-70b-instruct",
}


class LLMAdapter:
    def __init__(self, provider: str = "anthropic", api_key: str = None, base_url: str = None):
        self.provider = provider
        if provider == "anthropic":
            self._client = anthropic.AsyncAnthropic(api_key=api_key)
        else:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def complete(self, prompt: str, system: str) -> str:
        if self.provider == "anthropic":
            msg = await self._client.messages.create(
                model=MODELS["anthropic"],
                max_tokens=4096,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text
        else:
            resp = await self._client.chat.completions.create(
                model=MODELS.get(self.provider, self.provider),
                max_tokens=4096,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            )
            return resp.choices[0].message.content

    async def stream(self, prompt: str, system: str) -> AsyncIterator[str]:
        if self.provider == "anthropic":
            async with self._client.messages.stream(
                model=MODELS["anthropic"],
                max_tokens=4096,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                async for event in stream:
                    if event.type == "content_block_delta" and hasattr(event.delta, "text"):
                        yield event.delta.text
        else:
            stream = await self._client.chat.completions.create(
                model=MODELS.get(self.provider, self.provider),
                max_tokens=4096,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
