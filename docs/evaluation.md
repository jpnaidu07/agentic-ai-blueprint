# Evaluation evidence

The previous document contained hard-coded percentages and latency claims with no
underlying dataset. Those figures have been withdrawn. The current offline harness
reads the versioned synthetic dataset under
`solutions/government-tender-processing/datasets/golden.json`, runs five retrieval
and five deterministic scoring cases, and reports actual counts and measured local
runtime. Run `python -m src.evals.eval_harness`.

This small dataset checks evidence lookup, abstention, prompt-injection-as-data,
eligibility, scoring, low confidence, missing evidence and invalid commercial
values. It does not measure live model accuracy, hallucination, production latency,
human usefulness or cost. See the solution eval README and validation report.
