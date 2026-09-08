# Teaching contract for FDE engineering

Apply this teaching method at capability, design, decomposition and every implementation task. Read the selected skill's references/learning.md. Teach the actual approved use case and learner's requested depth; introduce unfamiliar terms before using them. A task title and a list of files are not a lesson.

Before implementation, explain:
1. **What:** define the concept in plain language and trace one concrete input to output.
2. **Why here:** identify the user's problem, requirement and constraints that justify this choice. When the concept is unnecessary, explain why and select the simpler design.
3. **Alternatives:** compare at least two credible approaches, including a deterministic or no-LLM baseline when relevant. State when an alternative would be preferable.
4. **Benefits and costs:** explain advantages alongside latency, accuracy, money, complexity, privacy and maintenance tradeoffs relevant to this task; do not invent benchmarks.
5. **Advanced concepts:** introduce two useful extensions or failure modes, explain the mechanism and when each is warranted. Label planned extensions separately from implemented features.
6. **Practice:** give a small reproducible exercise with fixture/input, steps, expected observation and failure case. Execute authorized checks and report observed results; otherwise label it proposed and give the exact missing prerequisite.
7. **Check understanding:** ask a scenario or counterfactual question, and include an answer rubric so the learner can self-check. In all mode continue without waiting for quiz answers. In step mode finish the selected step and allow discussion.
8. **Interview and customer explanation:** explain problem, decision, tradeoff and evidence in a short answer. Distinguish personal work, generated code, tested prototype and real deployment.

Adapt the reference example to the supplied domain. Tender rules must not leak into other solutions. Use customer discovery and acceptance metrics to justify architecture. Describe API contracts and user journeys together, and identify ownership of manual dependencies. During delivery also teach communication of unknowns, incident diagnosis, rollout, adoption and handoff where applicable.

Keep the lesson proportional to the selected task. Explain a new concept fully on first use, then connect later refinements to the current files and evidence. Never skip the lesson in all/section mode. Persist the explanation and measured/proposed experiment status with task evidence or run history. Quiz completion is not engineering completion and generated lessons are not proof of learning.

For Workbench implementation output, populate every structured lesson field. For specification stages put decisions and tradeoffs into the existing specification fields; do not invent schema fields. A coding agent should retain stage explanations in solution-local learning notes. The CLI prepares teaching prompts and primers; a developer/model must still personalize and execute them.
