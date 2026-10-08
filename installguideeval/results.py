"""Allocate immutable run directories and write JSON/text artifacts."""

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

    task_dir = settings.results_dir / settings.experiment_id / task_id
    existing_numbers = []

    # Continue after the highest existing run number. Previous experimental
    # evidence is never overwritten.
    if task_dir.is_dir():
        for path in task_dir.iterdir():
            match = _RUN_DIRECTORY_PATTERN.fullmatch(path.name)
            if path.is_dir() and match:
                existing_numbers.append(int(match.group(1)))

    run_number = max(existing_numbers, default=0) + 1
    run_name = f"run-{run_number:02d}"
    run_dir = task_dir / run_name
    evaluation_dir = run_dir / "evaluation"

    # exist_ok=False also protects against an accidental numbering collision.
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
