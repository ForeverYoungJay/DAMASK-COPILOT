"""Structured Responses API runner."""

from __future__ import annotations

import os
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from damask_copilot.llm.model_config import LLMModelConfig

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class StructuredLLMRunner:
    """Run structured prompts with the OpenAI Responses API."""

    def __init__(
        self,
        model_name: str | None = None,
        *,
        mock_mode: bool | None = None,
        mock_outputs: dict[str, Any] | None = None,
        client: Any | None = None,
    ) -> None:
        self.config = LLMModelConfig.from_env(model_name=model_name, mock_mode=mock_mode)
        self.mock_outputs = mock_outputs or {}
        self._client = client

    def run_structured(
        self,
        *,
        prompt_name: str,
        system_prompt: str,
        user_prompt: str,
        output_schema: type[SchemaT],
        model_name: str | None = None,
    ) -> SchemaT:
        """Execute a structured LLM request and parse into a Pydantic model."""
        if self.config.mock_mode:
            return self._parse_mock(prompt_name=prompt_name, output_schema=output_schema)

        client = self._get_client()
        response = client.responses.parse(
            model=model_name or self.config.model_name,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            text_format=output_schema,
        )
        parsed = getattr(response, "output_parsed", None)
        if parsed is None:
            raise ValueError(f"Structured parsing failed for prompt '{prompt_name}': no parsed output returned.")
        if isinstance(parsed, output_schema):
            return parsed
        return self._validate_output(parsed, output_schema, prompt_name)

    def _parse_mock(self, *, prompt_name: str, output_schema: type[SchemaT]) -> SchemaT:
        if prompt_name not in self.mock_outputs:
            raise KeyError(f"Mock output for prompt '{prompt_name}' is not configured.")
        return self._validate_output(self.mock_outputs[prompt_name], output_schema, prompt_name)

    def _validate_output(self, payload: Any, output_schema: type[SchemaT], prompt_name: str) -> SchemaT:
        try:
            validator = getattr(output_schema, "model_validate", None)
            if validator is not None:
                return validator(payload)
            return output_schema.parse_obj(payload)
        except ValidationError as exc:
            raise ValueError(f"Structured parsing failed for prompt '{prompt_name}': {exc}") from exc

    def _get_client(self):
        if self._client is not None:
            return self._client
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is missing in the current process environment. "
                "Export it in the same shell before running DAMASK Copilot with --llm."
            )
        self._client = OpenAI(api_key=api_key)
        return self._client
