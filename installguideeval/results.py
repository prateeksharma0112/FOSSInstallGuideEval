"""Create run folders and save result files."""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from installguideeval.config import settings

_RUN_DIRECTORY_PATTERN = re.compile(r"^run-(\d+)$")


@dataclass(frozen=True)
class RunLayout:
    run_id: str
    run_number: int
    run_dir: Path
    evaluation_dir: Path


def create_run_layout(task_id: str) -> RunLayout:
    """Create the next non-overwriting result directory for a task."""

    task_results_dir = settings.results_dir / settings.experiment_id / task_id
    existing_numbers = []

    # Find the next run number without overwriting earlier results.
    if task_results_dir.is_dir():
        for existing_run_dir in task_results_dir.iterdir():
            match = _RUN_DIRECTORY_PATTERN.fullmatch(existing_run_dir.name)
            if existing_run_dir.is_dir() and match:
                existing_numbers.append(int(match.group(1)))

    run_number = max(existing_numbers, default=0) + 1
    run_name = f"run-{run_number:02d}"
    run_dir = task_results_dir / run_name
    evaluation_dir = run_dir / "evaluation"

    evaluation_dir.mkdir(parents=True, exist_ok=False)
    return RunLayout(
        run_id=f"{settings.experiment_id}__{task_id}__{run_name}",
        run_number=run_number,
        run_dir=run_dir,
        evaluation_dir=evaluation_dir,
    )


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
