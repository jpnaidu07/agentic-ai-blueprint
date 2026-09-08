# Delivery, adoption and operational ownership

**What:** Deployment makes a tested application available in a target environment. FDE delivery also means that users can adopt it and someone can operate, troubleshoot and maintain it.

**Why:** A tender demo can work locally yet fail in a customer's identity, storage and network environment. A release needs a user journey, operational owner and a way to recover.

**Alternatives and tradeoffs:** Compare a local pilot with a managed deployment, and a full switch with a staged rollout. Pilots expose workflow feedback cheaply; broader releases need capacity and support. More automation reduces repeated work but still needs explicit rollback and decision criteria.

**Advanced:** An SLI measures service behavior, an SLO sets its target, and an error budget bounds tolerated failure. Rollback must account for data migrations as well as code. Adoption measures (repeat use, task completion) complement technical metrics. Incident review records impact, root cause and prevention without inventing a success story.

**Practice:** Prepare a customer demo with one happy path and one recovery path. Write a runbook with health checks, escalation owner and exact rollback steps. In a disposable environment execute a rollback or restore and record the result. Propose a pilot feedback schedule and measurable adoption target; leave unmeasured values labeled targets.

**Check:** Tests pass, but reviewers still use spreadsheets. Is delivery complete? Rubric: investigate workflow fit, training and missing integration; technical health alone is not adoption.

**Explain:** Present business outcome, implementation, measured evidence, current limits and ownership in a handoff another engineer can use.
