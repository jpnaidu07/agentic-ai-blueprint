# Verification map

Executable tests are under the shared `src/tests/` package. Run
`python -m pytest -q` from the checkout root. Tests create temporary databases and
synthetic digital PDFs; no confidential files or live model credentials are used.

The tender suite exercises authenticated API flows, duplicate uploads, quotes
and page validation, cross-tender and cross-bid denial, Decimal scoring, ties,
ineligible L1 exclusion, unknown-query abstention, low-confidence handling,
immutable facts, verified audit chains, concurrent idempotency, stale approvals,
independent reviewers and approved-version freezing. Provider tests intercept
HTTP and cover request schemas, missing credentials, retries/refusals and invalid
outputs. Spec tests check first-run behavior, approval staleness, path safety,
dependency cycles and changed evidence.

See `docs/validation-report.md` at the repository root for execution evidence and
the distinction between local checks, CI coverage and unexecuted external tests.
