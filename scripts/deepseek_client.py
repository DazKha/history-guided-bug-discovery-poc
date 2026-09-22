from __future__ import annotations

import os
import time
from dataclasses import dataclass

import requests


@dataclass
class GenerationResult:
    content: str
    usage: dict
    log_record: dict


class DeepSeekClient:
    def __init__(self, api_key: str | None = None, model: str = "deepseek-flash", temperature: float = 0.2):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is not available in the environment")
        self.model = model
        self.temperature = temperature
        self.request_count = 0

    def generate(self, prompt: str, max_tokens: int = 1800) -> GenerationResult:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an empirical software testing researcher. Follow the requested JSON schema exactly."},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "thinking": {"type": "disabled"},
            "max_tokens": max_tokens,
            "temperature": self.temperature,
        }
        last_error = None
        for retry in range(3):
            started = time.time()
            try:
                response = requests.post(
                    "https://api.deepseek.com/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json=payload,
                    timeout=120,
                )
                self.request_count += 1
                response.raise_for_status()
                body = response.json()
                choice = body["choices"][0]
                usage = body.get("usage") or {}
                log_record = {
                    "model": body.get("model", self.model),
                    "request_count": self.request_count,
                    "retry_index": retry,
                    "latency_seconds": round(time.time() - started, 3),
                    "usage": usage,
                    "finish_reason": choice.get("finish_reason"),
                    "status_code": getattr(response, "status_code", 200),
                }
                return GenerationResult(choice["message"].get("content") or "", usage, log_record)
            except Exception as exc:  # bounded retry; the sanitized error is recorded by caller
                last_error = str(exc)
                if retry < 2:
                    time.sleep(2 ** retry)
        raise RuntimeError(f"DeepSeek request failed after 3 attempts: {last_error}")
