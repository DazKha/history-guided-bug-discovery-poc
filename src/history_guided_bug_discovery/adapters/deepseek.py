from __future__ import annotations

import os
import time

import requests

from ..ports.llm import GenerationRequest, GenerationResponse


class DeepSeekProvider:
    def __init__(self, api_key: str | None = None, endpoint: str = "https://api.deepseek.com/chat/completions", max_retries: int = 3):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is not available in the environment")
        self.endpoint = endpoint
        self.max_retries = max(1, max_retries)
        self.provider_request_count = 0

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        payload = {"model": request.model, "messages": [{"role": "system", "content": "You are an empirical software testing researcher. Follow the requested JSON schema exactly."}, {"role": "user", "content": request.prompt}], "response_format": {"type": request.response_format}, "thinking": {"type": request.thinking}, "max_tokens": request.max_output_tokens, "temperature": request.temperature}
        last_error = ""
        for retry in range(self.max_retries):
            started = time.monotonic()
            try:
                response = requests.post(self.endpoint, headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}, json=payload, timeout=request.timeout_seconds)
                self.provider_request_count += 1
                response.raise_for_status()
                body = response.json()
                choice = body["choices"][0]
                usage = body.get("usage") or {}
                log_record = {"model": body.get("model", request.model), "provider_request_count": self.provider_request_count, "retry_index": retry, "latency_seconds": round(time.monotonic() - started, 3), "usage": usage, "finish_reason": choice.get("finish_reason"), "status_code": getattr(response, "status_code", 200), "prompt_hash": request.prompt_hash}
                return GenerationResponse(choice.get("message", {}).get("content", ""), usage, self.provider_request_count, log_record)
            except Exception as exc:
                last_error = str(exc)
                if retry + 1 < self.max_retries:
                    time.sleep(2 ** retry)
        raise RuntimeError(f"DeepSeek request failed after {self.max_retries} attempts: {last_error}")
