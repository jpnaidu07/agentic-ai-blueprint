# Product UI and API integration: section 7

**What:** The product UI turns a user's goal into visible actions and state. It is separate from the developer Workbench used to build it. A screen is complete when it handles the real API contract, including failure and permission states.

**Why:** An evaluator needs uploads, citations and comparison; a reviewer needs a stable evidence snapshot and a clear decision. A chat box alone cannot replace all these journeys.

**Alternatives and tradeoffs:** Compare a form/table workflow with chat and a mixed interface. Forms constrain exact decisions; chat supports exploration but can conceal state. Server-rendered pages or simple same-origin JavaScript reduce build complexity; a richer client framework may suit complex interaction but requires an approved runtime/build setup.

**Advanced:** Optimistic UI can show success before the server commits; avoid misleading approval status. Accessibility includes focus, keyboard navigation, labels and announced errors. Streaming needs cancellation, final citations and a terminal error state; the current generated preview relay does not support streaming/WebSockets, so this requires a reviewed extension.

**Practice:** Implement one journey against section 4 APIs. Test slow upload, missing file, denied scope, expired session, stale revision and empty results. Navigate using only the keyboard. Check a citation opens the correct document revision/page.

**Check:** Should a network timeout turn an approval green? Rubric: show pending/unknown state, reconcile with the server and avoid a duplicate decision.

**Explain:** Demonstrate a user completing a task and recovering from a failure, including what feedback changed the design.
