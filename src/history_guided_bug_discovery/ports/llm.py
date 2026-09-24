from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol


@dataclass(frozen=True)
class GenerationRequest:
    run_id: str
    request_id: str
    strategy: str
    prompt: str
    model: str
    temperature: float
    max_output_tokens: int
    timeout_seconds: float
    response_format: str = "json_object"
    thinking: str = "disabled"

    @property
    def prompt_hash(self) -> str:
        import hashlib
        return hashlib.sha256(self.prompt.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class GenerationResponse:
    content: str
    usage: Mapping[str, int]
    provider_request_count: int
    log_record: Mapping[str, object]


class LLMProvider(Protocol):
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        ...
