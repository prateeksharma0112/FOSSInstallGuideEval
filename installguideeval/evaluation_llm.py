"""Generic LiteLLM call with schema-constrained output."""

import os
from dataclasses import dataclass
from typing import Any

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

import litellm

from installguideeval.config import settings
from installguideeval.models import EvaluationReport


@dataclass(frozen=True)
class LLMResult:
    report: EvaluationReport
    llm_response: dict[str, Any]
    response_id: str | None
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None


class EvaluationLLM:
    def __init__(self) -> None:
        if not settings.evaluation_llm_model:
            raise ValueError("EVALUATION_LLM_MODEL must be configured.")
        if not settings.evaluation_llm_api_key:
            raise ValueError("EVALUATION_LLM_API_KEY must be configured.")
        self.model_name = settings.evaluation_llm_model

    def evaluate(self, prompt: str) -> LLMResult:
        request: dict[str, Any] = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "api_key": settings.evaluation_llm_api_key,
            "max_tokens": settings.evaluation_max_output_tokens,
            "timeout": settings.api_timeout_seconds,
            "num_retries": 0,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "guide_evaluation_report",
                    "strict": True,
                    "schema": EvaluationReport.model_json_schema(),
                },
            },
        }
        if settings.evaluation_llm_base_url:
            request["api_base"] = settings.evaluation_llm_base_url
        if settings.evaluation_llm_reasoning_effort:
            request["reasoning_effort"] = settings.evaluation_llm_reasoning_effort

        response = litellm.completion(**request)
        choice = response.choices[0]
        if choice.finish_reason == "length":
            raise RuntimeError("The LLM response reached the output-token limit.")
        if getattr(choice.message, "refusal", None):
            raise RuntimeError(f"The LLM refused the request: {choice.message.refusal}")
        if not choice.message.content:
            raise RuntimeError("The LLM returned no evaluation output.")

        report = EvaluationReport.model_validate_json(choice.message.content)
        usage = getattr(response, "usage", None)
        return LLMResult(
            report=report,
            llm_response=response.model_dump(mode="json"),
            response_id=response.id,
            input_tokens=getattr(usage, "prompt_tokens", None),
            output_tokens=getattr(usage, "completion_tokens", None),
            total_tokens=getattr(usage, "total_tokens", None),
        )
