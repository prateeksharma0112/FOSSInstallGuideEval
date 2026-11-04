# Inter-annotator agreement

This analysis measures agreement among the four human experts before creating a
human reference for comparison with LLM evaluations.

The unit of analysis is one project-criterion pair. Ordinal Krippendorff's alpha
is calculated separately across the 15 projects for completeness, structure,
clarity, and understandability. A supplementary overall alpha uses all 60
project-criterion pairs.

The 95% confidence intervals use 10,000 fixed-seed bootstrap samples. Projects
are resampled as clusters so that the four criteria belonging to the same
project remain together in the overall analysis.

Run from the repository root:

```powershell
python analysis/inter_annotator_agreement/calculate_agreement.py
```

Results are written to `outputs/agreement_results.csv`.

The script also performs a leave-one-expert-out sensitivity analysis. It removes
each expert in turn, recalculates ordinal alpha with the remaining three
experts, and records the change from the four-expert result in
`outputs/leave_one_expert_out_results.csv`. This is a diagnostic and does not by
itself justify excluding an expert.
