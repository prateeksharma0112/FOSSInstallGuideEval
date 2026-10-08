"""Run one evaluation and save its results."""

import time
from collections.abc import Callable
from datetime import datetime
from typing import Any

from installguideeval.config import settings
from installguideeval.inputs import build_prompt, load_criteria, load_task
from installguideeval.llm import LLMClient, LLMEvaluationResult, LLMResponseError
from installguideeval.models import EvaluationCriteria, EvaluationTask
from installguideeval.results import RunLayout, create_run_layout, write_json, write_text


class EvaluationRunner:
    """Coordinate the evaluation pipeline."""

    def __init__(
        self,
        llm: LLMClient | None = None,
        show_progress: Callable[[str], None] | None = None,
    ) -> None:
        self.llm = llm or LLMClient()
        self.show_progress = show_progress or (lambda message: None)

    def run(self, task_id: str) -> dict[str, Any]:
        # Start the timer.
        started_at = datetime.now().astimezone()
        timer_start = time.monotonic()

        self.show_progress("[1/5] Loading installation guide and criteria")
        task = load_task(task_id)
        criteria = load_criteria()

        self.show_progress("[2/5] Building evaluation prompt")
        prompt = build_prompt(task, criteria)

        self.show_progress("[3/5] Preparing result files")
        layout = create_run_layout(task.task_id)
        write_text(layout.evaluation_dir / "prompt.md", prompt)

        self.show_progress(f"[4/5] Evaluating guide with {self.llm.model_name}")
        try:
            llm_result = self.llm.evaluate(prompt)
        except Exception as exc:
            self.show_progress("[5/5] Saving failed run")
            return self._save_failure(
                layout=layout,
                task=task,
                criteria=criteria,
                started_at=started_at,
                timer_start=timer_start,
                error=exc,
            )

        self.show_progress("[5/5] Saving evaluation results")
        return self._save_success(
            layout=layout,
            task=task,
            criteria=criteria,
            started_at=started_at,
            timer_start=timer_start,
            llm_result=llm_result,
        )

    def _save_success(
        self,
        *,
        layout: RunLayout,
        task: EvaluationTask,
        criteria: EvaluationCriteria,
        started_at: datetime,
        timer_start: float,
        llm_result: LLMEvaluationResult,
    ) -> dict[str, Any]:
        # Save the complete response and the validated report.
        write_json(layout.evaluation_dir / "llm_response.json", llm_result.llm_response)
        write_json(layout.evaluation_dir / "report.json", llm_result.report.model_dump(mode="json"))

        # Save information about the completed run.
        run_record = self._run_record(
            layout=layout,
            task=task,
            criteria=criteria,
            started_at=started_at,
            timer_start=timer_start,
            status="completed",
            llm_result=llm_result,
        )
        run_record["artifacts"] = {
            "prompt": "evaluation/prompt.md",
            "llm_response": "evaluation/llm_response.json",
            "report": "evaluation/report.json",
        }
        write_json(layout.run_dir / "run.json", run_record)
        return run_record

    def _save_failure(
        self,
        *,
        layout: RunLayout,
        task: EvaluationTask,
        criteria: EvaluationCriteria,
        started_at: datetime,
        timer_start: float,
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
        run_record = self._run_record(
            layout=layout,
            task=task,
            criteria=criteria,
            started_at=started_at,
            timer_start=timer_start,
            status="failed",
            error=error_data,
        )
        run_record["artifacts"] = {
            "prompt": "evaluation/prompt.md",
            "error": "evaluation/error.json",
        }
        if llm_response is not None:
            run_record["artifacts"]["llm_response"] = "evaluation/llm_response.json"
        write_json(layout.run_dir / "run.json", run_record)
        return run_record

    def _run_record(
        self,
        *,
        layout: RunLayout,
        task: EvaluationTask,
        criteria: EvaluationCriteria,
        started_at: datetime,
        timer_start: float,
        status: str,
        llm_result: LLMEvaluationResult | None = None,
        error: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        # Add details from a successful response.
        llm_details = {
            "model": self.llm.model_name,
            "reasoning_effort": settings.evaluation_llm_reasoning_effort,
        }
        if llm_result is not None:
            llm_details.update(
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
            "status": status,
            "started_at": started_at.isoformat(),
            "finished_at": datetime.now().astimezone().isoformat(),
            "duration_seconds": round(time.monotonic() - timer_start, 3),
        }
        if error is not None:
            run["error"] = error

        return {
            "run": run,
            "task": {"task_id": task.task_id, **task.metadata},
            "prompt": {"template": settings.evaluation_prompt_path.as_posix()},
            "criteria": {"version": criteria.criteria_version},
            "llm": llm_details,
        }
