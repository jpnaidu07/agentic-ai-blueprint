# From architecture to deliverable work

**What:** Decomposition splits an approved design into tasks with inputs, outputs, dependencies and observable completion checks. A dependency graph prevents consuming an interface or data guarantee before it exists.

**Why:** A tender screen depends on an API contract and identity rules; vector retrieval depends on ingestion and indexed metadata. Build small vertical slices so a user can try a complete journey early.

**Alternatives and tradeoffs:** Compare a vertical slice (upload → view one citation) with a horizontal layer (all database tables first). The first exposes product misunderstandings earlier; the second can establish shared foundations. A single huge task reduces coordination but makes failure localization and review harder.

**Advanced:** Distinguish engineering dependencies from external blockers such as an identity tenant or data owner. Trace capability → task → acceptance test → evidence so scope changes have visible downstream impact. Critical-path work controls delivery time; parallel-looking tasks may still edit shared files.

**Practice:** Decompose a document question into storage, permission filter, search API and display work. Add tests and owners, then change the document revision contract and identify which tasks/evidence must be revalidated.

**Check:** Can section 7 finish before section 4? Rubric: a mock UI may validate the journey, but integrated completion needs the actual API/auth contract and evidence; use explicit dependencies.

**Explain:** Describe the smallest useful customer demo, what it proves and what remains blocked.
