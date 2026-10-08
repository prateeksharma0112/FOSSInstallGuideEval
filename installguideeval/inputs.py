"""Load evaluation inputs and assemble the prompt."""

import hashlib
import json

from installguideeval.config import settings
from installguideeval.models import EvaluationCriteria, EvaluationTask


def load_task(task_id: str) -> EvaluationTask:
    """Load one installation guide and its metadata snapshot."""

    tasks_root = settings.tasks_dir.resolve()
    task_dir = (tasks_root / task_id).resolve()

    # Prevent values such as "../other-folder" from escaping the dataset directory.
    if not task_dir.is_relative_to(tasks_root):
        raise ValueError(f"Invalid task ID: {task_id}")
    if not task_dir.is_dir():
        raise FileNotFoundError(f"Task not found: {task_id}")

    metadata_path = task_dir / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    # Existing guides use both capitalization styles, so accept either one.
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


def load_criteria() -> tuple[EvaluationCriteria, str]:
    """Load the criteria and return their SHA-256 fingerprint."""

    content = settings.evaluation_criteria_path.read_bytes()
    criteria = EvaluationCriteria.model_validate_json(content)

    # The hash makes it possible to prove exactly which criteria file a run used.
    return criteria, hashlib.sha256(content).hexdigest()


def build_prompt(task: EvaluationTask, criteria: EvaluationCriteria) -> str:
    """Insert the criteria and guide into the versioned prompt template."""

    template = settings.evaluation_prompt_path.read_text(encoding="utf-8")

    # Only the criteria and guide are sent to the model. Project metadata is kept
    # for traceability in run.json and cannot influence the evaluation.
    return template.format(
        criteria=json.dumps(criteria.model_dump(mode="json"), indent=2),
        installation_guide=task.guide_text.strip(),
    )
