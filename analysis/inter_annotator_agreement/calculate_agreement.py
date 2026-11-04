import csv
import math
import random
from collections import Counter
from pathlib import Path


ANALYSIS_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = ANALYSIS_DIR.parents[1]
INPUT_PATH = (
    REPOSITORY_ROOT / "expert_assessments" / "processed" / "expert_scores.csv"
)
OUTPUTS_DIR = ANALYSIS_DIR / "outputs"
OUTPUT_PATH = OUTPUTS_DIR / "agreement_results.csv"
LEAVE_ONE_OUT_PATH = OUTPUTS_DIR / "leave_one_expert_out_results.csv"

EXPERT_COLUMNS = ("expert_1", "expert_2", "expert_3", "expert_4")
CRITERIA = ("Completeness", "Structure", "Clarity", "Understandability")
EXPECTED_PROJECTS = tuple(f"P{number:03d}" for number in range(1, 16))
BOOTSTRAP_SAMPLES = 10_000
RANDOM_SEED = 20261104


def load_ratings() -> dict[str, dict[str, list[int]]]:
    ratings: dict[str, dict[str, list[int]]] = {}
    with INPUT_PATH.open(encoding="utf-8", newline="") as input_file:
        reader = csv.DictReader(input_file)
        expected_columns = {"project_id", "criterion", *EXPERT_COLUMNS}
        if set(reader.fieldnames or []) != expected_columns:
            raise ValueError(f"Unexpected input columns: {reader.fieldnames}")

        for row in reader:
            project_id = row["project_id"]
            criterion = row["criterion"]
            if project_id not in EXPECTED_PROJECTS:
                raise ValueError(f"Unexpected project: {project_id}")
            if criterion not in CRITERIA:
                raise ValueError(f"Unexpected criterion: {criterion}")
            if criterion in ratings.setdefault(project_id, {}):
                raise ValueError(f"Duplicate item: {project_id}, {criterion}")

            scores = [int(row[column]) for column in EXPERT_COLUMNS]
            if any(score < 1 or score > 5 for score in scores):
                raise ValueError(f"Score outside 1-5: {project_id}, {criterion}")
            ratings[project_id][criterion] = scores

    if tuple(sorted(ratings)) != EXPECTED_PROJECTS:
        raise ValueError("The input must contain projects P001-P015")
    for project_id, project_ratings in ratings.items():
        if set(project_ratings) != set(CRITERIA):
            raise ValueError(f"Incomplete criteria for {project_id}")
    return ratings


def ordinal_distance(
    first: int, second: int, frequencies: Counter[int]
) -> float:
    lower, upper = sorted((first, second))
    if lower == upper:
        return 0.0
    cumulative_frequency = sum(
        frequencies[value] for value in range(lower, upper + 1)
    )
    midpoint_adjustment = (frequencies[lower] + frequencies[upper]) / 2
    return (cumulative_frequency - midpoint_adjustment) ** 2


def krippendorff_alpha_ordinal(units: list[list[int]]) -> float:
    if not units or any(len(unit) < 2 for unit in units):
        raise ValueError("Each unit must contain at least two ratings")

    frequencies = Counter(score for unit in units for score in unit)
    total_ratings = sum(frequencies.values())
    categories = sorted(frequencies)

    observed_disagreement = 0.0
    expected_disagreement = 0.0
    for category_index, first in enumerate(categories):
        for second in categories[category_index + 1 :]:
            distance = ordinal_distance(first, second, frequencies)
            observed_coincidences = sum(
                unit.count(first) * unit.count(second) / (len(unit) - 1)
                for unit in units
            )
            observed_disagreement += observed_coincidences * distance
            expected_disagreement += frequencies[first] * frequencies[second] * distance

    if expected_disagreement == 0:
        return math.nan
    return 1 - (total_ratings - 1) * observed_disagreement / expected_disagreement


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower_index = math.floor(position)
    upper_index = math.ceil(position)
    if lower_index == upper_index:
        return ordered[lower_index]
    fraction = position - lower_index
    return ordered[lower_index] * (1 - fraction) + ordered[upper_index] * fraction


def bootstrap_interval(
    project_units: list[list[list[int]]], random_generator: random.Random
) -> tuple[float, float, int]:
    estimates = []
    project_count = len(project_units)
    for _ in range(BOOTSTRAP_SAMPLES):
        sampled_units = []
        for _ in range(project_count):
            sampled_units.extend(random_generator.choice(project_units))
        estimate = krippendorff_alpha_ordinal(sampled_units)
        if not math.isnan(estimate):
            estimates.append(estimate)

    if not estimates:
        return math.nan, math.nan, 0
    return percentile(estimates, 0.025), percentile(estimates, 0.975), len(estimates)


def summarize(
    label: str,
    project_units: list[list[list[int]]],
    random_generator: random.Random,
) -> dict[str, str | int]:
    units = [unit for project in project_units for unit in project]
    alpha = krippendorff_alpha_ordinal(units)
    confidence_low, confidence_high, valid_samples = bootstrap_interval(
        project_units, random_generator
    )
    return {
        "analysis": label,
        "projects": len(project_units),
        "items": len(units),
        "experts": len(EXPERT_COLUMNS),
        "ordinal_alpha": f"{alpha:.4f}",
        "ci_95_low": f"{confidence_low:.4f}",
        "ci_95_high": f"{confidence_high:.4f}",
        "bootstrap_samples": valid_samples,
    }


def main() -> None:
    ratings = load_ratings()
    random_generator = random.Random(RANDOM_SEED)
    results = []

    for criterion in CRITERIA:
        project_units = [
            [ratings[project_id][criterion]] for project_id in EXPECTED_PROJECTS
        ]
        results.append(summarize(criterion, project_units, random_generator))

    overall_project_units = [
        [ratings[project_id][criterion] for criterion in CRITERIA]
        for project_id in EXPECTED_PROJECTS
    ]
    results.append(summarize("Overall", overall_project_units, random_generator))

    full_alphas = {
        result["analysis"]: float(result["ordinal_alpha"]) for result in results
    }
    leave_one_out_results = []
    for omitted_index, omitted_expert in enumerate(EXPERT_COLUMNS):
        for analysis in (*CRITERIA, "Overall"):
            criteria = CRITERIA if analysis == "Overall" else (analysis,)
            units = [
                [
                    score
                    for expert_index, score in enumerate(ratings[project_id][criterion])
                    if expert_index != omitted_index
                ]
                for project_id in EXPECTED_PROJECTS
                for criterion in criteria
            ]
            alpha = krippendorff_alpha_ordinal(units)
            leave_one_out_results.append(
                {
                    "omitted_expert": omitted_expert,
                    "analysis": analysis,
                    "projects": len(EXPECTED_PROJECTS),
                    "items": len(units),
                    "remaining_experts": len(EXPERT_COLUMNS) - 1,
                    "ordinal_alpha": f"{alpha:.4f}",
                    "full_four_expert_alpha": f"{full_alphas[analysis]:.4f}",
                    "alpha_change": f"{alpha - full_alphas[analysis]:.4f}",
                }
            )

    perfect_agreement = krippendorff_alpha_ordinal(
        [[1, 1, 1, 1], [5, 5, 5, 5]]
    )
    if not math.isclose(perfect_agreement, 1.0):
        raise AssertionError("Krippendorff alpha self-check failed")

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    with LEAVE_ONE_OUT_PATH.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(
            output_file, fieldnames=leave_one_out_results[0].keys()
        )
        writer.writeheader()
        writer.writerows(leave_one_out_results)

    print(f"Created {OUTPUT_PATH}")
    print(f"Created {LEAVE_ONE_OUT_PATH}")
    for result in results:
        print(
            f"{result['analysis']}: alpha={result['ordinal_alpha']} "
            f"(95% CI {result['ci_95_low']} to {result['ci_95_high']})"
        )


if __name__ == "__main__":
    main()
