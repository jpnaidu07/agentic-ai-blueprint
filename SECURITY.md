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

If any GitHub, model-provider or local development token is pasted into chat,
logs, commits or terminal history, revoke it at its issuer and create a new one.
Deleting it from the latest commit is insufficient if it entered Git history.
