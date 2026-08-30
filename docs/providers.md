# Provider contract and limitations

The adapter in `src/agent/llm_client.py` uses the Chat Completions compatibility
contract so applications can change providers through configuration. It does not
assume all providers or models support the same features. `LLM_MODEL` is required;
default model names and price tables from the reference image are intentionally
not copied into the code.

| Provider | LLM_PROVIDER | API base | Important boundary |
|---|---|---|---|
| OpenAI | `openai` | `https://api.openai.com/v1` | Model-specific output and tool capabilities must be checked. |
| Azure OpenAI | `azure` | Your resource URL ending `/openai/v1` | Set deployment name as model; API-key authentication. Entra integration is not implemented. |
| Anthropic | `anthropic` | `https://api.anthropic.com/v1` | Compatibility chat/tools only. Schema extraction is rejected because `response_format` is ignored. Native Messages adapter remains an extension. |
| Gemini | `gemini` | `https://generativelanguage.googleapis.com/v1beta/openai` | Compatibility subset; native features and multi-turn thought signatures are not implemented. |
| Ollama | `ollama` | `http://localhost:11434/v1` | Explicit local model; no automatic pull or silent mock fallback. |
| Compatible endpoint | `openai-compatible` | Explicit HTTPS API base ending `/v1` where applicable | Validate actual vendor semantics before use. |

`LLM_API_KEY`, `LLM_MODEL`, `LLM_BASE_URL`, temperature/top-p, output budget,
context budget, timeout and retry count are externally configurable. Sampling
values default to omitted, because some models reject them. The context check is
a conservative byte heuristic, not an exact tokenizer; validate it against your
model. `LLM_STRUCTURED_OUTPUT` and `LLM_TOOL_CALLING` default false. Setting a flag
is an operator assertion, not automatic capability discovery.

Fallback is opt-in through `LLM_FALLBACK_MODEL` and remains on the same provider
and endpoint, avoiding an implicit cross-provider data transfer. Only timeout,
network failures, rate limits and selected server errors are retried. Auth and
invalid-input errors are not retried. Schema-invalid, refused or truncated
responses raise errors. The maximum attempts are `(retries + 1)` per configured
model, with per-request timeouts; no live inference costs are measured by offline
tests. Response token usage is retained when the provider supplies it.

The `mock` provider is an explicitly selected infrastructure simulation. Tender
extraction rejects it. The old `auto` mode has been removed because infrastructure
outages must not become plausible-looking mock results.

The adapter forwards tool definitions and returns tool calls, but the old demo
orchestrator still uses its bounded text-action convention. It is not a complete
multi-provider production tool-calling agent. Tender extraction never invokes
tools or persists facts directly.

Official references used to verify request shapes:

- [OpenAI Chat Completions](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create)
- [Azure OpenAI v1 REST contract](https://learn.microsoft.com/en-us/rest/api/microsoft-foundry/azureopenai/chat)
- [Gemini compatibility](https://ai.google.dev/gemini-api/docs/openai)
- [Anthropic compatibility limitations](https://platform.claude.com/docs/en/cli-sdks-libraries/libraries/openai-sdk)
- [Ollama compatibility](https://docs.ollama.com/api/openai-compatibility)

Contract tests intercept HTTP; they do not establish account access, live provider
availability, model quality, production latency or correct billing.
