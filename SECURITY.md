# Security policy

Do not report vulnerabilities through public issues when they expose secrets,
authentication bypasses, cross-tender data, unsafe document parsing or integrity
failures. Use the repository's private **Security → Report a vulnerability**
workflow. Include the affected commit, minimal synthetic reproduction, impact and
any relevant request ID. Do not include real tender documents, credentials or
personal data.

The supported surface is the latest `main` branch. This development reference is
not an approved public service. Keep it on loopback, use synthetic data, rotate
any exposed credentials, and do not grant it production access while a report is
being assessed.

Development controls include strict input models, request limits, tender-scoped
authorization, independent review, idempotent version binding, append-only SQLite
triggers, credential-free logs, explicit model transfer and dependency scanning.
They do not replace an organizational identity provider, TLS, encrypted storage,
malware scanning, isolated parsers, database privilege separation, audit/WORM
anchoring, secret management, rate limiting or procurement governance. These are
documented deployment gates, not certifications.

The local workbench is a separate control plane on loopback port 8080. Treat its
terminal pairing token as a credential. Browser bearer/CSRF tokens and provider
keys are memory-only, never cookies or browser storage. Host, Origin, client IP,
bounded inputs and fixed provider origins are checked. All paired sessions share
the checkout; this is not a multi-user or remote administration service.

Model-generated writes stay under the selected solution's runtime directory.
There is no arbitrary host shell or model-selected package installer. Generated
tests/previews run only in a restricted Docker container without model keys,
repository/home mounts or the Docker socket. Tests have no network; previews use
an internal-only network behind a separate trusted, fixed-upstream HTTP relay with
a loopback-published port. The relay has no generated source mount, arbitrary URL
forwarding or CONNECT support. Docker is not a complete defense
against hostile code or kernel exploits. Use a disposable VM for untrusted projects.
Do not expose the workbench through tunnels or public reverse proxies.

Source/test snapshots and run history are local development evidence, not independent
proof of correctness. Review agent-authored tests and use external acceptance checks.
See [workbench limits](docs/workbench.md) before extending execution or deployment.

If any GitHub, model-provider or local development token is pasted into chat,
logs, commits or terminal history, revoke it at its issuer and create a new one.
Deleting it from the latest commit is insufficient if it entered Git history.
