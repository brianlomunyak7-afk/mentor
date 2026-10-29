import anthropic

from app.llm.base import ChatMessage, LLMProviderError, LLMResponse


class AnthropicProvider:
    provider_name = "anthropic"

    def __init__(self, api_key: str, model: str) -> None:
        if not api_key.strip():
            raise ValueError("ANTHROPIC_API_KEY is required for the Anthropic provider")
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model_name = model

    async def generate(
        self,
        messages: list[ChatMessage],
        *,
        system_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1200,
    ) -> LLMResponse:
        try:
            response = await self.client.messages.create(
                model=self.model_name,
                system=system_prompt,
                messages=[
                    {"role": message.role, "content": message.content}
                    for message in messages
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except anthropic.APIError as error:
            raise LLMProviderError(
                f"Anthropic request failed: {error.__class__.__name__}"
            ) from error

        text = "".join(
            block.text
            for block in response.content
            if getattr(block, "type", None) == "text"
        ).strip()
        if not text:
            raise LLMProviderError("Anthropic returned an empty response")
        return LLMResponse(text=text, provider=self.provider_name, model=self.model_name)
