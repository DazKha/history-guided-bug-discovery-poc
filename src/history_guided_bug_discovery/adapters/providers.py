from __future__ import annotations

from ..config.models import RunConfig
from ..domain.errors import ConfigurationError
from .deepseek import DeepSeekProvider


def create_provider(config: RunConfig):
    """Construct exactly the provider named by configuration."""

    provider = config.model.provider.strip().lower()
    if provider == "deepseek":
        return DeepSeekProvider()
    raise ConfigurationError(f"unsupported model.provider: {config.model.provider}")
