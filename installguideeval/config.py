"""Evaluation settings loaded automatically from the ``.env`` file."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration values with optional overrides from ``.env``."""

    # Pydantic reads matching environment variables and values from .env.
    # Unknown variables are ignored so unrelated local settings do not break a run.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Input and output locations.
    tasks_dir: Path = Path("dataset-02")
    results_dir: Path = Path("results")
    experiment_id: str = Field(
        default="development",
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$",
    )
    evaluation_prompt_path: Path = Path(
        "installguideeval/prompts/evaluation_prompt.md"
    )
    evaluation_criteria_path: Path = Path("criteria/evaluation_criteria.json")

    # Model settings remain provider-neutral because LiteLLM handles the endpoint.
    evaluation_llm_model: str = ""
    evaluation_llm_api_key: str | None = None
    evaluation_llm_base_url: str | None = None
    evaluation_llm_reasoning_effort: (
        Literal["none", "minimal", "low", "medium", "high", "xhigh"] | None
    ) = None
    evaluation_max_output_tokens: int = Field(default=12000, gt=0)

    # The timeout applies to the single LLM request made for each guide.
    api_timeout_seconds: float = Field(default=300, gt=0)


settings = Settings()
