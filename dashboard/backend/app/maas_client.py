import json
import logging
import re

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class MaasDisabledError(RuntimeError):
    """Raised when MaaS AI insights are used without a configured API key."""


async def chat_completion(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> str:
    if not settings.maas_enabled:
        raise MaasDisabledError(
            "AI insights are disabled: MAAS_API_KEY is not set. "
            "Configure it in backend/.env to enable this feature."
        )
    model = model or settings.maas_model
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.maas_api_key}",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient(timeout=180.0) as client:
        resp = await client.post(
            f"{settings.maas_base_url}/chat/completions",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    return data["choices"][0]["message"]["content"]


async def chat_completion_json(
    messages: list[dict],
    model: str | None = None,
) -> dict:
    text = await chat_completion(messages, model)
    return _extract_json(text)


def _extract_json(text: str) -> dict:
    # Try to find JSON in markdown code blocks
    match = re.search(r"```(?:json)?\s*\n(.*?)\n```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find raw JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # Last resort: wrap in a basic structure
    return {"summary": text, "findings": [], "risks": []}
