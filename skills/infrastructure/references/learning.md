# Reproducible runtime and integrations

**What:** Infrastructure supplies processes, networks, storage and configuration. A container packages dependencies; it does not automatically provide production reliability or make its data persistent.

**Why:** The customer's workstation must reproduce the app, database and parser behavior. Resource budgets matter when the OS, IDE, LLM and services share laptop memory.

**Alternatives and tradeoffs:** Compare a virtual environment with Docker, and local services with managed services. Containers improve reproducibility but require a daemon and image maintenance. Managed services reduce some operations while introducing network, cost and account dependencies.

**Advanced:** Readiness asks whether traffic can be served; liveness asks whether the process should restart. Networks and secrets should match each component's actual needs. Persistent volumes, backup recovery and resource limits must be tested. Infrastructure as code captures reviewed configuration; it does not remove environment-specific prerequisites.

**Practice:** Start the stack, verify health, stop a dependency and observe the error, then restart and check data persistence. In a disposable environment, restore a synthetic backup and inspect real records. The generated Workbench preview has temporary data and no external network; identify the explicit extension needed for live RAG.

**Check:** Does a working localhost URL establish a deployable production service? Rubric: only the tested local path is demonstrated; establish persistence, connectivity, capacity and operations against the target environment.

**Explain:** Give a teammate the setup, observable verification and troubleshooting steps needed to reproduce your result.
