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
        self.api_key = api_key
        self.base_url = base_url

    def _anthropic_client(self):
        return anthropic.AsyncAnthropic(api_key=self.api_key)

    def _openai_compatible_client(self):
        from openai import AsyncOpenAI
        return AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

    async def complete(self, prompt: str, system: str) -> str:
        if self.provider == "anthropic":
            client = self._anthropic_client()
            msg = await client.messages.create(
                model=MODELS["anthropic"],
                max_tokens=4096,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text
        else:
            client = self._openai_compatible_client()
            resp = await client.chat.completions.create(
                model=MODELS.get(self.provider, self.provider),
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            )
            return resp.choices[0].message.content

    async def stream(self, prompt: str, system: str) -> AsyncIterator[str]:
        if self.provider == "anthropic":
            client = self._anthropic_client()
            async with client.messages.stream(
                model=MODELS["anthropic"],
                max_tokens=4096,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                async for event in stream:
                    if event.type == "content_block_delta":
                        yield event.delta.text
        else:
            client = self._openai_compatible_client()
            stream = await client.chat.completions.create(
                model=MODELS.get(self.provider, self.provider),
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
