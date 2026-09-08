# APIs, services and agent tools: section 4

**What:** An API is a callable contract; a service implements business behavior behind it. An agent tool exposes a constrained operation to the model. The model's request still passes through normal server validation and authorization.

**Why:** A tender UI and an agent can share retrieval services while the approval endpoint independently enforces reviewer identity. Inputs, outputs and errors let section 7 display the real workflow state.

**Alternatives and tradeoffs:** Compare synchronous REST with an asynchronous job for long ingestion; jobs improve responsiveness but require durable status and retries. Compare direct SQL service queries with LLM-generated queries; deterministic queries suit known counts and ranking rules. An MCP transport can standardize tool exposure but is unnecessary for a single internal function.

**Advanced:** Idempotency makes an eligible retry return the same operation result; reusing a key for different input must conflict. Optimistic concurrency checks a revision to prevent overwriting intervening work. Webhooks need authenticity checks, replay handling and a bounded retry policy.

**Practice:** Send an allowed create request, retry it, change the payload under the same idempotency key, then call with a forbidden role. Observe one creation, stable retry, explicit conflict and denied access. Connect a UI error state to the actual response.

**Check:** Is hiding Approve in the UI sufficient? Rubric: direct API/tool callers bypass the screen; enforce identity, role, resource and current revision server-side.

**Explain:** Show the request, contract, service decision, failure path and user-visible result. Do not claim that defining a tool schema implements a real external integration.
