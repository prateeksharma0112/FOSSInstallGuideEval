"""Data models used by the evaluation pipeline."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    # Reject unexpected fields instead of silently accepting malformed data.
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class RatingLevel(StrictModel):
    score: int
    label: str = Field(min_length=1)


class Criterion(StrictModel):
    criterion_id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    name: str = Field(min_length=1)
    question: str = Field(min_length=1)


class EvaluationCriteria(StrictModel):
    criteria_version: str = Field(min_length=1)
    title: str = Field(min_length=1)
    rating_scale: list[RatingLevel] = Field(min_length=2)
    criteria: list[Criterion] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_definitions(self) -> "EvaluationCriteria":
        # Criteria are versioned input data, so validate them before contacting
        # the model rather than discovering errors after an expensive request.
        scores = [level.score for level in self.rating_scale]
        if scores != sorted(set(scores)):
            raise ValueError("rating-scale scores must be unique and ordered")
        criterion_ids = [criterion.criterion_id for criterion in self.criteria]
        if len(criterion_ids) != len(set(criterion_ids)):
            raise ValueError("criterion IDs must be unique")
        return self


class EvaluationTask(StrictModel):
    task_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    metadata: dict[str, Any]
    guide_text: str = Field(min_length=1)


Score = Literal[1, 2, 3, 4, 5]


class CriterionRating(StrictModel):
    score: Score
    reason: str = Field(min_length=1)


class EvaluationReport(StrictModel):
    # Fixed field names ensure every guide is evaluated on the same four criteria.
    completeness: CriterionRating
    structure: CriterionRating
    clarity: CriterionRating
    understandability: CriterionRating
