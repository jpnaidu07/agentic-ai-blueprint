# Tender architecture diagrams
Solid lines describe the reference. Dotted lines mark optional or planned integrations.

## System Context

```mermaid
flowchart LR
  Admin[Procurement administrator] --> API[Tender platform]
  Evaluator[Evidence evaluator] --> API
  Committee[Independent committee] --> API
  Auditor[Scoped auditor] --> API
  API -. Opt-in page extraction .-> Provider[Approved model provider]
  API --> Records[Evidence and audit records]
```


## Container Architecture

```mermaid
flowchart LR
  Browser[Same-origin portal] --> FastAPI[Authenticated FastAPI]
  FastAPI --> Policy[Deterministic policy engine]
  FastAPI --> Parser[Digital PDF parser]
  FastAPI --> DB[(PostgreSQL)]
  FastAPI -. Optional .-> LLM[Provider adapter]
  Policy --> DB
  Parser --> DB
```


## Agent Workflow

```mermaid
flowchart TD
  Page[Authorized page and published criteria] --> Gate{Model transfer allowed?}
  Gate -->|No| Manual[Human fact review]
  Gate -->|Yes| Extract[Versioned extraction prompt]
  Extract --> Schema[Validate schema and exact quotes]
  Schema -->|Valid| Proposals[Unaccepted proposals]
  Schema -->|Invalid| Failure[Explicit failure; no facts written]
  Proposals --> Manual
  Manual --> Facts[Append reviewed fact]
```


## Data Flow

```mermaid
flowchart LR
  PDF[Original digital PDF] --> Docs[(Document bytes and digest)]
  PDF --> Pages[Page text and offsets]
  Pages --> Chunks[Evidence chunks]
  Pages --> Review[Verified quote and numeric value]
  Review --> Facts[(Versioned facts)]
  Facts --> Evaluation[(Frozen evaluation snapshot)]
  Evaluation --> Decision[(Independent human decision)]
  Docs --> Audit[(Audit chain)]
  Facts --> Audit
  Decision --> Audit
```


## Document Ingestion

```mermaid
flowchart TD
  Upload[Authorized upload] --> Bounds[Bound body before multipart]
  Bounds --> Type[Validate PDF signature and type]
  Type --> Scan{Scanner clean or local development?}
  Scan -->|No| Reject[Reject upload]
  Scan -->|Yes| Parse[Extract layout and page text]
  Parse --> Check{Supported digital PDF?}
  Check -->|No| Reject
  Check -->|Yes| Hash[Hash and detect duplicate in scope]
  Hash --> Store[(Transactional bytes, pages and chunks)]
```


## Rag Flow

```mermaid
flowchart LR
  Query[Evidence query] --> ACL[Tender and bidder scope filter]
  ACL --> BM25[BM25 lexical ranking]
  ACL -. Extension .-> Embeddings[Approved embedding provider and index]
  BM25 --> Results[Page-cited evidence]
  Embeddings -. Rank fusion extension .-> Results
  Results --> Empty{Evidence found?}
  Empty -->|No| Abstain[Insufficient evidence]
  Empty -->|Yes| Human[Human interpretation; no invented answer]
```


## Evaluation Workflow

```mermaid
flowchart TD
  Lock[Lock tender revision] --> Facts[Load latest reviewed facts]
  Facts --> Gate{Eligibility and evidence complete?}
  Gate -->|No| Block[Ineligible or needs review; no rank]
  Gate -->|Yes| Price[Lowest complete eligible commercial total]
  Price --> Score[Decimal weighted scoring]
  Score --> Snapshot[Store version and input digest]
  Snapshot --> Committee{Independent reviewer; same revision?}
  Committee -->|No| Reject[Reject stale or unauthorized decision]
  Committee -->|Yes| Decision[Append human approval or rejection]
  Decision --> Frozen[Approval freezes version; no automatic award]
```


## Deployment Architecture

```mermaid
flowchart LR
  Laptop[Windows or Linux developer] --> Loopback[Loopback port 8000]
  Loopback --> App[Non-root app container: 2 GiB]
  App --> DB[(PostgreSQL container: 2 GiB)]
  DB --> Volume[Persistent named volume]
  App -. Cloud default when configured .-> Cloud[Approved HTTPS provider]
  App -. Opt-in local-ai profile .-> Ollama[Ollama: 8 GiB cap]
  Dev[Python-only alternative] --> SQLite[(Temporary or local SQLite)]
```
