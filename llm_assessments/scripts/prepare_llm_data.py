"""Standardize one raw LLM experiment for reproducible analysis."""

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
RESULTS_DIR = ROOT_DIR / "results"
ASSESSMENTS_DIR = ROOT_DIR / "llm_assessments"
MAPPING_PATH = ASSESSMENTS_DIR / "project_mapping.csv"
PROCESSED_DIR = ASSESSMENTS_DIR / "processed"
CRITERIA = ("Completeness", "Structure", "Clarity", "Understandability")
EXPECTED_RUN_COUNT = 4


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Standardize one raw LLM evaluation experiment."
    )
    parser.add_argument(
        "--experiment",
        required=True,
        help="Result experiment directory, for example GLM_P1.",
    )
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as input_file:
        return list(csv.DictReader(input_file))


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as input_file:
        data = json.load(input_file)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return data


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    with temporary_path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    temporary_path.replace(path)


def write_json(path: Path, data: dict[str, Any]) -> None:
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    temporary_path.replace(path)


def load_mapping() -> dict[str, str]:
    rows = read_csv(MAPPING_PATH)
    if len(rows) != 15:
        raise ValueError(f"Expected 15 project mappings, found {len(rows)}")

    task_to_project: dict[str, str] = {}
    project_ids: set[str] = set()
    for row in rows:
        project_id = row["project_id"]
        task_id = row["task_id"]
        if project_id in project_ids or task_id in task_to_project:
            raise ValueError(f"Duplicate project mapping: {row}")
        project_ids.add(project_id)
        task_to_project[task_id] = project_id
    return task_to_project


def load_experiment(
    experiment_id: str, task_to_project: dict[str, str]
) -> tuple[list[dict[str, Any]], dict[str, str], int, int]:
    experiment_dir = RESULTS_DIR / experiment_id
    if not experiment_dir.is_dir():
        raise FileNotFoundError(f"Experiment not found: {experiment_dir}")

    completed_runs: dict[str, list[tuple[dict[str, Any], Path]]] = defaultdict(list)
    failed_attempts = 0
    for run_path in sorted(experiment_dir.glob("*/run-*/run.json")):
        run_record = read_json(run_path)
        run = run_record.get("run", {})
        task_id = run_record.get("task", {}).get("task_id")
        if task_id not in task_to_project:
            raise ValueError(f"Unmapped task in {run_path}: {task_id!r}")
        if run.get("experiment_id") != experiment_id:
            raise ValueError(f"Experiment mismatch in {run_path}")
        if run.get("status") == "failed":
            failed_attempts += 1
            continue
        if run.get("status") != "completed":
            raise ValueError(f"Unexpected run status in {run_path}")
        completed_runs[task_id].append((run_record, run_path))

    if set(completed_runs) != set(task_to_project):
        missing = sorted(set(task_to_project) - set(completed_runs))
        raise ValueError(f"Experiment is missing completed tasks: {missing}")

    rows: list[dict[str, Any]] = []
    metadata: dict[str, str] | None = None
    placeholder_reasons = 0
    for task_id in sorted(completed_runs):
        runs = sorted(
            completed_runs[task_id], key=lambda item: int(item[0]["run"]["run_number"])
        )
        if len(runs) != EXPECTED_RUN_COUNT:
            raise ValueError(
                f"Expected four completed runs for {task_id}, found {len(runs)}"
            )

        for run_record, run_path in runs:
            run = run_record["run"]
            task = run_record["task"]
            llm = run_record["llm"]
            current_metadata = {
                "experiment_id": experiment_id,
                "model_name": llm["model_name"],
                "model_identifier": llm["model_identifier"],
                "prompt_template": run_record["prompt"]["template"],
            }
            if metadata is None:
                metadata = current_metadata
            elif metadata != current_metadata:
                raise ValueError(f"Inconsistent experiment metadata in {run_path}")

            report_relative_path = run_record.get("artifacts", {}).get("report")
            if not report_relative_path:
                raise ValueError(f"Missing report reference in {run_path}")
            report_path = run_path.parent / report_relative_path
            report = read_json(report_path)
            if set(report) != {criterion.lower() for criterion in CRITERIA}:
                raise ValueError(f"Unexpected report criteria in {report_path}")

            for criterion in CRITERIA:
                rating = report[criterion.lower()]
                score = rating.get("score")
                reason = rating.get("reason")
                if not isinstance(score, int) or score not in range(1, 6):
                    raise ValueError(f"Invalid score in {report_path}: {criterion}")
                if not isinstance(reason, str) or not reason.strip():
                    raise ValueError(f"Missing reason in {report_path}: {criterion}")
                cleaned_reason = reason.strip()
                if cleaned_reason in {"...", "…"}:
                    placeholder_reasons += 1
                rows.append(
                    {
                        "project_id": task_to_project[task_id],
                        "project_name": task["project"]["name"],
                        "run_number": run["run_number"],
                        "criterion": criterion,
                        "score": score,
                        "reason": cleaned_reason,
                    }
                )

    if metadata is None:
        raise ValueError(f"No completed runs found for {experiment_id}")
    if len(rows) != 240:
        raise ValueError(f"Expected 240 LLM rating rows, found {len(rows)}")
    return rows, metadata, failed_attempts, placeholder_reasons


def build_score_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], dict[int, int]] = defaultdict(dict)
    for row in rows:
        item = (row["project_id"], row["project_name"], row["criterion"])
        run_number = row["run_number"]
        if run_number in grouped[item]:
            raise ValueError(f"Duplicate score: {item}, run {run_number}")
        grouped[item][run_number] = row["score"]

    output_rows = []
    for item in sorted(grouped, key=lambda value: (value[0], CRITERIA.index(value[2]))):
        run_scores = grouped[item]
        ordered_run_numbers = sorted(run_scores)
        if len(ordered_run_numbers) != EXPECTED_RUN_COUNT:
            raise ValueError(f"Expected four runs for {item}")
        output_rows.append(
            {
                "project_id": item[0],
                "project_name": item[1],
                "criterion": item[2],
                **{
                    f"run_{position}": run_scores[run_number]
                    for position, run_number in enumerate(ordered_run_numbers, start=1)
                },
            }
        )
    if len(output_rows) != 60:
        raise ValueError(f"Expected 60 score rows, found {len(output_rows)}")
    return output_rows


def main() -> None:
    args = parse_args()
    task_to_project = load_mapping()
    rows, metadata, failed_attempts, placeholder_reasons = load_experiment(
        args.experiment, task_to_project
    )
    score_rows = build_score_rows(rows)

    output_dir = PROCESSED_DIR / args.experiment
    output_dir.mkdir(parents=True, exist_ok=True)
    responses_path = output_dir / "llm_responses.csv"
    scores_path = output_dir / "llm_scores.csv"
    summary_path = output_dir / "validation_summary.json"
    write_csv(
        responses_path,
        ["project_id", "project_name", "run_number", "criterion", "score", "reason"],
        rows,
    )
    write_csv(
        scores_path,
        ["project_id", "project_name", "criterion", "run_1", "run_2", "run_3", "run_4"],
        score_rows,
    )
    write_json(
        summary_path,
        {
            **metadata,
            "mapped_projects": len(task_to_project),
            "completed_runs": len(rows) // len(CRITERIA),
            "failed_attempts_retained": failed_attempts,
            "llm_rating_rows": len(rows),
            "llm_score_rows": len(score_rows),
            "placeholder_reasons": placeholder_reasons,
            "criteria": list(CRITERIA),
            "validation_status": (
                "passed_with_reason_warnings" if placeholder_reasons else "passed"
            ),
        },
    )
    print(f"Created {responses_path.relative_to(ROOT_DIR)} ({len(rows)} rows)")
    print(f"Created {scores_path.relative_to(ROOT_DIR)} ({len(score_rows)} rows)")
    print(f"Created {summary_path.relative_to(ROOT_DIR)}")


if __name__ == "__main__":
    main()

