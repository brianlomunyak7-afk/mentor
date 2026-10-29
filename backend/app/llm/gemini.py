from google import genai
from google.genai import errors, types

from app.llm.base import ChatMessage, LLMProviderError, LLMResponse


class GeminiProvider:
    provider_name = "gemini"

    def __init__(self, api_key: str, model: str) -> None:
        if not api_key.strip():
            raise ValueError("GEMINI_API_KEY is required for the Gemini provider")
        self.client = genai.Client(api_key=api_key)
        self.model_name = model

    async def generate(
        self,
        messages: list[ChatMessage],
        *,
        system_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1200,
    ) -> LLMResponse:
        contents = [
            types.Content(
                role="model" if message.role == "assistant" else "user",
                parts=[types.Part.from_text(text=message.content)],
            )
            for message in messages
        ]
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )
        except errors.APIError as error:
            raise LLMProviderError(
                f"Gemini request failed: {error.__class__.__name__}"
            ) from error

        text = (response.text or "").strip()
        if not text:
            raise LLMProviderError("Gemini returned an empty response")
        return LLMResponse(text=text, provider=self.provider_name, model=self.model_name)
