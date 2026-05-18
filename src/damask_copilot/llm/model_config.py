"""Model configuration helpers for LLM-backed agents."""

from __future__ import annotations

import os

from pydantic import BaseModel


class LLMModelConfig(BaseModel):
    """Resolved LLM configuration."""

    model_name: str = "gpt-5.5"
    mock_mode: bool = False

    @classmethod
    def from_env(cls, model_name: str | None = None, mock_mode: bool | None = None) -> "LLMModelConfig":
        """Build model config from explicit args and environment variables."""
        env_model = os.getenv("DAMASK_COPILOT_MODEL")
        env_mock = os.getenv("DAMASK_COPILOT_LLM_MOCK", "").lower() in {"1", "true", "yes", "on"}
        return cls(
            model_name=model_name or env_model or "gpt-5.5",
            mock_mode=env_mock if mock_mode is None else mock_mode,
        )
