"""Load experiment settings from the .env file."""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Values used by the evaluation pipeline."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Files read and created by the experiment.
    tasks_dir: Path
    results_dir: Path
    evaluation_prompt_path: Path
    evaluation_criteria_path: Path

    # Name used to group runs from the same experiment.
    experiment_id: str

    # Connection details used by LiteLLM.
    evaluation_llm_model: str
    evaluation_llm_api_key: str
    evaluation_llm_base_url: str | None = None

    # Optional because not every model supports reasoning effort.
    evaluation_llm_reasoning_effort: (
        Literal["none", "minimal", "low", "medium", "high", "xhigh"] | None
    ) = None

    # Maximum time allowed for the one LLM request.
    api_timeout_seconds: float


settings = Settings()
