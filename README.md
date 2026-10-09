# FOSSInstallGuideEval

`FOSSInstallGuideEval` implements the second experiment of the master's thesis
*Assessing the Ability of Large Language Models to Evaluate Software
Installation Guides*. The experiment uses an LLM to assess FOSS installation
guides so that its ratings can later be compared with human expert assessments.
This repository runs and records the LLM evaluations; it does not perform the
human comparison itself.

The model assigns each guide a score from 1 (**Very poor**) to 5
(**Excellent**) and a brief reason for each of four documentation-quality
criteria:

- **Completeness:** coverage of the information needed to install, configure
  where required, and verify the software.
- **Structure:** whether users can find the required information and follow the
  installation process in the necessary order.
- **Clarity:** whether instructions, commands, prerequisites, configuration
  values, and expected outcomes are precise and unambiguous.
- **Understandability:** how easy the installation steps are to understand and
  whether technical terms and concepts are explained or require prior
  knowledge.

## How the pipeline works

For each evaluation, the pipeline:

1. loads one installation guide, its metadata, and the shared criteria;
2. inserts the guide and criteria into the selected prompt template;
3. sends one request to the configured model through LiteLLM;
4. validates the structured response with Pydantic; and
5. saves the prompt, raw response, validated report, and run metadata.

Project metadata is stored in the run record for traceability but is not
included in the model prompt.

## Installation

Python 3.10 or newer is required. The selected model endpoint must support
JSON-schema response formatting.

### PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

## Configuration

The `.env.example` file contains all available settings. The main settings are:

```dotenv
EVALUATION_LLM_MODEL=provider/model-name
EVALUATION_LLM_API_KEY=replace-with-api-key
EXPERIMENT_ID=thesis-main-evaluation-01
TASKS_DIR=dataset-02
RESULTS_DIR=results
EVALUATION_PROMPT_PATH=installguideeval/prompts/01_minimal.md
EVALUATION_CRITERIA_PATH=criteria/evaluation_criteria.json
```

A custom API base URL and reasoning effort are optional. Enable reasoning
effort only when the selected model supports it. The `.env` file is ignored by
Git and must not be committed because it contains credentials.

### Evaluation criteria

The rating scale and criterion definitions are stored in
`criteria/evaluation_criteria.json`.

### Prompt templates

Two templates are included:

- `01_minimal.md` contains the task, criteria, scale, and guide.
- `02_structured.md` adds an evaluator role and an explicit procedure.

Select a template with `EVALUATION_PROMPT_PATH`. The `{criteria}` and
`{installation_guide}` placeholders insert the two evaluation inputs into a
template.

## Running evaluations

Run the CLI from the repository root. The task ID is the name of a directory
inside `TASKS_DIR`:

```powershell
python -m installguideeval.cli run --task-id 01-P002-liquio
```

The short option `-t` can be used instead of `--task-id`:

```powershell
python -m installguideeval.cli run -t 01-P002-liquio
```

To evaluate all included tasks in PowerShell:

```powershell
Get-ChildItem dataset-02 -Directory | ForEach-Object {
    python -m installguideeval.cli run --task-id $_.Name
}
```

An evaluation that reaches the model uses one request, with automatic retries
disabled. When result storage is prepared, the pipeline creates the next
available numbered directory (`run-01`, `run-02`, and so on), so existing
results are not overwritten.

## Results

A successful evaluation produces:

```text
results/<experiment-id>/<task-id>/run-NN/
|-- run.json                       # Run metadata and artifact references
`-- evaluation/
    |-- prompt.md                  # Prompt sent to the model
    |-- llm_response.json          # Complete LiteLLM response
    `-- report.json                # Validated ratings and reasons
```

Failures during the model request or response validation are recorded in
`error.json`. If a model response fails validation, the raw response is also
preserved. Input or configuration errors that occur before the result directory
is created are not saved as run artifacts. The process returns a non-zero exit
status whenever an evaluation cannot be completed.

## Repository structure

```text
.
|-- criteria/
|   `-- evaluation_criteria.json   # Rating scale and criteria
|-- dataset-02/
|   `-- <task-id>/
|       |-- metadata.json          # Project and source provenance
|       `-- docs/Installation.md   # Guide to evaluate
|-- installguideeval/
|   |-- prompts/                   # Prompt templates
|   |-- cli.py                     # Command-line interface
|   |-- config.py                  # Environment configuration
|   |-- inputs.py                  # Input and prompt handling
|   |-- llm.py                     # Model request and validation
|   |-- models.py                  # Data schemas
|   |-- results.py                 # Result storage
|   `-- runner.py                  # Pipeline orchestration
|-- .env.example                   # Configuration template
|-- requirements.in                # Direct dependencies
`-- requirements.txt               # Pinned dependencies
```

The included dataset contains 15 installation guides. Each guide is linked to
a specific repository commit in its metadata.

## Reproducibility

The experiment ID groups result directories. Each completed `run.json` records
the task metadata, criteria version, prompt-template path, model name, reasoning
setting, response identifier, token usage, timestamps, duration, and status.
The exact rendered prompt and complete model response are stored alongside it.
The pipeline evaluates local copies of the guides, while their metadata records
the corresponding upstream repository commits.

## Scope

The pipeline evaluates documentation quality. It does not execute installation
instructions or confirm that the software installs successfully. It processes
one task at a time and does not aggregate results or perform statistical
analysis.
