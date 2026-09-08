# Identity, permissions and evidence boundaries

**What:** Authentication establishes identity; authorization decides what that identity may do to a resource. An audit record explains which actor changed which version and why.

**Why:** Bids and evaluations have distinct readers and decision makers. The same resource policy must hold through the UI, APIs, retrieval, agents and background processing.

**Alternatives and tradeoffs:** Development tokens support local examples; an identity provider supports organizational identity and lifecycle. Role checks are simple but may need resource/tenant attributes for precise scope. Pre-filtered retrieval limits candidate exposure; filtering only the answer can expose forbidden text earlier in the pipeline.

**Advanced:** Least privilege applies to service accounts and tools as well as people. Retrieved instructions are untrusted data. A hash chain can reveal some alterations but does not prevent a privileged database owner rewriting the chain without an external anchor. Secret rotation and retention need operational owners.

**Practice:** Call the same read and mutation endpoints as two different roles and with an unrelated tender ID. Insert a malicious instruction in a synthetic document and verify it cannot expand tool permissions. Inspect audit metadata without logging secret tokens or full sensitive prompts.

**Check:** Can an evaluator use a second browser tab to approve their own work? Rubric: tabs do not provide identity separation; enforce independent actors and current role/revision policy on the server.

**Explain:** State the concrete trust boundary, exploit you tested and remaining environment controls.
