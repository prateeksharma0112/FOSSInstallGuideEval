"""Execute one schema-constrained LLM evaluation request."""

import os
from dataclasses import dataclass
from typing import Any

# Use LiteLLM without downloading pricing data.
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

import litellm

from installguideeval.config import settings
from installguideeval.models import EvaluationReport


@dataclass(frozen=True)
class LLMResult:
    """Validated result and response metadata from one LLM call."""

    report: EvaluationReport
    llm_response: dict[str, Any]
    response_id: str | None
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None


class LLMResponseError(RuntimeError):
    """An unusable LLM response that must still be kept as evidence."""

    def __init__(self, message: str, llm_response: dict[str, Any]) -> None:
        super().__init__(message)
        self.llm_response = llm_response


class EvaluationLLM:
    """Evaluate a prompt through the configured LiteLLM endpoint."""

    def __init__(self) -> None:
        if not settings.evaluation_llm_model:
            raise ValueError("EVALUATION_LLM_MODEL must be configured.")
        if not settings.evaluation_llm_api_key:
            raise ValueError("EVALUATION_LLM_API_KEY must be configured.")
        self.model_name = settings.evaluation_llm_model

    def evaluate(self, prompt: str) -> LLMResult:
        # Send request to the LLM.
        response = litellm.completion(**self._request_parameters(prompt))
        llm_response = response.model_dump(mode="json")
        choice = response.choices[0]

        # Reject responses that cannot be evaluated.
        if choice.finish_reason == "length":
            raise LLMResponseError(
                "The LLM response reached the output-token limit.", llm_response
            )
        if getattr(choice.message, "refusal", None):
            raise LLMResponseError(
                f"The LLM refused the request: {choice.message.refusal}",
                llm_response,
            )
        if not choice.message.content:
            raise LLMResponseError(
                "The LLM returned no evaluation output.", llm_response
            )

        try:
            report = EvaluationReport.model_validate_json(choice.message.content)
        except ValueError as exc:
            raise LLMResponseError(
                f"The LLM returned an invalid evaluation: {exc}", llm_response
            ) from exc

        usage = getattr(response, "usage", None)
        return LLMResult(
            report=report,
            llm_response=llm_response,
            response_id=response.id,
            input_tokens=getattr(usage, "prompt_tokens", None),
            output_tokens=getattr(usage, "completion_tokens", None),
            total_tokens=getattr(usage, "total_tokens", None),
        )

    def _request_parameters(self, prompt: str) -> dict[str, Any]:
        # Build the LiteLLM request.
        parameters: dict[str, Any] = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "api_key": settings.evaluation_llm_api_key,
            "timeout": settings.api_timeout_seconds,
            "num_retries": 0,
            # Request the four ratings in the required JSON structure.
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "guide_evaluation_report",
                    "strict": True,
                    "schema": EvaluationReport.model_json_schema(),
                },
            },
        }

        # Add optional model settings when they are configured.
        if settings.evaluation_llm_base_url:
            parameters["api_base"] = settings.evaluation_llm_base_url
        if settings.evaluation_llm_reasoning_effort:
            parameters["reasoning_effort"] = settings.evaluation_llm_reasoning_effort
        return parameters
