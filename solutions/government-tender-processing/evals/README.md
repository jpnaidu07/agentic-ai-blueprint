# Repeatable evaluation

Run `python -m src.evals.eval_harness` from the checkout root. The harness reads
the versioned synthetic dataset in `../datasets/golden.json`, evaluates actual
retrieval and policy outputs, reports counts and measured latency, and exits
nonzero if a golden expectation fails. Results go under ignored `reports/`.

These ten checks do not measure a production hallucination rate, broad answer
quality, human usefulness, cloud cost or enterprise capacity. Prompt-injection
text in the dataset is retrieved as evidence, never executed. API tests separately
verify that extraction cannot accept facts or issue procurement awards.

For a live-provider release, collect de-identified approved PDFs, page-level gold
annotations and adverse examples (OCR, contradictory tables, wrong units,
certification expiry, bid collusion flags). Compare extraction precision/recall,
quote validity, numeric correctness, abstention and reviewer correction rate.
Record exact model/prompt versions and observed token usage. Obtain human quality
review and measure cost from the provider's current billing data. Do not replace
missing experiments with invented scores.
