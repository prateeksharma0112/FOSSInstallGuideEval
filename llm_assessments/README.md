# LLM assessments

This directory contains standardized LLM assessment tables used by analysis
scripts. The original, immutable run artifacts remain under `results/`.

## Structure

```text
llm_assessments/
|-- project_mapping.csv
|-- scripts/
|   `-- prepare_llm_data.py
`-- processed/
    `-- <experiment-id>/
        |-- llm_responses.csv
        |-- llm_scores.csv
        `-- validation_summary.json
```

`llm_responses.csv` is the canonical long-form table: one row per project,
criterion, and completed run. `llm_scores.csv` is a readable wide view with the
four run scores in columns.

Prepare one experiment from the repository root:

```powershell
python llm_assessments/scripts/prepare_llm_data.py --experiment GLM_P1
```

Preparation validates that the experiment contains 15 mapped projects, four
completed runs per project, four criteria per run, and scores from 1 to 5.

