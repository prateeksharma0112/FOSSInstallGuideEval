# FOSSInstallGuideEval

FOSSInstallGuideEval performs criteria-based LLM evaluation of installation
guides for free and open-source software. It is the companion experiment to
FOSSInstallBench.

The pipeline loads one guide and its immutable metadata snapshot, loads a
versioned criteria set, requests a schema-constrained evaluation, validates the
response with Pydantic, and saves both normalized results and raw provider
evidence.

## Setup

1. Create and activate a Python 3.11+ virtual environment.
2. Install the dependencies from `requirements.in`.
3. Copy `.env.example` to `.env` and configure the model.
4. Review the versioned thesis criteria before starting the main experiment.

## Run one evaluation

```powershell
python -m installguideeval.cli --task-id 01-P002-liquio
```

Results are written below
`results/{experiment_id}/{task_id}/run-{number}/` without overwriting an
existing run.
