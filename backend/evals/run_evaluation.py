import argparse
import asyncio
import json
import re
from pathlib import Path

from app.config import Settings
from app.llm.anthropic import AnthropicProvider
from app.llm.base import ChatMessage, LLMProvider
from app.llm.gemini import GeminiProvider

EVAL_PATH = Path(__file__).with_name("questions.json")


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).strip()


def provider_for(name: str, api_key: str) -> LLMProvider:
    if name == "anthropic":
        return AnthropicProvider(api_key, Settings().anthropic_model)
    if name == "gemini":
        return GeminiProvider(api_key, Settings().gemini_model)
    raise ValueError(f"Unsupported provider: {name}")


async def evaluate(provider: LLMProvider) -> list[dict[str, object]]:
    questions = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    results = []
    for item in questions:
        response = await provider.generate(
            [ChatMessage(role="user", content=item["question"])],
            system_prompt="Answer with a short, direct answer. Do not guess.",
            temperature=0,
            max_tokens=100,
        )
        answer = normalize(response.text)
        expected = normalize(item["answer"])
        results.append(
            {
                "id": item["id"],
                "expected": item["answer"],
                "response": response.text,
                "correct": expected in answer,
            }
        )
    return results


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=("anthropic", "gemini"), required=True)
    parser.add_argument("--api-key", required=True)
    args = parser.parse_args()
    results = await evaluate(provider_for(args.provider, args.api_key))
    correct = sum(bool(result["correct"]) for result in results)
    print(json.dumps({"provider": args.provider, "correct": correct, "total": len(results), "accuracy": correct / len(results), "results": results}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
