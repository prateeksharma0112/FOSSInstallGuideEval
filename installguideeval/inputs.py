"""Load the guide and criteria, then build the prompt."""

import json

from installguideeval.config import settings
from installguideeval.models import EvaluationCriteria, EvaluationTask


def load_task(task_id: str) -> EvaluationTask:
    """Load one installation guide and its metadata."""

    task_dir = settings.tasks_dir / task_id
    if not task_dir.is_dir():
        raise FileNotFoundError(f"Task not found: {task_id}")

    metadata_path = task_dir / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    guide_path = task_dir / "docs" / "Installation.md"
    if not guide_path.is_file():
        raise FileNotFoundError(f"Installation guide not found: {guide_path}")

    return EvaluationTask(
        task_id=task_id,
        metadata=metadata,
        guide_text=guide_path.read_text(encoding="utf-8"),
    )


def load_criteria() -> EvaluationCriteria:
    """Load the criteria used for every evaluation."""

    criteria_json = settings.evaluation_criteria_path.read_bytes()
    return EvaluationCriteria.model_validate_json(criteria_json)


def build_prompt(task: EvaluationTask, criteria: EvaluationCriteria) -> str:
    """Build the prompt sent to the LLM."""

    template = settings.evaluation_prompt_path.read_text(encoding="utf-8")

    return template.format(
        criteria=json.dumps(criteria.model_dump(mode="json"), indent=2),
        installation_guide=task.guide_text.strip(),
    )
