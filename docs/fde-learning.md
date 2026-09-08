# FDE learning audit and walkthrough

Audit date: 2026-09-08. This repository is a practical agent-application learning foundation, not a complete curriculum for every Forward Deployed Engineer role. The role's emphasis varies by employer and customer environment. The assessment below concerns observable repository coverage, not a claim of job qualification.

## Findings and changes

Previously the workflow required a brief purpose/design/test explanation. Most skills were a few implementation instructions; a Workbench task could satisfy its lesson field with a single generic sentence. There was no consistent comparison of alternatives, beginner explanation, advanced topic or learning experiment.

Now all 14 skill stages have a concept reference and share the [teaching contract](../skills/learning-contract.md). The CLI embeds these references in execution packets. Workbench loads the same material from disk for model prompts, shows concept primers in Run history, and requires eight nonempty structured lesson fields for generated implementations. Stage primers are maintained teaching text; generated task explanations must connect them to the supplied task and specifications. Required fields establish structure, not factual correctness or mastery.

| Coverage | Where to learn/practice | Remaining evidence or experience |
|---|---|---|
| Discovery, personas, scope, business success | capability lesson and capability specification | Interview real users; validate baseline, value and adoption |
| Architecture and eight-module mapping | design and decomposition lessons | Defend alternatives against a real customer's constraints |
| Prompts, model choice, tools, orchestration | design and agents lessons | Benchmark actual models and diagnose live provider failures |
| Section 4: APIs and integrations | backend lesson and implemented tender APIs | Real customer-system integration, identity and network setup |
| Section 5: relational data and RAG | database, rag and production-rag lessons | Persistent semantic index, actual embedding evaluations, restore/migration trials |
| Section 7: the product UI | frontend lesson and tender portal | User observation, broader accessibility/usability evaluation |
| Security, debugging, tests and evals | security/tests/evals lessons and repository checks | Real environment review, load/concurrency behavior and representative data |
| Setup, delivery, incidents and handoff | infrastructure/deployment lessons | Actual rollout, support rotation, adoption feedback and incident recovery |

The eight modules cover technical concerns; FDE practice also requires discovery, negotiation of scope, communication, delivery and customer ownership. These now appear at the corresponding workflow stages instead of being a ninth service.

## What each step teaches

1. What the concept is, including one input/output trace.
2. Why this requirement needs it and when it should be omitted.
3. Two alternatives and conditions favoring each.
4. Advantages and costs in this use case.
5. Two relevant advanced mechanisms or failure modes.
6. A reproducible exercise with expected behavior and an honest executed/proposed label.
7. A scenario question and answer rubric.
8. A concise customer/interview explanation tied to actual evidence.

Use next/task mode to discuss and experiment after each task; all and section modes retain teaching but continue without quiz confirmation. Quizzes never create task completion receipts.

## RAG example

Start with [retrieval foundations](../skills/rag/references/learning.md), then the
[production RAG lesson](../skills/production-rag/references/learning.md). The latter
compares SQL, keyword search, long context, RAG, fine-tuning and training; explains
ingestion/query pipelines; and provides a synthetic two-bid experiment with
paraphrases, missing evidence, unauthorized requests and revised documents.

The key question is why changing documents should require changing model weights.
Retrieval supplies current evidence at query time; fine-tuning changes model
behavior through training and may complement retrieval. Neither approach alone
establishes correct authorization or trustworthy business decisions. See
[AWS's comparison](https://docs.aws.amazon.com/prescriptive-guidance/latest/retrieval-augmented-generation-options/rag-vs-fine-tuning.html).

Trace "What is A's warranty?" through document processing, retrieval and evidence.
Trace "How many bids are approved?" through SQL. Explain the difference in the UI
and API contract. Do not claim the reference's cited-excerpt search is already a
full live generative RAG deployment.

## Using it locally

Restart the Workbench after updating, pair again, and open the skills/catalog.
Search for a skill's references/learning.md or this guide. Connect a model for
personalized generation, select a solution, review its specs and run next or a
specific section with its authorized dependencies. Read the primer and task
lesson in Run history, inspect generated files, and compare actual verification
results with the proposed exercise. The API key connection belongs to the builder;
generated previews still have no provider keys or external network access.

For CLI/coding-agent learning, use the repository blueprint-workflow skill and ask:

```text
Teach and implement the next ready task for my selected solution.
Read skills/learning-contract.md and the task skill's references/learning.md.
Explain what it is, why this use case needs it, alternatives and tradeoffs,
two advanced concepts, and a small experiment. Execute authorized checks,
show actual results, give me a self-check and retain the lesson in evidence.
Then stop at this task so I can discuss what I learned.
```

The existing government tender reference prepares teaching plans for shared source;
a coding agent/developer executes those plans. New solution-local apps use the
bounded Workbench code writer. CLI run commands prepare packets, not implementations.
The production-rag selector requires a corresponding approved task; adding the skill
does not silently rewrite existing tender requirements or mark advanced RAG built.

## Practice needed beyond this repository

Use a capstone to demonstrate discovery notes, an architecture decision record, an
integrated UI/API demo, a measured retrieval experiment, a diagnosed failure and a
handoff/runbook. Record user feedback and a proposed or measured adoption outcome.
Practice Python, SQL, HTTP, Git, testing and container fundamentals alongside it.
Then extend to the actual role's stack, cloud/IAM/network environment and customer
integrations. Hardware fit, live inference cost/quality, production reliability and
personal interview claims must come from actual exercises and experience.

Teaching structure is validated automatically; teaching accuracy and whether you can
explain the tradeoffs still need learner/reviewer judgment. No live LLM teaching
quality or customer outcome was measured as part of this repository update.
