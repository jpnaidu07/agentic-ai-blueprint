# Persistence and data integrity

**What:** A relational database stores records with constraints and transactions. A vector index supports similarity search; it does not replace the transaction system of record.

**Why:** Tenders, bids, criteria, score snapshots and approval state need relationships and repeatable calculations. Documents and index entries carry revision references back to authoritative records.

**Alternatives and tradeoffs:** SQLite simplifies a single-process prototype; PostgreSQL supports a broader concurrent deployment but adds service operations. Files suit immutable source blobs but require metadata and access controls. Embedding everything makes approximate search possible but does not guarantee exact counts or valid relationships.

**Advanced:** Isolation governs what concurrent transactions see; passing SQLite tests does not establish PostgreSQL behavior. Indexes speed suitable queries but cost writes/storage; inspect query plans. Schema changes need migration and rollback/data-compatibility plans. An outbox can coordinate committed business changes with asynchronous indexing without pretending two systems share one transaction.

**Practice:** Reject a bid referencing a nonexistent tender, roll back a failed multi-record write, and reproduce two competing updates. Add an index only after comparing an actual query plan on representative synthetic data.

**Check:** Can vector top-k results count all approved bids? Rubric: no, the query returns a limited approximate candidate set; use authorized SQL over authoritative approval state.

**Explain:** Link constraints and transaction behavior to the customer's ability to trust stored decisions.
