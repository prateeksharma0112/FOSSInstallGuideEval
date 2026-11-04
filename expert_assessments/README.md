# Expert assessments

This directory contains the human expert assessments.

## Structure

- `raw/result.json` is the original survey export and must not be edited.
- `processed/expert_scores.csv` contains the 240 numerical ratings used for
  statistical agreement analysis.
- `processed/expert_assessments.csv` contains all scores and written reasons in
  question order (`q1` score, `q2` reason, through `q8`).
- `processed/human_reference.csv` contains the four original expert scores and
  their mean and median for each project-criterion item.
- `scripts/prepare_expert_data.py` reproducibly generates both processed files
  from the raw JSON.

## Expert mapping

- `expert_1`: response ID 8
- `expert_2`: response ID 9
- `expert_3`: response ID 10
- `expert_4`: response ID 11

The preparation script repairs visible mojibake in processed reason text, such
as `â€™` to `’`, without modifying the raw source file.

Run the preparation step from the repository root:

```powershell
python expert_assessments/scripts/prepare_expert_data.py
```
