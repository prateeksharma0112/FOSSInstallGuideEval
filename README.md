# FOSSInstallGuideEval

FOSSInstallGuideEval is the second experiment for the master's thesis
*Assessing the Ability of Large Language Models to Evaluate Software
Installation Guides*. It evaluates installation guides with an LLM so that the
results can be compared with human expert assessments.

## Evaluation method

Each guide is evaluated once using the same four criteria:

- **Completeness:** coverage of the information needed to install, configure
  where required, and verify the software.
- **Structure:** whether users can find what they need and follow the required
  installation order.
- **Clarity:** whether instructions, commands, prerequisites, configuration
  values, and expected outcomes are precise and unambiguous.
- **Understandability:** how easily the installation steps and technical
  concepts can be understood.

Every criterion receives one score and one brief reason:

| Score | Rating |
| ---: | --- |
| 1 | Very poor |
| 2 | Poor |
| 3 | Adequate |
| 4 | Good |
| 5 | Excellent |

The LLM must evaluate only the supplied guide, must not consult external
sources or infer undocumented information, and must apply the criteria
consistently. The response is constrained to the four required ratings and is
validated with Pydantic.

## Pipeline

```text
Load guide and criteria -> build prompt -> one LLM call -> validate -> save
```

There are no automatic LLM retries. A failed call is saved as a failed run
instead of being silently repeated.

## Code structure

The implementation is kept flat, with one responsibility per file:

```text
installguideeval/
|-- cli.py       # command-line entry point
|-- config.py    # environment settings
|-- inputs.py    # load the guide and criteria, then build the prompt
|-- llm.py       # make one LiteLLM request and validate its response
|-- models.py    # Pydantic input and output models
|-- results.py   # create run directories and write artifacts
`-- runner.py    # coordinate the complete evaluation flow
```

`runner.py` contains the experiment flow. The other files isolate details that
are likely to change independently, such as the model endpoint, prompt inputs,
or result format.

## Setup

From `C:\Users\PSharma\Desktop\MasterThesis\FOSSInstallGuideEval`:

```powershell
C:\Users\PSharma\Desktop\MasterThesis\installguideeval\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Configure the model, API key, and internal endpoint in `.env`. The `.env` file
is excluded from Git.

## Run one evaluation

```powershell
python -m installguideeval.cli --task-id 01-P002-liquio
```

Results are written to:

```text
results/{experiment_id}/{task_id}/run-{number}/
```

A completed run contains:

```text
run.json
evaluation/prompt.md
evaluation/llm_response.json
evaluation/report.json
```

A failed run contains `run.json`, `evaluation/prompt.md`, and
`evaluation/error.json`. Existing run directories are never overwritten.

`run.json` records the task metadata snapshot, criteria version and SHA-256
hash, model, response identifier, token usage, timestamps, duration, status,
and artifact paths.
