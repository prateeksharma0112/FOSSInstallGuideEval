"""Call the custom CLEF SystemOne endpoint and normalize its ratings."""

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from installguideeval.config import settings
from installguideeval.llm import LLMEvaluationResult, LLMResponseError
from installguideeval.models import EvaluationCriteria, EvaluationReport, EvaluationTask


class CLEFClient:
    """Evaluate a guide through the custom SystemOne API."""

    def __init__(self) -> None:
        if not settings.evaluation_llm_base_url:
            raise ValueError("EVALUATION_LLM_BASE_URL must be configured for CLEF.")
        self.model_name = settings.evaluation_llm_model
        self.endpoint = settings.evaluation_llm_base_url

    def evaluate(
        self,
        prompt: str,
        *,
        task: EvaluationTask | None = None,
        criteria: EvaluationCriteria | None = None,
    ) -> LLMEvaluationResult:
        del prompt
        if task is None or criteria is None:
            raise ValueError("CLEF requires the evaluation task and criteria.")

        payload = self._build_payload(task, criteria)
        request = Request(
            self.endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=settings.api_timeout_seconds) as response:
                llm_response = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            response_body = exc.read().decode("utf-8", errors="replace")
            try:
                error_response = json.loads(response_body)
            except json.JSONDecodeError:
                error_response = {"body": response_body}
            raise LLMResponseError(
                f"CLEF returned HTTP {exc.code}: {response_body}", error_response
            ) from exc
        except URLError as exc:
            raise RuntimeError(f"Could not connect to CLEF: {exc.reason}") from exc

        report = self._normalize_report(llm_response, criteria)
        usage = llm_response.get("usage", {})
        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")
        total_tokens = (
            input_tokens + output_tokens
            if isinstance(input_tokens, int) and isinstance(output_tokens, int)
            else None
        )
        return LLMEvaluationResult(
            report=report,
            llm_response=llm_response,
            response_id=llm_response.get("id"),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            request_payload=payload,
        )

    def _build_payload(
        self, task: EvaluationTask, criteria: EvaluationCriteria
    ) -> dict[str, Any]:
        levels = [f"{level.score} - {level.label}" for level in criteria.rating_scale]
        questions = {
            code: {
                "type": "score",
                "instructions": instruction,
                "criteria": levels,
            }
            for code, instruction in criteria.criteria.items()
        }
        return {
            "model": self.model_name,
            "state": task.guide_text,
            "questions": questions,
        }

    def _normalize_report(
        self, llm_response: dict[str, Any], criteria: EvaluationCriteria
    ) -> EvaluationReport:
        answers = llm_response.get("answers")
        if not isinstance(answers, dict):
            raise LLMResponseError("CLEF returned no answers.", llm_response)

        ratings: dict[str, dict[str, Any]] = {}
        for code in criteria.criteria:
            answer = answers.get(code)
            if not isinstance(answer, dict):
                raise LLMResponseError(
                    f"CLEF returned no answer for {code}.", llm_response
                )
            if answer.get("type") != "score":
                raise LLMResponseError(
                    f"CLEF returned a non-score answer for {code}.", llm_response
                )
            probabilities = answer.get("probabilities")
            if not isinstance(probabilities, dict) or not probabilities:
                raise LLMResponseError(
                    f"CLEF returned no probabilities for {code}.", llm_response
                )
            expected_categories = {
                str(index) for index in range(len(criteria.rating_scale))
            }
            if set(probabilities) != expected_categories:
                raise LLMResponseError(
                    f"CLEF returned unexpected score categories for {code}.",
                    llm_response,
                )
            try:
                category = max(probabilities, key=lambda key: float(probabilities[key]))
                score = int(category) + 1
            except (TypeError, ValueError) as exc:
                raise LLMResponseError(
                    f"CLEF returned invalid probabilities for {code}.", llm_response
                ) from exc
            ratings[code] = {
                "score": score,
                "reason": "...",
            }

        try:
            return EvaluationReport.model_validate(ratings)
        except ValueError as exc:
            raise LLMResponseError(
                f"CLEF returned an invalid evaluation: {exc}", llm_response
            ) from exc
