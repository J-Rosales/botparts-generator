from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class LLMConfig:
    api_key: str
    api_base: str
    model: str
    temperature: float
    max_output_tokens: int | None
    timeout_s: float
    provider: str


@dataclass(frozen=True)
class LLMResult:
    output_text: str
    model_info: dict[str, Any]


def load_llm_config() -> LLMConfig:
    api_key = os.environ.get("BOTPARTS_LLM_API_KEY")
    if not api_key:
        raise ValueError("BOTPARTS_LLM_API_KEY is required for LLM calls.")
    api_base = os.environ.get("BOTPARTS_LLM_API_BASE", "https://api.openai.com/v1")
    model = os.environ.get("BOTPARTS_LLM_MODEL", "gpt-4.1-mini")
    temperature = float(os.environ.get("BOTPARTS_LLM_TEMPERATURE", "0.3"))
    max_tokens_raw = os.environ.get("BOTPARTS_LLM_MAX_OUTPUT_TOKENS", "")
    max_output_tokens = int(max_tokens_raw) if max_tokens_raw else None
    timeout_s = float(os.environ.get("BOTPARTS_LLM_TIMEOUT", "60"))
    provider = os.environ.get("BOTPARTS_LLM_PROVIDER", "openai")
    return LLMConfig(
        api_key=api_key,
        api_base=api_base.rstrip("/"),
        model=model,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        timeout_s=timeout_s,
        provider=provider,
    )


def invoke_llm(compiled_prompt: str, config: LLMConfig) -> LLMResult:
    payload: dict[str, Any] = {
        "model": config.model,
        "input": compiled_prompt,
        "temperature": config.temperature,
    }
    if config.max_output_tokens is not None:
        payload["max_output_tokens"] = config.max_output_tokens
    response = _post_json(f"{config.api_base}/responses", payload, config)
    output_text = _extract_output_text(response)
    if not output_text:
        raise ValueError("LLM response contained no output text.")
    model_info = {
        "model": config.model,
        "temperature": config.temperature,
        "max_output_tokens": config.max_output_tokens,
        "provider": config.provider,
        "api_base": config.api_base,
        "response_id": response.get("id"),
    }
    return LLMResult(output_text=output_text, model_info=model_info)


def _post_json(url: str, payload: dict[str, Any], config: LLMConfig) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=config.timeout_s) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8") if exc.fp else str(exc)
        raise RuntimeError(f"LLM request failed ({exc.code}): {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"LLM request failed: {exc.reason}") from exc
    return json.loads(raw)


def _extract_output_text(response: dict[str, Any]) -> str:
    if isinstance(response.get("output_text"), str):
        return response["output_text"]
    texts: list[str] = []
    for item in response.get("output", []) or []:
        for content in item.get("content", []) or []:
            if not isinstance(content, dict):
                continue
            text = content.get("text")
            if isinstance(text, str):
                texts.append(text)
    return "".join(texts)
