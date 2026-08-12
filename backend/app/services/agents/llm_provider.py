"""
LLM provider abstraction (section 6 / 50).

The rest of the app never talks to a vendor SDK/API directly - it talks to
this interface using a single normalized message format, so the model and
provider are swappable purely via environment variables (LLM_PROVIDER,
LLM_MODEL, and the relevant *_API_KEY).

Normalized message format (provider-agnostic, OpenAI-shaped since it's the
easiest to convert to/from):

    {"role": "user", "content": "..."}
    {"role": "assistant", "content": "...", "tool_calls": [
        {"id": "call_1", "name": "get_supplier_risk", "input": {...}}
    ]}
    {"role": "tool", "tool_call_id": "call_1", "name": "get_supplier_risk", "content": "..."}

Normalized response:

    {"content": str, "tool_calls": [{"id", "name", "input"}], "stop_reason": str}

Supported providers:
    - anthropic  (Claude, native tool-use API)
    - gemini     (Google AI Studio / Gemini API, functionCalling)
    - openrouter (OpenAI-compatible /chat/completions across many models)
"""
import json
from abc import ABC, abstractmethod
from typing import Any, Optional

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class BaseLLMProvider(ABC):
    @abstractmethod
    def complete(
        self,
        messages: list[dict],
        system: str = "",
        tools: Optional[list[dict]] = None,
        max_tokens: int = 1024,
    ) -> dict:
        ...


# ---------------------------------------------------------------------------
# Anthropic (Claude)
# ---------------------------------------------------------------------------
class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def _to_anthropic_messages(self, messages: list[dict]) -> list[dict]:
        out = []
        for m in messages:
            if m["role"] == "user":
                out.append({"role": "user", "content": m["content"]})
            elif m["role"] == "assistant":
                blocks = []
                if m.get("content"):
                    blocks.append({"type": "text", "text": m["content"]})
                for call in m.get("tool_calls", []):
                    blocks.append({"type": "tool_use", "id": call["id"], "name": call["name"], "input": call["input"]})
                out.append({"role": "assistant", "content": blocks or m.get("content", "")})
            elif m["role"] == "tool":
                out.append({"role": "user", "content": [
                    {"type": "tool_result", "tool_use_id": m["tool_call_id"], "content": str(m["content"])}
                ]})
        return out

    def complete(self, messages, system="", tools=None, max_tokens=1024) -> dict:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": self._to_anthropic_messages(messages),
        }
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = tools  # already Anthropic-shaped (see tools.py TOOL_SPECS)

        response = self.client.messages.create(**kwargs)

        text_parts, tool_calls = [], []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append({"name": block.name, "input": block.input, "id": block.id})

        return {"content": "\n".join(text_parts), "tool_calls": tool_calls, "stop_reason": response.stop_reason}


# ---------------------------------------------------------------------------
# OpenRouter (OpenAI-compatible /chat/completions, many models incl. free tiers)
# ---------------------------------------------------------------------------
class OpenRouterProvider(BaseLLMProvider):
    API_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    def _to_openai_tools(self, tools: list[dict]) -> list[dict]:
        return [{"type": "function", "function": {
            "name": t["name"], "description": t.get("description", ""), "parameters": t["input_schema"],
        }} for t in tools]

    def _to_openai_messages(self, messages: list[dict], system: str) -> list[dict]:
        out = []
        if system:
            out.append({"role": "system", "content": system})
        for m in messages:
            if m["role"] in ("user", "assistant") and not m.get("tool_calls"):
                out.append({"role": m["role"], "content": m.get("content") or ""})
            elif m["role"] == "assistant" and m.get("tool_calls"):
                out.append({
                    "role": "assistant",
                    "content": m.get("content") or None,
                    "tool_calls": [
                        {"id": c["id"], "type": "function",
                         "function": {"name": c["name"], "arguments": json.dumps(c["input"])}}
                        for c in m["tool_calls"]
                    ],
                })
            elif m["role"] == "tool":
                out.append({"role": "tool", "tool_call_id": m["tool_call_id"], "content": str(m["content"])})
        return out

    def complete(self, messages, system="", tools=None, max_tokens=1024) -> dict:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": self._to_openai_messages(messages, system),
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = self._to_openai_tools(tools)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://supplychain-ai.local",
            "X-Title": "Supply Chain AI Assistant",
        }
        with httpx.Client(timeout=60) as client:
            resp = client.post(self.API_URL, headers=headers, json=payload)
        if resp.status_code >= 400:
            logger.error("openrouter.error", status=resp.status_code, body=resp.text[:500])
            return {"content": f"OpenRouter API error ({resp.status_code}): {resp.text[:300]}", "tool_calls": [], "stop_reason": "error"}

        data = resp.json()
        choice = data["choices"][0]
        msg = choice["message"]
        tool_calls = []
        for tc in msg.get("tool_calls") or []:
            try:
                args = json.loads(tc["function"]["arguments"])
            except Exception:
                args = {}
            tool_calls.append({"id": tc["id"], "name": tc["function"]["name"], "input": args})

        return {"content": msg.get("content") or "", "tool_calls": tool_calls, "stop_reason": choice.get("finish_reason")}


# ---------------------------------------------------------------------------
# Gemini (Google AI Studio)
# ---------------------------------------------------------------------------
class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    @property
    def _url(self) -> str:
        return f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def _to_gemini_tools(self, tools: list[dict]) -> list[dict]:
        return [{"functionDeclarations": [
            {"name": t["name"], "description": t.get("description", ""), "parameters": t["input_schema"]}
            for t in tools
        ]}]

    def _to_gemini_contents(self, messages: list[dict]) -> list[dict]:
        contents = []
        for m in messages:
            if m["role"] == "user":
                contents.append({"role": "user", "parts": [{"text": m["content"]}]})
            elif m["role"] == "assistant":
                parts = []
                if m.get("content"):
                    parts.append({"text": m["content"]})
                for call in m.get("tool_calls", []):
                    parts.append({"functionCall": {"name": call["name"], "args": call["input"]}})
                contents.append({"role": "model", "parts": parts})
            elif m["role"] == "tool":
                contents.append({"role": "user", "parts": [{
                    "functionResponse": {"name": m.get("name", "tool"), "response": {"result": str(m["content"])}}
                }]})
        return contents

    def complete(self, messages, system="", tools=None, max_tokens=1024) -> dict:
        payload: dict[str, Any] = {
            "contents": self._to_gemini_contents(messages),
            "generationConfig": {"maxOutputTokens": max_tokens},
        }
        if system:
            payload["system_instruction"] = {"parts": [{"text": system}]}
        if tools:
            payload["tools"] = self._to_gemini_tools(tools)

        with httpx.Client(timeout=60) as client:
            resp = client.post(self._url, params={"key": self.api_key}, json=payload)
        if resp.status_code >= 400:
            logger.error("gemini.error", status=resp.status_code, body=resp.text[:500])
            return {"content": f"Gemini API error ({resp.status_code}): {resp.text[:300]}", "tool_calls": [], "stop_reason": "error"}

        data = resp.json()
        candidates = data.get("candidates") or []
        if not candidates:
            return {"content": "Gemini returned no candidates (possibly blocked by safety filters).", "tool_calls": [], "stop_reason": "empty"}

        parts = candidates[0].get("content", {}).get("parts", [])
        text_parts, tool_calls = [], []
        for i, part in enumerate(parts):
            if "text" in part:
                text_parts.append(part["text"])
            elif "functionCall" in part:
                fc = part["functionCall"]
                tool_calls.append({"id": f"call_{i}", "name": fc["name"], "input": fc.get("args", {})})

        return {"content": "\n".join(text_parts), "tool_calls": tool_calls, "stop_reason": candidates[0].get("finishReason")}


# ---------------------------------------------------------------------------
class UnavailableProvider(BaseLLMProvider):
    """Used when no LLM key is configured - keeps the rest of the app
    functional (dashboard/ML/RAG all work without an LLM key)."""

    def complete(self, messages, system="", tools=None, max_tokens=1024) -> dict:
        return {
            "content": "The AI assistant is not configured. Set LLM_PROVIDER + the matching API key in .env.",
            "tool_calls": [],
            "stop_reason": "unavailable",
        }


def get_llm_provider() -> BaseLLMProvider:
    provider = settings.LLM_PROVIDER

    if provider == "anthropic" and settings.LLM_API_KEY:
        return AnthropicProvider(settings.LLM_API_KEY, settings.LLM_MODEL)
    if provider == "gemini" and settings.GEMINI_API_KEY:
        return GeminiProvider(settings.GEMINI_API_KEY, settings.LLM_MODEL or "gemini-2.0-flash")
    if provider == "openrouter" and settings.OPENROUTER_API_KEY:
        return OpenRouterProvider(settings.OPENROUTER_API_KEY, settings.LLM_MODEL or "openai/gpt-4o-mini")

    logger.warning("llm_provider.unavailable", configured_provider=provider)
    return UnavailableProvider()
