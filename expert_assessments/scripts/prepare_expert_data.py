import csv
import json
import re
import statistics
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
SOURCE_PATH = BASE_DIR / "raw" / "result.json"
PROCESSED_DIR = BASE_DIR / "processed"
SCORES_PATH = PROCESSED_DIR / "expert_scores.csv"
ASSESSMENTS_PATH = PROCESSED_DIR / "expert_assessments.csv"
HUMAN_REFERENCE_PATH = PROCESSED_DIR / "human_reference.csv"

ANNOTATORS = (8, 9, 10, 11)
EXPERT_COLUMNS = tuple(f"expert_{number}" for number in range(1, 5))
PROJECTS = tuple(f"P{number:03d}" for number in range(1, 16))
QUESTION_TO_CRITERION = {
    1: "Completeness",
    3: "Structure",
    5: "Clarity",
    7: "Understandability",
}
FIELD_PATTERN = re.compile(r"^(P\d{3})q([1-8])\.")
SCORE_PATTERN = re.compile(r"^([1-5])\s*=\s*.+$")


def repair_mojibake(value: str) -> str:
    if not any(marker in value for marker in ("â", "Ã", "Â")):
        return value
    try:
        return value.encode("cp1252").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value


def load_responses() -> list[dict]:
    with SOURCE_PATH.open(encoding="utf-8") as source_file:
        data = json.load(source_file)
    responses = data.get("responses")
    if not isinstance(responses, list):
        raise ValueError("Expected 'responses' to be a list")
    return responses


def extract_data() -> tuple[dict, dict]:
    ratings: dict[tuple[str, str], dict[int, int]] = {}
    reasons: dict[tuple[str, str], dict[int, str]] = {}
    found_annotators = []

    for response in load_responses():
        annotator_id = response.get("id. Response ID")
        if annotator_id not in ANNOTATORS or annotator_id in found_annotators:
            raise ValueError(f"Unexpected or duplicate annotator: {annotator_id!r}")
        found_annotators.append(annotator_id)

        matched_fields = 0
        for field_name, field_value in response.items():
            field_match = FIELD_PATTERN.match(field_name)
            if field_match is None:
                continue

            project_id = field_match.group(1)
            question_number = int(field_match.group(2))
            if project_id not in PROJECTS:
                raise ValueError(f"Unexpected project: {project_id}")
            if not isinstance(field_value, str) or not field_value.strip():
                raise ValueError(
                    f"Missing response for annotator {annotator_id}, "
                    f"{project_id}q{question_number}"
                )

            score_question = question_number if question_number % 2 else question_number - 1
            criterion = QUESTION_TO_CRITERION[score_question]
            item = (project_id, criterion)
            target = ratings if question_number % 2 else reasons
            if annotator_id in target.setdefault(item, {}):
                raise ValueError(
                    f"Duplicate response for annotator {annotator_id}, "
                    f"{project_id}q{question_number}"
                )

            if question_number % 2:
                score_match = SCORE_PATTERN.fullmatch(field_value.strip())
                if score_match is None:
                    raise ValueError(
                        f"Invalid score for annotator {annotator_id}, "
                        f"{project_id}q{question_number}: {field_value!r}"
                    )
                target[item][annotator_id] = int(score_match.group(1))
            else:
                target[item][annotator_id] = repair_mojibake(field_value)
            matched_fields += 1

        if matched_fields != 120:
            raise ValueError(
                f"Expected 120 assessment fields for annotator {annotator_id}, "
                f"found {matched_fields}"
            )

    if tuple(sorted(found_annotators)) != ANNOTATORS:
        raise ValueError(f"Expected annotators {ANNOTATORS}, found {found_annotators}")

    expected_items = {
        (project_id, criterion)
        for project_id in PROJECTS
        for criterion in QUESTION_TO_CRITERION.values()
    }
    for name, values in (("ratings", ratings), ("reasons", reasons)):
        if set(values) != expected_items:
            raise ValueError(f"Unexpected or missing {name} items")
        for item, expert_values in values.items():
            if set(expert_values) != set(ANNOTATORS):
                raise ValueError(f"Incomplete {name} for {item}")

    return ratings, reasons


def write_csv(path: Path, rows: list[list]) -> None:
    temporary_path = path.with_suffix(".csv.tmp")
    with temporary_path.open("w", encoding="utf-8", newline="") as output_file:
        csv.writer(output_file).writerows(rows)
    temporary_path.replace(path)


def main() -> None:
    ratings, reasons = extract_data()
    PROCESSED_DIR.mkdir(exist_ok=True)

    score_rows = [["project_id", "criterion", *EXPERT_COLUMNS]]
    human_reference_rows = [
        [
            "project_id",
            "criterion",
            *EXPERT_COLUMNS,
            "human_mean",
            "human_median",
        ]
    ]
    assessment_rows = [
        [
            "project_id",
            "question_code",
            "criterion",
            "response_type",
            *EXPERT_COLUMNS,
        ]
    ]

    for project_id in PROJECTS:
        for question_number, criterion in QUESTION_TO_CRITERION.items():
            item = (project_id, criterion)
            item_scores = [
                ratings[item][annotator_id] for annotator_id in ANNOTATORS
            ]
            score_rows.append(
                [project_id, criterion] + item_scores
            )
            human_reference_rows.append(
                [project_id, criterion]
                + item_scores
                + [
                    f"{statistics.mean(item_scores):.2f}",
                    f"{statistics.median(item_scores):.2f}",
                ]
            )
            assessment_rows.append(
                [project_id, f"{project_id}q{question_number}", criterion, "score"]
                + [ratings[item][annotator_id] for annotator_id in ANNOTATORS]
            )
            assessment_rows.append(
                [project_id, f"{project_id}q{question_number + 1}", criterion, "reason"]
                + [reasons[item][annotator_id] for annotator_id in ANNOTATORS]
            )

    write_csv(SCORES_PATH, score_rows)
    write_csv(ASSESSMENTS_PATH, assessment_rows)
    write_csv(HUMAN_REFERENCE_PATH, human_reference_rows)
    print(
        "Created 60 score rows, 120 vertical assessment rows, "
        "and 60 human reference rows."
    )


if __name__ == "__main__":
    main()
