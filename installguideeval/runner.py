"""Run one installation-guide evaluation and save its evidence."""

import hashlib
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from installguideeval.config import settings
from installguideeval.evaluation_llm import EvaluationLLM
from installguideeval.models import EvaluationCriteria, EvaluationTask
_RUN_DIRECTORY_PATTERN = re.compile(r"^run-(\d+)$")


class EvaluationRunner:
    def __init__(self) -> None:
        self.llm = EvaluationLLM()

    def run(self, task_id: str) -> dict[str, Any]:
        started_at = datetime.now().astimezone()
        started = time.monotonic()
        task = self._load_task(task_id)
        criteria, criteria_sha256 = self._load_criteria()
        prompt = self._build_prompt(task, criteria)
        run_dir, run_number, run_id = self._allocate_run(task.task_id)
        evaluation_dir = run_dir / "evaluation"
        evaluation_dir.mkdir()
        self._write_text(evaluation_dir / "prompt.md", prompt)

        try:
            llm_result = self.llm.evaluate(prompt)
        except Exception as exc:
            error = {"type": type(exc).__name__, "message": str(exc)}
            self._write_json(evaluation_dir / "error.json", error)
            run_result = {
                "run": {
                    "run_id": run_id,
                    "experiment_id": settings.experiment_id,
                    "run_number": run_number,
                    "started_at": started_at.isoformat(),
                    "finished_at": datetime.now().astimezone().isoformat(),
                    "status": "failed",
                    "error": error,
                },
                "task": {"task_id": task.task_id, **task.metadata},
                "criteria": {
                    "version": criteria.criteria_version,
                    "sha256": criteria_sha256,
                },
                "llm": {"model": self.llm.model_name},
                "duration_seconds": time.monotonic() - started,
                "artifacts": {
                    "prompt": "evaluation/prompt.md",
                    "error": "evaluation/error.json",
                },
            }
            self._write_json(run_dir / "run.json", run_result)
            return run_result

        finished_at = datetime.now().astimezone()
        self._write_json(evaluation_dir / "raw_response.json", llm_result.raw_response)
        self._write_json(
            evaluation_dir / "report.json",
            llm_result.report.model_dump(mode="json"),
        )

        run_result = {
            "run": {
                "run_id": run_id,
                "experiment_id": settings.experiment_id,
                "run_number": run_number,
                "started_at": started_at.isoformat(),
                "finished_at": finished_at.isoformat(),
                "status": "completed",
            },
            "task": {"task_id": task.task_id, **task.metadata},
            "criteria": {
                "version": criteria.criteria_version,
                "sha256": criteria_sha256,
            },
            "llm": {
                "model": self.llm.model_name,
                "response_id": llm_result.response_id,
                "input_tokens": llm_result.input_tokens,
                "output_tokens": llm_result.output_tokens,
                "total_tokens": llm_result.total_tokens,
            },
            "duration_seconds": time.monotonic() - started,
            "artifacts": {
                "prompt": "evaluation/prompt.md",
                "raw_response": "evaluation/raw_response.json",
                "report": "evaluation/report.json",
            },
        }
        self._write_json(run_dir / "run.json", run_result)
        return run_result

    @staticmethod
    def _load_task(task_id: str) -> EvaluationTask:
        tasks_root = settings.tasks_dir.resolve()
        task_dir = (tasks_root / task_id).resolve()
        if not task_dir.is_relative_to(tasks_root):
            raise ValueError(f"Invalid task ID: {task_id}")
        if not task_dir.is_dir():
            raise FileNotFoundError(f"Task not found: {task_id}")

        metadata_path = task_dir / "metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        guide_path = task_dir / "docs" / "Installation.md"
        if not guide_path.is_file():
            guide_path = task_dir / "docs" / "installation.md"
        if not guide_path.is_file():
            raise FileNotFoundError(f"Installation guide not found: {task_dir / 'docs'}")

        return EvaluationTask(
            task_id=task_id,
            metadata=metadata,
            guide_text=guide_path.read_text(encoding="utf-8"),
        )

    @staticmethod
    def _load_criteria() -> tuple[EvaluationCriteria, str]:
        content = settings.evaluation_criteria_path.read_bytes()
        criteria = EvaluationCriteria.model_validate_json(content)
        return criteria, hashlib.sha256(content).hexdigest()

    @staticmethod
    def _build_prompt(task: EvaluationTask, criteria: EvaluationCriteria) -> str:
        template = settings.evaluation_prompt_path.read_text(encoding="utf-8")
        return template.format(
            criteria=json.dumps(criteria.model_dump(mode="json"), indent=2),
            installation_guide=task.guide_text.strip(),
        )

    @staticmethod
    def _allocate_run(task_id: str) -> tuple[Path, int, str]:
        task_dir = settings.results_dir / settings.experiment_id / task_id
        existing_numbers = []
        if task_dir.is_dir():
            for path in task_dir.iterdir():
                match = _RUN_DIRECTORY_PATTERN.fullmatch(path.name)
                if path.is_dir() and match:
                    existing_numbers.append(int(match.group(1)))
        run_number = max(existing_numbers, default=0) + 1
        run_name = f"run-{run_number:02d}"
        run_dir = task_dir / run_name
        run_dir.mkdir(parents=True, exist_ok=False)
        run_id = f"{settings.experiment_id}__{task_id}__{run_name}"
        return run_dir, run_number, run_id

    @staticmethod
    def _write_json(path: Path, data: dict[str, Any]) -> None:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    def _write_text(path: Path, text: str) -> None:
        path.write_text(text, encoding="utf-8")
