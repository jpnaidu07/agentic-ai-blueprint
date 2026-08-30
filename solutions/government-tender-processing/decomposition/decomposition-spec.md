# Government Tender Intelligence & Bid Evaluation Platform: Decomposition

Generated proposal. Review before approving implementation.

## Schema Version

```yaml
1
...
```

## Solution

government-tender-processing

## Design Digest

12421fd193db8d4e9263803328855ebcbcb4bde335d87c902e07d3ceccd68a82

## Tasks

```yaml
- id: TASK-CAP-IDENTITY
  parent_capability: CAP-IDENTITY
  objective: Enforce authenticated roles and tender scope on every operation including
    documents, searches and audit access.
  skill: security
  dependencies: []
  inputs:
  - capability/capability.yaml
  - design/architecture.yaml
  outputs:
  - implementation/security/cap-identity.md
  affected_modules:
  - implementation/security
  api_contract: Derive request/response and error schemas from this capability; review
    before coding.
  data_contract: Define typed records, relationships, validation and migration from
    this capability.
  agent_tools:
  - Use only design-approved tools with caller resource scope
  instructions:
  - Enforce authenticated roles and tender scope on every operation including documents,
    searches and audit access.
  - Record implementation files and validation evidence in the completion receipt.
  tests:
  - Missing or invalid bearer tokens are rejected.
  - Cross-tender document IDs and bid IDs never reveal evidence.
  - An evaluator cannot approve their own work, including after a role change.
  definition_of_done:
  - Missing or invalid bearer tokens are rejected.
  - Cross-tender document IDs and bid IDs never reveal evidence.
  - An evaluator cannot approve their own work, including after a role change.
  - No secrets; tests pass; evidence reviewed
- id: TASK-CAP-INGEST
  parent_capability: CAP-INGEST
  objective: Validate digital PDF uploads, extract page-aware text and segment evidence
    without losing provenance.
  skill: backend
  dependencies: []
  inputs:
  - capability/capability.yaml
  - design/architecture.yaml
  outputs:
  - implementation/backend/cap-ingest.md
  affected_modules:
  - implementation/backend
  api_contract: Derive request/response and error schemas from this capability; review
    before coding.
  data_contract: Define typed records, relationships, validation and migration from
    this capability.
  agent_tools:
  - Use only design-approved tools with caller resource scope
  instructions:
  - Validate digital PDF uploads, extract page-aware text and segment evidence without
    losing provenance.
  - Record implementation files and validation evidence in the completion receipt.
  tests:
  - Reject malformed, oversized, encrypted, interactive and scanned-only PDFs with
    an actionable response.
  - Uploading identical bytes within the same tender and bid scope returns the existing
    document.
  - Retain original bytes, SHA-256, page text, chunk offsets and scanner status.
  definition_of_done:
  - Reject malformed, oversized, encrypted, interactive and scanned-only PDFs with
    an actionable response.
  - Uploading identical bytes within the same tender and bid scope returns the existing
    document.
  - Retain original bytes, SHA-256, page text, chunk offsets and scanner status.
  - No secrets; tests pass; evidence reviewed
- id: TASK-CAP-FACTS
  parent_capability: CAP-FACTS
  objective: Propose numeric requirement observations through configurable models
    and accept only explicitly reviewed evidence.
  skill: agents
  dependencies: []
  inputs:
  - capability/capability.yaml
  - design/architecture.yaml
  outputs:
  - implementation/agents/cap-facts.md
  affected_modules:
  - implementation/agents
  api_contract: Derive request/response and error schemas from this capability; review
    before coding.
  data_contract: Define typed records, relationships, validation and migration from
    this capability.
  agent_tools:
  - Use only design-approved tools with caller resource scope
  instructions:
  - Propose numeric requirement observations through configurable models and accept
    only explicitly reviewed evidence.
  - Record implementation files and validation evidence in the completion receipt.
  tests:
  - Model output cannot accept facts or approve procurement decisions.
  - Every accepted fact cites an existing page and exact quote in that bidder's document.
  - Missing evidence or invalid model JSON fails without creating facts.
  definition_of_done:
  - Model output cannot accept facts or approve procurement decisions.
  - Every accepted fact cites an existing page and exact quote in that bidder's document.
  - Missing evidence or invalid model JSON fails without creating facts.
  - No secrets; tests pass; evidence reviewed
- id: TASK-CAP-SCORE
  parent_capability: CAP-SCORE
  objective: Calculate published weighted scores, eligibility gates, L1 comparison
    and equal ranks for ties deterministically.
  skill: backend
  dependencies: []
  inputs:
  - capability/capability.yaml
  - design/architecture.yaml
  outputs:
  - implementation/backend/cap-score.md
  affected_modules:
  - implementation/backend
  api_contract: Derive request/response and error schemas from this capability; review
    before coding.
  data_contract: Define typed records, relationships, validation and migration from
    this capability.
  agent_tools:
  - Use only design-approved tools with caller resource scope
  instructions:
  - Calculate published weighted scores, eligibility gates, L1 comparison and equal
    ranks for ties deterministically.
  - Record implementation files and validation evidence in the completion receipt.
  tests:
  - Scored weights total exactly 100 and mandatory eligibility has zero score weight.
  - Missing evidence, low confidence or nonpositive commercial totals block ranking.
  - Ineligible bids cannot set the commercial baseline or receive a rank.
  definition_of_done:
  - Scored weights total exactly 100 and mandatory eligibility has zero score weight.
  - Missing evidence, low confidence or nonpositive commercial totals block ranking.
  - Ineligible bids cannot set the commercial baseline or receive a rank.
  - No secrets; tests pass; evidence reviewed
- id: TASK-CAP-REVIEW
  parent_capability: CAP-REVIEW
  objective: Persist versioned evaluations, reject stale approvals and require independent
    human decisions.
  skill: backend
  dependencies: []
  inputs:
  - capability/capability.yaml
  - design/architecture.yaml
  outputs:
  - implementation/backend/cap-review.md
  affected_modules:
  - implementation/backend
  api_contract: Derive request/response and error schemas from this capability; review
    before coding.
  data_contract: Define typed records, relationships, validation and migration from
    this capability.
  agent_tools:
  - Use only design-approved tools with caller resource scope
  instructions:
  - Persist versioned evaluations, reject stale approvals and require independent
    human decisions.
  - Record implementation files and validation evidence in the completion receipt.
  tests:
  - Repeating an evaluation key with unchanged inputs returns the same result.
  - Reusing the key after evidence changes returns a conflict.
  - A reviewer cannot approve incomplete or stale evidence; approval freezes the reference
    evaluation.
  definition_of_done:
  - Repeating an evaluation key with unchanged inputs returns the same result.
  - Reusing the key after evidence changes returns a conflict.
  - A reviewer cannot approve incomplete or stale evidence; approval freezes the reference
    evaluation.
  - No secrets; tests pass; evidence reviewed
- id: TASK-CAP-SEARCH
  parent_capability: CAP-SEARCH
  objective: Retrieve tender-scoped page evidence using lexical search and expose
    a hybrid retrieval extension.
  skill: rag
  dependencies: []
  inputs:
  - capability/capability.yaml
  - design/architecture.yaml
  outputs:
  - implementation/rag/cap-search.md
  affected_modules:
  - implementation/rag
  api_contract: Derive request/response and error schemas from this capability; review
    before coding.
  data_contract: Define typed records, relationships, validation and migration from
    this capability.
  agent_tools:
  - Use only design-approved tools with caller resource scope
  instructions:
  - Retrieve tender-scoped page evidence using lexical search and expose a hybrid
    retrieval extension.
  - Record implementation files and validation evidence in the completion receipt.
  tests:
  - Unknown queries return insufficient evidence without invented answers.
  - Search results contain document, page, section, bidder and tender identifiers.
  - Structured bidder counts and rankings come from SQL and scoring snapshots, not
    vector similarity.
  definition_of_done:
  - Unknown queries return insufficient evidence without invented answers.
  - Search results contain document, page, section, bidder and tender identifiers.
  - Structured bidder counts and rankings come from SQL and scoring snapshots, not
    vector similarity.
  - No secrets; tests pass; evidence reviewed
- id: TASK-CAP-PORTAL
  parent_capability: CAP-PORTAL
  objective: Provide an accessible portfolio and tender dashboard with evidence review,
    scores, risk flags and audit history.
  skill: frontend
  dependencies: []
  inputs:
  - capability/capability.yaml
  - design/architecture.yaml
  outputs:
  - implementation/frontend/cap-portal.md
  affected_modules:
  - implementation/frontend
  api_contract: Derive request/response and error schemas from this capability; review
    before coding.
  data_contract: Define typed records, relationships, validation and migration from
    this capability.
  agent_tools:
  - Use only design-approved tools with caller resource scope
  instructions:
  - Provide an accessible portfolio and tender dashboard with evidence review, scores,
    risk flags and audit history.
  - Record implementation files and validation evidence in the completion receipt.
  tests:
  - Show active, closed, low-participation and approved tenders from actual records.
  - Render untrusted names, documents and model outputs as text, never HTML.
  - Display stale revisions and missing evidence next to scores and approval controls.
  definition_of_done:
  - Show active, closed, low-participation and approved tenders from actual records.
  - Render untrusted names, documents and model outputs as text, never HTML.
  - Display stale revisions and missing evidence next to scores and approval controls.
  - No secrets; tests pass; evidence reviewed
- id: TASK-CAP-OPS
  parent_capability: CAP-OPS
  objective: Run the development reference on a 32 GB Windows laptop using bounded
    containers and explicit prerequisites.
  skill: infrastructure
  dependencies: []
  inputs:
  - capability/capability.yaml
  - design/architecture.yaml
  outputs:
  - implementation/infrastructure/cap-ops.md
  affected_modules:
  - implementation/infrastructure
  api_contract: Derive request/response and error schemas from this capability; review
    before coding.
  data_contract: Define typed records, relationships, validation and migration from
    this capability.
  agent_tools:
  - Use only design-approved tools with caller resource scope
  instructions:
  - Run the development reference on a 32 GB Windows laptop using bounded containers
    and explicit prerequisites.
  - Record implementation files and validation evidence in the completion receipt.
  tests:
  - Core Compose requires no local LLM and publishes application ports on loopback
    only.
  - Setup detects Docker and credentials, creates unique local identities and never
    installs host system services silently.
  - Provide reproducible tests, evaluation datasets, schema and link validation in
    CI.
  definition_of_done:
  - Core Compose requires no local LLM and publishes application ports on loopback
    only.
  - Setup detects Docker and credentials, creates unique local identities and never
    installs host system services silently.
  - Provide reproducible tests, evaluation datasets, schema and link validation in
    CI.
  - No secrets; tests pass; evidence reviewed
- id: TASK-TESTS
  parent_capability: CAP-IDENTITY
  objective: Validate tests against approved capabilities
  skill: tests
  dependencies:
  - TASK-CAP-IDENTITY
  - TASK-CAP-INGEST
  - TASK-CAP-FACTS
  - TASK-CAP-SCORE
  - TASK-CAP-REVIEW
  - TASK-CAP-SEARCH
  - TASK-CAP-PORTAL
  - TASK-CAP-OPS
  inputs:
  - decomposition/tasks.yaml
  outputs:
  - implementation/tests/evidence.md
  affected_modules:
  - implementation/tests
  api_contract: Exercise approved API contracts
  data_contract: Use synthetic fixtures only
  agent_tools: []
  instructions:
  - Execute the corresponding reusable skill and retain reproducible evidence.
  tests:
  - All prerequisite work packages complete against current specs
  definition_of_done:
  - Evidence exists and reviewer accepts the results
- id: TASK-EVALS
  parent_capability: CAP-IDENTITY
  objective: Validate evals against approved capabilities
  skill: evals
  dependencies:
  - TASK-TESTS
  inputs:
  - decomposition/tasks.yaml
  outputs:
  - implementation/evals/evidence.md
  affected_modules:
  - implementation/evals
  api_contract: Exercise approved API contracts
  data_contract: Use synthetic fixtures only
  agent_tools: []
  instructions:
  - Execute the corresponding reusable skill and retain reproducible evidence.
  tests:
  - All prerequisite work packages complete against current specs
  definition_of_done:
  - Evidence exists and reviewer accepts the results
- id: TASK-DEPLOYMENT
  parent_capability: CAP-IDENTITY
  objective: Validate deployment against approved capabilities
  skill: deployment
  dependencies:
  - TASK-EVALS
  inputs:
  - decomposition/tasks.yaml
  outputs:
  - implementation/deployment/evidence.md
  affected_modules:
  - implementation/deployment
  api_contract: Exercise approved API contracts
  data_contract: Use synthetic fixtures only
  agent_tools: []
  instructions:
  - Execute the corresponding reusable skill and retain reproducible evidence.
  tests:
  - All prerequisite work packages complete against current specs
  definition_of_done:
  - Evidence exists and reviewer accepts the results
```
