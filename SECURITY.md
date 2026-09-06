# Security policy

Incident Lab is a local workflow aid, not a security sandbox or independent auditor.

- Never store credentials or raw private conversations in evidence references.
- Run under a trusted local user. SQLite state and plugin code remain mutable by that user.
- Keep host homes private. POSIX database files are restricted to owner read/write.
- Native observation must fail open for host availability and fail closed for uncertain scope: missing trusted session identity means no capture, not guessed routing.
- Model-generated evidence and operator attestations are claims. They cannot authorize a repair, payment, credential use, or deployment.
- No automatic provider retries, host restarts, or approval bypass are part of this package.

Report security concerns privately through GitHub private vulnerability reporting when available; otherwise contact the maintainer without posting credentials or exploit data publicly. Do not include sensitive runtime databases in issues.
