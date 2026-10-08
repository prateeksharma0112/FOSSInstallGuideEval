"""Orchestrate one installation-guide evaluation run."""

import time
from datetime import datetime
from typing import Any

from installguideeval.config import settings
from installguideeval.inputs import build_prompt, load_criteria, load_task
from installguideeval.llm import EvaluationLLM, LLMResponseError, LLMResult
from installguideeval.models import EvaluationCriteria, EvaluationTask
from installguideeval.results import RunLayout, create_run_layout, write_json, write_text


class EvaluationRunner:
    """Coordinate input loading, one LLM call, and artifact storage."""

    def __init__(self, llm: EvaluationLLM | None = None) -> None:
        self.llm = llm or EvaluationLLM()

    def run(self, task_id: str) -> dict[str, Any]:
        # Start the run timer.
        started_at = datetime.now().astimezone()
        started = time.monotonic()

        # Load the guide and evaluation criteria.
        task = load_task(task_id)
        criteria = load_criteria()

        # Build the prompt.
        prompt = build_prompt(task, criteria)

        # Create the run folder and save the prompt.
        layout = create_run_layout(task.task_id)
        write_text(layout.evaluation_dir / "prompt.md", prompt)

        # Send the prompt to the LLM.
        try:
            llm_result = self.llm.evaluate(prompt)
        except Exception as exc:
            # Save the failed run without retrying.
            return self._save_failure(
                layout=layout,
                task=task,
                criteria=criteria,
                started_at=started_at,
                started=started,
                error=exc,
            )

        return self._save_success(
            layout=layout,
            task=task,
            criteria=criteria,
            started_at=started_at,
            started=started,
            llm_result=llm_result,
        )

    def _save_success(
        self,
        *,
        layout: RunLayout,
        task: EvaluationTask,
        criteria: EvaluationCriteria,
        started_at: datetime,
        started: float,
        llm_result: LLMResult,
    ) -> dict[str, Any]:
        # Save the complete response and the validated report.
        write_json(layout.evaluation_dir / "llm_response.json", llm_result.llm_response)
        write_json(layout.evaluation_dir / "report.json", llm_result.report.model_dump(mode="json"))

        # Save information about the completed run.
        result = self._run_record(
            layout=layout,
            task=task,
            criteria=criteria,
            started_at=started_at,
            started=started,
            status="completed",
            llm_result=llm_result,
        )
        result["artifacts"] = {
            "prompt": "evaluation/prompt.md",
            "llm_response": "evaluation/llm_response.json",
            "report": "evaluation/report.json",
        }
        write_json(layout.run_dir / "run.json", result)
        return result

    def _save_failure(
        self,
        *,
        layout: RunLayout,
        task: EvaluationTask,
        criteria: EvaluationCriteria,
        started_at: datetime,
        started: float,
        error: Exception,
    ) -> dict[str, Any]:
        # Save the error.
        error_data = {"type": type(error).__name__, "message": str(error)}
        write_json(layout.evaluation_dir / "error.json", error_data)

        # Keep the LLM response when validation fails.
        llm_response = error.llm_response if isinstance(error, LLMResponseError) else None
        if llm_response is not None:
            write_json(layout.evaluation_dir / "llm_response.json", llm_response)

        # Save information about the failed run.
        result = self._run_record(
            layout=layout,
            task=task,
            criteria=criteria,
            started_at=started_at,
            started=started,
            status="failed",
            error=error_data,
        )
        result["artifacts"] = {
            "prompt": "evaluation/prompt.md",
            "error": "evaluation/error.json",
        }
        if llm_response is not None:
            result["artifacts"]["llm_response"] = "evaluation/llm_response.json"
        write_json(layout.run_dir / "run.json", result)
        return result

    def _run_record(
        self,
        *,
        layout: RunLayout,
        task: EvaluationTask,
        criteria: EvaluationCriteria,
        started_at: datetime,
        started: float,
        status: str,
        llm_result: LLMResult | None = None,
        error: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        # Add LLM details when a response was successfully validated.
        llm = {"model": self.llm.model_name}
        if llm_result is not None:
            llm.update(
                {
                    "response_id": llm_result.response_id,
                    "input_tokens": llm_result.input_tokens,
                    "output_tokens": llm_result.output_tokens,
                    "total_tokens": llm_result.total_tokens,
                }
            )

        run = {
            "run_id": layout.run_id,
            "experiment_id": settings.experiment_id,
            "run_number": layout.run_number,
            "started_at": started_at.isoformat(),
            "finished_at": datetime.now().astimezone().isoformat(),
            "status": status,
        }
        if error is not None:
            run["error"] = error

        return {
            "run": run,
            # Use the task ID from the dataset folder.
            "task": {**task.metadata, "task_id": task.task_id},
            "criteria": {"version": criteria.criteria_version},
            "llm": llm,
            "duration_seconds": time.monotonic() - started,
        }
