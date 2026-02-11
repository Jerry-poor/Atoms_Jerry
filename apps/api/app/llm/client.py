from __future__ import annotations

import json
import time
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Callable

import httpx

from app.core.config import get_settings


@dataclass(frozen=True)
class ChatMessage:
    role: str  # system|user|assistant
    content: str


StreamEmitter = Callable[[str, str], None]

# Optional per-run emitter installed by the executor to surface token deltas.
LLM_STREAM_EMITTER: ContextVar[StreamEmitter | None] = ContextVar(
    "LLM_STREAM_EMITTER", default=None
)


def _deterministic_fallback(messages: list[ChatMessage]) -> str:
    # Keep it predictable in dev/test when no API is configured.
    user_text = ""
    for m in messages:
        if m.role == "user":
            user_text = m.content.strip()
            break
    return (user_text or "Run completed").strip()


def chat(
    *,
    messages: list[ChatMessage],
    temperature: float = 0.2,
    fallback: str | None = None,
    stream: bool = False,
    event_role: str | None = None,
) -> str:
    settings = get_settings()
    api_key = (settings.deepseek_api_key or "").strip()
    api_base = (settings.deepseek_api_base or "").strip().rstrip("/")
    model = (settings.deepseek_model or "").strip()

    if not api_key or not api_base or not model:
        return (fallback or _deterministic_fallback(messages)).strip()

    url = f"{api_base}/chat/completions"
    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": m.role, "content": m.content} for m in messages],
        "temperature": temperature,
    }
    if stream:
        payload["stream"] = True

    emitter = LLM_STREAM_EMITTER.get()
    role_tag = (event_role or "").strip() or "assistant"

    def _emit(delta: str) -> None:
        if not delta or not emitter:
            return
        try:
            emitter(role_tag, delta)
        except Exception:
            # Never allow streaming telemetry to break the main response path.
            return

    try:
        with httpx.Client(timeout=60) as client:
            if stream and emitter:
                # OpenAI-compatible SSE streaming: "data: {json}\n\n" ... "data: [DONE]".
                acc: list[str] = []
                last_emit = time.monotonic()
                with client.stream(
                    "POST",
                    url,
                    headers={"authorization": f"Bearer {api_key}"},
                    json=payload,
                ) as resp:
                    resp.raise_for_status()
                    for line in resp.iter_lines():
                        if not line:
                            continue
                        s = line.decode("utf-8", errors="ignore").strip()
                        if not s.startswith("data:"):
                            continue
                        data_s = s[len("data:") :].strip()
                        if data_s == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_s)
                        except Exception:
                            continue
                        try:
                            choices = chunk.get("choices") or []
                            delta = (choices[0].get("delta") or {}) if choices else {}
                            text = (delta.get("content") or "") if isinstance(delta, dict) else ""
                        except Exception:
                            text = ""
                        if not text:
                            continue
                        acc.append(text)
                        # Throttle emission a bit so we don't spam the DB.
                        now = time.monotonic()
                        if now - last_emit >= 0.08 or len(text) >= 32:
                            _emit(text)
                            last_emit = now
                return "".join(acc).strip() or (fallback or _deterministic_fallback(messages)).strip()

            resp = client.post(
                url,
                headers={"authorization": f"Bearer {api_key}"},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return (fallback or _deterministic_fallback(messages)).strip()

    # OpenAI-compatible shape
    try:
        choices = data.get("choices") or []
        msg = choices[0].get("message") or {}
        content = (msg.get("content") or "").strip()
        if content:
            return content
    except Exception:
        pass

    # Debug-friendly fallback for unexpected schemas.
    return json.dumps(data)[:2000]
