---
name: database
description: Implement relational entities, constraints, migrations and data integrity checks from an approved solution's database work packages.
---

# Database engineering

Before this step, read [the teaching contract](../learning-contract.md) and
[this concept lesson](references/learning.md). Explain what, why for the selected
use case, alternatives, benefits/costs, advanced mechanisms and a practical
exercise with a self-check; retain the explanation with the task evidence.

Explain the entity relationships, ownership and transactional invariants. Implement
the approved schema, foreign keys, uniqueness, indexes, migration and rollback
path. Distinguish transactional records from document/object storage and optional
retrieval indexes. Test duplicate/conflicting writes and the actual target database
where available; SQLite results do not prove PostgreSQL concurrency behavior.

Use `agent-blueprint run <solution> database` for a teaching plan. Follow its
dependencies and definition of done. If a database runtime is missing, give the
exact setup and connection-check commands, finish safe schema work and leave the
runtime acceptance task incomplete. Record actual source and test evidence with
`agent-blueprint complete`; a plan is not a migration or an executed database.
