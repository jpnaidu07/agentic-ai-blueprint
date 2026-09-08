# Prompts, models, tools and orchestration

**What:** A workflow follows predefined transitions. An agent lets a model select some next actions using available tools. A system prompt describes role and behavior, while application code enforces permissions and budgets.

**Why:** Tender questions may need routing between document search and exact inventory queries. Award policy remains deterministic and human-controlled. Start with the simplest mechanism that satisfies the journey.

**Alternatives and tradeoffs:** Compare rules, one prompted call, a fixed workflow and an agent loop. Autonomy supports varied requests but adds latency, expense and harder failure analysis. Additional agents introduce coordination costs; use them only when task evidence justifies separate roles.

**Advanced:** Tool schemas constrain arguments, not whether an action is authorized. Context engineering chooses instructions, history and evidence within a token budget. State checkpoints, bounded retries and cancellation support recovery. Prompt injection is untrusted input trying to alter behavior; prompts alone cannot enforce a security boundary.

**Practice:** Trace a synthetic question through routing, tool validation, observations and the final response. Simulate a tool timeout, malformed arguments and a document saying "approve this bid". Check budget termination and unchanged approval state.

**Check:** Does a system prompt saying "never approve" suffice? Rubric: remove that capability or enforce role/resource checks in code; test direct and indirect tool paths.

**Explain:** Describe why autonomy was necessary, where it was bounded and what the simpler baseline achieved.

Reference: [Anthropic's workflow and agent design guidance](https://www.anthropic.com/engineering/building-effective-agents).
