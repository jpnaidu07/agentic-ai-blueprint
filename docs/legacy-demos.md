# Existing infrastructure simulations

The disk, patch and log examples in `src/solutions/` are retained as explicit,
offline exercises. Synthetic OME/Redfish, ticket, runbook and log records live in
local Python fixtures. Their tools demonstrate schemas, idempotency, DAG concepts
and orchestration traces; they do not connect to Dell OME, Redfish hardware,
ServiceNow, ChromaDB, Slack or Discord. No benchmark percentages are claimed.

The old standalone dashboard and aspirational component documents were removed
because they presented simulated values and unimplemented integrations as measured
or production-ready behavior. Authenticated demo endpoints are disabled by default.
The tender portal is the maintained UI.

These problem statements remain useful engineering exercises. Treat any numeric
threshold, server ID, incident, remediation or runbook text as synthetic and obtain
vendor/domain validation before adapting it to real infrastructure.
