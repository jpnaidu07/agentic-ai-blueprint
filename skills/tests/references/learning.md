# Engineering checks and failure diagnosis

**What:** A test compares observed behavior with a defined expectation. Unit tests isolate logic, integration tests exercise boundaries, and end-to-end tests follow a user journey.

**Why:** A tender app needs more than a happy-path screen: malformed uploads, conflicting updates and unauthorized reads must behave predictably. Acceptance criteria anchor tests to user value.

**Alternatives and tradeoffs:** Mocks make isolated checks fast but cannot establish real provider, database or network behavior. Real integrations provide stronger boundary evidence with more setup and variability. A small meaningful suite is better evidence than many assertions that reproduce the code's logic.

**Advanced:** Contract tests catch API/UI incompatibility. Property-based tests explore invariants across generated inputs. Concurrency tests expose races a sequential fixture misses. Reproducible seeds, logs and minimized failing cases shorten diagnosis; do not fix a failure by weakening the acceptance expectation.

**Practice:** Trace one acceptance criterion to a unit test and an integrated request. Deliberately introduce a defect, observe the correct failure, restore the code and verify success. Keep the experiment isolated and record actual commands.

**Check:** Do mocked embedding tests prove retrieval quality? Rubric: they validate plumbing; representative labeled queries and the actual retrieval configuration need separate evaluations.

**Explain:** Describe the symptom, hypothesis, experiment, root cause, fix and regression evidence. Do not claim generated tests independently prove all business requirements.
